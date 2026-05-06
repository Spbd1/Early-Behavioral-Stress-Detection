"""Synthetic validation helpers for stress-regime probabilities."""
from __future__ import annotations

from typing import Iterable

from behavioral_stress.validation.metrics import binary_classification_metrics


def evaluate_stress_probability(latent_states: Iterable[int], posterior: Iterable[Iterable[float]]) -> dict[str, float]:
    """Evaluate the probability assigned to the highest-index stress state."""
    states = [int(value) for value in latent_states]
    rows = [list(map(float, row)) for row in posterior]
    if not states or not rows:
        return {}
    stress_state = max(states)
    stress_prob = [row[min(stress_state, len(row) - 1)] for row in rows]
    target = [1 if state == stress_state else 0 for state in states]
    metrics = binary_classification_metrics(target, stress_prob)
    metrics["stress_state"] = float(stress_state)
    return metrics
