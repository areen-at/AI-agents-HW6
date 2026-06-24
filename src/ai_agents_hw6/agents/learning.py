from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ai_agents_hw6.agents.heuristic import HeuristicPolicy
from ai_agents_hw6.agents.policy import PolicyInput
from ai_agents_hw6.domain import (
    Direction,
    GameAction,
    MoveAction,
    PlaceBarrierAction,
    Role,
)
from ai_agents_hw6.domain.errors import DomainError

Q_TABLE_VERSION = 1
MOVE_ACTION_INDICES = {
    Direction.UP: 0,
    Direction.RIGHT: 1,
    Direction.DOWN: 2,
    Direction.LEFT: 3,
}
COP_BARRIER_ACTION_OFFSET = 4


@dataclass(frozen=True)
class LearningSettings:
    enabled: bool = False
    alpha: float = 0.1
    gamma: float = 0.95
    epsilon: float = 0.1
    seed: int = 2026
    training_seed: int = 2026
    evaluation_seed: int = 2027
    cop_table_path: str = "artifacts/learning/cop_q_table.json"
    thief_table_path: str = "artifacts/learning/thief_q_table.json"

    def __post_init__(self) -> None:
        for name, value in (
            ("alpha", self.alpha),
            ("gamma", self.gamma),
            ("epsilon", self.epsilon),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be numeric")
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.training_seed == self.evaluation_seed:
            raise ValueError("training_seed and evaluation_seed must be distinct")


@dataclass
class QLearningPolicy:
    settings: LearningSettings
    fallback: HeuristicPolicy = field(default_factory=HeuristicPolicy)
    cop_table: dict[str, dict[int, float]] = field(default_factory=dict)
    thief_table: dict[str, dict[int, float]] = field(default_factory=dict)
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.settings.seed)

    def choose_action(self, policy_input: PolicyInput) -> GameAction:
        if not policy_input.legal_actions:
            raise DomainError("policy input has no legal actions")
        if not self.settings.enabled:
            return self.fallback.choose_action(policy_input)

        indexed = tuple(
            (action_index(policy_input.role, action, policy_input.grid.columns), action)
            for action in policy_input.legal_actions
        )
        if self._rng.random() < self.settings.epsilon:
            return self._rng.choice(indexed)[1]

        state_key = encode_observation_state(policy_input)
        values = self._table(policy_input.role).get(state_key, {})
        best_value = max((values.get(index, 0.0) for index, _ in indexed), default=0.0)
        best = tuple(action for index, action in indexed if values.get(index, 0.0) == best_value)
        fallback_action = self.fallback.choose_action(policy_input)
        return fallback_action if fallback_action in best else best[0]

    def update(
        self,
        *,
        current: PolicyInput,
        action: GameAction,
        reward: float,
        next_input: PolicyInput | None,
        terminal: bool,
    ) -> None:
        if action not in current.legal_actions:
            raise DomainError("cannot update Q value for an illegal action")
        state_key = encode_observation_state(current)
        index = action_index(current.role, action, current.grid.columns)
        state_values = self._table(current.role).setdefault(state_key, {})
        current_value = state_values.get(index, 0.0)
        future_value = 0.0
        if not terminal:
            if next_input is None:
                raise ValueError("next_input is required for a non-terminal update")
            if next_input.role is not current.role:
                raise ValueError("Q update must remain role-specific")
            next_values = self._table(current.role).get(encode_observation_state(next_input), {})
            future_value = max(
                (
                    next_values.get(
                        action_index(next_input.role, candidate, next_input.grid.columns),
                        0.0,
                    )
                    for candidate in next_input.legal_actions
                ),
                default=0.0,
            )
        target = float(reward) + self.settings.gamma * future_value
        state_values[index] = current_value + self.settings.alpha * (target - current_value)

    def load(self) -> None:
        self.cop_table = load_q_table(self.settings.cop_table_path, Role.COP)
        self.thief_table = load_q_table(self.settings.thief_table_path, Role.THIEF)

    def save(self) -> None:
        save_q_table(self.settings.cop_table_path, Role.COP, self.cop_table)
        save_q_table(self.settings.thief_table_path, Role.THIEF, self.thief_table)

    def _table(self, role: Role) -> dict[str, dict[int, float]]:
        if role is Role.COP:
            return self.cop_table
        if role is Role.THIEF:
            return self.thief_table
        raise DomainError(f"unsupported role: {role!r}")


def encode_observation_state(policy_input: PolicyInput) -> str:
    """Encode only role-approved observation fields; authoritative hidden state is unavailable."""

    payload = {
        "role": policy_input.role.value,
        "self": policy_input.self_position.to_json(),
        "opponent": (
            policy_input.visible_opponent.to_json()
            if policy_input.visible_opponent is not None
            else None
        ),
        "barriers": [barrier.to_json() for barrier in sorted(policy_input.visible_barriers)],
        "grid": policy_input.grid.to_json(),
        "legal": sorted(
            action_index(policy_input.role, action, policy_input.grid.columns)
            for action in policy_input.legal_actions
        ),
        "round": policy_input.move_round,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def action_index(role: Role, action: GameAction, grid_columns: int) -> int:
    if isinstance(action, MoveAction):
        return MOVE_ACTION_INDICES[action.direction]
    if isinstance(action, PlaceBarrierAction):
        if role is not Role.COP:
            raise DomainError("Thief has no barrier action indices")
        return COP_BARRIER_ACTION_OFFSET + action.target.row * grid_columns + action.target.column
    raise DomainError("unsupported action type")


def save_q_table(
    path: str | Path,
    role: Role,
    table: dict[str, dict[int, float]],
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": Q_TABLE_VERSION,
        "role": role.value,
        "values": {
            state: {str(index): value for index, value in sorted(values.items())}
            for state, values in sorted(table.items())
        },
    }
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    temporary.replace(target)


def load_q_table(path: str | Path, role: Role) -> dict[str, dict[int, float]]:
    target = Path(path)
    if not target.exists():
        return {}
    payload: Any = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("version") != Q_TABLE_VERSION:
        raise ValueError(f"incompatible Q-table version at {target}")
    if payload.get("role") != role.value:
        raise ValueError(f"Q-table role mismatch at {target}")
    values = payload.get("values")
    if not isinstance(values, dict):
        raise ValueError(f"invalid Q-table values at {target}")
    return {
        str(state): {int(index): float(value) for index, value in state_values.items()}
        for state, state_values in values.items()
        if isinstance(state_values, dict)
    }
