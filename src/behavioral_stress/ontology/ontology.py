"""Behavioral signal ontology definitions.

The ontology is descriptive and interpretive. It does not establish causal mechanisms or
individual-level behavioral diagnoses from aggregate traces.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd
import yaml
from pydantic import BaseModel, Field

OntologyLevel = Literal[
    "level_1_immediate_discretionary_contraction",
    "level_2_deferred_semi_essential_adjustment",
    "level_3_substitution_persistence_micro_luxury_response",
]
DataType = Literal["continuous", "count", "categorical"]


class SignalDefinition(BaseModel):
    """Metadata for one aggregate behavioral signal."""

    signal_name: str
    ontology_level: OntologyLevel
    behavioral_concept: str
    expected_direction_under_stress: Literal["increase", "decrease", "mixed", "unknown"]
    data_type: DataType = "continuous"
    frequency: str = "weekly"
    possible_biases: list[str] = Field(default_factory=list)
    notes: str = ""


class BehavioralOntology(BaseModel):
    """Serializable collection of signal definitions."""

    signals: list[SignalDefinition]

    def to_dataframe(self) -> pd.DataFrame:
        """Return the ontology as a pandas DataFrame."""
        return pd.DataFrame([signal.model_dump() for signal in self.signals])

    def to_yaml(self, path: str | Path) -> None:
        """Serialize the ontology to YAML."""
        payload = {"signals": [signal.model_dump() for signal in self.signals]}
        Path(path).write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    @classmethod
    def from_yaml(cls, path: str | Path) -> "BehavioralOntology":
        """Load an ontology from YAML."""
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(payload)


def default_ontology(n_features: int = 9) -> BehavioralOntology:
    """Create a compact default ontology for synthetic demonstrations."""
    levels: list[OntologyLevel] = [
        "level_1_immediate_discretionary_contraction",
        "level_2_deferred_semi_essential_adjustment",
        "level_3_substitution_persistence_micro_luxury_response",
    ]
    concepts = [
        "discretionary search/spend contraction",
        "deferred semi-essential adjustment",
        "substitution and micro-luxury persistence",
    ]
    signals: list[SignalDefinition] = []
    for idx in range(n_features):
        level_idx = idx % 3
        signals.append(
            SignalDefinition(
                signal_name=f"synthetic_signal_{idx + 1:02d}",
                ontology_level=levels[level_idx],
                behavioral_concept=concepts[level_idx],
                expected_direction_under_stress="decrease" if level_idx < 2 else "increase",
                data_type="count" if idx % 4 == 3 else "continuous",
                possible_biases=["digital trace representativeness", "platform/API measurement drift"],
                notes="Synthetic aggregate feature for reproducible method validation.",
            )
        )
    return BehavioralOntology(signals=signals)
