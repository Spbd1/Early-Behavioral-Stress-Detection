#!/usr/bin/env python
"""Print instructions for launching the Streamlit dashboard."""
from __future__ import annotations

from pathlib import Path

import typer

from behavioral_stress.utils.config import load_config

app = typer.Typer(add_completion=False)


@app.command()
def main(config: Path = typer.Option(Path("configs/default.yaml"), "--config")) -> None:
    """Validate dashboard config and show the Streamlit command."""
    load_config(config)
    typer.echo("Run: streamlit run src/behavioral_stress/visualization/dashboard.py")


if __name__ == "__main__":
    app()
