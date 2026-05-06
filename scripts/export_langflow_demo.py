#!/usr/bin/env python
"""Validate the Langflow scaffold and print import instructions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_COMPONENTS = [
    "synthetic_data_component.py",
    "preprocessing_component.py",
    "ontology_signal_component.py",
    "adaptive_hmm_component.py",
    "validation_metrics_component.py",
    "report_component.py",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Langflow demo scaffold")
    parser.add_argument("--flow", type=Path, default=Path("langflow/behavioral_stress_flow.json"))
    args = parser.parse_args()
    payload = json.loads(args.flow.read_text(encoding="utf-8"))
    node_ids = {node["id"] for node in payload.get("nodes", [])}
    required_nodes = {"config", "synthetic_data", "preprocessing", "ontology", "adaptive_hmm", "metrics", "report"}
    missing = sorted(required_nodes - node_ids)
    if missing:
        raise SystemExit(f"Flow missing nodes: {missing}")
    component_dir = Path("langflow/custom_components")
    missing_components = [name for name in REQUIRED_COMPONENTS if not (component_dir / name).exists()]
    if missing_components:
        raise SystemExit(f"Missing custom components: {missing_components}")
    print(f"Validated Langflow flow JSON: {args.flow}")
    print(f"Custom components: {component_dir}")
    print("Import steps:")
    print("1. pip install -e .[langflow]")
    print("2. langflow run")
    print(f"3. Import {args.flow} and add custom components from {component_dir}")
    print("Fallback: python scripts/run_synthetic_demo.py --config configs/synthetic.yaml")


if __name__ == "__main__":
    main()
