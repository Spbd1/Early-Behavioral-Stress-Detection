"""Langflow report/output wrapper for the package synthetic workflow."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from behavioral_stress.workflows.synthetic_workflow import WORKFLOW_WARNING, run_synthetic_workflow


class ReportComponent:
    """Wrap report output metadata and the pure-Python fallback runner."""

    display_name = "Report / Output Files"
    description = "Adds reporting guidance, or runs the package fallback workflow if requested."

    def run(
        self,
        payload: dict[str, Any] | str | Path | None = None,
        *,
        run_fallback: bool = False,
    ) -> dict[str, Any]:
        """Return report metadata, optionally delegating to ``run_synthetic_workflow``."""
        if run_fallback or not isinstance(payload, dict):
            config_path = payload if isinstance(payload, (str, Path)) else "configs/synthetic.yaml"
            result = run_synthetic_workflow(config_path)
        else:
            result = dict(payload)
        result["warning"] = WORKFLOW_WARNING
        result["dashboard_command"] = "streamlit run src/behavioral_stress/visualization/dashboard.py"
        result["fallback_command"] = "python scripts/run_synthetic_demo.py --config configs/synthetic.yaml"
        return result
