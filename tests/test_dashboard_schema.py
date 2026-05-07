import json

from behavioral_stress.api.dashboard_data import (
    SCHEMA_VERSION,
    build_dashboard_payload,
    validate_dashboard_payload,
    write_dashboard_payload,
)


def test_dashboard_payload_schema_snapshot_for_empty_static_build(tmp_path):
    payload = build_dashboard_payload(tmp_path, "configs/default.yaml")

    validate_dashboard_payload(payload)

    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["static_mode"] == {
        "supported": True,
        "data_file": "dashboard.json",
        "requires_backend": False,
    }
    assert set(payload["warnings"]) == {"data_quality", "drift", "geo_reliability"}
    assert payload["quality_warnings"] == payload["warnings"]["data_quality"]
    assert payload["drift_warnings"] == payload["warnings"]["drift"]
    assert payload["geo_reliability_warnings"] == payload["warnings"]["geo_reliability"]
    assert "not recession" in payload["system"]["claim_guardrail"]
    assert payload["reports"]["primary"] == payload["report"]
    assert payload["reports"]["export_status"] == "available_static_json_export"
    assert payload["geo_comparison"][0].keys() >= {
        "country",
        "region",
        "city",
        "bsi",
        "reliability_score",
        "warnings",
        "geo",
    }
    assert payload["report"]["warnings"] == payload["warnings"]


def test_write_dashboard_payload_outputs_valid_static_json(tmp_path):
    output = tmp_path / "dashboard.json"

    write_dashboard_payload(output, tmp_path, "configs/default.yaml")
    payload = json.loads(output.read_text(encoding="utf-8"))

    validate_dashboard_payload(payload)
    assert payload["static_mode"]["requires_backend"] is False
