from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ai_agents_hw6.domain import Coordinate, GameAction, GridSize, Role


@dataclass(frozen=True)
class PolicyInput:
    """Role-scoped decision input for policies.

    This is intentionally smaller than authoritative GameState. Phase 6 will replace the
    current adapter with the formal partial-observation DTO while preserving this shape.
    """

    role: Role
    self_position: Coordinate
    visible_opponent: Coordinate | None
    visible_barriers: frozenset[Coordinate]
    grid: GridSize
    legal_actions: tuple[GameAction, ...]
    move_round: int
    seed: int


class Policy(Protocol):
    def choose_action(self, policy_input: PolicyInput) -> GameAction:
        """Return one typed action from the legal action vocabulary."""
