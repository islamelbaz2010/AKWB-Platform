"""Domain models for the Enterprise Extraction Pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from akwb.knowledge.models import KnowledgeObject, KnowledgeSource
from akwb.types import Diagnostic, make_id


class ContentKind(str, Enum):
    """High-level categories of normalized artifact content."""

    TEXT = "text"
    BINARY = "binary"
    STRUCTURED = "structured"
    MARKDOWN = "markdown"
    DOCUMENT = "document"
    MULTIMODAL = "multimodal"


class SegmentType(str, Enum):
    """Kinds of segments produced by a segmentation engine."""

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    CODE = "code"
    TABLE = "table"
    LIST = "list"
    QUOTE = "quote"
    LINK = "link"
    IMAGE = "image"
    HTML = "html"
    FOOTNOTE = "footnote"
    TASK_LIST = "task_list"
    METADATA = "metadata"
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"
    ADAPTIVE = "adaptive"
    DOCUMENT = "document"
    OTHER = "other"


class NormalizedContent(BaseModel):
    """Normalized representation produced by a Reader."""

    kind: ContentKind
    mime_type: str
    content: Any
    encoding: str | None = "utf-8"
    source_uri: str
    language: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "allow"}


class Segment(BaseModel):
    """A contiguous, typed piece of normalized content."""

    id: str = Field(default_factory=make_id)
    type: SegmentType
    label: str | None = None
    content: Any
    location: str | None = None
    parent_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractionCandidate(BaseModel):
    """A candidate fact before it becomes a KnowledgeObject."""

    id: str = Field(default_factory=make_id)
    knowledge_type: str
    title: str
    description: str | None = None
    content: Any = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: KnowledgeSource | None = None
    evidence_excerpt: str | None = None
    evidence_location: str | None = None
    segment: Segment | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


@dataclass
class ExtractionResult:
    """Outcome of running the extraction pipeline on an artifact."""

    ok: bool = True
    objects: list[KnowledgeObject] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    candidate_count: int = 0

    def __bool__(self) -> bool:
        return self.ok
