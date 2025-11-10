from typing import Tuple
import numpy as np
from sklearn.metrics import mean_squared_error, r2_score


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(r2_score(y_true, y_pred))


def regression_report(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float]:
    return rmse(y_true, y_pred), r2(y_true, y_pred)
