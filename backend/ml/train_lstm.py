import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import joblib

from dataset import load_sensor_data, create_sequences, FEATURES

MODEL_PATH = "trained_model.h5"
SCALER_PATH = "scaler.pkl"

print("🔹 Loading dataset...")
df = load_sensor_data()

scaler = MinMaxScaler()
df[FEATURES] = scaler.fit_transform(df[FEATURES])

X, y = create_sequences(df)

print("🔹 Total sequences:", X.shape)

# Train / validation split
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, shuffle=False
)

model = Sequential([
    LSTM(64, input_shape=(X.shape[1], X.shape[2])),
    Dense(1)
])

model.compile(
    optimizer="adam",
    loss="mse"
)

model.fit(
    X_train,
    y_train,
    validation_data=(X_val, y_val),
    epochs=20,
    batch_size=16
)

model.save(MODEL_PATH)
joblib.dump(scaler, SCALER_PATH)

print("Model & scaler saved successfully")
