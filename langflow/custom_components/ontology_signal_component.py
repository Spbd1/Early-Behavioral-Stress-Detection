"""Langflow custom component scaffold for ontology-guided signals."""
from behavioral_stress.ontology.ontology import default_ontology


def load_default_ontology(n_features: int = 9):
    """Return the default synthetic signal ontology."""
    return default_ontology(n_features)
