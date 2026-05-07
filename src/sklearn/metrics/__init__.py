"""Minimal metrics shims."""

from __future__ import annotations


def precision_score(y_true, y_pred, zero_division=0):
    return 0.0


def recall_score(y_true, y_pred, zero_division=0):
    return 0.0


def brier_score_loss(y_true, y_score):
    return 0.0


def roc_auc_score(y_true, y_score):
    return 0.5


def average_precision_score(y_true, y_score):
    return 0.0
