import pandas as pd
import numpy as np
from pymongo import MongoClient

FEATURES = ["temperature", "humidity", "ethylene", "co2", "o2"]
SEQUENCE_LENGTH = 10

client = MongoClient("mongodb://localhost:27017")
db = client["shelfnet"]
sensor_collection = db["sensor_readings"]
batch_collection = db["batches"]

def load_sensor_data():
    readings = list(sensor_collection.find({}, {"_id": 0}))
    batches = {
        b["batch_id"]: b
        for b in batch_collection.find({}, {"_id": 0})
    }

    df = pd.DataFrame(readings)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # attach arrival_date & expected shelf life
    df["arrival_date"] = df["batch_id"].map(
        lambda x: batches[x]["arrival_date"]
    )
    df["expected_shelf_life"] = df["batch_id"].map(
        lambda x: batches[x]["expected_shelf_life_days"]
    )

    df["arrival_date"] = pd.to_datetime(df["arrival_date"])

    # Remaining shelf life label
    df["days_since_arrival"] = (
        df["timestamp"] - df["arrival_date"]
    ).dt.total_seconds() / (3600 * 24)

    df["remaining_shelf_life"] = (
        df["expected_shelf_life"] - df["days_since_arrival"]
    ).clip(lower=0)

    return df

def create_sequences(df):
    X, y = [], []

    for batch_id, batch_df in df.groupby("batch_id"):
        batch_df = batch_df.sort_values("timestamp")

        values = batch_df[FEATURES].values
        labels = batch_df["remaining_shelf_life"].values

        for i in range(len(values) - SEQUENCE_LENGTH):
            X.append(values[i:i + SEQUENCE_LENGTH])
            y.append(labels[i + SEQUENCE_LENGTH])

    return np.array(X), np.array(y)
