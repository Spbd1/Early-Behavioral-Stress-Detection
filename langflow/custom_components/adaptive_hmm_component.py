"""Langflow wrapper for package AdaptiveHMM fit and prediction."""

from __future__ import annotations

from typing import Any

from behavioral_stress.models.adaptive_hmm import AdaptiveHMM


class AdaptiveHMMComponent:
    """Wrap ``AdaptiveHMM`` training and inference for the scaffold flow."""

    display_name = "Adaptive HMM Fit + Predict"
    description = "Fits the package AdaptiveHMM and attaches posterior/filter/path outputs."

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Fit AdaptiveHMM on prepared observations and attach the model result."""
        cfg = payload.get("config", {})
        model_cfg = cfg.get("model", {})
        synth_cfg = cfg.get("synthetic", {})
        seed = int(cfg.get("random_seed", synth_cfg.get("random_seed", 42)))
        observations = payload["observations_prepared"].to_numpy()
        model = AdaptiveHMM(
            n_states=int(model_cfg.get("n_states", synth_cfg.get("n_states", 3))),
            covariance_type=str(model_cfg.get("covariance_type", "diagonal")),
            forgetting_rate=float(model_cfg.get("forgetting_rate", 0.05)),
            random_seed=seed,
        ).fit(observations)
        payload["model"] = model
        payload["result"] = model.predict(observations)
        return payload
