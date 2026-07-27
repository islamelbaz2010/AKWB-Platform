"""Generic registries for knowledge types, relationship types, and evidence types."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any, TypeVar

T = TypeVar("T")


class TypeRegistry[T]:
    """A strongly-typed registry keyed by ``.id``.

    Used for ``KnowledgeType``, ``RelationshipType``, and ``EvidenceType``.
    """

    def __init__(self) -> None:
        self._items: dict[str, T] = {}

    def register(self, item: T) -> None:
        """Register an item. ``item`` must have an ``id`` attribute."""
        item_id = getattr(item, "id", None)
        if not item_id:
            raise ValueError("Registry items must have a non-empty 'id' attribute")
        self._items[item_id] = item

    def register_all(self, items: Iterable[T]) -> None:
        """Register many items at once."""
        for item in items:
            self.register(item)

    def has(self, item_id: str) -> bool:
        """Return True if ``item_id`` is registered."""
        return item_id in self._items

    def get(self, item_id: str) -> T | None:
        """Return the registered item, or None."""
        return self._items.get(item_id)

    def items(self) -> dict[str, T]:
        """Return a snapshot of all registered items as a dict."""
        return dict(self._items)

    def __iter__(self) -> Iterator[tuple[str, T]]:
        return iter(self._items.items())

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, item_id: Any) -> bool:
        return self.has(str(item_id))
