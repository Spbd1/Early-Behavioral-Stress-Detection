#!/usr/bin/env python
"""Run validation for the synthetic latent-regime research prototype."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


REQUIRED_PACKAGES = ("numpy", "pandas", "scipy", "sklearn", "yaml")


REQUIRED_VALIDATION_OUTPUTS = {"metrics", "posterior", "filtered", "run_metadata"}


def _repo_path(path: Path) -> Path:
    """Resolve a CLI path relative to the repository root."""
    return path if path.is_absolute() else REPO_ROOT / path


def _validate_workflow_outputs(result: dict[str, Any]) -> None:
    files = result.get("files")
    if not isinstance(files, dict):
        raise RuntimeError("Validation workflow did not return a 'files' mapping.")

    missing_keys = sorted(REQUIRED_VALIDATION_OUTPUTS - set(files))
    if missing_keys:
        raise RuntimeError(
            f"Validation result is missing output entries: {', '.join(missing_keys)}"
        )

    missing_files = [name for name in REQUIRED_VALIDATION_OUTPUTS if not Path(files[name]).exists()]
    if missing_files:
        raise RuntimeError(
            f"Validation outputs were not written: {', '.join(sorted(missing_files))}"
        )


def _missing_runtime_packages() -> list[str]:
    return [package for package in REQUIRED_PACKAGES if importlib.util.find_spec(package) is None]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the validation-config synthetic workflow for aggregate behavioral-stress metrics. "
            "This is not a reliable recession prediction tool."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/validation.yaml"),
        help="Path to the validation YAML config, relative to the repository root by default.",
    )
    args = parser.parse_args()

    config_path = _repo_path(args.config)
    if not config_path.exists():
        parser.error(f"Config file not found: {config_path}")

    missing_packages = _missing_runtime_packages()
    if missing_packages:
        print(
            "ERROR: validation workflow requires missing Python packages: "
            + ", ".join(missing_packages)
            + ". Install project dependencies with: pip install -e .",
            file=sys.stderr,
        )
        return 1

    import pandas as pd

    from behavioral_stress.workflows.synthetic_workflow import run_synthetic_workflow

    try:
        result = run_synthetic_workflow(config_path)
        _validate_workflow_outputs(result)
        metrics_path = Path(result["output_dir"]) / "validation_summary.csv"
        pd.Series(result["metrics"], name="value").to_csv(metrics_path)
    except Exception as exc:
        print(f"ERROR: validation workflow failed: {exc}", file=sys.stderr)
        return 1

    print(f"Validation metrics written to {metrics_path}")
    warning = result.get("warning", "Research prototype; not a reliable recession predictor.")
    print(f"Warning: {warning}")
    print("Metrics:")
    for name, value in result["metrics"].items():
        print(f"  {name}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
