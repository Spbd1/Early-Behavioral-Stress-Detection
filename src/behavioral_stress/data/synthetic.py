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
    """Container for synthetic observations, covariates, latent states, and metadata."""

    observations: pd.DataFrame
    covariates: pd.DataFrame
    latent_states: pd.Series
    codebook: pd.DataFrame
    metadata: dict[str, Any]


def _default_transition_matrix(n_states: int) -> np.ndarray:
    matrix = np.full((n_states, n_states), 0.05 / max(n_states - 1, 1), dtype=float)
    np.fill_diagonal(matrix, 0.95)
    if n_states == 3:
        matrix = np.array([[0.92, 0.07, 0.01], [0.08, 0.84, 0.08], [0.03, 0.12, 0.85]])
    matrix /= matrix.sum(axis=1, keepdims=True)
    return matrix


def _simulate_states(rng: np.random.Generator, n_steps: int, transition: np.ndarray) -> np.ndarray:
    states = np.zeros(n_steps, dtype=int)
    for t in range(1, n_steps):
        states[t] = rng.choice(transition.shape[0], p=transition[states[t - 1]])
    return states


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
    """Generate aggregate synthetic traces with known latent regimes.

    Regime separation is intentionally moderate: signals contain shared shocks, seasonality, drift,
    and observation noise so synthetic validation is informative but not unrealistically perfect.
    """
    if n_steps < 5:
        raise ValueError("n_steps must be at least 5")
    if n_states < 2:
        raise ValueError("n_states must be at least 2")
    if n_features < 1:
        raise ValueError("n_features must be positive")

    rng = np.random.default_rng(random_seed)
    index = pd.date_range(start=start_date, periods=n_steps, freq=freq)
    transition = _default_transition_matrix(n_states)
    states = _simulate_states(rng, n_steps, transition)

    time = np.arange(n_steps)
    covariates = pd.DataFrame(index=index)
    for j in range(n_covariates):
        seasonal = np.sin(2 * np.pi * time / max(24, 52) + j)
        covariates[f"covariate_{j + 1:02d}"] = seasonal + 0.2 * rng.normal(size=n_steps)

    codebook = build_default_codebook(n_features=n_features, freq=freq)
    observations = pd.DataFrame(index=index)
    stress_axis = np.linspace(0.0, 1.0, n_states)
    shared_shock = rng.normal(0, 0.35, size=n_steps)

    for feature_idx in range(n_features):
        level_idx = feature_idx % 3
        baseline = rng.normal(0.0, 0.25)
        loading = rng.uniform(0.7, 1.3)
        sign = -1.0 if level_idx in {0, 1} else 1.0
        if level_idx == 1:
            effect = sign * loading * np.sqrt(stress_axis[states] + 0.05)
        elif level_idx == 2:
            effect = sign * loading * (0.35 + stress_axis[states])
        else:
            effect = sign * loading * stress_axis[states]
        drift = drift_strength * (time / max(n_steps - 1, 1)) * rng.normal(0.0, 1.0)
        cov_effect = 0.15 * covariates.sum(axis=1).to_numpy() if n_covariates else 0.0
        noise = rng.normal(0.0, 0.65, size=n_steps)
        values = baseline + effect + 0.25 * shared_shock + cov_effect + drift + noise

        if include_count_features and codebook.loc[feature_idx, "data_type"] == "count":
            # Overdispersed aggregate count trace with non-perfect state separation.
            mu = np.exp(2.2 + values / 2.5)
            r = 8.0
            p = r / (r + mu)
            values = nbinom(n=r, p=p).rvs(random_state=rng)
        observations[codebook.loc[feature_idx, "signal_name"]] = values

    latent_states = pd.Series(states, index=index, name="latent_state")
    metadata = {
        "n_steps": n_steps,
        "n_states": n_states,
        "n_features": n_features,
        "n_covariates": n_covariates,
        "random_seed": random_seed,
        "drift_strength": drift_strength,
        "include_count_features": include_count_features,
        "start_date": start_date,
        "freq": freq,
        "transition_matrix": transition.tolist(),
        "warning": "Synthetic aggregate-level latent regimes for research validation only.",
    }
    return SyntheticRegimeData(observations, covariates, latent_states, codebook, metadata)
