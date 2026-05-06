"""Data lineage and model-version manifests."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ArtifactRecord:
    path: str
    sha256: str
    bytes: int


@dataclass(frozen=True)
class LineageManifest:
    run_id: str
    git_commit: str
    python_version: str
    artifacts: list[ArtifactRecord] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "git_commit": self.git_commit,
            "python_version": self.python_version,
            "artifacts": [artifact.__dict__ for artifact in self.artifacts],
            "metadata": self.metadata,
        }

    def write(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps(self.as_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )


def build_lineage_manifest(
    run_id: str,
    artifact_paths: list[str | Path],
    metadata: dict[str, Any] | None = None,
) -> LineageManifest:
    records = []
    for raw_path in artifact_paths:
        path = Path(raw_path)
        if path.exists() and path.is_file():
            records.append(
                ArtifactRecord(
                    path=str(path),
                    sha256=_sha256(path),
                    bytes=path.stat().st_size,
                )
            )
    return LineageManifest(
        run_id=run_id,
        git_commit=_git_commit(),
        python_version=platform.python_version(),
        artifacts=records,
        metadata=metadata or {},
    )


def model_version_id(manifest: LineageManifest) -> str:
    encoded = json.dumps(manifest.as_dict(), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"
