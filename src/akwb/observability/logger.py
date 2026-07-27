"""Default observability implementation using the Python stdlib logging."""

from __future__ import annotations

import logging

from akwb.domain.events import DiagnosticEmitted
from akwb.domain.ports import EventBus, Observability
from akwb.types import Diagnostic


class LoggerObservability(Observability):
    """Collects diagnostics and emits structured log messages."""

    def __init__(
        self,
        name: str = "akwb",
        level: str = "INFO",
        event_bus: EventBus | None = None,
    ) -> None:
        self._diagnostics: list[Diagnostic] = []
        self._event_bus = event_bus
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(levelname)s [%(name)s] %(message)s"))
            self._logger.addHandler(handler)

    def info(self, message: str) -> None:
        self._logger.info(message)

    def warning(self, message: str) -> None:
        self._logger.warning(message)

    def error(self, message: str) -> None:
        self._logger.error(message)

    def diagnostic(self, diagnostic: Diagnostic) -> None:
        self._diagnostics.append(diagnostic)
        self._logger.log(
            getattr(logging, diagnostic.level.upper(), logging.INFO),
            "%s",
            str(diagnostic),
        )
        if self._event_bus:
            self._event_bus.publish(
                DiagnosticEmitted(
                    level=diagnostic.level,
                    code=diagnostic.code,
                    message=diagnostic.message,
                    source_ref=diagnostic.source_ref,
                )
            )

    def get_diagnostics(self) -> list[Diagnostic]:
        return list(self._diagnostics)
