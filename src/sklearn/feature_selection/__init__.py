"""Minimal feature-selection shims."""

from __future__ import annotations


def mutual_info_classif(x, y, **kwargs):
    width = len(x[0]) if x else 0
    return [0.0 for _ in range(width)]
