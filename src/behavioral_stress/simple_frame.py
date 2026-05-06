"""Small tabular containers used by the dependency-free demo path."""
from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any, Iterable, Iterator


class Vector(list):
    """List subclass with a few NumPy-like conveniences used in tests."""

    @property
    def values(self) -> "Vector":
        return self

    def mean(self) -> float:
        return sum(float(x) for x in self) / len(self) if self else 0.0

    def std(self) -> float:
        if len(self) < 2:
            return 1.0
        mu = self.mean()
        var = sum((float(x) - mu) ** 2 for x in self) / len(self)
        return math.sqrt(var) or 1.0

    def sum(self, axis: int | None = None) -> float:
        if axis is not None:
            raise ValueError("Vector.sum only supports axis=None")
        return sum(float(x) for x in self)

    def __gt__(self, other: float) -> "Vector":
        return Vector([x > other for x in self])

    def __ge__(self, other: float) -> "Vector":
        return Vector([x >= other for x in self])

    def __lt__(self, other: float) -> "Vector":
        return Vector([x < other for x in self])

    def __le__(self, other: float) -> "Vector":
        return Vector([x <= other for x in self])


class Matrix(list):
    """List-of-lists container with row/column aggregation helpers."""

    @property
    def shape(self) -> tuple[int, int]:
        return (len(self), len(self[0]) if self else 0)

    def sum(self, axis: int | None = None) -> Vector | float:
        if axis is None:
            return sum(sum(float(value) for value in row) for row in self)
        if axis == 1:
            return Vector([sum(float(value) for value in row) for row in self])
        if axis == 0:
            cols = self.shape[1]
            return Vector([sum(float(row[col]) for row in self) for col in range(cols)])
        raise ValueError("axis must be None, 0, or 1")


class Series:
    """Minimal one-dimensional labeled data container."""

    def __init__(self, data: Iterable[Any], index: Iterable[Any] | None = None, name: str | None = None) -> None:
        self.data = Vector(list(data))
        self.index = list(index) if index is not None else list(range(len(self.data)))
        self.name = name or "value"

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self) -> Iterator[Any]:
        return iter(self.data)

    def __getitem__(self, item: int | slice) -> Any:
        return self.data[item]

    @property
    def values(self) -> Vector:
        return self.data

    def to_csv(self, path: str | Path, index: bool = True) -> None:
        with Path(path).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow((["index"] if index else []) + [self.name])
            for idx, value in zip(self.index, self.data):
                writer.writerow(([idx] if index else []) + [value])


class DataFrame:
    """Minimal table with enough behavior for demos, validation, and tests."""

    def __init__(
        self,
        data: Iterable[Iterable[Any]] | Iterable[dict[str, Any]],
        columns: Iterable[str] | None = None,
        index: Iterable[Any] | None = None,
    ) -> None:
        rows = list(data)
        if rows and isinstance(rows[0], dict):
            dict_rows = [dict(row) for row in rows]  # type: ignore[arg-type]
            cols = list(columns) if columns is not None else list(dict_rows[0].keys())
            self.rows = [[row.get(col, "") for col in cols] for row in dict_rows]
            self.columns = cols
        else:
            self.rows = [list(row) for row in rows]  # type: ignore[arg-type]
            width = len(self.rows[0]) if self.rows else 0
            self.columns = list(columns) if columns is not None else [f"col_{i}" for i in range(width)]
        self.index = list(index) if index is not None else list(range(len(self.rows)))

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, column: str) -> Vector:
        pos = self.columns.index(column)
        return Vector([row[pos] for row in self.rows])

    @property
    def shape(self) -> tuple[int, int]:
        return (len(self.rows), len(self.columns))

    @property
    def values(self) -> Matrix:
        return Matrix([list(row) for row in self.rows])

    def to_csv(self, path: str | Path, index: bool = True) -> None:
        with Path(path).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow((["index"] if index else []) + list(self.columns))
            for idx, row in zip(self.index, self.rows):
                writer.writerow(([idx] if index else []) + row)

    @classmethod
    def from_columns(cls, columns: dict[str, Iterable[Any]], index: Iterable[Any] | None = None) -> "DataFrame":
        names = list(columns)
        values = [list(columns[name]) for name in names]
        rows = [list(row) for row in zip(*values)] if values else []
        return cls(rows, columns=names, index=index)
