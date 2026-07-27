"""Canonical Document Model for the extraction pipeline.

Every future parser (DOCX, PDF, HTML, email, etc.) should output exactly one
``CanonicalDocument``. The canonical model is intentionally parser-agnostic and
captures the structural elements that downstream segmenters and extractors
need: headings, paragraphs, lists, tables, code blocks, images, links, quotes,
footnotes, metadata, and generic containers.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from akwb.domain.models import Artifact
from akwb.extraction.models import (
    ContentKind,
    NormalizedContent,
    Segment,
    SegmentType,
)
from akwb.extraction.plugins import Reader, Segmenter
from akwb.types import Diagnostic, make_id


class DocumentElement(BaseModel):
    """A single node in a ``CanonicalDocument``.

    ``DocumentElement`` is deliberately permissive: ``type`` is a string so new
    parser-specific element names can be introduced without schema churn. The
    common structural vocabulary lives in ``CanonicalElementType``.
    """

    model_config = ConfigDict(extra="allow")

    id: str = Field(default_factory=make_id)
    type: str
    level: int | None = Field(default=None, description="Heading level, list nesting depth, etc.")
    content: Any = Field(default=None, description="Raw element payload (text, rows, code, etc.)")
    location: dict[str, Any] | None = Field(
        default=None,
        description="Source location, e.g. {'start_line': 1, 'end_line': 3}.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
    children: list[DocumentElement] = Field(default_factory=list)


class CanonicalElementType:
    """Well-known element type names for canonical documents."""

    DOCUMENT = "document"
    SECTION = "section"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    LIST_ITEM = "list_item"
    TASK_LIST = "task_list"
    TASK_LIST_ITEM = "task_list_item"
    CODE = "code"
    TABLE = "table"
    TABLE_ROW = "table_row"
    TABLE_CELL = "table_cell"
    TABLE_HEAD = "table_head"
    TABLE_BODY = "table_body"
    QUOTE = "quote"
    IMAGE = "image"
    LINK = "link"
    HTML = "html"
    FOOTNOTE = "footnote"
    FOOTNOTE_BLOCK = "footnote_block"
    METADATA = "metadata"
    PAGE_BREAK = "page_break"
    FORMULA = "formula"
    CONTAINER = "container"
    OTHER = "other"


@dataclass
class CanonicalValidationResult:
    """Outcome of validating a ``CanonicalDocument``."""

    ok: bool
    diagnostics: list[Diagnostic] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.ok


class CanonicalDocument(DocumentElement):
    """Parser-agnostic, normalized representation of a source document.

    A ``CanonicalDocument`` is the single output that every document reader is
    expected to produce. It carries enough structure for the segmentation
    engine to emit standard ``Segment`` objects without parser-specific
    knowledge.
    """

    type: str = CanonicalElementType.DOCUMENT
    source_uri: str | None = None
    mime_type: str | None = None
    language: str | None = None
    title: str | None = None

    @classmethod
    def empty(cls, source_uri: str | None = None, mime_type: str | None = None) -> CanonicalDocument:
        """Return an empty canonical document."""
        return cls(source_uri=source_uri, mime_type=mime_type, children=[])


class DocumentReader(Reader):
    """Base class for readers that produce a ``CanonicalDocument``.

    Subclasses should implement ``read_canonical`` and return a
    ``CanonicalDocument``. The default ``read`` wraps the result in a
    ``NormalizedContent`` with ``kind=ContentKind.DOCUMENT`` so the document
    plugs directly into the existing extraction pipeline.
    """

    @abstractmethod
    def read_canonical(
        self,
        artifact: Artifact,
        content: bytes | str,
        context: Any | None = None,
    ) -> CanonicalDocument:
        """Parse ``content`` and return a ``CanonicalDocument``."""
        ...

    def read(
        self,
        artifact: Artifact,
        content: bytes | str,
        context: Any | None = None,
    ) -> NormalizedContent:
        """Return a ``NormalizedContent`` wrapping the canonical document."""
        document = self.read_canonical(artifact, content, context)
        if not document.mime_type:
            document.mime_type = artifact.mime_type
        if not document.source_uri:
            document.source_uri = artifact.relative_path or artifact.name
        return NormalizedContent(
            kind=ContentKind.DOCUMENT,
            mime_type=artifact.mime_type,
            content=document,
            source_uri=document.source_uri or artifact.relative_path or artifact.name,
            language=document.language,
            metadata=document.metadata,
        )


class CanonicalValidator:
    """Validate a ``CanonicalDocument`` before extraction.

    Enforces the structural contract that every document reader must satisfy:
    a well-formed root, required metadata, valid element hierarchy, unique
    element IDs, and no unsupported structural errors. Malformed documents are
    rejected with diagnostics before any segmenter or extractor runs.
    """

    # Parent element type -> allowed child types (None means any child is allowed).
    _VALID_CHILDREN: dict[str, set[str] | None] = {
        CanonicalElementType.DOCUMENT: {
            CanonicalElementType.SECTION,
            CanonicalElementType.HEADING,
            CanonicalElementType.PARAGRAPH,
            CanonicalElementType.LIST,
            CanonicalElementType.CODE,
            CanonicalElementType.TABLE,
            CanonicalElementType.QUOTE,
            CanonicalElementType.IMAGE,
            CanonicalElementType.LINK,
            CanonicalElementType.HTML,
            CanonicalElementType.FOOTNOTE,
            CanonicalElementType.FOOTNOTE_BLOCK,
            CanonicalElementType.METADATA,
            CanonicalElementType.PAGE_BREAK,
            CanonicalElementType.FORMULA,
            CanonicalElementType.CONTAINER,
            CanonicalElementType.OTHER,
        },
        CanonicalElementType.SECTION: {
            CanonicalElementType.SECTION,
            CanonicalElementType.HEADING,
            CanonicalElementType.PARAGRAPH,
            CanonicalElementType.LIST,
            CanonicalElementType.CODE,
            CanonicalElementType.TABLE,
            CanonicalElementType.QUOTE,
            CanonicalElementType.IMAGE,
            CanonicalElementType.LINK,
            CanonicalElementType.HTML,
            CanonicalElementType.PAGE_BREAK,
            CanonicalElementType.FORMULA,
            CanonicalElementType.CONTAINER,
            CanonicalElementType.OTHER,
        },
        CanonicalElementType.LIST: {
            CanonicalElementType.LIST_ITEM,
            CanonicalElementType.TASK_LIST_ITEM,
            CanonicalElementType.CONTAINER,
            CanonicalElementType.OTHER,
        },
        CanonicalElementType.TASK_LIST: {
            CanonicalElementType.TASK_LIST_ITEM,
            CanonicalElementType.LIST_ITEM,
            CanonicalElementType.CONTAINER,
            CanonicalElementType.OTHER,
        },
        CanonicalElementType.LIST_ITEM: None,
        CanonicalElementType.TASK_LIST_ITEM: None,
        CanonicalElementType.TABLE: {
            CanonicalElementType.TABLE_ROW,
            CanonicalElementType.TABLE_HEAD,
            CanonicalElementType.TABLE_BODY,
            CanonicalElementType.CONTAINER,
            CanonicalElementType.OTHER,
        },
        CanonicalElementType.TABLE_ROW: {
            CanonicalElementType.TABLE_CELL,
            CanonicalElementType.CONTAINER,
            CanonicalElementType.OTHER,
        },
        CanonicalElementType.TABLE_HEAD: {
            CanonicalElementType.TABLE_ROW,
            CanonicalElementType.CONTAINER,
            CanonicalElementType.OTHER,
        },
        CanonicalElementType.TABLE_BODY: {
            CanonicalElementType.TABLE_ROW,
            CanonicalElementType.CONTAINER,
            CanonicalElementType.OTHER,
        },
        CanonicalElementType.FOOTNOTE_BLOCK: {
            CanonicalElementType.FOOTNOTE,
            CanonicalElementType.CONTAINER,
            CanonicalElementType.OTHER,
        },
        CanonicalElementType.QUOTE: None,
        CanonicalElementType.CONTAINER: None,
        CanonicalElementType.OTHER: None,
    }

    def validate(
        self,
        document: Any,
        *,
        source_ref: str | None = None,
    ) -> CanonicalValidationResult:
        """Return a validation result for ``document``."""
        diagnostics: list[Diagnostic] = []

        if not isinstance(document, CanonicalDocument):
            diagnostics.append(
                Diagnostic(
                    "error",
                    "invalid_canonical_root",
                    "Expected a CanonicalDocument instance",
                    source_ref=source_ref,
                )
            )
            return CanonicalValidationResult(False, diagnostics)

        if document.type != CanonicalElementType.DOCUMENT:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "invalid_canonical_root_type",
                    f"Expected root type '{CanonicalElementType.DOCUMENT}', got {document.type!r}",
                    source_ref=source_ref,
                )
            )

        if not document.source_uri:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "missing_source_uri",
                    "CanonicalDocument.source_uri is required",
                    source_ref=source_ref,
                )
            )

        if not document.mime_type:
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "missing_mime_type",
                    "CanonicalDocument.mime_type is recommended for future readers",
                    source_ref=source_ref,
                )
            )

        if not isinstance(document.children, (list, tuple)):
            diagnostics.append(
                Diagnostic(
                    "error",
                    "invalid_children",
                    "CanonicalDocument.children must be a sequence of DocumentElement objects",
                    source_ref=source_ref,
                )
            )
            if diagnostics and any(d.level == "error" for d in diagnostics):
                return CanonicalValidationResult(False, diagnostics)

        seen_ids: set[str] = set()
        self._validate_element(
            document,
            seen_ids,
            diagnostics,
            source_ref=source_ref,
            path="root",
            parent_type="",
        )

        if any(d.level == "error" for d in diagnostics):
            return CanonicalValidationResult(False, diagnostics)
        return CanonicalValidationResult(True, diagnostics)

    def _validate_element(
        self,
        element: DocumentElement,
        seen_ids: set[str],
        diagnostics: list[Diagnostic],
        *,
        source_ref: str | None,
        path: str,
        parent_type: str,
    ) -> None:
        if not isinstance(element, DocumentElement):
            diagnostics.append(
                Diagnostic(
                    "error",
                    "invalid_element",
                    f"Element at {path} is not a DocumentElement",
                    source_ref=source_ref,
                )
            )
            return

        if not element.id:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "missing_element_id",
                    f"Element at {path} has no id",
                    source_ref=source_ref,
                )
            )
        elif element.id in seen_ids:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "duplicate_element_id",
                    f"Duplicate element id {element.id!r} at {path}",
                    source_ref=source_ref,
                )
            )
        else:
            seen_ids.add(element.id)

        if not element.type:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "missing_element_type",
                    f"Element at {path} has no type",
                    source_ref=source_ref,
                )
            )

        if not isinstance(element.metadata, dict):
            diagnostics.append(
                Diagnostic(
                    "error",
                    "invalid_metadata",
                    f"Element {path!r} metadata must be a dict",
                    source_ref=source_ref,
                )
            )

        if element.location is not None and not isinstance(element.location, dict):
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "invalid_location",
                    f"Element {path!r} location should be a dict or None",
                    source_ref=source_ref,
                )
            )

        valid_children = self._VALID_CHILDREN.get(parent_type)
        if valid_children is not None and element.type not in valid_children:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "invalid_child_element",
                    f"Element type {element.type!r} is not allowed under {parent_type!r}",
                    source_ref=source_ref,
                )
            )

        # Flag unsupported structural shapes rather than silently ignoring them.
        if element.type not in self._known_element_types():
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "unsupported_element_type",
                    f"Element {path!r} uses an unsupported type {element.type!r}; "
                    "segmenters may skip it",
                    source_ref=source_ref,
                )
            )

        for index, child in enumerate(element.children):
            self._validate_element(
                child,
                seen_ids,
                diagnostics,
                source_ref=source_ref,
                path=f"{path}.{element.type}[{index}]",
                parent_type=element.type,
            )

    def _known_element_types(self) -> set[str]:
        return {
            getattr(CanonicalElementType, attr)
            for attr in dir(CanonicalElementType)
            if not attr.startswith("_")
        }


class CanonicalSegmenter(Segmenter):
    """Segment a ``CanonicalDocument`` into standard ``Segment`` objects.

    This segmenter makes future parser plug-ins work out of the box: any
    ``DocumentReader`` that emits a ``CanonicalDocument`` will be decomposed
    into the same segment types the rest of the pipeline already understands.
    """

    supported_content_kinds = (ContentKind.DOCUMENT,)

    def segment(
        self,
        content: NormalizedContent,
        context: Any | None = None,
    ) -> list[Segment]:
        document = content.content
        if not isinstance(document, CanonicalDocument):
            # Gracefully degrade: if content is not a canonical document, treat
            # it as a raw document segment so the pipeline does not crash.
            return [
                Segment(
                    id=make_id(),
                    type=SegmentType.DOCUMENT,
                    label="document",
                    content=document,
                    location=str(content.source_uri),
                    metadata={"kind": content.kind.value},
                )
            ]
        segments: list[Segment] = []
        for child in document.children:
            segments.extend(self._segment_element(child))
        return segments

    def _segment_element(self, element: DocumentElement) -> list[Segment]:
        segments: list[Segment] = []
        segments.extend(self._segment_self(element))
        for child in element.children:
            segments.extend(self._segment_element(child))
        return segments

    def _segment_self(self, element: DocumentElement) -> list[Segment]:
        element_type = element.type
        location = self._location(element)

        if element_type == CanonicalElementType.HEADING:
            return [
                Segment(
                    id=element.id or make_id(),
                    type=SegmentType.HEADING,
                    label=f"h{element.level}" if element.level else "heading",
                    content=self._text(element),
                    location=location,
                    metadata=element.metadata,
                )
            ]

        if element_type == CanonicalElementType.PARAGRAPH:
            return [
                Segment(
                    id=element.id or make_id(),
                    type=SegmentType.PARAGRAPH,
                    label="paragraph",
                    content=self._text(element),
                    location=location,
                    metadata=element.metadata,
                )
            ]

        if element_type == CanonicalElementType.CODE:
            return [
                Segment(
                    id=element.id or make_id(),
                    type=SegmentType.CODE,
                    label=element.metadata.get("language"),
                    content=element.content or self._text(element),
                    location=location,
                    metadata=element.metadata,
                )
            ]

        if element_type == CanonicalElementType.TABLE:
            rows = self._table_rows(element)
            return [
                Segment(
                    id=element.id or make_id(),
                    type=SegmentType.TABLE,
                    label="table",
                    content=rows,
                    location=location,
                    metadata=element.metadata,
                )
            ]

        if element_type == CanonicalElementType.LIST:
            return [
                Segment(
                    id=element.id or make_id(),
                    type=SegmentType.LIST,
                    label="list",
                    content=[self._text(item) for item in element.children],
                    location=location,
                    metadata={"ordered": bool(element.metadata.get("ordered")), **element.metadata},
                )
            ]

        if element_type == CanonicalElementType.TASK_LIST:
            items = [
                {
                    "text": self._text(item),
                    "checked": bool(item.metadata.get("checked", False)),
                }
                for item in element.children
            ]
            return [
                Segment(
                    id=element.id or make_id(),
                    type=SegmentType.TASK_LIST,
                    label="task_list",
                    content=items,
                    location=location,
                    metadata={"ordered": False, **element.metadata},
                )
            ]

        if element_type == CanonicalElementType.QUOTE:
            return [
                Segment(
                    id=element.id or make_id(),
                    type=SegmentType.QUOTE,
                    label="quote",
                    content=self._text(element),
                    location=location,
                    metadata=element.metadata,
                )
            ]

        if element_type == CanonicalElementType.IMAGE:
            return [
                Segment(
                    id=element.id or make_id(),
                    type=SegmentType.IMAGE,
                    label=element.metadata.get("src") or "image",
                    content=element.content,
                    location=location,
                    metadata=element.metadata,
                )
            ]

        if element_type == CanonicalElementType.LINK:
            return [
                Segment(
                    id=element.id or make_id(),
                    type=SegmentType.LINK,
                    label=element.metadata.get("href") or "link",
                    content=self._text(element),
                    location=location,
                    metadata=element.metadata,
                )
            ]

        if element_type == CanonicalElementType.HTML:
            return [
                Segment(
                    id=element.id or make_id(),
                    type=SegmentType.HTML,
                    label="html",
                    content=element.content or self._text(element),
                    location=location,
                    metadata=element.metadata,
                )
            ]

        if element_type == CanonicalElementType.FOOTNOTE:
            return [
                Segment(
                    id=element.id or make_id(),
                    type=SegmentType.FOOTNOTE,
                    label=element.metadata.get("label"),
                    content=element.content or self._text(element),
                    location=location,
                    metadata=element.metadata,
                )
            ]

        if element_type == CanonicalElementType.METADATA:
            return [
                Segment(
                    id=element.id or make_id(),
                    type=SegmentType.METADATA,
                    label="metadata",
                    content=element.content or element.metadata,
                    location=location,
                    metadata=element.metadata,
                )
            ]

        if element_type in {
            CanonicalElementType.SECTION,
            CanonicalElementType.DOCUMENT,
            CanonicalElementType.FOOTNOTE_BLOCK,
            CanonicalElementType.CONTAINER,
            CanonicalElementType.LIST_ITEM,
            CanonicalElementType.TABLE_ROW,
            CanonicalElementType.TABLE_CELL,
        }:
            # Container elements are not emitted as segments themselves; their
            # children are walked recursively.
            return []

        # Catch-all for unknown element types.
        return [
            Segment(
                id=element.id or make_id(),
                type=SegmentType.OTHER,
                label=element_type,
                content=element.content,
                location=location,
                metadata=element.metadata,
            )
        ]

    @staticmethod
    def _text(element: DocumentElement) -> str:
        if isinstance(element.content, str):
            return element.content
        if element.children:
            parts: list[str] = []
            for child in element.children:
                if child.type in (CanonicalElementType.IMAGE, CanonicalElementType.HTML):
                    parts.append(str(child.content))
                else:
                    parts.append(CanonicalSegmenter._text(child))
            return " ".join(part for part in parts if part)
        return ""

    @staticmethod
    def _table_rows(element: DocumentElement) -> list[list[str]]:
        rows: list[list[str]] = []
        for row in element.children:
            if row.type == CanonicalElementType.TABLE_ROW:
                rows.append(
                    [CanonicalSegmenter._text(cell) for cell in row.children]
                )
        if not rows and element.content is not None:
            # Some readers may store rows directly in content.
            rows = element.content if isinstance(element.content, list) else []
        return rows

    @staticmethod
    def _location(element: DocumentElement) -> str | None:
        if not element.location:
            return None
        start = element.location.get("start_line")
        end = element.location.get("end_line")
        if start is not None and end is not None and start != end:
            return f"lines {start}-{end}"
        if start is not None:
            return f"line {start}"
        return None


class MarkdownCanonicalMapper:
    """Map the existing Markdown AST into the Canonical Document Model.

    This mapper preserves all existing Markdown-specific behavior while making
    Markdown a first-class producer of the canonical model. Future readers for
    DOCX, PDF, HTML, etc. can follow the same pattern.
    """

    def map(self, markdown_document: Any) -> CanonicalDocument:
        """Convert a ``MarkdownDocument`` to a ``CanonicalDocument``."""
        from akwb.extraction.markdown import MarkdownDocument

        if not isinstance(markdown_document, MarkdownDocument):
            raise TypeError("Expected MarkdownDocument")

        root = CanonicalDocument(
            source_uri=markdown_document.source_uri,
            mime_type="text/markdown",
            language="markdown",
            metadata=dict(markdown_document.metadata or {}),
            children=[self._map_node(child) for child in markdown_document.children],
        )
        return root

    def _map_node(self, node: Any) -> DocumentElement:
        from akwb.extraction.markdown import MarkdownNode

        if not isinstance(node, MarkdownNode):
            raise TypeError("Expected MarkdownNode")

        children = [self._map_node(child) for child in node.children]

        # Map Markdown AST node types to canonical element types.
        element_type = self._canonical_type(node.type)
        content: Any = node.content
        metadata: dict[str, Any] = dict(node.metadata or {})

        if node.attrs:
            metadata.update({"attrs": dict(node.attrs)})

        if element_type == CanonicalElementType.TASK_LIST:
            metadata["ordered"] = False
            children = [self._map_task_item(child) for child in children]

        return DocumentElement(
            id=getattr(node, "id", None) or make_id(),
            type=element_type,
            level=node.level,
            content=content,
            location=dict(node.location) if node.location else None,
            metadata=metadata,
            children=children,
        )

    def _map_task_item(self, node: Any) -> DocumentElement:
        metadata = dict(node.metadata or {})
        metadata.setdefault("task", True)
        metadata.setdefault("checked", metadata.get("checked", False))
        return DocumentElement(
            id=getattr(node, "id", None) or make_id(),
            type=CanonicalElementType.TASK_LIST_ITEM,
            level=node.level,
            content=node.content,
            location=dict(node.location) if node.location else None,
            metadata=metadata,
            children=[self._map_node(child) for child in node.children],
        )

    @staticmethod
    def _canonical_type(node_type: str) -> str:
        mapping = {
            "document": CanonicalElementType.DOCUMENT,
            "heading": CanonicalElementType.HEADING,
            "paragraph": CanonicalElementType.PARAGRAPH,
            "list": CanonicalElementType.LIST,
            "list_item": CanonicalElementType.LIST_ITEM,
            "task_list": CanonicalElementType.TASK_LIST,
            "task_list_item": CanonicalElementType.TASK_LIST_ITEM,
            "code": CanonicalElementType.CODE,
            "table": CanonicalElementType.TABLE,
            "table_row": CanonicalElementType.TABLE_ROW,
            "table_cell": CanonicalElementType.TABLE_CELL,
            "quote": CanonicalElementType.QUOTE,
            "image": CanonicalElementType.IMAGE,
            "link": CanonicalElementType.LINK,
            "html": CanonicalElementType.HTML,
            "footnote": CanonicalElementType.FOOTNOTE,
            "footnote_block": CanonicalElementType.FOOTNOTE_BLOCK,
            "metadata": CanonicalElementType.METADATA,
        }
        return mapping.get(node_type, CanonicalElementType.OTHER)


DocumentElement.model_rebuild()
CanonicalDocument.model_rebuild()
