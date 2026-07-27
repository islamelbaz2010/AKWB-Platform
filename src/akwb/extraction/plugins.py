"""Plugin extension ports for the extraction pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from akwb.domain.models import Artifact
from akwb.domain.ports import PluginPort
from akwb.knowledge.models import KnowledgeObject, KnowledgeSource
from akwb.knowledge.validation import ValidationResult

if TYPE_CHECKING:
    from akwb.extraction.models import (
        ExtractionCandidate,
        NormalizedContent,
        Segment,
    )
    from akwb.extraction.pipeline import ExtractionContext


class Reader(PluginPort, ABC):
    """Read an artifact into a normalized representation."""

    port_name = "reader"
    supported_mime_types: tuple[str, ...] = ()

    @abstractmethod
    def read(
        self,
        artifact: Artifact,
        content: bytes | str,
        context: ExtractionContext | None = None,
    ) -> NormalizedContent:
        """Return a normalized content object for the artifact."""
        ...

    def can_read(self, mime_type: str) -> bool:
        """Return True if this reader handles ``mime_type``."""
        return mime_type in self.supported_mime_types


class Segmenter(PluginPort, ABC):
    """Segment normalized content into discrete pieces."""

    port_name = "segmenter"
    supported_content_kinds: tuple[Any, ...] = ()

    @abstractmethod
    def segment(
        self,
        content: NormalizedContent,
        context: ExtractionContext | None = None,
    ) -> list[Segment]:
        """Return a list of segments."""
        ...

    def can_segment(self, kind: Any) -> bool:
        """Return True if this segmenter handles ``kind``."""
        return kind in self.supported_content_kinds


class Extractor(PluginPort, ABC):
    """Turn segments into extraction candidates."""

    port_name = "extractor"

    @abstractmethod
    def extract(
        self,
        segments: list[Segment],
        source: KnowledgeSource,
        context: ExtractionContext | None = None,
    ) -> list[ExtractionCandidate]:
        """Return candidates extracted from ``segments``."""
        ...


class CandidateBuilder(PluginPort, ABC):
    """Transform a validated candidate into a canonical KnowledgeObject."""

    port_name = "candidate_builder"

    @abstractmethod
    def build(
        self,
        candidate: ExtractionCandidate,
        source: KnowledgeSource,
        context: ExtractionContext | None = None,
    ) -> KnowledgeObject:
        """Build and return a KnowledgeObject."""
        ...


class CandidateValidator(PluginPort, ABC):
    """Validate an extraction candidate before it is built."""

    port_name = "candidate_validator"

    @abstractmethod
    def validate(
        self,
        candidate: ExtractionCandidate,
        context: ExtractionContext | None = None,
    ) -> ValidationResult:
        """Return a ValidationResult for the candidate."""
        ...
