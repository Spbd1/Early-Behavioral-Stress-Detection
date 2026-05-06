"""Adaptive Gaussian Hidden Markov Model for latent regime research."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import multivariate_normal
from sklearn.cluster import KMeans


@dataclass
class HMMResult:
    """Inference outputs for an HMM sequence."""

    posterior: np.ndarray
    filtered: np.ndarray
    viterbi_path: np.ndarray
    log_likelihood: float


class AdaptiveHMM:
    """Gaussian HMM with scaled inference and exponential transition adaptation.

    This class is intended for offline methodological experimentation with aggregate traces, not
    as a validated recession forecasting system.
    """

    def __init__(
        self,
        n_states: int,
        covariance_type: str = "diagonal",
        forgetting_rate: float = 0.05,
        random_seed: int = 42,
    ) -> None:
        if covariance_type not in {"diagonal", "full"}:
            raise ValueError("covariance_type must be 'diagonal' or 'full'")
        self.n_states = n_states
        self.covariance_type = covariance_type
        self.forgetting_rate = forgetting_rate
        self.random_seed = random_seed
        self.initial_probs_: np.ndarray | None = None
        self.transition_matrix_: np.ndarray | None = None
        self.means_: np.ndarray | None = None
        self.covariances_: np.ndarray | None = None

    def fit(self, observations: np.ndarray) -> "AdaptiveHMM":
        """Initialize emissions by KMeans clusters and empirical covariances."""
        x = self._as_2d(observations)
        kmeans = KMeans(n_clusters=self.n_states, n_init=10, random_state=self.random_seed)
        labels = kmeans.fit_predict(x)
        n_features = x.shape[1]
        self.means_ = kmeans.cluster_centers_
        covariances = np.zeros((self.n_states, n_features, n_features))
        for state in range(self.n_states):
            members = x[labels == state]
            if len(members) < 2:
                cov = np.eye(n_features)
            else:
                cov = np.cov(members, rowvar=False)
                if cov.ndim == 0:
                    cov = np.array([[float(cov)]])
            if self.covariance_type == "diagonal":
                cov = np.diag(np.clip(np.diag(cov), 1e-4, None))
            covariances[state] = cov + np.eye(n_features) * 1e-6
        self.covariances_ = covariances
        self.initial_probs_ = np.full(self.n_states, 1.0 / self.n_states)
        self.transition_matrix_ = self._estimate_transition_from_labels(labels)
        return self

    def forward(self, observations: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
        """Run numerically scaled forward recursion.

        Returns filtered probabilities, scaling constants, and sequence log likelihood.
        """
        self._check_fitted()
        log_emissions = self._emission_log_probabilities(self._as_2d(observations))
        row_offsets = log_emissions.max(axis=1)
        emissions = np.exp(log_emissions - row_offsets[:, None])
        t_steps = emissions.shape[0]
        alpha = np.zeros((t_steps, self.n_states))
        scales = np.zeros(t_steps)
        alpha[0] = self.initial_probs_ * emissions[0]  # type: ignore[operator]
        scales[0] = alpha[0].sum()
        alpha[0] /= scales[0]
        for t in range(1, t_steps):
            alpha[t] = emissions[t] * (alpha[t - 1] @ self.transition_matrix_)  # type: ignore[operator]
            scales[t] = alpha[t].sum()
            alpha[t] /= scales[t]
        log_likelihood = np.log(scales).sum() + row_offsets.sum()
        return alpha, scales, float(log_likelihood)

    def backward(self, observations: np.ndarray, scales: np.ndarray) -> np.ndarray:
        """Run scaled backward recursion."""
        self._check_fitted()
        log_emissions = self._emission_log_probabilities(self._as_2d(observations))
        emissions = np.exp(log_emissions - log_emissions.max(axis=1, keepdims=True))
        t_steps = emissions.shape[0]
        beta = np.ones((t_steps, self.n_states))
        for t in range(t_steps - 2, -1, -1):
            beta[t] = self.transition_matrix_ @ (emissions[t + 1] * beta[t + 1])  # type: ignore[operator]
            beta[t] /= scales[t + 1]
        return beta

    def smooth(self, observations: np.ndarray) -> np.ndarray:
        """Return smoothed posterior state probabilities P(Z_t | O_1:T)."""
        alpha, scales, _ = self.forward(observations)
        beta = self.backward(observations, scales)
        posterior = alpha * beta
        posterior /= posterior.sum(axis=1, keepdims=True)
        return posterior

    def viterbi(self, observations: np.ndarray) -> np.ndarray:
        """Decode the most likely latent state path using log-space Viterbi recursion."""
        self._check_fitted()
        x = self._as_2d(observations)
        log_b = self._emission_log_probabilities(x)
        log_a = np.log(self.transition_matrix_ + 1e-300)  # type: ignore[operator]
        log_pi = np.log(self.initial_probs_ + 1e-300)  # type: ignore[operator]
        delta = np.zeros((x.shape[0], self.n_states))
        psi = np.zeros((x.shape[0], self.n_states), dtype=int)
        delta[0] = log_pi + log_b[0]
        for t in range(1, x.shape[0]):
            scores = delta[t - 1][:, None] + log_a
            psi[t] = scores.argmax(axis=0)
            delta[t] = scores.max(axis=0) + log_b[t]
        path = np.zeros(x.shape[0], dtype=int)
        path[-1] = int(delta[-1].argmax())
        for t in range(x.shape[0] - 2, -1, -1):
            path[t] = psi[t + 1, path[t + 1]]
        return path

    def filter_online(self, observation: np.ndarray, previous_filter: np.ndarray | None = None) -> np.ndarray:
        """Filter one observation, optionally continuing from a prior filtered distribution."""
        self._check_fitted()
        obs = np.asarray(observation, dtype=float).reshape(1, -1)
        prior = self.initial_probs_ if previous_filter is None else previous_filter
        pred = prior @ self.transition_matrix_  # type: ignore[operator]
        filtered = pred * self._emission_probabilities(obs)[0]
        return filtered / filtered.sum()

    def update_transition_matrix(self, recent_state_probs: np.ndarray) -> np.ndarray:
        """Apply A_next = (1-lambda) A_current + lambda A_hat_recent.

        `recent_state_probs` may be hard one-hot states or soft posterior probabilities. The update
        uses expected adjacent state counts and always preserves row normalization.
        """
        self._check_fitted()
        probs = np.asarray(recent_state_probs, dtype=float)
        if probs.ndim == 1:
            one_hot = np.zeros((len(probs), self.n_states))
            one_hot[np.arange(len(probs)), probs.astype(int)] = 1.0
            probs = one_hot
        counts = probs[:-1].T @ probs[1:] + 1e-6
        a_hat = counts / counts.sum(axis=1, keepdims=True)
        lam = self.forgetting_rate
        self.transition_matrix_ = (1.0 - lam) * self.transition_matrix_ + lam * a_hat  # type: ignore[operator]
        self.transition_matrix_ /= self.transition_matrix_.sum(axis=1, keepdims=True)
        return self.transition_matrix_

    def predict(self, observations: np.ndarray) -> HMMResult:
        """Run filtering, smoothing, and Viterbi decoding for a sequence."""
        filtered, _, log_likelihood = self.forward(observations)
        posterior = self.smooth(observations)
        return HMMResult(posterior, filtered, self.viterbi(observations), log_likelihood)

    def _estimate_transition_from_labels(self, labels: np.ndarray) -> np.ndarray:
        counts = np.ones((self.n_states, self.n_states))
        for prev, nxt in zip(labels[:-1], labels[1:]):
            counts[prev, nxt] += 1.0
        return counts / counts.sum(axis=1, keepdims=True)

    def _emission_probabilities(self, observations: np.ndarray) -> np.ndarray:
        log_probs = self._emission_log_probabilities(observations)
        shifted = np.exp(log_probs - log_probs.max(axis=1, keepdims=True))
        return np.clip(shifted, 1e-300, None)

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
        return x.reshape(-1, 1) if x.ndim == 1 else x

    def _check_fitted(self) -> None:
        if self.initial_probs_ is None or self.transition_matrix_ is None or self.means_ is None:
            raise RuntimeError("AdaptiveHMM must be fitted before inference.")
