"""Plotly figures for synthetic latent-regime outputs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd


def posterior_regime_plot(posterior: pd.DataFrame) -> Any:
    """Plot posterior regime probabilities over time."""
    import plotly.express as px

    figure = px.line(
        posterior,
        title="Posterior regime probabilities over time",
        labels={"index": "time", "value": "probability", "variable": "regime"},
    )
    figure.update_yaxes(range=[0, 1], title="probability")
    figure.update_xaxes(title="time")
    return figure


def regime_path_plot(path: pd.Series | pd.DataFrame) -> Any:
    """Plot a Viterbi or most-likely regime path over time."""
    import pandas as pd

    import plotly.express as px

    if isinstance(path, pd.DataFrame):
        values = path.iloc[:, 0] if not path.empty else pd.Series(dtype=float)
    else:
        values = path

    figure = px.line(
        values.rename("regime"),
        title="Viterbi / most likely regime path",
        labels={"index": "time", "value": "regime"},
    )
    figure.update_traces(mode="lines+markers", line_shape="hv")
    figure.update_xaxes(title="time")
    figure.update_yaxes(title="regime")
    return figure


def transition_heatmap(transition: pd.DataFrame) -> Any:
    """Plot transition matrix heatmap."""
    import plotly.graph_objects as go

    figure = go.Figure(
        data=go.Heatmap(
            z=transition.to_numpy(),
            x=list(transition.columns),
            y=list(transition.index),
            colorscale="Blues",
            colorbar={"title": "probability"},
            text=transition.round(3).astype(str).to_numpy(),
            texttemplate="%{text}",
            hovertemplate="from %{y}<br>to %{x}<br>p=%{z:.3f}<extra></extra>",
        )
    )
    figure.update_layout(
        title="Transition matrix heatmap", xaxis_title="to regime", yaxis_title="from regime"
    )
    return figure


def feature_plot(observations: pd.DataFrame, max_features: int = 6) -> Any:
    """Plot a small set of aggregate observation features over time."""
    import plotly.express as px

    selected = observations.iloc[:, : min(max_features, observations.shape[1])]
    figure = px.line(
        selected,
        title="Basic aggregate feature plot",
        labels={"index": "time", "value": "value", "variable": "feature"},
    )
    figure.update_xaxes(title="time")
    figure.update_yaxes(title="value")
    return figure
