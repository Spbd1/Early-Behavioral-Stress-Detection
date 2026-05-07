#!/usr/bin/env python
"""Container and CI health check entry point."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from behavioral_stress.ops.health import build_health_report  # noqa: E402


def main() -> int:
    report = build_health_report()
    print(json.dumps(report.as_dict(), indent=2))
    return 0 if report.status in {"ok", "degraded"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
