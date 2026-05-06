#!/usr/bin/env python
"""Run Google Trends ingestion from a YAML config."""
from behavioral_stress.ingestion.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["google-trends", *(__import__("sys").argv[1:])]))
