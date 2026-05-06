"""Sensitivity-analysis placeholders for exploratory causal interpretation."""
from __future__ import annotations


def estimand_description() -> str:
    """Return the exploratory heterogeneous treatment-effect estimand."""
    return "tau(x) = E[Y(1) - Y(0) | X = x]"
