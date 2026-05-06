#!/usr/bin/env python
"""Run validation for the synthetic latent-regime prototype."""
from __future__ import annotations

import argparse
from pathlib import Path

from behavioral_stress.simple_frame import Series
from behavioral_stress.workflows.synthetic_workflow import run_synthetic_workflow


def main() -> None:
    parser = argparse.ArgumentParser(description="Run synthetic validation")
    parser.add_argument("--config", type=Path, default=Path("configs/validation.yaml"))
    args = parser.parse_args()
    result = run_synthetic_workflow(args.config)
    metrics_path = Path(result["output_dir"]) / "validation_summary.csv"
    Series(result["metrics"].values(), index=result["metrics"].keys(), name="value").to_csv(metrics_path)
    print(f"Validation metrics written to {metrics_path}")
    print(result["metrics"])


if __name__ == "__main__":
    main()
