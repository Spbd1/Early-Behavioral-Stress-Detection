"""Langflow wrapper for synthetic validation metrics."""
from __future__ import annotations

from behavioral_stress.validation.synthetic_validation import evaluate_stress_probability


class ValidationMetricsComponent:
    """Compute metrics against known synthetic latent regimes."""

    display_name = "Validation Metrics"

    def run(self, payload: dict) -> dict:
        payload["metrics"] = evaluate_stress_probability(payload["data"].latent_states.values, payload["result"].posterior)
        return payload
