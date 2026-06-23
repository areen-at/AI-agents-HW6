from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    COP = "cop"
    THIEF = "thief"


class Direction(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class ActionType(str, Enum):
    MOVE = "move"
    PLACE_BARRIER = "place_barrier"


class TerminalOutcome(str, Enum):
    COP_WIN = "cop_win"
    THIEF_WIN = "thief_win"


class TerminalReason(str, Enum):
    CAPTURE = "capture"
    MOVE_LIMIT = "move_limit"


class TechnicalFailureReason(str, Enum):
    MCP_TIMEOUT = "mcp_timeout"
    MCP_UNAVAILABLE = "mcp_unavailable"
    MALFORMED_RESPONSE = "malformed_response"
    ILLEGAL_ACTION_AFTER_REPAIR = "illegal_action_after_repair"
    PROTOCOL_MISMATCH = "protocol_mismatch"
    SERVER_CRASH = "server_crash"
    APPLICATION_ERROR = "application_error"
