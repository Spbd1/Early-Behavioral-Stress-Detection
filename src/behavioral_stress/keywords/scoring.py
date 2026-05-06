"""Keyword scoring heuristics for review prioritization, not alert decisions."""

from __future__ import annotations

from behavioral_stress.keywords.rag import RetrievedContext


def keyword_confidence_score(
    keyword: str,
    contexts: list[RetrievedContext],
    *,
    ontology_match: bool,
    geo_supported: bool,
    locale_match: bool,
) -> float:
    """Score candidate review priority from grounding, ontology, geography, and specificity.

    This score ranks human-review candidates only. It must not be used as a behavioral-stress alert.
    """
    score = 0.15
    if ontology_match:
        score += 0.2
    if geo_supported:
        score += 0.15
    if locale_match:
        score += 0.1
    if contexts:
        score += min(sum(context.score for context in contexts) / 20, 0.25)
    token_count = len(keyword.split())
    if 2 <= token_count <= 5:
        score += 0.1
    elif token_count > 7:
        score -= 0.1
    if any(
        marker in keyword.lower()
        for marker in ["cheap", "coupon", "repair", "debt", "rent", "layoff"]
    ):
        score += 0.05
    return round(max(0.0, min(score, 1.0)), 3)


def needs_drift_review(
    *,
    retrieval_score: float,
    zero_volume_share: float,
    months_since_review: int,
    minimum_retrieval_score: float = 0.5,
) -> bool:
    """Flag weak, low-volume, or stale keywords for human drift review."""
    return (
        retrieval_score < minimum_retrieval_score
        or zero_volume_share >= 0.6
        or months_since_review >= 6
    )
