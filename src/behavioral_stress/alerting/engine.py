"""Conservative geo-aware alert engine for aggregate behavioral stress monitoring."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from behavioral_stress.alerting.bsi import BehavioralStressIndex, BSIInput, BSIResult
from behavioral_stress.alerting.explainability import (
    describe_signal_agreement,
    explain_alert_decision,
)
from behavioral_stress.alerting.geo import GeoUnit

ALERT_ORDER = {"none": 0, "yellow": 1, "orange": 2, "red": 3}


@dataclass(frozen=True)
class AlertObservation:
    """One decision-time aggregate observation for a geography."""

    timestamp: str
    geo: GeoUnit
    hmm_stress_posterior: float
    anomaly_strength: float
    keyword_family_scores: Mapping[str, float]
    persistence_score: float
    trend_acceleration: float
    drift_confidence: float
    data_quality_score: float
    ontology_category_scores: Mapping[str, float] = field(default_factory=dict)
    recent_change: float = 0.0
    limitations: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class AlertDecision:
    """Structured alert output suitable for JSON APIs, history, and dashboards."""

    alert_id: str
    timestamp: str
    geo: dict[str, object]
    level: str
    confidence: float
    bsi: BSIResult
    criteria: dict[str, object]
    explanation: str
    suppressions: list[str]
    warnings: list[str]
    cooldown_active: bool
    history: list[dict[str, object]]
    ontology_movers: list[dict[str, float | str]]

    def to_dict(self) -> dict[str, object]:
        return {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp,
            "geo": self.geo,
            "level": self.level,
            "confidence": self.confidence,
            "bsi": self.bsi.to_dict(),
            "criteria": self.criteria,
            "explanation": self.explanation,
            "suppressions": self.suppressions,
            "warnings": self.warnings,
            "cooldown_active": self.cooldown_active,
            "history": self.history,
            "ontology_movers": self.ontology_movers,
        }


@dataclass(frozen=True)
class AlertPolicy:
    """Thresholds and suppression rules for conservative alerting."""

    min_active_keyword_families: int = 2
    keyword_family_threshold: float = 0.60
    min_data_quality: float = 0.70
    min_geo_reliability: float = 0.70
    min_drift_confidence: float = 0.55
    min_persistence: float = 0.60
    min_anomaly_strength: float = 0.55
    cooldown_periods: int = 2
    false_positive_quality_floor: float = 0.55
    require_anomaly_confirmation: bool = True


class AlertHistory:
    """In-memory alert history store keyed by geography."""

    def __init__(self) -> None:
        self._events: dict[str, list[dict[str, object]]] = {}

    def add(self, decision: AlertDecision) -> None:
        self._events.setdefault(str(decision.geo["geo_id"]), []).append(decision.to_dict())

    def recent(self, geo_id: str, limit: int = 10) -> list[dict[str, object]]:
        return self._events.get(geo_id, [])[-limit:]

    def last_alert(self, geo_id: str) -> dict[str, object] | None:
        for event in reversed(self._events.get(geo_id, [])):
            if ALERT_ORDER.get(str(event["level"]), 0) > 0:
                return event
        return None


class GeoAwareAlertEngine:
    """Evaluate conservative alerts from HMM, anomaly, persistence, quality, and geo signals."""

    def __init__(
        self, policy: AlertPolicy | None = None, history: AlertHistory | None = None
    ) -> None:
        self.policy = policy or AlertPolicy()
        self.history = history or AlertHistory()

    def evaluate(self, observation: AlertObservation) -> AlertDecision:
        agreement = describe_signal_agreement(
            observation.keyword_family_scores, self.policy.keyword_family_threshold
        )
        bsi = BehavioralStressIndex.compute(
            BSIInput(
                hmm_stress_posterior=observation.hmm_stress_posterior,
                anomaly_strength=observation.anomaly_strength,
                signal_breadth=float(agreement["agreement_ratio"]),
                persistence=observation.persistence_score,
                trend_acceleration=observation.trend_acceleration,
                data_quality=observation.data_quality_score,
                drift_confidence=observation.drift_confidence,
                geographic_confidence=observation.geo.reliability_score,
                signal_contributions=observation.keyword_family_scores,
                recent_change=observation.recent_change,
                limitations=observation.limitations,
            )
        )
        criteria = self._criteria(observation, agreement, bsi)
        warnings = self._warnings(observation)
        suppressions = self._suppressions(observation, agreement, criteria, warnings)
        level = self._level(bsi.score, observation.hmm_stress_posterior)
        if suppressions:
            level = "none"
        cooldown_active = self._cooldown_active(observation.geo.geo_id)
        if (
            cooldown_active
            and ALERT_ORDER[level] <= ALERT_ORDER[self._last_level(observation.geo.geo_id)]
        ):
            suppressions.append("cooldown_active_for_same_or_lower_alert_level")
            level = "none"
        confidence = self._confidence(observation, agreement, suppressions)
        history_before = self.history.recent(observation.geo.geo_id)
        decision = AlertDecision(
            alert_id=f"{observation.geo.geo_id}:{observation.timestamp}:{level}",
            timestamp=observation.timestamp,
            geo=observation.geo.to_dict(),
            level=level,
            confidence=confidence,
            bsi=bsi,
            criteria=criteria,
            explanation=explain_alert_decision(
                level=level,
                bsi_score=bsi.score,
                criteria=criteria,
                suppressions=suppressions,
                warnings=warnings,
            ),
            suppressions=list(dict.fromkeys(suppressions)),
            warnings=warnings,
            cooldown_active=cooldown_active,
            history=history_before,
            ontology_movers=self._ontology_movers(observation.ontology_category_scores),
        )
        self.history.add(decision)
        return decision

    def dashboard_payload(self, decisions: Sequence[AlertDecision]) -> dict[str, object]:
        """Return dashboard-ready alert rows and summary counts."""
        rows = [decision.to_dict() for decision in decisions]
        counts = {level: sum(1 for row in rows if row["level"] == level) for level in ALERT_ORDER}
        return {"alerts": rows, "counts_by_level": counts, "policy": self.policy.__dict__}

    def _criteria(
        self,
        observation: AlertObservation,
        agreement: Mapping[str, object],
        bsi: BSIResult,
    ) -> dict[str, object]:
        return {
            "hmm_posterior": round(float(observation.hmm_stress_posterior), 4),
            "active_keyword_families": agreement["active_family_count"],
            "keyword_agreement_ratio": agreement["agreement_ratio"],
            "persistence_score": round(float(observation.persistence_score), 4),
            "anomaly_strength": round(float(observation.anomaly_strength), 4),
            "drift_confidence": round(float(observation.drift_confidence), 4),
            "data_quality_score": round(float(observation.data_quality_score), 4),
            "geographic_reliability_score": round(float(observation.geo.reliability_score), 4),
            "bsi_score": bsi.score,
            "bsi_severity_band": bsi.severity_band,
        }

    def _warnings(self, observation: AlertObservation) -> list[str]:
        warnings = list(observation.geo.warnings)
        if not observation.geo.supported:
            warnings.append("Geography is unsupported by the source.")
        if observation.geo.reliability_score < self.policy.min_geo_reliability:
            warnings.append("Geographic data is sparse, unstable, or below reliability threshold.")
        if observation.geo.sample_size is not None and observation.geo.sample_size < 30:
            warnings.append("Geographic sample size is low.")
        if observation.data_quality_score < self.policy.min_data_quality:
            warnings.append("Data quality is below alerting threshold.")
        return list(dict.fromkeys(warnings))

    def _suppressions(
        self,
        observation: AlertObservation,
        agreement: Mapping[str, object],
        criteria: Mapping[str, object],
        warnings: Sequence[str],
    ) -> list[str]:
        suppressions = []
        if int(agreement["active_family_count"]) < self.policy.min_active_keyword_families:
            suppressions.append("single_signal_or_insufficient_keyword_family_agreement")
        if (
            self.policy.require_anomaly_confirmation
            and observation.anomaly_strength < self.policy.min_anomaly_strength
        ):
            suppressions.append("anomaly_confirmation_below_threshold")
        if observation.persistence_score < self.policy.min_persistence:
            suppressions.append("persistence_below_threshold")
        if observation.drift_confidence < self.policy.min_drift_confidence:
            suppressions.append("drift_confidence_below_threshold")
        if observation.data_quality_score < self.policy.min_data_quality:
            suppressions.append("data_quality_below_threshold")
        if observation.geo.reliability_score < self.policy.min_geo_reliability:
            suppressions.append("geographic_reliability_below_threshold")
        if not observation.geo.supported:
            suppressions.append("unsupported_geography")
        if observation.data_quality_score < self.policy.false_positive_quality_floor:
            suppressions.append("false_positive_suppression_low_quality_floor")
        if warnings and criteria["bsi_score"] < 75.0:
            suppressions.append("false_positive_suppression_due_to_geo_or_quality_warning")
        return suppressions

    @staticmethod
    def _level(bsi_score: float, hmm_posterior: float) -> str:
        if bsi_score >= 75.0 and hmm_posterior >= 0.75:
            return "red"
        if bsi_score >= 60.0 and hmm_posterior >= 0.65:
            return "orange"
        if bsi_score >= 45.0 and hmm_posterior >= 0.55:
            return "yellow"
        return "none"

    def _cooldown_active(self, geo_id: str) -> bool:
        last = self.history.last_alert(geo_id)
        if last is None:
            return False
        recent = self.history.recent(geo_id, self.policy.cooldown_periods)
        return any(event["alert_id"] == last["alert_id"] for event in recent)

    def _last_level(self, geo_id: str) -> str:
        last = self.history.last_alert(geo_id)
        return str(last["level"]) if last else "none"

    def _confidence(
        self,
        observation: AlertObservation,
        agreement: Mapping[str, object],
        suppressions: Sequence[str],
    ) -> float:
        base = min(
            float(observation.hmm_stress_posterior),
            float(observation.anomaly_strength),
            float(observation.persistence_score),
            float(observation.drift_confidence),
            float(observation.data_quality_score),
            float(observation.geo.reliability_score),
        )
        breadth = float(agreement["agreement_ratio"])
        penalty = 0.08 * len(suppressions)
        return round(max(0.0, min(1.0, 0.70 * base + 0.30 * breadth - penalty)), 4)

    @staticmethod
    def _ontology_movers(category_scores: Mapping[str, float]) -> list[dict[str, float | str]]:
        return [
            {"category": name, "movement": round(float(value), 4)}
            for name, value in sorted(
                category_scores.items(), key=lambda item: abs(float(item[1])), reverse=True
            )[:5]
        ]
