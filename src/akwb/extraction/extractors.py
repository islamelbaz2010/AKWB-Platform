"""Built-in extractors for the extraction pipeline."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from akwb.extraction.models import (
    ExtractionCandidate,
    Segment,
    SegmentType,
)
from akwb.extraction.plugins import Extractor
from akwb.knowledge.models import KnowledgeSource
from akwb.types import make_id

if TYPE_CHECKING:
    from akwb.extraction.pipeline import ExtractionContext


# Lower-case keyword -> built-in knowledge type id.
KEYWORD_TYPE_MAP: dict[str, list[str]] = {
    "decision": ["decision", "adr", "decided"],
    "requirement": ["requirement", "req", "must ", "shall", "should"],
    "risk": ["risk", "threat"],
    "issue": ["issue", "problem", "bug"],
    "task": ["task", "todo", "action item"],
    "goal": ["goal", "objective"],
    "metric": ["metric", "kpi", "measure"],
    "constraint": ["constraint", "limitation"],
    "assumption": ["assumption", "assume"],
    "component": ["component", "module", "class", "function"],
    "technology": ["technology", "library", "framework", "tool"],
    "business_rule": ["business rule", "rule"],
    "stakeholder": ["stakeholder", "customer", "user"],
}


def _classify_text(text: str, default: str = "document") -> str:
    lowered = text.lower()
    for knowledge_type, keywords in KEYWORD_TYPE_MAP.items():
        for keyword in keywords:
            if keyword in lowered:
                return knowledge_type
    return default


class RuleBasedExtractor(Extractor):
    """Rule-based extractor that maps segments to extraction candidates."""

    def extract(
        self,
        segments: list[Segment],
        source: KnowledgeSource,
        context: ExtractionContext | None = None,
    ) -> list[ExtractionCandidate]:
        candidates: list[ExtractionCandidate] = []
        for segment in segments:
            candidates.extend(self._extract_segment(segment, source))
        return candidates

    def _extract_segment(
        self,
        segment: Segment,
        source: KnowledgeSource,
    ) -> list[ExtractionCandidate]:
        content = segment.content
        if not content and content != "":
            return []

        if segment.type == SegmentType.HEADING:
            title = str(content).strip()
            return [ExtractionCandidate(
                id=make_id(),
                knowledge_type=_classify_text(title, default="goal"),
                title=title,
                description=title,
                content=None,
                source=source,
                evidence_excerpt=title,
                evidence_location=segment.location,
                segment=segment,
            )]

        if segment.type in {SegmentType.PARAGRAPH, SegmentType.SEMANTIC}:
            text = str(content).strip()
            title = _first_sentence(text) or text[:80]
            return [ExtractionCandidate(
                id=make_id(),
                knowledge_type=_classify_text(text, default="document"),
                title=title,
                description=text,
                content=text,
                source=source,
                evidence_excerpt=text,
                evidence_location=segment.location,
                segment=segment,
            )]

        if segment.type == SegmentType.CODE:
            code = str(content)
            title = self._code_title(code)
            knowledge_type = "component"
            return [ExtractionCandidate(
                id=make_id(),
                knowledge_type=knowledge_type,
                title=title,
                description=f"Code block{(' (' + segment.label + ')') if segment.label else ''}",
                content=code,
                source=source,
                evidence_excerpt=code[:200],
                evidence_location=segment.location,
                segment=segment,
            )]

        if segment.type == SegmentType.TABLE:
            rows = content if isinstance(content, list) else [content]
            title = f"Table {segment.location or ''}".strip()
            return [ExtractionCandidate(
                id=make_id(),
                knowledge_type="business_rule",
                title=title,
                description="Extracted table",
                content=rows,
                source=source,
                evidence_excerpt=str(rows)[:200],
                evidence_location=segment.location,
                segment=segment,
            )]

        if segment.type == SegmentType.STRUCTURAL:
            label = str(segment.label or "structural item")
            value = segment.content
            title = label if len(label) <= 80 else label[:77] + "..."
            return [ExtractionCandidate(
                id=make_id(),
                knowledge_type=_classify_text(label, default="entity"),
                title=title,
                description=None,
                content=value,
                source=source,
                evidence_excerpt=str(value)[:200],
                evidence_location=segment.location,
                segment=segment,
            )]

        if segment.type in (SegmentType.LIST, SegmentType.TASK_LIST):
            return self._extract_list_segment(segment, source)

        return []

    @staticmethod
    def _code_title(code: str) -> str:
        first = code.splitlines()[0].strip() if code else ""
        if first.startswith("#"):
            return first.lstrip("#").strip()
        return "Code snippet"

    def _extract_list_segment(
        self,
        segment: Segment,
        source: KnowledgeSource,
    ) -> list[ExtractionCandidate]:
        """Create a candidate for each item in a list segment."""
        candidates: list[ExtractionCandidate] = []
        content = segment.content
        if not isinstance(content, list):
            return candidates

        for index, item in enumerate(content):
            if isinstance(item, dict):
                text = str(item.get("text", "")).strip()
            else:
                text = str(item).strip()
            if not text:
                continue
            title = _first_sentence(text) or text[:80]
            candidates.append(
                ExtractionCandidate(
                    id=make_id(),
                    knowledge_type=_classify_text(text, default="document"),
                    title=title,
                    description=text,
                    content=text,
                    source=source,
                    evidence_excerpt=text,
                    evidence_location=f"{segment.location}[{index}]" if segment.location else f"item {index}",
                    segment=segment,
                )
            )
        return candidates


def _first_sentence(text: str) -> str:
    match = re.match(r"[^.!?]+[.!?]", text.strip())
    if match:
        return match.group(0).strip()
    return text.strip()[:80]
