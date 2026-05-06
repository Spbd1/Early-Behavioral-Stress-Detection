"""Ontology-guided keyword generation grounded by a local RAG layer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from behavioral_stress.keywords.ontology_manager import KeywordOntologyManager
from behavioral_stress.keywords.rag import LightweightRAGRetriever, RetrievedContext
from behavioral_stress.keywords.registry import GeoMetadata, KeywordCandidate
from behavioral_stress.keywords.scoring import keyword_confidence_score


@dataclass(frozen=True)
class SeedTerm:
    """Auditable seed term used to create controlled keyword variants."""

    term: str
    ontology_category: str
    reason: str


class KeywordGenerationPipeline:
    """Generate reviewable keyword candidates without autonomous promotion or alerting."""

    def __init__(
        self,
        ontology_manager: KeywordOntologyManager,
        retriever: LightweightRAGRetriever,
        *,
        max_variants_per_seed: int = 3,
    ) -> None:
        self.ontology_manager = ontology_manager
        self.retriever = retriever
        self.max_variants_per_seed = max_variants_per_seed

    def generate(
        self,
        seeds: Iterable[SeedTerm],
        geographies: Iterable[GeoMetadata],
        *,
        locale: str = "en",
    ) -> list[KeywordCandidate]:
        """Generate grounded candidates for each seed/geography pair."""
        candidates: list[KeywordCandidate] = []
        for geography in geographies:
            if not geography.supported or geography.low_volume:
                continue
            for seed in seeds:
                category = self.ontology_manager.get(seed.ontology_category)
                variants = self._variants(seed.term, geography)
                for variant in variants[: self.max_variants_per_seed]:
                    query = f"{variant} {category.label} {geography.name} {seed.reason}"
                    contexts = self.retriever.retrieve(
                        query, geography=geography.geo_id, locale=locale, top_k=3
                    )
                    if not contexts:
                        continue
                    score = keyword_confidence_score(
                        variant,
                        contexts,
                        ontology_match=True,
                        geo_supported=geography.supported and not geography.low_volume,
                        locale_match=geography.locale == locale,
                    )
                    candidates.append(
                        KeywordCandidate(
                            keyword=variant,
                            source_context=[context.to_dict() for context in contexts],
                            ontology_category=category.key,
                            expected_direction_under_stress=category.default_expected_direction_under_stress,
                            target_geography=geography,
                            language_locale=locale,
                            confidence_score=score,
                            reason_for_inclusion=(
                                f"Seed '{seed.term}' maps to {category.label}; generated for "
                                f"{geography.name} because {seed.reason}. RAG supplied "
                                f"{_context_summary(contexts)}."
                            ),
                            review_status="pending_review",
                        )
                    )
        return _deduplicate(candidates)

    def _variants(self, term: str, geography: GeoMetadata) -> list[str]:
        base = term.strip().lower()
        variants = [base]
        if geography.level in {"city", "metro"}:
            variants.append(f"{base} {geography.name.lower()}")
        if geography.region_code:
            variants.append(f"{base} {geography.region_code.lower()}")
        return variants


def _context_summary(contexts: list[RetrievedContext]) -> str:
    return "; ".join(f"{context.source_type}:{context.doc_id}" for context in contexts)


def _deduplicate(candidates: list[KeywordCandidate]) -> list[KeywordCandidate]:
    seen: set[str] = set()
    unique: list[KeywordCandidate] = []
    for candidate in candidates:
        if candidate.canonical_key in seen:
            continue
        seen.add(candidate.canonical_key)
        unique.append(candidate)
    return unique
