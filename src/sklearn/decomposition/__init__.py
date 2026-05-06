"""Minimal decomposition shims."""
from __future__ import annotations


class PCA:
    """Placeholder PCA returning leading columns."""

    def __init__(self, n_components=2):
        self.n_components = n_components
        self.explained_variance_ratio_ = [0.0 for _ in range(n_components)]

    def fit_transform(self, x):
        return [list(row)[: self.n_components] for row in x]
