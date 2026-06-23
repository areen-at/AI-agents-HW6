from __future__ import annotations

from random import Random

from ai_agents_hw6.domain.enums import Role
from ai_agents_hw6.domain.errors import DomainError
from ai_agents_hw6.domain.geometry import GridSize
from ai_agents_hw6.domain.identifiers import AttemptId, SeriesId, SubGameId
from ai_agents_hw6.domain.state import GameState


def create_initial_state(
    *,
    grid: GridSize,
    seed: int,
    series_id: SeriesId | None = None,
    sub_game_id: SubGameId | None = None,
    attempt_id: AttemptId | None = None,
) -> GameState:
    """Create a deterministic, distinct-position initial state for one attempt."""

    if isinstance(seed, bool) or not isinstance(seed, int):
        raise DomainError("seed must be an integer")

    cells = grid.all_coordinates()
    if len(cells) < 2:
        raise DomainError("grid must contain at least two cells")

    random = Random(seed)
    cop_position, thief_position = random.sample(cells, 2)
    return GameState(
        series_id=series_id or SeriesId.new(),
        sub_game_id=sub_game_id or SubGameId.new(),
        attempt_id=attempt_id or AttemptId.new(),
        grid=grid,
        cop_position=cop_position,
        thief_position=thief_position,
        active_role=Role.THIEF,
        seed=seed,
        move_round=0,
        barriers=frozenset(),
        barriers_placed=0,
    )
