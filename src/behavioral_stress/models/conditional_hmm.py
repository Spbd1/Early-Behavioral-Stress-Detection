"""Prototype conditional adaptive HMM with covariate-dependent transitions."""
from __future__ import annotations

import numpy as np
from scipy.special import softmax

from behavioral_stress.models.adaptive_hmm import AdaptiveHMM


class ConditionalAdaptiveHMM(AdaptiveHMM):
    """Clarity-first prototype for covariate-dependent transitions and emissions."""

    def __init__(self, n_states: int, n_covariates: int, **kwargs: object) -> None:
        super().__init__(n_states=n_states, **kwargs)
        self.n_covariates = n_covariates
        self.transition_betas_ = np.zeros((n_states, n_states, n_covariates))
        self.emission_gammas_: np.ndarray | None = None

    def transition_matrix_for_covariate(self, covariate: np.ndarray) -> np.ndarray:
        """Compute row-wise softmax transition probabilities for one covariate vector."""
        logits = np.tensordot(self.transition_betas_, covariate, axes=([2], [0]))
        return softmax(logits, axis=1)

    def adjusted_means(self, covariate: np.ndarray) -> np.ndarray:
        """Return mu_i + Gamma_i X_t if emission gammas are available."""
        if self.means_ is None:
            raise RuntimeError("Model must be fitted before adjusted means are available.")
        if self.emission_gammas_ is None:
            return self.means_
        return self.means_ + np.einsum("skf,k->sf", self.emission_gammas_, covariate)
