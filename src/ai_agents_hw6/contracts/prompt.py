from __future__ import annotations

import json

from ai_agents_hw6.contracts.observation import Observation
from ai_agents_hw6.domain import Role


def render_decision_prompt(observation: Observation) -> str:
    role_objective = (
        "You are the Cop. Your objective is to catch the Thief."
        if observation.role is Role.COP
        else "You are the Thief. Your objective is to avoid capture until the move limit."
    )
    schema = {
        "protocol_version": observation.protocol_version,
        "request_id": observation.request_id,
        "role": observation.role.value,
        "action": {
            "type": "move",
            "direction": "up|down|left|right",
        },
    }
    if observation.role is Role.COP:
        schema["action"] = {
            "type": "move|place_barrier",
            "direction": "up|down|left|right for move only",
            "target": "[row, column] for place_barrier only",
        }

    return "\n".join(
        [
            role_objective,
            "Use only the observation below. Do not invent hidden board state.",
            "Return exactly one JSON object and no surrounding prose.",
            "Allowed response schema:",
            json.dumps(schema, sort_keys=True),
            "Current observation:",
            json.dumps(observation.to_public_json(), sort_keys=True),
        ]
    )
