import os
import argparse
import json
import pandas as pd
import numpy as np
import torch
from .data import PreprocessConfig, load_dataset, transform_with_loaded, build_sequences
from .model import LSTMRegressor


def load_meta(artifacts: str):
    with open(os.path.join(artifacts, "config.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def predict_sequences(csv_path: str, artifacts: str) -> pd.DataFrame:
    meta = load_meta(artifacts)
    cfg = PreprocessConfig(
        timestamp_col=meta["timestamp_col"],
        fruit_col=meta["fruit_col"],
        target_col=meta.get("target_col", "remaining_shelf_life"),
        lookback=int(meta["lookback"]),
    )
    df = load_dataset(csv_path, cfg)
    x_tab, _ = transform_with_loaded(df, artifacts)

    x_seq, _ = build_sequences(df, x_tab, None, cfg)
    if len(x_seq) == 0:
        raise ValueError("Not enough data to build sequences; check lookback and dataset size")

    input_dim = x_seq.shape[-1]
    model = LSTMRegressor(input_dim=input_dim)
    model.load_state_dict(torch.load(os.path.join(artifacts, "model.pth"), map_location="cpu"))
    model.eval()

    with torch.no_grad():
        preds = model(torch.from_numpy(x_seq)).numpy()

    # align predictions back to rows; each pred corresponds to window end
    end_idx = np.arange(cfg.lookback, cfg.lookback + len(preds))
    out = df.iloc[end_idx].copy().reset_index(drop=True)
    out["predicted_shelf_life"] = preds
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="Path to dataset (.csv or .xlsx) for inference")
    ap.add_argument("--artifacts", default="artifacts")
    ap.add_argument("--out", default="predictions.csv")
    ap.add_argument("--threshold", type=float, default=24.0)
    args = ap.parse_args()

    pred_df = predict_sequences(args.data, args.artifacts)
    pred_df["alert"] = pred_df["predicted_shelf_life"] < args.threshold
    pred_df.to_csv(args.out, index=False)
    print(f"Saved predictions to {args.out}. Alerts: {pred_df['alert'].sum()} / {len(pred_df)}")


if __name__ == "__main__":
    main()
