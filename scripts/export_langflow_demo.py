#!/usr/bin/env python
"""Validate the Langflow scaffold and print import instructions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FLOW = Path("langflow/behavioral_stress_flow.json")
COMPONENT_DIR = Path("langflow/custom_components")
REQUIRED_COMPONENTS = [
    "synthetic_data_component.py",
    "preprocessing_component.py",
    "ontology_signal_component.py",
    "adaptive_hmm_component.py",
    "validation_metrics_component.py",
    "report_component.py",
]
REQUIRED_NODES = {
    "config",
    "synthetic_data",
    "preprocessing",
    "ontology",
    "adaptive_hmm",
    "metrics",
    "report",
}
REQUIRED_EDGES = [
    ["config", "synthetic_data"],
    ["synthetic_data", "preprocessing"],
    ["preprocessing", "ontology"],
    ["ontology", "adaptive_hmm"],
    ["adaptive_hmm", "metrics"],
    ["metrics", "report"],
]
PROTOTYPE_WARNING = (
    "Experimental research prototype. Not a validated recession predictor. "
    "Aggregate-level inference only."
)


def _repo_path(path: Path) -> Path:
    """Resolve a CLI path relative to the repository root."""
    return path if path.is_absolute() else REPO_ROOT / path


def _default_flow_payload() -> dict[str, Any]:
    return {
        "name": "behavioral_stress_synthetic_workflow",
        "description": "Synthetic aggregate latent-regime research workflow.",
        "nodes": [
            {
                "id": "config",
                "type": "input_config",
                "label": "Input Config",
                "config_path": "configs/synthetic.yaml",
            },
            {
                "id": "synthetic_data",
                "type": "custom_component",
                "component": "SyntheticDataComponent",
            },
            {
                "id": "preprocessing",
                "type": "custom_component",
                "component": "PreprocessingComponent",
            },
            {"id": "ontology", "type": "custom_component", "component": "OntologySignalComponent"},
            {"id": "adaptive_hmm", "type": "custom_component", "component": "AdaptiveHMMComponent"},
            {
                "id": "metrics",
                "type": "custom_component",
                "component": "ValidationMetricsComponent",
            },
            {"id": "report", "type": "custom_component", "component": "ReportComponent"},
        ],
        "edges": REQUIRED_EDGES,
        "fallback_runner": "behavioral_stress.workflows.synthetic_workflow:run_synthetic_workflow",
        "responsible_use_warning": PROTOTYPE_WARNING,
    }


def _load_or_generate_flow(flow_path: Path, generate_missing: bool) -> dict[str, Any]:
    if flow_path.exists():
        try:
            return json.loads(flow_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Flow JSON is invalid at {flow_path}: {exc}") from exc

    if not generate_missing:
        raise RuntimeError(f"Flow JSON not found: {flow_path}")

    if flow_path != _repo_path(DEFAULT_FLOW):
        raise RuntimeError(f"Refusing to generate non-default flow path: {flow_path}")

    payload = _default_flow_payload()
    flow_path.parent.mkdir(parents=True, exist_ok=True)
    flow_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def _validate_flow(payload: dict[str, Any], flow_path: Path, component_dir: Path) -> None:
    node_ids = {node.get("id") for node in payload.get("nodes", []) if isinstance(node, dict)}
    missing_nodes = sorted(REQUIRED_NODES - node_ids)
    if missing_nodes:
        raise RuntimeError(f"Flow missing nodes: {', '.join(missing_nodes)}")

    edges = payload.get("edges", [])
    normalized_edges = []
    for edge in edges:
        if isinstance(edge, dict):
            normalized_edges.append([edge.get("source"), edge.get("target")])
        else:
            normalized_edges.append(edge)
    missing_edges = [edge for edge in REQUIRED_EDGES if edge not in normalized_edges]
    if missing_edges:
        raise RuntimeError(f"Flow missing edges: {missing_edges}")

    warning = str(payload.get("responsible_use_warning", ""))
    if "not a validated recession predictor" not in warning.lower():
        raise RuntimeError(
            "Flow must include a responsible-use warning that it is not a "
            "validated recession predictor."
        )

    missing_components = [
        name for name in REQUIRED_COMPONENTS if not (component_dir / name).exists()
    ]
    if missing_components:
        raise RuntimeError(
            f"Missing custom components in {component_dir}: {', '.join(missing_components)}"
        )

    if not flow_path.exists():
        raise RuntimeError(f"Flow was not written: {flow_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate or generate the Langflow demo JSON for the "
            "behavioral-stress research prototype. This is not a reliable "
            "recession prediction tool."
        )
    )
    parser.add_argument(
        "--flow",
        type=Path,
        default=DEFAULT_FLOW,
        help="Path to the Langflow JSON, relative to the repository root by default.",
    )
    parser.add_argument(
        "--no-generate",
        action="store_true",
        help="Validate only; fail instead of generating the default flow JSON if it is missing.",
    )
    args = parser.parse_args()

    flow_path = _repo_path(args.flow)
    component_dir = _repo_path(COMPONENT_DIR)

    try:
        payload = _load_or_generate_flow(flow_path, generate_missing=not args.no_generate)
        _validate_flow(payload, flow_path, component_dir)
    except Exception as exc:
        print(f"ERROR: Langflow demo export failed: {exc}", file=sys.stderr)
        return 1

    display_flow = (
        flow_path.relative_to(REPO_ROOT) if flow_path.is_relative_to(REPO_ROOT) else flow_path
    )
    display_components = (
        component_dir.relative_to(REPO_ROOT)
        if component_dir.is_relative_to(REPO_ROOT)
        else component_dir
    )
    print(f"Validated Langflow flow JSON: {display_flow}")
    print(f"Custom components: {display_components}")
    print(f"Warning: {payload['responsible_use_warning']}")
    print("Import steps:")
    print("1. pip install -e .[langflow]")
    print("2. langflow run")
    print(f"3. Import {display_flow} in Langflow.")
    print(
        "4. Add custom components from "
        f"{display_components} if your Langflow installation does not load "
        "them automatically."
    )
    print("Fallback runner: python scripts/run_synthetic_demo.py --config configs/synthetic.yaml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
