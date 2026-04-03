import os
import sys
import numpy as np
import joblib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import load_model
from keras.engine import input_layer as keras_input_layer

_orig = keras_input_layer.InputLayer.__init__
def _patched(self, *args, **kwargs):
    kwargs.pop("batch_shape", None)
    kwargs.pop("optional", None)
    return _orig(self, *args, **kwargs)
keras_input_layer.InputLayer.__init__ = _patched

from dataset import load_sensor_data, create_sequences, FEATURES, SEQUENCE_LENGTH

SENSOR_FEATURES = ["temperature", "humidity", "ethylene", "co2", "o2"]

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH  = os.path.join(BASE_DIR, "trained_model.h5")
SCALER_PATH = os.path.join(BASE_DIR, "scaler.pkl")

print("=" * 55)
print("  ShelfNet LSTM — Model Evaluation")
print("=" * 55)

print("\n🔹 Loading model and scaler...")
try:
    model = load_model(MODEL_PATH, compile=False)
    print("  ✅ Model loaded:", MODEL_PATH)
except Exception as e:
    print(f"  ❌ Model load failed: {e}")
    sys.exit(1)

try:
    scaler = joblib.load(SCALER_PATH)
    print("  ✅ Scaler loaded:", SCALER_PATH)
except Exception as e:
    print(f"  ❌ Scaler load failed: {e}")
    sys.exit(1)

print("\n🔹 Loading dataset from MongoDB...")
df = load_sensor_data()
print(f"  Total readings loaded: {len(df)}")

print("\n🔹 Label distribution:")
print(f"  Mean  : {df['remaining_shelf_life'].mean():.2f} days")
print(f"  Std   : {df['remaining_shelf_life'].std():.2f} days")
print(f"  Min   : {df['remaining_shelf_life'].min():.2f} days")
print(f"  Max   : {df['remaining_shelf_life'].max():.2f} days")

# Only scale sensor features — fruit_encoded is a category, not scaled
df[SENSOR_FEATURES] = scaler.transform(df[SENSOR_FEATURES])

X, y = create_sequences(df)
print(f"  Total sequences: {X.shape}  →  labels shape: {y.shape}")

# Match same split as training
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, shuffle=True, random_state=42
)
print(f"  Train sequences : {len(X_train)}")
print(f"  Val   sequences : {len(X_val)}")
print(f"  Train label std : {y_train.std():.2f}")
print(f"  Val   label std : {y_val.std():.2f}")

print("\n🔹 Running predictions...")
y_pred_train = model.predict(X_train, verbose=0).flatten()
y_pred_val   = model.predict(X_val,   verbose=0).flatten()

def compute_metrics(y_true, y_pred, label):
    mae      = mean_absolute_error(y_true, y_pred)
    mse      = mean_squared_error(y_true, y_pred)
    rmse     = np.sqrt(mse)
    r2       = r2_score(y_true, y_pred)
    mape     = np.mean(np.abs((y_true - y_pred) / np.clip(np.abs(y_true), 1e-8, None))) * 100
    within_1 = np.mean(np.abs(y_true - y_pred) <= 1.0) * 100
    within_2 = np.mean(np.abs(y_true - y_pred) <= 2.0) * 100
    within_5 = np.mean(np.abs(y_true - y_pred) <= 5.0) * 100

    print(f"\n  ── {label} ──")
    print(f"  MAE          : {mae:.4f} days  (avg error)")
    print(f"  RMSE         : {rmse:.4f} days  (penalises large errors)")
    print(f"  MSE          : {mse:.4f}")
    print(f"  R² Score     : {r2:.4f}        (1.0 = perfect)")
    print(f"  MAPE         : {mape:.2f}%      (% error relative to true value)")
    print(f"  Within 1 day : {within_1:.1f}%")
    print(f"  Within 2 days: {within_2:.1f}%")
    print(f"  Within 5 days: {within_5:.1f}%")

    return {
        "mae": mae, "rmse": rmse, "mse": mse,
        "r2": r2, "mape": mape,
        "within_1": within_1, "within_2": within_2, "within_5": within_5
    }

print("\n" + "=" * 55)
train_metrics = compute_metrics(y_train, y_pred_train, "TRAINING SET")
val_metrics   = compute_metrics(y_val,   y_pred_val,   "VALIDATION SET")
print("\n" + "=" * 55)

print("\n🔹 Overfitting Check:")
mae_gap = val_metrics["mae"] - train_metrics["mae"]
if mae_gap < 1.0:
    print(f"  ✅ Good generalisation (MAE gap = {mae_gap:.3f} days)")
elif mae_gap < 3.0:
    print(f"  ⚠️  Mild overfitting (MAE gap = {mae_gap:.3f} days) — consider more data or dropout")
else:
    print(f"  ❌ Significant overfitting (MAE gap = {mae_gap:.3f} days) — model memorising training data")

print("\n🔹 Generating evaluation plots...")

fig = plt.figure(figsize=(16, 12))
fig.suptitle("ShelfNet LSTM — Model Evaluation", fontsize=15, fontweight="bold")
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.35)

ax1 = fig.add_subplot(gs[0, 0])
ax1.scatter(y_val, y_pred_val, alpha=0.4, s=15, color="#2196F3")
lims = [min(y_val.min(), y_pred_val.min()), max(y_val.max(), y_pred_val.max())]
ax1.plot(lims, lims, "r--", linewidth=1.5, label="Perfect prediction")
ax1.set_xlabel("Actual (days)")
ax1.set_ylabel("Predicted (days)")
ax1.set_title("Actual vs Predicted\n(Validation)")
ax1.legend(fontsize=8)

residuals = y_val - y_pred_val
ax2 = fig.add_subplot(gs[0, 1])
ax2.scatter(y_pred_val, residuals, alpha=0.4, s=15, color="#FF9800")
ax2.axhline(0, color="red", linestyle="--", linewidth=1.5)
ax2.set_xlabel("Predicted (days)")
ax2.set_ylabel("Residual (Actual − Predicted)")
ax2.set_title("Residual Plot\n(Validation)")

ax3 = fig.add_subplot(gs[0, 2])
ax3.hist(residuals, bins=30, color="#4CAF50", edgecolor="white", alpha=0.85)
ax3.axvline(0, color="red", linestyle="--", linewidth=1.5)
ax3.set_xlabel("Residual (days)")
ax3.set_ylabel("Count")
ax3.set_title("Residual Distribution\n(Validation)")

ax4 = fig.add_subplot(gs[1, 0:2])
n = min(200, len(y_val))
ax4.plot(y_val[:n],      label="Actual",    color="#2196F3", linewidth=1.2)
ax4.plot(y_pred_val[:n], label="Predicted", color="#F44336", linewidth=1.2, linestyle="--")
ax4.set_xlabel("Sample index")
ax4.set_ylabel("Shelf life (days)")
ax4.set_title(f"Actual vs Predicted over Time — first {n} validation samples")
ax4.legend(fontsize=9)

ax5 = fig.add_subplot(gs[1, 2])
categories = ["Within\n1 day", "Within\n2 days", "Within\n5 days"]
train_vals = [train_metrics["within_1"], train_metrics["within_2"], train_metrics["within_5"]]
val_vals   = [val_metrics["within_1"],   val_metrics["within_2"],   val_metrics["within_5"]]
x = np.arange(len(categories))
w = 0.35
ax5.bar(x - w/2, train_vals, w, label="Train", color="#4CAF50", alpha=0.85)
ax5.bar(x + w/2, val_vals,   w, label="Val",   color="#2196F3", alpha=0.85)
ax5.set_xticks(x)
ax5.set_xticklabels(categories, fontsize=9)
ax5.set_ylabel("% of predictions")
ax5.set_ylim(0, 105)
ax5.set_title("Within-N-Days Accuracy")
ax5.legend(fontsize=9)
for i, (tv, vv) in enumerate(zip(train_vals, val_vals)):
    ax5.text(i - w/2, tv + 1, f"{tv:.0f}%", ha="center", fontsize=8)
    ax5.text(i + w/2, vv + 1, f"{vv:.0f}%", ha="center", fontsize=8)

out_path = os.path.join(BASE_DIR, "evaluation_report.png")
plt.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"  ✅ Plot saved to: {out_path}")
plt.show()

print("\n✅ Evaluation complete.")