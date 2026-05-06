"""Configuration models for ingestion pipelines."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class RetryConfig:
    """Retry behavior for transient provider failures."""

    max_attempts: int = 3
    backoff_seconds: float = 1.0
    backoff_multiplier: float = 2.0


@dataclass(frozen=True)
class RateLimitConfig:
    """Minimum spacing between provider calls."""

    requests_per_minute: float = 12.0


@dataclass(frozen=True)
class CacheConfig:
    """On-disk cache settings for provider responses."""

    directory: Path = Path("data/cache/google_trends")
    ttl_seconds: int | None = 86_400
    enabled: bool = True


@dataclass(frozen=True)
class StorageConfig:
    """Raw, processed, and metadata storage locations."""

    raw_directory: Path = Path("data/raw/google_trends")
    processed_directory: Path = Path("data/processed/google_trends")
    metadata_directory: Path = Path("data/metadata/google_trends")


@dataclass(frozen=True)
class ValidationConfig:
    """Quality gates for sparse or unstable Google Trends data."""

    max_missing_fraction: float = 0.2
    min_nonzero_fraction: float = 0.1
    max_batch_anchor_cv: float = 0.35
    require_complete_anchor: bool = True


@dataclass(frozen=True)
class GoogleTrendsIngestionConfig:
    """End-to-end Google Trends ingestion configuration."""

    keywords: list[str]
    regions: list[str] = field(default_factory=lambda: [""])
    timeframe: str = "today 5-y"
    historical_timeframes: list[str] = field(default_factory=list)
    category: int = 0
    gprop: str = ""
    batch_size: int = 4
    anchor_keyword: str | None = None
    incremental: bool = True
    overlap_days: int = 14
    language: str = "en-US"
    timezone: int = 0
    storage: StorageConfig = field(default_factory=StorageConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)

    def all_timeframes(self) -> list[str]:
        """Return historical windows followed by the current/incremental window."""
        windows = list(dict.fromkeys([*self.historical_timeframes, self.timeframe]))
        return windows


def _paths(cls: type, data: dict[str, Any]) -> dict[str, Any]:
    return {key: Path(value) if key.endswith("directory") else value for key, value in data.items()}


def load_ingestion_config(path: str | Path) -> GoogleTrendsIngestionConfig:
    """Load a Google Trends ingestion config from YAML."""
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if "google_trends" in payload:
        payload = payload["google_trends"] or {}

    payload = dict(payload)
    storage = StorageConfig(**_paths(StorageConfig, payload.pop("storage", {}) or {}))
    cache = CacheConfig(**_paths(CacheConfig, payload.pop("cache", {}) or {}))
    retry = RetryConfig(**(payload.pop("retry", {}) or {}))
    rate_limit = RateLimitConfig(**(payload.pop("rate_limit", {}) or {}))
    validation = ValidationConfig(**(payload.pop("validation", {}) or {}))

    if "keywords" not in payload or not payload["keywords"]:
        raise ValueError("google_trends.keywords must contain at least one keyword")

    return GoogleTrendsIngestionConfig(
        **payload,
        storage=storage,
        cache=cache,
        retry=retry,
        rate_limit=rate_limit,
        validation=validation,
    )
