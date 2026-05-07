#!/usr/bin/env python
"""Run the synthetic AdaptiveHMM demo and write expected output files."""

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


EXPECTED_OUTPUT_KEYS = {
    "observations",
    "covariates",
    "latent_states",
    "codebook",
    "posterior",
    "filtered",
    "viterbi_path",
    "transition_matrix",
    "metrics",
    "run_metadata",
}


def _repo_path(path: Path) -> Path:
    """Resolve a CLI path relative to the repository root."""
    return path if path.is_absolute() else REPO_ROOT / path


def _validate_outputs(result: dict[str, Any]) -> None:
    files = result.get("files")
    if not isinstance(files, dict):
        raise RuntimeError("Workflow did not return a 'files' mapping of expected outputs.")

    missing_keys = sorted(EXPECTED_OUTPUT_KEYS - set(files))
    if missing_keys:
        raise RuntimeError(f"Workflow result is missing output entries: {', '.join(missing_keys)}")

    missing_files = [name for name, file_path in files.items() if not Path(file_path).exists()]
    if missing_files:
        raise RuntimeError(
            f"Workflow reported outputs that were not written: {', '.join(sorted(missing_files))}"
        )


def _missing_runtime_packages() -> list[str]:
    return [package for package in REQUIRED_PACKAGES if importlib.util.find_spec(package) is None]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the synthetic aggregate behavioral-stress research demo. "
            "This is not a reliable recession prediction tool."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/synthetic.yaml"),
        help=(
            "Path to the synthetic workflow YAML config, relative to the "
            "repository root by default."
        ),
    )
    args = parser.parse_args()

    config_path = _repo_path(args.config)
    if not config_path.exists():
        parser.error(f"Config file not found: {config_path}")

    missing_packages = _missing_runtime_packages()
    if missing_packages:
        print(
            "ERROR: synthetic demo requires missing Python packages: "
            + ", ".join(missing_packages)
            + ". Install project dependencies with: pip install -e .",
            file=sys.stderr,
        )
        return 1

    from behavioral_stress.workflows.synthetic_workflow import run_synthetic_workflow

    try:
        result = run_synthetic_workflow(config_path)
        _validate_outputs(result)
    except Exception as exc:
        print(f"ERROR: synthetic demo failed: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote synthetic demo outputs to {result['output_dir']}")
    warning = result.get("warning", "Research prototype; not a reliable recession predictor.")
    print(f"Warning: {warning}")
    print("Metrics:")
    for name, value in result["metrics"].items():
        print(f"  {name}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
