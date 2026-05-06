"""Feature screening routines for offline exploration."""
from __future__ import annotations

import numpy as np
from sklearn.feature_selection import mutual_info_classif
from sklearn.linear_model import LogisticRegression


def mutual_information_scores(features: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """Return mutual-information scores for features against labels."""
    return mutual_info_classif(features, labels, random_state=42)


def l1_logistic_screening(features: np.ndarray, labels: np.ndarray, c: float = 0.5) -> np.ndarray:
    """Return absolute L1-regularized logistic coefficients as screening scores."""
    model = LogisticRegression(penalty="l1", solver="liblinear", C=c, max_iter=1000)
    model.fit(features, labels)
    return np.abs(model.coef_).max(axis=0)
