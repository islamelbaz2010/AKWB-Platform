"""Built-in segmenters for the extraction pipeline."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from akwb.extraction.models import ContentKind, Segment, SegmentType
from akwb.extraction.plugins import Segmenter
from akwb.types import Diagnostic, make_id

if TYPE_CHECKING:
    from akwb.extraction.models import NormalizedContent
    from akwb.extraction.pipeline import ExtractionContext


def _line_number(text: str, index: int) -> int:
    """Return the 1-based line number for ``index`` in ``text``."""
    return text[:index].count("\n") + 1


class HeadingSegmenter(Segmenter):
    """Detect atx and setext headings in text."""

    supported_content_kinds = (ContentKind.TEXT,)

    def segment(
        self,
        content: NormalizedContent,
        context: ExtractionContext | None = None,
    ) -> list[Segment]:
        text = str(content.content)
        segments: list[Segment] = []
        atx = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+#*)?$", re.MULTILINE)
        for match in atx.finditer(text):
            level = len(match.group(1))
            title = match.group(2).strip()
            segments.append(
                Segment(
                    id=make_id(),
                    type=SegmentType.HEADING,
                    label=f"h{level}",
                    content=title,
                    location=f"line {_line_number(text, match.start())}",
                )
            )

        lines = text.splitlines()
        i = 0
        while i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            if re.fullmatch(r"=+", next_line):
                segments.append(
                    Segment(
                        id=make_id(),
                        type=SegmentType.HEADING,
                        label="h1",
                        content=lines[i].strip(),
                        location=f"line {i + 1}",
                    )
                )
                i += 2
                continue
            if re.fullmatch(r"-+", next_line):
                segments.append(
                    Segment(
                        id=make_id(),
                        type=SegmentType.HEADING,
                        label="h2",
                        content=lines[i].strip(),
                        location=f"line {i + 1}",
                    )
                )
                i += 2
                continue
            i += 1

        return segments


class ParagraphSegmenter(Segmenter):
    """Split text into paragraphs, skipping structural blocks."""

    supported_content_kinds = (ContentKind.TEXT,)

    def segment(
        self,
        content: NormalizedContent,
        context: ExtractionContext | None = None,
    ) -> list[Segment]:
        text = str(content.content)
        segments: list[Segment] = []
        for match in re.finditer(r"(?:^|\n\s*\n)(.*?)(?=\n\s*\n|\Z)", text, re.DOTALL):
            block = match.group(1).strip()
            if not block or self._is_structural_block(block):
                continue
            start = match.start(1)
            segments.append(
                Segment(
                    id=make_id(),
                    type=SegmentType.PARAGRAPH,
                    content=block,
                    location=f"line {_line_number(text, start)}",
                )
            )
        return segments

    @staticmethod
    def _is_structural_block(block: str) -> bool:
        first = block.lstrip()
        if first.startswith("#"):
            return True
        if first.startswith("```") or first.endswith("```"):
            return True
        lines = block.splitlines()
        return bool(all("|" in line for line in lines) and any("-" in line for line in lines))


class CodeSegmenter(Segmenter):
    """Detect fenced code blocks in text."""

    supported_content_kinds = (ContentKind.TEXT,)

    def segment(
        self,
        content: NormalizedContent,
        context: ExtractionContext | None = None,
    ) -> list[Segment]:
        text = str(content.content)
        segments: list[Segment] = []
        pattern = re.compile(r"```[ \t]*(\w+)?[ \t]*\r?\n(.*?)```", re.DOTALL)
        for i, match in enumerate(pattern.finditer(text), start=1):
            language = (match.group(1) or "").strip()
            code = match.group(2)
            segments.append(
                Segment(
                    id=make_id(),
                    type=SegmentType.CODE,
                    label=language or None,
                    content=code.strip("\n"),
                    location=f"code block {i} (line {_line_number(text, match.start())})",
                )
            )
        return segments


class TableSegmenter(Segmenter):
    """Detect markdown-style tables in text."""

    supported_content_kinds = (ContentKind.TEXT,)

    def segment(
        self,
        content: NormalizedContent,
        context: ExtractionContext | None = None,
    ) -> list[Segment]:
        text = str(content.content)
        segments: list[Segment] = []
        lines = text.splitlines()

        i = 0
        while i < len(lines):
            if self._is_table_row(lines[i]):
                start = i
                while i < len(lines) and self._is_table_row(lines[i]):
                    i += 1
                end = i
                rows = self._parse_table_block(lines[start:end])
                if rows:
                    segments.append(
                        Segment(
                            id=make_id(),
                            type=SegmentType.TABLE,
                            label="table",
                            content=rows,
                            location=f"lines {start + 1}-{end}",
                        )
                    )
                continue
            i += 1

        return segments

    @staticmethod
    def _is_table_row(line: str) -> bool:
        return "|" in line

    @staticmethod
    def _is_separator(line: str) -> bool:
        return "|" in line and all(c in "-:| \t" for c in line) and "-" in line

    @staticmethod
    def _parse_table_block(lines: list[str]) -> list[list[str]]:
        rows: list[list[str]] = []
        for line in lines:
            if TableSegmenter._is_separator(line):
                continue
            cells = [cell.strip() for cell in line.split("|")]
            if line.startswith("|") and cells and cells[0] == "":
                cells = cells[1:]
            if line.endswith("|") and cells and cells[-1] == "":
                cells = cells[:-1]
            if cells:
                rows.append(cells)
        return rows


class StructuralSegmenter(Segmenter):
    """Segment structured (JSON/YAML) content into key/value or item segments."""

    supported_content_kinds = (ContentKind.STRUCTURED,)

    def segment(
        self,
        content: NormalizedContent,
        context: ExtractionContext | None = None,
    ) -> list[Segment]:
        data = content.content
        segments: list[Segment] = []
        if isinstance(data, dict):
            for key, value in data.items():
                segments.extend(self._segments_from_value(key, value))
        elif isinstance(data, list):
            for index, item in enumerate(data):
                segments.extend(self._segments_from_value(f"[{index}]", item))
        else:
            segments.append(
                Segment(
                    id=make_id(),
                    type=SegmentType.STRUCTURAL,
                    label="root",
                    content=data,
                    location="root",
                )
            )
        return segments

    def _segments_from_value(self, key: str, value: Any) -> list[Segment]:
        segments: list[Segment] = []
        if isinstance(value, dict):
            segments.append(
                Segment(
                    id=make_id(),
                    type=SegmentType.STRUCTURAL,
                    label=key,
                    content=value,
                    location=key,
                )
            )
            for nested_key, nested_value in value.items():
                segments.extend(
                    self._segments_from_value(f"{key}.{nested_key}", nested_value)
                )
        elif isinstance(value, list):
            for index, item in enumerate(value):
                segments.extend(self._segments_from_value(f"{key}[{index}]", item))
        else:
            segments.append(
                Segment(
                    id=make_id(),
                    type=SegmentType.STRUCTURAL,
                    label=key,
                    content=value,
                    location=key,
                )
            )
        return segments


class SemanticSegmenter(Segmenter):
    """Split text into sentence-level semantic segments."""

    supported_content_kinds = (ContentKind.TEXT,)

    def segment(
        self,
        content: NormalizedContent,
        context: ExtractionContext | None = None,
    ) -> list[Segment]:
        text = str(content.content)
        segments: list[Segment] = []
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        line = 1
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            segments.append(
                Segment(
                    id=make_id(),
                    type=SegmentType.SEMANTIC,
                    content=sentence,
                    location=f"line {line}",
                )
            )
            line += sentence.count("\n") + 1
        return segments


class AdaptiveSegmenter(Segmenter):
    """Choose and run appropriate segmenters based on content kind."""

    supported_content_kinds = (
        ContentKind.TEXT,
        ContentKind.STRUCTURED,
        ContentKind.DOCUMENT,
        ContentKind.BINARY,
        ContentKind.MULTIMODAL,
    )

    def __init__(self, segmenters: list[Segmenter] | None = None) -> None:
        self.segmenters = segmenters or []

    def add_segmenter(self, segmenter: Segmenter) -> None:
        """Register an additional segmenter, prepending so plugins take priority."""
        self.segmenters.insert(0, segmenter)

    def segment(
        self,
        content: NormalizedContent,
        context: ExtractionContext | None = None,
    ) -> list[Segment]:
        segments: list[Segment] = []
        for segmenter in self.segmenters:
            if segmenter.can_segment(content.kind):
                try:
                    segments.extend(segmenter.segment(content, context))
                except (ValueError, TypeError, RuntimeError, OSError) as exc:
                    if context is not None:
                        context.emit(
                            Diagnostic(
                                "warning",
                                "segmenter_failed",
                                f"Segmenter {type(segmenter).__name__} failed: {exc}",
                            )
                        )
        return segments
