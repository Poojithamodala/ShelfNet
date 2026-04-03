from datetime import datetime, timedelta
import os
import numpy as np
import joblib
from tensorflow.keras.models import load_model
from tensorflow.keras import layers
from keras.engine import input_layer as keras_input_layer
from pymongo import MongoClient

# Patch for legacy model format
_orig_input_layer_init = keras_input_layer.InputLayer.__init__

def _input_layer_init_wrapper(self, *args, **kwargs):
    kwargs.pop("batch_shape", None)
    kwargs.pop("optional", None)
    return _orig_input_layer_init(self, *args, **kwargs)

keras_input_layer.InputLayer.__init__ = _input_layer_init_wrapper

from ml.dataset import FEATURES, SENSOR_FEATURES, SEQUENCE_LENGTH, FRUIT_ENCODING
from services.alert_service import evaluate_alerts

# ── PATHS ────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH  = os.path.join(BASE_DIR, "ml", "trained_model.h5")
SCALER_PATH = os.path.join(BASE_DIR, "ml", "scaler.pkl")

# ── LOAD MODEL & SCALER ──────────────────────────────────────────────────────
try:
    model = load_model(MODEL_PATH, compile=False)
    print("✅ Model loaded successfully.")
except Exception as exc:
    print(f"WARNING: Model load failed ({exc}), using dummy fallback.")
    model = None

try:
    scaler = joblib.load(SCALER_PATH)
    print("✅ Scaler loaded successfully.")
except Exception as exc:
    print(f"WARNING: Scaler load failed ({exc}), using identity transform.")
    scaler = None

# ── DB ───────────────────────────────────────────────────────────────────────
client           = MongoClient("mongodb://localhost:27017")
db               = client["shelfnet"]
sensor_collection = db["sensor_readings"]
batches_col       = db["batches"]


def _encode_fruit(fruit: str) -> int:
    """Encode fruit name to integer. Returns 0 for unknown fruits."""
    return FRUIT_ENCODING.get(fruit, 0)


def _scale_sensor_row(row_5: np.ndarray) -> np.ndarray:
    """
    Scale a (N, 5) array of sensor features using the fitted scaler.
    Scaler was trained on SENSOR_FEATURES only (5 cols), not fruit_encoded.
    """
    if scaler is not None:
        return scaler.transform(row_5)
    return row_5


def _build_sequence(sensor_reading: dict, fruit: str) -> np.ndarray:
    """
    Build a (1, SEQUENCE_LENGTH, 6) input array from a single static
    sensor reading + fruit type by repeating SEQUENCE_LENGTH times.

    Features order: [temperature, humidity, ethylene, co2, o2, fruit_encoded]
    Scaler applied only to the first 5 (sensor) features.
    """
    fruit_encoded = _encode_fruit(fruit)

    # Build 5-feature sensor row
    sensor_row = np.array([[
        float(sensor_reading.get("temperature_c",    12.0)),
        float(sensor_reading.get("humidity_percent", 90.0)),
        float(sensor_reading.get("ethylene_ppm",      0.5)),
        float(sensor_reading.get("co2_ppm",           1.0)),
        float(sensor_reading.get("o2_percent",       20.0)),
    ]] * SEQUENCE_LENGTH, dtype=np.float32)  # (SEQUENCE_LENGTH, 5)

    # Scale sensor features
    sensor_row_scaled = _scale_sensor_row(sensor_row)  # (SEQUENCE_LENGTH, 5)

    # Append fruit_encoded as 6th column (not scaled)
    fruit_col = np.full((SEQUENCE_LENGTH, 1), fruit_encoded, dtype=np.float32)
    X = np.concatenate([sensor_row_scaled, fruit_col], axis=1)  # (SEQUENCE_LENGTH, 6)

    return X.reshape(1, SEQUENCE_LENGTH, len(FEATURES))  # (1, 10, 6)


def predict_static(sensor_reading: dict, fruit: str = "Unknown") -> float:
    """
    Predict remaining shelf life from a single static sensor reading.
    Used when adding a batch — no DB readings needed.

    Args:
        sensor_reading : dict with any of:
                         temperature_c, humidity_percent, ethylene_ppm,
                         co2_ppm, o2_percent
        fruit          : fruit name string (e.g. "Apple", "Banana")

    Returns:
        Predicted remaining shelf life in days (float).
    """
    X = _build_sequence(sensor_reading, fruit)

    if model is not None:
        prediction = round(float(model.predict(X, verbose=0)[0][0]), 2)
    else:
        # Fallback heuristic based on temperature
        temp_norm  = X[0, 0, 0]
        prediction = round(max(1.0, (1.0 - temp_norm) * 30.0), 2)

    return prediction


def predict_for_batch(batch_id: str, force: bool = False) -> float:
    """
    Predict remaining shelf life for a batch using its stored sensor readings.
    Falls back to static prediction if not enough readings exist yet.
    """
    batch = batches_col.find_one({"batch_id": batch_id})
    if not batch:
        raise ValueError("Batch not found")

    fruit = batch.get("fruit", "Unknown")

    # ── TTL cache (30 min) ───────────────────────────────────────────────────
    if (
        not force
        and batch.get("predicted_remaining_shelf_life_days") is not None
        and batch.get("last_predicted_at")
        and datetime.utcnow() - batch["last_predicted_at"] < timedelta(minutes=30)
    ):
        return batch["predicted_remaining_shelf_life_days"]

    # ── Fetch latest SEQUENCE_LENGTH sensor readings ─────────────────────────
    readings = list(
        sensor_collection.find(
            {"batch_id": batch_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(SEQUENCE_LENGTH)
    )

    # ── Fallback: not enough real readings yet → use static prediction ────────
    if len(readings) < SEQUENCE_LENGTH:
        print(f"⚠️  Only {len(readings)} readings for {batch_id} "
              f"(need {SEQUENCE_LENGTH}). Using static prediction.")

        # Build sensor_reading dict from whatever we have, or use batch defaults
        if readings:
            latest = readings[0]
            sensor_reading = {
                "temperature_c":    latest.get("temperature",  12.0),
                "humidity_percent": latest.get("humidity",     90.0),
                "ethylene_ppm":     latest.get("ethylene",      0.5),
                "co2_ppm":          latest.get("co2",           1.0),
                "o2_percent":       latest.get("o2",           20.0),
            }
        else:
            # Brand new batch — use fruit profile defaults
            from simulator import FRUIT_PROFILES, DEFAULT_PROFILE
            profile = FRUIT_PROFILES.get(fruit, DEFAULT_PROFILE)
            sensor_reading = {
                "temperature_c":    sum(profile["temperature"]) / 2,
                "humidity_percent": sum(profile["humidity"]) / 2,
                "ethylene_ppm":     sum(profile["ethylene"]) / 2,
                "co2_ppm":          1.0,
                "o2_percent":       20.0,
            }

        prediction = predict_static(sensor_reading, fruit)

        # Persist and return
        batches_col.update_one(
            {"batch_id": batch_id},
            {"$set": {
                "predicted_remaining_shelf_life_days": prediction,
                "last_predicted_at": datetime.utcnow()
            }}
        )
        return prediction

    # ── Full LSTM prediction from real readings ───────────────────────────────
    latest     = readings[0]
    warehouse_id = latest["warehouse_id"]
    readings   = list(reversed(readings))  # oldest → newest

    # Build (SEQUENCE_LENGTH, 5) sensor array
    sensor_arr = np.array(
        [[r["temperature"], r["humidity"], r["ethylene"], r["co2"], r["o2"]]
         for r in readings],
        dtype=np.float32
    )

    # Scale sensor features only
    sensor_arr_scaled = _scale_sensor_row(sensor_arr)  # (SEQUENCE_LENGTH, 5)

    # Append fruit_encoded as 6th column
    fruit_encoded = _encode_fruit(fruit)
    fruit_col     = np.full((SEQUENCE_LENGTH, 1), fruit_encoded, dtype=np.float32)
    X = np.concatenate([sensor_arr_scaled, fruit_col], axis=1)  # (SEQUENCE_LENGTH, 6)
    X = X.reshape(1, SEQUENCE_LENGTH, len(FEATURES))            # (1, 10, 6)

    # Predict
    if model is not None:
        prediction = round(float(model.predict(X, verbose=0)[0][0]), 2)
    else:
        prediction = round(float(X[0, :, 0].mean() * 0.1 + 1.0), 2)

    # ── Alert evaluation ─────────────────────────────────────────────────────
    history = list(
        sensor_collection.find(
            {"batch_id": batch_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(6)
    )

    evaluate_alerts(
        batch_id=batch_id,
        warehouse_id=warehouse_id,
        fruit=fruit,
        prediction=prediction,
        latest=latest,
        history=list(reversed(history))
    )

    # ── Persist prediction ───────────────────────────────────────────────────
    batches_col.update_one(
        {"batch_id": batch_id},
        {"$set": {
            "predicted_remaining_shelf_life_days": prediction,
            "last_predicted_at": datetime.utcnow()
        }}
    )

    return prediction