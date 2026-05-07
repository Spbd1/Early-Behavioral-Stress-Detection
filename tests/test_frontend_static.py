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
        "geo-warnings",
    ]
    for expected in expected_controls:
        assert expected in html
    assert "/api/dashboard.json" in app
    assert "dashboard.json" in app
    assert "requires_backend: false" in app
    assert "createObjectURL" in app
    assert "geo_reliability_warnings" in app
    assert "innerHTML" not in app
    assert "not a validated" in html.lower()
    assert "recession forecast" in html.lower()


def test_frontend_uses_broadly_supported_browser_apis():
    app = Path("frontend/app.js").read_text(encoding="utf-8")
    unsupported_patterns = [
        "showOpenFilePicker",
        "navigator.gpu",
        "HTMLPortalElement",
        "OffscreenCanvas",
        "SharedArrayBuffer",
        "import(",
    ]
    for pattern in unsupported_patterns:
        assert pattern not in app
