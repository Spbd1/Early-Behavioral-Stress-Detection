"""Build Chrome-friendly dashboard data from workflow artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from behavioral_stress.ops.health import build_health_report

EXPERIMENTAL_LABEL = (
    "Experimental research prototype — not a validated forecasting or policy system."
)


def build_dashboard_payload(
    data_dir: str | Path = "data/synthetic",
    config_path: str | Path = "configs/default.yaml",
) -> dict[str, Any]:
    """Return dashboard-ready JSON with conservative labels and warnings."""
    data_path = Path(data_dir)
    payload: dict[str, Any] = {
        "label": EXPERIMENTAL_LABEL,
        "locations": _locations(),
        "quality_warnings": [],
        "drift_warnings": ["Drift checks are sentinels only; investigate before acting."],
        "health": build_health_report(config_path).as_dict(),
    }
    posterior = _read_csv(data_path / "posterior.csv")
    observations = _read_csv(data_path / "observations.csv")
    metrics = _read_csv(data_path / "metrics.csv")
    viterbi = _read_csv(data_path / "viterbi_path.csv")

    if posterior.empty:
        payload["quality_warnings"].append(
            "No posterior artifact found. Run the synthetic workflow first."
        )
    payload["bsi"] = _bsi_series(posterior)
    payload["posterior"] = _records(posterior)
    payload["alerts"] = _alert_timeline(payload["bsi"], viterbi)
    payload["top_signals"] = _top_signals(observations)
    payload["geo_comparison"] = _geo_comparison(payload["bsi"])
    payload["report"] = _report(metrics, payload["alerts"])
    return payload


def write_dashboard_payload(
    output_path: str | Path,
    data_dir: str | Path = "data/synthetic",
    config_path: str | Path = "configs/default.yaml",
) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    payload = build_dashboard_payload(data_dir, config_path)
    Path(output_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


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
    return [
        {"date": str(row[date_col]), "value": round(float(row[stress_col]) * 100.0, 2)}
        for _, row in posterior.iterrows()
    ]


def _alert_timeline(bsi: list[dict[str, Any]], viterbi: pd.DataFrame) -> list[dict[str, Any]]:
    alerts = []
    for point in bsi:
        level = "watch" if point["value"] >= 65 else "normal"
        if point["value"] >= 85:
            level = "research-review"
        if level != "normal":
            alerts.append(
                {
                    "date": point["date"],
                    "level": level,
                    "message": "Threshold crossing for analyst review only.",
                }
            )
    if not alerts and not viterbi.empty:
        alerts.append(
            {
                "date": str(viterbi.iloc[-1, 0]),
                "level": "normal",
                "message": "No synthetic threshold crossings.",
            }
        )
    return alerts[-25:]


def _top_signals(observations: pd.DataFrame) -> list[dict[str, Any]]:
    if observations.empty:
        return []
    numeric = observations.select_dtypes(include="number")
    scores = numeric.abs().tail(min(12, len(numeric))).mean().sort_values(ascending=False).head(8)
    return [
        {"signal": name, "contribution": round(float(value), 3)}
        for name, value in scores.items()
    ]


def _geo_comparison(bsi: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest = bsi[-1]["value"] if bsi else 0.0
    return [
        {
            "country": "United States",
            "region": "National synthetic",
            "city": "All metros",
            "bsi": latest,
        },
        {
            "country": "United States",
            "region": "Midwest synthetic",
            "city": "Chicago metro",
            "bsi": max(0.0, latest - 7.5),
        },
        {
            "country": "Canada",
            "region": "Ontario synthetic",
            "city": "Toronto metro",
            "bsi": max(0.0, latest - 12.0),
        },
    ]


def _locations() -> dict[str, Any]:
    return {
        "countries": ["United States", "Canada", "United Kingdom"],
        "regions": {
            "United States": ["National synthetic", "California synthetic", "Midwest synthetic"],
            "Canada": ["National synthetic", "Ontario synthetic"],
            "United Kingdom": ["National synthetic", "England synthetic"],
        },
        "cities": {
            "California synthetic": ["Los Angeles metro", "San Francisco Bay Area"],
            "Midwest synthetic": ["Chicago metro", "Detroit metro"],
            "Ontario synthetic": ["Toronto metro", "Ottawa metro"],
            "England synthetic": ["London metro", "Manchester metro"],
        },
    }


def _report(metrics: pd.DataFrame, alerts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "title": "Experimental Behavioral Stress Report",
        "summary": (
            "Synthetic validation dashboard. "
            "Do not interpret as real-world predictive power."
        ),
        "metrics": _records(metrics),
        "alert_count": len(alerts),
    }
