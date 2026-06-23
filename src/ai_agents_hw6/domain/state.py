from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from ai_agents_hw6.domain.enums import Role, TerminalOutcome, TerminalReason
from ai_agents_hw6.domain.errors import DomainError
from ai_agents_hw6.domain.geometry import Coordinate, GridSize
from ai_agents_hw6.domain.identifiers import AttemptId, SeriesId, SubGameId


@dataclass(frozen=True)
class GameState:
    """Authoritative immutable state snapshot for one game attempt."""

    series_id: SeriesId
    sub_game_id: SubGameId
    attempt_id: AttemptId
    grid: GridSize
    cop_position: Coordinate
    thief_position: Coordinate
    active_role: Role
    seed: int
    move_round: int = 0
    barriers: Iterable[Coordinate] = field(default_factory=frozenset)
    barriers_placed: int = 0
    terminal_outcome: TerminalOutcome | None = None
    terminal_reason: TerminalReason | None = None

    def __post_init__(self) -> None:
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise DomainError("seed must be an integer")
        if isinstance(self.move_round, bool) or not isinstance(self.move_round, int):
            raise DomainError("move_round must be an integer")
        if self.move_round < 0:
            raise DomainError("move_round must be non-negative")
        if isinstance(self.barriers_placed, bool) or not isinstance(self.barriers_placed, int):
            raise DomainError("barriers_placed must be an integer")
        if self.barriers_placed < 0:
            raise DomainError("barriers_placed must be non-negative")
        if not isinstance(self.active_role, Role):
            raise DomainError("active_role must be a Role")

        barrier_items = tuple(self.barriers)
        normalized_barriers = frozenset(barrier_items)
        if len(normalized_barriers) != len(barrier_items):
            raise DomainError("barriers must be unique")
        object.__setattr__(self, "barriers", normalized_barriers)

        self._validate_positions()
        self._validate_barriers()
        self._validate_terminal_metadata()

    @property
    def is_terminal(self) -> bool:
        return self.terminal_outcome is not None

    def _validate_positions(self) -> None:
        if not self.grid.contains(self.cop_position):
            raise DomainError("cop_position must be inside the grid")
        if not self.grid.contains(self.thief_position):
            raise DomainError("thief_position must be inside the grid")

    def _validate_barriers(self) -> None:
        for barrier in self.barriers:
            if not isinstance(barrier, Coordinate):
                raise DomainError("every barrier must be a Coordinate")
            if not self.grid.contains(barrier):
                raise DomainError("barriers must be inside the grid")
            if barrier == self.cop_position:
                raise DomainError("barrier cannot overlap the Cop")
            if barrier == self.thief_position:
                raise DomainError("barrier cannot overlap the Thief")
        if self.barriers_placed < len(self.barriers):
            raise DomainError("barriers_placed cannot be less than current barriers")

    def _validate_terminal_metadata(self) -> None:
        has_outcome = self.terminal_outcome is not None
        has_reason = self.terminal_reason is not None
        if has_outcome != has_reason:
            raise DomainError("terminal_outcome and terminal_reason must be set together")
        if self.terminal_outcome is not None and not isinstance(
            self.terminal_outcome,
            TerminalOutcome,
        ):
            raise DomainError("terminal_outcome must be a TerminalOutcome")
        if self.terminal_reason is not None and not isinstance(
            self.terminal_reason,
            TerminalReason,
        ):
            raise DomainError("terminal_reason must be a TerminalReason")
