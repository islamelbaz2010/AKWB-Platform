"""Extract artifact metadata from filesystem paths."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from akwb.discovery.fingerprint import FingerprintEngine
from akwb.discovery.models import ArtifactEntry


class MetadataExtractor:
    """Build an ArtifactEntry from a discovered filesystem path."""

    def __init__(self, fingerprint_engine: FingerprintEngine) -> None:
        self._fingerprint = fingerprint_engine

    def extract(
        self,
        path: Path,
        relative_path: str,
        project_root: Path,
        artifact_type: str,
        category: str,
        content_hash: str | None,
        stat: os.stat_result | None = None,
    ) -> ArtifactEntry:
        """Extract metadata for a file."""
        resolved = path.resolve()
        if stat is None:
            stat = resolved.stat()
        return ArtifactEntry(
            id=self._fingerprint.stable_id(relative_path),
            absolute_path=str(resolved),
            relative_path=relative_path,
            type=artifact_type,
            category=category,
            extension=self._extension(resolved),
            hash=content_hash,
            size=stat.st_size,
            created_time=self._format_time(self._created_timestamp(stat)),
            modified_time=self._format_time(stat.st_mtime),
            parent_directory=str(resolved.parent),
            tags=[category, artifact_type],
        )

    def extract_directory(
        self,
        path: Path,
        relative_path: str,
        project_root: Path,
        stat: os.stat_result | None = None,
    ) -> ArtifactEntry:
        """Extract metadata for a directory."""
        resolved = path.resolve()
        if stat is None:
            stat = resolved.stat()
        return ArtifactEntry(
            id=self._fingerprint.stable_id(relative_path),
            absolute_path=str(resolved),
            relative_path=relative_path,
            type="directory",
            category="directory",
            extension="",
            hash=None,
            size=0,
            created_time=self._format_time(self._created_timestamp(stat)),
            modified_time=self._format_time(stat.st_mtime),
            parent_directory=str(resolved.parent),
            tags=["directory"],
        )

    @staticmethod
    def _extension(path: Path) -> str:
        """Return the extension for a file, treating dot-files as extensionless."""
        name = path.name
        if name.startswith(".") and "." not in name[1:]:
            return ""
        return path.suffix.lower().lstrip(".") or ""

    @staticmethod
    def _created_timestamp(stat: os.stat_result) -> float:
        """Return best available creation timestamp (birthtime when present)."""
        return float(getattr(stat, "st_birthtime", stat.st_ctime))

    @staticmethod
    def _format_time(timestamp: float) -> str:
        return datetime.fromtimestamp(timestamp, tz=UTC).isoformat()
