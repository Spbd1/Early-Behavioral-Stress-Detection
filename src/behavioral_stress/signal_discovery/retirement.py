"""Signal drift and retirement-review diagnostics."""
from __future__ import annotations

import numpy as np


def kl_divergence_gaussian(old_values: np.ndarray, new_values: np.ndarray, eps: float = 1e-8) -> float:
    """Estimate ``D_KL(N_old || N_new)`` for one-dimensional Gaussian approximations."""
    old = np.asarray(old_values, dtype=float)
    new = np.asarray(new_values, dtype=float)
    mu0, mu1 = old.mean(), new.mean()
    var0, var1 = old.var() + eps, new.var() + eps
    score = 0.5 * (np.log(var1 / var0) + (var0 + (mu0 - mu1) ** 2) / var1 - 1)
    return float(max(score, 0.0))


def flag_signal_retirement(
    old_values: np.ndarray,
    new_values: np.ndarray,
    threshold: float = 0.5,
) -> dict[str, float | bool | str]:
    """Flag KL drift for human review only; never automatically delete features.

    The threshold should be selected inside rolling-origin or nested validation.
    """
    score = kl_divergence_gaussian(old_values, new_values)
    return {
        "kl_divergence": score,
        "flag_for_review": bool(score > threshold),
        "note": "Review flag only; do not automatically retire or delete aggregate features.",
    }
