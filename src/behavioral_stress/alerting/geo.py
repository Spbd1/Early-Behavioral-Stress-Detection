"""Geographic normalization and comparison utilities for behavioral stress signals."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from statistics import mean, pstdev

SUPPORTED_LEVELS = {"global", "country", "region", "state", "province", "city", "metro"}


@dataclass(frozen=True)
class GeoUnit:
    """Geographic identity and reliability metadata."""

    geo_id: str
    name: str
    level: str
    parent_id: str | None = None
    reliability_score: float = 1.0
    sample_size: int | None = None
    supported: bool = True
    warnings: Sequence[str] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return {
            "geo_id": self.geo_id,
            "name": self.name,
            "level": self.level,
            "parent_id": self.parent_id,
            "reliability_score": round(float(self.reliability_score), 4),
            "sample_size": self.sample_size,
            "supported": self.supported,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class GeoTimePoint:
    """One timestamped value for a geography and signal."""

    geo: GeoUnit
    timestamp: str
    values: Mapping[str, float]


class GeoBaselineStore:
    """Per-geography local baselines used to avoid raw cross-region comparisons."""

    def __init__(self) -> None:
        self._stats: dict[str, dict[str, tuple[float, float]]] = {}

    def fit(self, history: Sequence[GeoTimePoint]) -> GeoBaselineStore:
        grouped: dict[str, dict[str, list[float]]] = {}
        for point in history:
            geo_values = grouped.setdefault(point.geo.geo_id, {})
            for signal, value in point.values.items():
                geo_values.setdefault(signal, []).append(float(value))
        self._stats = {
            geo_id: {
                signal: (mean(values), max(pstdev(values), 1e-6))
                for signal, values in signal_values.items()
            }
            for geo_id, signal_values in grouped.items()
        }
        return self

    def normalize(self, geo_id: str, values: Mapping[str, float]) -> dict[str, float]:
        if geo_id not in self._stats:
            raise ValueError(f"No local baseline available for geography {geo_id!r}")
        normalized: dict[str, float] = {}
        for signal, value in values.items():
            if signal not in self._stats[geo_id]:
                raise ValueError(f"No local baseline for signal {signal!r} in geography {geo_id!r}")
            local_mean, local_std = self._stats[geo_id][signal]
            normalized[signal] = round((float(value) - local_mean) / local_std, 4)
        return normalized

    def to_dict(self) -> dict[str, dict[str, dict[str, float]]]:
        return {
            geo_id: {
                signal: {"mean": round(avg, 4), "std": round(std, 4)}
                for signal, (avg, std) in signals.items()
            }
            for geo_id, signals in self._stats.items()
        }


class GeoComparisonBuilder:
    """Build dashboard-ready normalized comparison payloads across geographies."""

    def __init__(self, baseline_store: GeoBaselineStore | None = None) -> None:
        self.baseline_store = baseline_store or GeoBaselineStore()

    def build(
        self,
        current_points: Sequence[GeoTimePoint],
        history: Sequence[GeoTimePoint] | None = None,
    ) -> dict[str, object]:
        if history is not None:
            self.baseline_store.fit(history)
        rows = []
        warnings = [
            "Cross-geography comparisons use local-baseline-normalized values; "
            "raw Google Trends scores must not be compared directly across regions."
        ]
        for point in current_points:
            geo_warnings = self._geo_warnings(point.geo)
            warnings.extend(geo_warnings)
            normalized = self.baseline_store.normalize(point.geo.geo_id, point.values)
            rows.append(
                {
                    "geo": point.geo.to_dict(),
                    "timestamp": point.timestamp,
                    "normalized_values": normalized,
                    "raw_values_present_for_audit_only": {
                        k: round(float(v), 4) for k, v in point.values.items()
                    },
                    "warnings": geo_warnings,
                }
            )
        return {
            "comparison_mode": "local_baseline_normalized_z_score",
            "rows": rows,
            "warnings": list(dict.fromkeys(warnings)),
            "dashboard_series": self._dashboard_series(rows),
            "baselines": self.baseline_store.to_dict(),
        }

    @staticmethod
    def _geo_warnings(geo: GeoUnit) -> list[str]:
        warnings = list(geo.warnings)
        if geo.level not in SUPPORTED_LEVELS:
            warnings.append(f"Geographic level {geo.level!r} is unsupported.")
        if not geo.supported:
            warnings.append(f"Geography {geo.geo_id} is unsupported by the source.")
        if geo.reliability_score < 0.70:
            warnings.append(f"Geography {geo.geo_id} has sparse or unstable geographic data.")
        if geo.sample_size is not None and geo.sample_size < 30:
            warnings.append(f"Geography {geo.geo_id} has low sample size ({geo.sample_size}).")
        return list(dict.fromkeys(warnings))

    @staticmethod
    def _dashboard_series(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
        series = []
        for row in rows:
            geo = row["geo"]
            assert isinstance(geo, dict)
            normalized = row["normalized_values"]
            assert isinstance(normalized, dict)
            for signal, value in normalized.items():
                series.append(
                    {
                        "geo_id": geo["geo_id"],
                        "geo_name": geo["name"],
                        "geo_level": geo["level"],
                        "timestamp": row["timestamp"],
                        "signal": signal,
                        "normalized_value": value,
                    }
                )
        return series
