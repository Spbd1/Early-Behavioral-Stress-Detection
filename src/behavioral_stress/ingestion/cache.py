"""Small filesystem cache used by ingestion connectors."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class CacheEntry:
    """Cached DataFrame and metadata."""

    frame: pd.DataFrame
    metadata: dict[str, Any]


class FileCache:
    """Content-addressed DataFrame cache with optional TTL invalidation."""

    def __init__(self, directory: str | Path, ttl_seconds: int | None = None, enabled: bool = True):
        self.directory = Path(directory)
        self.ttl_seconds = ttl_seconds
        self.enabled = enabled
        self.directory.mkdir(parents=True, exist_ok=True)

    def key_for(self, payload: dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def get(self, key: str) -> CacheEntry | None:
        if not self.enabled:
            return None
        data_path = self.directory / f"{key}.csv"
        meta_path = self.directory / f"{key}.json"
        if not data_path.exists() or not meta_path.exists():
            return None
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        created_at = float(metadata.get("created_at_epoch", 0))
        if self.ttl_seconds is not None and time.time() - created_at > self.ttl_seconds:
            return None
        frame = pd.read_csv(data_path, index_col=0, parse_dates=True)
        return CacheEntry(frame=frame, metadata=metadata)

    def set(self, key: str, frame: pd.DataFrame, metadata: dict[str, Any]) -> None:
        if not self.enabled:
            return
        payload = {**metadata, "created_at_epoch": time.time()}
        frame.to_csv(self.directory / f"{key}.csv")
        (self.directory / f"{key}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
        )
