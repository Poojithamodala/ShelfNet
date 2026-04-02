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
MODEL_PATH = os.path.join(BASE_DIR, "ml", "trained_model.h5")
SCALER_PATH = os.path.join(BASE_DIR, "ml", "scaler.pkl")

# ---------------- LOAD MODEL ----------------
try:
    model = load_model(MODEL_PATH, compile=False)
except Exception as exc:
    print(f"WARNING: Model load failed ({exc}), using dummy fallback.")
    model = None

try:
    scaler = joblib.load(SCALER_PATH)
except Exception as exc:
    print(f"WARNING: Scaler load failed ({exc}), using identity transform.")
    scaler = None

# ---------------- DB ----------------
client = MongoClient("mongodb://localhost:27017")
db = client["shelfnet"]
sensor_collection = db["sensor_readings"]
batches_col = db["batches"]

# ---------------- PREDICTION ----------------
def predict_for_batch(batch_id: str, force: bool = False):

    batch = batches_col.find_one({"batch_id": batch_id})
    if not batch:
        raise ValueError("Batch not found")

    # ✅ TTL reuse (30 min)
    if (
        not force and
        batch.get("predicted_remaining_shelf_life_days") is not None and
        batch.get("last_predicted_at") and
        datetime.utcnow() - batch["last_predicted_at"] < timedelta(minutes=30)
    ):
        return batch["predicted_remaining_shelf_life_days"]

    # 🔹 Fetch sensor readings
    readings = list(
        sensor_collection.find(
            {"batch_id": batch_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(SEQUENCE_LENGTH)
    )

    if len(readings) < SEQUENCE_LENGTH:
        raise ValueError("Not enough sensor data for prediction")

    latest = readings[0]
    warehouse_id = latest["warehouse_id"]

    # Oldest → newest
    readings = list(reversed(readings))

    # 🔹 Build model input X  ✅ THIS WAS MISSING
    X = np.array([
        [r[f] for f in FEATURES]
        for r in readings
    ])

    if scaler is not None:
        X = scaler.transform(X)
    X = X.reshape(1, SEQUENCE_LENGTH, len(FEATURES))

    # 🔮 Predict
    if model is not None:
        prediction = round(float(model.predict(X, verbose=0)[0][0]), 2)
    else:
        # fallback: use normalized average temperature-based heuristic
        prediction = round(float(X[0,:,0].mean() * 0.1 + 1.0), 2)

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
