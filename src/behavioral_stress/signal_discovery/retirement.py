"""Signal drift and retirement-screening utilities."""
from __future__ import annotations

import math
from typing import Iterable


def kl_divergence_gaussian(old: Iterable[float], new: Iterable[float]) -> float:
    """Approximate KL divergence between univariate Gaussian summaries."""
    old_values = [float(value) for value in old]
    new_values = [float(value) for value in new]
    old_mean, old_var = _mean_var(old_values)
    new_mean, new_var = _mean_var(new_values)
    old_var = max(old_var, 1e-9)
    new_var = max(new_var, 1e-9)
    return max(0.0, 0.5 * (math.log(new_var / old_var) + (old_var + (old_mean - new_mean) ** 2) / new_var - 1.0))


def flag_signal_retirement(old: Iterable[float], new: Iterable[float], threshold: float = 0.5) -> dict[str, float | bool]:
    """Flag a signal for review when distribution drift exceeds a threshold."""
    score = kl_divergence_gaussian(old, new)
    return {"kl_divergence": score, "threshold": threshold, "flag_for_review": bool(score >= threshold)}


def _mean_var(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 1.0
    mean = sum(values) / len(values)
    var = sum((value - mean) ** 2 for value in values) / len(values)
    return mean, var or 1e-9
