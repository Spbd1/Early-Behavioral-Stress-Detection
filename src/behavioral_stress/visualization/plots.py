"""Plotly figures for synthetic latent-regime outputs."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def posterior_regime_plot(posterior: pd.DataFrame) -> go.Figure:
    """Plot posterior regime probabilities over time."""
    return px.line(posterior, title="Posterior latent-regime probabilities")


def transition_heatmap(transition: pd.DataFrame) -> go.Figure:
    """Plot transition matrix heatmap."""
    return px.imshow(transition, text_auto=True, title="Estimated transition matrix")
