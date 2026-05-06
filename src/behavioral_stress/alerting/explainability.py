"""Explainability helpers for conservative behavioral stress outputs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

PROHIBITED_CLAIMS = ("crisis is coming", "recession prediction", "predicts recession")


def describe_signal_agreement(
    family_scores: Mapping[str, float], threshold: float = 0.60
) -> dict[str, object]:
    """Summarize keyword-family agreement without allowing one signal to dominate."""
    active = [name for name, score in family_scores.items() if float(score) >= threshold]
    return {
        "active_family_count": len(active),
        "active_families": active,
        "total_family_count": len(family_scores),
        "agreement_ratio": round(len(active) / max(1, len(family_scores)), 4),
        "threshold": threshold,
    }


def explain_alert_decision(
    *,
    level: str,
    bsi_score: float,
    criteria: Mapping[str, object],
    suppressions: Sequence[str],
    warnings: Sequence[str],
) -> str:
    """Build a plain-language explanation for an alert or watch decision."""
    if level == "none":
        base = "No alert was issued because conservative multi-signal criteria were not all met."
    else:
        base = (
            f"A {level} alert was issued because multiple behavioral stress "
            "indicators moved together."
        )
    criteria_text = "; ".join(f"{key}={value}" for key, value in criteria.items())
    suppress_text = f" Suppressions: {'; '.join(suppressions)}." if suppressions else ""
    warning_text = f" Warnings: {'; '.join(warnings)}." if warnings else ""
    return (
        f"{base} BSI={bsi_score:.2f}. Criteria: {criteria_text}.{suppress_text}{warning_text} "
        "This describes an aggregate behavioral stress signal increased or watched; "
        "it is not a recession prediction."
    )


def ontology_movers(
    category_scores: Mapping[str, float], limit: int = 5
) -> list[dict[str, float | str]]:
    """Return ontology categories with the largest absolute movement."""
    return [
        {"category": name, "movement": round(float(score), 4)}
        for name, score in sorted(
            category_scores.items(), key=lambda item: abs(float(item[1])), reverse=True
        )[:limit]
    ]
