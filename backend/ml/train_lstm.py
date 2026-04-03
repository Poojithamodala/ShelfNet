import os
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import joblib

from dataset import load_sensor_data, create_sequences, FEATURES

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH  = os.path.join(BASE_DIR, "trained_model.h5")
SCALER_PATH = os.path.join(BASE_DIR, "scaler.pkl")

print("=" * 55)
print("  ShelfNet LSTM — Training")
print("=" * 55)

print("\n🔹 Loading dataset from MongoDB...")
df = load_sensor_data()
print(f"  Total readings loaded: {len(df)}")

print("\n🔹 Label distribution:")
print(f"  Mean  : {df['remaining_shelf_life'].mean():.2f} days")
print(f"  Std   : {df['remaining_shelf_life'].std():.2f} days")
print(f"  Min   : {df['remaining_shelf_life'].min():.2f} days")
print(f"  Max   : {df['remaining_shelf_life'].max():.2f} days")

# Scale only sensor features, not fruit_encoded
SENSOR_FEATURES = ["temperature", "humidity", "ethylene", "co2", "o2"]
scaler = MinMaxScaler()
df[SENSOR_FEATURES] = scaler.fit_transform(df[SENSOR_FEATURES])

X, y = create_sequences(df)
print(f"\n🔹 Total sequences : {X.shape}  →  labels shape: {y.shape}")

X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, shuffle=True, random_state=42
)

print(f"  Train sequences : {len(X_train)}")
print(f"  Val   sequences : {len(X_val)}")
print(f"\n  Train label std : {y_train.std():.2f}")
print(f"  Val   label std : {y_val.std():.2f}")

print("\n🔹 Building model...")
model = Sequential([
    LSTM(128, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])),
    BatchNormalization(),
    Dropout(0.3),

    LSTM(64, return_sequences=False),
    BatchNormalization(),
    Dropout(0.2),

    Dense(32, activation="relu"),
    Dense(1)
])

model.compile(
    optimizer="adam",
    loss="huber",
    metrics=["mae"]
)

model.summary()

callbacks = [
    EarlyStopping(
        monitor="val_loss",
        patience=15,
        restore_best_weights=True,
        verbose=1
    ),
    ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=5,
        min_lr=1e-5,
        verbose=1
    )
]

print("\n🔹 Training...")
history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=150,
    batch_size=32,
    callbacks=callbacks,
    verbose=1
)

print("\n🔹 Saving model and scaler...")
model.save(MODEL_PATH)
joblib.dump(scaler, SCALER_PATH)
print(f"  ✅ Model saved  : {MODEL_PATH}")
print(f"  ✅ Scaler saved : {SCALER_PATH}")

best_val_mae = min(history.history["val_mae"])
best_val_loss = min(history.history["val_loss"])
print(f"\n✅ Training complete.")
print(f"   Best val MAE  : {best_val_mae:.4f} days")
print(f"   Best val loss : {best_val_loss:.4f}")
print(f"   Epochs run    : {len(history.history['loss'])}")