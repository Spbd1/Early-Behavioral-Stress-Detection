"""Command-line interface for ingestion pipelines."""
from __future__ import annotations

import argparse
import json
import logging

from behavioral_stress.ingestion.config import load_ingestion_config
from behavioral_stress.ingestion.logging import configure_structured_logging
from behavioral_stress.ingestion.trends import GoogleTrendsIngestionPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Behavioral stress data ingestion commands")
    subparsers = parser.add_subparsers(dest="command", required=True)
    trends = subparsers.add_parser(
        "google-trends", help="Ingest Google Trends interest-over-time data"
    )
    trends.add_argument(
        "--config", required=True, help="Path to a Google Trends ingestion YAML config"
    )
    trends.add_argument("--log-level", default="INFO", help="Python logging level")
    trends.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Use the deterministic offline mock Google Trends client and write artifacts "
            "without network access"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_structured_logging(getattr(logging, args.log_level.upper()))
    if args.command == "google-trends":
        config = load_ingestion_config(args.config)
        if args.dry_run:
            config = config.__class__(**{**config.__dict__, "dry_run": True})
        outputs = GoogleTrendsIngestionPipeline(config).run()
        print(json.dumps(outputs, indent=2, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
