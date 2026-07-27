"""Local filesystem storage backend with path sandboxing and atomic writes."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from akwb.domain.events import StorageWritten
from akwb.domain.ports import EventBus, StoragePort


class LocalStorageBackend(StoragePort):
    """Production storage backend for local filesystem workspaces."""

    def __init__(
        self,
        root: Path,
        event_bus: EventBus | None = None,
    ) -> None:
        self._root = root.resolve()
        self._event_bus = event_bus

    def root(self) -> Path:
        return self._root

    def _resolve(self, relative_path: str | Path) -> Path:
        """Resolve a workspace-relative path and enforce the sandbox."""
        target = (self._root / relative_path).resolve()
        # Python 3.12+ uses is_relative_to
        if not target.is_relative_to(self._root):
            raise PermissionError(f"Path escapes workspace root: {relative_path}")
        return target

    def exists(self, relative_path: str | Path) -> bool:
        return self._resolve(relative_path).exists()

    def ensure_dir(self, relative_path: str | Path) -> Path:
        target = self._resolve(relative_path)
        target.mkdir(parents=True, exist_ok=True)
        return target

    def read_text(self, relative_path: str | Path) -> str:
        target = self._resolve(relative_path)
        with target.open("r", encoding="utf-8") as f:
            return f.read()

    def write_text(self, relative_path: str | Path, content: str) -> None:
        target = self._resolve(relative_path)
        self._atomic_write(target, content.encode("utf-8"))
        self._emit_written(relative_path, "text/plain")

    def read_json(self, relative_path: str | Path) -> Any:
        text = self.read_text(relative_path)
        return json.loads(text)

    def write_json(
        self,
        relative_path: str | Path,
        data: Any,
        indent: bool = True,
    ) -> None:
        content = json.dumps(data, indent=2 if indent else None, ensure_ascii=False)
        target = self._resolve(relative_path)
        self._atomic_write(target, content.encode("utf-8"))
        self._emit_written(relative_path, "application/json")

    def read_jsonl(self, relative_path: str | Path) -> list[dict[str, Any]]:
        target = self._resolve(relative_path)
        if not target.exists():
            return []
        records: list[dict[str, Any]] = []
        with target.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    def append_jsonl(
        self,
        relative_path: str | Path,
        records: list[dict[str, Any]],
    ) -> None:
        target = self._resolve(relative_path)
        self.ensure_dir(target.parent)
        with target.open("a", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._emit_written(relative_path, "application/jsonl")

    def _atomic_write(self, target: Path, data: bytes) -> None:
        self.ensure_dir(target.parent)
        fd, tmp_path = tempfile.mkstemp(
            dir=str(target.parent),
            prefix=".akwb-tmp-",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, target)
        except Exception:
            try:
                os.unlink(tmp_path)
            except FileNotFoundError:
                pass
            raise

    def _emit_written(self, relative_path: str | Path, mime_type: str) -> None:
        if self._event_bus:
            self._event_bus.publish(
                StorageWritten(relative_path=str(relative_path), mime_type=mime_type)
            )
