"""Rolling-origin validation utilities."""
from __future__ import annotations

from collections.abc import Iterator


def rolling_origin_splits(n_samples: int, initial_window: int, horizon: int, step: int) -> Iterator[tuple[slice, slice]]:
    """Yield train/test slices for temporal validation."""
    start = initial_window
    while start + horizon <= n_samples:
        yield slice(0, start), slice(start, start + horizon)
        start += step
