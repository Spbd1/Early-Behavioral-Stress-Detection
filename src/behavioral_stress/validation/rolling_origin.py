"""Rolling-origin validation splits with no future leakage."""
from __future__ import annotations


def create_rolling_origin_splits(n_samples: int, initial_window: int, horizon: int, step: int) -> list[tuple[slice, slice]]:
    """Return train/test slices where each train window strictly precedes its test window."""
    splits: list[tuple[slice, slice]] = []
    start = int(initial_window)
    while start + horizon <= n_samples:
        splits.append((slice(0, start), slice(start, start + horizon)))
        start += step
    return splits
