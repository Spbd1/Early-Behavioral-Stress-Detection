"""Adaptive Gaussian Hidden Markov Model utilities.

This module keeps a compact, valid Python implementation of the adaptive HMM
used by the focused tests.  It uses only the Python standard library so the
module remains importable before optional scientific dependencies are present.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import json
import math
from pathlib import Path
from typing import Sequence


class _FiniteResult:
    def __init__(self, values: list[list[bool]]) -> None:
        self._values = values

    def all(self) -> bool:
        return all(value for row in self._values for value in row)


class _ArrayCompat:
    def __init__(self, values: object) -> None:
        self._rows, self.ndim, self.shape = self._coerce(values)

    @staticmethod
    def _coerce(values: object) -> tuple[list[list[float]], int, tuple[int, ...]]:
        if isinstance(values, (str, bytes)) or not hasattr(values, "__iter__"):
            return [], 0, ()

        sequence = list(values)  # type: ignore[arg-type]
        if not sequence:
            return [], 1, (0,)

        first = sequence[0]
        if isinstance(first, (str, bytes)):
            raise ValueError("could not convert string to float")
        if hasattr(first, "__iter__"):
            rows = [[float(value) for value in row] for row in sequence]  # type: ignore[union-attr]
            if any(len(row) != len(rows[0]) for row in rows):
                raise ValueError("observations must have consistent row widths")
            return rows, 2, (len(rows), len(rows[0]))

        rows = [[float(value)] for value in sequence]
        return rows, 1, (len(rows),)

    def reshape(self, rows: int, columns: int) -> "_ArrayCompat":
        if (rows, columns) != (-1, 1):
            raise ValueError("compatibility array only supports reshape(-1, 1)")
        reshaped = _ArrayCompat([])
        reshaped._rows = self._rows
        reshaped.ndim = 2
        reshaped.shape = (len(self._rows), 1)
        return reshaped

    def tolist(self) -> list[list[float]]:
        return [list(row) for row in self._rows]


class _NumpyCompat:
    @staticmethod
    def asarray(values: object, dtype: type[float] = float) -> _ArrayCompat:
        del dtype
        return _ArrayCompat(values)

    @staticmethod
    def isfinite(values: _ArrayCompat) -> _FiniteResult:
        return _FiniteResult([[math.isfinite(value) for value in row] for row in values.tolist()])


if importlib.util.find_spec("numpy") is not None:
    np = importlib.import_module("numpy")
else:
    np = _NumpyCompat()

EPS = 1e-12
MIN_VARIANCE = 1e-6

Vector = list[float]
Matrix = list[Vector]
PathVector = list[int]
ArrayLike = Sequence[float] | Sequence[Sequence[float]]


@dataclass
class HMMResult:
    """Inference outputs for one observation sequence."""

    posterior: Matrix
    filtered: Matrix
    viterbi_path: PathVector
    log_likelihood: float


class AdaptiveHMM:
    """Diagonal Gaussian Hidden Markov Model with adaptive transitions."""

    def __init__(
        self,
        n_states: int,
        covariance_type: str = "diagonal",
        forgetting_rate: float = 0.05,
        random_seed: int = 42,
    ) -> None:
        if n_states < 2:
            raise ValueError("n_states must be at least 2")
        if covariance_type != "diagonal":
            raise ValueError("covariance_type must be 'diagonal'")
        if not 0.0 <= forgetting_rate <= 1.0:
            raise ValueError("forgetting_rate must be in [0, 1]")

        self.n_states = n_states
        self.covariance_type = covariance_type
        self.forgetting_rate = forgetting_rate
        self.random_seed = random_seed
        self.initial_probs_: Vector | None = None
        self.transition_matrix_: Matrix | None = None
        self.means_: Matrix | None = None
        self.variances_: Matrix | None = None

    def fit(self, observations: ArrayLike) -> "AdaptiveHMM":
        """Initialize model parameters from observations."""
        rows = self._as_matrix(observations)
        if len(rows) < self.n_states:
            raise ValueError("Need at least n_states observations")

        labels = self._initial_labels(rows)
        feature_count = len(rows[0])
        global_mean = self._column_means(rows)
        global_var = self._column_variances(rows, global_mean)

        means: Matrix = []
        variances: Matrix = []
        for state in range(self.n_states):
            members = [row for row, label in zip(rows, labels) if label == state]
            if members:
                state_mean = self._column_means(members)
                state_var = self._column_variances(members, state_mean)
            else:
                state_mean = list(global_mean)
                state_var = list(global_var)
            if len(state_mean) != feature_count:
                raise ValueError("inconsistent observation dimensions")
            means.append(state_mean)
            variances.append(state_var)

        initial_counts = [EPS for _ in range(self.n_states)]
        initial_counts[labels[0]] += 1.0

        self.initial_probs_ = self._normalize_vector(initial_counts)
        self.transition_matrix_ = self._estimate_transition_from_labels(labels)
        self.means_ = means
        self.variances_ = variances
        return self

    def forward(self, observations: ArrayLike) -> tuple[Matrix, Vector, float]:
        """Run scaled forward filtering."""
        self._check_fitted()
        rows = self._as_matrix(observations)
        emissions = self._emission_probabilities(rows)
        initial = self.initial_probs_ or []
        transitions = self.transition_matrix_ or []

        filtered: Matrix = []
        scales: Vector = []

        current = [initial[state] * emissions[0][state] for state in range(self.n_states)]
        scale = max(sum(current), EPS)
        filtered.append([value / scale for value in current])
        scales.append(scale)

        for t in range(1, len(rows)):
            predicted = [
                sum(filtered[t - 1][source] * transitions[source][target] for source in range(self.n_states))
                for target in range(self.n_states)
            ]
            current = [predicted[state] * emissions[t][state] for state in range(self.n_states)]
            scale = max(sum(current), EPS)
            filtered.append([value / scale for value in current])
            scales.append(scale)

        return filtered, scales, sum(math.log(scale) for scale in scales)

    def backward(self, observations: ArrayLike, scales: Sequence[float]) -> Matrix:
        """Run scaled backward recursion using forward-pass scales."""
        self._check_fitted()
        rows = self._as_matrix(observations)
        if len(scales) != len(rows):
            raise ValueError("scales must have one value per observation")

        emissions = self._emission_probabilities(rows)
        transitions = self.transition_matrix_ or []
        backward: Matrix = [[1.0 for _ in range(self.n_states)] for _ in rows]

        for t in range(len(rows) - 2, -1, -1):
            for source in range(self.n_states):
                total = 0.0
                for target in range(self.n_states):
                    total += transitions[source][target] * emissions[t + 1][target] * backward[t + 1][target]
                backward[t][source] = total / max(float(scales[t + 1]), EPS)

        return backward

    def smooth(self, observations: ArrayLike) -> Matrix:
        """Return normalized smoothed state probabilities."""
        filtered, scales, _ = self.forward(observations)
        backward = self.backward(observations, scales)
        return self._normalize_rows(
            [
                [filtered[t][state] * backward[t][state] for state in range(self.n_states)]
                for t in range(len(filtered))
            ]
        )

    def viterbi(self, observations: ArrayLike) -> PathVector:
        """Decode the most likely latent-state path in log space."""
        self._check_fitted()
        rows = self._as_matrix(observations)
        emissions = self._emission_probabilities(rows)
        initial = self.initial_probs_ or []
        transitions = self.transition_matrix_ or []

        scores: Matrix = [[0.0 for _ in range(self.n_states)] for _ in rows]
        backpointers: list[list[int]] = [[0 for _ in range(self.n_states)] for _ in rows]

        for state in range(self.n_states):
            scores[0][state] = math.log(max(initial[state], EPS)) + math.log(max(emissions[0][state], EPS))
        self._center_log_scores(scores[0])

        for t in range(1, len(rows)):
            for target in range(self.n_states):
                candidates = [
                    scores[t - 1][source] + math.log(max(transitions[source][target], EPS))
                    for source in range(self.n_states)
                ]
                best_source = max(range(self.n_states), key=lambda source: candidates[source])
                backpointers[t][target] = best_source
                scores[t][target] = candidates[best_source] + math.log(max(emissions[t][target], EPS))
            self._center_log_scores(scores[t])

        path = [0 for _ in rows]
        path[-1] = max(range(self.n_states), key=lambda state: scores[-1][state])
        for t in range(len(rows) - 2, -1, -1):
            path[t] = backpointers[t + 1][path[t + 1]]
        return path

    def filter_online(
        self,
        observation: Sequence[float] | float,
        previous_filtered: Sequence[float] | None = None,
    ) -> Vector:
        """Filter a single observation."""
        self._check_fitted()
        row = self._as_single_observation(observation)
        emissions = self._emission_probabilities([row])[0]
        transitions = self.transition_matrix_ or []

        if previous_filtered is None:
            prior = list(self.initial_probs_ or [])
        else:
            previous = self._normalize_vector(previous_filtered)
            prior = [
                sum(previous[source] * transitions[source][target] for source in range(self.n_states))
                for target in range(self.n_states)
            ]

        return self._normalize_vector([prior[state] * emissions[state] for state in range(self.n_states)])

    def update_transition_matrix(self, posterior_window: ArrayLike) -> Matrix:
        """Update transition probabilities from adjacent posterior rows."""
        self._check_fitted()
        posterior = self._normalize_rows(self._as_matrix(posterior_window))
        if any(len(row) != self.n_states for row in posterior):
            raise ValueError("posterior_window must have n_states columns")

        counts = [[EPS for _ in range(self.n_states)] for _ in range(self.n_states)]
        for previous, current in zip(posterior[:-1], posterior[1:]):
            for source in range(self.n_states):
                for target in range(self.n_states):
                    counts[source][target] += previous[source] * current[target]

        empirical = self._normalize_rows(counts)
        old = self.transition_matrix_ or []
        blended = [
            [
                (1.0 - self.forgetting_rate) * old[source][target]
                + self.forgetting_rate * empirical[source][target]
                for target in range(self.n_states)
            ]
            for source in range(self.n_states)
        ]
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
        """Save fitted model parameters as JSON."""
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
        """Load fitted model parameters from JSON."""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        model = cls(
            n_states=payload["n_states"],
            covariance_type=payload["covariance_type"],
            forgetting_rate=payload["forgetting_rate"],
            random_seed=payload["random_seed"],
        )
        model.initial_probs_ = model._normalize_vector(payload["initial_probs"])
        model.transition_matrix_ = model._normalize_rows(payload["transition_matrix"])
        model.means_ = [[float(value) for value in row] for row in payload["means"]]
        model.variances_ = [
            [max(float(value), MIN_VARIANCE) for value in row]
            for row in payload["variances"]
        ]
        return model

    def _initial_labels(self, rows: Matrix) -> PathVector:
        scores = [(index, sum(row) / len(row)) for index, row in enumerate(rows)]
        ordered = sorted(scores, key=lambda item: item[1])
        labels = [0 for _ in rows]
        for rank, (index, _) in enumerate(ordered):
            labels[index] = min(self.n_states - 1, rank * self.n_states // len(rows))
        return labels

    def _estimate_transition_from_labels(self, labels: PathVector) -> Matrix:
        counts = [[1.0 for _ in range(self.n_states)] for _ in range(self.n_states)]
        for source, target in zip(labels[:-1], labels[1:]):
            counts[source][target] += 1.0
        return self._normalize_rows(counts)

    def _emission_probabilities(self, rows: Matrix) -> Matrix:
        self._check_fitted()
        means = self.means_ or []
        variances = self.variances_ or []
        probabilities: Matrix = []
        for row in rows:
            row_probs: Vector = []
            for state in range(self.n_states):
                log_prob = 0.0
                for value, mean, variance in zip(row, means[state], variances[state]):
                    safe_variance = max(variance, MIN_VARIANCE)
                    log_prob += -0.5 * (
                        math.log(2.0 * math.pi * safe_variance)
                        + ((value - mean) ** 2) / safe_variance
                    )
                row_probs.append(max(math.exp(max(min(log_prob, -math.log(EPS)), math.log(EPS))), EPS))
            probabilities.append(row_probs)
        return probabilities

    @staticmethod
    def _as_matrix(observations: ArrayLike) -> Matrix:
        if observations is None:
            raise ValueError("observations must not be None")

        if hasattr(observations, "to_numpy"):
            rows = observations.to_numpy(dtype=float)  # type: ignore[attr-defined]
            if not hasattr(rows, "ndim"):
                rows = np.asarray(rows, dtype=float)
        else:
            rows = np.asarray(observations, dtype=float)

        if rows.ndim == 1:
            rows = rows.reshape(-1, 1)
        if rows.ndim != 2:
            raise ValueError("observations must be a 2D array")
        if rows.shape[0] < 1:
            raise ValueError("observations must contain at least one row")
        if rows.shape[1] < 1:
            raise ValueError("observations must contain at least one feature")
        if not np.isfinite(rows).all():
            raise ValueError("observations must be finite")
        return rows.tolist()

    def _as_single_observation(self, observation: Sequence[float] | float) -> Vector:
        if isinstance(observation, (int, float)):
            row = [float(observation)]
        else:
            row = [float(value) for value in observation]
        if self.means_ is not None and len(row) != len(self.means_[0]):
            raise ValueError("observation feature count does not match fitted model")
        if not row or any(not math.isfinite(value) for value in row):
            raise ValueError("observation must be finite")
        return row

    @staticmethod
    def _column_means(rows: Matrix) -> Vector:
        width = len(rows[0])
        return [sum(row[column] for row in rows) / len(rows) for column in range(width)]

    @staticmethod
    def _column_variances(rows: Matrix, means: Sequence[float]) -> Vector:
        return [
            max(sum((row[column] - means[column]) ** 2 for row in rows) / len(rows), MIN_VARIANCE)
            for column in range(len(means))
        ]

    @staticmethod
    def _normalize_vector(values: Sequence[float]) -> Vector:
        vector = [max(float(value), EPS) for value in values]
        total = max(sum(vector), EPS)
        return [value / total for value in vector]

    @classmethod
    def _normalize_rows(cls, values: Sequence[Sequence[float]]) -> Matrix:
        return [cls._normalize_vector(row) for row in values]

    @staticmethod
    def _center_log_scores(scores: Vector) -> None:
        largest = max(scores)
        total = sum(math.exp(score - largest) for score in scores)
        log_total = largest + math.log(max(total, EPS))
        for index, score in enumerate(scores):
            scores[index] = score - log_total

    def _check_fitted(self) -> None:
        if (
            self.initial_probs_ is None
            or self.transition_matrix_ is None
            or self.means_ is None
            or self.variances_ is None
        ):
            raise RuntimeError("AdaptiveHMM must be fitted before inference")
