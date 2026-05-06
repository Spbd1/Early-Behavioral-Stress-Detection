"""Validation metrics for regime-detection experiments."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)


def binary_classification_metrics(y_true: np.ndarray, y_score: np.ndarray, threshold: float = 0.5) -> dict[str, float]:
    """Compute common binary metrics with safe handling of degenerate examples."""
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score, dtype=float)
    y_pred = (y_score >= threshold).astype(int)
    metrics = {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "brier_score": float(brier_score_loss(y_true, y_score)),
    }
    metrics["pr_auc"] = float(average_precision_score(y_true, y_score)) if len(np.unique(y_true)) > 1 else float("nan")
    metrics["roc_auc"] = float(roc_auc_score(y_true, y_score)) if len(np.unique(y_true)) > 1 else float("nan")
    false_positives = np.sum((y_pred == 1) & (y_true == 0))
    negatives = np.sum(y_true == 0)
    metrics["false_positive_rate"] = float(false_positives / negatives) if negatives else float("nan")
    return metrics


def lead_time(first_signal_index: int | None, event_index: int) -> int | None:
    """Return lead time in time steps; positive values indicate a signal before event."""
    if first_signal_index is None:
        return None
    return int(event_index - first_signal_index)


def out_of_sample_log_predictive_density(log_likelihoods: np.ndarray) -> float:
    """Average log predictive density over held-out observations."""
    return float(np.mean(log_likelihoods))
