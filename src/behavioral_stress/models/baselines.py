"""Simple baseline models for research comparisons."""

from __future__ import annotations

import numpy as np

from sklearn.linear_model import LinearRegression, LogisticRegression
from statsmodels.tsa.statespace.sarimax import SARIMAX


class LogisticRegressionBaseline:
    """Logistic regression baseline for synthetic binary stress labels."""

    def __init__(self) -> None:
        self.model = LogisticRegression(max_iter=1000)

    def fit(self, x: np.ndarray, y: np.ndarray) -> LogisticRegressionBaseline:
        self.model.fit(x, y)
        return self

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(x)[:, 1]


class SARIMAXBaseline:
    """Univariate SARIMAX baseline for one aggregate trace."""

    def fit(self, y: np.ndarray, order: tuple[int, int, int] = (1, 0, 0)) -> SARIMAXBaseline:
        self.result_ = SARIMAX(
            y, order=order, enforce_stationarity=False, enforce_invertibility=False
        ).fit(disp=False)
        return self

    def forecast(self, steps: int) -> np.ndarray:
        return np.asarray(self.result_.forecast(steps=steps))


ARIMABaseline = SARIMAXBaseline


class UnivariateTraceRegressionBaseline:
    """Linear baseline from one aggregate trace to a target outcome."""

    def __init__(self) -> None:
        self.model = LinearRegression()

    def fit(self, trace: np.ndarray, y: np.ndarray) -> UnivariateTraceRegressionBaseline:
        self.model.fit(np.asarray(trace).reshape(-1, 1), y)
        return self

    def predict(self, trace: np.ndarray) -> np.ndarray:
        return self.model.predict(np.asarray(trace).reshape(-1, 1))


class LSTMBaseline:
    """Placeholder; neural baselines are intentionally not overbuilt in this prototype."""

    def fit(self, *_args: object, **_kwargs: object) -> None:
        raise NotImplementedError(
            "LSTM baseline is outside the lightweight synthetic prototype scope."
        )


class TransformerBaseline:
    """Placeholder; neural baselines are intentionally not overbuilt in this prototype."""

    def fit(self, *_args: object, **_kwargs: object) -> None:
        raise NotImplementedError(
            "Transformer baseline is outside the lightweight synthetic prototype scope."
        )
