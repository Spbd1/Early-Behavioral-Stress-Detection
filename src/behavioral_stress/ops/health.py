"""Health check aggregation for CLI, Docker, and API use."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from behavioral_stress.ops.config_validation import validate_runtime_config
from behavioral_stress.ops.environment import validate_environment


@dataclass(frozen=True)
class HealthReport:
    status: str
    checks: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"status": self.status, "checks": self.checks}


def build_health_report(config_path: str | Path = "configs/default.yaml") -> HealthReport:
    config = validate_runtime_config(config_path)
    environment = validate_environment(required_paths=[config_path])
    status = "ok" if config.ok and environment.ok else "degraded"
    return HealthReport(
        status=status,
        checks={"config": config.as_dict(), "environment": environment.as_dict()},
    )
