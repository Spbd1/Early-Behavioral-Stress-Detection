"""Negative-control check scaffolding."""
from __future__ import annotations

import pandas as pd
import statsmodels.formula.api as smf


def fit_negative_control(frame: pd.DataFrame, formula: str):
    """Fit a negative-control regression used to probe residual confounding."""
    return smf.ols(formula=formula, data=frame).fit()
