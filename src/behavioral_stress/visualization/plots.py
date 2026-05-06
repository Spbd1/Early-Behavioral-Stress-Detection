"""Plotly visualization helpers."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def posterior_probability_figure(index: pd.Index, posterior: np.ndarray) -> go.Figure:
    """Create a line plot of posterior regime probabilities over time."""
    frame = pd.DataFrame(posterior, index=index, columns=[f"regime_{i}" for i in range(posterior.shape[1])])
    return px.line(frame, x=frame.index, y=frame.columns, labels={"value": "Posterior probability", "index": "Time"})


def transition_heatmap(matrix: np.ndarray) -> go.Figure:
    """Create a transition-matrix heatmap."""
    return px.imshow(matrix, text_auto=True, labels={"x": "To state", "y": "From state", "color": "Probability"})
