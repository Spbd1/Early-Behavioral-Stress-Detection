#!/usr/bin/env python
"""Run a reproducible synthetic AdaptiveHMM demo."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import typer

from behavioral_stress.data.preprocessing import standardize_frame
from behavioral_stress.data.synthetic import generate_synthetic_regime_data
from behavioral_stress.models.adaptive_hmm import AdaptiveHMM
from behavioral_stress.utils.config import load_config
from behavioral_stress.validation.synthetic_validation import evaluate_stress_probability

app = typer.Typer(add_completion=False)


@app.command()
def main(config: Path = typer.Option(Path("configs/synthetic.yaml"), "--config")) -> None:
    """Generate synthetic data, fit an AdaptiveHMM, and save demo outputs."""
    cfg = load_config(config)
    seed = int(cfg.get("random_seed", 42))
    synth_cfg = cfg.get("synthetic", {})
    data = generate_synthetic_regime_data(random_seed=seed, **synth_cfg)
    observations = standardize_frame(data.observations)
    model_cfg = cfg.get("model", {})
    model = AdaptiveHMM(
        n_states=int(model_cfg.get("n_states", synth_cfg.get("n_states", 3))),
        covariance_type=model_cfg.get("covariance_type", "diagonal"),
        forgetting_rate=float(model_cfg.get("forgetting_rate", 0.05)),
        random_seed=seed,
    ).fit(observations.values)
    result = model.predict(observations.values)
    metrics = evaluate_stress_probability(data.latent_states.values, result.posterior)

    out_dir = Path(cfg.get("outputs", {}).get("directory", "data/synthetic"))
    out_dir.mkdir(parents=True, exist_ok=True)
    data.observations.to_csv(out_dir / "observations.csv")
    data.covariates.to_csv(out_dir / "covariates.csv")
    data.latent_states.to_csv(out_dir / "latent_states.csv")
    data.codebook.to_csv(out_dir / "codebook.csv", index=False)
    pd.DataFrame(result.posterior, index=observations.index).to_csv(out_dir / "posterior.csv")
    pd.Series(result.viterbi_path, index=observations.index, name="viterbi_state").to_csv(out_dir / "viterbi_path.csv")
    pd.Series(metrics).to_csv(out_dir / "metrics.csv")
    typer.echo(f"Wrote synthetic demo outputs to {out_dir}")
    typer.echo(metrics)


if __name__ == "__main__":
    app()
