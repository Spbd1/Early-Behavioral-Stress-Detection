from behavioral_stress.alerting import (
    AlertObservation,
    AlertPolicy,
    BehavioralStressIndex,
    BSIInput,
    GeoAwareAlertEngine,
    GeoComparisonBuilder,
    GeoTimePoint,
    GeoUnit,
    ReportGenerator,
)


def test_bsi_returns_required_structured_fields():
    result = BehavioralStressIndex.compute(
        BSIInput(
            hmm_stress_posterior=0.82,
            anomaly_strength=0.76,
            signal_breadth=0.67,
            persistence=0.74,
            trend_acceleration=0.60,
            data_quality=0.88,
            drift_confidence=0.80,
            geographic_confidence=0.90,
            signal_contributions={"jobs": 0.8, "debt": 0.65, "housing": 0.20},
            recent_change=8.5,
            limitations=["Fixture data only."],
        )
    )

    payload = result.to_dict()
    assert 0 <= payload["score"] <= 100
    assert payload["severity_band"] in {"watch", "yellow", "orange", "red"}
    assert payload["uncertainty_band"][0] <= payload["score"] <= payload["uncertainty_band"][1]
    assert payload["top_contributing_signals"][0]["signal"] == "jobs"
    assert "not a recession prediction" in payload["limitations"][-1]
    assert "Behavioral stress signal increased" in payload["explanation"]


def test_alert_engine_suppresses_single_signal_alerts():
    engine = GeoAwareAlertEngine()
    decision = engine.evaluate(
        AlertObservation(
            timestamp="2026-05-01",
            geo=GeoUnit("US", "United States", "country", reliability_score=0.95, sample_size=500),
            hmm_stress_posterior=0.95,
            anomaly_strength=0.95,
            keyword_family_scores={"jobs": 0.95, "debt": 0.10, "housing": 0.20},
            persistence_score=0.95,
            trend_acceleration=0.90,
            drift_confidence=0.95,
            data_quality_score=0.95,
            ontology_category_scores={"employment_stress": 0.9},
            recent_change=20,
        )
    )

    assert decision.level == "none"
    assert "single_signal_or_insufficient_keyword_family_agreement" in decision.suppressions
    assert "No alert was issued" in decision.explanation


def test_alert_engine_emits_alert_then_applies_cooldown():
    engine = GeoAwareAlertEngine(AlertPolicy(cooldown_periods=2))
    geo = GeoUnit("US-CA", "California", "state", reliability_score=0.92, sample_size=200)
    kwargs = dict(
        geo=geo,
        hmm_stress_posterior=0.86,
        anomaly_strength=0.86,
        keyword_family_scores={"jobs": 0.86, "debt": 0.82, "housing": 0.70},
        persistence_score=0.84,
        trend_acceleration=0.78,
        drift_confidence=0.82,
        data_quality_score=0.91,
        ontology_category_scores={"employment_stress": 0.8, "debt_stress": 0.7},
        recent_change=13,
    )

    first = engine.evaluate(AlertObservation(timestamp="2026-05-01", **kwargs))
    second = engine.evaluate(AlertObservation(timestamp="2026-05-02", **kwargs))

    assert first.level in {"yellow", "orange", "red"}
    assert second.level == "none"
    assert second.cooldown_active is True
    assert "cooldown_active_for_same_or_lower_alert_level" in second.suppressions
    assert second.history[0]["alert_id"] == first.alert_id


def test_geo_comparison_uses_local_baseline_normalization_and_warnings():
    us = GeoUnit("US", "United States", "country", reliability_score=0.95, sample_size=200)
    nyc = GeoUnit("US-NYC", "New York metro", "metro", reliability_score=0.62, sample_size=20)
    history = [
        GeoTimePoint(us, "2026-04-01", {"stress": 50}),
        GeoTimePoint(us, "2026-04-02", {"stress": 60}),
        GeoTimePoint(nyc, "2026-04-01", {"stress": 5}),
        GeoTimePoint(nyc, "2026-04-02", {"stress": 7}),
    ]
    current = [
        GeoTimePoint(us, "2026-05-01", {"stress": 70}),
        GeoTimePoint(nyc, "2026-05-01", {"stress": 9}),
    ]

    payload = GeoComparisonBuilder().build(current, history)

    assert payload["comparison_mode"] == "local_baseline_normalized_z_score"
    assert "raw Google Trends scores must not be compared directly" in payload["warnings"][0]
    assert payload["rows"][0]["normalized_values"]["stress"] == 3.0
    assert payload["rows"][1]["normalized_values"]["stress"] == 3.0
    assert any("low sample size" in warning for warning in payload["rows"][1]["warnings"])


def test_report_generator_avoids_prediction_claims_and_marks_watch():
    engine = GeoAwareAlertEngine()
    decision = engine.evaluate(
        AlertObservation(
            timestamp="2026-05-01",
            geo=GeoUnit("GLOBAL", "Global", "global", reliability_score=0.95, sample_size=1000),
            hmm_stress_posterior=0.50,
            anomaly_strength=0.40,
            keyword_family_scores={"jobs": 0.65, "debt": 0.64},
            persistence_score=0.40,
            trend_acceleration=0.30,
            drift_confidence=0.75,
            data_quality_score=0.90,
            recent_change=4,
        )
    )

    report = ReportGenerator().generate(decisions=[decision])

    assert report.structured["alert_or_watch_signal"] == {"alerts": 0, "watch_signals": 1}
    assert "behavioral stress signal increased" in report.markdown
    assert "not a recession prediction" in report.markdown
    assert "crisis is coming" not in report.markdown.lower()
