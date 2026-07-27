"""Typed, in-memory publish/subscribe event bus."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from akwb.domain.events import DomainEvent
from akwb.domain.ports import EventBus


class InMemoryEventBus(EventBus):
    """Synchronous in-process event bus."""

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[Callable[[DomainEvent], None]]] = defaultdict(list)

    def subscribe(
        self,
        event_type: type[DomainEvent],
        handler: Callable[[DomainEvent], None],
    ) -> None:
        """Register a handler for a concrete event type."""
        if not issubclass(event_type, DomainEvent):
            raise TypeError("event_type must be a DomainEvent subclass")
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        """Dispatch an event to all registered handlers."""
        if not isinstance(event, DomainEvent):
            raise TypeError("event must be a DomainEvent instance")
        for handler in self._handlers.get(type(event), []):
            handler(event)
