"""Dimensionality-reduction utilities for exploratory signal discovery."""
from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA


def pca_explore(features: np.ndarray, n_components: int = 2) -> tuple[np.ndarray, PCA]:
    """Fit PCA and return transformed features plus the fitted object."""
    model = PCA(n_components=n_components)
    return model.fit_transform(features), model


def umap_explore(features: np.ndarray, n_components: int = 2) -> np.ndarray:
    """Run UMAP if installed; otherwise raise an informative error."""
    try:
        import umap  # type: ignore
    except ImportError as exc:
        raise ImportError("Install umap-learn to use UMAP exploration.") from exc
    return umap.UMAP(n_components=n_components).fit_transform(features)
