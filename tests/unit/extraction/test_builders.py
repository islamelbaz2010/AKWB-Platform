"""Tests for the default knowledge object builder."""

from akwb.extraction.builders import DefaultKnowledgeObjectBuilder
from akwb.extraction.models import ExtractionCandidate, Segment, SegmentType
from akwb.extraction.pipeline import ExtractionContext
from akwb.knowledge.framework import KnowledgeFramework
from akwb.knowledge.models import KnowledgeSource


def test_build_knowledge_object() -> None:
    framework = KnowledgeFramework()
    context = ExtractionContext(framework=framework, project_id="akwb")
    source = KnowledgeSource(kind="markdown", uri="doc.md")
    segment = Segment(
        type=SegmentType.PARAGRAPH,
        content="The system must be available 99.9%.",
        location="line 5",
    )
    candidate = ExtractionCandidate(
        knowledge_type="requirement",
        title="Availability requirement",
        description="The system must be available 99.9%.",
        content="99.9% availability",
        source=source,
        evidence_excerpt="The system must be available 99.9%.",
        evidence_location="line 5",
        segment=segment,
        tags=["sre"],
    )
    builder = DefaultKnowledgeObjectBuilder()
    obj = builder.build(candidate, source, context)

    assert obj.type == "requirement"
    assert obj.title == "Availability requirement"
    assert obj.sources[0].uri == "doc.md"
    assert obj.evidence[0].excerpt == "The system must be available 99.9%."
    assert obj.domain_tags == ["sre"]
    assert obj.metadata.project_id == "akwb"
