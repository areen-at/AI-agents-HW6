from __future__ import annotations

from dataclasses import replace

from ai_agents_hw6.domain.actions import GameAction, MoveAction, PlaceBarrierAction
from ai_agents_hw6.domain.enums import Direction, Role, TerminalOutcome, TerminalReason
from ai_agents_hw6.domain.errors import DomainError
from ai_agents_hw6.domain.geometry import Coordinate
from ai_agents_hw6.domain.state import GameState


def legal_move_actions(state: GameState, role: Role) -> tuple[MoveAction, ...]:
    """Return legal movement actions for a role in the current snapshot."""

    _require_non_terminal(state)
    if not isinstance(role, Role):
        raise DomainError("role must be a Role")

    position = _position_for_role(state, role)
    legal: list[MoveAction] = []
    for direction in Direction:
        target = _move_target(position, direction)
        if target is not None and state.grid.contains(target) and target not in state.barriers:
            legal.append(MoveAction(direction))
    return tuple(legal)


def legal_barrier_actions(
    state: GameState, max_barriers: int = 5
) -> tuple[PlaceBarrierAction, ...]:
    """Return legal Cop barrier actions using the approved adjacent-empty-cell rule."""

    _require_non_terminal(state)
    _require_non_negative_limit(max_barriers, "max_barriers")

    if state.active_role is not Role.COP or state.barriers_placed >= max_barriers:
        return tuple()

    actions: list[PlaceBarrierAction] = []
    for target in state.grid.bounded_neighbors(state.cop_position):
        if _is_legal_barrier_target(state, target):
            candidate = replace(
                state,
                barriers=frozenset({*state.barriers, target}),
                barriers_placed=state.barriers_placed + 1,
            )
            if _has_any_movement(candidate, Role.COP) and _has_any_movement(candidate, Role.THIEF):
                actions.append(PlaceBarrierAction(target))
    return tuple(actions)


def legal_actions(
    state: GameState,
    *,
    role: Role | None = None,
    max_barriers: int = 5,
) -> tuple[GameAction, ...]:
    """Return all legal actions for the active role unless a role override is supplied."""

    acting_role = role or state.active_role
    movement: tuple[GameAction, ...] = legal_move_actions(state, acting_role)
    if acting_role is Role.COP:
        return movement + legal_barrier_actions(state, max_barriers=max_barriers)
    return movement


def apply_action(
    state: GameState,
    *,
    role: Role,
    action: GameAction,
    max_moves: int = 25,
    max_barriers: int = 5,
) -> GameState:
    """Validate and apply one role action to an immutable state snapshot."""

    _require_non_terminal(state)
    _require_positive_limit(max_moves, "max_moves")
    _require_non_negative_limit(max_barriers, "max_barriers")

    if not isinstance(role, Role):
        raise DomainError("role must be a Role")
    if role is not state.active_role:
        raise DomainError(
            f"out-of-turn action: expected {state.active_role.value}, got {role.value}"
        )

    if isinstance(action, MoveAction):
        return _apply_move(state, role=role, action=action, max_moves=max_moves)
    if isinstance(action, PlaceBarrierAction):
        return _apply_barrier(
            state,
            role=role,
            action=action,
            max_moves=max_moves,
            max_barriers=max_barriers,
        )
    raise DomainError("unsupported action type")


def replay_actions(
    initial_state: GameState,
    role_actions: tuple[tuple[Role, GameAction], ...],
    *,
    max_moves: int = 25,
    max_barriers: int = 5,
) -> GameState:
    state = initial_state
    for role, action in role_actions:
        state = apply_action(
            state,
            role=role,
            action=action,
            max_moves=max_moves,
            max_barriers=max_barriers,
        )
    return state


def _apply_move(
    state: GameState,
    *,
    role: Role,
    action: MoveAction,
    max_moves: int,
) -> GameState:
    legal_directions = {candidate.direction for candidate in legal_move_actions(state, role)}
    if action.direction not in legal_directions:
        raise DomainError("illegal move action")

    if role is Role.THIEF:
        moved = replace(
            state,
            thief_position=_position_for_role(state, role).moved(action.direction),
            active_role=Role.COP,
        )
        return moved

    next_position = _position_for_role(state, role).moved(action.direction)
    if next_position == state.thief_position:
        return replace(
            state,
            cop_position=next_position,
            terminal_outcome=TerminalOutcome.COP_WIN,
            terminal_reason=TerminalReason.CAPTURE,
        )

    next_round = state.move_round + 1
    if next_round >= max_moves:
        return replace(
            state,
            cop_position=next_position,
            move_round=next_round,
            terminal_outcome=TerminalOutcome.THIEF_WIN,
            terminal_reason=TerminalReason.MOVE_LIMIT,
        )
    return replace(
        state,
        cop_position=next_position,
        move_round=next_round,
        active_role=Role.THIEF,
    )


def _apply_barrier(
    state: GameState,
    *,
    role: Role,
    action: PlaceBarrierAction,
    max_moves: int,
    max_barriers: int,
) -> GameState:
    if role is not Role.COP:
        raise DomainError("only the Cop may place barriers")
    if state.barriers_placed >= max_barriers:
        raise DomainError("maximum barrier count reached")
    legal_targets = {
        candidate.target for candidate in legal_barrier_actions(state, max_barriers=max_barriers)
    }
    if action.target not in legal_targets:
        raise DomainError("illegal barrier placement")

    next_round = state.move_round + 1
    next_barriers = frozenset({*state.barriers, action.target})
    if next_round >= max_moves:
        return replace(
            state,
            barriers=next_barriers,
            barriers_placed=state.barriers_placed + 1,
            move_round=next_round,
            terminal_outcome=TerminalOutcome.THIEF_WIN,
            terminal_reason=TerminalReason.MOVE_LIMIT,
        )
    return replace(
        state,
        barriers=next_barriers,
        barriers_placed=state.barriers_placed + 1,
        move_round=next_round,
        active_role=Role.THIEF,
    )


def _position_for_role(state: GameState, role: Role) -> Coordinate:
    if role is Role.COP:
        return state.cop_position
    if role is Role.THIEF:
        return state.thief_position
    raise DomainError(f"unsupported role: {role!r}")


def _move_target(position: Coordinate, direction: Direction) -> Coordinate | None:
    try:
        return position.moved(direction)
    except DomainError:
        return None


def _is_legal_barrier_target(state: GameState, target: Coordinate) -> bool:
    if not state.grid.contains(target):
        return False
    if target in state.barriers:
        return False
    if target == state.cop_position or target == state.thief_position:
        return False
    return target in set(state.grid.bounded_neighbors(state.cop_position))


def _has_any_movement(state: GameState, role: Role) -> bool:
    position = _position_for_role(state, role)
    return any(target not in state.barriers for target in state.grid.bounded_neighbors(position))


def _require_non_terminal(state: GameState) -> None:
    if state.is_terminal:
        raise DomainError("terminal state cannot accept actions")


def _require_positive_limit(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise DomainError(f"{name} must be a positive integer")


def _require_non_negative_limit(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DomainError(f"{name} must be a non-negative integer")
