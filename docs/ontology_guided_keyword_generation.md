# Ontology-guided keyword generation with lightweight RAG

This repository includes a deterministic, local-first workflow for generating behavioral stress monitoring keyword candidates across countries, regions, provinces, states, cities, and metros. The workflow is designed for research governance and human review; it is not an autonomous alerting system.

## Ontology categories

`behavioral_stress.keywords.ontology_manager.KeywordOntologyManager` controls the allowed keyword categories:

- discretionary contraction
- repair vs replacement
- discount-seeking
- debt stress
- layoffs
- inflation anxiety
- substitution behavior
- micro-luxury persistence
- regional economic anxiety
- location-specific consumer stress signals

Each category stores a stable key, label, description, default expected direction under stress, and inclusion guidance.

## Local RAG knowledge base

`behavioral_stress.keywords.rag.LocalKnowledgeBase` reads local JSONL snippets from materials such as:

- the project paper or paper summary
- ontology documentation
- keyword codebooks
- historical reports
- manually curated economic notes
- validation notes

The default seed file is `data/knowledge_base/behavioral_stress_keyword_kb.jsonl`. `LightweightRAGRetriever` uses deterministic lexical retrieval with geographic and locale bonuses. RAG is used only to ground explanations and source context for candidate keywords. It must not make alert decisions.

## Generated keyword schema

Every `KeywordCandidate` includes:

- `source_context`
- `ontology_category`
- `expected_direction_under_stress`
- `target_geography`
- `language_locale`
- `confidence_score`
- `reason_for_inclusion`
- `review_status`
- `version`
- `semantic_group`
- optional retirement and drift-review metadata

`GeoMetadata` stores stable geographic identifiers (`geo_id`, `country_code`, optional `region_code`, `metro_code`, and provider code). Locations can be marked `supported=False` or `low_volume=True`; the generator and registry do not assume that Google Trends or any provider supports all locations equally.

## Human-in-the-loop approval and expansion controls

`GeoAwareKeywordRegistry` preserves review state and version history. New candidates enter `pending_review`, and a reviewer must call `approve`, `reject`, `retire`, or `mark_for_drift_review`. The registry:

- deduplicates exact candidates by geography, locale, keyword, and ontology category
- creates deterministic semantic groups
- blocks uncontrolled expansion with `max_pending_per_geo_category`
- rejects unsupported or low-volume geographies unless future code explicitly adds a reviewed override
- preserves history for reproducibility

## Validation, retirement, and drift review

`KeywordValidationPipeline` checks ontology membership, RAG grounding, confidence thresholds, review status, language/locale, and geography support. `needs_drift_review` in `behavioral_stress.keywords.scoring` flags stale, weakly grounded, or low-volume keywords for human review; it does not decide whether stress is present.

## Hallucination risks and mitigation

LLM-assisted ideation can hallucinate local slang, provider support, causal interpretation, or expected direction. The current implementation mitigates those risks by:

1. using a fixed ontology rather than open-ended category creation;
2. requiring local RAG source/context on each candidate;
3. recording geography and locale explicitly with stable codes where possible;
4. forcing generated items into human-review states rather than approval;
5. limiting pending candidates per geography/category;
6. preserving version history, retirement reasons, and drift-review flags; and
7. keeping RAG out of alert decisions.

Future LLM integrations should persist prompts, model/version identifiers, retrieval inputs, retrieved contexts, and raw structured outputs so reviewer decisions are reproducible.
