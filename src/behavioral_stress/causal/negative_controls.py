"""Negative-control diagnostics for aggregate observational templates."""

from __future__ import annotations

import numpy as np


def negative_control_check(
    outcome: np.ndarray, negative_control: np.ndarray
) -> dict[str, float | str]:
    """Return correlation with a negative-control trace as a confounding diagnostic."""
    corr = float(np.corrcoef(outcome, negative_control)[0, 1]) if len(outcome) > 1 else float("nan")
    return {
        "negative_control_correlation": corr,
        "note": "Diagnostic only; does not identify causal effects.",
    }
