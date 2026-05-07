"""Data ingestion placeholders.

Real public-data connectors are intentionally not implemented in the first deliverable to avoid
hallucinated data sources and unclear licensing. Use synthetic data by default.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_processed_csv(path: str | Path, date_column: str | None = None) -> pd.DataFrame:
    """Load a processed aggregate CSV file."""
    frame = pd.read_csv(path)
    if date_column:
        frame[date_column] = pd.to_datetime(frame[date_column])
        frame = frame.set_index(date_column)
    return frame
