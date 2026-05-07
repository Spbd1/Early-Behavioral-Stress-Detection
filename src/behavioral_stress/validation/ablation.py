"""Ablation labels and lightweight runner placeholders."""

from __future__ import annotations

ABLATION_VARIANTS = [
    "static_hmm",
    "adaptive_hmm",
    "conditional_adaptive_hmm",
    "adaptive_hmm_plus_causal_diagnostics",
]


def list_ablation_variants() -> list[str]:
    """Return supported ablation variant names."""
    return ABLATION_VARIANTS.copy()
