"""Build Chrome-friendly dashboard data from workflow artifacts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from behavioral_stress.ops.health import build_health_report

EXPERIMENTAL_LABEL = (
    "Experimental research prototype — not a validated forecasting or policy system."
)
CLAIM_GUARDRAIL = (
    "Behavioral Stress Index (BSI) values are aggregate research signals; "
    "they are not recession predictions and must not be used for automated decisions."
)
SCHEMA_VERSION = "dashboard.v1"
EXPORT_FILENAME = "experimental-behavioral-stress-report.json"


def build_dashboard_payload(
    data_dir: str | Path = "data/synthetic",
    config_path: str | Path = "configs/default.yaml",
) -> dict[str, Any]:
    """Return dashboard-ready JSON with conservative labels and warnings."""
    data_path = Path(data_dir)
    quality_warnings: list[str] = []
    drift_warnings = ["Drift checks are sentinels only; investigate before acting."]
    geo_reliability_warnings = [
        "Geo comparison rows are synthetic/demo metadata and are not a validated map.",
        "Cross-geography interpretation must account for local baselines, "
        "sample size, and provider coverage.",
    ]

    posterior = _read_csv(data_path / "posterior.csv")
    observations = _read_csv(data_path / "observations.csv")
    metrics = _read_csv(data_path / "metrics.csv")
    viterbi = _read_csv(data_path / "viterbi_path.csv")

    if posterior.empty:
        quality_warnings.append("No posterior artifact found. Run the synthetic workflow first.")
    if observations.empty:
        quality_warnings.append(
            "No observation artifact found; top contributing signals are unavailable."
        )

    bsi = _bsi_series(posterior)
    alerts = _alert_timeline(bsi, viterbi)
    geo_comparison = _geo_comparison(bsi)
    report = _report(metrics, alerts, quality_warnings, drift_warnings, geo_reliability_warnings)
    locations = _locations()
    geo_metadata = {
        **locations,
        "comparison_mode": "synthetic_demo_rows_not_validated_map",
        "reliability_notes": geo_reliability_warnings,
        "default_selection": {
            "country": "United States",
            "region": "National synthetic",
            "city": "All metros",
        },
    }

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "label": EXPERIMENTAL_LABEL,
        "system": {
            "label": EXPERIMENTAL_LABEL,
            "claim_guardrail": CLAIM_GUARDRAIL,
            "experimental": True,
        },
        "locations": locations,
        "geo_metadata": geo_metadata,
        "warnings": {
            "data_quality": quality_warnings,
            "drift": drift_warnings,
            "geo_reliability": geo_reliability_warnings,
        },
        # Backward-compatible aliases used by the simple frontend.
        "quality_warnings": quality_warnings,
        "drift_warnings": drift_warnings,
        "geo_reliability_warnings": geo_reliability_warnings,
        "health": build_health_report(config_path).as_dict(),
        "bsi": bsi,
        "posterior": _records(posterior),
        "alerts": alerts,
        "top_signals": _top_signals(observations),
        "geo_comparison": geo_comparison,
        "report": report,
        "reports": {
            "primary": report,
            "export_filename": EXPORT_FILENAME,
            "export_status": "available_static_json_export",
        },
        "static_mode": {
            "supported": True,
            "data_file": "dashboard.json",
            "requires_backend": False,
        },
    }
    validate_dashboard_payload(payload)
    return payload


def write_dashboard_payload(
    output_path: str | Path,
    data_dir: str | Path = "data/synthetic",
    config_path: str | Path = "configs/default.yaml",
) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    payload = build_dashboard_payload(data_dir, config_path)
    Path(output_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def validate_dashboard_payload(payload: dict[str, Any]) -> None:
    """Validate the dashboard API/static JSON contract without extra dependencies."""
    required_types: dict[str, type | tuple[type, ...]] = {
        "schema_version": str,
        "label": str,
        "system": dict,
        "locations": dict,
        "geo_metadata": dict,
        "warnings": dict,
        "quality_warnings": list,
        "drift_warnings": list,
        "geo_reliability_warnings": list,
        "bsi": list,
        "posterior": list,
        "alerts": list,
        "top_signals": list,
        "geo_comparison": list,
        "report": dict,
        "reports": dict,
        "static_mode": dict,
    }
    for key, expected_type in required_types.items():
        if key not in payload:
            raise ValueError(f"Dashboard payload missing required key: {key}")
        if not isinstance(payload[key], expected_type):
            raise TypeError(f"Dashboard payload key {key!r} must be {expected_type}.")

    if payload["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"Unsupported dashboard schema_version: {payload['schema_version']!r}")
    if "not recession" not in payload["system"].get("claim_guardrail", ""):
        raise ValueError("Dashboard guardrail must state that BSI is not recession prediction.")
    if payload["static_mode"].get("requires_backend") is not False:
        raise ValueError("Static dashboard mode must not require a backend.")

    warning_groups = payload["warnings"]
    for name in ("data_quality", "drift", "geo_reliability"):
        if not isinstance(warning_groups.get(name), list):
            raise TypeError(f"Dashboard warnings.{name} must be a list.")

    for point in payload["bsi"]:
        _require_keys(point, {"date": str, "value": (int, float), "severity_band": str})
    for alert in payload["alerts"]:
        _require_keys(alert, {"date": str, "level": str, "message": str, "bsi_score": (int, float)})
    for row in payload["geo_comparison"]:
        _require_keys(
            row,
            {
                "country": str,
                "region": str,
                "city": str,
                "bsi": (int, float),
                "reliability_score": (int, float),
                "warnings": list,
            },
        )
    _require_keys(
        payload["report"], {"title": str, "summary": str, "metrics": list, "alert_count": int}
    )


def _require_keys(row: dict[str, Any], required: dict[str, type | tuple[type, ...]]) -> None:
    for key, expected_type in required.items():
        if key not in row:
            raise ValueError(f"Dashboard row missing required key: {key}")
        if not isinstance(row[key], expected_type):
            raise TypeError(f"Dashboard row key {key!r} must be {expected_type}.")


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def _bsi_series(posterior: pd.DataFrame) -> list[dict[str, Any]]:
    if posterior.empty:
        return []
    date_col = posterior.columns[0]
    state_cols = [col for col in posterior.columns if col.startswith("state_")]
    stress_col = state_cols[-1] if state_cols else posterior.columns[-1]
    rows = []
    for _, row in posterior.iterrows():
        value = round(float(row[stress_col]) * 100.0, 2)
        rows.append(
            {
                "date": str(row[date_col]),
                "value": value,
                "severity_band": _severity_band(value),
                "implementation_label": "MVP BSI proxy from stress-state posterior",
            }
        )
    return rows


def _severity_band(value: float) -> str:
    if value >= 85:
        return "red"
    if value >= 75:
        return "orange"
    if value >= 65:
        return "yellow"
    return "watch"


def _alert_timeline(bsi: list[dict[str, Any]], viterbi: pd.DataFrame) -> list[dict[str, Any]]:
    alerts = []
    for point in bsi:
        if point["value"] < 65:
            continue
        alerts.append(
            {
                "date": point["date"],
                "level": point["severity_band"],
                "message": (
                    "BSI threshold crossing for analyst research review only; "
                    "not a recession prediction."
                ),
                "bsi_score": point["value"],
                "severity_band": point["severity_band"],
                "warnings": [
                    "Requires data-quality, drift, and geo reliability review "
                    "before interpretation."
                ],
            }
        )
    if not alerts and not viterbi.empty:
        alerts.append(
            {
                "date": str(viterbi.iloc[-1, 0]),
                "level": "none",
                "message": "No synthetic threshold crossings.",
                "bsi_score": 0.0,
                "severity_band": "watch",
                "warnings": [],
            }
        )
    return alerts[-25:]


def _top_signals(observations: pd.DataFrame) -> list[dict[str, Any]]:
    if observations.empty:
        return []
    numeric = observations.select_dtypes(include="number")
    scores = numeric.abs().tail(min(12, len(numeric))).mean().sort_values(ascending=False).head(8)
    return [
        {"signal": name, "contribution": round(float(value), 3)} for name, value in scores.items()
    ]


def _geo_comparison(bsi: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest = bsi[-1]["value"] if bsi else 0.0
    return [
        _geo_row("United States", "National synthetic", "All metros", latest, 0.90, []),
        _geo_row(
            "United States",
            "Midwest synthetic",
            "Chicago metro",
            max(0.0, latest - 7.5),
            0.74,
            ["Synthetic metro row; verify provider coverage before interpretation."],
        ),
        _geo_row(
            "Canada",
            "Ontario synthetic",
            "Toronto metro",
            max(0.0, latest - 12.0),
            0.68,
            ["Lower synthetic reliability score; treat cross-region comparison as illustrative."],
        ),
    ]


def _geo_row(
    country: str,
    region: str,
    city: str,
    bsi: float,
    reliability_score: float,
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "country": country,
        "region": region,
        "city": city,
        "bsi": round(float(bsi), 2),
        "reliability_score": reliability_score,
        "comparison_mode": "synthetic_local_baseline_demo",
        "warnings": warnings,
        "geo": {
            "country": country,
            "region": region,
            "city": city,
            "reliability_score": reliability_score,
            "warnings": warnings,
        },
    }


def _locations() -> dict[str, Any]:
    return {
        "countries": ["United States", "Canada", "United Kingdom"],
        "regions": {
            "United States": ["National synthetic", "California synthetic", "Midwest synthetic"],
            "Canada": ["National synthetic", "Ontario synthetic"],
            "United Kingdom": ["National synthetic", "England synthetic"],
        },
        "cities": {
            "National synthetic": ["All metros"],
            "California synthetic": ["Los Angeles metro", "San Francisco Bay Area"],
            "Midwest synthetic": ["Chicago metro", "Detroit metro"],
            "Ontario synthetic": ["Toronto metro", "Ottawa metro"],
            "England synthetic": ["London metro", "Manchester metro"],
        },
    }


def _report(
    metrics: pd.DataFrame,
    alerts: list[dict[str, Any]],
    quality_warnings: list[str],
    drift_warnings: list[str],
    geo_reliability_warnings: list[str],
) -> dict[str, Any]:
    return {
        "title": "Experimental Behavioral Stress Report",
        "summary": (
            "Synthetic validation dashboard. BSI values describe aggregate behavioral stress "
            "signals only and are not recession predictions."
        ),
        "metrics": _records(metrics),
        "alert_count": len(alerts),
        "warnings": {
            "data_quality": quality_warnings,
            "drift": drift_warnings,
            "geo_reliability": geo_reliability_warnings,
        },
        "export_status": "available_static_json_export",
    }
