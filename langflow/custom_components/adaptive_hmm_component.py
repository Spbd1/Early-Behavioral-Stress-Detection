"""Langflow custom component scaffold for AdaptiveHMM filtering."""
from behavioral_stress.models.adaptive_hmm import AdaptiveHMM


def build_adaptive_hmm(n_states: int = 3) -> AdaptiveHMM:
    """Return an unfitted AdaptiveHMM for use inside a Langflow experiment."""
    return AdaptiveHMM(n_states=n_states)
