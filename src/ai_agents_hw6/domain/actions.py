from __future__ import annotations

from dataclasses import dataclass

from ai_agents_hw6.domain.enums import ActionType, Direction
from ai_agents_hw6.domain.errors import DomainError
from ai_agents_hw6.domain.geometry import Coordinate


@dataclass(frozen=True)
class MoveAction:
    direction: Direction
    type: ActionType = ActionType.MOVE

    def __post_init__(self) -> None:
        if not isinstance(self.direction, Direction):
            raise DomainError("move action direction must be a Direction")


@dataclass(frozen=True)
class PlaceBarrierAction:
    target: Coordinate
    type: ActionType = ActionType.PLACE_BARRIER

    def __post_init__(self) -> None:
        if not isinstance(self.target, Coordinate):
            raise DomainError("barrier target must be a Coordinate")


GameAction = MoveAction | PlaceBarrierAction
