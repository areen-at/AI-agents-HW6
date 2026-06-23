from __future__ import annotations

from dataclasses import dataclass

from ai_agents_hw6.domain.enums import Direction
from ai_agents_hw6.domain.errors import DomainError


@dataclass(frozen=True, order=True)
class Coordinate:
    """Zero-based board coordinate stored as [row, column]."""

    row: int
    column: int

    def __post_init__(self) -> None:
        if isinstance(self.row, bool) or not isinstance(self.row, int):
            raise DomainError("coordinate.row must be an integer")
        if isinstance(self.column, bool) or not isinstance(self.column, int):
            raise DomainError("coordinate.column must be an integer")
        if self.row < 0:
            raise DomainError("coordinate.row must be non-negative")
        if self.column < 0:
            raise DomainError("coordinate.column must be non-negative")

    def to_json(self) -> list[int]:
        return [self.row, self.column]

    @classmethod
    def from_json(cls, value: object) -> "Coordinate":
        if (
            not isinstance(value, list)
            or len(value) != 2
            or any(isinstance(item, bool) or not isinstance(item, int) for item in value)
        ):
            raise DomainError("coordinate JSON value must be [row, column]")
        return cls(row=value[0], column=value[1])

    def moved(self, direction: Direction) -> "Coordinate":
        delta = direction_delta(direction)
        return Coordinate(row=self.row + delta[0], column=self.column + delta[1])


@dataclass(frozen=True)
class GridSize:
    rows: int
    columns: int

    def __post_init__(self) -> None:
        if isinstance(self.rows, bool) or not isinstance(self.rows, int):
            raise DomainError("grid.rows must be an integer")
        if isinstance(self.columns, bool) or not isinstance(self.columns, int):
            raise DomainError("grid.columns must be an integer")
        if self.rows < 2 or self.columns < 2:
            raise DomainError("grid size must be at least 2 by 2")

    def contains(self, coordinate: Coordinate) -> bool:
        return 0 <= coordinate.row < self.rows and 0 <= coordinate.column < self.columns

    def all_coordinates(self) -> tuple[Coordinate, ...]:
        return tuple(
            Coordinate(row=row, column=column)
            for row in range(self.rows)
            for column in range(self.columns)
        )

    def bounded_neighbors(self, coordinate: Coordinate) -> tuple[Coordinate, ...]:
        if not self.contains(coordinate):
            raise DomainError("cannot generate neighbors for an out-of-bounds coordinate")
        neighbors: list[Coordinate] = []
        for direction in Direction:
            row_delta, column_delta = direction_delta(direction)
            row = coordinate.row + row_delta
            column = coordinate.column + column_delta
            if 0 <= row < self.rows and 0 <= column < self.columns:
                neighbors.append(Coordinate(row=row, column=column))
        return tuple(neighbors)

    def to_json(self) -> list[int]:
        return [self.rows, self.columns]

    @classmethod
    def from_json(cls, value: object) -> "GridSize":
        if (
            not isinstance(value, list)
            or len(value) != 2
            or any(isinstance(item, bool) or not isinstance(item, int) for item in value)
        ):
            raise DomainError("grid size JSON value must be [rows, columns]")
        return cls(rows=value[0], columns=value[1])


def direction_delta(direction: Direction) -> tuple[int, int]:
    if direction is Direction.UP:
        return (-1, 0)
    if direction is Direction.DOWN:
        return (1, 0)
    if direction is Direction.LEFT:
        return (0, -1)
    if direction is Direction.RIGHT:
        return (0, 1)
    raise DomainError(f"unsupported direction: {direction!r}")
