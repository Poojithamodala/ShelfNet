import os
import json
import numpy as np
import pandas as pd
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
import joblib


@dataclass
class PreprocessConfig:
    timestamp_col: str = "time_step"
    fruit_col: str = "fruit"
    numeric_cols: Tuple[str, ...] = (
        "temperature_c",
        "humidity_pct",
        "ethylene_ppm",
        "co2_ppm",
        "o2_pct",
        "vibration_ms2",
        "light_lux",
        "door_open_count",
    )
    target_col: str = "remaining_shelf_life"
    lookback: int = 24
    test_size: float = 0.2
    random_state: int = 42


def load_dataset(path: str, cfg: PreprocessConfig) -> pd.DataFrame:
    # Read CSV or Excel
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    # Normalize original column names for matching (lowercase, strip spaces, remove underscores)
    original_cols = list(df.columns)
    def _norm(s: str) -> str:
        return "".join(ch for ch in s.lower().strip() if ch.isalnum())
    norm_map = {c: _norm(c) for c in original_cols}

    def _find_col(candidates: Tuple[str, ...]) -> Optional[str]:
        cand_norm = tuple(_norm(c) for c in candidates)
        for orig, norm in norm_map.items():
            if norm in cand_norm:
                return orig
        return None

    # Derive/rename to internal schema
    mapping = {}
    # Fruit
    fruit_col = _find_col(("fruit", "fruit_type"))
    if fruit_col:
        mapping[fruit_col] = "fruit"
    # Time step
    step_col = _find_col(("timestep", "time_step", "step", "dayindex", "day", "index"))
    if step_col is None:
        # Try to extract from a label-like timestamp e.g., "Day_1"
        ts_label = _find_col(("timestampday1day2", "timestampday", "timestamp"))
        if ts_label and ts_label in df.columns:
            # Create numeric time_step by extracting trailing integer
            df["time_step"] = pd.to_numeric(df[ts_label].astype(str).str.extract(r"(\d+)$")[0], errors="coerce")
        else:
            step_col = None
    if step_col:
        mapping[step_col] = "time_step"

    # Timestamps (optional). If present, keep as 'timestamp' for potential downstream use
    ts_col = _find_col(("timestamp", "time", "datetime"))
    if ts_col:
        mapping[ts_col] = "timestamp"

    # Numeric sensors with units
    col_specs = [
        (("temperaturec", "temperature", "temp"), "temperature_c"),
        (("humidity", "humiditypct"), "humidity_pct"),
        (("ethyleneppm", "ethylene"), "ethylene_ppm"),
        (("co2ppm", "co2"), "co2_ppm"),
        (("o2level", "o2", "o2pct"), "o2_pct"),
        (("vibrationlevelms2", "vibration", "vibrationms2"), "vibration_ms2"),
        (("lightintensitylux", "light", "lightlux"), "light_lux"),
        (("storagedooropencount", "dooropencount", "door_open_count"), "door_open_count"),
    ]
    for cands, target in col_specs:
        col = _find_col(cands)
        if col:
            mapping[col] = target

    # Categorical power status
    pwr_col = _find_col(("powersupplystatus", "powerstatus"))
    if pwr_col:
        mapping[pwr_col] = "power_status"

    if mapping:
        df = df.rename(columns=mapping)

    # Validate required columns
    if cfg.fruit_col not in df.columns:
        raise ValueError(f"Missing required column: {cfg.fruit_col}")

    # If time_step exists ensure numeric; if missing, create from order within fruit
    if cfg.timestamp_col in df.columns:
        df[cfg.timestamp_col] = pd.to_numeric(df[cfg.timestamp_col], errors="coerce")
    else:
        df[cfg.timestamp_col] = df.groupby(cfg.fruit_col).cumcount()

    # Auto-create target if absent
    if cfg.target_col not in df.columns and cfg.timestamp_col in df.columns:
        max_per_fruit = df.groupby(cfg.fruit_col)[cfg.timestamp_col].transform("max")
        df[cfg.target_col] = (max_per_fruit - df[cfg.timestamp_col]).astype(float)

    # Sort deterministically for sequence construction
    df = df.sort_values(by=[cfg.fruit_col, cfg.timestamp_col]).reset_index(drop=True)
    return df


def build_preprocess_pipeline(df: pd.DataFrame, cfg: PreprocessConfig) -> ColumnTransformer:
    cat_cols = [c for c in [cfg.fruit_col, "power_status"] if c in df.columns]
    num_cols = [c for c in cfg.numeric_cols if c in df.columns]
    transformers = []
    if len(cat_cols) > 0:
        transformers.append(("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols))
    if len(num_cols) > 0:
        transformers.append(("num", StandardScaler(), num_cols))
    pre = ColumnTransformer(transformers=transformers, remainder="drop")
    return pre


def fit_transformers(df: pd.DataFrame, cfg: PreprocessConfig, artifacts_dir: str) -> Tuple[np.ndarray, Optional[np.ndarray], ColumnTransformer]:
    pre = build_preprocess_pipeline(df, cfg)
    cat_cols = [c for c in [cfg.fruit_col, "power_status"] if c in df.columns]
    features = cat_cols + [c for c in cfg.numeric_cols if c in df.columns]
    X = pre.fit_transform(df[features])
    y = None
    if cfg.target_col in df.columns:
        y = df[cfg.target_col].values.astype(np.float32)
    os.makedirs(artifacts_dir, exist_ok=True)
    joblib.dump(pre, os.path.join(artifacts_dir, "preprocess.joblib"))
    meta = {
        "features": features,
        "timestamp_col": cfg.timestamp_col,
        "fruit_col": cfg.fruit_col,
        "target_col": cfg.target_col,
        "lookback": cfg.lookback,
    }
    with open(os.path.join(artifacts_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    return X, y, pre


def transform_with_loaded(df: pd.DataFrame, artifacts_dir: str) -> Tuple[np.ndarray, Dict]:
    pre = joblib.load(os.path.join(artifacts_dir, "preprocess.joblib"))
    with open(os.path.join(artifacts_dir, "config.json"), "r", encoding="utf-8") as f:
        meta = json.load(f)
    features = meta["features"]
    X = pre.transform(df[features])
    return X, meta


def build_sequences(
    df: pd.DataFrame,
    X: np.ndarray,
    y: Optional[np.ndarray],
    cfg: PreprocessConfig,
) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    lookback = cfg.lookback
    sequences = []
    targets = [] if y is not None else None

    # group per fruit type to avoid mixing categories across sequences
    groups = df[cfg.fruit_col].values
    unique, idx = np.unique(groups, return_inverse=True)

    for g in range(len(unique)):
        mask = idx == g
        locs = np.nonzero(mask)[0]
        if len(locs) == 0:
            continue
        # contiguous block
        block_x = X[locs]
        block_y = y[locs] if y is not None else None
        for i in range(len(block_x) - lookback):
            window = block_x[i : i + lookback]
            sequences.append(window)
            if targets is not None:
                targets.append(block_y[i + lookback])
    x_seq = np.stack(sequences).astype(np.float32) if sequences else np.empty((0, lookback, X.shape[1]), dtype=np.float32)
    y_seq = np.array(targets, dtype=np.float32) if targets is not None else None
    return x_seq, y_seq


def train_val_split(X: np.ndarray, y: np.ndarray, test_size: float, random_state: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    return train_test_split(X, y, test_size=test_size, random_state=random_state, shuffle=True)
