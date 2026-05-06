import json
from pathlib import Path

from behavioral_stress.api.dashboard_data import build_dashboard_payload
from behavioral_stress.ops.config_validation import validate_runtime_config
from behavioral_stress.ops.environment import validate_environment
from behavioral_stress.ops.lineage import build_lineage_manifest, model_version_id
from behavioral_stress.ops.monitoring import compare_means_for_drift


def _valid_config(tmp_path: Path) -> dict[str, object]:
    return {
        "random_seed": 7,
        "synthetic": {
            "n_steps": 24,
            "n_states": 3,
            "n_features": 4,
            "n_covariates": 1,
            "freq": "W",
        },
        "model": {"n_states": 3, "covariance_type": "diagonal", "forgetting_rate": 0.05},
        "outputs": {"directory": str(tmp_path)},
    }


def test_config_validation_requires_deterministic_seed(tmp_path):
    cfg = _valid_config(tmp_path)
    assert validate_runtime_config(cfg).ok
    cfg.pop("random_seed")
    cfg["synthetic"] = {
        "n_steps": 24,
        "n_states": 3,
        "n_features": 4,
        "n_covariates": 1,
        "freq": "W",
    }
    report = validate_runtime_config(cfg)
    assert not report.ok
    assert any(issue.path == "random_seed" for issue in report.issues)


def test_environment_validation_redacts_secret(monkeypatch):
    monkeypatch.setenv("BEHAVIORAL_STRESS_API_TOKEN", "sensitive")
    report = validate_environment(optional_secret_vars=["BEHAVIORAL_STRESS_API_TOKEN"])
    encoded = json.dumps(report.as_dict())
    assert report.ok
    assert "sensitive" not in encoded
    assert "redacted" in encoded


def test_lineage_manifest_hashes_artifacts(tmp_path):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("stable", encoding="utf-8")
    manifest = build_lineage_manifest("run-1", [artifact], {"mode": "test"})
    assert manifest.artifacts[0].sha256
    assert model_version_id(manifest) == model_version_id(manifest)


def test_monitoring_recommends_rollback_on_drift():
    report = compare_means_for_drift({"x": [0, 0, 0]}, {"x": [1, 1, 1]}, warning_delta=0.5)
    assert report.rollback_recommended
    assert not report.ok


def test_dashboard_payload_contains_experimental_guardrails(tmp_path):
    payload = build_dashboard_payload(tmp_path, "configs/default.yaml")
    assert "Experimental" in payload["label"]
    assert payload["quality_warnings"]
    assert "locations" in payload
