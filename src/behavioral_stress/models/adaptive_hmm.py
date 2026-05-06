"""Dependency-free adaptive Hidden Markov Model facade for syntax/runtime checks."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Iterable

from behavioral_stress.simple_frame import Matrix, Vector

EPS = 1e-12


@dataclass
class HMMResult:
    """Inference outputs for one HMM sequence."""

    posterior: Matrix
    filtered: Matrix
    viterbi_path: Vector
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
        self.initial_probs_: Vector | None = None
        self.transition_matrix_: Matrix | None = None
        self.means_: Matrix | None = None
        self.variances_: Matrix | None = None

    def fit(self, observations: Iterable[Iterable[float]]) -> "AdaptiveHMM":
        """Initialize state means by sorting observations on their row average."""
        x = self._as_matrix(observations)
        if len(x) < self.n_states:
            raise ValueError("Need at least n_states observations")
        labels = self._initial_labels(x)
        n_features = x.shape[1]
        means: list[list[float]] = []
        variances: list[list[float]] = []
        for state in range(self.n_states):
            members = [row for row, label in zip(x, labels) if label == state] or list(x)
            mean = [sum(row[col] for row in members) / len(members) for col in range(n_features)]
            var = []
            for col in range(n_features):
                value = sum((row[col] - mean[col]) ** 2 for row in members) / len(members)
                var.append(max(value, 1e-4))
            means.append(mean)
            variances.append(var)
        self.means_ = Matrix(means)
        self.variances_ = Matrix(variances)
        self.initial_probs_ = Vector([1.0 / self.n_states for _ in range(self.n_states)])
        self.transition_matrix_ = self._estimate_transition_from_labels(labels)
        return self

    def forward(self, observations: Iterable[Iterable[float]]) -> tuple[Matrix, Vector, float]:
        """Run a scaled forward recursion."""
        self._check_fitted()
        x = self._as_matrix(observations)
        alpha: list[list[float]] = []
        scales = Vector([])
        likelihood = 0.0
        previous: list[float] | None = None
        for row in x:
            emissions = self._emission_probabilities(row)
            if previous is None:
                current = [self.initial_probs_[s] * emissions[s] for s in range(self.n_states)]  # type: ignore[index]
            else:
                current = []
                for state in range(self.n_states):
                    incoming = sum(previous[src] * self.transition_matrix_[src][state] for src in range(self.n_states))  # type: ignore[index]
                    current.append(incoming * emissions[state])
            scale = max(sum(current), EPS)
            scales.append(scale)
            likelihood += math.log(scale)
            current = [value / scale for value in current]
            alpha.append(current)
            previous = current
        return Matrix(alpha), scales, float(likelihood)

    def backward(self, observations: Iterable[Iterable[float]], scales: Vector) -> Matrix:
        """Run a scaled backward recursion compatible with :meth:`forward`."""
        self._check_fitted()
        x = self._as_matrix(observations)
        beta = [[1.0 for _ in range(self.n_states)] for _ in x]
        for t in range(len(x) - 2, -1, -1):
            emissions = self._emission_probabilities(x[t + 1])
            for state in range(self.n_states):
                beta[t][state] = sum(
                    self.transition_matrix_[state][next_state] * emissions[next_state] * beta[t + 1][next_state]  # type: ignore[index]
                    for next_state in range(self.n_states)
                ) / max(scales[t + 1], EPS)
        return Matrix(beta)

    def smooth(self, observations: Iterable[Iterable[float]]) -> Matrix:
        """Return smoothed posterior probabilities whose rows sum to one."""
        alpha, scales, _ = self.forward(observations)
        beta = self.backward(observations, scales)
        rows = []
        for a_row, b_row in zip(alpha, beta):
            row = [max(a * b, EPS) for a, b in zip(a_row, b_row)]
            total = sum(row)
            rows.append([value / total for value in row])
        return Matrix(rows)

    def viterbi(self, observations: Iterable[Iterable[float]]) -> Vector:
        """Decode a simple most-likely state path from posterior probabilities."""
        posterior = self.smooth(observations)
        return Vector([max(range(self.n_states), key=lambda state: row[state]) for row in posterior])

    def predict(self, observations: Iterable[Iterable[float]]) -> HMMResult:
        """Return filtered, smoothed, Viterbi, and likelihood outputs."""
        filtered, _, log_likelihood = self.forward(observations)
        posterior = self.smooth(observations)
        return HMMResult(
            posterior=posterior,
            filtered=filtered,
            viterbi_path=self.viterbi(observations),
            log_likelihood=log_likelihood,
        )

    def update_transition_matrix(self, posterior_window: Iterable[Iterable[float]]) -> Matrix:
        """Blend transition probabilities with expected transitions from a posterior window."""
        self._check_fitted()
        rows = self._as_matrix(posterior_window)
        counts = [[1e-3 for _ in range(self.n_states)] for _ in range(self.n_states)]
        for prev, cur in zip(rows, rows[1:]):
            for i in range(self.n_states):
                for j in range(self.n_states):
                    counts[i][j] += prev[i] * cur[j]
        empirical = []
        for row in counts:
            total = sum(row)
            empirical.append([value / total for value in row])
        blended = []
        for old, new in zip(self.transition_matrix_, empirical):  # type: ignore[arg-type]
            row = [(1 - self.forgetting_rate) * o + self.forgetting_rate * n for o, n in zip(old, new)]
            total = sum(row)
            blended.append([value / total for value in row])
        self.transition_matrix_ = Matrix(blended)
        return self.transition_matrix_

    def save(self, path: str | Path) -> None:
        """Save fitted parameters as JSON."""
        payload = {
            "n_states": self.n_states,
            "covariance_type": self.covariance_type,
            "forgetting_rate": self.forgetting_rate,
            "random_seed": self.random_seed,
            "initial_probs": self.initial_probs_,
            "transition_matrix": self.transition_matrix_,
            "means": self.means_,
            "variances": self.variances_,
        }
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "AdaptiveHMM":
        """Load fitted parameters from JSON."""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        model = cls(payload["n_states"], payload["covariance_type"], payload["forgetting_rate"], payload["random_seed"])
        model.initial_probs_ = Vector(payload["initial_probs"])
        model.transition_matrix_ = Matrix(payload["transition_matrix"])
        model.means_ = Matrix(payload["means"])
        model.variances_ = Matrix(payload["variances"])
        return model

    def _initial_labels(self, x: Matrix) -> Vector:
        scores = [(idx, sum(row) / len(row)) for idx, row in enumerate(x)]
        ordered = sorted(scores, key=lambda item: item[1])
        labels = [0 for _ in x]
        for rank, (idx, _) in enumerate(ordered):
            labels[idx] = min(self.n_states - 1, rank * self.n_states // len(x))
        return Vector(labels)

    def _estimate_transition_from_labels(self, labels: Vector) -> Matrix:
        counts = [[1.0 for _ in range(self.n_states)] for _ in range(self.n_states)]
        for src, dst in zip(labels, labels[1:]):
            counts[int(src)][int(dst)] += 1.0
        return Matrix([[value / sum(row) for value in row] for row in counts])

    def _emission_probabilities(self, row: list[float]) -> list[float]:
        probs = []
        for state in range(self.n_states):
            distance = 0.0
            for col, value in enumerate(row):
                mean = self.means_[state][col]  # type: ignore[index]
                var = self.variances_[state][col]  # type: ignore[index]
                distance += (value - mean) ** 2 / var
            probs.append(math.exp(-0.5 * min(distance, 100.0)) + EPS)
        return probs

    @staticmethod
    def _as_matrix(observations: Iterable[Iterable[float]]) -> Matrix:
        if isinstance(observations, Matrix):
            return Matrix([list(map(float, row)) for row in observations])
        return Matrix([list(map(float, row)) for row in observations])

    def _check_fitted(self) -> None:
        if self.initial_probs_ is None or self.transition_matrix_ is None or self.means_ is None or self.variances_ is None:
            raise RuntimeError("AdaptiveHMM must be fitted before inference")
