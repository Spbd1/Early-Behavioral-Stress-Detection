"""Validation helpers for synthetic data with known regimes."""
from __future__ import annotations

import numpy as np

from behavioral_stress.data.preprocessing import standardize_frame
from behavioral_stress.data.synthetic import generate_synthetic_regime_data
from behavioral_stress.models.adaptive_hmm import AdaptiveHMM
from behavioral_stress.validation.metrics import binary_classification_metrics


def evaluate_stress_probability(latent_states: np.ndarray, posterior: np.ndarray, stress_state: int | None = None) -> dict[str, float]:
    """Evaluate posterior probability assigned to stress-or-higher synthetic regimes."""
    if stress_state is None:
        stress_state = posterior.shape[1] - 1
    y_true = (np.asarray(latent_states) >= stress_state).astype(int)
    y_score = posterior[:, stress_state:].sum(axis=1)
    return binary_classification_metrics(y_true, y_score)


def compare_inferred_to_true_regimes(latent_states: np.ndarray, inferred_states: np.ndarray) -> dict[str, float]:
    """Return simple agreement diagnostics without assuming label identifiability is solved."""
    latent_states = np.asarray(latent_states)
    inferred_states = np.asarray(inferred_states)
    return {"raw_state_agreement": float(np.mean(latent_states == inferred_states))}


def run_synthetic_validation(n_steps: int = 240, random_seed: int = 42) -> dict[str, float]:
    """Run one end-to-end synthetic validation experiment."""
    data = generate_synthetic_regime_data(n_steps=n_steps, random_seed=random_seed)
    x = standardize_frame(data.observations).values
    model = AdaptiveHMM(n_states=int(data.metadata["n_states"]), random_seed=random_seed).fit(x)
    result = model.predict(x)
    metrics = evaluate_stress_probability(data.latent_states.values, result.posterior)
    metrics["log_likelihood"] = float(result.log_likelihood)
    return metrics
