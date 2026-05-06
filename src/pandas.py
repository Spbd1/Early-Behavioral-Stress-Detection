"""Tiny pandas compatibility shim for import-time optional modules."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from behavioral_stress.simple_frame import DataFrame, Series, Vector

Index = list
Timestamp = str


def read_csv(path: str | Path, **_: Any) -> DataFrame:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        return DataFrame([])
    header = rows[0]
    return DataFrame(rows[1:], columns=header)


def to_datetime(values: Any) -> Any:
    return values
