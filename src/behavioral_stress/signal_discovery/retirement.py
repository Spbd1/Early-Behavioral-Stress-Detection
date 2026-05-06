"""Signal drift and retirement-screening utilities.

These diagnostics are intentionally conservative: they flag a signal for human
review only.  They never delete, drop, or retire a feature automatically.
Operational thresholds should be selected inside rolling-origin or nested
validation, not tuned on a final test set.
"""
from __future__ import annotations

import math
from typing import Iterable

_EPS = 1e-9


def kl_divergence_gaussian(old: Iterable[float], new: Iterable[float]) -> float:
    """Return KL divergence ``KL(old || new)`` for fitted univariate Gaussians.

    Non-finite observations are ignored.  Empty windows use a unit-variance zero
    mean fallback, and variances are floored so valid numeric inputs always
    produce a finite, nonnegative divergence.
    """
    old_values = _finite_values(old)
    new_values = _finite_values(new)
    old_mean, old_var = _mean_var(old_values)
    new_mean, new_var = _mean_var(new_values)
    old_var = max(old_var, _EPS)
    new_var = max(new_var, _EPS)

    divergence = 0.5 * (
        math.log(new_var / old_var)
        + (old_var + (old_mean - new_mean) ** 2) / new_var
        - 1.0
    )
    if not math.isfinite(divergence):
        return math.inf
    return max(0.0, divergence)


def flag_signal_retirement(
    old: Iterable[float],
    new: Iterable[float],
    threshold: float = 0.5,
) -> dict[str, float | bool | str]:
    """Flag distribution drift for human review without automatic deletion.

    The threshold is assumed to have been selected during rolling-origin or
    nested validation.  This helper reports diagnostics and review status only;
    downstream code must make any feature-governance decision explicitly.
    """
    if threshold < 0 or not math.isfinite(float(threshold)):
        raise ValueError("threshold must be a finite nonnegative value selected during validation")

    score = kl_divergence_gaussian(old, new)
    flag_for_review = bool(score >= threshold)
    return {
        "kl_divergence": score,
        "threshold": float(threshold),
        "flag_for_review": flag_for_review,
        "human_review_required": flag_for_review,
        "automatic_deletion": False,
        "retire_automatically": False,
        "recommended_action": "human_review" if flag_for_review else "monitor",
        "threshold_selection": "rolling_origin_or_nested_validation_not_final_test",
    }


def _finite_values(values: Iterable[float]) -> list[float]:
    return [float(value) for value in values if math.isfinite(float(value))]


def _mean_var(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 1.0
    mean = sum(values) / len(values)
    var = sum((value - mean) ** 2 for value in values) / len(values)
    return mean, max(var, _EPS)
