from pathlib import Path


def test_frontend_has_chrome_friendly_dashboard_elements():
    html = Path("frontend/index.html").read_text(encoding="utf-8")
    app = Path("frontend/app.js").read_text(encoding="utf-8")
    expected_controls = [
        "country",
        "region",
        "city",
        "time-range",
        "bsi-chart",
        "posterior-chart",
        "export-report",
    ]
    for expected in expected_controls:
        assert expected in html
    assert "/api/dashboard.json" in app
    assert "dashboard.json" in app
    assert "not a validated" in html.lower()
