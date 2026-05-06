"""Langflow report/output wrapper using the pure-Python fallback runner."""
from __future__ import annotations

from behavioral_stress.workflows.synthetic_workflow import run_synthetic_workflow


class ReportComponent:
    """Generate output files and dashboard launch instructions."""

    display_name = "Report / Output Files"

    def run(self, config_path: str = "configs/synthetic.yaml") -> dict:
        result = run_synthetic_workflow(config_path)
        result["dashboard"] = "streamlit run src/behavioral_stress/visualization/dashboard.py"
        return result
