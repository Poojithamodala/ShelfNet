from datetime import datetime, timedelta
import os
import numpy as np
import joblib
from tensorflow.keras.models import load_model
from pymongo import MongoClient

from ml.dataset import FEATURES, SEQUENCE_LENGTH
from services.alert_service import evaluate_alerts

# ---------------- PATHS ----------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "ml", "trained_model.h5")
SCALER_PATH = os.path.join(BASE_DIR, "ml", "scaler.pkl")

# ---------------- LOAD MODEL ----------------
model = load_model(MODEL_PATH, compile=False)
scaler = joblib.load(SCALER_PATH)

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

    X = scaler.transform(X)
    X = X.reshape(1, SEQUENCE_LENGTH, len(FEATURES))

    # 🔮 Predict
    prediction = round(float(model.predict(X, verbose=0)[0][0]), 2)

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
