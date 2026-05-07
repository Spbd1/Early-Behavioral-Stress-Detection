"""Monitoring hooks for health, drift, and rollback guardrails."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from statistics import mean


@dataclass(frozen=True)
class DriftSignal:
    name: str
    baseline_mean: float
    current_mean: float
    absolute_delta: float
    severity: str


@dataclass(frozen=True)
class MonitoringReport:
    ok: bool
    drift: list[DriftSignal] = field(default_factory=list)
    rollback_recommended: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "rollback_recommended": self.rollback_recommended,
            "drift": [signal.__dict__ for signal in self.drift],
        }


def compare_means_for_drift(
    baseline: dict[str, Iterable[float]],
    current: dict[str, Iterable[float]],
    warning_delta: float = 0.25,
) -> MonitoringReport:
    """Compare feature means as a simple deterministic drift sentinel."""
    signals: list[DriftSignal] = []
    for name, baseline_values in baseline.items():
        if name not in current:
            continue
        b_values = list(baseline_values)
        c_values = list(current[name])
        if not b_values or not c_values:
            continue
        b_mean = float(mean(b_values))
        c_mean = float(mean(c_values))
        delta = abs(c_mean - b_mean)
        severity = "warning" if delta >= warning_delta else "info"
        signals.append(DriftSignal(name, b_mean, c_mean, delta, severity))
    rollback = any(signal.severity == "warning" for signal in signals)
    return MonitoringReport(ok=not rollback, drift=signals, rollback_recommended=rollback)
