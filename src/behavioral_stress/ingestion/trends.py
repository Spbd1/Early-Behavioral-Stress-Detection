"""Google Trends ingestion pipeline with batching, caching, and normalization."""
from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol

import pandas as pd

from behavioral_stress.ingestion.cache import FileCache
from behavioral_stress.ingestion.config import GoogleTrendsIngestionConfig

LOGGER = logging.getLogger(__name__)


class TrendsClient(Protocol):
    """Minimal protocol implemented by pytrends and test fixtures."""

    def interest_over_time(
        self,
        keywords: list[str],
        timeframe: str,
        geo: str,
        category: int,
        gprop: str,
    ) -> pd.DataFrame:
        """Return Google Trends interest-over-time data."""


class PytrendsClient:
    """pytrends-backed Google Trends client."""

    def __init__(self, language: str = "en-US", timezone: int = 0):
        from pytrends.request import TrendReq

        self._trend_req = TrendReq(hl=language, tz=timezone)

    def interest_over_time(
        self,
        keywords: list[str],
        timeframe: str,
        geo: str,
        category: int,
        gprop: str,
    ) -> pd.DataFrame:
        self._trend_req.build_payload(
            kw_list=keywords, cat=category, timeframe=timeframe, geo=geo, gprop=gprop
        )
        frame = self._trend_req.interest_over_time()
        return frame.drop(columns=["isPartial"], errors="ignore")


class RateLimiter:
    """Wall-clock rate limiter for provider calls."""

    def __init__(self, requests_per_minute: float):
        self.minimum_interval = 60.0 / max(requests_per_minute, 0.001)
        self._last_call = 0.0

    def wait(self) -> None:
        elapsed = time.monotonic() - self._last_call
        remaining = self.minimum_interval - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_call = time.monotonic()


class GoogleTrendsIngestionPipeline:
    """Reusable ingestion layer for Google Trends interest-over-time data.

    The pipeline stores provider responses exactly as raw batch files, then produces a separate
    keyword-by-date processed panel. Processed batches are anchor-normalized when configured so
    that each keyword batch is scaled onto a common anchor series.
    """

    def __init__(self, config: GoogleTrendsIngestionConfig, client: TrendsClient | None = None):
        self.config = config
        self.client = client or PytrendsClient(config.language, config.timezone)
        self.cache = FileCache(
            config.cache.directory, config.cache.ttl_seconds, config.cache.enabled
        )
        self.rate_limiter = RateLimiter(config.rate_limit.requests_per_minute)
        for directory in (
            config.storage.raw_directory,
            config.storage.processed_directory,
            config.storage.metadata_directory,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def run(self) -> dict[str, str]:
        """Run ingestion for configured timeframes and regions."""
        run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        LOGGER.info("starting trends ingestion", extra={"ingestion_run_id": run_id})
        outputs: dict[str, str] = {}
        metadata: dict[str, object] = {
            "run_id": run_id,
            "started_at": datetime.now(UTC).isoformat(),
            "config": _jsonable_config(self.config),
            "regions": [],
        }

        for region in self.config.regions:
            region_metadata = {"region": region, "timeframes": []}
            frames = []
            for timeframe in self._timeframes_for_region(region):
                result = self._ingest_region_timeframe(run_id, region, timeframe)
                frames.append(result["processed"])
                region_metadata["timeframes"].append(result["metadata"])
            processed = _merge_processed_frames(frames)
            processed_path = self._processed_path(run_id, region)
            processed.to_csv(processed_path, index=False)
            outputs[f"processed_{region or 'global'}"] = str(processed_path)
            region_metadata["processed_path"] = str(processed_path)
            metadata["regions"].append(region_metadata)

        metadata["finished_at"] = datetime.now(UTC).isoformat()
        metadata_path = self.config.storage.metadata_directory / f"{run_id}.json"
        metadata_path.write_text(
            json.dumps(metadata, indent=2, sort_keys=True, default=str), "utf-8"
        )
        outputs["metadata"] = str(metadata_path)
        LOGGER.info("finished trends ingestion", extra={"ingestion_run_id": run_id})
        return outputs

    def _timeframes_for_region(self, region: str) -> list[str]:
        if not self.config.incremental:
            return self.config.all_timeframes()
        latest = _latest_processed_date(self.config.storage.processed_directory, region)
        if latest is None:
            return self.config.all_timeframes()
        start = (latest - timedelta(days=self.config.overlap_days)).strftime("%Y-%m-%d")
        end = datetime.now(UTC).strftime("%Y-%m-%d")
        return [f"{start} {end}"]

    def _ingest_region_timeframe(
        self, run_id: str, region: str, timeframe: str
    ) -> dict[str, object]:
        batch_metadata = []
        processed_frames = []
        for index, batch in enumerate(self._keyword_batches()):
            raw = self._fetch_batch(batch, timeframe, region)
            validation = validate_trends_frame(
                raw, batch, self.config.validation, self.config.anchor_keyword
            )
            raw_path = self._raw_path(run_id, region, timeframe, index)
            raw.to_csv(raw_path)
            processed = normalize_batch(raw, batch, self.config.anchor_keyword)
            processed["region"] = region
            processed["timeframe"] = timeframe
            processed_frames.append(processed)
            batch_metadata.append(
                {
                    "batch_index": index,
                    "keywords": batch,
                    "raw_path": str(raw_path),
                    "validation": validation,
                }
            )
            LOGGER.info(
                "ingested trends batch",
                extra={
                    "ingestion_run_id": run_id,
                    "ingestion_region": region,
                    "ingestion_timeframe": timeframe,
                    "ingestion_batch_index": index,
                    "ingestion_quality": validation["status"],
                },
            )
        return {
            "processed": _merge_processed_frames(processed_frames),
            "metadata": {"timeframe": timeframe, "batches": batch_metadata},
        }

    def _keyword_batches(self) -> list[list[str]]:
        keywords = list(dict.fromkeys(self.config.keywords))
        anchor = self.config.anchor_keyword
        payload_size = min(max(self.config.batch_size, 1), 5)
        if anchor and anchor not in keywords:
            keywords.insert(0, anchor)
        non_anchor = [keyword for keyword in keywords if keyword != anchor]
        batch_capacity = payload_size - 1 if anchor else payload_size
        batches = [
            non_anchor[i : i + batch_capacity]
            for i in range(0, len(non_anchor), batch_capacity)
        ]
        if anchor:
            return [[anchor, *batch] for batch in batches]
        return batches

    def _fetch_batch(self, keywords: list[str], timeframe: str, region: str) -> pd.DataFrame:
        request = {
            "keywords": keywords,
            "timeframe": timeframe,
            "region": region,
            "category": self.config.category,
            "gprop": self.config.gprop,
        }
        key = self.cache.key_for(request)
        cached = self.cache.get(key)
        if cached is not None:
            LOGGER.info("cache hit", extra={"ingestion_cache_key": key})
            return cached.frame

        last_error: Exception | None = None
        delay = self.config.retry.backoff_seconds
        for attempt in range(1, self.config.retry.max_attempts + 1):
            try:
                self.rate_limiter.wait()
                frame = self.client.interest_over_time(
                    keywords=keywords,
                    timeframe=timeframe,
                    geo=region,
                    category=self.config.category,
                    gprop=self.config.gprop,
                )
                frame.index = pd.to_datetime(frame.index)
                self.cache.set(key, frame, {"request": request})
                return frame
            except Exception as exc:  # noqa: BLE001 - connector boundary retries arbitrary provider errors
                last_error = exc
                LOGGER.warning(
                    "google trends request failed",
                    extra={"ingestion_attempt": attempt, "ingestion_cache_key": key},
                )
                if attempt < self.config.retry.max_attempts:
                    time.sleep(delay)
                    delay *= self.config.retry.backoff_multiplier
        raise RuntimeError(f"Google Trends request failed after retries: {request}") from last_error

    def _raw_path(self, run_id: str, region: str, timeframe: str, batch_index: int) -> Path:
        safe_region = region or "global"
        safe_timeframe = timeframe.replace(" ", "_").replace("/", "-")
        return (
            self.config.storage.raw_directory
            / f"{run_id}_{safe_region}_{safe_timeframe}_b{batch_index}.csv"
        )

    def _processed_path(self, run_id: str, region: str) -> Path:
        safe_region = region or "global"
        return self.config.storage.processed_directory / f"{run_id}_{safe_region}_processed.csv"


def normalize_batch(
    frame: pd.DataFrame, keywords: list[str], anchor_keyword: str | None
) -> pd.DataFrame:
    """Convert a Google Trends batch into a long, consistently normalized panel."""
    if frame.empty:
        return pd.DataFrame(
            columns=["date", "keyword", "value_raw", "value_normalized", "anchor_value"]
        )
    missing = [keyword for keyword in keywords if keyword not in frame.columns]
    if missing:
        raise ValueError(f"missing expected Google Trends columns: {missing}")
    data = frame[keywords].copy()
    anchor_series = (
        data[anchor_keyword]
        if anchor_keyword in data.columns
        else pd.Series(100.0, index=data.index)
    )
    records = []
    for keyword in keywords:
        if keyword == anchor_keyword:
            continue
        values = data[keyword].astype(float)
        normalized = values / anchor_series.replace(0, pd.NA).astype("Float64") * 100.0
        for date, raw_value in values.items():
            records.append(
                {
                    "date": pd.Timestamp(date).date().isoformat(),
                    "keyword": keyword,
                    "value_raw": float(raw_value) if pd.notna(raw_value) else None,
                    "value_normalized": (
                        float(normalized.loc[date]) if pd.notna(normalized.loc[date]) else None
                    ),
                    "anchor_value": (
                        float(anchor_series.loc[date])
                        if pd.notna(anchor_series.loc[date])
                        else None
                    ),
                }
            )
    return pd.DataFrame.from_records(records)


def validate_trends_frame(
    frame: pd.DataFrame, keywords: list[str], validation, anchor_keyword: str | None = None
) -> dict[str, object]:
    """Flag missing, sparse, or anchor-unstable trend batches."""
    issues: list[str] = []
    if frame.empty:
        issues.append("empty_frame")
        return {"status": "fail", "issues": issues}
    for keyword in keywords:
        if keyword not in frame.columns:
            issues.append(f"missing_column:{keyword}")
            continue
        series = frame[keyword]
        missing_fraction = float(series.isna().mean())
        nonzero_fraction = float((series.fillna(0) > 0).mean())
        if missing_fraction > validation.max_missing_fraction:
            issues.append(f"high_missing:{keyword}:{missing_fraction:.3f}")
        if nonzero_fraction < validation.min_nonzero_fraction:
            issues.append(f"low_nonzero:{keyword}:{nonzero_fraction:.3f}")
    anchor = anchor_keyword
    if validation.require_complete_anchor and anchor and anchor in frame.columns:
        anchor_series = frame[anchor].dropna().astype(float)
        if (anchor_series <= 0).any():
            issues.append(f"nonpositive_anchor:{anchor}")
        mean = anchor_series.mean()
        cv = float(anchor_series.std(ddof=0) / mean) if mean else float("inf")
        if cv > validation.max_batch_anchor_cv:
            issues.append(f"unstable_anchor:{anchor}:{cv:.3f}")
    return {"status": "fail" if issues else "pass", "issues": issues}


def _merge_processed_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    if combined.empty:
        return combined
    combined["date"] = pd.to_datetime(combined["date"])
    combined = combined.sort_values(["region", "keyword", "date", "timeframe"], kind="stable")
    combined = combined.drop_duplicates(["region", "keyword", "date"], keep="last")
    combined["date"] = combined["date"].dt.date.astype(str)
    return combined.reset_index(drop=True)


def _latest_processed_date(processed_directory: Path, region: str) -> datetime | None:
    safe_region = region or "global"
    latest: pd.Timestamp | None = None
    for path in processed_directory.glob(f"*_{safe_region}_processed.csv"):
        frame = pd.read_csv(path, usecols=["date"])
        if frame.empty:
            continue
        candidate = pd.to_datetime(frame["date"]).max()
        latest = candidate if latest is None or candidate > latest else latest
    return latest.to_pydatetime().replace(tzinfo=UTC) if latest is not None else None


def _jsonable_config(config: GoogleTrendsIngestionConfig) -> dict[str, object]:
    payload = asdict(config)
    for section in ("storage", "cache"):
        for key, value in payload[section].items():
            payload[section][key] = str(value)
    return payload
