"""Validation metric helpers implemented without third-party dependencies."""
from __future__ import annotations

from typing import Iterable


def binary_classification_metrics(y_true: Iterable[float], y_score: Iterable[float], threshold: float = 0.5) -> dict[str, float]:
    """Return precision, recall, Brier score, ROC AUC, and average precision."""
    truth = [1 if float(value) >= 0.5 else 0 for value in y_true]
    scores = [float(value) for value in y_score]
    pred = [1 if score >= threshold else 0 for score in scores]
    tp = sum(1 for t, p in zip(truth, pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(truth, pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(truth, pred) if t == 1 and p == 0)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    brier = sum((score - target) ** 2 for target, score in zip(truth, scores)) / len(scores) if scores else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "brier_score": brier,
        "roc_auc": _roc_auc(truth, scores),
        "average_precision": _average_precision(truth, scores),
    }


def _roc_auc(truth: list[int], scores: list[float]) -> float:
    positives = [score for target, score in zip(truth, scores) if target == 1]
    negatives = [score for target, score in zip(truth, scores) if target == 0]
    if not positives or not negatives:
        return 0.5
    wins = 0.0
    for pos in positives:
        for neg in negatives:
            wins += 1.0 if pos > neg else 0.5 if pos == neg else 0.0
    return wins / (len(positives) * len(negatives))


def _average_precision(truth: list[int], scores: list[float]) -> float:
    total_pos = sum(truth)
    if total_pos == 0:
        return 0.0
    pairs = sorted(zip(scores, truth), reverse=True)
    hits = 0
    precision_sum = 0.0
    for rank, (_, target) in enumerate(pairs, start=1):
        if target:
            hits += 1
            precision_sum += hits / rank
    return precision_sum / total_pos
