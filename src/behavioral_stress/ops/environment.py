"""Environment and secret validation for experimental production runs."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
_SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")


@dataclass(frozen=True)
class EnvironmentCheck:
    """Result of an environment validation check."""

    name: str
    ok: bool
    severity: str
    message: str


@dataclass(frozen=True)
class EnvironmentReport:
    """Aggregated environment validation report."""

    ok: bool
    checks: list[EnvironmentCheck] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "checks": [check.__dict__ for check in self.checks],
        }


def validate_environment(
    required_vars: list[str] | None = None,
    optional_secret_vars: list[str] | None = None,
    required_paths: list[str | Path] | None = None,
) -> EnvironmentReport:
    """Validate process environment without exposing secret values.

    The validator intentionally reports only variable names and redacted state. It fails closed for
    required environment variables and paths, and warns when secret-looking variables have invalid
    names or are present as empty strings.
    """

    checks: list[EnvironmentCheck] = []
    for name in required_vars or []:
        checks.append(_check_env_var(name, required=True))
    for name in optional_secret_vars or []:
        checks.append(_check_env_var(name, required=False, secret=True))
    for raw_path in required_paths or []:
        path = Path(raw_path)
        checks.append(
            EnvironmentCheck(
                name=f"path:{path}",
                ok=path.exists(),
                severity="error",
                message="required path exists" if path.exists() else "required path is missing",
            )
        )

    for name, value in os.environ.items():
        if any(marker in name for marker in _SECRET_MARKERS) and value == "":
            checks.append(
                EnvironmentCheck(
                    name=name,
                    ok=False,
                    severity="warning",
                    message="secret-like environment variable is set but empty",
                )
            )

    ok = all(check.ok or check.severity != "error" for check in checks)
    return EnvironmentReport(ok=ok, checks=checks)


def _check_env_var(name: str, required: bool, secret: bool = False) -> EnvironmentCheck:
    if not _ENV_NAME.match(name):
        return EnvironmentCheck(
            name=name,
            ok=False,
            severity="error",
            message="invalid env var name",
        )
    value = os.environ.get(name)
    if value is None:
        return EnvironmentCheck(
            name=name,
            ok=not required,
            severity="error" if required else "warning",
            message="required variable is missing" if required else "optional variable is not set",
        )
    if value == "":
        return EnvironmentCheck(
            name=name,
            ok=False,
            severity="error" if required else "warning",
            message="variable is empty",
        )
    label = "secret variable is set (redacted)" if secret else "variable is set"
    return EnvironmentCheck(name=name, ok=True, severity="info", message=label)
