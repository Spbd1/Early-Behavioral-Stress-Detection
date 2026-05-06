"""Preprocessing helpers for aggregate time-series traces."""
from __future__ import annotations

import pandas as pd
from sklearn.preprocessing import RobustScaler, StandardScaler


def standardize_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Z-score numeric columns using only the provided frame."""
    scaler = StandardScaler()
    values = scaler.fit_transform(df.astype(float).values)
    return pd.DataFrame(values, index=df.index, columns=df.columns)


def robust_scale_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Robust-scale numeric columns using median and IQR of the provided frame."""
    scaler = RobustScaler()
    values = scaler.fit_transform(df.astype(float).values)
    return pd.DataFrame(values, index=df.index, columns=df.columns)


def add_missingness_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Append binary missingness indicators and impute missing numeric values by column median."""
    result = df.copy()
    for column in df.columns:
        result[f"{column}_missing"] = df[column].isna().astype(int)
    return result.fillna(result.median(numeric_only=True))


def winsorize_frame(df: pd.DataFrame, lower: float = 0.01, upper: float = 0.99) -> pd.DataFrame:
    """Clip each column to empirical quantiles computed on the provided frame."""
    if not 0 <= lower < upper <= 1:
        raise ValueError("Require 0 <= lower < upper <= 1")
    return df.clip(lower=df.quantile(lower), upper=df.quantile(upper), axis=1)


def train_test_time_split(df: pd.DataFrame, train_fraction: float = 0.7) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a time-ordered frame without shuffling or future leakage."""
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1")
    split = max(1, min(len(df) - 1, int(len(df) * train_fraction)))
    return df.iloc[:split].copy(), df.iloc[split:].copy()
