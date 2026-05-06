#!/usr/bin/env python
"""Print dashboard launch instructions for the research prototype."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Show dashboard launch command")
    parser.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    args = parser.parse_args()
    print("Experimental research prototype. Not a validated recession predictor. Aggregate-level inference only.")
    print(f"Using config: {args.config}")
    print("Run: streamlit run src/behavioral_stress/visualization/dashboard.py")


if __name__ == "__main__":
    main()
