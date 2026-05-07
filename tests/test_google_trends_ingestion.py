from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from behavioral_stress.ingestion.cli import build_parser
from behavioral_stress.ingestion.config import (
    CacheConfig,
    GoogleTrendsIngestionConfig,
    RateLimitConfig,
    RetryConfig,
    StorageConfig,
    ValidationConfig,
    load_ingestion_config,
)
from behavioral_stress.ingestion.trends import (
    GoogleTrendsIngestionPipeline,
    MockTrendsClient,
    PytrendsClient,
    normalize_batch,
    validate_metadata_artifact,
    validate_processed_artifact,
    validate_raw_artifact,
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
        validation=ValidationConfig(min_nonzero_fraction=0.5),
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
  keywords:
    - anchor
    - kw
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


def test_import_and_mock_client_do_not_require_pytrends(tmp_path):
    config = _config(tmp_path).__class__(**{**_config(tmp_path).__dict__, "dry_run": True})
    pipeline = GoogleTrendsIngestionPipeline(config)

    assert isinstance(pipeline.client, MockTrendsClient)


def test_live_client_reports_clear_pytrends_error_when_missing(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def blocked_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("pytrends"):
            raise ModuleNotFoundError("No module named 'pytrends'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", blocked_import)

    try:
        PytrendsClient()
    except RuntimeError as exc:
        assert "optional pytrends dependency" in str(exc)
        assert "--dry-run" in str(exc)
    else:  # pragma: no cover - this should not be reached when import is blocked
        raise AssertionError("PytrendsClient should fail clearly when pytrends is unavailable")


def test_dry_run_writes_valid_artifacts_and_preserves_geo_metadata(tmp_path):
    base = _config(tmp_path)
    config = base.__class__(
        **{
            **base.__dict__,
            "dry_run": True,
            "regions": [
                "US",
                {"geo": "US-CA", "country": "US", "region": "CA", "city": "Los Angeles"},
            ],
            "cache": CacheConfig(directory=tmp_path / "cache", ttl_seconds=3600, enabled=False),
        }
    )

    outputs = GoogleTrendsIngestionPipeline(config).run()

    assert Path(outputs["processed_US"]).exists()
    assert Path(outputs["processed_US-CA"]).exists()
    assert validate_processed_artifact(outputs["processed_US"])["status"] == "pass"
    assert validate_metadata_artifact(outputs["metadata"])["status"] == "pass"

    raw_paths = sorted((tmp_path / "raw").glob("*.csv"))
    assert raw_paths
    assert validate_raw_artifact(raw_paths[0], ["anchor", "kw1", "kw2"])["status"] == "pass"

    metadata = json.loads(Path(outputs["metadata"]).read_text(encoding="utf-8"))
    assert metadata["dry_run"] is True
    assert metadata["provider"] == "mock"
    ca_region = next(region for region in metadata["regions"] if region["region"] == "US-CA")
    assert ca_region["geo_metadata"]["country"] == "US"
    assert ca_region["geo_metadata"]["region"] == "CA"
    assert ca_region["geo_metadata"]["city"] == "Los Angeles"
    assert ca_region["geo_metadata"]["warnings"]
    assert (
        "should not be naively compared across regions"
        in ca_region["geo_metadata"]["comparability_note"]
    )


def test_artifact_validators_flag_schema_errors(tmp_path):
    bad_raw = tmp_path / "bad_raw.csv"
    bad_raw.write_text("date,unexpected\n2024-01-01,1\n", encoding="utf-8")
    assert validate_raw_artifact(bad_raw, ["anchor"])["status"] == "fail"

    bad_processed = tmp_path / "bad_processed.csv"
    bad_processed.write_text("date,keyword\n2024-01-01,kw\n", encoding="utf-8")
    assert validate_processed_artifact(bad_processed)["status"] == "fail"

    bad_metadata = tmp_path / "bad_metadata.json"
    bad_metadata.write_text('{"run_id": "only"}', encoding="utf-8")
    assert validate_metadata_artifact(bad_metadata)["status"] == "fail"


def test_ingestion_cli_help_includes_dry_run():
    parser = build_parser()
    subparsers = next(action for action in parser._actions if action.dest == "command")
    trends_parser = subparsers.choices["google-trends"]

    assert "--dry-run" in trends_parser.format_help()
    assert "google-trends" in parser.format_help()
