#!/usr/bin/env python
"""Build static dashboard JSON for browser-only deployments."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from behavioral_stress.api.dashboard_data import write_dashboard_payload  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write frontend/dashboard.json from workflow artifacts."
    )
    parser.add_argument("--data-dir", type=Path, default=Path("data/synthetic"))
    parser.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    parser.add_argument("--output", type=Path, default=Path("frontend/dashboard.json"))
    args = parser.parse_args()
    write_dashboard_payload(args.output, args.data_dir, args.config)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
