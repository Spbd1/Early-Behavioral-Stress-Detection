"""Adaptive Gaussian Hidden Markov Model utilities."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Sequence

import numpy as np
from scipy.special import logsumexp
from scipy.stats import multivariate_normal

from sklearn.cluster import KMeans


EPS = 1e-12
MIN_VARIANCE = 1e-6


@dataclass
class ForwardResult:
    probabilities: np.ndarray
    scales: np.ndarray
    log_likelihood: float

    def __iter__(self) -> Iterator[object]:
        yield self.probabilities
        yield self.scales
        yield self.log_likelihood

    def __array__(self, dtype: np.dtype | None = None) -> np.ndarray:
        return np.asarray(self.probabilities, dtype=dtype)

    def __len__(self) -> int:
        return len(self.probabilities)

    def __getitem__(self, index: object) -> object:
        return self.probabilities[index]

    @property
    def shape(self) -> tuple[int, ...]:
        return self.probabilities.shape

    def sum(self, *args: object, **kwargs: object) -> np.ndarray:
        return self.probabilities.sum(*args, **kwargs)


@dataclass
class HMMResult:
    posterior: np.ndarray
    filtered: np.ndarray
    viterbi_path: np.ndarray
    log_likelihood: float


class AdaptiveHMM:
    """Diagonal Gaussian Hidden Markov Model with adaptive transitions."""

    def __init__(
        self,
        n_states: int,
        covariance_type: str = "diagonal",
        forgetting_rate: float = 0.05,
        random_seed: int = 42,
        max_iter: int = 25,
        tol: float = 1e-4,
    ) -> None:
        if n_states < 2:
            raise ValueError("n_states must be at least 2")
        if covariance_type != "diagonal":
            raise ValueError("covariance_type must be 'diagonal'")
        if not 0.0 <= forgetting_rate <= 1.0:
            raise ValueError("forgetting_rate must be in [0, 1]")
        if max_iter < 1:
            raise ValueError("max_iter must be at least 1")
        if tol < 0.0:
            raise ValueError("tol must be non-negative")

        self.n_states = int(n_states)
        self.covariance_type = covariance_type
        self.forgetting_rate = float(forgetting_rate)
        self.random_seed = int(random_seed)
        self.max_iter = int(max_iter)
        self.tol = float(tol)

        self.initial_probs_: np.ndarray | None = None
        self.transition_matrix_: np.ndarray | None = None
        self.means_: np.ndarray | None = None
        self.covariances_: np.ndarray | None = None
        self.log_likelihood_: float | None = None
        self._online_filtered: np.ndarray | None = None

    def fit(self, observations: object) -> "AdaptiveHMM":
        rows = self._as_matrix(observations)
        if rows.shape[0] < self.n_states:
            raise ValueError("Need at least n_states observations")

        labels = self._initial_labels(rows)
        self.initial_probs_ = self._normalize_vector(np.bincount([labels[0]], minlength=self.n_states))
        self.transition_matrix_ = self._estimate_transition_from_labels(labels)
        self.means_, self.covariances_ = self._estimate_gaussians(rows, labels)

        previous_log_likelihood = -math.inf
        for _ in range(self.max_iter):
            forward_result = self.forward(rows)
            backward = self.backward(rows, forward_result.scales)
            gamma = self._normalize_rows(forward_result.probabilities * backward)
            xi_sum = self._expected_transition_counts(rows, backward, forward_result.scales)

            self.initial_probs_ = self._normalize_vector(gamma[0])
            self.transition_matrix_ = self._normalize_rows(xi_sum)
            self.means_, self.covariances_ = self._estimate_gaussians_from_responsibilities(rows, gamma)

            current_log_likelihood = float(forward_result.log_likelihood)
            if abs(current_log_likelihood - previous_log_likelihood) <= self.tol:
                break
            previous_log_likelihood = current_log_likelihood

        final_forward = self.forward(rows)
        if not math.isfinite(float(final_forward.log_likelihood)):
            raise RuntimeError("HMM fit produced a non-finite log likelihood")
        self.log_likelihood_ = float(final_forward.log_likelihood)
        self._online_filtered = None
        return self

    def forward(self, observations: object) -> ForwardResult:
        self._check_fitted()
        rows = self._as_matrix(observations)
        log_emissions = self._log_emission_probabilities(rows)

        probabilities = np.zeros((rows.shape[0], self.n_states), dtype=float)
        scales = np.zeros(rows.shape[0], dtype=float)

        current = self.initial_probs_ * np.exp(log_emissions[0])
        scale = max(float(current.sum()), EPS)
        probabilities[0] = current / scale
        scales[0] = scale

        for t in range(1, rows.shape[0]):
            predicted = probabilities[t - 1] @ self.transition_matrix_
            current = predicted * np.exp(log_emissions[t])
            scale = max(float(current.sum()), EPS)
            probabilities[t] = current / scale
            scales[t] = scale

        probabilities = self._normalize_rows(probabilities)
        log_likelihood = float(np.log(scales).sum())
        return ForwardResult(probabilities=probabilities, scales=scales, log_likelihood=log_likelihood)

    def backward(self, observations: object, scales: Sequence[float] | None = None) -> np.ndarray:
        self._check_fitted()
        rows = self._as_matrix(observations)
        if scales is None:
            scales = self.forward(rows).scales
        scales_array = np.asarray(scales, dtype=float)
        if scales_array.shape != (rows.shape[0],):
            raise ValueError("scales must have one value per observation")

        log_emissions = self._log_emission_probabilities(rows)
        emissions = np.exp(log_emissions)
        backward = np.ones((rows.shape[0], self.n_states), dtype=float)

        for t in range(rows.shape[0] - 2, -1, -1):
            backward[t] = self.transition_matrix_ @ (emissions[t + 1] * backward[t + 1])
            backward[t] /= max(float(scales_array[t + 1]), EPS)
            backward[t] = self._normalize_vector(backward[t])

        return backward

    def smooth(self, observations: object) -> np.ndarray:
        forward_result = self.forward(observations)
        backward = self.backward(observations, forward_result.scales)
        posterior = forward_result.probabilities * backward
        return self._normalize_rows(posterior)

    def viterbi(self, observations: object) -> np.ndarray:
        self._check_fitted()
        rows = self._as_matrix(observations)
        log_emissions = self._log_emission_probabilities(rows)
        log_initial = np.log(np.clip(self.initial_probs_, EPS, None))
        log_transition = np.log(np.clip(self.transition_matrix_, EPS, None))

        scores = np.zeros((rows.shape[0], self.n_states), dtype=float)
        backpointers = np.zeros((rows.shape[0], self.n_states), dtype=int)
        scores[0] = log_initial + log_emissions[0]
        scores[0] -= logsumexp(scores[0])

        for t in range(1, rows.shape[0]):
            for target in range(self.n_states):
                candidates = scores[t - 1] + log_transition[:, target]
                backpointers[t, target] = int(np.argmax(candidates))
                scores[t, target] = candidates[backpointers[t, target]] + log_emissions[t, target]
            scores[t] -= logsumexp(scores[t])

        path = np.zeros(rows.shape[0], dtype=int)
        path[-1] = int(np.argmax(scores[-1]))
        for t in range(rows.shape[0] - 2, -1, -1):
            path[t] = backpointers[t + 1, path[t + 1]]
        return path

    def filter_online(self, observation: object) -> np.ndarray:
        self._check_fitted()
        row = self._as_matrix(observation)
        if row.shape[0] != 1:
            raise ValueError("filter_online expects exactly one observation")
        if row.shape[1] != self.means_.shape[1]:
            raise ValueError("observation feature count does not match fitted model")

        emission = np.exp(self._log_emission_probabilities(row)[0])
        if self._online_filtered is None:
            predicted = self.initial_probs_
        else:
            predicted = self._online_filtered @ self.transition_matrix_
        self._online_filtered = self._normalize_vector(predicted * emission)
        return self._online_filtered.copy()

    def update_transition_matrix(self, recent_responsibilities: object) -> np.ndarray:
        self._check_fitted()
        responsibilities = self._as_matrix(recent_responsibilities)
        if responsibilities.shape[1] != self.n_states:
            raise ValueError("recent_responsibilities must have one column per state")
        responsibilities = self._normalize_rows(responsibilities)

        counts = np.full((self.n_states, self.n_states), EPS, dtype=float)
        if responsibilities.shape[0] == 1:
            counts += np.outer(responsibilities[0], responsibilities[0])
        else:
            for t in range(responsibilities.shape[0] - 1):
                counts += np.outer(responsibilities[t], responsibilities[t + 1])

        updated = self._normalize_rows(counts)
        keep = 1.0 - self.forgetting_rate
        self.transition_matrix_ = self._normalize_rows(
            keep * self.transition_matrix_ + self.forgetting_rate * updated
        )
        return self.transition_matrix_.copy()

    def predict(self, observations: object) -> HMMResult:
        forward_result = self.forward(observations)
        posterior = self.smooth(observations)
        path = self.viterbi(observations)
        return HMMResult(
            posterior=posterior,
            filtered=forward_result.probabilities,
            viterbi_path=path,
            log_likelihood=float(forward_result.log_likelihood),
        )

    def save(self, path: str | Path) -> None:
        self._check_fitted()
        payload = {
            "n_states": self.n_states,
            "covariance_type": self.covariance_type,
            "forgetting_rate": self.forgetting_rate,
            "random_seed": self.random_seed,
            "max_iter": self.max_iter,
            "tol": self.tol,
            "initial_probs": self.initial_probs_.tolist(),
            "transition_matrix": self.transition_matrix_.tolist(),
            "means": self.means_.tolist(),
            "covariances": self.covariances_.tolist(),
            "log_likelihood": self.log_likelihood_,
        }
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "AdaptiveHMM":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        model = cls(
            n_states=int(payload["n_states"]),
            covariance_type=str(payload.get("covariance_type", "diagonal")),
            forgetting_rate=float(payload.get("forgetting_rate", 0.05)),
            random_seed=int(payload.get("random_seed", 42)),
            max_iter=int(payload.get("max_iter", 25)),
            tol=float(payload.get("tol", 1e-4)),
        )
        model.initial_probs_ = np.asarray(payload["initial_probs"], dtype=float)
        model.transition_matrix_ = model._normalize_rows(payload["transition_matrix"])
        model.means_ = np.asarray(payload["means"], dtype=float)
        model.covariances_ = np.maximum(np.asarray(payload["covariances"], dtype=float), MIN_VARIANCE)
        model.log_likelihood_ = float(payload["log_likelihood"])
        return model

    @staticmethod
    def _as_matrix(observations: object) -> np.ndarray:
        if observations is None:
            raise ValueError("observations must not be None")

        if hasattr(observations, "to_numpy"):
            rows = observations.to_numpy(dtype=float)
        else:
            rows = np.asarray(observations, dtype=float)

        if rows.ndim == 1:
            rows = rows.reshape(-1, 1)
        if rows.ndim != 2:
            raise ValueError("observations must be a 2D array")
        if rows.shape[0] < 1:
            raise ValueError("observations must contain at least one sample")
        if rows.shape[1] < 1:
            raise ValueError("observations must contain at least one feature")
        if not np.isfinite(rows).all():
            raise ValueError("observations must contain only finite values")
        return rows.astype(float, copy=False)

    def _initial_labels(self, rows: np.ndarray) -> np.ndarray:
        labels = KMeans(n_clusters=self.n_states, n_init=10, random_state=self.random_seed).fit_predict(rows)
        labels = np.asarray(labels, dtype=int)
        if labels.shape == (rows.shape[0],):
            return labels

        order = np.argsort(rows[:, 0], kind="mergesort")
        labels = np.zeros(rows.shape[0], dtype=int)
        for rank, row_index in enumerate(order):
            labels[row_index] = min(self.n_states - 1, rank * self.n_states // rows.shape[0])
        return labels

    def _estimate_transition_from_labels(self, labels: np.ndarray) -> np.ndarray:
        counts = np.full((self.n_states, self.n_states), EPS, dtype=float)
        if labels.shape[0] == 1:
            counts[labels[0], labels[0]] += 1.0
        else:
            for source, target in zip(labels[:-1], labels[1:]):
                counts[int(source), int(target)] += 1.0
        return self._normalize_rows(counts)

    def _estimate_gaussians(self, rows: np.ndarray, labels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        responsibilities = np.zeros((rows.shape[0], self.n_states), dtype=float)
        responsibilities[np.arange(rows.shape[0]), labels] = 1.0
        return self._estimate_gaussians_from_responsibilities(rows, responsibilities)

    def _estimate_gaussians_from_responsibilities(
        self, rows: np.ndarray, responsibilities: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        responsibilities = self._normalize_rows(responsibilities)
        weights = responsibilities.sum(axis=0)
        global_mean = rows.mean(axis=0)
        global_var = np.maximum(rows.var(axis=0), MIN_VARIANCE)

        means = np.zeros((self.n_states, rows.shape[1]), dtype=float)
        covariances = np.zeros((self.n_states, rows.shape[1]), dtype=float)
        for state in range(self.n_states):
            if weights[state] <= EPS:
                means[state] = global_mean
                covariances[state] = global_var
                continue
            means[state] = (responsibilities[:, state, None] * rows).sum(axis=0) / weights[state]
            centered = rows - means[state]
            covariances[state] = (
                responsibilities[:, state, None] * centered * centered
            ).sum(axis=0) / weights[state]
        return means, np.maximum(covariances, MIN_VARIANCE)

    def _expected_transition_counts(
        self, rows: np.ndarray, backward: np.ndarray, scales: np.ndarray
    ) -> np.ndarray:
        log_emissions = self._log_emission_probabilities(rows)
        emissions = np.exp(log_emissions)
        counts = np.full((self.n_states, self.n_states), EPS, dtype=float)
        forward_result = self.forward(rows)

        for t in range(rows.shape[0] - 1):
            numerator = (
                forward_result.probabilities[t, :, None]
                * self.transition_matrix_
                * emissions[t + 1, None, :]
                * backward[t + 1, None, :]
            )
            denominator = max(float(numerator.sum()), EPS)
            counts += numerator / denominator
        return counts

    def _log_emission_probabilities(self, rows: np.ndarray) -> np.ndarray:
        self._check_fitted()
        log_probs = np.zeros((rows.shape[0], self.n_states), dtype=float)
        for state in range(self.n_states):
            covariance = np.diag(np.maximum(self.covariances_[state], MIN_VARIANCE))
            values = multivariate_normal.logpdf(
                rows,
                mean=self.means_[state],
                cov=covariance,
                allow_singular=True,
            )
            log_probs[:, state] = np.asarray(values, dtype=float)
        return np.nan_to_num(log_probs, nan=-1e12, neginf=-1e12, posinf=0.0)

    @staticmethod
    def _normalize_vector(values: object) -> np.ndarray:
        vector = np.asarray(values, dtype=float)
        vector = np.maximum(vector, EPS)
        total = max(float(vector.sum()), EPS)
        return vector / total

    @classmethod
    def _normalize_rows(cls, values: object) -> np.ndarray:
        matrix = np.asarray(values, dtype=float)
        if matrix.ndim != 2:
            raise ValueError("values must be a 2D array")
        normalized = np.zeros_like(matrix, dtype=float)
        for index, row in enumerate(matrix):
            normalized[index] = cls._normalize_vector(row)
        return normalized

    def _check_fitted(self) -> None:
        if (
            self.initial_probs_ is None
            or self.transition_matrix_ is None
            or self.means_ is None
            or self.covariances_ is None
        ):
            raise RuntimeError("AdaptiveHMM must be fitted before inference")
