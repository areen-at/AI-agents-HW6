from __future__ import annotations

from ai_agents_hw6.agents.heuristic import HeuristicPolicy
from ai_agents_hw6.agents.policy import Policy, PolicyInput
from ai_agents_hw6.contracts import (
    Observation,
    action_response_json,
    build_observation,
    parse_action_response,
)
from ai_agents_hw6.domain import GameAction, GameState, Role, legal_actions


def policy_input_from_observation(observation: Observation) -> PolicyInput:
    return PolicyInput(
        role=observation.role,
        self_position=observation.self_position,
        visible_opponent=observation.visible_opponent,
        visible_barriers=observation.visible_barriers,
        grid=observation.grid,
        legal_actions=observation.legal_actions,
        move_round=observation.move_round,
        seed=0,
    )


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


def heuristic_protocol_decision(
    observation: Observation,
    *,
    policy: Policy | None = None,
) -> str:
    selected_policy = policy or HeuristicPolicy()
    action = selected_policy.choose_action(policy_input_from_observation(observation))
    return action_response_json(
        protocol_version=observation.protocol_version,
        request_id=observation.request_id,
        role=observation.role,
        action=action,
    )


def heuristic_protocol_decision_provider(*, max_barriers: int = 5, manhattan_radius: int = 2):
    def decide(state: GameState) -> GameAction:
        observation = build_observation(
            state,
            request_id="engine-only-request",
            role=state.active_role,
            manhattan_radius=manhattan_radius,
            max_barriers=max_barriers,
        )
        raw_response = heuristic_protocol_decision(observation)
        return parse_action_response(raw_response, observation).action

    return decide
