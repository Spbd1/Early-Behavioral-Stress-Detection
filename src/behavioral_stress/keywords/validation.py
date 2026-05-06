"""Validation pipeline for generated behavioral-stress keywords."""

from __future__ import annotations

from dataclasses import dataclass

from behavioral_stress.keywords.ontology_manager import KeywordOntologyManager
from behavioral_stress.keywords.registry import KeywordCandidate, semantic_group


@dataclass(frozen=True)
class KeywordValidationResult:
    """Validation outcome for one keyword candidate."""

    candidate: KeywordCandidate
    valid: bool
    issues: list[str]
    semantic_group: str


class KeywordValidationPipeline:
    """Check schema completeness, ontology fit, RAG grounding, geo metadata, and expansion risk."""

    def __init__(
        self, ontology_manager: KeywordOntologyManager, *, min_confidence: float = 0.35
    ) -> None:
        self.ontology_manager = ontology_manager
        self.min_confidence = min_confidence

    def validate(self, candidate: KeywordCandidate) -> KeywordValidationResult:
        """Validate a candidate before registry insertion or human approval."""
        issues: list[str] = []
        try:
            self.ontology_manager.validate_category(candidate.ontology_category)
        except ValueError as exc:
            issues.append(str(exc))
        if not candidate.source_context:
            issues.append("candidate lacks RAG source/context grounding")
        if candidate.confidence_score < self.min_confidence:
            issues.append("candidate confidence is below review threshold")
        if not candidate.target_geography.supported:
            issues.append("target geography is marked unsupported by provider metadata")
        if candidate.target_geography.low_volume:
            issues.append("target geography is marked low-volume")
        if not candidate.language_locale:
            issues.append("language/locale is required")
        if candidate.review_status == "approved":
            issues.append("generated candidates must enter human review before approval")
        return KeywordValidationResult(
            candidate=candidate,
            valid=not issues,
            issues=issues,
            semantic_group=candidate.semantic_group or semantic_group(candidate.keyword),
        )

    def validate_many(self, candidates: list[KeywordCandidate]) -> list[KeywordValidationResult]:
        """Validate multiple candidates and detect exact duplicates."""
        results = [self.validate(candidate) for candidate in candidates]
        seen: set[str] = set()
        with_dupes: list[KeywordValidationResult] = []
        for result in results:
            issues = list(result.issues)
            if result.candidate.canonical_key in seen:
                issues.append("duplicate candidate within geography/category/locale")
            seen.add(result.candidate.canonical_key)
            with_dupes.append(
                KeywordValidationResult(
                    candidate=result.candidate,
                    valid=not issues,
                    issues=issues,
                    semantic_group=result.semantic_group,
                )
            )
        return with_dupes
