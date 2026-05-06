"""Geo-aware governed keyword registry with review states and version history."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SUPPORTED_REVIEW_STATUSES = {
    "draft",
    "pending_review",
    "approved",
    "rejected",
    "retired",
    "drift_review",
}
SUPPORTED_GEO_LEVELS = {"country", "region", "state", "province", "city", "metro"}


@dataclass(frozen=True)
class GeoMetadata:
    """Stable geographic metadata for country, region/province/state, city, or metro sets."""

    geo_id: str
    name: str
    level: str
    country_code: str
    region_code: str | None = None
    metro_code: str | None = None
    provider_geo_code: str | None = None
    locale: str = "en"
    supported: bool = True
    low_volume: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        if self.level not in SUPPORTED_GEO_LEVELS:
            raise ValueError(f"Unsupported geography level: {self.level}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KeywordCandidate:
    """Reviewable, reproducible keyword proposal grounded by ontology and RAG context."""

    keyword: str
    source_context: list[dict[str, Any]]
    ontology_category: str
    expected_direction_under_stress: str
    target_geography: GeoMetadata
    language_locale: str
    confidence_score: float
    reason_for_inclusion: str
    review_status: str = "pending_review"
    version: int = 1
    semantic_group: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str | None = None
    retired_reason: str | None = None
    drift_review_due: str | None = None

    def __post_init__(self) -> None:
        if self.review_status not in SUPPORTED_REVIEW_STATUSES:
            raise ValueError(f"Unsupported review status: {self.review_status}")
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("confidence_score must be in [0, 1]")
        if not self.keyword.strip():
            raise ValueError("keyword is required")

    @property
    def canonical_key(self) -> str:
        """Stable key used for exact deduplication within a geography and locale."""
        return "|".join(
            [
                self.target_geography.geo_id,
                self.language_locale.lower(),
                _normalize_keyword(self.keyword),
                self.ontology_category,
            ]
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["target_geography"] = self.target_geography.to_dict()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> KeywordCandidate:
        data = dict(payload)
        data["target_geography"] = GeoMetadata(**data["target_geography"])
        return cls(**data)


class GeoAwareKeywordRegistry:
    """Maintain keyword sets, review approvals, deduplication, grouping, and versions."""

    def __init__(self, *, max_pending_per_geo_category: int = 25) -> None:
        self.max_pending_per_geo_category = max_pending_per_geo_category
        self._items: dict[str, KeywordCandidate] = {}
        self._history: list[dict[str, Any]] = []
        self._unsupported_locations: dict[str, GeoMetadata] = {}

    @property
    def history(self) -> list[dict[str, Any]]:
        return list(self._history)

    def add_candidate(self, candidate: KeywordCandidate) -> KeywordCandidate:
        """Add a candidate unless it is a duplicate or violates expansion controls."""
        if not candidate.target_geography.supported or candidate.target_geography.low_volume:
            self._unsupported_locations[candidate.target_geography.geo_id] = (
                candidate.target_geography
            )
            raise ValueError(
                "Cannot add keywords for unsupported or low-volume locations without override"
            )
        group = candidate.semantic_group or semantic_group(candidate.keyword)
        candidate = replace(candidate, semantic_group=group)
        self._enforce_expansion_limit(candidate)
        existing = self._items.get(candidate.canonical_key)
        if existing:
            return existing
        self._items[candidate.canonical_key] = candidate
        self._record("add", candidate)
        return candidate

    def approve(self, canonical_key: str, reviewer: str, note: str = "") -> KeywordCandidate:
        """Human-in-the-loop approval gate."""
        return self._transition(canonical_key, "approved", reviewer, note)

    def reject(self, canonical_key: str, reviewer: str, note: str = "") -> KeywordCandidate:
        """Reject a candidate during human review."""
        return self._transition(canonical_key, "rejected", reviewer, note)

    def retire(self, canonical_key: str, reviewer: str, reason: str) -> KeywordCandidate:
        """Retire a keyword while preserving versioned history."""
        current = self._require(canonical_key)
        updated = replace(
            current,
            review_status="retired",
            version=current.version + 1,
            updated_at=datetime.now(timezone.utc).isoformat(),
            retired_reason=reason,
        )
        self._items[canonical_key] = updated
        self._record("retire", updated, reviewer=reviewer, note=reason)
        return updated

    def mark_for_drift_review(
        self, canonical_key: str, reviewer: str, note: str = ""
    ) -> KeywordCandidate:
        """Flag a keyword for drift review without making alert decisions."""
        return self._transition(canonical_key, "drift_review", reviewer, note)

    def list_by_geo(self, geo_id: str, *, include_retired: bool = False) -> list[KeywordCandidate]:
        """List keyword candidates for one geography."""
        items = [item for item in self._items.values() if item.target_geography.geo_id == geo_id]
        if not include_retired:
            items = [item for item in items if item.review_status != "retired"]
        return sorted(items, key=lambda item: (item.ontology_category, item.keyword))

    def unsupported_locations(self) -> list[GeoMetadata]:
        """Return locations blocked because support or volume is insufficient."""
        return sorted(self._unsupported_locations.values(), key=lambda item: item.geo_id)

    def to_json(self, path: str | Path) -> None:
        """Persist registry state with version history."""
        payload = {
            "max_pending_per_geo_category": self.max_pending_per_geo_category,
            "items": [item.to_dict() for item in self._items.values()],
            "history": self._history,
            "unsupported_locations": [
                item.to_dict() for item in self._unsupported_locations.values()
            ],
        }
        Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    @classmethod
    def from_json(cls, path: str | Path) -> GeoAwareKeywordRegistry:
        """Load registry state."""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        registry = cls(max_pending_per_geo_category=payload.get("max_pending_per_geo_category", 25))
        registry._items = {
            item.canonical_key: item
            for item in (KeywordCandidate.from_dict(row) for row in payload.get("items", []))
        }
        registry._history = payload.get("history", [])
        registry._unsupported_locations = {
            geo.geo_id: geo
            for geo in (GeoMetadata(**row) for row in payload.get("unsupported_locations", []))
        }
        return registry

    def _enforce_expansion_limit(self, candidate: KeywordCandidate) -> None:
        pending = [
            item
            for item in self._items.values()
            if item.target_geography.geo_id == candidate.target_geography.geo_id
            and item.ontology_category == candidate.ontology_category
            and item.review_status in {"draft", "pending_review"}
        ]
        if len(pending) >= self.max_pending_per_geo_category:
            raise ValueError("Keyword expansion limit exceeded for geography/category")

    def _transition(
        self, canonical_key: str, status: str, reviewer: str, note: str
    ) -> KeywordCandidate:
        current = self._require(canonical_key)
        updated = replace(
            current,
            review_status=status,
            version=current.version + 1,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        self._items[canonical_key] = updated
        self._record(status, updated, reviewer=reviewer, note=note)
        return updated

    def _require(self, canonical_key: str) -> KeywordCandidate:
        if canonical_key not in self._items:
            raise KeyError(f"Unknown keyword candidate: {canonical_key}")
        return self._items[canonical_key]

    def _record(
        self, action: str, candidate: KeywordCandidate, reviewer: str | None = None, note: str = ""
    ) -> None:
        self._history.append(
            {
                "action": action,
                "canonical_key": candidate.canonical_key,
                "version": candidate.version,
                "reviewer": reviewer,
                "note": note,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )


def semantic_group(keyword: str) -> str:
    """Assign a deterministic semantic group using normalized high-signal tokens."""
    tokens = [
        token
        for token in re.findall(r"[a-z0-9]+", keyword.lower())
        if token not in {"near", "me", "the", "a"}
    ]
    return " ".join(sorted(tokens[:4])) or _normalize_keyword(keyword)


def _normalize_keyword(keyword: str) -> str:
    return " ".join(re.findall(r"[\w'-]+", keyword.lower()))
