"""Helpers for signal codebooks."""
from __future__ import annotations

import pandas as pd

from behavioral_stress.ontology.ontology import BehavioralOntology, default_ontology


def build_default_codebook(n_features: int = 9) -> pd.DataFrame:
    """Return a default synthetic signal codebook."""
    return default_ontology(n_features).to_dataframe()


def codebook_from_ontology(ontology: BehavioralOntology) -> pd.DataFrame:
    """Convert an ontology object to tabular signal metadata."""
    return ontology.to_dataframe()
