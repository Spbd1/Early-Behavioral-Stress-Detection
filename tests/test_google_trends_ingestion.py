from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from behavioral_stress.ingestion.config import (
    CacheConfig,
    GoogleTrendsIngestionConfig,
    RateLimitConfig,
    RetryConfig,
    StorageConfig,
    load_ingestion_config,
)
from behavioral_stress.ingestion.trends import (
    GoogleTrendsIngestionPipeline,
    normalize_batch,
    validate_trends_frame,
)


class FlakyFixtureClient:
    def __init__(self):
        self.calls = 0
        self.requests = []

    def interest_over_time(self, keywords, timeframe, geo, category, gprop):
        self.calls += 1
        self.requests.append((tuple(keywords), timeframe, geo, category, gprop))
        if self.calls == 1:
            raise RuntimeError("transient")
        index = pd.date_range("2024-01-01", periods=4, freq="D")
        return pd.DataFrame({keyword: [50, 50, 50, 50] for keyword in keywords}, index=index)


def _config(tmp_path: Path) -> GoogleTrendsIngestionConfig:
    return GoogleTrendsIngestionConfig(
        keywords=["anchor", "kw1", "kw2", "kw3", "kw4", "kw5"],
        anchor_keyword="anchor",
        regions=["US"],
        timeframe="2024-01-01 2024-01-04",
        batch_size=3,
        incremental=False,
        storage=StorageConfig(
            raw_directory=tmp_path / "raw",
            processed_directory=tmp_path / "processed",
            metadata_directory=tmp_path / "metadata",
        ),
        cache=CacheConfig(directory=tmp_path / "cache", ttl_seconds=3600, enabled=True),
        retry=RetryConfig(max_attempts=2, backoff_seconds=0, backoff_multiplier=1),
        rate_limit=RateLimitConfig(requests_per_minute=1_000_000),
    )


def test_pipeline_retries_batches_caches_and_separates_outputs(tmp_path):
    client = FlakyFixtureClient()
    pipeline = GoogleTrendsIngestionPipeline(_config(tmp_path), client=client)

    outputs = pipeline.run()

    assert client.calls == 4  # one failed attempt plus three successful keyword batches
    assert Path(outputs["processed_US"]).exists()
    assert Path(outputs["metadata"]).exists()
    assert len(list((tmp_path / "raw").glob("*.csv"))) == 3
    assert len(list((tmp_path / "cache").glob("*.csv"))) == 3

    processed = pd.read_csv(outputs["processed_US"])
    assert set(processed["keyword"]) == {"kw1", "kw2", "kw3", "kw4", "kw5"}
    assert set(processed["value_normalized"]) == {100.0}

    metadata = json.loads(Path(outputs["metadata"]).read_text(encoding="utf-8"))
    assert metadata["regions"][0]["timeframes"][0]["batches"][0]["validation"]["status"] == "pass"

    second_client = FlakyFixtureClient()
    GoogleTrendsIngestionPipeline(_config(tmp_path), client=second_client).run()
    assert second_client.calls == 0


def test_validation_flags_sparse_and_unstable_anchor():
    frame = pd.DataFrame(
        {"anchor": [0, 100, 0, 100], "rare": [0, 0, 0, 1]},
        index=pd.date_range("2024-01-01", periods=4),
    )
    config = _config(Path("/tmp"))

    result = validate_trends_frame(frame, ["anchor", "rare"], config.validation, "anchor")

    assert result["status"] == "fail"
    assert any(issue.startswith("low_nonzero:rare") for issue in result["issues"])
    assert any(issue.startswith("nonpositive_anchor:anchor") for issue in result["issues"])


def test_normalize_batch_uses_anchor_for_consistent_scaling():
    frame = pd.DataFrame(
        {"anchor": [50, 100], "kw": [25, 100]}, index=pd.date_range("2024-01-01", periods=2)
    )

    normalized = normalize_batch(frame, ["anchor", "kw"], "anchor")

    assert normalized["value_normalized"].tolist() == [50.0, 100.0]
    assert normalized["anchor_value"].tolist() == [50.0, 100.0]


def test_load_ingestion_config_supports_nested_sections(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(
        """
google_trends:
  keywords: [anchor, kw]
  anchor_keyword: anchor
  storage:
    raw_directory: raw_dir
  cache:
    enabled: false
  retry:
    max_attempts: 5
""",
        encoding="utf-8",
    )

    config = load_ingestion_config(path)

    assert config.keywords == ["anchor", "kw"]
    assert config.storage.raw_directory == Path("raw_dir")
    assert config.cache.enabled is False
    assert config.retry.max_attempts == 5
