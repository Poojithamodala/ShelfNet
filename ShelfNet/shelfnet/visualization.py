import io
import base64
import numpy as np
import matplotlib.pyplot as plt


def plot_true_vs_pred(y_true, y_pred, title="True vs Pred"):
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(y_true, y_pred, alpha=0.6)
    lims = [min(np.min(y_true), np.min(y_pred)), max(np.max(y_true), np.max(y_pred))]
    ax.plot(lims, lims, 'k--', alpha=0.7)
    ax.set_xlabel("True")
    ax.set_ylabel("Pred")
    ax.set_title(title)
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('ascii')
