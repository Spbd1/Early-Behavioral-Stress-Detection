"""Langflow wrapper for preprocessing aggregate synthetic observations."""
from __future__ import annotations

from behavioral_stress.data.preprocessing import standardize_frame, winsorize_frame


class PreprocessingComponent:
    """Winsorize and standardize observation frames without duplicating model logic."""

    display_name = "Preprocessing / Standardization"

    def run(self, payload: dict) -> dict:
        data = payload["data"]
        payload["observations_prepared"] = standardize_frame(winsorize_frame(data.observations))
        return payload
