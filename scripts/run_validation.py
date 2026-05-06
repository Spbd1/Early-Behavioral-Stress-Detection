#!/usr/bin/env python
"""Run lightweight validation workflow."""
from __future__ import annotations

from pathlib import Path

import typer

from behavioral_stress.utils.config import load_config

app = typer.Typer(add_completion=False)


@app.command()
def main(config: Path = typer.Option(Path("configs/validation.yaml"), "--config")) -> None:
    """Load validation config and report available validation scaffolding."""
    cfg = load_config(config)
    typer.echo("Validation configuration loaded.")
    typer.echo(cfg.get("validation", {}))


if __name__ == "__main__":
    app()
