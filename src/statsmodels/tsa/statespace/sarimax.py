"""Minimal SARIMAX shim."""
from __future__ import annotations


class SARIMAX:
    def __init__(self, y, *args, **kwargs) -> None:
        self.y = list(y)

    def fit(self, disp=False):
        return self

    def forecast(self, steps=1):
        value = self.y[-1] if self.y else 0.0
        return [value for _ in range(steps)]
