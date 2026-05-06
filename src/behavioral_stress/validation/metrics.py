"""Validation metrics for synthetic latent-regime experiments."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, precision_score, recall_score, roc_auc_score


def binary_classification_metrics(y_true: np.ndarray, y_score: np.ndarray, threshold: float = 0.5) -> dict[str, float]:
    """Compute binary metrics with safe handling for degenerate labels."""
    y_true = np.asarray(y_true).astype(int)
    y_score = np.clip(np.asarray(y_score, dtype=float), 0.0, 1.0)
    y_pred = (y_score >= threshold).astype(int)
    out = {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "brier_score": float(brier_score_loss(y_true, y_score)),
    }
    out["pr_auc"] = float(average_precision_score(y_true, y_score)) if len(np.unique(y_true)) > 1 else float("nan")
    out["roc_auc"] = float(roc_auc_score(y_true, y_score)) if len(np.unique(y_true)) > 1 else float("nan")
    fp = float(np.sum((y_pred == 1) & (y_true == 0)))
    negatives = float(np.sum(y_true == 0))
    out["false_positive_rate"] = fp / negatives if negatives else float("nan")
    return out


def calibration_brier_score(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Return Brier score as a simple calibration diagnostic."""
    return float(brier_score_loss(np.asarray(y_true).astype(int), np.clip(y_score, 0, 1)))


def out_of_sample_log_predictive_density(log_likelihoods: np.ndarray) -> float:
    """Average held-out log predictive density."""
    return float(np.mean(log_likelihoods))


def lead_time(first_signal_index: int | None, event_index: int) -> int | None:
    """Return positive lead time when the signal precedes the synthetic event."""
    return None if first_signal_index is None else int(event_index - first_signal_index)


def feature_stability(old_ranks: list[str], new_ranks: list[str], top_k: int = 10) -> float:
    """Compute top-k overlap as a lightweight feature-stability metric."""
    old_top = set(old_ranks[:top_k])
    new_top = set(new_ranks[:top_k])
    return float(len(old_top & new_top) / max(1, len(old_top | new_top)))
