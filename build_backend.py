"""Minimal PEP 517/660 backend for offline editable installs in this kata."""
from __future__ import annotations

import base64
import csv
import hashlib
from pathlib import Path
import zipfile

NAME = "behavioral_stress_regime_detection"
VERSION = "0.1.0"
DIST_INFO = f"{NAME}-{VERSION}.dist-info"


def build_wheel(wheel_directory: str, config_settings=None, metadata_directory: str | None = None) -> str:
    return _write_wheel(Path(wheel_directory), editable=False)


def build_editable(wheel_directory: str, config_settings=None, metadata_directory: str | None = None) -> str:
    return _write_wheel(Path(wheel_directory), editable=True)


def prepare_metadata_for_build_wheel(metadata_directory: str, config_settings=None) -> str:
    return _write_metadata(Path(metadata_directory))


def prepare_metadata_for_build_editable(metadata_directory: str, config_settings=None) -> str:
    return _write_metadata(Path(metadata_directory))


def get_requires_for_build_wheel(config_settings=None) -> list[str]:
    return []


def get_requires_for_build_editable(config_settings=None) -> list[str]:
    return []


def _write_metadata(directory: Path) -> str:
    dist = directory / DIST_INFO
    dist.mkdir(parents=True, exist_ok=True)
    (dist / "METADATA").write_text(_metadata(), encoding="utf-8")
    (dist / "WHEEL").write_text(_wheel_metadata(), encoding="utf-8")
    return DIST_INFO


def _write_wheel(directory: Path, editable: bool) -> str:
    directory.mkdir(parents=True, exist_ok=True)
    tag = "py3-none-any"
    filename = f"{NAME}-{VERSION}-{tag}.whl"
    wheel_path = directory / filename
    records: list[tuple[str, bytes]] = []

    def add_file(archive: zipfile.ZipFile, name: str, content: str | bytes) -> None:
        data = content.encode("utf-8") if isinstance(content, str) else content
        archive.writestr(name, data)
        records.append((name, data))

    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        if editable:
            add_file(archive, "behavioral_stress_src.pth", str(Path.cwd() / "src"))
        else:
            for path in Path("src").rglob("*.py"):
                add_file(archive, str(path.relative_to("src")), path.read_bytes())
        add_file(archive, f"{DIST_INFO}/METADATA", _metadata())
        add_file(archive, f"{DIST_INFO}/WHEEL", _wheel_metadata())
        record_name = f"{DIST_INFO}/RECORD"
        output = []
        for name, data in records:
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode("ascii")
            output.append([name, f"sha256={digest}", str(len(data))])
        output.append([record_name, "", ""])
        lines = []
        for row in output:
            pseudo = csv.StringIO()
            csv.writer(pseudo, lineterminator="").writerow(row)
            lines.append(pseudo.getvalue())
        archive.writestr(record_name, "\n".join(lines) + "\n")
    return filename


def _metadata() -> str:
    return "\n".join(
        [
            "Metadata-Version: 2.1",
            "Name: behavioral-stress-regime-detection",
            f"Version: {VERSION}",
            "Summary: Research prototype for latent behavioral stress regime detection.",
            "Requires-Python: >=3.10",
            "",
        ]
    )


def _wheel_metadata() -> str:
    return "\n".join(
        [
            "Wheel-Version: 1.0",
            "Generator: behavioral-stress-build-backend",
            "Root-Is-Purelib: true",
            "Tag: py3-none-any",
            "",
        ]
    )
