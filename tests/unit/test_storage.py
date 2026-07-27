"""Tests for the local storage backend."""

from pathlib import Path

import pytest

from akwb.domain.events import StorageWritten
from akwb.events import InMemoryEventBus
from akwb.storage import LocalStorageBackend


def test_storage_json_roundtrip(tmp_path: Path) -> None:
    backend = LocalStorageBackend(tmp_path / "ws")
    backend.write_json("test.json", {"key": "value"})
    assert backend.read_json("test.json") == {"key": "value"}


def test_storage_text_roundtrip(tmp_path: Path) -> None:
    backend = LocalStorageBackend(tmp_path / "ws")
    backend.write_text("notes.md", "hello")
    assert backend.read_text("notes.md") == "hello"


def test_storage_jsonl_roundtrip(tmp_path: Path) -> None:
    backend = LocalStorageBackend(tmp_path / "ws")
    backend.append_jsonl("log.jsonl", [{"a": 1}, {"b": 2}])
    backend.append_jsonl("log.jsonl", [{"c": 3}])
    assert len(backend.read_jsonl("log.jsonl")) == 3


def test_storage_sandbox_escape(tmp_path: Path) -> None:
    backend = LocalStorageBackend(tmp_path / "ws")
    with pytest.raises((PermissionError, ValueError)):
        backend.write_text("../escape.txt", "bad")


def test_storage_emits_event(tmp_path: Path) -> None:
    bus = InMemoryEventBus()
    events: list = []
    bus.subscribe(StorageWritten, lambda e: events.append(e))
    backend = LocalStorageBackend(tmp_path / "ws", event_bus=bus)
    backend.write_json("data.json", {})
    assert len(events) == 1
    assert events[0].relative_path == "data.json"
    assert events[0].mime_type == "application/json"
