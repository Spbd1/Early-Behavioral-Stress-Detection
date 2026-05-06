"""Synthetic aggregate behavioral stress data generation."""
from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Any

from behavioral_stress.ontology.signal_codebook import build_default_codebook
from behavioral_stress.simple_frame import DataFrame, Series


@dataclass
class SyntheticRegimeData:
    """Container for generated observations, covariates, latent states, and metadata."""

    observations: DataFrame
    covariates: DataFrame
    latent_states: Series
    codebook: DataFrame
    metadata: dict[str, Any]


def generate_synthetic_regime_data(
    n_steps: int = 240,
    n_states: int = 3,
    n_features: int = 9,
    n_covariates: int = 2,
    random_seed: int = 42,
    drift_strength: float = 0.02,
    include_count_features: bool = True,
    start_date: str = "2018-01-01",
    freq: str = "W",
) -> SyntheticRegimeData:
    """Generate a deterministic aggregate latent-regime toy data set."""
    rng = random.Random(random_seed)
    transition = _transition_matrix(n_states)
    states = [0]
    for _ in range(1, n_steps):
        states.append(_sample_categorical(rng, transition[states[-1]]))

    index = [f"t_{step:04d}" for step in range(n_steps)]
    observations: list[list[float]] = []
    covariates: list[list[float]] = []
    for step, state in enumerate(states):
        seasonal = 0.25 * _sin(step / 8.0)
        drift = drift_strength * step
        covariates.append([round(seasonal + rng.gauss(0.0, 0.15), 6) for _ in range(n_covariates)])
        row: list[float] = []
        for feature in range(n_features):
            direction = -1.0 if feature % 3 in {0, 1} else 1.0
            mean = 10.0 + direction * state * 1.7 + seasonal + drift * (feature + 1) / n_features
            value = mean + rng.gauss(0.0, 0.8 + 0.15 * state)
            if include_count_features and feature % 4 == 3:
                value = max(0.0, round(value))
            row.append(round(value, 6))
        observations.append(row)

    obs_cols = [f"synthetic_signal_{idx + 1:02d}" for idx in range(n_features)]
    cov_cols = [f"covariate_{idx + 1:02d}" for idx in range(n_covariates)]
    metadata = {
        "n_steps": n_steps,
        "n_states": n_states,
        "n_features": n_features,
        "n_covariates": n_covariates,
        "random_seed": random_seed,
        "start_date": start_date,
        "freq": freq,
        "warning": "Synthetic aggregate research data only; not a diagnostic or recession forecast.",
    }
    return SyntheticRegimeData(
        observations=DataFrame(observations, columns=obs_cols, index=index),
        covariates=DataFrame(covariates, columns=cov_cols, index=index),
        latent_states=Series(states, index=index, name="latent_state"),
        codebook=build_default_codebook(n_features=n_features, freq=freq),
        metadata=metadata,
    )


def _transition_matrix(n_states: int) -> list[list[float]]:
    stay = 0.86
    move = (1.0 - stay) / max(1, n_states - 1)
    return [[stay if i == j else move for j in range(n_states)] for i in range(n_states)]


def _sample_categorical(rng: random.Random, probs: list[float]) -> int:
    draw = rng.random()
    total = 0.0
    for idx, prob in enumerate(probs):
        total += prob
        if draw <= total:
            return idx
    return len(probs) - 1


def _sin(value: float) -> float:
    import math

    return math.sin(value)
