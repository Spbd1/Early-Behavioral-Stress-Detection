import json

from behavioral_stress.alerting import (
    AlertHistory,
    AlertObservation,
    GeoAwareAlertEngine,
    GeoComparisonBuilder,
    GeoTimePoint,
    GeoUnit,
    JsonlAlertHistory,
    ReportGenerator,
)


def _high_observation(timestamp="2026-05-07", geo=None):
    return AlertObservation(
        timestamp=timestamp,
        geo=geo
        or GeoUnit("US", "United States", "country", reliability_score=0.95, sample_size=500),
        hmm_stress_posterior=0.86,
        anomaly_strength=0.84,
        keyword_family_scores={"jobs": 0.86, "debt": 0.82, "housing": 0.72},
        persistence_score=0.83,
        trend_acceleration=0.70,
        drift_confidence=0.81,
        data_quality_score=0.93,
        ontology_category_scores={"employment_stress": 0.80, "debt_stress": 0.72},
        recent_change=12.0,
        limitations=("Synthetic offline fixture only.",),
    )


def test_jsonl_alert_history_persists_and_replays(tmp_path):
    history_path = tmp_path / "alerts.jsonl"
    engine = GeoAwareAlertEngine(history=JsonlAlertHistory(history_path))

    decision = engine.evaluate(_high_observation())

    assert history_path.exists()
    lines = history_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["alert_id"] == decision.alert_id

    reloaded = JsonlAlertHistory(history_path)
    assert reloaded.replay()[0]["alert_id"] == decision.alert_id
    assert reloaded.recent("US")[0]["level"] == decision.level
    assert reloaded.last_alert("US")["alert_id"] == decision.alert_id


def test_in_memory_alert_history_loads_serialized_events():
    first_history = AlertHistory()
    engine = GeoAwareAlertEngine(history=first_history)
    decision = engine.evaluate(_high_observation())

    loaded_history = AlertHistory(events=first_history.replay())

    assert loaded_history.replay()[0]["alert_id"] == decision.alert_id
    assert loaded_history.last_alert("US")["level"] == decision.level


def test_offline_bsi_alert_report_dashboard_smoke_payload_is_safe_json():
    engine = GeoAwareAlertEngine(history=AlertHistory())
    decision = engine.evaluate(_high_observation())
    report = ReportGenerator().generate(decisions=[decision])
    dashboard_payload = engine.dashboard_payload([decision])
    dashboard_payload["report"] = report.structured
    dashboard_payload["report_markdown"] = report.markdown

    encoded = json.dumps(dashboard_payload, sort_keys=True)

    assert decision.bsi.score > 0
    assert decision.level in {"yellow", "orange", "red"}
    assert dashboard_payload["alerts"][0]["bsi"]["score"] == decision.bsi.score
    assert "behavioral stress signal increased" in encoded.lower()
    assert "recession is coming" not in encoded.lower()
    assert "Synthetic offline fixture only." in encoded


def test_low_confidence_metro_suppresses_high_signal_alert():
    engine = GeoAwareAlertEngine()
    low_confidence_metro = GeoUnit(
        "US-LOW-METRO",
        "Sparse metro",
        "metro",
        reliability_score=0.42,
        sample_size=12,
    )

    decision = engine.evaluate(_high_observation(geo=low_confidence_metro))

    assert decision.level == "none"
    assert "geographic_reliability_below_threshold" in decision.suppressions
    assert any("sparse" in warning.lower() for warning in decision.warnings)
    assert decision.confidence < 0.70


def test_unsupported_geography_does_not_emit_high_confidence_alert():
    engine = GeoAwareAlertEngine()
    unsupported_geo = GeoUnit(
        "UNSUPPORTED-X",
        "Unsupported synthetic area",
        "neighborhood",
        reliability_score=0.99,
        sample_size=1000,
        supported=False,
    )

    decision = engine.evaluate(_high_observation(geo=unsupported_geo))

    assert decision.level == "none"
    assert "unsupported_geography" in decision.suppressions
    assert any("unsupported" in warning.lower() for warning in decision.warnings)
    assert decision.confidence < 0.90


def test_geo_comparison_low_confidence_city_payload_carries_warnings():
    city = GeoUnit("US-CITY", "Sparse city", "city", reliability_score=0.50, sample_size=9)
    history = [
        GeoTimePoint(city, "2026-05-01", {"stress": 3.0}),
        GeoTimePoint(city, "2026-05-02", {"stress": 4.0}),
    ]
    current = [GeoTimePoint(city, "2026-05-07", {"stress": 5.0})]

    payload = GeoComparisonBuilder().build(current, history)

    warnings = payload["rows"][0]["warnings"]
    assert any("sparse or unstable" in warning for warning in warnings)
    assert any("low sample size" in warning for warning in warnings)
