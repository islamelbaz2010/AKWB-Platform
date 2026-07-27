"""Repository and service ports declared in the domain layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Any

from akwb.domain.events import DomainEvent
from akwb.types import Diagnostic


class StoragePort(ABC):
    """Abstract storage backend implementing atomic, path-sandboxed file access."""

    @abstractmethod
    def root(self) -> Path:
        """Return the absolute root directory of this storage backend."""
        ...

    @abstractmethod
    def exists(self, relative_path: str | Path) -> bool:
        """Return True if the file or directory exists."""
        ...

    @abstractmethod
    def ensure_dir(self, relative_path: str | Path) -> Path:
        """Create a directory and return its absolute path."""
        ...

    @abstractmethod
    def read_text(self, relative_path: str | Path) -> str:
        """Read a text file and return its content."""
        ...

    @abstractmethod
    def write_text(self, relative_path: str | Path, content: str) -> None:
        """Write text content atomically."""
        ...

    @abstractmethod
    def read_json(self, relative_path: str | Path) -> Any:
        """Read and parse a JSON file."""
        ...

    @abstractmethod
    def write_json(self, relative_path: str | Path, data: Any, indent: bool = True) -> None:
        """Serialize and write JSON atomically."""
        ...

    @abstractmethod
    def read_jsonl(self, relative_path: str | Path) -> list[dict[str, Any]]:
        """Read a JSONL file into a list of objects."""
        ...

    @abstractmethod
    def append_jsonl(self, relative_path: str | Path, records: list[dict[str, Any]]) -> None:
        """Append records to a JSONL file (creating it if necessary)."""
        ...


class EventBus(ABC):
    """In-process publish/subscribe event bus."""

    @abstractmethod
    def subscribe(self, event_type: type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
        """Subscribe a handler to an event type."""
        ...

    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """Publish an event to all subscribed handlers."""
        ...


class Observability(ABC):
    """Cross-cutting observability port: logging, diagnostics, and progress."""

    @abstractmethod
    def info(self, message: str) -> None:
        ...

    @abstractmethod
    def warning(self, message: str) -> None:
        ...

    @abstractmethod
    def error(self, message: str) -> None:
        ...

    @abstractmethod
    def diagnostic(self, diagnostic: Diagnostic) -> None:
        ...

    @abstractmethod
    def get_diagnostics(self) -> list[Diagnostic]:
        ...


class PluginPort(ABC):
    """Marker base class for all plugin extension ports."""

    port_name: str = ""
