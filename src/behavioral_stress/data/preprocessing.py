"""Preprocessing helpers for dependency-free tabular data."""
from __future__ import annotations

from behavioral_stress.simple_frame import DataFrame


def winsorize_frame(frame: DataFrame, lower: float = 0.01, upper: float = 0.99) -> DataFrame:
    """Clip each column to empirical lower and upper quantiles."""
    rows = [list(row) for row in frame.rows]
    if not rows:
        return DataFrame(rows, columns=frame.columns, index=frame.index)
    for col in range(len(frame.columns)):
        values = sorted(float(row[col]) for row in rows)
        lo = values[int((len(values) - 1) * lower)]
        hi = values[int((len(values) - 1) * upper)]
        for row in rows:
            row[col] = min(max(float(row[col]), lo), hi)
    return DataFrame(rows, columns=frame.columns, index=frame.index)


def standardize_frame(frame: DataFrame) -> DataFrame:
    """Return a column-wise z-score standardized copy of a frame."""
    rows = [list(map(float, row)) for row in frame.rows]
    if not rows:
        return DataFrame(rows, columns=frame.columns, index=frame.index)
    columns = list(zip(*rows))
    means = [sum(col) / len(col) for col in columns]
    stds = []
    for col, mean in zip(columns, means):
        var = sum((value - mean) ** 2 for value in col) / len(col)
        stds.append(var ** 0.5 or 1.0)
    scaled = [[(value - means[idx]) / stds[idx] for idx, value in enumerate(row)] for row in rows]
    return DataFrame(scaled, columns=frame.columns, index=frame.index)
