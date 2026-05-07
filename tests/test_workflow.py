import csv
import json
from pathlib import Path

import yaml
from behavioral_stress.workflows.synthetic_workflow import run_synthetic_workflow


def test_run_synthetic_workflow_completes(tmp_path):
    cfg = {
        "random_seed": 3,
        "synthetic": {
            "n_steps": 50,
            "n_states": 3,
            "n_features": 6,
            "n_covariates": 1,
            "random_seed": 3,
        },
        "model": {"n_states": 3, "covariance_type": "diagonal", "forgetting_rate": 0.05},
        "outputs": {"directory": str(tmp_path)},
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    result = run_synthetic_workflow(path)
    expected_warning = (
        "Experimental research prototype. Not a validated recession predictor. "
        "Aggregate-level inference only."
    )
    expected_files = {
        "observations": "observations.csv",
        "covariates": "covariates.csv",
        "latent_states": "latent_states.csv",
        "codebook": "codebook.csv",
        "posterior": "posterior.csv",
        "filtered": "filtered.csv",
        "viterbi_path": "viterbi_path.csv",
        "transition_matrix": "transition_matrix.csv",
        "metrics": "metrics.csv",
        "run_metadata": "run_metadata.json",
    }

    assert result["output_dir"] == str(tmp_path)
    assert result["warning"] == expected_warning
    assert result["metrics"]
    assert set(result["files"]) == set(expected_files)
    for name, filename in expected_files.items():
        output = Path(result["files"][name])
        assert output == tmp_path / filename
        assert output.exists()

    assert _csv_shape(Path(result["files"]["posterior"])) == (50, 3)
    assert _csv_shape(Path(result["files"]["filtered"])) == (50, 3)
    assert _csv_shape(Path(result["files"]["viterbi_path"])) == (50, 1)
    assert _csv_shape(Path(result["files"]["transition_matrix"])) == (3, 3)
    assert "log_likelihood" in _csv_index(Path(result["files"]["metrics"]))

    metadata = json.loads(Path(result["files"]["run_metadata"]).read_text(encoding="utf-8"))
    assert metadata["warning"] == expected_warning


def _csv_shape(path: Path) -> tuple[int, int]:
    rows = list(csv.reader(path.read_text(encoding="utf-8").splitlines()))
    return len(rows) - 1, len(rows[0]) - 1


def _csv_index(path: Path) -> list[str]:
    rows = list(csv.reader(path.read_text(encoding="utf-8").splitlines()))
    return [row[0] for row in rows[1:]]
