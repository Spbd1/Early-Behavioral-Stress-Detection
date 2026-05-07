"""Runnable conditional HMM prototype for aggregate-regime experiments."""

from __future__ import annotations

import numpy as np

from scipy.special import softmax
from sklearn.cluster import KMeans


class ConditionalHMM:
    """Prototype conditional HMM with covariate-dependent transitions and emissions.

    Transition: ``P(Z_t=i | Z_{t-1}=j, X_t) = softmax_i(beta[j, i]^T X_t)``.
    Emission: ``O_t | Z_t=i, X_t ~ Normal(mu_i + Gamma_i X_t, Sigma_i)``.
    """

    def __init__(self, n_states: int = 3, random_seed: int = 42) -> None:
        self.n_states = n_states
        self.random_seed = random_seed
        self.beta_: np.ndarray | None = None
        self.mu_: np.ndarray | None = None
        self.gamma_: np.ndarray | None = None
        self.sigma_: np.ndarray | None = None
        self.initial_probs_: np.ndarray | None = None

    def fit(self, observations: np.ndarray, covariates: np.ndarray) -> ConditionalHMM:
        """Initialize a clear, testable conditional HMM prototype."""
        y = np.asarray(observations, dtype=float)
        y = y.reshape(-1, 1) if y.ndim == 1 else y
        x = np.asarray(covariates, dtype=float)
        x = x.reshape(-1, 1) if x.ndim == 1 else x
        labels = KMeans(
            n_clusters=self.n_states, n_init=10, random_state=self.random_seed
        ).fit_predict(y)
        self.initial_probs_ = np.full(self.n_states, 1 / self.n_states)
        self.beta_ = np.zeros((self.n_states, self.n_states, x.shape[1] + 1))
        self.mu_ = np.vstack(
            [
                y[labels == i].mean(axis=0) if np.any(labels == i) else y.mean(axis=0)
                for i in range(self.n_states)
            ]
        )
        self.gamma_ = np.zeros((self.n_states, y.shape[1], x.shape[1]))
        self.sigma_ = np.stack([np.eye(y.shape[1]) for _ in range(self.n_states)])
        return self

    def transition_matrix(self, covariate: np.ndarray) -> np.ndarray:
        """Return covariate-dependent transition matrix."""
        if self.beta_ is None:
            raise RuntimeError("ConditionalHMM must be fitted first")
        x = np.r_[1.0, np.asarray(covariate, dtype=float)]
        logits = np.einsum("jif,f->ji", self.beta_, x)
        return softmax(logits, axis=1)

    def predict_proba(self, observations: np.ndarray, covariates: np.ndarray) -> np.ndarray:
        """Run a simple filtering pass using Gaussian residual distances."""
        if self.mu_ is None or self.initial_probs_ is None:
            raise RuntimeError("ConditionalHMM must be fitted first")
        y = np.asarray(observations, dtype=float)
        y = y.reshape(-1, 1) if y.ndim == 1 else y
        x = np.asarray(covariates, dtype=float)
        x = x.reshape(-1, 1) if x.ndim == 1 else x
        probs = np.zeros((len(y), self.n_states))
        prev = self.initial_probs_
        for t in range(len(y)):
            transition = self.transition_matrix(x[t])
            pred = prev @ transition
            dist = ((y[t] - self.mu_) ** 2).sum(axis=1)
            emission = np.exp(-0.5 * dist)
            prev = pred * emission
            prev = prev / max(prev.sum(), 1e-12)
            probs[t] = prev
        return probs
