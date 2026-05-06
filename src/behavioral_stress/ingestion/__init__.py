"""Reusable ingestion interfaces and Google Trends connector."""
from behavioral_stress.ingestion.config import GoogleTrendsIngestionConfig, load_ingestion_config
from behavioral_stress.ingestion.trends import GoogleTrendsIngestionPipeline

__all__ = [
    "GoogleTrendsIngestionConfig",
    "GoogleTrendsIngestionPipeline",
    "load_ingestion_config",
]
