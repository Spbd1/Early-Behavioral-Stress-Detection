"""Strict-enough configuration validation for experimental production usage."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from behavioral_stress.utils.config import load_config

_ALLOWED_FREQ = {"D", "W", "M", "MS", "QS", "YS"}


@dataclass(frozen=True)
class ConfigIssue:
    path: str
    severity: str
    message: str


@dataclass(frozen=True)
class ConfigValidationReport:
    ok: bool
    issues: list[ConfigIssue] = field(default_factory=list)
    normalized: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "issues": [issue.__dict__ for issue in self.issues],
            "normalized": self.normalized,
        }


def validate_runtime_config(config: str | Path | dict[str, Any]) -> ConfigValidationReport:
    """Validate workflow configuration and return actionable issues."""
    cfg = load_config(config) if isinstance(config, (str, Path)) else dict(config)
    issues: list[ConfigIssue] = []

    seed = cfg.get("random_seed", cfg.get("synthetic", {}).get("random_seed"))
    if seed is None:
        issues.append(ConfigIssue("random_seed", "error", "deterministic random_seed is required"))
    elif int(seed) < 0:
        issues.append(ConfigIssue("random_seed", "error", "random_seed must be non-negative"))

    synth = cfg.get("synthetic", {})
    _positive_int(synth, "n_steps", issues, minimum=12)
    _positive_int(synth, "n_states", issues, minimum=2)
    _positive_int(synth, "n_features", issues, minimum=1)
    _positive_int(synth, "n_covariates", issues, minimum=0, allow_zero=True)
    freq = str(synth.get("freq", "W"))
    if freq not in _ALLOWED_FREQ:
        issues.append(
            ConfigIssue(
                "synthetic.freq",
                "error",
                f"freq must be one of {sorted(_ALLOWED_FREQ)}",
            )
        )

    model = cfg.get("model", {})
    _positive_int(model, "n_states", issues, minimum=2, path_prefix="model")
    forgetting_rate = float(model.get("forgetting_rate", 0.05))
    if not 0.0 <= forgetting_rate <= 1.0:
        issues.append(
            ConfigIssue(
                "model.forgetting_rate",
                "error",
                "forgetting_rate must be between 0 and 1",
            )
        )
    if str(model.get("covariance_type", "diagonal")) != "diagonal":
        issues.append(
            ConfigIssue(
                "model.covariance_type",
                "warning",
                "only diagonal covariance is tested",
            )
        )

    outputs = cfg.get("outputs", {})
    if not outputs.get("directory"):
        issues.append(ConfigIssue("outputs.directory", "error", "outputs.directory is required"))

    normalized = dict(cfg)
    normalized.setdefault("deployment", {})
    normalized["deployment"].setdefault("experimental", True)
    normalized["deployment"].setdefault("deterministic", True)
    ok = all(issue.severity != "error" for issue in issues)
    return ConfigValidationReport(ok=ok, issues=issues, normalized=normalized)


def _positive_int(
    section: dict[str, Any],
    key: str,
    issues: list[ConfigIssue],
    minimum: int,
    path_prefix: str = "synthetic",
    allow_zero: bool = False,
) -> None:
    path = f"{path_prefix}.{key}"
    if key not in section:
        issues.append(ConfigIssue(path, "error", "required integer is missing"))
        return
    value = int(section[key])
    if value < minimum and not (allow_zero and value == 0):
        issues.append(ConfigIssue(path, "error", f"must be >= {minimum}"))
