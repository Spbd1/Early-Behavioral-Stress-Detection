"""Synthetic aggregate behavioral stress data generation."""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Any

import pandas as pd

from behavioral_stress.ontology.signal_codebook import build_default_codebook


@dataclass
class SyntheticRegimeData:
    """Container for generated observations, covariates, latent states, and metadata."""

    observations: pd.DataFrame
    covariates: pd.DataFrame
    latent_states: pd.Series
    codebook: pd.DataFrame
    metadata: dict[str, Any]


def generate_synthetic_regime_data(
    n_steps: int = 300,
    n_states: int = 3,
    n_features: int = 9,
    n_covariates: int = 2,
    random_seed: int = 42,
    drift_strength: float = 0.02,
    include_count_features: bool = True,
    start_date: str = "2020-01-01",
    freq: str = "D",
) -> SyntheticRegimeData:
    """Generate aggregate traces with noisy latent behavioral stress regimes.

    The synthetic signal families follow the ontology levels used by the project:
    level 1 represents immediate elastic discretionary contraction, level 2
    represents deferred/semi-essential adjustment, and level 3 represents
    substitution, persistence, and micro-luxury responses.  Regime effects are
    deliberately noisy and partially overlapping so the latent states are useful
    for method validation without creating unrealistically perfect separation.
    """
    _validate_generation_args(n_steps, n_states, n_features, n_covariates)

    rng = random.Random(random_seed)
    transition = _transition_matrix(n_states)
    states = [0]
    for _ in range(1, n_steps):
        states.append(_sample_categorical(rng, transition[states[-1]]))

    index = pd.date_range(start=start_date, periods=n_steps, freq=freq)
    codebook = build_default_codebook(n_features=n_features, freq=freq)

    observations: list[list[float]] = []
    covariates: list[list[float]] = []
    for step, state in enumerate(states):
        stress = _stress_scale(state, n_states)
        seasonal = 0.35 * math.sin(2.0 * math.pi * step / 30.0)
        longer_cycle = 0.18 * math.cos(2.0 * math.pi * step / 91.0)
        drift = drift_strength * step / max(1, n_steps - 1)
        common_shock = rng.gauss(0.0, 0.35)

        covariates.append(
            _covariate_row(
                n_covariates=n_covariates,
                stress=stress,
                seasonal=seasonal,
                drift=drift,
                rng=rng,
            )
        )

        row: list[float] = []
        for feature in range(n_features):
            level = feature % 3
            feature_scale = 1.0 + 0.08 * (feature // 3)
            baseline = 10.0 + 0.25 * feature + 0.45 * seasonal + 0.25 * longer_cycle
            effect = _level_regime_effect(level, stress, feature_scale)
            heterogeneity = rng.gauss(0.0, 0.22)
            noise = rng.gauss(0.0, 1.05 + 0.20 * stress)
            value = (
                baseline
                + effect
                + drift * (feature + 1)
                + common_shock
                + heterogeneity
                + noise
            )
            if include_count_features and feature % 4 == 3:
                value = max(0.0, round(value))
            row.append(round(value, 6))
        observations.append(row)

    obs_cols = [f"synthetic_signal_{idx + 1:02d}" for idx in range(n_features)]
    cov_cols = [f"covariate_{idx + 1:02d}" for idx in range(n_covariates)]
    metadata: dict[str, Any] = {
        "n_steps": n_steps,
        "n_states": n_states,
        "n_features": n_features,
        "n_covariates": n_covariates,
        "random_seed": random_seed,
        "drift_strength": drift_strength,
        "include_count_features": include_count_features,
        "start_date": start_date,
        "freq": freq,
        "ontology_mapping": {
            "level_1": "immediate elastic discretionary contraction",
            "level_2": "deferred/semi-essential adjustment",
            "level_3": "substitution/persistence/micro-luxury response",
        },
        "warning": (
            "Synthetic aggregate research data only; not a diagnostic or recession forecast."
        ),
    }
    return SyntheticRegimeData(
        observations=pd.DataFrame(observations, columns=obs_cols, index=index),
        covariates=pd.DataFrame(covariates, columns=cov_cols, index=index),
        latent_states=pd.Series(states, index=index, name="latent_state"),
        codebook=codebook,
        metadata=metadata,
    )


def _validate_generation_args(
    n_steps: int,
    n_states: int,
    n_features: int,
    n_covariates: int,
) -> None:
    if n_steps <= 0:
        raise ValueError("n_steps must be positive")
    if n_states <= 0:
        raise ValueError("n_states must be positive")
    if n_features <= 0:
        raise ValueError("n_features must be positive")
    if n_covariates < 0:
        raise ValueError("n_covariates must be non-negative")


def _transition_matrix(n_states: int) -> list[list[float]]:
    if n_states == 1:
        return [[1.0]]
    stay = 0.82
    move = (1.0 - stay) / max(1, n_states - 1)
    return [[stay if i == j else move for j in range(n_states)] for i in range(n_states)]


def _stress_scale(state: int, n_states: int) -> float:
    if n_states == 1:
        return 0.0
    return state / (n_states - 1)


def _level_regime_effect(level: int, stress: float, feature_scale: float) -> float:
    if level == 0:
        return -2.0 * stress * feature_scale
    if level == 1:
        return -1.25 * (stress**1.15) * feature_scale
    return 1.45 * stress * feature_scale


def _covariate_row(
    n_covariates: int,
    stress: float,
    seasonal: float,
    drift: float,
    rng: random.Random,
) -> list[float]:
    values: list[float] = []
    templates = (
        seasonal + 0.25 * stress,
        drift + rng.gauss(0.0, 0.08),
        0.5 * seasonal - 0.15 * stress,
    )
    for idx in range(n_covariates):
        base = templates[idx % len(templates)]
        values.append(round(base + rng.gauss(0.0, 0.12), 6))
    return values


def _sample_categorical(rng: random.Random, probs: list[float]) -> int:
    draw = rng.random()
    total = 0.0
    for idx, prob in enumerate(probs):
        total += prob
        if draw <= total:
            return idx
    return len(probs) - 1
