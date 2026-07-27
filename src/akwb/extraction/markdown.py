"""Enterprise Markdown AST parser for the extraction pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import yaml
from markdown_it import MarkdownIt
from mdit_py_plugins.gfm import gfm_plugin
from pydantic import BaseModel, ConfigDict, Field

from akwb.domain.models import Artifact
from akwb.extraction.document import CanonicalDocument, DocumentReader, MarkdownCanonicalMapper
from akwb.extraction.models import (
    ContentKind,
    NormalizedContent,
    Segment,
    SegmentType,
)
from akwb.extraction.plugins import Segmenter
from akwb.types import make_id


class MarkdownNode(BaseModel):
    """A node in the normalized Markdown AST."""

    model_config = ConfigDict(extra="allow")

    type: str
    tag: str | None = None
    level: int | None = None
    content: Any = None
    attrs: dict[str, Any] | None = None
    location: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    children: list[MarkdownNode] = Field(default_factory=list)


class MarkdownDocument(MarkdownNode):
    """Root of a parsed Markdown document."""

    type: str = "document"
    source_uri: str | None = None


class MarkdownParser:
    """Parse Markdown into a typed AST using markdown-it-py."""

    def __init__(self) -> None:
        self.md = MarkdownIt()
        self.md.use(gfm_plugin, front_matter=True)

    def parse(self, text: str, source_uri: str | None = None) -> MarkdownDocument:
        """Return a ``MarkdownDocument`` for ``text``."""
        tokens = self.md.parse(text)
        return self._build_tree(tokens, text, source_uri)

    def _build_tree(
        self,
        tokens: list[Any],
        source_text: str,
        source_uri: str | None,
    ) -> MarkdownDocument:
        root = MarkdownDocument(source_uri=source_uri)
        stack: list[MarkdownNode] = [root]

        for token in tokens:
            if token.nesting == 1:
                node = self._open_node(token, source_text)
                stack[-1].children.append(node)
                stack.append(node)
            elif token.nesting == -1:
                node = stack.pop()
                self._finalize_node(node)
            else:
                self._self_closing(token, stack[-1], source_text, root)

        return root

    def _open_node(self, token: Any, source_text: str) -> MarkdownNode:
        node_type = self._node_type_for_open(token)
        node = MarkdownNode(
            type=node_type,
            tag=token.tag or None,
            location=self._token_location(token),
            attrs=self._token_attrs(token),
        )

        if node.type == "heading" and node.tag:
            node.level = int(node.tag[1])

        if node.type in ("list_item", "task_list_item"):
            node.metadata = node.metadata or {}
            node.metadata["task"] = node.type == "task_list_item"
            node.metadata["checked"] = self._task_checked(token, source_text)

        if node.type == "footnote":
            node.metadata = node.metadata or {}
            meta = getattr(token, "meta", {}) or {}
            node.metadata["label"] = meta.get("label")

        if node.type == "list" and node.attrs and node.tag == "ol":
            node.metadata = node.metadata or {}
            start = node.attrs.get("start", "1")
            try:
                node.metadata["start"] = int(start)
            except ValueError:
                node.metadata["start"] = 1
            node.metadata["ordered"] = True
        elif node.type == "list":
            node.metadata = node.metadata or {}
            node.metadata["ordered"] = False

        return node

    @staticmethod
    def _node_type_for_open(token: Any) -> str:
        token_type = token.type
        if token_type == "heading_open":
            return "heading"
        if token_type == "paragraph_open":
            return "paragraph"
        if token_type == "bullet_list_open":
            return "list"
        if token_type == "ordered_list_open":
            return "list"
        if token_type == "list_item_open":
            if token.attrs and "class" in token.attrs:
                class_value = token.attrs["class"]
                if isinstance(class_value, str) and "task-list-item" in class_value:
                    return "task_list_item"
                if isinstance(class_value, list) and any(
                    "task-list-item" in str(v) for v in class_value
                ):
                    return "task_list_item"
            return "list_item"
        if token_type == "blockquote_open":
            return "quote"
        if token_type == "table_open":
            return "table"
        if token_type == "thead_open":
            return "table_head"
        if token_type == "tbody_open":
            return "table_body"
        if token_type == "tr_open":
            return "table_row"
        if token_type in ("th_open", "td_open"):
            return "table_cell"
        if token_type == "footnote_block_open":
            return "footnote_block"
        if token_type == "footnote_open":
            return "footnote"
        return token_type.replace("_open", "") or token.tag or "unknown"

    @staticmethod
    def _token_attrs(token: Any) -> dict[str, Any] | None:
        attrs = getattr(token, "attrs", None)
        if not attrs:
            return None
        if isinstance(attrs, dict):
            return dict(attrs)
        return {str(k): str(v) for k, v in attrs}

    @staticmethod
    def _token_location(token: Any) -> dict[str, int] | None:
        token_map = getattr(token, "map", None)
        if not token_map:
            return None
        start, end = token_map
        return {"start_line": start + 1, "end_line": end}

    @staticmethod
    def _task_checked(token: Any, source_text: str) -> bool | None:
        if "task-list-item" not in str(token.attrs):
            return None
        loc = MarkdownParser._token_location(token)
        if not loc:
            return None
        line_index = loc["start_line"] - 1
        lines = source_text.splitlines()
        if 0 <= line_index < len(lines):
            stripped = lines[line_index].lstrip()
            return stripped.startswith(("- [x]", "* [x]"))
        return None

    def _self_closing(
        self,
        token: Any,
        parent: MarkdownNode,
        source_text: str,
        root: MarkdownDocument,
    ) -> None:
        if token.type == "inline":
            parent.children.extend(self._process_inline(token))
            return

        if token.type == "fence":
            language = (token.info or "").strip().split()[0] if token.info else None
            node = MarkdownNode(
                type="code",
                tag="code",
                content=token.content,
                location=self._token_location(token),
                metadata={"language": language, "block": True},
            )
            parent.children.append(node)
            return

        if token.type == "html_block":
            node = MarkdownNode(
                type="html",
                content=token.content,
                location=self._token_location(token),
            )
            parent.children.append(node)
            return

        if token.type == "front_matter":
            node = self._front_matter_node(token)
            parent.children.append(node)
            if isinstance(node.content, dict):
                root.metadata.update(node.content)
            return

        if token.type == "hr":
            parent.children.append(
                MarkdownNode(
                    type="thematic_break",
                    location=self._token_location(token),
                )
            )
            return

        if token.type in ("footnote_anchor",):
            return

        parent.children.append(
            MarkdownNode(
                type=token.type,
                tag=token.tag or None,
                content=getattr(token, "content", None) or None,
                location=self._token_location(token),
                attrs=self._token_attrs(token),
            )
        )

    def _front_matter_node(self, token: Any) -> MarkdownNode:
        raw = token.content
        content: Any = raw
        metadata: dict[str, Any] = {"format": "front_matter"}
        try:
            content = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            metadata["parse_error"] = str(exc)
        return MarkdownNode(
            type="metadata",
            content=content,
            location=self._token_location(token),
            metadata=metadata,
        )

    def _process_inline(self, token: Any) -> list[MarkdownNode]:
        root = MarkdownNode(type="inline_root")
        stack: list[MarkdownNode] = [root]

        def _flush_text() -> None:
            top = stack[-1]
            if isinstance(top.content, str) and top.content:
                top.children.append(MarkdownNode(type="text", content=top.content))
                top.content = ""

        for child in token.children or []:
            child_type = child.type

            if child_type == "text":
                stack[-1].content = (stack[-1].content or "") + (child.content or "")
            elif child_type == "softbreak":
                stack[-1].content = (stack[-1].content or "") + " "
            elif child_type == "hardbreak":
                stack[-1].content = (stack[-1].content or "") + "\n"
            elif child_type == "code_inline":
                _flush_text()
                stack[-1].children.append(
                    MarkdownNode(
                        type="code",
                        content=child.content,
                        metadata={"inline": True},
                    )
                )
            elif child_type == "html_inline":
                _flush_text()
                stack[-1].children.append(
                    MarkdownNode(
                        type="html",
                        content=child.content,
                        metadata={"inline": True},
                    )
                )
            elif child_type == "image":
                _flush_text()
                attrs = self._token_attrs(child) or {}
                stack[-1].children.append(
                    MarkdownNode(
                        type="image",
                        content=child.content,
                        attrs=attrs,
                        metadata={"title": attrs.get("title")},
                    )
                )
            elif child_type.endswith("_open"):
                _flush_text()
                if child_type == "link_open":
                    attrs = self._token_attrs(child) or {}
                    node = MarkdownNode(
                        type="link",
                        tag=child.tag or "a",
                        attrs=attrs,
                        metadata={"title": attrs.get("title")},
                    )
                else:
                    node = MarkdownNode(
                        type="text",
                        tag=child.tag,
                        metadata={"style": child.tag or child.type.replace("_open", "")},
                    )
                stack.append(node)
            elif child_type.endswith("_close"):
                if len(stack) > 1:
                    node = stack.pop()
                    _flush_text_for_node(node)
                    if node.type == "link":
                        node.content = _node_text(node)
                    stack[-1].children.append(node)
            else:
                # Fallback for unknown inline tokens.
                stack[-1].content = (stack[-1].content or "") + (child.content or "")

        _flush_text()
        return root.children

    def _finalize_node(self, node: MarkdownNode) -> None:
        if node.type == "table":
            node.content = _table_rows(node)
        elif node.type == "table_row":
            node.content = [
                cell.content
                for cell in node.children
                if cell.type == "table_cell"
            ]
        elif node.type == "table_cell" or node.type == "link" or node.type in ("heading", "paragraph", "quote", "footnote"):
            node.content = _node_text(node)
        elif node.type in ("list_item", "task_list_item"):
            node.content = _item_text(node)
            if node.type == "task_list_item":
                node.metadata = node.metadata or {}
                node.metadata["checked"] = node.metadata.get("checked", False)
        elif node.type in ("list",):
            node.content = [
                _item_text(item)
                for item in node.children
                if item.type in ("list_item", "task_list_item")
            ]


def _flush_text_for_node(node: MarkdownNode) -> None:
    if isinstance(node.content, str) and node.content:
        node.children.append(MarkdownNode(type="text", content=node.content))
        node.content = ""


def _node_text(node: MarkdownNode) -> str:
    """Return the plain text content of ``node`` and its inline children."""
    if node.type == "link" and not node.content and node.children:
        return "".join(_node_text(child) for child in node.children if child.type != "html")

    if node.type == "text" and node.children:
        parts: list[str] = [node.content or ""]
        for child in node.children:
            if child.type == "link" or child.type in ("code", "image"):
                parts.append(str(child.content or ""))
            elif child.type == "html":
                continue
            elif child.type == "text":
                parts.append(_node_text(child))
        return "".join(parts)

    if isinstance(node.content, str):
        if node.children:
            # ``content`` already includes child text (e.g. a finalized link).
            return node.content
        return node.content

    parts = []
    for child in node.children:
        if child.type in {"list", "quote", "table", "html", "metadata", "thematic_break"}:
            continue
        if child.type == "image":
            parts.append(str(child.content or ""))
        else:
            parts.append(_node_text(child))
    return "".join(parts)


def _item_text(item: MarkdownNode) -> str:
    """Return the first paragraph-level text of a list or quote item."""
    parts: list[str] = []
    for child in item.children:
        if child.type in ("paragraph", "heading") or child.type == "text":
            parts.append(_node_text(child))
        elif child.type in ("list", "quote"):
            # Nested lists are represented by their own list segment.
            continue
    return " ".join(parts)


def _table_rows(table: MarkdownNode) -> list[list[Any]]:
    """Return a list of rows with cell strings from a table node."""
    rows: list[list[Any]] = []
    for child in table.children:
        if child.type == "table_row":
            rows.append(child.content if isinstance(child.content, list) else [])
        elif child.type in ("table_head", "table_body"):
            for row in child.children:
                if row.type == "table_row":
                    rows.append(row.content if isinstance(row.content, list) else [])
    return rows


class MarkdownASTVisitor(ABC):
    """Base visitor for ``MarkdownNode`` trees."""

    def visit(self, node: MarkdownNode) -> None:
        """Dispatch to a type-specific visitor method."""
        method = getattr(self, f"visit_{node.type}", self.visit_default)
        method(node)

    @abstractmethod
    def visit_default(self, node: MarkdownNode) -> None:
        """Handle node types without a dedicated visitor method."""


class MarkdownASTWalker:
    """Depth-first walker over a ``MarkdownNode`` tree."""

    def walk(self, node: MarkdownNode, visitor: MarkdownASTVisitor) -> None:
        """Visit ``node`` and all descendants."""
        visitor.visit(node)
        for child in node.children:
            self.walk(child, visitor)


class MarkdownASTMapper:
    """Map a parsed Markdown AST to ``NormalizedContent``."""

    def __init__(self, parser: MarkdownParser | None = None) -> None:
        self.parser = parser or MarkdownParser()

    def map(
        self,
        text: str,
        artifact: Artifact,
        source_uri: str | None = None,
    ) -> NormalizedContent:
        """Return a ``NormalizedContent`` wrapping the Markdown AST."""
        document = self.parser.parse(text, source_uri=source_uri)
        return NormalizedContent(
            kind=ContentKind.MARKDOWN,
            mime_type=artifact.mime_type,
            content=document,
            source_uri=source_uri or artifact.relative_path or artifact.name,
            encoding="utf-8",
            language=None,
            metadata={"parser": "markdown-it-py", "gfm": True},
        )


class MarkdownReader(DocumentReader):
    """Reader plugin that parses Markdown artifacts into a Canonical Document.

    Markdown now enters the extraction pipeline through the Canonical Document
    Model, the same path that future DOCX, PDF, HTML, and email readers will use.
    """

    supported_mime_types = (
        "text/markdown",
        "text/x-markdown",
    )

    def __init__(self, parser: MarkdownParser | None = None) -> None:
        self._parser = parser or MarkdownParser()
        self._mapper = MarkdownCanonicalMapper()

    def can_read(self, mime_type: str) -> bool:
        return mime_type in self.supported_mime_types

    def read_canonical(
        self,
        artifact: Artifact,
        content: bytes | str,
        context: Any | None = None,
    ) -> CanonicalDocument:
        text = content.decode("utf-8") if isinstance(content, bytes) else content
        source_uri = artifact.relative_path or artifact.name
        markdown_document = self._parser.parse(text, source_uri=source_uri)
        canonical_document = self._mapper.map(markdown_document)
        if not canonical_document.source_uri:
            canonical_document.source_uri = source_uri
        project_id = getattr(context, "project_id", None)
        if project_id:
            canonical_document.metadata["project_id"] = project_id
        return canonical_document


class MarkdownSegmenter(Segmenter):
    """Segment a Markdown AST into typed pipeline segments."""

    supported_content_kinds = (ContentKind.MARKDOWN,)

    def segment(
        self,
        content: NormalizedContent,
        context: Any | None = None,
    ) -> list[Segment]:
        document = content.content
        if not isinstance(document, MarkdownDocument):
            # Fallback: attempt to parse raw text if a reader passed plain text.
            parser = MarkdownParser()
            text = str(document)
            document = parser.parse(text, source_uri=content.source_uri)

        segments: list[Segment] = []
        for node in document.children:
            segments.extend(self._build_segments(node))
        return segments

    def _build_segments(
        self,
        node: MarkdownNode,
        inside_list_or_quote: bool = False,
    ) -> list[Segment]:
        segments: list[Segment] = []

        if node.type == "heading" and not inside_list_or_quote:
            segments.append(self._heading_segment(node))
        elif node.type == "paragraph" and not inside_list_or_quote:
            segments.extend(self._paragraph_segments(node))
        elif node.type == "code" and not inside_list_or_quote:
            segments.append(self._code_segment(node))
        elif node.type == "table":
            segments.append(self._table_segment(node))
        elif node.type == "list":
            segments.append(self._list_segment(node))
            for child in node.children:
                segments.extend(self._build_segments(child, inside_list_or_quote=True))
        elif node.type == "quote":
            segments.append(self._quote_segment(node))
            for child in node.children:
                segments.extend(self._build_segments(child, inside_list_or_quote=True))
        elif node.type == "html" and not inside_list_or_quote:
            segments.append(self._html_segment(node))
        elif node.type == "footnote":
            segments.append(self._footnote_segment(node))
        elif node.type == "metadata":
            segments.append(self._metadata_segment(node))
        elif node.type == "footnote_block":
            for child in node.children:
                segments.extend(self._build_segments(child, inside_list_or_quote))
        elif node.type in ("list_item", "task_list_item"):
            for child in node.children:
                segments.extend(self._build_segments(child, inside_list_or_quote=True))
        elif node.type in (
            "table_head",
            "table_body",
            "table_row",
            "table_cell",
            "inline_root",
            "thematic_break",
        ):
            pass
        else:
            for child in node.children:
                segments.extend(self._build_segments(child, inside_list_or_quote))

        return segments

    def _heading_segment(self, node: MarkdownNode) -> Segment:
        return Segment(
            id=make_id(),
            type=SegmentType.HEADING,
            label=f"h{node.level}" if node.level else "h",
            content=node.content,
            location=self._location(node),
            metadata={"level": node.level},
        )

    def _paragraph_segments(self, node: MarkdownNode) -> list[Segment]:
        # Paragraph with a single image becomes an image segment.
        if len(node.children) == 1 and node.children[0].type == "image":
            return [self._image_segment(node.children[0])]

        return [
            Segment(
                id=make_id(),
                type=SegmentType.PARAGRAPH,
                content=node.content,
                location=self._location(node),
            )
        ]

    def _image_segment(self, node: MarkdownNode) -> Segment:
        attrs = node.attrs or {}
        return Segment(
            id=make_id(),
            type=SegmentType.IMAGE,
            label=attrs.get("src") or "image",
            content=node.content,
            location=self._location(node),
            metadata={"src": attrs.get("src"), "title": node.metadata.get("title")},
        )

    def _code_segment(self, node: MarkdownNode) -> Segment:
        language = node.metadata.get("language")
        return Segment(
            id=make_id(),
            type=SegmentType.CODE,
            label=language,
            content=node.content,
            location=self._location(node),
            metadata={"language": language},
        )

    def _table_segment(self, node: MarkdownNode) -> Segment:
        rows = node.content if isinstance(node.content, list) else []
        return Segment(
            id=make_id(),
            type=SegmentType.TABLE,
            label="table",
            content=rows,
            location=self._location(node),
        )

    def _list_segment(self, node: MarkdownNode) -> Segment:
        item_nodes = [
            child for child in node.children if child.type in ("list_item", "task_list_item")
        ]
        if any(child.type == "task_list_item" for child in item_nodes):
            content = [
                {
                    "text": _item_text(item),
                    "checked": item.metadata.get("checked", False),
                }
                for item in item_nodes
            ]
            return Segment(
                id=make_id(),
                type=SegmentType.TASK_LIST,
                label="task_list",
                content=content,
                location=self._location(node),
                metadata={"ordered": bool(node.metadata.get("ordered"))},
            )

        return Segment(
            id=make_id(),
            type=SegmentType.LIST,
            label="list",
            content=[_item_text(item) for item in item_nodes],
            location=self._location(node),
            metadata={"ordered": bool(node.metadata.get("ordered"))},
        )

    def _quote_segment(self, node: MarkdownNode) -> Segment:
        return Segment(
            id=make_id(),
            type=SegmentType.QUOTE,
            label="quote",
            content=node.content,
            location=self._location(node),
        )

    def _html_segment(self, node: MarkdownNode) -> Segment:
        return Segment(
            id=make_id(),
            type=SegmentType.HTML,
            label="html",
            content=node.content,
            location=self._location(node),
        )

    def _footnote_segment(self, node: MarkdownNode) -> Segment:
        return Segment(
            id=make_id(),
            type=SegmentType.FOOTNOTE,
            label=node.metadata.get("label"),
            content=node.content,
            location=self._location(node),
        )

    def _metadata_segment(self, node: MarkdownNode) -> Segment:
        return Segment(
            id=make_id(),
            type=SegmentType.METADATA,
            label="metadata",
            content=node.content,
            location=self._location(node),
            metadata=node.metadata,
        )

    @staticmethod
    def _location(node: MarkdownNode) -> str | None:
        if node.location:
            start = node.location.get("start_line")
            end = node.location.get("end_line")
            if start and end and start != end:
                return f"lines {start}-{end}"
            if start:
                return f"line {start}"
        return None


MarkdownNode.model_rebuild()
MarkdownDocument.model_rebuild()
