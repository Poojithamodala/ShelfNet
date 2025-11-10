import os
import io
import json
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import pandas as pd
import numpy as np
from .predict import predict_sequences

app = Flask(__name__)
app.secret_key = os.environ.get("SHELFNET_SECRET", "dev-secret")

ARTIFACTS_DIR = os.environ.get("SHELFNET_ARTIFACTS", os.path.join(os.path.dirname(__file__), "..", "artifacts"))
THRESHOLD_DEFAULT = float(os.environ.get("SHELFNET_THRESHOLD", 24.0))


@app.route("/")
def index():
    metrics = None
    metrics_path = os.path.join(ARTIFACTS_DIR, "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics = json.load(f)
    return render_template("index.html", metrics=metrics, threshold=THRESHOLD_DEFAULT)


@app.route("/predict", methods=["POST"]) 
def predict():
    if "file" not in request.files:
        flash("No file uploaded")
        return redirect(url_for("index"))
    f = request.files["file"]
    if f.filename == "":
        flash("No file selected")
        return redirect(url_for("index"))
    threshold = float(request.form.get("threshold", THRESHOLD_DEFAULT))
    fruit_filter = request.form.get("fruit_filter", "")
    tmp_path = os.path.join("/tmp" if os.name != "nt" else os.environ.get("TEMP", "."), f.filename)
    f.save(tmp_path)
    try:
        pred_df = predict_sequences(tmp_path, ARTIFACTS_DIR)
    except Exception as e:
        flash(f"Error during prediction: {e}")
        return redirect(url_for("index"))
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

    # Harmonize columns
    if "fruit" not in pred_df.columns and "fruit_type" in pred_df.columns:
        pred_df = pred_df.rename(columns={"fruit_type": "fruit"})
    if "timestamp" not in pred_df.columns and "time_step" in pred_df.columns:
        pred_df["timestamp"] = pred_df["time_step"].astype(str)

    # Apply fruit filter if provided
    if fruit_filter:
        pred_df = pred_df[pred_df["fruit"].astype(str) == fruit_filter]

    # Risk and alerts
    pred_df["alert"] = pred_df["predicted_shelf_life"] < threshold
    warn_lo = threshold
    warn_hi = threshold * 1.5
    def risk_level(v: float) -> str:
        if v < warn_lo:
            return "critical"
        if v < warn_hi:
            return "warning"
        return "safe"
    pred_df["risk"] = pred_df["predicted_shelf_life"].apply(risk_level)

    # Metrics
    total_items = int(len(pred_df))
    avg_shelf = float(np.nanmean(pred_df["predicted_shelf_life"])) if total_items else 0.0
    alerts_count = int(pred_df["alert"].sum())

    # Aggregations
    fruit_col = "fruit" if "fruit" in pred_df.columns else ("fruit_type" if "fruit_type" in pred_df.columns else None)
    agg = []
    if fruit_col:
        agg = pred_df.groupby(fruit_col)["predicted_shelf_life"].agg(["mean", "min", "max"]).reset_index().rename(columns={fruit_col: "fruit"}).to_dict(orient="records")

    # Chart data
    labels = pred_df["timestamp"].astype(str).tolist()
    values = pred_df["predicted_shelf_life"].round(2).tolist()
    colors = [
        "#dc2626" if r == "critical" else ("#f59e0b" if r == "warning" else "#16a34a")
        for r in pred_df["risk"].tolist()
    ]
    chart = {"labels": labels, "values": values, "colors": colors}

    # Bar chart: alerts per fruit
    bar = {"labels": [], "values": []}
    if fruit_col:
        grp = pred_df.groupby(fruit_col)["alert"].sum().reset_index()
        bar = {"labels": grp[fruit_col].astype(str).tolist(), "values": grp["alert"].astype(int).tolist()}

    # Optional scatter for sensor trends if available
    sensor_cols = [
        c for c in [
            "temperature_c","humidity_pct","ethylene_ppm","co2_ppm","o2_pct","vibration_ms2","light_lux"
        ] if c in pred_df.columns
    ]
    scatter = {"labels": labels, "series": []}
    for c in sensor_cols:
        scatter["series"].append({"name": c, "values": pred_df[c].astype(float).round(3).tolist()})

    # Build preview and unique fruits for filter
    preview = pred_df.head(500).to_dict(orient="records")
    fruits = sorted(pred_df["fruit"].dropna().astype(str).unique().tolist()) if fruit_col else []

    # Save predictions for download endpoints
    batch_id = str(uuid.uuid4())
    tmp_dir = os.path.join("/tmp" if os.name != "nt" else os.environ.get("TEMP", "."), "shelfnet")
    os.makedirs(tmp_dir, exist_ok=True)
    csv_path = os.path.join(tmp_dir, f"{batch_id}.csv")
    xlsx_path = os.path.join(tmp_dir, f"{batch_id}.xlsx")
    try:
        pred_df.to_csv(csv_path, index=False)
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            pred_df.to_excel(writer, index=False, sheet_name="predictions")
    except Exception:
        pass

    return render_template(
        "index.html",
        metrics={
            "total_items": total_items,
            "avg_shelf": avg_shelf,
            "alerts": alerts_count,
        },
        predictions=preview,
        alerts=alerts_count,
        threshold=threshold,
        agg=agg,
        chart=chart,
        bar=bar,
        scatter=scatter,
        fruits=fruits,
        selected_fruit=fruit_filter,
        batch_id=batch_id,
    )


@app.route("/download/<batch_id>.csv")
def download_csv(batch_id: str):
    tmp_dir = os.path.join("/tmp" if os.name != "nt" else os.environ.get("TEMP", "."), "shelfnet")
    path = os.path.join(tmp_dir, f"{batch_id}.csv")
    if not os.path.exists(path):
        flash("File not found")
        return redirect(url_for("index"))
    return send_file(path, as_attachment=True, download_name="predictions.csv")


@app.route("/download/<batch_id>.xlsx")
def download_xlsx(batch_id: str):
    tmp_dir = os.path.join("/tmp" if os.name != "nt" else os.environ.get("TEMP", "."), "shelfnet")
    path = os.path.join(tmp_dir, f"{batch_id}.xlsx")
    if not os.path.exists(path):
        flash("File not found")
        return redirect(url_for("index"))
    return send_file(path, as_attachment=True, download_name="predictions.xlsx")
