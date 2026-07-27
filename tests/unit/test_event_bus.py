"""Tests for the in-memory event bus."""

from akwb.domain.events import WorkspaceInitialized
from akwb.events import InMemoryEventBus


def test_subscribe_and_publish() -> None:
    bus = InMemoryEventBus()
    received: list[WorkspaceInitialized] = []

    def handler(event: WorkspaceInitialized) -> None:
        received.append(event)

    bus.subscribe(WorkspaceInitialized, handler)
    bus.publish(WorkspaceInitialized(project_root="/tmp/p", workspace_dir="/tmp/p/.akwb"))
    assert len(received) == 1
    assert received[0].project_root == "/tmp/p"


def test_no_handlers_no_error() -> None:
    bus = InMemoryEventBus()
    bus.publish(WorkspaceInitialized(project_root="/tmp/p", workspace_dir="/tmp/p/.akwb"))
