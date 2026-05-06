"""Adaptive Gaussian Hidden Markov Model utilities.

The model in this module is intended for research workflows that need a
small, inspectable HMM implementation.  It performs Gaussian-emission
initialization from observed data and numerically stable inference with scaled
forward/backward recursions.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.special import logsumexp
from sklearn.cluster import KMeans

EPS = 1e-12
MIN_VARIANCE = 1e-6
FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


@dataclass
class HMMResult:
    """Inference outputs for one observation sequence."""

    posterior: FloatArray
    filtered: FloatArray
    viterbi_path: IntArray
    log_likelihood: float


class AdaptiveHMM:
    """Gaussian-emission Hidden Markov Model with adaptive transitions.

    Parameters are initialized from observations using ``KMeans`` and simple
    maximum-likelihood summaries.  Inference uses scaled forward and backward
    recursions so filtered and smoothed probabilities remain normalized and the
    sequence log likelihood remains finite for typical research-sized inputs.
    """

    def __init__(
        self,
        n_states: int,
        covariance_type: str = "diagonal",
        forgetting_rate: float = 0.05,
        random_seed: int = 42,
    ) -> None:
        """Create an unfitted adaptive HMM.

        Args:
            n_states: Number of latent states.
            covariance_type: Currently supports diagonal Gaussian covariance.
            forgetting_rate: Weight assigned to newly estimated transition
                counts in :meth:`update_transition_matrix`.
            random_seed: Seed used for KMeans initialization.
        """
        if n_states < 2:
            raise ValueError("n_states must be at least 2")
        if covariance_type != "diagonal":
            raise ValueError("covariance_type must be 'diagonal'")
        if not 0 <= forgetting_rate <= 1:
            raise ValueError("forgetting_rate must be in [0, 1]")
        self.n_states = n_states
        self.covariance_type = covariance_type
        self.forgetting_rate = forgetting_rate
        self.random_seed = random_seed
        self.initial_probs_: FloatArray | None = None
        self.transition_matrix_: FloatArray | None = None
        self.means_: FloatArray | None = None
        self.variances_: FloatArray | None = None

    def fit(self, observations: ArrayLike) -> "AdaptiveHMM":
        """Initialize Gaussian emissions and transition probabilities.

        One-dimensional observations are treated as a single feature column.
        States are initialized with ``sklearn.cluster.KMeans``; state labels are
        then ordered by mean feature value for deterministic interpretation.
        """
        x = self._as_matrix(observations)
        if len(x) < self.n_states:
            raise ValueError("Need at least n_states observations")

        labels = self._initial_labels(x)
        means: list[FloatArray] = []
        variances: list[FloatArray] = []
        initial_counts = np.full(self.n_states, EPS, dtype=float)
        initial_counts[labels[0]] += 1.0

        global_mean = x.mean(axis=0)
        global_var = np.maximum(x.var(axis=0), MIN_VARIANCE)
        for state in range(self.n_states):
            members = x[labels == state]
            if len(members) == 0:
                means.append(global_mean)
                variances.append(global_var)
                continue
            means.append(members.mean(axis=0))
            variances.append(np.maximum(members.var(axis=0), MIN_VARIANCE))

        self.means_ = np.vstack(means).astype(float)
        self.variances_ = np.vstack(variances).astype(float)
        self.initial_probs_ = self._normalize_vector(initial_counts)
        self.transition_matrix_ = self._estimate_transition_from_labels(labels)
        return self

    def forward(self, observations: ArrayLike) -> tuple[FloatArray, FloatArray, float]:
        """Run the scaled forward recursion.

        Returns:
            A tuple of ``(filtered_probabilities, scales, log_likelihood)``.
            Each row of ``filtered_probabilities`` sums to one and the log
            likelihood is computed from the scaling constants.
        """
        self._check_fitted()
        x = self._as_matrix(observations)
        alpha = np.zeros((len(x), self.n_states), dtype=float)
        scales = np.zeros(len(x), dtype=float)
        log_likelihood = 0.0

        emissions = self._emission_probabilities(x)
        current = self.initial_probs_ * emissions[0]  # type: ignore[operator]
        scales[0] = max(float(current.sum()), EPS)
        alpha[0] = current / scales[0]
        log_likelihood += np.log(scales[0])

        for t in range(1, len(x)):
            predicted = alpha[t - 1] @ self.transition_matrix_  # type: ignore[operator]
            current = predicted * emissions[t]
            scales[t] = max(float(current.sum()), EPS)
            alpha[t] = current / scales[t]
            log_likelihood += np.log(scales[t])

        return alpha, scales, float(log_likelihood)

    def backward(self, observations: ArrayLike, scales: ArrayLike) -> FloatArray:
        """Run the scaled backward recursion compatible with :meth:`forward`.

        Args:
            observations: Observation sequence used for the forward pass.
            scales: Scaling constants returned by :meth:`forward`.
        """
        self._check_fitted()
        x = self._as_matrix(observations)
        scale_values = np.asarray(scales, dtype=float)
        if scale_values.shape != (len(x),):
            raise ValueError("scales must have one value per observation")

        beta = np.ones((len(x), self.n_states), dtype=float)
        emissions = self._emission_probabilities(x)
        for t in range(len(x) - 2, -1, -1):
            next_terms = emissions[t + 1] * beta[t + 1]
            beta[t] = (self.transition_matrix_ @ next_terms) / max(float(scale_values[t + 1]), EPS)  # type: ignore[operator]
        return np.maximum(beta, EPS)

    def smooth(self, observations: ArrayLike) -> FloatArray:
        """Return normalized smoothed posterior state probabilities."""
        alpha, scales, _ = self.forward(observations)
        beta = self.backward(observations, scales)
        posterior = np.maximum(alpha * beta, EPS)
        return self._normalize_rows(posterior)

    def viterbi(self, observations: ArrayLike) -> IntArray:
        """Decode the most likely latent-state path in log space."""
        self._check_fitted()
        x = self._as_matrix(observations)
        emissions = self._emission_probabilities(x)
        log_initial = np.log(np.maximum(self.initial_probs_, EPS))  # type: ignore[arg-type]
        log_transition = np.log(np.maximum(self.transition_matrix_, EPS))  # type: ignore[arg-type]
        log_emissions = np.log(np.maximum(emissions, EPS))

        scores = np.zeros((len(x), self.n_states), dtype=float)
        backpointers = np.zeros((len(x), self.n_states), dtype=np.int64)
        scores[0] = log_initial + log_emissions[0]
        scores[0] -= logsumexp(scores[0])

        for t in range(1, len(x)):
            candidates = scores[t - 1][:, np.newaxis] + log_transition
            backpointers[t] = np.argmax(candidates, axis=0)
            scores[t] = np.max(candidates, axis=0) + log_emissions[t]
            scores[t] -= logsumexp(scores[t])

        path = np.zeros(len(x), dtype=np.int64)
        path[-1] = int(np.argmax(scores[-1]))
        for t in range(len(x) - 2, -1, -1):
            path[t] = backpointers[t + 1, path[t + 1]]
        return path

    def filter_online(self, observation: ArrayLike, previous_filtered: ArrayLike | None = None) -> FloatArray:
        """Filter one observation and return normalized state probabilities.

        Args:
            observation: One observation vector, or a one-element sequence.
            previous_filtered: Previous normalized state probabilities.  If
                omitted, the model's initial probabilities are used.
        """
        self._check_fitted()
        row = self._as_single_observation(observation)
        emissions = self._emission_probabilities(row[np.newaxis, :])[0]
        if previous_filtered is None:
            prior = self.initial_probs_  # type: ignore[assignment]
        else:
            prior = self._normalize_vector(np.asarray(previous_filtered, dtype=float)) @ self.transition_matrix_  # type: ignore[operator]
        filtered = np.maximum(prior * emissions, EPS)  # type: ignore[operator]
        return self._normalize_vector(filtered)

    def update_transition_matrix(self, posterior_window: ArrayLike) -> FloatArray:
        """Adapt transition probabilities from a window of posterior rows.

        The supplied posterior rows are normalized before use.  The updated
        transition matrix is row-normalized before it is stored and returned.
        """
        self._check_fitted()
        rows = self._normalize_rows(self._as_matrix(posterior_window))
        if rows.shape[1] != self.n_states:
            raise ValueError("posterior_window must have n_states columns")

        counts = np.full((self.n_states, self.n_states), EPS, dtype=float)
        for prev, cur in zip(rows[:-1], rows[1:]):
            counts += np.outer(prev, cur)
        empirical = self._normalize_rows(counts)
        blended = (1 - self.forgetting_rate) * self.transition_matrix_ + self.forgetting_rate * empirical  # type: ignore[operator]
        self.transition_matrix_ = self._normalize_rows(blended)
        return self.transition_matrix_

    def predict(self, observations: ArrayLike) -> HMMResult:
        """Return filtered, smoothed, Viterbi, and likelihood outputs."""
        filtered, _, log_likelihood = self.forward(observations)
        posterior = self.smooth(observations)
        return HMMResult(
            posterior=posterior,
            filtered=filtered,
            viterbi_path=self.viterbi(observations),
            log_likelihood=log_likelihood,
        )

    def save(self, path: str | Path) -> None:
        """Save fitted parameters as JSON."""
        payload = {
            "n_states": self.n_states,
            "covariance_type": self.covariance_type,
            "forgetting_rate": self.forgetting_rate,
            "random_seed": self.random_seed,
            "initial_probs": None if self.initial_probs_ is None else self.initial_probs_.tolist(),
            "transition_matrix": None if self.transition_matrix_ is None else self.transition_matrix_.tolist(),
            "means": None if self.means_ is None else self.means_.tolist(),
            "variances": None if self.variances_ is None else self.variances_.tolist(),
        }
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "AdaptiveHMM":
        """Load fitted parameters from JSON."""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        model = cls(payload["n_states"], payload["covariance_type"], payload["forgetting_rate"], payload["random_seed"])
        model.initial_probs_ = np.asarray(payload["initial_probs"], dtype=float)
        model.transition_matrix_ = model._normalize_rows(np.asarray(payload["transition_matrix"], dtype=float))
        model.means_ = np.asarray(payload["means"], dtype=float)
        model.variances_ = np.maximum(np.asarray(payload["variances"], dtype=float), MIN_VARIANCE)
        return model

    def _initial_labels(self, x: FloatArray) -> IntArray:
        kmeans = KMeans(n_clusters=self.n_states, n_init=10, random_state=self.random_seed)
        raw_labels = kmeans.fit_predict(x).astype(np.int64)
        centers = kmeans.cluster_centers_.mean(axis=1)
        label_order = np.argsort(centers)
        remap = {int(old_label): int(new_label) for new_label, old_label in enumerate(label_order)}
        return np.asarray([remap[int(label)] for label in raw_labels], dtype=np.int64)

    def _estimate_transition_from_labels(self, labels: IntArray) -> FloatArray:
        counts = np.ones((self.n_states, self.n_states), dtype=float)
        for src, dst in zip(labels[:-1], labels[1:]):
            counts[int(src), int(dst)] += 1.0
        return self._normalize_rows(counts)

    def _emission_probabilities(self, x: FloatArray) -> FloatArray:
        """Evaluate diagonal Gaussian emission densities for each row/state."""
        self._check_fitted()
        variances = np.maximum(self.variances_, MIN_VARIANCE)  # type: ignore[arg-type]
        diff = x[:, np.newaxis, :] - self.means_[np.newaxis, :, :]  # type: ignore[index]
        log_det = np.sum(np.log(2.0 * np.pi * variances), axis=1)
        mahalanobis = np.sum((diff**2) / variances[np.newaxis, :, :], axis=2)
        log_prob = -0.5 * (log_det[np.newaxis, :] + mahalanobis)
        log_prob = np.clip(log_prob, np.log(EPS), -np.log(EPS))
        return np.maximum(np.exp(log_prob), EPS)

    @staticmethod
    def _as_matrix(observations: ArrayLike) -> FloatArray:
        matrix = np.asarray(observations, dtype=float)
        if matrix.ndim == 1:
            matrix = matrix.reshape(-1, 1)
        if matrix.ndim != 2:
            raise ValueError("observations must be one- or two-dimensional")
        if matrix.shape[0] == 0:
            raise ValueError("observations must contain at least one row")
        if not np.all(np.isfinite(matrix)):
            raise ValueError("observations must be finite")
        return matrix.astype(float, copy=False)

    def _as_single_observation(self, observation: ArrayLike) -> FloatArray:
        row = np.asarray(observation, dtype=float)
        if row.ndim == 0:
            row = row.reshape(1)
        elif row.ndim == 2 and row.shape[0] == 1:
            row = row.reshape(-1)
        elif row.ndim != 1:
            raise ValueError("observation must be a single one-dimensional observation")
        if self.means_ is not None and row.shape[0] != self.means_.shape[1]:
            raise ValueError("observation feature count does not match fitted model")
        if not np.all(np.isfinite(row)):
            raise ValueError("observation must be finite")
        return row.astype(float, copy=False)

    @staticmethod
    def _normalize_vector(values: ArrayLike) -> FloatArray:
        vector = np.maximum(np.asarray(values, dtype=float), EPS)
        total = max(float(vector.sum()), EPS)
        return vector / total

    @staticmethod
    def _normalize_rows(values: ArrayLike) -> FloatArray:
        rows = np.maximum(np.asarray(values, dtype=float), EPS)
        totals = np.maximum(rows.sum(axis=1, keepdims=True), EPS)
        return rows / totals

    def _check_fitted(self) -> None:
        if (
            self.initial_probs_ is None
            or self.transition_matrix_ is None
            or self.means_ is None
            or self.variances_ is None
        ):
            raise RuntimeError("AdaptiveHMM must be fitted before inference")
