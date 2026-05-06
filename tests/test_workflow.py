from pathlib import Path

import yaml

from behavioral_stress.workflows.synthetic_workflow import run_synthetic_workflow


def test_run_synthetic_workflow_completes(tmp_path):
    cfg = {
        "random_seed": 3,
        "synthetic": {"n_steps": 50, "n_states": 3, "n_features": 6, "n_covariates": 1, "random_seed": 3},
        "model": {"n_states": 3, "covariance_type": "diagonal", "forgetting_rate": 0.05},
        "outputs": {"directory": str(tmp_path)},
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    result = run_synthetic_workflow(path)
    assert result["metrics"]
    for output in result["paths"].values():
        assert Path(output).exists()
