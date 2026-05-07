"""Cautious event-study design templates for aggregate observational traces."""

from __future__ import annotations

import pandas as pd


def simple_event_study_design_matrix(
    index: pd.Index, event_time: pd.Timestamp, min_lag: int = -4, max_lag: int = 8
) -> pd.DataFrame:
    """Build relative-time indicators around an event without claiming causal identification.

    Observational aggregate digital traces do not identify causal effects by
    themselves; endogeneity, omitted variables, policy feedback, ecological
    fallacy, and time-varying confounding remain threats.
    """
    positions = pd.Series(range(len(index)), index=index)
    event_pos = int(positions.loc[event_time]) if event_time in positions.index else len(index) // 2
    rel = positions.to_numpy() - event_pos
    return pd.DataFrame(
        {f"event_time_{k}": (rel == k).astype(int) for k in range(min_lag, max_lag + 1)},
        index=index,
    )
