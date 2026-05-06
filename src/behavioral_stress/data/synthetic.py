"""Synthetic aggregate digital trace generator with known latent regimes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import nbinom

from behavioral_stress.ontology.signal_codebook import build_default_codebook


@dataclass(frozen=True)
class SyntheticRegimeData:
    """Container for synthetic observations, covariates, states, and metadata."""

    observations: pd.DataFrame
    covariates: pd.DataFrame
    latent_states: pd.Series
    codebook: pd.DataFrame
    transition_matrix: np.ndarray
    metadata: dict[str, Any]


def _default_transition_matrix(n_states: int) -> np.ndarray:
    matrix = np.full((n_states, n_states), 0.05 / max(n_states - 1, 1))
    np.fill_diagonal(matrix, 0.95)
    if n_states >= 3:
        matrix[0] = np.array([0.92, 0.07, 0.01] + [0.0] * (n_states - 3))[:n_states]
        matrix[1] = np.array([0.08, 0.84, 0.08] + [0.0] * (n_states - 3))[:n_states]
        matrix[2] = np.array([0.03, 0.12, 0.85] + [0.0] * (n_states - 3))[:n_states]
    matrix = matrix + 1e-6
    return matrix / matrix.sum(axis=1, keepdims=True)


def generate_synthetic_regime_data(
    n_steps: int = 240,
    n_states: int = 3,
    n_features: int = 9,
    n_covariates: int = 2,
    start_date: str = "2018-01-01",
    frequency: str = "W",
    include_counts: bool = True,
    concept_drift: bool = True,
    random_seed: int = 42,
) -> SyntheticRegimeData:
    """Generate aggregate traces with Gaussian and optional count-like emissions.

    The returned latent states are ground truth for simulation validation only. They are not
    claims about real-world recessions or individual behavioral states.
    """
    rng = np.random.default_rng(random_seed)
    dates = pd.date_range(start=start_date, periods=n_steps, freq=frequency)
    transition_matrix = _default_transition_matrix(n_states)

    states = np.zeros(n_steps, dtype=int)
    for t in range(1, n_steps):
        states[t] = rng.choice(n_states, p=transition_matrix[states[t - 1]])

    covariates = rng.normal(size=(n_steps, n_covariates))
    if n_covariates:
        covariates[:, 0] += np.linspace(-0.5, 0.5, n_steps)

    base_means = np.zeros((n_states, n_features))
    for state in range(n_states):
        stress_scale = state / max(n_states - 1, 1)
        for feature in range(n_features):
            level = feature % 3
            if level == 0:
                base_means[state, feature] = -1.5 * stress_scale
            elif level == 1:
                base_means[state, feature] = -0.8 * stress_scale
            else:
                base_means[state, feature] = 0.9 * stress_scale

    observations = np.zeros((n_steps, n_features), dtype=float)
    count_columns: set[int] = set(range(3, n_features, 4)) if include_counts else set()
    drift = np.linspace(0.0, 0.4, n_steps) if concept_drift else np.zeros(n_steps)
    for t, state in enumerate(states):
        means = base_means[state].copy()
        means[2::3] += drift[t]
        means += 0.15 * covariates[t, :1].sum() if n_covariates else 0.0
        for feature in range(n_features):
            if feature in count_columns:
                mu = np.exp(1.2 + means[feature])
                r = 8.0
                p = r / (r + mu)
                observations[t, feature] = nbinom.rvs(r, p, random_state=rng)
            else:
                observations[t, feature] = rng.normal(means[feature], 0.5 + 0.1 * state)

    obs_cols = [f"synthetic_signal_{i + 1:02d}" for i in range(n_features)]
    cov_cols = [f"covariate_{i + 1:02d}" for i in range(n_covariates)]
    codebook = build_default_codebook(n_features)
    for idx in count_columns:
        codebook.loc[codebook["signal_name"] == obs_cols[idx], "data_type"] = "count"

    return SyntheticRegimeData(
        observations=pd.DataFrame(observations, index=dates, columns=obs_cols),
        covariates=pd.DataFrame(covariates, index=dates, columns=cov_cols),
        latent_states=pd.Series(states, index=dates, name="latent_state"),
        codebook=codebook,
        transition_matrix=transition_matrix,
        metadata={
            "n_steps": n_steps,
            "n_states": n_states,
            "n_features": n_features,
            "n_covariates": n_covariates,
            "count_columns": sorted(obs_cols[i] for i in count_columns),
            "concept_drift": concept_drift,
        },
    )
