"""Behavioral Stress Index (BSI) scoring utilities.

The BSI is a conservative, composite research signal. It summarizes whether aggregate behavioral
stress signals increased for a geography; it must not be interpreted as a recession forecast,
crisis prediction, or individual-level diagnostic.
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
    """Inputs needed to compute a geography-specific Behavioral Stress Index."""

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
    """Structured Behavioral Stress Index output for APIs, reports, and dashboards."""

    score: float
    severity_band: str
    uncertainty_band: tuple[float, float]
    top_contributing_signals: list[dict[str, float | str]]
    recent_change: float
    explanation: str
    limitations: list[str]
    components: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "score": self.score,
            "severity_band": self.severity_band,
            "uncertainty_band": list(self.uncertainty_band),
            "top_contributing_signals": self.top_contributing_signals,
            "recent_change": self.recent_change,
            "explanation": self.explanation,
            "limitations": self.limitations,
            "components": self.components,
        }


class BehavioralStressIndex:
    """Compute a conservative composite index from 0 to 100."""

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
        top_signals = cls._top_signals(inputs.signal_contributions)
        limitations = cls._limitations(inputs.limitations, components)
        explanation = cls._explain(score, components, inputs.recent_change, top_signals)
        return BSIResult(
            score=score,
            severity_band=cls.severity_band(score),
            uncertainty_band=(low, high),
            top_contributing_signals=top_signals,
            recent_change=round(float(inputs.recent_change), 2),
            explanation=explanation,
            limitations=limitations,
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
        result.append("This is an aggregate behavioral stress signal, not a recession prediction.")
        return list(dict.fromkeys(result))

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
