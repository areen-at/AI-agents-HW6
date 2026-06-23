"""Pure domain model for the Cop-and-Thief game."""

from ai_agents_hw6.domain.actions import GameAction, MoveAction, PlaceBarrierAction
from ai_agents_hw6.domain.enums import (
    ActionType,
    Direction,
    Role,
    TechnicalFailureReason,
    TerminalOutcome,
    TerminalReason,
)
from ai_agents_hw6.domain.errors import DomainError
from ai_agents_hw6.domain.geometry import Coordinate, GridSize, direction_delta
from ai_agents_hw6.domain.identifiers import AttemptId, RequestId, SeriesId, SubGameId
from ai_agents_hw6.domain.initialization import create_initial_state
from ai_agents_hw6.domain.rules import apply_action, legal_actions, legal_barrier_actions, legal_move_actions, replay_actions
from ai_agents_hw6.domain.scoring import ScoreMatrix, ScoreResult, score_state
from ai_agents_hw6.domain.state import GameState

__all__ = [
    "ActionType",
    "AttemptId",
    "Coordinate",
    "Direction",
    "DomainError",
    "GameState",
    "GameAction",
    "GridSize",
    "MoveAction",
    "PlaceBarrierAction",
    "RequestId",
    "Role",
    "ScoreMatrix",
    "ScoreResult",
    "SeriesId",
    "SubGameId",
    "TechnicalFailureReason",
    "TerminalOutcome",
    "TerminalReason",
    "apply_action",
    "create_initial_state",
    "direction_delta",
    "legal_actions",
    "legal_barrier_actions",
    "legal_move_actions",
    "replay_actions",
    "score_state",
]
