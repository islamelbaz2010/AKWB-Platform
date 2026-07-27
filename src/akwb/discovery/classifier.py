"""File and directory classification into AKWB artifact types and categories."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import ClassVar


class FileClassifier:
    """Classify filesystem paths into stable artifact types and categories."""

    _TYPE_MAP: ClassVar[dict[str, str]] = {
        # documents
        ".md": "markdown",
        ".markdown": "markdown",
        ".txt": "text",
        ".rst": "text",
        ".log": "text",
        ".pdf": "pdf",
        ".docx": "docx",
        ".doc": "docx",
        ".pptx": "pptx",
        ".ppt": "pptx",
        # data
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".xml": "xml",
        ".csv": "csv",
        ".toml": "toml",
        ".ini": "ini",
        # source code
        ".py": "source_code",
        ".js": "source_code",
        ".ts": "source_code",
        ".jsx": "source_code",
        ".tsx": "source_code",
        ".java": "source_code",
        ".c": "source_code",
        ".cpp": "source_code",
        ".cc": "source_code",
        ".h": "source_code",
        ".hpp": "source_code",
        ".go": "source_code",
        ".rs": "source_code",
        ".rb": "source_code",
        ".php": "source_code",
        ".sh": "source_code",
        ".bash": "source_code",
        ".zsh": "source_code",
        # configuration
        ".conf": "config",
        ".cfg": "config",
        ".env": "config",
        ".properties": "config",
        # media
        ".png": "image",
        ".jpg": "image",
        ".jpeg": "image",
        ".gif": "image",
        ".svg": "image",
        ".bmp": "image",
        ".webp": "image",
        ".ico": "image",
        ".mp4": "video",
        ".mov": "video",
        ".avi": "video",
        ".mkv": "video",
        ".webm": "video",
        ".mp3": "audio",
        ".wav": "audio",
        ".ogg": "audio",
        ".flac": "audio",
        ".m4a": "audio",
        # archives
        ".zip": "archive",
        ".tar": "archive",
        ".gz": "archive",
        ".bz2": "archive",
        ".xz": "archive",
        ".rar": "archive",
        ".7z": "archive",
    }

    _CATEGORY_MAP: ClassVar[dict[str, str]] = {
        "markdown": "document",
        "text": "document",
        "pdf": "document",
        "docx": "document",
        "pptx": "document",
        "json": "data",
        "yaml": "data",
        "xml": "data",
        "csv": "data",
        "toml": "config",
        "ini": "config",
        "source_code": "code",
        "config": "config",
        "image": "media",
        "video": "media",
        "audio": "media",
        "archive": "archive",
    }

    def classify(self, path: Path, is_directory: bool = False) -> tuple[str, str]:
        """Return (type, category) for the given path."""
        if is_directory:
            return "directory", "directory"

        ext = path.suffix.lower()
        if ext in self._TYPE_MAP:
            artifact_type = self._TYPE_MAP[ext]
            return artifact_type, self._CATEGORY_MAP.get(artifact_type, "unknown")

        mime, _ = mimetypes.guess_type(str(path), strict=False)
        if mime:
            main, _, sub = mime.partition("/")
            if main == "image":
                return "image", "media"
            if main == "video":
                return "video", "media"
            if main == "audio":
                return "audio", "media"
            if main == "text":
                return "text", "document"
            if mime in ("application/pdf",):
                return "pdf", "document"
            if mime == "application/zip" or sub in ("zip", "x-tar", "x-gzip"):
                return "archive", "archive"

        return "unknown", "unknown"
