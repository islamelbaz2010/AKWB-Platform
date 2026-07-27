"""Shared, framework-agnostic types."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal, TypeVar

T = TypeVar("T")
E = TypeVar("E")


def utc_now() -> str:
    """Return an ISO 8601 UTC timestamp."""
    return datetime.now(UTC).isoformat()


def make_id() -> str:
    """Return a random v4 UUID string."""
    return str(uuid.uuid4())


@dataclass(frozen=True)
class Diagnostic:
    """A machine- and human-readable diagnostic message."""

    level: Literal["info", "warning", "error"]
    code: str
    message: str
    source_ref: str | None = None

    def __str__(self) -> str:
        return f"[{self.level.upper()}:{self.code}] {self.message}"


@dataclass(frozen=True)
class Result[T, E]:
    """Container for an operation that can fail with a diagnostic."""

    ok: bool
    value: T | None = field(default=None)
    error: E | None = field(default=None)
    diagnostics: list[Diagnostic] = field(default_factory=list)

    @staticmethod
    def success(value: T, diagnostics: list[Diagnostic] | None = None) -> Result[T, Any]:
        return Result(ok=True, value=value, diagnostics=diagnostics or [])

    @staticmethod
    def failure(error: E, diagnostics: list[Diagnostic] | None = None) -> Result[Any, E]:
        return Result(ok=False, error=error, diagnostics=diagnostics or [])
