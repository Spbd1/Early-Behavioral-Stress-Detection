"""Langflow wrapper for AdaptiveHMM fit and prediction."""
from __future__ import annotations

from behavioral_stress.models.adaptive_hmm import AdaptiveHMM


class AdaptiveHMMComponent:
    """Fit the package AdaptiveHMM and attach inference outputs."""

    display_name = "Adaptive HMM Fit + Predict"

    def run(self, payload: dict) -> dict:
        cfg = payload.get("config", {})
        model_cfg = cfg.get("model", {})
        synth_cfg = cfg.get("synthetic", {})
        x = payload["observations_prepared"].values
        model = AdaptiveHMM(
            n_states=int(model_cfg.get("n_states", synth_cfg.get("n_states", 3))),
            covariance_type=model_cfg.get("covariance_type", "diagonal"),
            forgetting_rate=float(model_cfg.get("forgetting_rate", 0.05)),
            random_seed=int(cfg.get("random_seed", synth_cfg.get("random_seed", 42))),
        ).fit(x)
        payload["model"] = model
        payload["result"] = model.predict(x)
        return payload
