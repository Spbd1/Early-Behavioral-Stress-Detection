"""Langflow custom-component wrapper for synthetic aggregate data generation."""
from __future__ import annotations

from behavioral_stress.data.synthetic import generate_synthetic_regime_data
from behavioral_stress.utils.config import load_config


class SyntheticDataComponent:
    """Wrap ``generate_synthetic_regime_data`` for Langflow-style orchestration."""

    display_name = "Synthetic Data Generator"

    def run(self, config_path: str = "configs/synthetic.yaml") -> dict:
        cfg = load_config(config_path)
        data = generate_synthetic_regime_data(**cfg.get("synthetic", {}))
        return {"data": data, "config": cfg}
