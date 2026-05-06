"""Behavioral signal ontology definitions for aggregate synthetic traces."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REQUIRED_CODEBOOK_COLUMNS = [
    "signal_name",
    "ontology_level",
    "behavioral_concept",
    "expected_direction_under_stress",
    "data_type",
    "frequency",
    "possible_biases",
    "notes",
]

LEVELS = (
    "level_1_immediate_discretionary_contraction",
    "level_2_deferred_semi_essential_adjustment",
    "level_3_substitution_persistence_micro_luxury_response",
)


@dataclass(frozen=True)
class BehavioralSignal:
    """Metadata for one aggregate behavioral signal."""

    signal_name: str
    ontology_level: str
    behavioral_concept: str
    expected_direction_under_stress: str
    data_type: str
    frequency: str
    possible_biases: list[str]
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON/YAML-serializable dictionary."""
        return asdict(self)


class BehavioralOntology:
    """Serializable collection of aggregate signal definitions."""

    def __init__(self, signals: list[BehavioralSignal]) -> None:
        self.signals = signals

    def to_dataframe(self) -> pd.DataFrame:
        """Return ontology signals as a codebook table."""
        return pd.DataFrame([signal.to_dict() for signal in self.signals])

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary payload for serialization."""
        return {"signals": [signal.to_dict() for signal in self.signals]}

    def to_yaml(self, path: str | Path) -> None:
        """Export the ontology to YAML."""
        Path(path).write_text(yaml.safe_dump(self.to_dict()), encoding="utf-8")

    def to_json(self, path: str | Path) -> None:
        """Export the ontology to JSON."""
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def from_yaml(cls, path: str | Path) -> "BehavioralOntology":
        """Load ontology signals from YAML."""
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return cls.from_dict(payload)

    @classmethod
    def from_json(cls, path: str | Path) -> "BehavioralOntology":
        """Load ontology signals from JSON."""
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BehavioralOntology":
        """Create an ontology from a dictionary payload."""
        return cls([BehavioralSignal(**item) for item in payload.get("signals", [])])


def default_ontology(n_features: int = 9, freq: str = "D") -> BehavioralOntology:
    """Create a default ontology used by the synthetic demo."""
    concepts = (
        "immediate elastic discretionary contraction",
        "deferred/semi-essential adjustment",
        "substitution/persistence/micro-luxury response",
    )
    signals: list[BehavioralSignal] = []
    for idx in range(n_features):
        level_idx = idx % 3
        signals.append(
            BehavioralSignal(
                signal_name=f"synthetic_signal_{idx + 1:02d}",
                ontology_level=LEVELS[level_idx],
                behavioral_concept=concepts[level_idx],
                expected_direction_under_stress="decrease" if level_idx in {0, 1} else "increase",
                data_type="count" if idx % 4 == 3 else "continuous",
                frequency=freq,
                possible_biases=[
                    "digital trace representativeness",
                    "platform measurement drift",
                    "seasonality and calendar effects",
                ],
                notes="Synthetic aggregate trace for cautious latent-regime method validation.",
            )
        )
    return BehavioralOntology(signals)


def validate_codebook(codebook: pd.DataFrame) -> bool:
    """Validate that a codebook contains required columns and valid ontology levels."""
    missing = [column for column in REQUIRED_CODEBOOK_COLUMNS if column not in codebook.columns]
    if missing:
        raise ValueError(f"Codebook missing required columns: {missing}")
    invalid_levels = set(codebook["ontology_level"]) - set(LEVELS)
    if invalid_levels:
        raise ValueError(f"Codebook contains invalid ontology levels: {sorted(invalid_levels)}")
    return True
