"""Streamlit dashboard for synthetic research-prototype outputs."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from behavioral_stress.visualization.plots import posterior_regime_plot, transition_heatmap

WARNING = "Experimental research prototype. Not a validated recession predictor. Aggregate-level inference only."


def _read_csv(path: Path, **kwargs):
    return pd.read_csv(path, **kwargs) if path.exists() else None


def main() -> None:
    """Render the dashboard from files produced by the synthetic demo."""
    st.set_page_config(page_title="Behavioral Stress Regime Detection", layout="wide")
    st.warning(WARNING)
    st.title("Behavioral Stress Regime Detection — Synthetic Demo")
    out_dir = Path(st.sidebar.text_input("Output directory", "data/synthetic"))
    posterior = _read_csv(out_dir / "posterior.csv", index_col=0, parse_dates=True)
    observations = _read_csv(out_dir / "observations.csv", index_col=0, parse_dates=True)
    latent = _read_csv(out_dir / "latent_states.csv", index_col=0, parse_dates=True)
    viterbi = _read_csv(out_dir / "viterbi_path.csv", index_col=0, parse_dates=True)
    transition = _read_csv(out_dir / "transition_matrix.csv", index_col=0)
    metrics = _read_csv(out_dir / "metrics.csv", index_col=0)

    if posterior is not None:
        st.plotly_chart(posterior_regime_plot(posterior), use_container_width=True)
    if viterbi is not None:
        st.plotly_chart(px.line(viterbi, title="Viterbi / most likely synthetic regime path"), use_container_width=True)
    if latent is not None:
        st.plotly_chart(px.line(latent, title="Synthetic latent truth (available only for default demo)"), use_container_width=True)
    if observations is not None:
        st.plotly_chart(px.line(observations.iloc[:, : min(6, observations.shape[1])], title="Observations by ontology-coded aggregate signals"), use_container_width=True)
    if transition is not None:
        st.plotly_chart(transition_heatmap(transition), use_container_width=True)
    if metrics is not None:
        st.subheader("Validation metrics")
        st.dataframe(metrics)
    st.info("Signal drift / KL diagnostics can be added from validation outputs when available.")


if __name__ == "__main__":
    main()
