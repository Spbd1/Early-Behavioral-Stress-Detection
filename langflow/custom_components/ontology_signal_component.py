"""Langflow wrapper for ontology signal-codebook validation."""
from __future__ import annotations

from behavioral_stress.ontology.ontology import validate_codebook


class OntologySignalComponent:
    """Validate and forward the ontology-derived codebook."""

    display_name = "Ontology Signal Codebook"

    def run(self, payload: dict) -> dict:
        validate_codebook(payload["data"].codebook)
        payload["codebook_valid"] = True
        return payload
