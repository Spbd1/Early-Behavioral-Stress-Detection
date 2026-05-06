"""Report generation for geo-aware behavioral stress monitoring outputs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from behavioral_stress.alerting.engine import AlertDecision


@dataclass(frozen=True)
class StressReport:
    """Structured and Markdown report outputs."""

    structured: dict[str, object]
    markdown: str


class ReportGenerator:
    """Generate conservative structured JSON and Markdown reports."""

    def generate(
        self,
        *,
        decisions: Sequence[AlertDecision],
        geo_comparison: Mapping[str, object] | None = None,
    ) -> StressReport:
        decisions_payload = [decision.to_dict() for decision in decisions]
        alerts = [payload for payload in decisions_payload if payload["level"] != "none"]
        watches = [payload for payload in decisions_payload if payload["level"] == "none"]
        structured = {
            "summary": self._summary(alerts, watches),
            "what_changed": self._what_changed(decisions_payload),
            "where_changed": self._where_changed(decisions_payload),
            "contributing_signals": self._signals(decisions_payload),
            "ontology_categories_moved": self._ontology(decisions_payload),
            "broad_or_localized": self._breadth(decisions_payload),
            "uncertainty": self._uncertainty(decisions_payload),
            "possible_confounders": [
                "media or platform attention shifts",
                "seasonality and calendar effects",
                "source coverage changes",
                "local events unrelated to macroeconomic stress",
            ],
            "data_quality_limitations": self._limitations(decisions_payload),
            "alert_or_watch_signal": {"alerts": len(alerts), "watch_signals": len(watches)},
            "geo_comparison": geo_comparison or {},
            "claim_guardrail": (
                "Reports describe that a behavioral stress signal increased; "
                "they do not claim recession prediction."
            ),
        }
        return StressReport(
            structured=structured, markdown=self._markdown(structured, decisions_payload)
        )

    @staticmethod
    def _summary(
        alerts: Sequence[Mapping[str, object]], watches: Sequence[Mapping[str, object]]
    ) -> str:
        if alerts:
            return (
                f"{len(alerts)} geography alert(s) met conservative multi-signal "
                f"criteria; {len(watches)} remained watch signals."
            )
        return (
            "No geography met conservative alert criteria; "
            f"{len(watches)} geography/geographies remain watch signals."
        )

    @staticmethod
    def _what_changed(decisions: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
        return [
            {
                "geo_id": decision["geo"]["geo_id"],
                "geo_name": decision["geo"]["name"],
                "recent_change": decision["bsi"]["recent_change"],
                "bsi_score": decision["bsi"]["score"],
                "level": decision["level"],
            }
            for decision in decisions
        ]

    @staticmethod
    def _where_changed(decisions: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
        return [decision["geo"] for decision in decisions]

    @staticmethod
    def _signals(decisions: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
        rows = []
        for decision in decisions:
            for signal in decision["bsi"]["top_contributing_signals"]:
                rows.append({"geo_id": decision["geo"]["geo_id"], **signal})
        return rows

    @staticmethod
    def _ontology(decisions: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
        rows = []
        for decision in decisions:
            for mover in decision["ontology_movers"]:
                rows.append({"geo_id": decision["geo"]["geo_id"], **mover})
        return rows

    @staticmethod
    def _breadth(decisions: Sequence[Mapping[str, object]]) -> str:
        if not decisions:
            return "No geographies evaluated."
        levels = {decision["geo"]["level"] for decision in decisions}
        alert_geos = {
            decision["geo"]["geo_id"] for decision in decisions if decision["level"] != "none"
        }
        if len(alert_geos) > 1 or "global" in levels or "country" in levels:
            return (
                "Potentially broad; compare local-baseline-normalized geographies "
                "before interpretation."
            )
        return "Localized or watch-only based on evaluated geographies."

    @staticmethod
    def _uncertainty(decisions: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
        return [
            {
                "geo_id": decision["geo"]["geo_id"],
                "uncertainty_band": decision["bsi"]["uncertainty_band"],
                "confidence": decision["confidence"],
                "warnings": decision["warnings"],
            }
            for decision in decisions
        ]

    @staticmethod
    def _limitations(decisions: Sequence[Mapping[str, object]]) -> list[str]:
        limitations: list[str] = []
        for decision in decisions:
            limitations.extend(decision["bsi"]["limitations"])
            limitations.extend(decision["warnings"])
            limitations.extend(decision["suppressions"])
        return list(dict.fromkeys(str(item) for item in limitations if str(item)))

    @staticmethod
    def _markdown(
        structured: Mapping[str, object], decisions: Sequence[Mapping[str, object]]
    ) -> str:
        lines = [
            "# Behavioral Stress Monitoring Report",
            "",
            "**Guardrail:** This report says behavioral stress signal increased or "
            "is under watch; it is not a recession prediction.",
            "",
            f"## Summary\n{structured['summary']}",
            "",
            "## What changed and where",
        ]
        for decision in decisions:
            geo = decision["geo"]
            bsi = decision["bsi"]
            lines.append(
                f"- {geo['name']} ({geo['level']}): level={decision['level']}, "
                f"BSI={bsi['score']}, recent_change={bsi['recent_change']}."
            )
        lines.extend(
            [
                "",
                "## Signals and ontology categories",
                "- Top contributing signals and ontology movers are provided in the "
                "structured JSON fields.",
                "",
                "## Uncertainty and limitations",
            ]
        )
        for item in structured["data_quality_limitations"]:
            lines.append(f"- {item}")
        lines.extend(
            [
                "",
                "## Possible confounders",
            ]
        )
        for item in structured["possible_confounders"]:
            lines.append(f"- {item}")
        return "\n".join(lines) + "\n"
