"""Adaptive Hidden Markov Model facade for syntax/runtime checks."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import numpy as np
from numpy.typing import ArrayLike, NDArray

EPS = 1e-12
FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


@dataclass
class HMMResult:
    """Inference outputs for one HMM sequence."""

    posterior: FloatArray
    filtered: FloatArray
    viterbi_path: IntArray
    log_likelihood: float


class AdaptiveHMM:
    """Small Gaussian-like HMM with deterministic initialization and scaled probabilities."""

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
        self.initial_probs_: FloatArray | None = None
        self.transition_matrix_: FloatArray | None = None
        self.means_: FloatArray | None = None
        self.variances_: FloatArray | None = None

    def fit(self, observations: ArrayLike) -> "AdaptiveHMM":
        """Initialize state means by sorting observations on their row average."""
        x = self._as_matrix(observations)
        if len(x) < self.n_states:
            raise ValueError("Need at least n_states observations")
        labels = self._initial_labels(x)
        means: list[FloatArray] = []
        variances: list[FloatArray] = []
        for state in range(self.n_states):
            members = x[labels == state]
            if len(members) == 0:
                members = x
            mean = members.mean(axis=0)
            var = np.maximum(((members - mean) ** 2).mean(axis=0), 1e-4)
            means.append(mean)
            variances.append(var)
        self.means_ = np.vstack(means).astype(float)
        self.variances_ = np.vstack(variances).astype(float)
        self.initial_probs_ = np.full(self.n_states, 1.0 / self.n_states, dtype=float)
        self.transition_matrix_ = self._estimate_transition_from_labels(labels)
        return self

    def forward(self, observations: ArrayLike) -> tuple[FloatArray, FloatArray, float]:
        """Run a scaled forward recursion."""
        self._check_fitted()
        x = self._as_matrix(observations)
        alpha = np.zeros((len(x), self.n_states), dtype=float)
        scales = np.zeros(len(x), dtype=float)
        likelihood = 0.0
        previous: FloatArray | None = None
        for row_idx, row in enumerate(x):
            emissions = self._emission_probabilities(row)
            if previous is None:
                current = self.initial_probs_ * emissions  # type: ignore[operator]
            else:
                current = previous @ self.transition_matrix_ * emissions  # type: ignore[operator]
            scale = max(float(current.sum()), EPS)
            scales[row_idx] = scale
            likelihood += math.log(scale)
            current = current / scale
            alpha[row_idx] = current
            previous = current
        return alpha, scales, float(likelihood)

    def backward(self, observations: ArrayLike, scales: ArrayLike) -> FloatArray:
        """Run a scaled backward recursion compatible with :meth:`forward`."""
        self._check_fitted()
        x = self._as_matrix(observations)
        scale_values = np.asarray(scales, dtype=float)
        beta = np.ones((len(x), self.n_states), dtype=float)
        for t in range(len(x) - 2, -1, -1):
            emissions = self._emission_probabilities(x[t + 1])
            beta[t] = (self.transition_matrix_ @ (emissions * beta[t + 1])) / max(  # type: ignore[operator]
                float(scale_values[t + 1]), EPS
            )
        return beta

    def smooth(self, observations: ArrayLike) -> FloatArray:
        """Return smoothed posterior probabilities whose rows sum to one."""
        alpha, scales, _ = self.forward(observations)
        beta = self.backward(observations, scales)
        rows = np.maximum(alpha * beta, EPS)
        return rows / rows.sum(axis=1, keepdims=True)

    def viterbi(self, observations: ArrayLike) -> IntArray:
        """Decode a simple most-likely state path from posterior probabilities."""
        posterior = self.smooth(observations)
        return posterior.argmax(axis=1).astype(np.int64)

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

    def update_transition_matrix(self, posterior_window: ArrayLike) -> FloatArray:
        """Blend transition probabilities with expected transitions from a posterior window."""
        self._check_fitted()
        rows = self._as_matrix(posterior_window)
        counts = np.full((self.n_states, self.n_states), 1e-3, dtype=float)
        for prev, cur in zip(rows, rows[1:]):
            counts += np.outer(prev, cur)
        empirical = counts / counts.sum(axis=1, keepdims=True)
        blended = (1 - self.forgetting_rate) * self.transition_matrix_ + self.forgetting_rate * empirical  # type: ignore[operator]
        self.transition_matrix_ = blended / blended.sum(axis=1, keepdims=True)
        return self.transition_matrix_

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
        model.transition_matrix_ = np.asarray(payload["transition_matrix"], dtype=float)
        model.means_ = np.asarray(payload["means"], dtype=float)
        model.variances_ = np.asarray(payload["variances"], dtype=float)
        return model

    def _initial_labels(self, x: FloatArray) -> IntArray:
        order = np.argsort(x.mean(axis=1))
        labels = np.zeros(len(x), dtype=np.int64)
        for rank, idx in enumerate(order):
            labels[idx] = min(self.n_states - 1, rank * self.n_states // len(x))
        return labels

    def _estimate_transition_from_labels(self, labels: IntArray) -> FloatArray:
        counts = np.ones((self.n_states, self.n_states), dtype=float)
        for src, dst in zip(labels, labels[1:]):
            counts[int(src), int(dst)] += 1.0
        return counts / counts.sum(axis=1, keepdims=True)

    def _emission_probabilities(self, row: FloatArray) -> FloatArray:
        distance = ((row - self.means_) ** 2 / self.variances_).sum(axis=1)  # type: ignore[operator]
        return np.exp(-0.5 * np.minimum(distance, 100.0)) + EPS

    @staticmethod
    def _as_matrix(observations: ArrayLike) -> FloatArray:
        matrix = np.asarray(observations, dtype=float)
        if matrix.ndim != 2:
            raise ValueError("observations must be a two-dimensional matrix")
        return matrix

    def _check_fitted(self) -> None:
        if (
            self.initial_probs_ is None
            or self.transition_matrix_ is None
            or self.means_ is None
            or self.variances_ is None
        ):
            raise RuntimeError("AdaptiveHMM must be fitted before inference")
