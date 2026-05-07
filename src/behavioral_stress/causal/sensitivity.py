"""Sensitivity-analysis templates for cautious causal feedback layers."""

from __future__ import annotations

import numpy as np

from sklearn.linear_model import LinearRegression


def lag_structured_regression(
    y: np.ndarray, x: np.ndarray, max_lag: int = 3
) -> dict[str, np.ndarray | float | str]:
    """Fit a lag-structured regression for exploratory diagnostics.

    Estimand of interest in a credible causal design: ``tau(x) = E[Y(1) - Y(0) | X=x]``.
    This helper alone is not a credible causal design and makes no policy prescriptions.
    """
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    rows = [np.roll(x, lag) for lag in range(max_lag + 1)]
    design = np.column_stack(rows)[max_lag:]
    target = y[max_lag:]
    model = LinearRegression().fit(design, target)
    return {
        "coefficients": model.coef_,
        "intercept": float(model.intercept_),
        "note": "Observational diagnostic only.",
    }


def sensitivity_analysis_placeholder() -> dict[str, str]:
    """Describe sensitivity-analysis threats.

    Threats include endogeneity, omitted variables, feedback, ecological
    fallacy, and confounding.
    """
    return {
        "status": "placeholder",
        "note": "No policy prescriptions without a separate credible causal design.",
    }
