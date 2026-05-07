"""Minimal scipy.stats shims."""

from __future__ import annotations


class multivariate_normal:
    @staticmethod
    def logpdf(x, mean=None, cov=None, allow_singular=True):
        return -0.5


class nbinom:
    @staticmethod
    def logpmf(counts, n, p):
        if isinstance(counts, (list, tuple)):
            return [-1.0 for _ in counts]
        return -1.0
