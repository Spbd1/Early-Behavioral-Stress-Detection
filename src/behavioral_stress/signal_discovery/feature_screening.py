"""Feature-screening utilities for synthetic labels and aggregate traces."""

from __future__ import annotations

import numpy as np
import pandas as pd

from sklearn.feature_selection import mutual_info_classif
from sklearn.linear_model import LogisticRegression


def mutual_information_screening(x: pd.DataFrame, y: np.ndarray) -> pd.DataFrame:
    """Rank features by mutual information with synthetic stress labels."""
    scores = mutual_info_classif(x.values, y, discrete_features=False, random_state=42)
    return pd.DataFrame({"feature": x.columns, "mutual_information": scores}).sort_values(
        "mutual_information", ascending=False
    )


def l1_logistic_screening(x: pd.DataFrame, y: np.ndarray, c: float = 0.5) -> pd.DataFrame:
    """Rank features by absolute L1-logistic coefficients."""
    model = LogisticRegression(penalty="l1", solver="liblinear", C=c, max_iter=1000)
    model.fit(x.values, y)
    coefs = np.abs(model.coef_[0])
    return pd.DataFrame({"feature": x.columns, "abs_coefficient": coefs}).sort_values(
        "abs_coefficient", ascending=False
    )
