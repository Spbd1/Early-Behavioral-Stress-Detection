"""MVP Behavioral Stress Index (BSI) scoring utilities.

The BSI implemented here is a conservative, composite research signal. It summarizes whether
aggregate behavioral stress signals increased for a geography; it must not be interpreted as a
recession forecast, crisis prediction, or individual-level diagnostic.

Implementation status versus ``BSI_DESIGN.md``:

Implemented in this MVP:
- bounded 0-100 score from HMM posterior, anomaly, breadth, persistence, acceleration, data
  quality, drift confidence, and geographic confidence components;
- conservative severity bands, uncertainty band, reliability score, top contributors, limitations,
  and safety warnings in the serialized output.

Deferred from the fuller design:
- local rolling-baseline computation from raw signal panels;
- seasonal/holiday/event adjustment;
- calibrated uncertainty intervals and threshold calibration;
- volume-aware geographic confidence estimation;
- transform, weight, calibration, and lineage version metadata.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, float(value)))


def _scale_0_100(value: float) -> float:
    return round(100.0 * _clamp(value), 2)


@dataclass(frozen=True)
class BSIInput:
    """Inputs needed to compute the MVP geography-specific Behavioral Stress Index.

    Callers are responsible for supplying already-normalized component scores in ``[0, 1]``.
    This MVP does not compute local baselines, seasonal adjustments, or calibrated uncertainty from
    raw Google Trends or other provider observations.
    """

    hmm_stress_posterior: float
    anomaly_strength: float
    signal_breadth: float
    persistence: float
    trend_acceleration: float
    data_quality: float
    drift_confidence: float
    geographic_confidence: float
    signal_contributions: Mapping[str, float] = field(default_factory=dict)
    recent_change: float = 0.0
    limitations: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class BSIResult:
    """Structured MVP Behavioral Stress Index output for APIs, reports, and dashboards."""

    score: float
    severity_band: str
    uncertainty_band: tuple[float, float]
    reliability_score: float
    top_contributing_signals: list[dict[str, float | str]]
    recent_change: float
    explanation: str
    limitations: list[str]
    warnings: list[str]
    implementation_label: str
    components: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "score": self.score,
            "severity_band": self.severity_band,
            "uncertainty_band": list(self.uncertainty_band),
            "reliability_score": self.reliability_score,
            "top_contributing_signals": self.top_contributing_signals,
            "recent_change": self.recent_change,
            "explanation": self.explanation,
            "limitations": self.limitations,
            "warnings": self.warnings,
            "implementation_label": self.implementation_label,
            "components": self.components,
        }


class BehavioralStressIndex:
    """Compute the MVP conservative composite index from 0 to 100.

    The weights and penalties below are fixed MVP heuristics for deterministic research demos.
    They are not calibrated production thresholds and do not implement the complete BSI design.
    """

    IMPLEMENTATION_LABEL = "MVP BSI"
    EXPERIMENTAL_WARNING = (
        "Experimental MVP BSI: use only for aggregate research/demo interpretation; not validated "
        "for operational decisions."
    )
    NOT_RECESSION_PREDICTION_WARNING = (
        "This is an aggregate behavioral stress signal, not a recession prediction."
    )

    WEIGHTS = {
        "hmm_stress_posterior": 0.24,
        "anomaly_strength": 0.18,
        "signal_breadth": 0.14,
        "persistence": 0.14,
        "trend_acceleration": 0.10,
        "data_quality": 0.08,
        "drift_confidence": 0.06,
        "geographic_confidence": 0.06,
    }

    @classmethod
    def compute(cls, inputs: BSIInput) -> BSIResult:
        """Compute BSI score, uncertainty, explanation, and limitations."""
        components = {
            "hmm_stress_posterior": _clamp(inputs.hmm_stress_posterior),
            "anomaly_strength": _clamp(inputs.anomaly_strength),
            "signal_breadth": _clamp(inputs.signal_breadth),
            "persistence": _clamp(inputs.persistence),
            "trend_acceleration": _clamp(inputs.trend_acceleration),
            "data_quality": _clamp(inputs.data_quality),
            "drift_confidence": _clamp(inputs.drift_confidence),
            "geographic_confidence": _clamp(inputs.geographic_confidence),
        }
        weighted = sum(components[name] * weight for name, weight in cls.WEIGHTS.items())
        drift_penalty = (1.0 - components["drift_confidence"]) * 0.10
        quality_floor = min(components["data_quality"], components["geographic_confidence"])
        quality_penalty = (1.0 - quality_floor) * 0.12
        score = _scale_0_100(weighted - drift_penalty - quality_penalty)
        uncertainty = cls._uncertainty_width(components)
        low = round(max(0.0, score - uncertainty), 2)
        high = round(min(100.0, score + uncertainty), 2)
        reliability_score = cls._reliability_score(components)
        top_signals = cls._top_signals(inputs.signal_contributions)
        limitations = cls._limitations(inputs.limitations, components)
        warnings = cls._warnings()
        explanation = cls._explain(score, components, inputs.recent_change, top_signals)
        return BSIResult(
            score=score,
            severity_band=cls.severity_band(score),
            uncertainty_band=(low, high),
            reliability_score=reliability_score,
            top_contributing_signals=top_signals,
            recent_change=round(float(inputs.recent_change), 2),
            explanation=explanation,
            limitations=limitations,
            warnings=warnings,
            implementation_label=cls.IMPLEMENTATION_LABEL,
            components={name: round(value, 4) for name, value in components.items()},
        )

    @staticmethod
    def severity_band(score: float) -> str:
        """Map a BSI score to a conservative severity band."""
        if score >= 75.0:
            return "red"
        if score >= 60.0:
            return "orange"
        if score >= 45.0:
            return "yellow"
        return "watch"

    @staticmethod
    def _uncertainty_width(components: Mapping[str, float]) -> float:
        quality_floor = min(components["data_quality"], components["geographic_confidence"])
        drift_uncertainty = 1.0 - components["drift_confidence"]
        return round(5.0 + 18.0 * (1.0 - quality_floor) + 10.0 * drift_uncertainty, 2)

    @staticmethod
    def _reliability_score(components: Mapping[str, float]) -> float:
        """Return an MVP reliability proxy from quality, drift, and geography components."""
        reliability = min(
            components["data_quality"],
            components["drift_confidence"],
            components["geographic_confidence"],
        )
        return round(reliability, 4)

    @staticmethod
    def _top_signals(contributions: Mapping[str, float]) -> list[dict[str, float | str]]:
        ordered = sorted(contributions.items(), key=lambda item: abs(float(item[1])), reverse=True)
        return [
            {"signal": name, "contribution": round(float(value), 4)}
            for name, value in ordered[:5]
            if abs(float(value)) > 0.0
        ]

    @staticmethod
    def _limitations(limitations: Sequence[str], components: Mapping[str, float]) -> list[str]:
        result = list(dict.fromkeys(str(item) for item in limitations if str(item)))
        if components["data_quality"] < 0.70:
            result.append("Data quality is below the preferred alerting threshold.")
        if components["geographic_confidence"] < 0.70:
            result.append("Geographic confidence is limited; local data may be sparse or unstable.")
        if components["drift_confidence"] < 0.60:
            result.append("Model drift confidence is low, increasing uncertainty.")
        result.append(BehavioralStressIndex.EXPERIMENTAL_WARNING)
        result.append(BehavioralStressIndex.NOT_RECESSION_PREDICTION_WARNING)
        return list(dict.fromkeys(result))

    @staticmethod
    def _warnings() -> list[str]:
        return [
            BehavioralStressIndex.EXPERIMENTAL_WARNING,
            BehavioralStressIndex.NOT_RECESSION_PREDICTION_WARNING,
        ]

    @staticmethod
    def _explain(
        score: float,
        components: Mapping[str, float],
        recent_change: float,
        top_signals: Sequence[Mapping[str, object]],
    ) -> str:
        if recent_change > 0:
            direction = "increased"
        elif recent_change < 0:
            direction = "decreased"
        else:
            direction = "was stable"
        signals = (
            ", ".join(str(item["signal"]) for item in top_signals[:3])
            or "no single dominant signal"
        )
        return (
            f"Behavioral stress signal {direction}; BSI is {score:.2f}. "
            f"The score combines HMM posterior ({components['hmm_stress_posterior']:.2f}), "
            f"anomaly strength ({components['anomaly_strength']:.2f}), signal breadth "
            f"({components['signal_breadth']:.2f}), persistence ({components['persistence']:.2f}), "
            f"trend acceleration ({components['trend_acceleration']:.2f}), data quality "
            f"({components['data_quality']:.2f}), drift confidence "
            f"({components['drift_confidence']:.2f}), "
            f"and geographic confidence ({components['geographic_confidence']:.2f}). "
            f"Largest contributing signals: {signals}."
        )
