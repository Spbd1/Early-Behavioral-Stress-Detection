"""Cautious event-study templates for aggregate observational traces."""
from __future__ import annotations

import pandas as pd
import statsmodels.formula.api as smf

CAUSAL_LIMITATIONS = (
    "Observational aggregate data are vulnerable to endogeneity, omitted variables, policy "
    "feedback, ecological fallacy, and time-varying confounding. No policy prescription should "
    "be made without a separate credible causal design."
)


def fit_event_study(frame: pd.DataFrame, formula: str):
    """Fit an OLS event-study-style regression template."""
    return smf.ols(formula=formula, data=frame).fit()
