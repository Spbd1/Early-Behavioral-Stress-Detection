"""Minimal scipy.special shims."""
from __future__ import annotations

import math


def logsumexp(values, axis=None):
    vals = list(values)
    m = max(vals) if vals else 0.0
    return m + math.log(sum(math.exp(v - m) for v in vals)) if vals else float('-inf')


def softmax(values, axis=None):
    vals = list(values)
    m = max(vals) if vals else 0.0
    exps = [math.exp(v - m) for v in vals]
    total = sum(exps) or 1.0
    return [v / total for v in exps]
