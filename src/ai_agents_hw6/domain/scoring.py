from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_agents_hw6.domain.enums import TerminalOutcome
from ai_agents_hw6.domain.errors import DomainError
from ai_agents_hw6.domain.state import GameState


@dataclass(frozen=True)
class ScoreResult:
    cop: int
    thief: int


@dataclass(frozen=True)
class ScoreMatrix:
    cop_win: int = 20
    thief_win: int = 10
    cop_loss: int = 5
    thief_loss: int = 5

    def __post_init__(self) -> None:
        for field_name in ("cop_win", "thief_win", "cop_loss", "thief_loss"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise DomainError(f"{field_name} score must be an integer")
            if value < 0:
                raise DomainError(f"{field_name} score must be non-negative")

    @classmethod
    def from_config(cls, config: Any) -> "ScoreMatrix":
        """Create a score matrix from the Phase 1 config scoring object."""

        return cls(
            cop_win=config.cop_win,
            thief_win=config.thief_win,
            cop_loss=config.cop_loss,
            thief_loss=config.thief_loss,
        )

    def score(self, outcome: TerminalOutcome) -> ScoreResult:
        if outcome is TerminalOutcome.COP_WIN:
            return ScoreResult(cop=self.cop_win, thief=self.thief_loss)
        if outcome is TerminalOutcome.THIEF_WIN:
            return ScoreResult(cop=self.cop_loss, thief=self.thief_win)
        raise DomainError(f"unsupported terminal outcome: {outcome!r}")


def score_state(state: GameState, scoring: ScoreMatrix) -> ScoreResult:
    if state.terminal_outcome is None:
        raise DomainError("cannot score a non-terminal state")
    return scoring.score(state.terminal_outcome)
