import os
import numpy as np
import joblib
from tensorflow.keras.models import load_model
from pymongo import MongoClient

from ml.dataset import FEATURES, SEQUENCE_LENGTH
from services.alert_service import evaluate_alerts

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "ml", "trained_model.h5")
SCALER_PATH = os.path.join(BASE_DIR, "ml", "scaler.pkl")

# LOAD MODEL & SCALER (ONCE)
model = load_model(MODEL_PATH, compile=False)
scaler = joblib.load(SCALER_PATH)

client = MongoClient("mongodb://localhost:27017")
db = client["shelfnet"]
sensor_collection = db["sensor_readings"]
batches_col = db["batches"]

# PREDICTION
def predict_for_batch(batch_id: str):
    
    batch = batches_col.find_one(
        {"batch_id": batch_id},
        {"_id": 0, "fruit": 1}
    )
    fruit = batch["fruit"] if batch and "fruit" in batch else None

    # Fetch latest N readings for prediction
    readings = list(
        sensor_collection.find(
            {"batch_id": batch_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(SEQUENCE_LENGTH)
    )

    if len(readings) < SEQUENCE_LENGTH:
        raise ValueError("Not enough sensor data for prediction")

    latest_reading = readings[0]
    warehouse_id = latest_reading["warehouse_id"]

    # Oldest → newest
    readings = list(reversed(readings))

    # Prepare model input
    X = np.array([[r[f] for f in FEATURES] for r in readings])
    X = scaler.transform(X)
    X = X.reshape(1, SEQUENCE_LENGTH, len(FEATURES))

    # Predict shelf life
    prediction = round(float(model.predict(X)[0][0]), 2)

    # Fetch short history for trend-based alerts
    history = list(
        sensor_collection.find(
            {"batch_id": batch_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(6)
    )

    # Trigger alerts
    evaluate_alerts(
        batch_id=batch_id,
        warehouse_id=warehouse_id,
        fruit=fruit,
        prediction=prediction,
        latest=latest_reading,
        history=list(reversed(history))
    )

    return prediction
