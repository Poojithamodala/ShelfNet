import os
import argparse
import json
import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset
from .data import PreprocessConfig, load_dataset, fit_transformers, build_sequences, train_val_split
from .model import LSTMRegressor
from .evaluate import regression_report
import joblib


def train_loop(model, train_loader, val_loader, device, epochs=20, lr=1e-3):
    model.to(device)
    optim = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    loss_fn = torch.nn.MSELoss()
    best_val = float('inf')
    best_state = None

    for ep in range(1, epochs + 1):
        model.train()
        total = 0.0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optim.zero_grad()
            pred = model(xb)
            loss = loss_fn(pred, yb)
            loss.backward()
            optim.step()
            total += loss.item() * xb.size(0)
        train_loss = total / len(train_loader.dataset)

        model.eval()
        with torch.no_grad():
            val_total = 0.0
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                pred = model(xb)
                loss = loss_fn(pred, yb)
                val_total += loss.item() * xb.size(0)
        val_loss = val_total / len(val_loader.dataset)
        if val_loss < best_val:
            best_val = val_loss
            best_state = {k: v.cpu() for k, v in model.state_dict().items()}
        print(f"Epoch {ep:03d} | train_loss={train_loss:.4f} val_loss={val_loss:.4f}")
    if best_state is not None:
        model.load_state_dict(best_state)
    return model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="Path to dataset (.csv or .xlsx)")
    ap.add_argument("--artifacts", default="artifacts", help="Dir to save model and preprocessors")
    ap.add_argument("--lookback", type=int, default=24)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--hidden", type=int, default=64)
    ap.add_argument("--layers", type=int, default=2)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--test-size", type=float, default=0.2)
    ap.add_argument("--target-col", default="remaining_shelf_life")
    args = ap.parse_args()

    cfg = PreprocessConfig(lookback=args.lookback, target_col=args.target_col)
    df = load_dataset(args.data, cfg)

    x_tab, y_vec, _ = fit_transformers(df, cfg, args.artifacts)
    if y_vec is None:
        raise ValueError(f"Target column '{cfg.target_col}' is required for training")

    x_seq, y_seq = build_sequences(df, x_tab, y_vec, cfg)
    if len(x_seq) == 0:
        raise ValueError("Not enough data to build sequences; check lookback and dataset size")

    x_train, x_val, y_train, y_val = train_val_split(x_seq, y_seq, args.test_size, 42)

    train_ds = TensorDataset(torch.from_numpy(x_train), torch.from_numpy(y_train))
    val_ds = TensorDataset(torch.from_numpy(x_val), torch.from_numpy(y_val))
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, num_workers=0)

    input_dim = x_seq.shape[-1]
    model = LSTMRegressor(input_dim=input_dim, hidden_dim=args.hidden, num_layers=args.layers)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = train_loop(model, train_loader, val_loader, device, epochs=args.epochs, lr=args.lr)

    model_path = os.path.join(args.artifacts, "model.pth")
    torch.save(model.state_dict(), model_path)

    # Evaluate
    model.eval()
    with torch.no_grad():
        y_true = torch.from_numpy(y_val).to(device)
        y_pred = model(torch.from_numpy(x_val).to(device))
        y_pred_np = y_pred.cpu().numpy()
        rmse_val, r2_val = regression_report(y_true.cpu().numpy(), y_pred_np)
    report = {"rmse": rmse_val, "r2": r2_val}
    with open(os.path.join(args.artifacts, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Saved model to {model_path}; RMSE={rmse_val:.4f}, R2={r2_val:.4f}")


if __name__ == "__main__":
    main()
