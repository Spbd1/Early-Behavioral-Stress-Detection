"""Langflow wrapper for package synthetic validation metrics."""
from __future__ import annotations

from typing import Any

from behavioral_stress.validation.synthetic_validation import evaluate_stress_probability


class ValidationMetricsComponent:
    """Wrap validation metric calculation for known synthetic latent regimes."""

    display_name = "Validation Metrics"
    description = "Evaluates inferred stress probability against synthetic latent states."

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Attach validation metrics and model log-likelihood to the payload."""
        metrics = evaluate_stress_probability(
            payload["data"].latent_states.to_numpy(),
            payload["result"].posterior,
        )
        metrics["log_likelihood"] = float(payload["result"].log_likelihood)
        payload["metrics"] = metrics
        return payload
