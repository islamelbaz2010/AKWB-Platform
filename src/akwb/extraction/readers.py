"""Built-in readers for the extraction pipeline."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import yaml

from akwb.domain.models import Artifact
from akwb.extraction.models import ContentKind, NormalizedContent
from akwb.extraction.plugins import Reader

if TYPE_CHECKING:
    from akwb.extraction.pipeline import ExtractionContext


class TextReader(Reader):
    """Reader for text-based artifacts."""

    supported_mime_types = (
        "text/plain",
        "text/markdown",
        "text/x-markdown",
        "text/html",
        "text/css",
        "text/javascript",
    )

    def can_read(self, mime_type: str) -> bool:
        return mime_type.startswith("text/")

    def read(
        self,
        artifact: Artifact,
        content: bytes | str,
        context: ExtractionContext | None = None,
    ) -> NormalizedContent:
        text = content.decode("utf-8") if isinstance(content, bytes) else content
        return NormalizedContent(
            kind=ContentKind.TEXT,
            mime_type=artifact.mime_type,
            content=text,
            source_uri=artifact.relative_path or artifact.name,
            encoding="utf-8",
            language=None,
        )


class BinaryReader(Reader):
    """Reader for binary artifacts that cannot be directly extracted as text."""

    supported_mime_types = ("application/octet-stream",)

    def can_read(self, mime_type: str) -> bool:
        return mime_type.startswith(("image/", "audio/", "video/", "application/octet-stream"))

    def read(
        self,
        artifact: Artifact,
        content: bytes | str,
        context: ExtractionContext | None = None,
    ) -> NormalizedContent:
        data = content.encode("utf-8") if isinstance(content, str) else content
        return NormalizedContent(
            kind=ContentKind.BINARY,
            mime_type=artifact.mime_type,
            content=data,
            source_uri=artifact.relative_path or artifact.name,
            encoding=None,
            language=None,
        )


class StructuredReader(Reader):
    """Reader for JSON and YAML artifacts."""

    supported_mime_types = (
        "application/json",
        "application/x-yaml",
        "application/yaml",
        "text/yaml",
    )

    def can_read(self, mime_type: str) -> bool:
        return (
            mime_type in self.supported_mime_types
            or mime_type.endswith(("+json", "+yaml"))
        )

    def read(
        self,
        artifact: Artifact,
        content: bytes | str,
        context: ExtractionContext | None = None,
    ) -> NormalizedContent:
        text = content.decode("utf-8") if isinstance(content, bytes) else content
        data: Any
        if "json" in artifact.mime_type or artifact.mime_type.endswith("+json"):
            data = json.loads(text)
        else:
            data = yaml.safe_load(text)
        return NormalizedContent(
            kind=ContentKind.STRUCTURED,
            mime_type=artifact.mime_type,
            content=data,
            source_uri=artifact.relative_path or artifact.name,
            encoding="utf-8",
        )
