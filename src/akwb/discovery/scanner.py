"""Recursive filesystem scanner used by the Discovery engine."""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from akwb.discovery.ignore import IgnoreEngine


@dataclass
class ScannedItem:
    """A path discovered during recursive scanning."""

    path: Path
    relative_path: str
    is_directory: bool


class RecursiveScanner:
    """Walk a project tree while respecting ignore rules and symlink settings."""

    def __init__(
        self,
        ignore_engine: IgnoreEngine,
        follow_symlinks: bool = False,
        include_directories: bool = True,
    ) -> None:
        self._ignore = ignore_engine
        self._follow_symlinks = follow_symlinks
        self._include_directories = include_directories

    def scan(self, project_root: Path) -> Iterator[ScannedItem]:
        """Yield ScannedItem instances for all non-ignored project paths."""
        root = project_root.resolve()
        seen: set[tuple[int, int]] = set()
        yield from self._scan_dir(root, root, seen)

    def _scan_dir(
        self,
        dirpath: Path,
        root: Path,
        seen: set[tuple[int, int]],
    ) -> Iterator[ScannedItem]:
        """Recursively scan a directory using os.scandir for efficiency."""
        try:
            with os.scandir(dirpath) as it:
                entries = sorted(it, key=lambda e: e.name)
        except OSError:
            return

        dirs: list[os.DirEntry[str]] = []
        files: list[os.DirEntry[str]] = []

        for entry in entries:
            abs_path = Path(entry.path)
            is_symlink = entry.is_symlink()

            if is_symlink and not self._follow_symlinks:
                # Directory symlinks are reported as directories when not followed.
                if (
                    self._include_directories
                    and entry.is_dir(follow_symlinks=True)
                    and not self._ignore.is_ignored(abs_path, is_dir=True)
                ):
                    rel = abs_path.relative_to(root).as_posix()
                    yield ScannedItem(abs_path, rel, True)
                continue

            entry_is_dir = entry.is_dir(follow_symlinks=self._follow_symlinks)
            entry_is_file = entry.is_file(follow_symlinks=self._follow_symlinks)

            if entry_is_dir:
                if not self._ignore.is_ignored(abs_path, is_dir=True):
                    dirs.append(entry)
            elif entry_is_file and not self._ignore.is_ignored(abs_path, is_dir=False):
                files.append(entry)
            # Other entry types (sockets, FIFOs, devices) are ignored.

        if self._include_directories:
            for entry in dirs:
                abs_path = Path(entry.path)
                rel = abs_path.relative_to(root).as_posix()
                yield ScannedItem(abs_path, rel, True)

        for entry in files:
            abs_path = Path(entry.path)
            rel = abs_path.relative_to(root).as_posix()
            yield ScannedItem(abs_path, rel, False)

        for entry in dirs:
            abs_path = Path(entry.path)
            if self._follow_symlinks:
                try:
                    stat = entry.stat(follow_symlinks=True)
                    key = (stat.st_ino, stat.st_dev)
                except OSError:
                    continue
                if key in seen:
                    continue
                seen.add(key)
            yield from self._scan_dir(abs_path, root, seen)
