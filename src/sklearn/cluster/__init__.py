"""Minimal clustering shims."""

from __future__ import annotations


class KMeans:
    """Deterministic placeholder KMeans."""

    def __init__(self, n_clusters=3, n_init=10, random_state=None):
        self.n_clusters = n_clusters

    def fit_predict(self, x):
        labels = [idx % self.n_clusters for idx, _ in enumerate(x)]
        self.cluster_centers_ = [list(x[idx]) for idx in range(min(self.n_clusters, len(x)))]
        return labels
