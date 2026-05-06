"""Data and report validation guardrails."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ValidationFinding:
    name: str
    ok: bool
    message: str


def validate_schema(frame: pd.DataFrame, required_columns: list[str]) -> list[ValidationFinding]:
    missing = [column for column in required_columns if column not in frame.columns]
    message = "missing columns: " + ", ".join(missing) if missing else "schema ok"
    return [ValidationFinding("schema", not missing, message)]


def detect_temporal_leakage(
    frame: pd.DataFrame,
    timestamp_column: str,
    available_at_column: str,
) -> list[ValidationFinding]:
    if timestamp_column not in frame or available_at_column not in frame:
        return [ValidationFinding("temporal_leakage", False, "timestamp columns missing")]
    timestamps = pd.to_datetime(frame[timestamp_column])
    available = pd.to_datetime(frame[available_at_column])
    leaked = frame.loc[available < timestamps]
    return [
        ValidationFinding(
            "temporal_leakage",
            leaked.empty,
            f"{len(leaked)} rows available before event time",
        )
    ]


def validate_geo_data(frame: pd.DataFrame) -> list[ValidationFinding]:
    required = ["country", "region", "city"]
    findings = validate_schema(frame, required)
    if all(column in frame for column in required):
        blank_strings = frame[required].astype(str).apply(lambda col: col.str.strip()).eq("")
        blank = frame[required].isna().any(axis=1) | blank_strings.any(axis=1)
        findings.append(
            ValidationFinding(
                "geo",
                not blank.any(),
                f"{int(blank.sum())} rows have incomplete geography",
            )
        )
    return findings


def backtest_alert_threshold(series: list[float], threshold: float) -> dict[str, Any]:
    crossings = [index for index, value in enumerate(series) if value >= threshold]
    return {"threshold": threshold, "crossings": crossings, "alert_count": len(crossings)}


def report_snapshot(report: dict[str, Any]) -> dict[str, Any]:
    """Return a stable, non-floating snapshot structure for regression tests."""
    return {
        "title": report.get("title"),
        "has_summary": bool(report.get("summary")),
        "alert_count": int(report.get("alert_count", 0)),
        "metric_rows": len(report.get("metrics", [])),
    }
