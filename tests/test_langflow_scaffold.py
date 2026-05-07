import json
from pathlib import Path


def test_langflow_json_and_components_exist():
    flow = json.loads(Path("langflow/behavioral_stress_flow.json").read_text(encoding="utf-8"))
    node_ids = {node["id"] for node in flow["nodes"]}
    assert {
        "config",
        "synthetic_data",
        "preprocessing",
        "ontology",
        "adaptive_hmm",
        "metrics",
        "report",
    }.issubset(node_ids)
    for name in [
        "synthetic_data_component.py",
        "preprocessing_component.py",
        "ontology_signal_component.py",
        "adaptive_hmm_component.py",
        "validation_metrics_component.py",
        "report_component.py",
    ]:
        assert (Path("langflow/custom_components") / name).exists()
