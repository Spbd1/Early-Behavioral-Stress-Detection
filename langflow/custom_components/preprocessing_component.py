"""Langflow wrapper for preprocessing aggregate synthetic observations."""

from __future__ import annotations

from typing import Any

from behavioral_stress.data.preprocessing import standardize_frame, winsorize_frame


class PreprocessingComponent:
    """Wrap package preprocessing helpers without duplicating transformation logic."""

    display_name = "Preprocessing / Standardization"
    description = "Winsorizes and standardizes generated observation frames."

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Attach a prepared observations frame to the Langflow payload."""
        data = payload["data"]
        payload["observations_prepared"] = standardize_frame(winsorize_frame(data.observations))
        return payload
