"""Fingerprint / hashing engine for artifact content and stable IDs."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


class FingerprintEngine:
    """Compute content hashes and stable artifact identifiers."""

    def __init__(self, algorithm: str = "sha256", max_file_size_bytes: int | None = None) -> None:
        self._algorithm = algorithm
        self._max_file_size = max_file_size_bytes

    def stable_id(self, relative_path: str) -> str:
        """Return a deterministic, stable ID for an artifact path."""
        digest = hashlib.sha256(relative_path.encode("utf-8")).hexdigest()
        return digest[:32]

    def hash_file(
        self, path: Path, stat: os.stat_result | None = None
    ) -> str | None:
        """Return the content hash of ``path`` or None if skipped/oversized."""
        resolved = path.resolve()
        if resolved.is_dir():
            return None

        if stat is None:
            try:
                stat = resolved.stat()
            except OSError:
                return None

        if self._max_file_size is not None and stat.st_size > self._max_file_size:
            return None

        hasher = hashlib.new(self._algorithm)
        try:
            with resolved.open("rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except OSError:
            return None
