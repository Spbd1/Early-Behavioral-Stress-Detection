"""Preprocessing helpers for pandas tabular data."""

from __future__ import annotations

import pandas as pd


def winsorize_frame(frame: pd.DataFrame, lower: float = 0.01, upper: float = 0.99) -> pd.DataFrame:
    """Clip each column to empirical lower and upper quantiles."""
    if frame.empty:
        return frame.copy()
    clipped = frame.astype(float).copy()
    bounds = clipped.quantile([lower, upper])
    return clipped.clip(lower=bounds.loc[lower], upper=bounds.loc[upper], axis="columns")


def standardize_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a column-wise z-score standardized copy of a frame."""
    if frame.empty:
        return frame.copy()
    numeric = frame.astype(float)
    std = numeric.std(axis=0, ddof=0).replace(0, 1.0)
    return (numeric - numeric.mean(axis=0)) / std
