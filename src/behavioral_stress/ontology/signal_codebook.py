"""Helpers for ontology-derived signal codebooks."""
from __future__ import annotations

import pandas as pd

from behavioral_stress.ontology.ontology import BehavioralOntology, default_ontology, validate_codebook


def build_default_codebook(n_features: int = 9, freq: str = "D") -> pd.DataFrame:
    """Return the default synthetic signal codebook."""
    codebook = default_ontology(n_features=n_features, freq=freq).to_dataframe()
    validate_codebook(codebook)
    return codebook


def codebook_from_ontology(ontology: BehavioralOntology) -> pd.DataFrame:
    """Convert an ontology object to a validated table."""
    codebook = ontology.to_dataframe()
    validate_codebook(codebook)
    return codebook


__all__ = ["build_default_codebook", "codebook_from_ontology", "validate_codebook"]
