"""Minimal plotly.express shims."""
from __future__ import annotations


def line(data, title=""):
    return {"type": "line", "title": title, "data": data}


def imshow(data, text_auto=True, title=""):
    return {"type": "heatmap", "title": title, "data": data}
