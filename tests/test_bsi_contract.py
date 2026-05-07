from behavioral_stress.alerting import BehavioralStressIndex, BSIInput


def test_mvp_bsi_output_includes_safety_and_reliability_fields():
    result = BehavioralStressIndex.compute(
        BSIInput(
            hmm_stress_posterior=0.8,
            anomaly_strength=0.7,
            signal_breadth=0.6,
            persistence=0.65,
            trend_acceleration=0.5,
            data_quality=0.9,
            drift_confidence=0.75,
            geographic_confidence=0.85,
            signal_contributions={"debt": 0.7, "jobs": 0.5},
            limitations=["Synthetic fixture only."],
        )
    )

    payload = result.to_dict()

    assert payload["implementation_label"] == "MVP BSI"
    assert 0 <= payload["score"] <= 100
    assert payload["severity_band"] in {"watch", "yellow", "orange", "red"}
    assert payload["uncertainty_band"][0] <= payload["score"] <= payload["uncertainty_band"][1]
    assert payload["reliability_score"] == 0.75
    assert payload["top_contributing_signals"][0] == {"signal": "debt", "contribution": 0.7}
    assert any("Experimental MVP BSI" in warning for warning in payload["warnings"])
    assert any("not a recession prediction" in warning for warning in payload["warnings"])
    assert any("Synthetic fixture only." in item for item in payload["limitations"])
    assert set(payload["components"]) == set(BehavioralStressIndex.WEIGHTS)


def test_bsi_docs_label_mvp_and_deferred_design_components():
    bsi_source = open("src/behavioral_stress/alerting/bsi.py", encoding="utf-8").read()
    readme = open("README.md", encoding="utf-8").read()
    design = open("BSI_DESIGN.md", encoding="utf-8").read()

    assert "MVP Behavioral Stress Index" in bsi_source
    assert "Deferred from the fuller design" in bsi_source
    assert "Implemented MVP BSI" in readme
    assert "Design-only specification" in design
