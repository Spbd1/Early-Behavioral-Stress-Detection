"""Validation helpers for synthetic data with known regimes."""
from __future__ import annotations

import numpy as np

from behavioral_stress.validation.metrics import binary_classification_metrics


def evaluate_stress_probability(latent_states: np.ndarray, posterior: np.ndarray, stress_state: int | None = None) -> dict[str, float]:
    """Evaluate posterior probability of a stress-or-higher regime on synthetic labels."""
    if stress_state is None:
        stress_state = posterior.shape[1] - 1
    y_true = (np.asarray(latent_states) >= stress_state).astype(int)
    y_score = posterior[:, stress_state:].sum(axis=1)
    return binary_classification_metrics(y_true, y_score)
