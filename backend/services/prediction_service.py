from datetime import datetime, timedelta
import os
import numpy as np
import joblib
from tensorflow.keras.models import load_model
from tensorflow.keras import layers
from keras.engine import input_layer as keras_input_layer
from pymongo import MongoClient

# patch for legacy model format with batch_shape and optional in InputLayer
_orig_input_layer_init = keras_input_layer.InputLayer.__init__

def _input_layer_init_wrapper(self, *args, **kwargs):
    kwargs.pop("batch_shape", None)
    kwargs.pop("optional", None)
    return _orig_input_layer_init(self, *args, **kwargs)

keras_input_layer.InputLayer.__init__ = _input_layer_init_wrapper

from ml.dataset import FEATURES, SEQUENCE_LENGTH
from services.alert_service import evaluate_alerts

# ---------------- PATHS ----------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH  = os.path.join(BASE_DIR, "ml", "trained_model.h5")
SCALER_PATH = os.path.join(BASE_DIR, "ml", "scaler.pkl")

# ---------------- LOAD MODEL & SCALER ----------------
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

# ---------------- DB ----------------
client = MongoClient("mongodb://localhost:27017")
db = client["shelfnet"]
sensor_collection = db["sensor_readings"]
batches_col       = db["batches"]

# ---------------- FEATURE ORDER (must match training) ----------------
# FEATURES = ["temperature", "humidity", "ethylene", "co2", "o2"]
# Scaler ranges from training data:
#   temperature : 0.0  – 18.0  °C
#   humidity    : 85.0 – 95.0  %
#   ethylene    : 0.1  –  6.0  ppm
#   co2         : 0.6  –  1.58 ppm
#   o2          : 17.76– 20.5  %


def _build_static_sequence(sensor_reading: dict) -> np.ndarray:
    """
    Build a (1, SEQUENCE_LENGTH, n_features) array from a single static
    sensor reading by repeating the reading SEQUENCE_LENGTH times.
    This simulates a steady-state environment for the batch at arrival.

    Expected keys in sensor_reading (all optional — defaults used if missing):
        temperature_c   (float)  default 12.0 °C
        humidity_percent(float)  default 90.0 %
        ethylene_ppm    (float)  default 0.5  ppm
        co2_ppm         (float)  default 1.0  ppm
        o2_percent      (float)  default 20.0 %
    """
    # Pull values with sensible cold-storage defaults
    row = [
        float(sensor_reading.get("temperature_c",    12.0)),
        float(sensor_reading.get("humidity_percent", 90.0)),
        float(sensor_reading.get("ethylene_ppm",      0.5)),
        float(sensor_reading.get("co2_ppm",           1.0)),
        float(sensor_reading.get("o2_percent",       20.0)),
    ]

    # Repeat single reading to fill the required sequence length
    X = np.array([row] * SEQUENCE_LENGTH, dtype=np.float32)  # (SEQUENCE_LENGTH, 5)

    if scaler is not None:
        X = scaler.transform(X)

    return X.reshape(1, SEQUENCE_LENGTH, len(FEATURES))       # (1, 10, 5)


def predict_static(sensor_reading: dict) -> float:
    """
    Predict remaining shelf life from a single static sensor reading.
    Used when adding a batch manually — no DB readings needed.

    Args:
        sensor_reading: dict with any of:
            temperature_c, humidity_percent, ethylene_ppm, co2_ppm, o2_percent

    Returns:
        Predicted remaining shelf life in days (float).
    """
    X = _build_static_sequence(sensor_reading)

    if model is not None:
        prediction = round(float(model.predict(X, verbose=0)[0][0]), 2)
    else:
        # Fallback: rough heuristic based on temperature
        # Lower temperature → longer shelf life
        temp_norm = X[0, 0, 0]  # already scaled
        prediction = round(max(1.0, (1.0 - temp_norm) * 30.0), 2)

    return prediction


# ---------------- PREDICTION FROM DB READINGS ----------------
def predict_for_batch(batch_id: str, force: bool = False):
    """
    Predict remaining shelf life for a batch using its stored sensor readings.
    Requires at least SEQUENCE_LENGTH readings in sensor_readings collection.
    """
    batch = batches_col.find_one({"batch_id": batch_id})
    if not batch:
        raise ValueError("Batch not found")

    # ✅ TTL reuse (30 min) — skip re-prediction if recently predicted
    if (
        not force and
        batch.get("predicted_remaining_shelf_life_days") is not None and
        batch.get("last_predicted_at") and
        datetime.utcnow() - batch["last_predicted_at"] < timedelta(minutes=30)
    ):
        return batch["predicted_remaining_shelf_life_days"]

    # 🔹 Fetch latest SEQUENCE_LENGTH sensor readings
    readings = list(
        sensor_collection.find(
            {"batch_id": batch_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(SEQUENCE_LENGTH)
    )

    if len(readings) < SEQUENCE_LENGTH:
        raise ValueError(
            f"Not enough sensor data for prediction "
            f"(need {SEQUENCE_LENGTH}, got {len(readings)})"
        )

    latest = readings[0]
    warehouse_id = latest["warehouse_id"]

    # Oldest → newest
    readings = list(reversed(readings))

    # 🔹 Build model input
    X = np.array(
        [[r[f] for f in FEATURES] for r in readings],
        dtype=np.float32
    )

    if scaler is not None:
        X = scaler.transform(X)
    X = X.reshape(1, SEQUENCE_LENGTH, len(FEATURES))

    # 🔮 Predict
    if model is not None:
        prediction = round(float(model.predict(X, verbose=0)[0][0]), 2)
    else:
        prediction = round(float(X[0, :, 0].mean() * 0.1 + 1.0), 2)

    # 🔔 Alert evaluation
    history = list(
        sensor_collection.find(
            {"batch_id": batch_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(6)
    )

    evaluate_alerts(
        batch_id=batch_id,
        warehouse_id=warehouse_id,
        fruit=batch.get("fruit"),
        prediction=prediction,
        latest=latest,
        history=list(reversed(history))
    )

    # 💾 Persist prediction
    batches_col.update_one(
        {"batch_id": batch_id},
        {
            "$set": {
                "predicted_remaining_shelf_life_days": prediction,
                "last_predicted_at": datetime.utcnow()
            }
        }
    )

    return prediction