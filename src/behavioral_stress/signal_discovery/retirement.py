"""Signal drift and retirement-review diagnostics."""
from __future__ import annotations

import numpy as np
from scipy.special import rel_entr


def histogram_kl_divergence(old_values: np.ndarray, new_values: np.ndarray, bins: int = 20) -> float:
    """Estimate D_KL(P_old || P_new) with shared histogram bins."""
    combined = np.concatenate([old_values, new_values])
    counts_old, edges = np.histogram(old_values, bins=bins, range=(combined.min(), combined.max()))
    counts_new, _ = np.histogram(new_values, bins=edges)
    p_old = (counts_old + 1e-6) / (counts_old.sum() + 1e-6 * bins)
    p_new = (counts_new + 1e-6) / (counts_new.sum() + 1e-6 * bins)
    return float(np.sum(rel_entr(p_old, p_new)))


def flag_signal_retirement(
    old_values: np.ndarray,
    new_values: np.ndarray,
    retirement_threshold: float,
    bins: int = 20,
) -> dict[str, float | bool]:
    """Flag a signal for human review when KL drift exceeds a validation-selected threshold.

    The diagnostic never deletes features automatically; it only returns a review flag.
    """
    kl_value = histogram_kl_divergence(old_values, new_values, bins=bins)
    return {"kl_divergence": kl_value, "flag_for_review": bool(kl_value > retirement_threshold)}
