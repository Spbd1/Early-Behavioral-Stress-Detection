"""Minimal linear-model shims."""
from __future__ import annotations


class LinearRegression:
    """Very small linear regression placeholder."""

    def fit(self, x, y):
        self.coef_ = [0.0 for _ in (x[0] if x else [0.0])]
        self.intercept_ = float(y[0]) if y else 0.0
        return self

    def predict(self, x):
        return [self.intercept_ for _ in x]


class LogisticRegression:
    """Very small logistic regression placeholder."""

    def __init__(self, *args, **kwargs) -> None:
        self.coef_ = [[0.0]]

    def fit(self, x, y):
        width = len(x[0]) if x else 1
        self.coef_ = [[0.0 for _ in range(width)]]
        return self

    def predict_proba(self, x):
        return [[0.5, 0.5] for _ in x]
