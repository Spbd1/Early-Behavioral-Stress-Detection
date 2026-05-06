from behavioral_stress.keywords.ontology_manager import KeywordOntologyManager
from behavioral_stress.keywords.pipeline import KeywordGenerationPipeline, SeedTerm
from behavioral_stress.keywords.rag import (
    KnowledgeDocument,
    LightweightRAGRetriever,
    LocalKnowledgeBase,
)
from behavioral_stress.keywords.registry import (
    GeoAwareKeywordRegistry,
    GeoMetadata,
    KeywordCandidate,
)
from behavioral_stress.keywords.scoring import needs_drift_review
from behavioral_stress.keywords.validation import KeywordValidationPipeline


def _retriever():
    kb = LocalKnowledgeBase(
        [
            KnowledgeDocument(
                doc_id="doc1",
                title="Codebook",
                source_type="keyword codebooks",
                text=(
                    "Discount-seeking and repair keywords include cheap groceries, "
                    "coupons, appliance repair, and fix car under stress."
                ),
            ),
            KnowledgeDocument(
                doc_id="doc2",
                title="California notes",
                source_type="manually curated economic notes",
                text=(
                    "California metros can show technology layoffs, rent stress, "
                    "utility bills, and repair searches."
                ),
                geography="US-CA",
            ),
        ]
    )
    return LightweightRAGRetriever(kb)


def test_ontology_contains_required_categories():
    manager = KeywordOntologyManager()
    labels = {category.label for category in manager.categories.values()}
    assert "discretionary contraction" in labels
    assert "repair vs replacement" in labels
    assert "discount-seeking" in labels
    assert "debt stress" in labels
    assert "layoffs" in labels
    assert "inflation anxiety" in labels
    assert "substitution behavior" in labels
    assert "micro-luxury persistence" in labels
    assert "regional economic anxiety" in labels
    assert "location-specific consumer stress signals" in labels


def test_generation_includes_required_reviewable_fields_and_rag_context():
    manager = KeywordOntologyManager()
    pipeline = KeywordGenerationPipeline(manager, _retriever(), max_variants_per_seed=2)
    geo = GeoMetadata(
        geo_id="US-CA",
        name="California",
        level="state",
        country_code="US",
        region_code="US-CA",
        provider_geo_code="US-CA",
    )

    candidates = pipeline.generate(
        [SeedTerm("cheap groceries", "discount_seeking", "codebook value-seeking term")],
        [geo],
    )

    assert candidates
    candidate = candidates[0]
    assert candidate.source_context
    assert candidate.ontology_category == "discount_seeking"
    assert candidate.expected_direction_under_stress == "increase"
    assert candidate.target_geography.geo_id == "US-CA"
    assert candidate.language_locale == "en"
    assert 0 <= candidate.confidence_score <= 1
    assert "RAG supplied" in candidate.reason_for_inclusion
    assert candidate.review_status == "pending_review"


def test_validation_and_registry_human_approval_versioning_and_dedup():
    manager = KeywordOntologyManager()
    validation = KeywordValidationPipeline(manager, min_confidence=0.1)
    geo = GeoMetadata(geo_id="US", name="United States", level="country", country_code="US")
    candidate = KeywordCandidate(
        keyword="appliance repair",
        source_context=[{"doc_id": "doc1", "snippet": "repair terms increase"}],
        ontology_category="repair_vs_replacement",
        expected_direction_under_stress="increase",
        target_geography=geo,
        language_locale="en",
        confidence_score=0.7,
        reason_for_inclusion="Grounded in codebook repair notes.",
    )

    result = validation.validate(candidate)
    assert result.valid

    registry = GeoAwareKeywordRegistry(max_pending_per_geo_category=2)
    added = registry.add_candidate(candidate)
    duplicate = registry.add_candidate(candidate)
    assert duplicate.canonical_key == added.canonical_key

    approved = registry.approve(
        added.canonical_key, reviewer="analyst", note="approved for fixture"
    )
    assert approved.review_status == "approved"
    assert approved.version == 2

    retired = registry.retire(added.canonical_key, reviewer="analyst", reason="provider drift")
    assert retired.review_status == "retired"
    assert retired.version == 3
    assert registry.history[-1]["action"] == "retire"


def test_unsupported_low_volume_locations_are_tracked_and_not_generated():
    manager = KeywordOntologyManager()
    pipeline = KeywordGenerationPipeline(manager, _retriever())
    low_volume_geo = GeoMetadata(
        geo_id="US-CA-TINY",
        name="Tiny Place",
        level="city",
        country_code="US",
        region_code="US-CA",
        supported=True,
        low_volume=True,
    )

    generated = pipeline.generate(
        [SeedTerm("rent help", "debt_stress", "historical reports mention rent stress")],
        [low_volume_geo],
    )
    assert generated == []

    registry = GeoAwareKeywordRegistry()
    candidate = KeywordCandidate(
        keyword="rent help tiny place",
        source_context=[{"doc_id": "doc2", "snippet": "rent stress"}],
        ontology_category="debt_stress",
        expected_direction_under_stress="increase",
        target_geography=low_volume_geo,
        language_locale="en",
        confidence_score=0.5,
        reason_for_inclusion="Testing low volume handling.",
    )
    try:
        registry.add_candidate(candidate)
    except ValueError as exc:
        assert "unsupported or low-volume" in str(exc)
    else:
        raise AssertionError("low-volume geography should be blocked")
    assert registry.unsupported_locations()[0].geo_id == "US-CA-TINY"


def test_expansion_limit_and_drift_review_heuristic():
    geo = GeoMetadata(geo_id="US", name="United States", level="country", country_code="US")
    registry = GeoAwareKeywordRegistry(max_pending_per_geo_category=1)
    first = KeywordCandidate(
        keyword="coupon groceries",
        source_context=[{"doc_id": "doc1"}],
        ontology_category="discount_seeking",
        expected_direction_under_stress="increase",
        target_geography=geo,
        language_locale="en",
        confidence_score=0.6,
        reason_for_inclusion="Grounded coupon term.",
    )
    second = KeywordCandidate(
        keyword="clearance groceries",
        source_context=[{"doc_id": "doc1"}],
        ontology_category="discount_seeking",
        expected_direction_under_stress="increase",
        target_geography=geo,
        language_locale="en",
        confidence_score=0.6,
        reason_for_inclusion="Grounded clearance term.",
    )
    registry.add_candidate(first)
    try:
        registry.add_candidate(second)
    except ValueError as exc:
        assert "expansion limit" in str(exc)
    else:
        raise AssertionError("expansion limit should block the second pending keyword")

    assert needs_drift_review(retrieval_score=0.2, zero_volume_share=0.1, months_since_review=1)
    assert needs_drift_review(retrieval_score=0.8, zero_volume_share=0.7, months_since_review=1)
    assert needs_drift_review(retrieval_score=0.8, zero_volume_share=0.1, months_since_review=6)
