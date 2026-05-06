import pandas as pd

from behavioral_stress.validation.data_quality import (
    backtest_alert_threshold,
    detect_temporal_leakage,
    report_snapshot,
    validate_geo_data,
    validate_schema,
)


def test_schema_validation_detects_missing_columns():
    findings = validate_schema(pd.DataFrame({"date": []}), ["date", "value"])
    assert not findings[0].ok
    assert "value" in findings[0].message


def test_temporal_leakage_detection_flags_future_availability():
    frame = pd.DataFrame({"event_time": ["2024-01-02"], "available_at": ["2024-01-01"]})
    findings = detect_temporal_leakage(frame, "event_time", "available_at")
    assert not findings[0].ok


def test_geo_data_validation_requires_complete_labels():
    frame = pd.DataFrame({"country": ["US"], "region": [""], "city": ["Chicago"]})
    findings = validate_geo_data(frame)
    assert any(not finding.ok for finding in findings)


def test_alert_backtesting_counts_crossings():
    result = backtest_alert_threshold([10, 70, 80], 65)
    assert result["crossings"] == [1, 2]


def test_report_snapshot_is_stable():
    snap = report_snapshot(
        {
            "title": "Experimental",
            "summary": "Do not overclaim",
            "alert_count": 2,
            "metrics": [{}, {}],
        }
    )
    assert snap == {
        "title": "Experimental",
        "has_summary": True,
        "alert_count": 2,
        "metric_rows": 2,
    }
