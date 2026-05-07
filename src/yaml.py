"""Small YAML reader/writer for simple mapping configs used in this project."""
from __future__ import annotations

import ast
import json
from typing import Any


def _parse_scalar(text: str) -> Any:
    text = text.strip()
    if text == "":
        return {}
    if text.lower() == "true":
        return True
    if text.lower() == "false":
        return False
    if text.lower() in {"null", "none"}:
        return None
    if (text.startswith('"') and text.endswith('"')) or (
        text.startswith("'") and text.endswith("'")
    ):
        return text[1:-1]
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        try:
            parsed = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return [_parse_scalar(part.strip()) for part in inner.split(",")]
        return parsed
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


def safe_load(text: str) -> dict[str, Any]:
    if not text.strip():
        return {}
    stripped = text.lstrip()
    if stripped.startswith("{"):
        return json.loads(text)
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any, str | None]] = [(-1, root, None)]
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped_line = raw.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if stripped_line.startswith("- "):
            value_text = stripped_line[2:].strip()
            if not isinstance(parent, list):
                container_indent, container_parent, container_key = stack[-1]
                if (
                    isinstance(container_parent, dict)
                    and not container_parent
                    and container_key is not None
                    and len(stack) >= 2
                    and isinstance(stack[-2][1], dict)
                ):
                    parent = []
                    stack[-2][1][container_key] = parent
                    stack[-1] = (container_indent, parent, container_key)
                else:
                    continue
            parent.append(_parse_scalar(value_text))
            continue

        key, sep, value = stripped_line.partition(":")
        if not sep:
            continue
        parsed = _parse_scalar(value)
        if isinstance(parent, dict):
            parent[key] = parsed
            if parsed == {} and value.strip() == "":
                stack.append((indent, parent, key))
                stack.append((indent, parsed, key))
    return root


def safe_dump(data: Any, sort_keys: bool = False, **_: Any) -> str:
    try:
        return _dump_mapping(data, sort_keys=sort_keys)
    except Exception:
        return json.dumps(data, indent=2)


def _dump_mapping(data: Any, indent: int = 0, sort_keys: bool = False) -> str:
    if not isinstance(data, dict):
        return repr(data)
    keys = sorted(data) if sort_keys else list(data)
    lines: list[str] = []
    for key in keys:
        value = data[key]
        prefix = " " * indent + f"{key}:"
        if isinstance(value, dict):
            lines.append(prefix)
            lines.append(_dump_mapping(value, indent + 2, sort_keys))
        else:
            lines.append(prefix + " " + _format_scalar(value))
    return "\n".join(lines) + "\n"


def _format_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    return repr(str(value))
