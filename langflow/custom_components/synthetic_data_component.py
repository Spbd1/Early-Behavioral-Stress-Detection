"""Langflow wrapper for package synthetic aggregate data generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from behavioral_stress.data.synthetic import generate_synthetic_regime_data
from behavioral_stress.utils.config import load_config


class SyntheticDataComponent:
    """Wrap ``generate_synthetic_regime_data`` for Langflow-style orchestration."""

    display_name = "Synthetic Data Generator"
    description = "Loads a config file and generates synthetic aggregate regime data."

    def run(self, payload: dict[str, Any] | str | Path | None = None) -> dict[str, Any]:
        """Return a payload containing generated data and its loaded configuration."""
        config_path = _config_path_from_payload(payload)
        cfg = load_config(config_path)
        synth_cfg = dict(cfg.get("synthetic", {}))
        seed = int(cfg.get("random_seed", synth_cfg.get("random_seed", 42)))
        synth_cfg["random_seed"] = seed
        data = generate_synthetic_regime_data(**synth_cfg)
        return {"config_path": str(config_path), "config": cfg, "data": data}


def _config_path_from_payload(payload: dict[str, Any] | str | Path | None) -> str | Path:
    if payload is None:
        return "configs/synthetic.yaml"
    if isinstance(payload, (str, Path)):
        return payload
    return payload.get("config_path") or payload.get("path") or "configs/synthetic.yaml"
