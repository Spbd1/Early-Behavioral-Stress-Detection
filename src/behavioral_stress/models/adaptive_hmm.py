"""Adaptive Gaussian Hidden Markov Model for latent-regime research."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from scipy.special import logsumexp
from scipy.stats import multivariate_normal
from sklearn.cluster import KMeans

EPS = 1e-12


@dataclass
class HMMResult:
    """Inference outputs for one HMM sequence."""

    posterior: np.ndarray
    filtered: np.ndarray
    viterbi_path: np.ndarray
    log_likelihood: float


class AdaptiveHMM:
    """Gaussian HMM with scaled inference and cautious transition adaptation.

    The model is intended for synthetic validation and aggregate latent-regime exploration, not for
    validated recession prediction or individual-level stress inference.
    """

    def __init__(
        self,
        n_states: int,
        covariance_type: str = "diagonal",
        forgetting_rate: float = 0.05,
        random_seed: int = 42,
    ) -> None:
        if n_states < 2:
            raise ValueError("n_states must be at least 2")
        if covariance_type not in {"diagonal", "full"}:
            raise ValueError("covariance_type must be 'diagonal' or 'full'")
        if not 0 <= forgetting_rate <= 1:
            raise ValueError("forgetting_rate must be in [0, 1]")
        self.n_states = n_states
        self.covariance_type = covariance_type
        self.forgetting_rate = forgetting_rate
        self.random_seed = random_seed
        self.initial_probs_: np.ndarray | None = None
        self.transition_matrix_: np.ndarray | None = None
        self.means_: np.ndarray | None = None
        self.covariances_: np.ndarray | None = None

    def fit(self, observations: np.ndarray) -> "AdaptiveHMM":
        """Initialize emissions with KMeans and empirical covariance estimates."""
        x = self._as_2d(observations)
        if len(x) < self.n_states:
            raise ValueError("Need at least n_states observations")
        kmeans = KMeans(n_clusters=self.n_states, n_init=10, random_state=self.random_seed)
        labels = kmeans.fit_predict(x)
        n_features = x.shape[1]
        self.means_ = kmeans.cluster_centers_.astype(float)
        covs = np.zeros((self.n_states, n_features, n_features), dtype=float)
        global_cov = np.cov(x, rowvar=False)
        if np.ndim(global_cov) == 0:
            global_cov = np.array([[float(global_cov)]])
        for state in range(self.n_states):
            members = x[labels == state]
            if len(members) < 2:
                cov = np.asarray(global_cov, dtype=float)
            else:
                cov = np.cov(members, rowvar=False)
                if np.ndim(cov) == 0:
                    cov = np.array([[float(cov)]])
            if self.covariance_type == "diagonal":
                cov = np.diag(np.clip(np.diag(cov), 1e-4, None))
            covs[state] = cov + np.eye(n_features) * 1e-6
        self.covariances_ = covs
        self.initial_probs_ = np.bincount(labels[: max(1, len(labels) // 10)], minlength=self.n_states) + 1.0
        self.initial_probs_ = self.initial_probs_ / self.initial_probs_.sum()
        self.transition_matrix_ = self._estimate_transition_from_labels(labels)
        return self

    def forward(self, observations: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
        """Run scaled forward recursion and return filtered probabilities, scales, log-likelihood."""
        self._check_fitted()
        x = self._as_2d(observations)
        log_emissions = self._emission_log_probabilities(x)
        offsets = log_emissions.max(axis=1)
        emissions = np.exp(log_emissions - offsets[:, None])
        emissions = np.clip(emissions, EPS, None)
        alpha = np.zeros((len(x), self.n_states), dtype=float)
        scales = np.zeros(len(x), dtype=float)
        alpha[0] = self.initial_probs_ * emissions[0]  # type: ignore[operator]
        scales[0] = max(alpha[0].sum(), EPS)
        alpha[0] /= scales[0]
        for t in range(1, len(x)):
            alpha[t] = emissions[t] * (alpha[t - 1] @ self.transition_matrix_)  # type: ignore[operator]
            scales[t] = max(alpha[t].sum(), EPS)
            alpha[t] /= scales[t]
        log_likelihood = float(np.log(scales).sum() + offsets.sum())
        return alpha, scales, log_likelihood

    def backward(self, observations: np.ndarray, scales: np.ndarray) -> np.ndarray:
        """Run scaled backward recursion compatible with :meth:`forward`."""
        self._check_fitted()
        x = self._as_2d(observations)
        log_emissions = self._emission_log_probabilities(x)
        offsets = log_emissions.max(axis=1)
        emissions = np.exp(log_emissions - offsets[:, None])
        emissions = np.clip(emissions, EPS, None)
        beta = np.ones((len(x), self.n_states), dtype=float)
        for t in range(len(x) - 2, -1, -1):
            beta[t] = self.transition_matrix_ @ (emissions[t + 1] * beta[t + 1])  # type: ignore[operator]
            beta[t] /= max(scales[t + 1], EPS)
        return beta

    def smooth(self, observations: np.ndarray) -> np.ndarray:
        """Return smoothed posterior probabilities whose rows sum to one."""
        alpha, scales, _ = self.forward(observations)
        beta = self.backward(observations, scales)
        posterior = np.clip(alpha * beta, EPS, None)
        posterior /= posterior.sum(axis=1, keepdims=True)
        return posterior

    def viterbi(self, observations: np.ndarray) -> np.ndarray:
        """Decode a most likely latent path using log-space dynamic programming."""
        self._check_fitted()
        x = self._as_2d(observations)
        log_b = self._emission_log_probabilities(x)
        log_a = np.log(np.clip(self.transition_matrix_, EPS, None))  # type: ignore[arg-type]
        log_pi = np.log(np.clip(self.initial_probs_, EPS, None))  # type: ignore[arg-type]
        delta = np.zeros((len(x), self.n_states), dtype=float)
        psi = np.zeros((len(x), self.n_states), dtype=int)
        delta[0] = log_pi + log_b[0]
        for t in range(1, len(x)):
            scores = delta[t - 1][:, None] + log_a
            psi[t] = np.argmax(scores, axis=0)
            delta[t] = np.max(scores, axis=0) + log_b[t]
        path = np.zeros(len(x), dtype=int)
        path[-1] = int(np.argmax(delta[-1]))
        for t in range(len(x) - 2, -1, -1):
            path[t] = psi[t + 1, path[t + 1]]
        return path

    def filter_online(self, observation: np.ndarray, previous_filter: np.ndarray | None = None) -> np.ndarray:
        """Filter one observation and return a normalized state-probability vector."""
        self._check_fitted()
        obs = self._as_2d(observation)
        if obs.shape[0] != 1:
            obs = obs[-1:].copy()
        prior = self.initial_probs_ if previous_filter is None else np.asarray(previous_filter, dtype=float)
        prior = prior / max(prior.sum(), EPS)
        pred = prior @ self.transition_matrix_  # type: ignore[operator]
        filtered = pred * self._emission_probabilities(obs)[0]
        filtered = np.clip(filtered, EPS, None)
        return filtered / filtered.sum()

    def update_transition_matrix(self, recent_state_probs: np.ndarray, lambda_: float | None = None) -> np.ndarray:
        """Update transitions using ``A_next = (1-lambda) A_current + lambda A_hat_recent``."""
        self._check_fitted()
        probs = np.asarray(recent_state_probs, dtype=float)
        if probs.ndim == 1:
            hard = probs.astype(int)
            one_hot = np.zeros((len(hard), self.n_states), dtype=float)
            one_hot[np.arange(len(hard)), hard] = 1.0
            probs = one_hot
        probs = np.clip(probs, EPS, None)
        probs /= probs.sum(axis=1, keepdims=True)
        if len(probs) < 2:
            return self.transition_matrix_  # type: ignore[return-value]
        counts = probs[:-1].T @ probs[1:] + EPS
        a_hat = counts / counts.sum(axis=1, keepdims=True)
        lam = self.forgetting_rate if lambda_ is None else lambda_
        self.transition_matrix_ = (1.0 - lam) * self.transition_matrix_ + lam * a_hat  # type: ignore[operator]
        self.transition_matrix_ = np.clip(self.transition_matrix_, EPS, None)
        self.transition_matrix_ /= self.transition_matrix_.sum(axis=1, keepdims=True)
        return self.transition_matrix_

    def predict(self, observations: np.ndarray) -> HMMResult:
        """Run filtering, smoothing, and Viterbi decoding for a sequence."""
        filtered, _, log_likelihood = self.forward(observations)
        posterior = self.smooth(observations)
        return HMMResult(posterior, filtered, self.viterbi(observations), log_likelihood)

    def save(self, path: str | Path) -> None:
        """Serialize the fitted model with joblib."""
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: str | Path) -> "AdaptiveHMM":
        """Load a model saved with :meth:`save`."""
        return joblib.load(path)

    def _estimate_transition_from_labels(self, labels: np.ndarray) -> np.ndarray:
        counts = np.ones((self.n_states, self.n_states), dtype=float)
        for prev, nxt in zip(labels[:-1], labels[1:]):
            counts[int(prev), int(nxt)] += 1.0
        return counts / counts.sum(axis=1, keepdims=True)

    def _emission_probabilities(self, observations: np.ndarray) -> np.ndarray:
        log_probs = self._emission_log_probabilities(observations)
        row_norm = logsumexp(log_probs, axis=1, keepdims=True)
        probs = np.exp(log_probs - row_norm)
        return np.clip(probs, EPS, None)

    def _emission_log_probabilities(self, observations: np.ndarray) -> np.ndarray:
        self._check_fitted()
        return np.column_stack(
            [
                multivariate_normal.logpdf(
                    observations,
                    mean=self.means_[state],  # type: ignore[index]
                    cov=self.covariances_[state],  # type: ignore[index]
                    allow_singular=True,
                )
                for state in range(self.n_states)
            ]
        )

    @staticmethod
    def _as_2d(observations: np.ndarray) -> np.ndarray:
        x = np.asarray(observations, dtype=float)
        if x.ndim == 0:
            return x.reshape(1, 1)
        return x.reshape(-1, 1) if x.ndim == 1 else x

    def _check_fitted(self) -> None:
        if (
            self.initial_probs_ is None
            or self.transition_matrix_ is None
            or self.means_ is None
            or self.covariances_ is None
        ):
            raise RuntimeError("AdaptiveHMM must be fitted before inference")
