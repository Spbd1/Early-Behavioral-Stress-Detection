"""Preprocessing helpers for aggregate traces."""
from __future__ import annotations

import pandas as pd
from sklearn.preprocessing import StandardScaler


def standardize_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a z-scored copy of numeric columns."""
    scaler = StandardScaler()
    values = scaler.fit_transform(frame.values)
    return pd.DataFrame(values, index=frame.index, columns=frame.columns)
