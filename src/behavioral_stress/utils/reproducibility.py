"""Utilities for deterministic research runs."""

from __future__ import annotations

import os
import random

import numpy as np


def set_random_seed(seed: int) -> np.random.Generator:
    """Seed common pseudo-random generators and return a NumPy Generator."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    return np.random.default_rng(seed)
