"""Emission distributions for regime models."""
from __future__ import annotations

import numpy as np
from scipy.stats import nbinom


class NegativeBinomialEmission:
    """Negative Binomial emission for overdispersed count-like digital traces.

    Gaussian emissions are appropriate for normalized continuous indices. Negative Binomial
    emissions are preferable for non-negative counts whose variance exceeds the mean.
    """

    def __init__(self, eta: float, dispersion: float, gamma: np.ndarray | None = None) -> None:
        self.eta = eta
        self.dispersion = dispersion
        self.gamma = gamma

    def mean(self, covariates: np.ndarray | None = None, offset: float = 0.0) -> float:
        """Compute mu where log(mu)=eta+offset+gamma'X."""
        linear = self.eta + offset
        if covariates is not None and self.gamma is not None:
            linear += float(np.dot(self.gamma, covariates))
        return float(np.exp(linear))

    def logpmf(self, y: np.ndarray, covariates: np.ndarray | None = None, offset: float = 0.0) -> np.ndarray:
        """Evaluate log probabilities for observed counts."""
        mu = self.mean(covariates, offset)
        r = self.dispersion
        p = r / (r + mu)
        return nbinom.logpmf(y, r, p)
