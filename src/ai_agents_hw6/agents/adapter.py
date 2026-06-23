from __future__ import annotations

from ai_agents_hw6.agents.heuristic import HeuristicPolicy
from ai_agents_hw6.agents.policy import Policy, PolicyInput
from ai_agents_hw6.domain import GameAction, GameState, Role, legal_actions


def policy_input_from_state(state: GameState, *, max_barriers: int = 5) -> PolicyInput:
    role = state.active_role
    return PolicyInput(
        role=role,
        self_position=state.cop_position if role is Role.COP else state.thief_position,
        visible_opponent=state.thief_position if role is Role.COP else state.cop_position,
        visible_barriers=frozenset(state.barriers),
        grid=state.grid,
        legal_actions=legal_actions(state, max_barriers=max_barriers),
        move_round=state.move_round,
        seed=state.seed,
    )


def policy_decision_provider(policy: Policy, *, max_barriers: int = 5):
    def decide(state: GameState) -> GameAction:
        return policy.choose_action(policy_input_from_state(state, max_barriers=max_barriers))

    return decide


def heuristic_decision_provider(*, max_barriers: int = 5):
    return policy_decision_provider(HeuristicPolicy(), max_barriers=max_barriers)
