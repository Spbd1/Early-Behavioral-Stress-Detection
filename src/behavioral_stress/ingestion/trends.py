"""Google Trends ingestion pipeline with batching, caching, and normalization."""
from __future__ import annotations

import json
import logging
import re
import time
import uuid
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

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
    """pytrends-backed Google Trends client.

    pytrends is intentionally imported only when this live connector is constructed so package
    imports, offline tests, and dry runs do not require the optional dependency.
    """

    def __init__(self, language: str = "en-US", timezone: int = 0):
        try:
            from pytrends.request import TrendReq
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Live Google Trends ingestion requires the optional pytrends dependency. "
                "Install it with `pip install -e .[ingestion]`, or run with `--dry-run`/"
                "`google_trends.dry_run: true` for offline artifact generation."
            ) from exc

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


class MockTrendsClient:
    """Deterministic offline Google Trends fixture client for dry runs and tests.

    The generated values are intentionally plausible provider-shaped 0-100 indexes, not claims of
    real query volume. Region and keyword differences are deterministic so artifact validation can
    exercise multi-keyword, multi-geo panels without network access.
    """

    def interest_over_time(
        self,
        keywords: list[str],
        timeframe: str,
        geo: str,
        category: int,
        gprop: str,
    ) -> pd.DataFrame:
        dates = _dates_for_timeframe(timeframe)
        geo_seed = sum(ord(char) for char in (geo or "global")) % 17
        data: dict[str, list[int]] = {}
        for keyword_index, keyword in enumerate(keywords):
            keyword_seed = sum(ord(char) for char in keyword) % 23
            baseline = 35 + ((geo_seed + keyword_seed + keyword_index * 3) % 25)
            values = []
            for day_index, _ in enumerate(dates):
                seasonal = ((day_index * (keyword_index + 2) + geo_seed) % 21) - 10
                value = max(0, min(100, baseline + seasonal))
                values.append(int(value))
            data[keyword] = values
        return pd.DataFrame(data, index=dates)


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
        self.client = client or (
            MockTrendsClient()
            if config.dry_run
            else PytrendsClient(config.language, config.timezone)
        )
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
            "dry_run": self.config.dry_run,
            "provider": "mock" if self.config.dry_run else "pytrends",
            "config": _jsonable_config(self.config),
            "regions": [],
            "warnings": [
                "Google Trends values are scaled within a requested keyword set, geography, and "
                "timeframe and should not be naively compared across regions."
            ],
        }

        for region_entry in self.config.regions:
            geo = _geo_from_region_entry(region_entry)
            geo_metadata = build_geo_metadata(region_entry)
            for warning in geo_metadata["warnings"]:
                LOGGER.warning(
                    "google trends geography warning",
                    extra={"ingestion_region": geo, "ingestion_warning": warning},
                )
            region_metadata: dict[str, Any] = {
                "region": geo,
                "geo_metadata": geo_metadata,
                "timeframes": [],
            }
            frames = []
            for timeframe in self._timeframes_for_region(geo):
                result = self._ingest_region_timeframe(run_id, geo, timeframe)
                frames.append(result["processed"])
                region_metadata["timeframes"].append(result["metadata"])
            processed = _merge_processed_frames(frames)
            processed_path = self._processed_path(run_id, geo)
            processed.to_csv(processed_path, index=False)
            processed_validation = validate_processed_artifact(processed_path)
            if processed_validation["status"] == "fail":
                raise ValueError(f"processed artifact validation failed: {processed_validation}")
            outputs[f"processed_{geo or 'global'}"] = str(processed_path)
            region_metadata["processed_path"] = str(processed_path)
            region_metadata["processed_validation"] = processed_validation
            metadata["regions"].append(region_metadata)

        metadata["finished_at"] = datetime.now(UTC).isoformat()
        metadata_path = self.config.storage.metadata_directory / f"{run_id}.json"
        metadata_path.write_text(
            json.dumps(metadata, indent=2, sort_keys=True, default=str), "utf-8"
        )
        metadata_validation = validate_metadata_artifact(metadata_path)
        if metadata_validation["status"] == "fail":
            raise ValueError(f"metadata artifact validation failed: {metadata_validation}")
        outputs["metadata"] = str(metadata_path)
        LOGGER.info("finished trends ingestion", extra={"ingestion_run_id": run_id})
        return outputs

    def _timeframes_for_region(self, region: str) -> list[str]:
        if self.config.dry_run:
            return self.config.all_timeframes()
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
            raw_artifact_validation = validate_raw_artifact(raw_path, batch)
            if raw_artifact_validation["status"] == "fail":
                raise ValueError(f"raw artifact validation failed: {raw_artifact_validation}")
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
                    "raw_artifact_validation": raw_artifact_validation,
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
            "dry_run": self.config.dry_run,
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
                if not self.config.dry_run:
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
        safe_region = _safe_label(region or "global")
        safe_timeframe = _safe_label(timeframe.replace(" ", "_"))
        return (
            self.config.storage.raw_directory
            / f"{run_id}_{safe_region}_{safe_timeframe}_b{batch_index}.csv"
        )

    def _processed_path(self, run_id: str, region: str) -> Path:
        safe_region = _safe_label(region or "global")
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


def validate_raw_artifact(path: str | Path, expected_keywords: list[str]) -> dict[str, object]:
    """Validate a raw provider response CSV artifact for date index and keyword columns."""
    issues: list[str] = []
    path = Path(path)
    if not path.exists():
        return {"status": "fail", "issues": ["missing_file"]}
    try:
        frame = pd.read_csv(path, index_col=0)
    except Exception as exc:  # noqa: BLE001 - artifact boundary should report any parse failure
        return {"status": "fail", "issues": [f"unreadable_csv:{exc.__class__.__name__}"]}
    if frame.empty:
        issues.append("empty_file")
    try:
        dates = pd.to_datetime(frame.index, errors="raise")
    except Exception:  # noqa: BLE001
        issues.append("invalid_date_index")
        dates = pd.Index([])
    if len(dates) and pd.Index(dates).duplicated().any():
        issues.append("duplicate_dates")
    for keyword in expected_keywords:
        if keyword not in frame.columns:
            issues.append(f"missing_column:{keyword}")
            continue
        numeric = pd.to_numeric(frame[keyword], errors="coerce")
        if numeric.notna().sum() == 0:
            issues.append(f"non_numeric_column:{keyword}")
        outside_scale = numeric.dropna()[(numeric.dropna() < 0) | (numeric.dropna() > 100)]
        if not outside_scale.empty:
            issues.append(f"outside_0_100_scale:{keyword}")
    return {"status": "fail" if issues else "pass", "issues": issues, "path": str(path)}


def validate_processed_artifact(path: str | Path) -> dict[str, object]:
    """Validate a processed long-format Google Trends panel artifact."""
    required = [
        "date",
        "keyword",
        "value_raw",
        "value_normalized",
        "anchor_value",
        "region",
        "timeframe",
    ]
    issues: list[str] = []
    path = Path(path)
    if not path.exists():
        return {"status": "fail", "issues": ["missing_file"]}
    try:
        frame = pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001
        return {"status": "fail", "issues": [f"unreadable_csv:{exc.__class__.__name__}"]}
    if frame.empty:
        issues.append("empty_file")
    for column in required:
        if column not in frame.columns:
            issues.append(f"missing_column:{column}")
    if issues:
        return {"status": "fail", "issues": issues, "path": str(path)}
    if pd.to_datetime(frame["date"], errors="coerce").isna().any():
        issues.append("invalid_dates")
    for column in ["value_raw", "value_normalized", "anchor_value"]:
        if pd.to_numeric(frame[column], errors="coerce").isna().all():
            issues.append(f"non_numeric_column:{column}")
    if frame[["region", "keyword", "date"]].duplicated().any():
        issues.append("duplicate_region_keyword_date")
    if frame["keyword"].isna().any() or (frame["keyword"].astype(str).str.len() == 0).any():
        issues.append("blank_keyword")
    return {"status": "fail" if issues else "pass", "issues": issues, "path": str(path)}


def validate_metadata_artifact(path: str | Path) -> dict[str, object]:
    """Validate run metadata for required run, region, geo, and artifact references."""
    issues: list[str] = []
    path = Path(path)
    if not path.exists():
        return {"status": "fail", "issues": ["missing_file"]}
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"status": "fail", "issues": [f"unreadable_json:{exc.__class__.__name__}"]}
    for field in [
        "run_id",
        "started_at",
        "finished_at",
        "config",
        "regions",
        "provider",
        "dry_run",
    ]:
        if field not in metadata:
            issues.append(f"missing_field:{field}")
    if "regions" in metadata and not isinstance(metadata["regions"], list):
        issues.append("regions_not_list")
    for region_index, region in enumerate(metadata.get("regions", []) or []):
        for field in [
            "region",
            "geo_metadata",
            "timeframes",
            "processed_path",
            "processed_validation",
        ]:
            if field not in region:
                issues.append(f"region_{region_index}_missing_field:{field}")
        processed_path = region.get("processed_path")
        if processed_path and not Path(processed_path).exists():
            issues.append(f"region_{region_index}_missing_processed_path")
        geo_metadata = region.get("geo_metadata", {})
        for field in ["provider_geo", "geography_level", "country", "region", "city", "warnings"]:
            if field not in geo_metadata:
                issues.append(f"region_{region_index}_geo_missing_field:{field}")
        for timeframe_index, timeframe in enumerate(region.get("timeframes", []) or []):
            if "timeframe" not in timeframe or "batches" not in timeframe:
                issues.append(f"region_{region_index}_timeframe_{timeframe_index}_invalid")
            for batch_index, batch in enumerate(timeframe.get("batches", []) or []):
                for field in [
                    "batch_index",
                    "keywords",
                    "raw_path",
                    "validation",
                    "raw_artifact_validation",
                ]:
                    if field not in batch:
                        issues.append(
                            "region_"
                            f"{region_index}_timeframe_{timeframe_index}_batch_"
                            f"{batch_index}_missing_field:{field}"
                        )
                raw_path = batch.get("raw_path")
                if raw_path and not Path(raw_path).exists():
                    issues.append(
                        "region_"
                        f"{region_index}_timeframe_{timeframe_index}_batch_"
                        f"{batch_index}_missing_raw_path"
                    )
    return {"status": "fail" if issues else "pass", "issues": issues, "path": str(path)}


def build_geo_metadata(region_entry: str | dict[str, Any]) -> dict[str, object]:
    """Build preserved geography metadata and conservative Google Trends warnings."""
    if isinstance(region_entry, dict):
        provider_geo = str(region_entry.get("geo", region_entry.get("provider_geo", "")) or "")
        country = region_entry.get("country")
        region = region_entry.get("region")
        city = region_entry.get("city")
    else:
        provider_geo = str(region_entry or "")
        country = None
        region = None
        city = None

    level = "global"
    warnings: list[str] = []
    if provider_geo:
        parts = provider_geo.split("-")
        if len(parts) == 1 and re.fullmatch(r"[A-Z]{2}", provider_geo):
            level = "country"
            country = country or provider_geo
        elif len(parts) == 2 and all(parts):
            level = "region"
            country = country or parts[0]
            region = region or parts[1]
        else:
            level = "unsupported_or_low_volume"
            warnings.append(
                "unsupported_or_low_volume_geography: verify the Google Trends geo code before "
                "using this artifact for analysis"
            )
    if city:
        level = "city"
        warnings.append(
            "city_level_google_trends_inputs_are_often_unsupported_or_low_volume; preserve "
            "metadata but validate provider support before analysis"
        )
    if level in {"region", "city"}:
        warnings.append("low_volume_geographies_may_be_zero_filled_or_suppressed")
    return {
        "input": region_entry,
        "provider_geo": provider_geo,
        "geography_level": level,
        "country": country,
        "region": region,
        "city": city,
        "warnings": warnings,
        "comparability_note": (
            "Raw Google Trends values are scaled within each request and should not be naively "
            "compared across regions."
        ),
    }


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
    safe_region = _safe_label(region or "global")
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


def _geo_from_region_entry(region_entry: str | dict[str, Any]) -> str:
    if isinstance(region_entry, dict):
        return str(region_entry.get("geo", region_entry.get("provider_geo", "")) or "")
    return str(region_entry or "")


def _safe_label(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "global"


def _dates_for_timeframe(timeframe: str) -> pd.DatetimeIndex:
    match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})\s+(\d{4}-\d{2}-\d{2})", timeframe)
    if match:
        start = pd.Timestamp(match.group(1))
        end = pd.Timestamp(match.group(2))
        periods = min(max((end - start).days + 1, 1), 30)
        return pd.date_range(start, periods=periods, freq="D")
    return pd.date_range(end=pd.Timestamp("2024-01-31"), periods=30, freq="D")
