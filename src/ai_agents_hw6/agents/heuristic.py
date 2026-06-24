from __future__ import annotations

from dataclasses import replace

from ai_agents_hw6.agents.policy import PolicyInput
from ai_agents_hw6.domain import (
    AttemptId,
    Coordinate,
    Direction,
    GameAction,
    GridSize,
    MoveAction,
    PlaceBarrierAction,
    Role,
    SeriesId,
    SubGameId,
    legal_move_actions,
)
from ai_agents_hw6.domain.errors import DomainError
from ai_agents_hw6.domain.state import GameState

DIRECTION_TIE_BREAK = {
    Direction.UP: 0,
    Direction.RIGHT: 1,
    Direction.DOWN: 2,
    Direction.LEFT: 3,
}


class HeuristicPolicy:
    """Simple deterministic Cop/Thief baseline policy."""

    def choose_action(self, policy_input: PolicyInput) -> GameAction:
        if not policy_input.legal_actions:
            raise DomainError("policy input has no legal actions")
        if policy_input.role is Role.COP:
            return _choose_cop_action(policy_input)
        if policy_input.role is Role.THIEF:
            return _choose_thief_action(policy_input)
        raise DomainError(f"unsupported role: {policy_input.role!r}")


def _choose_cop_action(policy_input: PolicyInput) -> GameAction:
    moves = _move_actions(policy_input)
    barriers = _barrier_actions(policy_input)
    if policy_input.visible_opponent is None:
        return _deterministic_first(policy_input.legal_actions)

    opponent = policy_input.visible_opponent
    capture = _capture_move(moves, policy_input.self_position, opponent)
    if capture is not None:
        return capture

    useful_barrier = _useful_barrier(policy_input, barriers)
    if useful_barrier is not None:
        return useful_barrier

    return min(
        moves or policy_input.legal_actions,
        key=lambda action: (
            _distance_after_action(policy_input.self_position, action, opponent),
            _action_tie_break(action),
        ),
    )


def _choose_thief_action(policy_input: PolicyInput) -> GameAction:
    moves = _move_actions(policy_input)
    if not moves:
        raise DomainError("Thief has no legal movement action")
    if policy_input.visible_opponent is None:
        return min(moves, key=_action_tie_break)

    opponent = policy_input.visible_opponent
    return max(
        moves,
        key=lambda action: (
            _distance_after_action(policy_input.self_position, action, opponent),
            _escape_degree(policy_input, action),
            *_reverse_tie_break(action),
        ),
    )


def _capture_move(
    moves: tuple[MoveAction, ...],
    self_position: Coordinate,
    opponent: Coordinate,
) -> MoveAction | None:
    for move in sorted(moves, key=_action_tie_break):
        if self_position.moved(move.direction) == opponent:
            return move
    return None


def _useful_barrier(
    policy_input: PolicyInput,
    barriers: tuple[PlaceBarrierAction, ...],
) -> PlaceBarrierAction | None:
    if policy_input.visible_opponent is None:
        return None

    current_escape_degree = _visible_opponent_escape_degree(policy_input)
    useful: list[tuple[int, int, PlaceBarrierAction]] = []
    for barrier in barriers:
        next_barriers = frozenset({*policy_input.visible_barriers, barrier.target})
        reduced_escape_degree = _visible_opponent_escape_degree(
            replace(policy_input, visible_barriers=next_barriers),
        )
        reduction = current_escape_degree - reduced_escape_degree
        if reduction > 0:
            useful.append(
                (
                    -reduction,
                    manhattan_distance(barrier.target, policy_input.visible_opponent),
                    barrier,
                )
            )
    if not useful:
        return None
    return sorted(
        useful, key=lambda item: (item[0], item[1], item[2].target.row, item[2].target.column)
    )[0][2]


def _visible_opponent_escape_degree(policy_input: PolicyInput) -> int:
    if policy_input.visible_opponent is None:
        return 0
    pseudo_state = GameState(
        series_id=_DUMMY_STATE.series_id,
        sub_game_id=_DUMMY_STATE.sub_game_id,
        attempt_id=_DUMMY_STATE.attempt_id,
        grid=policy_input.grid,
        cop_position=policy_input.self_position
        if policy_input.role is Role.COP
        else policy_input.visible_opponent,
        thief_position=policy_input.visible_opponent
        if policy_input.role is Role.COP
        else policy_input.self_position,
        active_role=Role.THIEF,
        seed=policy_input.seed,
        barriers=policy_input.visible_barriers,
        barriers_placed=len(policy_input.visible_barriers),
    )
    return len(legal_move_actions(pseudo_state, _opponent_role(policy_input.role)))


def _escape_degree(policy_input: PolicyInput, action: MoveAction) -> int:
    next_position = policy_input.self_position.moved(action.direction)
    return sum(
        neighbor not in policy_input.visible_barriers
        for neighbor in policy_input.grid.bounded_neighbors(next_position)
    )


def _opponent_role(role: Role) -> Role:
    return Role.THIEF if role is Role.COP else Role.COP


def _move_actions(policy_input: PolicyInput) -> tuple[MoveAction, ...]:
    return tuple(action for action in policy_input.legal_actions if isinstance(action, MoveAction))


def _barrier_actions(policy_input: PolicyInput) -> tuple[PlaceBarrierAction, ...]:
    return tuple(
        action for action in policy_input.legal_actions if isinstance(action, PlaceBarrierAction)
    )


def _distance_after_action(
    self_position: Coordinate,
    action: GameAction,
    opponent: Coordinate,
) -> int:
    if isinstance(action, MoveAction):
        return manhattan_distance(self_position.moved(action.direction), opponent)
    if isinstance(action, PlaceBarrierAction):
        return manhattan_distance(self_position, opponent)
    return 10**9


def _deterministic_first(actions: tuple[GameAction, ...]) -> GameAction:
    return min(actions, key=_action_tie_break)


def _action_tie_break(action: GameAction) -> tuple[int, int, int]:
    if isinstance(action, MoveAction):
        return (0, DIRECTION_TIE_BREAK[action.direction], 0)
    if isinstance(action, PlaceBarrierAction):
        return (1, action.target.row, action.target.column)
    return (2, 0, 0)


def _reverse_tie_break(action: GameAction) -> tuple[int, int, int]:
    tie = _action_tie_break(action)
    return (-tie[0], -tie[1], -tie[2])


def manhattan_distance(first: Coordinate, second: Coordinate) -> int:
    return abs(first.row - second.row) + abs(first.column - second.column)


_DUMMY_STATE = GameState(
    series_id=SeriesId.new(),
    sub_game_id=SubGameId.new(),
    attempt_id=AttemptId.new(),
    grid=GridSize(2, 2),
    cop_position=Coordinate(0, 0),
    thief_position=Coordinate(1, 1),
    active_role=Role.THIEF,
    seed=0,
)
