"""Emission distributions for aggregate trace models."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import multivariate_normal, nbinom


@dataclass
class GaussianEmission:
    """Gaussian emission for normalized continuous aggregate traces."""

    mean: np.ndarray
    covariance: np.ndarray

    def log_prob(self, observations: np.ndarray) -> np.ndarray:
        """Return log probabilities under a multivariate Gaussian emission."""
        return multivariate_normal.logpdf(observations, mean=self.mean, cov=self.covariance, allow_singular=True)


@dataclass
class NegativeBinomialEmission:
    """Negative-binomial emission for overdispersed aggregate count traces.

    ``log(mu_t) = eta_i + delta_t + gamma^T X_t`` and ``r`` controls overdispersion.
    """

    eta: float
    r: float = 8.0
    gamma: np.ndarray | None = None

    def mean(self, covariates: np.ndarray | None = None, delta_t: np.ndarray | float = 0.0) -> np.ndarray:
        """Compute the conditional mean ``mu_t``."""
        linear = np.asarray(delta_t, dtype=float) + self.eta
        if covariates is not None and self.gamma is not None:
            linear = linear + np.asarray(covariates) @ self.gamma
        return np.exp(linear)

    def log_prob(
        self,
        counts: np.ndarray,
        covariates: np.ndarray | None = None,
        delta_t: np.ndarray | float = 0.0,
    ) -> np.ndarray:
        """Return log probabilities for overdispersed count observations."""
        mu = self.mean(covariates=covariates, delta_t=delta_t)
        p = self.r / (self.r + mu)
        return nbinom.logpmf(counts, n=self.r, p=p)
