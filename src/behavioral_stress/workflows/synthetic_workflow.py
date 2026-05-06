"""Runnable equivalent to the documented Langflow synthetic pipeline."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from behavioral_stress.data.preprocessing import standardize_frame, winsorize_frame
from behavioral_stress.data.synthetic import generate_synthetic_regime_data
from behavioral_stress.models.adaptive_hmm import AdaptiveHMM
from behavioral_stress.ontology.ontology import validate_codebook
from behavioral_stress.ops.config_validation import validate_runtime_config
from behavioral_stress.ops.lineage import build_lineage_manifest, model_version_id
from behavioral_stress.utils.config import load_config
from behavioral_stress.validation.synthetic_validation import evaluate_stress_probability

WORKFLOW_WARNING = (
    "Experimental research prototype. Not a validated recession predictor. "
    "Aggregate-level inference only."
)


def run_synthetic_workflow(config_path: str | Path) -> dict[str, Any]:
    """Run config → data → preprocessing → ontology → AdaptiveHMM → metrics → output files."""
    cfg = load_config(config_path)
    config_report = validate_runtime_config(cfg)
    if not config_report.ok:
        messages = "; ".join(f"{issue.path}: {issue.message}" for issue in config_report.issues)
        raise ValueError(f"Invalid workflow config: {messages}")
    synth_cfg = dict(cfg.get("synthetic", {}))
    seed = int(cfg.get("random_seed", synth_cfg.get("random_seed", 42)))
    synth_cfg["random_seed"] = seed
    data = generate_synthetic_regime_data(**synth_cfg)
    validate_codebook(data.codebook)

    observations_prepared = standardize_frame(winsorize_frame(data.observations))
    model_cfg = cfg.get("model", {})
    model = AdaptiveHMM(
        n_states=int(model_cfg.get("n_states", synth_cfg.get("n_states", 3))),
        covariance_type=str(model_cfg.get("covariance_type", "diagonal")),
        forgetting_rate=float(model_cfg.get("forgetting_rate", 0.05)),
        random_seed=seed,
    ).fit(observations_prepared.to_numpy())
    result = model.predict(observations_prepared.to_numpy())
    metrics = evaluate_stress_probability(data.latent_states.to_numpy(), result.posterior)
    metrics["log_likelihood"] = float(result.log_likelihood)

    out_dir = Path(cfg.get("outputs", {}).get("directory", "data/synthetic"))
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "observations": out_dir / "observations.csv",
        "covariates": out_dir / "covariates.csv",
        "latent_states": out_dir / "latent_states.csv",
        "codebook": out_dir / "codebook.csv",
        "posterior": out_dir / "posterior.csv",
        "filtered": out_dir / "filtered.csv",
        "viterbi_path": out_dir / "viterbi_path.csv",
        "transition_matrix": out_dir / "transition_matrix.csv",
        "metrics": out_dir / "metrics.csv",
        "run_metadata": out_dir / "run_metadata.json",
    }
    data.observations.to_csv(paths["observations"])
    data.covariates.to_csv(paths["covariates"])
    data.latent_states.to_csv(paths["latent_states"])
    data.codebook.to_csv(paths["codebook"], index=False)
    state_cols = [f"state_{i}" for i in range(model.n_states)]
    pd.DataFrame(result.posterior, index=data.observations.index, columns=state_cols).to_csv(
        paths["posterior"]
    )
    pd.DataFrame(result.filtered, index=data.observations.index, columns=state_cols).to_csv(
        paths["filtered"]
    )
    pd.Series(result.viterbi_path, index=data.observations.index, name="viterbi_state").to_csv(
        paths["viterbi_path"]
    )
    pd.DataFrame(
        model.transition_matrix_,
        columns=[f"to_{i}" for i in range(model.n_states)],
        index=[f"from_{i}" for i in range(model.n_states)],
    ).to_csv(paths["transition_matrix"])
    pd.Series(metrics.values(), index=metrics.keys(), name="value").to_csv(paths["metrics"])
    files = {name: str(path) for name, path in paths.items()}
    artifact_paths = [path for name, path in paths.items() if name != "run_metadata"]
    lineage = build_lineage_manifest(
        run_id=str(data.metadata.get("random_seed", seed)),
        artifact_paths=artifact_paths,
        metadata={"config_path": str(config_path), "deterministic": True},
    )
    version_id = model_version_id(lineage)
    metadata = {
        **data.metadata,
        "model": model_cfg,
        "model_version": version_id,
        "lineage": lineage.as_dict(),
        "config_validation": config_report.as_dict(),
        "outputs": files,
        "warning": WORKFLOW_WARNING,
    }
    paths["run_metadata"].write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return {
        "output_dir": str(out_dir),
        "metrics": metrics,
        "files": files,
        "warning": WORKFLOW_WARNING,
    }
