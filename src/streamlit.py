"""Minimal streamlit shim so dashboard module imports offline."""
from __future__ import annotations


def set_page_config(**kwargs):
    return None


def warning(message):
    print(message)


def title(message):
    print(message)


def plotly_chart(*args, **kwargs):
    return None


def subheader(message):
    print(message)


def dataframe(data):
    return data


def info(message):
    print(message)


class _Sidebar:
    def text_input(self, label, value=""):
        return value


sidebar = _Sidebar()
