"""End-to-end validation of the Canonical Document pipeline.

This module is the architectural proof required by Sprint 7.2: it shows that
any future parser can plug into the extraction pipeline by implementing
``DocumentReader`` and producing a valid ``CanonicalDocument``.
"""

from akwb.domain.models import Artifact
from akwb.extraction import (
    CanonicalDocument,
    CanonicalElementType,
    CanonicalValidator,
    ContentKind,
    DocumentElement,
    DocumentReader,
    ExtractionPipeline,
)


class StubDocumentReader(DocumentReader):
    """Minimal document reader used to validate the canonical pipeline.

    This is intentionally simple and generic; it proves the contract that
    future DOCX, PDF, HTML, and email parsers will follow.
    """

    supported_mime_types = ("application/x-stub-document",)

    def read_canonical(
        self,
        artifact: Artifact,
        content: bytes | str,
        context: object | None = None,
    ) -> CanonicalDocument:
        text = content.decode("utf-8") if isinstance(content, bytes) else content
        return CanonicalDocument(
            source_uri=artifact.relative_path or artifact.name,
            mime_type="application/x-stub-document",
            language="stub",
            children=[
                DocumentElement(
                    type=CanonicalElementType.HEADING,
                    content="Decision to use the Canonical Model",
                    level=1,
                ),
                DocumentElement(
                    type=CanonicalElementType.PARAGRAPH,
                    content=text,
                ),
            ],
        )


def _artifact() -> Artifact:
    return Artifact(
        name="demo.sdoc",
        relative_path="docs/demo.sdoc",
        mime_type="application/x-stub-document",
    )


def test_canonical_reader_produces_document_content() -> None:
    reader = StubDocumentReader()
    artifact = _artifact()
    normalized = reader.read(artifact, "The canonical model is the only path.")

    assert normalized.kind == ContentKind.DOCUMENT
    assert isinstance(normalized.content, CanonicalDocument)
    assert normalized.content.children[0].type == CanonicalElementType.HEADING


def test_pipeline_extracts_from_generic_canonical_reader() -> None:
    pipeline = ExtractionPipeline()
    pipeline.readers.insert(0, StubDocumentReader())

    artifact = _artifact()
    result = pipeline.extract(
        artifact,
        "The architecture must be canonical end-to-end.",
        project_id="stub-project",
    )

    assert result.ok
    assert result.candidate_count >= 1
    assert len(result.objects) >= 1
    assert any(obj.type == "decision" for obj in result.objects)


def test_validation_layer_rejects_invalid_canonical_document() -> None:
    validator = CanonicalValidator()
    invalid = CanonicalDocument(
        source_uri="broken.md",
        mime_type="text/markdown",
        children=[
            DocumentElement(
                type=CanonicalElementType.LIST,
                children=[
                    # A paragraph directly inside a list is not allowed by the
                    # current hierarchy contract.
                    DocumentElement(type=CanonicalElementType.PARAGRAPH, content="bad"),
                ],
            ),
        ],
    )

    validation = validator.validate(invalid, source_ref="broken.md")
    assert not validation.ok
    assert any(d.code == "invalid_child_element" for d in validation.diagnostics)


def test_validation_layer_accepts_valid_canonical_document() -> None:
    validator = CanonicalValidator()
    doc = CanonicalDocument(
        source_uri="good.md",
        mime_type="text/markdown",
        children=[
            DocumentElement(
                type=CanonicalElementType.HEADING,
                level=1,
                content="Valid",
            ),
            DocumentElement(
                type=CanonicalElementType.PARAGRAPH,
                content="This document is valid.",
            ),
        ],
    )

    validation = validator.validate(doc, source_ref="good.md")
    assert validation.ok
    assert not any(d.level == "error" for d in validation.diagnostics)
