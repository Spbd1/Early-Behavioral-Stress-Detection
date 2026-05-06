#!/usr/bin/env python
"""Run the synthetic AdaptiveHMM demo and write all expected outputs."""
from __future__ import annotations

import argparse
from pathlib import Path

from behavioral_stress.workflows.synthetic_workflow import run_synthetic_workflow


def main() -> None:
    parser = argparse.ArgumentParser(description="Run synthetic behavioral-stress HMM demo")
    parser.add_argument("--config", type=Path, default=Path("configs/synthetic.yaml"))
    args = parser.parse_args()
    result = run_synthetic_workflow(args.config)
    print(f"Wrote synthetic demo outputs to {result['output_dir']}")
    print(result["metrics"])


if __name__ == "__main__":
    main()
