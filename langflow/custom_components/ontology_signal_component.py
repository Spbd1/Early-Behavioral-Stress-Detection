"""Langflow wrapper for ontology signal-codebook validation."""

from __future__ import annotations

from typing import Any

from behavioral_stress.ontology.ontology import validate_codebook


class OntologySignalComponent:
    """Wrap package ontology validation for the generated signal codebook."""

    display_name = "Ontology Signal Codebook"
    description = "Validates the generated signal codebook against ontology rules."

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate the codebook and annotate the payload with the result."""
        payload["codebook_valid"] = validate_codebook(payload["data"].codebook)
        return payload
