from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class ConfigError(ValueError):
    """Raised when configuration is missing, malformed, or invalid."""


@dataclass(frozen=True)
class GroupConfig:
    name: str
    github_repo: str
    students: tuple[str, ...]


@dataclass(frozen=True)
class ServerUrls:
    cop_mcp_url: str
    thief_mcp_url: str


@dataclass(frozen=True)
class BonusOpponentConfig:
    group_name: str
    github_repo: str
    students: tuple[str, ...]
    cop_mcp_url: str
    thief_mcp_url: str


@dataclass(frozen=True)
class ScoringConfig:
    cop_win: int
    thief_win: int
    cop_loss: int
    thief_loss: int


@dataclass(frozen=True)
class GameConfig:
    grid_size: tuple[int, int]
    max_moves: int
    num_games: int
    max_barriers: int
    scoring: ScoringConfig


@dataclass(frozen=True)
class ObservationConfig:
    manhattan_radius: int


@dataclass(frozen=True)
class RuntimeConfig:
    timezone: str
    random_seed: int
    decision_timeout_seconds: int
    max_retries: int
    technical_attempt_limit_per_slot: int


@dataclass(frozen=True)
class ReportPaths:
    internal_game_report: str
    bonus_game_report: str
    bonus_mock_report: str


@dataclass(frozen=True)
class LoggingConfig:
    level: str
    event_log_dir: str


@dataclass(frozen=True)
class AppConfig:
    group: GroupConfig
    my_servers: ServerUrls
    bonus_opponent: BonusOpponentConfig
    game: GameConfig
    observation: ObservationConfig
    runtime: RuntimeConfig
    reports: ReportPaths
    logging: LoggingConfig


PLACEHOLDER_VALUES = {
    "",
    "MY_GROUP_NAME",
    "MY_REPO_URL",
    "MY_COP_MCP_URL",
    "MY_THIEF_MCP_URL",
    "OTHER_TEAM_NAME",
    "OTHER_TEAM_REPO_URL",
    "OTHER_TEAM_COP_MCP_URL",
    "OTHER_TEAM_THIEF_MCP_URL",
}

VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"config file not found: {config_path}")

    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON at {config_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("config root must be a JSON object")

    return _parse_config(raw)


def validate_for_mode(config: AppConfig, mode: str) -> None:
    if mode not in {"internal", "bonus", "bonus-mock"}:
        raise ConfigError(f"unknown mode: {mode}")

    if config.game.num_games != 6:
        raise ConfigError("production modes require game.num_games to be exactly 6")

    _require_valid_url(
        "my_servers.cop_mcp_url",
        config.my_servers.cop_mcp_url,
        require_https=False,
        allow_local_http=True,
    )
    _require_valid_url(
        "my_servers.thief_mcp_url",
        config.my_servers.thief_mcp_url,
        require_https=False,
        allow_local_http=True,
    )

    if mode == "bonus":
        _require_real_text("bonus_opponent.group_name", config.bonus_opponent.group_name)
        _require_valid_url(
            "bonus_opponent.github_repo",
            config.bonus_opponent.github_repo,
            require_https=True,
            allow_local_http=False,
        )
        _require_valid_url(
            "bonus_opponent.cop_mcp_url",
            config.bonus_opponent.cop_mcp_url,
            require_https=True,
            allow_local_http=False,
        )
        _require_valid_url(
            "bonus_opponent.thief_mcp_url",
            config.bonus_opponent.thief_mcp_url,
            require_https=True,
            allow_local_http=False,
        )


def validate_for_public_deployment(config: AppConfig) -> None:
    cop_url = config.my_servers.cop_mcp_url
    thief_url = config.my_servers.thief_mcp_url
    _require_valid_url(
        "my_servers.cop_mcp_url",
        cop_url,
        require_https=True,
        allow_local_http=False,
    )
    _require_valid_url(
        "my_servers.thief_mcp_url",
        thief_url,
        require_https=True,
        allow_local_http=False,
    )
    if cop_url.rstrip("/") == thief_url.rstrip("/"):
        raise ConfigError("Cop and Thief public MCP URLs must be distinct")


def _parse_config(raw: dict[str, Any]) -> AppConfig:
    group_raw = _require_object(raw, "group")
    servers_raw = _require_object(raw, "my_servers")
    opponent_raw = _require_object(raw, "bonus_opponent")
    game_raw = _require_object(raw, "game")
    observation_raw = _require_object(raw, "observation")
    runtime_raw = _require_object(raw, "runtime")
    reports_raw = _require_object(raw, "reports")
    logging_raw = _require_object(raw, "logging")

    scoring_raw = _require_object(game_raw, "game.scoring", key="scoring")

    config = AppConfig(
        group=GroupConfig(
            name=_require_string(group_raw, "group.name", key="name"),
            github_repo=_require_string(group_raw, "group.github_repo", key="github_repo"),
            students=_require_string_tuple(group_raw, "group.students", key="students"),
        ),
        my_servers=ServerUrls(
            cop_mcp_url=_require_string(servers_raw, "my_servers.cop_mcp_url", key="cop_mcp_url"),
            thief_mcp_url=_require_string(
                servers_raw,
                "my_servers.thief_mcp_url",
                key="thief_mcp_url",
            ),
        ),
        bonus_opponent=BonusOpponentConfig(
            group_name=_require_string(
                opponent_raw,
                "bonus_opponent.group_name",
                key="group_name",
            ),
            github_repo=_require_string(
                opponent_raw,
                "bonus_opponent.github_repo",
                key="github_repo",
            ),
            students=_require_string_tuple(
                opponent_raw,
                "bonus_opponent.students",
                key="students",
            ),
            cop_mcp_url=_require_string(
                opponent_raw,
                "bonus_opponent.cop_mcp_url",
                key="cop_mcp_url",
            ),
            thief_mcp_url=_require_string(
                opponent_raw,
                "bonus_opponent.thief_mcp_url",
                key="thief_mcp_url",
            ),
        ),
        game=GameConfig(
            grid_size=_require_grid_size(game_raw),
            max_moves=_require_positive_int(game_raw, "game.max_moves", key="max_moves"),
            num_games=_require_positive_int(game_raw, "game.num_games", key="num_games"),
            max_barriers=_require_non_negative_int(
                game_raw,
                "game.max_barriers",
                key="max_barriers",
            ),
            scoring=ScoringConfig(
                cop_win=_require_non_negative_int(scoring_raw, "game.scoring.cop_win", key="cop_win"),
                thief_win=_require_non_negative_int(
                    scoring_raw,
                    "game.scoring.thief_win",
                    key="thief_win",
                ),
                cop_loss=_require_non_negative_int(
                    scoring_raw,
                    "game.scoring.cop_loss",
                    key="cop_loss",
                ),
                thief_loss=_require_non_negative_int(
                    scoring_raw,
                    "game.scoring.thief_loss",
                    key="thief_loss",
                ),
            ),
        ),
        observation=ObservationConfig(
            manhattan_radius=_require_non_negative_int(
                observation_raw,
                "observation.manhattan_radius",
                key="manhattan_radius",
            ),
        ),
        runtime=RuntimeConfig(
            timezone=_require_string(runtime_raw, "runtime.timezone", key="timezone"),
            random_seed=_require_int(runtime_raw, "runtime.random_seed", key="random_seed"),
            decision_timeout_seconds=_require_positive_int(
                runtime_raw,
                "runtime.decision_timeout_seconds",
                key="decision_timeout_seconds",
            ),
            max_retries=_require_non_negative_int(
                runtime_raw,
                "runtime.max_retries",
                key="max_retries",
            ),
            technical_attempt_limit_per_slot=_require_positive_int(
                runtime_raw,
                "runtime.technical_attempt_limit_per_slot",
                key="technical_attempt_limit_per_slot",
            ),
        ),
        reports=ReportPaths(
            internal_game_report=_require_string(
                reports_raw,
                "reports.internal_game_report",
                key="internal_game_report",
            ),
            bonus_game_report=_require_string(
                reports_raw,
                "reports.bonus_game_report",
                key="bonus_game_report",
            ),
            bonus_mock_report=_require_string(
                reports_raw,
                "reports.bonus_mock_report",
                key="bonus_mock_report",
            ),
        ),
        logging=LoggingConfig(
            level=_require_log_level(logging_raw),
            event_log_dir=_require_string(logging_raw, "logging.event_log_dir", key="event_log_dir"),
        ),
    )

    if config.game.grid_size[0] < 2 or config.game.grid_size[1] < 2:
        raise ConfigError("game.grid_size must be at least [2, 2]")

    return config


def _require_object(container: dict[str, Any], path: str, *, key: str | None = None) -> dict[str, Any]:
    lookup = key if key is not None else path
    value = container.get(lookup)
    if not isinstance(value, dict):
        raise ConfigError(f"{path} must be an object")
    return value


def _require_string(container: dict[str, Any], path: str, *, key: str) -> str:
    value = container.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{path} must be a non-empty string")
    return value.strip()


def _require_string_tuple(container: dict[str, Any], path: str, *, key: str) -> tuple[str, ...]:
    value = container.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"{path} must be a list of strings")
    cleaned = tuple(item.strip() for item in value)
    if any(not item for item in cleaned):
        raise ConfigError(f"{path} must not contain blank strings")
    return cleaned


def _require_int(container: dict[str, Any], path: str, *, key: str) -> int:
    value = container.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{path} must be an integer")
    return value


def _require_positive_int(container: dict[str, Any], path: str, *, key: str) -> int:
    value = _require_int(container, path, key=key)
    if value <= 0:
        raise ConfigError(f"{path} must be positive")
    return value


def _require_non_negative_int(container: dict[str, Any], path: str, *, key: str) -> int:
    value = _require_int(container, path, key=key)
    if value < 0:
        raise ConfigError(f"{path} must be non-negative")
    return value


def _require_grid_size(container: dict[str, Any]) -> tuple[int, int]:
    value = container.get("grid_size")
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(isinstance(item, bool) or not isinstance(item, int) for item in value)
    ):
        raise ConfigError("game.grid_size must be a two-item integer list")
    return (value[0], value[1])


def _require_log_level(container: dict[str, Any]) -> str:
    value = _require_string(container, "logging.level", key="level").upper()
    if value not in VALID_LOG_LEVELS:
        raise ConfigError(
            "logging.level must be one of DEBUG, INFO, WARNING, ERROR, or CRITICAL"
        )
    return value


def _require_real_text(path: str, value: str) -> None:
    if value.strip() in PLACEHOLDER_VALUES or "example.com" in value:
        raise ConfigError(f"{path} must be real production data, not a placeholder")


def _require_valid_url(
    path: str,
    value: str,
    *,
    require_https: bool,
    allow_local_http: bool,
) -> None:
    if not allow_local_http:
        _require_real_text(path, value)
    parsed = urlparse(value)
    if require_https and parsed.scheme != "https":
        raise ConfigError(f"{path} must be an HTTPS URL")
    if not parsed.netloc:
        raise ConfigError(f"{path} must include a host")
    if parsed.scheme not in {"http", "https"}:
        raise ConfigError(f"{path} must be an HTTP or HTTPS URL")
    if parsed.scheme == "http" and not allow_local_http:
        raise ConfigError(f"{path} must use HTTPS outside local development")
