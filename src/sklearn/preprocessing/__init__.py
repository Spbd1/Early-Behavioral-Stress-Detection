"""Minimal preprocessing shims."""
from __future__ import annotations


class StandardScaler:
    def fit_transform(self, x):
        return x


class RobustScaler:
    def fit_transform(self, x):
        return x
