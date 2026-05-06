"""Dimensionality-reduction helpers for aggregate traces."""
from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA


def run_pca(x: np.ndarray, n_components: int = 2) -> dict[str, np.ndarray]:
    """Run PCA and return transformed values plus explained variance ratios."""
    model = PCA(n_components=n_components)
    transformed = model.fit_transform(x)
    return {"transformed": transformed, "explained_variance_ratio": model.explained_variance_ratio_}


def run_umap_if_available(x: np.ndarray, n_components: int = 2, random_state: int = 42) -> dict[str, np.ndarray | str]:
    """Run UMAP when installed; otherwise return an explanatory warning."""
    import importlib

    spec = importlib.util.find_spec("umap")
    if spec is None:
        return {"warning": "umap-learn is not installed; install .[advanced] to enable UMAP."}
    umap = importlib.import_module("umap")
    reducer = umap.UMAP(n_components=n_components, random_state=random_state)
    return {"transformed": reducer.fit_transform(x)}
