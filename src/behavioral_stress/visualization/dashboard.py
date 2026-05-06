"""Streamlit dashboard for synthetic research-prototype outputs."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from behavioral_stress.visualization.plots import (
    feature_plot,
    posterior_regime_plot,
    regime_path_plot,
    transition_heatmap,
)

if TYPE_CHECKING:
    import pandas as pd

WARNING = "Experimental research prototype. Not a validated recession predictor. Aggregate-level inference only."
DEFAULT_OUTPUT_DIR = Path("data/synthetic")


def _read_csv(path: Path, **kwargs) -> "pd.DataFrame | None":
    """Read a CSV file when it exists; otherwise return ``None``."""
    import pandas as pd

    return pd.read_csv(path, **kwargs) if path.exists() else None


def _read_time_series(path: Path) -> "pd.DataFrame | None":
    """Read a time-indexed CSV produced by the synthetic workflow."""
    return _read_csv(path, index_col=0, parse_dates=True)


def _most_likely_path_from_posterior(posterior: "pd.DataFrame | None") -> "pd.Series | None":
    """Derive a most-likely regime path when no Viterbi file is available."""
    if posterior is None or posterior.empty:
        return None
    return posterior.idxmax(axis=1).rename("most_likely_regime")


def main() -> None:
    """Render the dashboard from synthetic workflow output files if present."""
    import streamlit as st

    st.set_page_config(page_title="Behavioral Stress Regime Detection", layout="wide")
    st.warning(WARNING)
    st.title("Behavioral Stress Regime Detection — Synthetic Dashboard")
    st.caption("Reads local synthetic outputs when available; no external data is required.")

    output_dir = Path(st.sidebar.text_input("Output directory", str(DEFAULT_OUTPUT_DIR)))
    st.sidebar.caption("Expected CSV files are optional and are loaded from the selected directory.")

    posterior = _read_time_series(output_dir / "posterior.csv")
    observations = _read_time_series(output_dir / "observations.csv")
    viterbi = _read_time_series(output_dir / "viterbi_path.csv")
    transition = _read_csv(output_dir / "transition_matrix.csv", index_col=0)
    metrics = _read_csv(output_dir / "metrics.csv")

    if not output_dir.exists():
        st.info(f"Output directory `{output_dir}` does not exist yet. Run the synthetic workflow or choose another directory.")

    st.header("Regime diagnostics")
    if posterior is not None:
        st.plotly_chart(posterior_regime_plot(posterior), use_container_width=True)
    else:
        st.info("No posterior regime probabilities found at `posterior.csv`.")

    regime_path = viterbi if viterbi is not None else _most_likely_path_from_posterior(posterior)
    if regime_path is not None:
        st.plotly_chart(regime_path_plot(regime_path), use_container_width=True)
    else:
        st.info("No Viterbi path found at `viterbi_path.csv`, and no posterior file is available for a most-likely path.")

    if transition is not None:
        st.plotly_chart(transition_heatmap(transition), use_container_width=True)
    else:
        st.info("No transition matrix found at `transition_matrix.csv`.")

    st.header("Observations and metrics")
    if observations is not None:
        st.plotly_chart(feature_plot(observations), use_container_width=True)
    else:
        st.info("No observations found at `observations.csv`.")

    if metrics is not None:
        st.subheader("Metrics")
        st.dataframe(metrics, use_container_width=True)
    else:
        st.info("No metrics table found at `metrics.csv`.")


if __name__ == "__main__":
    main()
