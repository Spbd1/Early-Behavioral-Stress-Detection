"""Validation metric helpers for binary stress-signal evaluation.

Thresholds used by these helpers should be chosen inside rolling-origin or
nested validation folds.  The final test split should only be used once to
report metrics for a pre-selected threshold.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

_EPS = 1e-15


def binary_classification_metrics(
    y_true: Iterable[float],
    y_score: Iterable[float],
    threshold: float = 0.5,
    *,
    baseline_feature: Iterable[float] | None = None,
    current_feature: Iterable[float] | None = None,
) -> dict[str, float]:
    """Return standard validation metrics for binary probabilistic forecasts.

    Degenerate label sets are handled explicitly: ROC-AUC returns ``0.5`` when
    only one class is present, and PR-AUC returns ``1.0`` for all-positive labels
    and ``0.0`` for all-negative labels.  This keeps validation summaries finite
    while making the degeneracy visible to callers.
    """
    truth, scores = _prepare_binary_inputs(y_true, y_score)
    preds = [1 if score >= threshold else 0 for score in scores]

    return {
        "precision": precision(truth, preds),
        "recall": recall(truth, preds),
        "false_positive_rate": false_positive_rate(truth, preds),
        "roc_auc": roc_auc(truth, scores),
        "pr_auc": pr_auc(truth, scores),
        "average_precision": pr_auc(truth, scores),
        "brier_score": brier_score(truth, scores),
        "log_predictive_density": out_of_sample_log_predictive_density(truth, scores),
        "lead_time": simple_lead_time(truth, scores, threshold=threshold),
        "feature_stability": feature_stability_metric(baseline_feature, current_feature),
    }


def precision(y_true: Iterable[float], y_pred: Iterable[float], threshold: float = 0.5) -> float:
    """Return positive predictive value for binary labels and predictions."""
    truth, pred = _prepare_binary_inputs(y_true, y_pred, score_threshold=threshold)
    tp = sum(
        1 for target, prediction in zip(truth, pred, strict=True) if target == 1 and prediction == 1
    )
    fp = sum(
        1 for target, prediction in zip(truth, pred, strict=True) if target == 0 and prediction == 1
    )
    return tp / (tp + fp) if tp + fp else 0.0


def recall(y_true: Iterable[float], y_pred: Iterable[float], threshold: float = 0.5) -> float:
    """Return sensitivity for binary labels and predictions."""
    truth, pred = _prepare_binary_inputs(y_true, y_pred, score_threshold=threshold)
    tp = sum(
        1 for target, prediction in zip(truth, pred, strict=True) if target == 1 and prediction == 1
    )
    fn = sum(
        1 for target, prediction in zip(truth, pred, strict=True) if target == 1 and prediction == 0
    )
    return tp / (tp + fn) if tp + fn else 0.0


def false_positive_rate(
    y_true: Iterable[float], y_pred: Iterable[float], threshold: float = 0.5
) -> float:
    """Return the false-positive rate for binary labels and predictions."""
    truth, pred = _prepare_binary_inputs(y_true, y_pred, score_threshold=threshold)
    fp = sum(
        1 for target, prediction in zip(truth, pred, strict=True) if target == 0 and prediction == 1
    )
    tn = sum(
        1 for target, prediction in zip(truth, pred, strict=True) if target == 0 and prediction == 0
    )
    return fp / (fp + tn) if fp + tn else 0.0


def roc_auc(y_true: Iterable[float], y_score: Iterable[float]) -> float:
    """Return rank-based ROC-AUC with a finite degenerate-label fallback."""
    truth, scores = _prepare_binary_inputs(y_true, y_score)
    positives = [score for target, score in zip(truth, scores, strict=True) if target == 1]
    negatives = [score for target, score in zip(truth, scores, strict=True) if target == 0]
    if not positives or not negatives:
        return 0.5

    wins = 0.0
    for pos_score in positives:
        for neg_score in negatives:
            if pos_score > neg_score:
                wins += 1.0
            elif pos_score == neg_score:
                wins += 0.5
    return wins / (len(positives) * len(negatives))


def pr_auc(y_true: Iterable[float], y_score: Iterable[float]) -> float:
    """Return average-precision PR-AUC with finite degenerate-label handling."""
    truth, scores = _prepare_binary_inputs(y_true, y_score)
    total_pos = sum(truth)
    if total_pos == 0:
        return 0.0
    if total_pos == len(truth):
        return 1.0

    pairs = sorted(zip(scores, truth, strict=True), key=lambda item: item[0], reverse=True)
    hits = 0
    precision_sum = 0.0
    for rank, (_, target) in enumerate(pairs, start=1):
        if target:
            hits += 1
            precision_sum += hits / rank
    return precision_sum / total_pos


def brier_score(y_true: Iterable[float], y_score: Iterable[float]) -> float:
    """Return the mean squared error of probabilistic binary forecasts."""
    truth, scores = _prepare_binary_inputs(y_true, y_score)
    if not scores:
        return 0.0
    return sum(
        (_clip_probability(score) - target) ** 2
        for target, score in zip(truth, scores, strict=True)
    ) / len(scores)


def out_of_sample_log_predictive_density(
    y_true: Iterable[float], y_score: Iterable[float]
) -> float:
    """Return mean held-out Bernoulli log predictive density."""
    truth, scores = _prepare_binary_inputs(y_true, y_score)
    if not scores:
        return 0.0
    log_density = 0.0
    for target, score in zip(truth, scores, strict=True):
        probability = _clip_probability(score)
        log_density += math.log(probability) if target == 1 else math.log1p(-probability)
    return log_density / len(scores)


def simple_lead_time(
    y_true: Iterable[float], y_score: Iterable[float], threshold: float = 0.5
) -> float:
    """Return periods by which the first alarm precedes the first event.

    A positive value means the first threshold crossing occurred before the first
    positive label.  A zero value means there was no useful lead time; alarms
    after the first event are not credited.
    """
    truth, scores = _prepare_binary_inputs(y_true, y_score)
    first_event = next((idx for idx, target in enumerate(truth) if target == 1), None)
    if first_event is None:
        return 0.0
    first_alarm = next((idx for idx, score in enumerate(scores) if score >= threshold), None)
    if first_alarm is None or first_alarm > first_event:
        return 0.0
    return float(first_event - first_alarm)


def feature_stability_metric(
    baseline_feature: Iterable[float] | None,
    current_feature: Iterable[float] | None,
) -> float:
    """Return a simple finite stability score in ``[0, 1]`` for one feature.

    The score is ``1`` when the two windows have identical means and decreases as
    their standardized mean difference grows.  Missing windows return ``1`` so
    that optional use inside aggregate metric reporting remains non-disruptive.
    """
    if baseline_feature is None or current_feature is None:
        return 1.0
    baseline = _finite_values(baseline_feature)
    current = _finite_values(current_feature)
    if not baseline or not current:
        return 1.0

    baseline_mean, baseline_var = _mean_var(baseline)
    current_mean, current_var = _mean_var(current)
    pooled_scale = math.sqrt(max((baseline_var + current_var) / 2.0, _EPS))
    standardized_shift = abs(current_mean - baseline_mean) / pooled_scale
    return 1.0 / (1.0 + standardized_shift)


def _prepare_binary_inputs(
    y_true: Iterable[float],
    y_score: Iterable[float],
    *,
    score_threshold: float | None = None,
) -> tuple[list[int], list[float]]:
    truth = [1 if float(value) >= 0.5 else 0 for value in y_true]
    scores = [float(value) for value in y_score]
    if score_threshold is not None:
        scores = [1.0 if score >= score_threshold else 0.0 for score in scores]
    if len(truth) != len(scores):
        raise ValueError("y_true and y_score must have the same length")
    return truth, scores


def _finite_values(values: Iterable[float]) -> list[float]:
    return [float(value) for value in values if math.isfinite(float(value))]


def _clip_probability(value: float) -> float:
    return min(max(float(value), _EPS), 1.0 - _EPS)


def _mean_var(values: Sequence[float]) -> tuple[float, float]:
    mean = sum(values) / len(values)
    var = sum((value - mean) ** 2 for value in values) / len(values)
    return mean, var


# Backward-compatible private aliases used by earlier tests and notebooks.
def _roc_auc(truth: list[int], scores: list[float]) -> float:
    return roc_auc(truth, scores)


def _average_precision(truth: list[int], scores: list[float]) -> float:
    return pr_auc(truth, scores)


def oos_log_predictive_density(y_true: Iterable[float], y_score: Iterable[float]) -> float:
    """Alias for out-of-sample log predictive density."""
    return out_of_sample_log_predictive_density(y_true, y_score)


def lead_time_metric(
    y_true: Iterable[float], y_score: Iterable[float], threshold: float = 0.5
) -> float:
    """Alias for the simple lead-time metric."""
    return simple_lead_time(y_true, y_score, threshold=threshold)


def feature_stability(
    baseline_feature: Iterable[float] | None,
    current_feature: Iterable[float] | None,
) -> float:
    """Alias for the simple feature-stability metric."""
    return feature_stability_metric(baseline_feature, current_feature)
