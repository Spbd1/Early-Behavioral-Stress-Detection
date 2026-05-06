"""Streamlit dashboard for research outputs."""
from __future__ import annotations

import streamlit as st

BANNER = "Experimental research prototype. Not a validated recession predictor. Aggregate-level inference only."


def run_dashboard() -> None:
    """Launch a minimal dashboard shell."""
    st.set_page_config(page_title="Behavioral Stress Regime Detection", layout="wide")
    st.warning(BANNER)
    st.title("Behavioral Stress Regime Detection")
    st.write("Use the synthetic demo or validation scripts to generate artifacts for inspection.")
    st.info("This dashboard is for reproducible research, interpretation, and diagnostics only.")
