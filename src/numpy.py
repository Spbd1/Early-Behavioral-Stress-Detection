"""Tiny NumPy compatibility shim for the repository's dependency-free checks."""
from __future__ import annotations

import math
import random as _random
from typing import Iterable, Any

from behavioral_stress.simple_frame import Matrix, Vector

ndarray = Matrix


def array(values: Iterable[Any]) -> Vector | Matrix:
    values = list(values)
    if values and isinstance(values[0], (list, tuple, Vector)):
        return Matrix([list(row) for row in values])
    return Vector(values)


def zeros(size: int | tuple[int, int]) -> Vector | Matrix:
    if isinstance(size, tuple):
        rows, cols = size
        return Matrix([[0.0 for _ in range(cols)] for _ in range(rows)])
    return Vector([0.0 for _ in range(size)])


def allclose(left: Any, right: Any, atol: float = 1e-8) -> bool:
    def flatten(value: Any):
        if isinstance(value, (list, tuple, Vector, Matrix)):
            for item in value:
                yield from flatten(item)
        else:
            yield value
    left_values = list(flatten(left))
    right_values = list(flatten(right))
    if len(right_values) == 1 and len(left_values) > 1:
        right_values *= len(left_values)
    if len(left_values) != len(right_values):
        return False
    return builtins_all(abs(float(a) - float(b)) <= atol for a, b in zip(left_values, right_values))


def isfinite(value: Any) -> bool | Vector:
    if isinstance(value, (list, tuple, Vector)):
        return Vector([math.isfinite(float(item)) for item in value])
    return math.isfinite(float(value))


def all(values: Iterable[Any]) -> bool:
    return builtins_all(values)


builtins_all = __builtins__["all"] if isinstance(__builtins__, dict) else __builtins__.all


class _Generator:
    def __init__(self, seed: int | None = None) -> None:
        self._rng = _random.Random(seed)

    def normal(self, loc: float = 0.0, scale: float = 1.0, size: int | None = None) -> float | Vector:
        if size is None:
            return self._rng.gauss(loc, scale)
        return Vector([self._rng.gauss(loc, scale) for _ in range(size)])


class _RandomModule:
    def default_rng(self, seed: int | None = None) -> _Generator:
        return _Generator(seed)


random = _RandomModule()
