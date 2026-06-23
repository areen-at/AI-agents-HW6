from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from ai_agents_hw6.domain.errors import DomainError


@dataclass(frozen=True)
class _Identifier:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise DomainError(f"{type(self).__name__}.value must be a non-empty string")
        normalized = self.value.strip()
        try:
            UUID(normalized)
        except ValueError as exc:
            raise DomainError(f"{type(self).__name__}.value must be a UUID string") from exc
        object.__setattr__(self, "value", normalized)

    @classmethod
    def new(cls) -> "_Identifier":
        return cls(str(uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class SeriesId(_Identifier):
    @classmethod
    def new(cls) -> "SeriesId":
        return cls(str(uuid4()))


@dataclass(frozen=True)
class SubGameId(_Identifier):
    @classmethod
    def new(cls) -> "SubGameId":
        return cls(str(uuid4()))


@dataclass(frozen=True)
class AttemptId(_Identifier):
    @classmethod
    def new(cls) -> "AttemptId":
        return cls(str(uuid4()))


@dataclass(frozen=True)
class RequestId(_Identifier):
    @classmethod
    def new(cls) -> "RequestId":
        return cls(str(uuid4()))
