"""Ignore engine for filtering paths during project discovery."""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path


class IgnoreEngine:
    """Match paths against default and project-specific ignore patterns."""

    def __init__(self, project_root: Path, patterns: list[str]) -> None:
        self._root = project_root.resolve()
        self._patterns = list(patterns)
        self._project_ignores = self._load_project_ignores()

    def _load_project_ignores(self) -> list[str]:
        """Load user-defined ignore patterns from ``.akwbignore`` if present."""
        ignore_file = self._root / ".akwbignore"
        if not ignore_file.exists():
            return []
        lines = ignore_file.read_text(encoding="utf-8").splitlines()
        return [
            line.strip()
            for line in lines
            if line.strip() and not line.startswith("#")
        ]

    def is_ignored(
        self, path: Path, is_dir: bool | None = None
    ) -> bool:
        """Return True if ``path`` should be skipped during discovery."""
        abs_path = Path(os.path.abspath(str(path)))
        if abs_path == self._root:
            return False

        try:
            rel_parts = abs_path.relative_to(self._root).parts
        except ValueError:
            rel_parts = abs_path.parts

        name = abs_path.name
        is_directory = path.is_dir() if is_dir is None else is_dir
        all_patterns = self._patterns + self._project_ignores

        for pattern in all_patterns:
            if not pattern:
                continue
            if self._matches(pattern, rel_parts, name, is_directory):
                return True
        return False

    @staticmethod
    def _matches(
        pattern: str, relative_parts: tuple[str, ...], name: str, is_dir: bool
    ) -> bool:
        """Check a single ignore pattern against a path component list.

        Anchored patterns (``/...``) are matched relative to the project root.
        Unanchored patterns match any path component or the file name.
        Patterns ending with ``/`` apply to directories only.
        """
        directory_only = pattern.endswith("/")
        raw = pattern.rstrip("/").lstrip("/")
        if directory_only and not is_dir:
            return False

        anchored = pattern.startswith("/")
        if anchored:
            pat_parts = raw.split("/")
            if len(pat_parts) > len(relative_parts):
                return False
            for pat_part, rel_part in zip(pat_parts, relative_parts):
                if not fnmatch.fnmatch(rel_part, pat_part):
                    return False
            return True

        if fnmatch.fnmatch(name, raw):
            return True
        for part in relative_parts:
            if fnmatch.fnmatch(part, raw):
                return True
        return False
