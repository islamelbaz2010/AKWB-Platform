"""Enterprise Extraction Pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from akwb.domain.models import Artifact
from akwb.domain.ports import Observability
from akwb.extraction.builders import (
    DefaultKnowledgeObjectBuilder,
    RegisteredTypeCandidateValidator,
    RequiredFieldsCandidateValidator,
)
from akwb.extraction.document import CanonicalSegmenter, CanonicalValidator
from akwb.extraction.extractors import RuleBasedExtractor
from akwb.extraction.markdown import MarkdownReader
from akwb.extraction.models import ContentKind, ExtractionResult
from akwb.extraction.plugins import (
    CandidateBuilder,
    CandidateValidator,
    Extractor,
    Reader,
    Segmenter,
)
from akwb.extraction.readers import BinaryReader, StructuredReader, TextReader
from akwb.extraction.segmenters import (
    AdaptiveSegmenter,
    CodeSegmenter,
    HeadingSegmenter,
    ParagraphSegmenter,
    StructuralSegmenter,
    TableSegmenter,
)
from akwb.knowledge.framework import KnowledgeFramework
from akwb.knowledge.models import KnowledgeSource
from akwb.types import Diagnostic


@dataclass
class ExtractionContext:
    """Context shared across pipeline stages."""

    framework: KnowledgeFramework
    observability: Observability | None = None
    project_id: str | None = None
    source_uri: str | None = None

    diagnostics: list[Diagnostic] = field(default_factory=list)

    def emit(self, diagnostic: Diagnostic) -> None:
        """Record a diagnostic and forward it to observability if configured."""
        self.diagnostics.append(diagnostic)
        if self.observability:
            self.observability.diagnostic(diagnostic)


class ExtractionPipeline:
    """Convert discovered artifacts into canonical KnowledgeObjects.

    The pipeline is intentionally free of AI-specific business logic; it
    orchestrates readers, segmenters, extractors, builders, and validators
    that may be extended through the plugin system.
    """

    def __init__(
        self,
        framework: KnowledgeFramework | None = None,
        observability: Observability | None = None,
    ) -> None:
        self.framework = framework or KnowledgeFramework()
        self.observability = observability

        self.readers: list[Reader] = [
            MarkdownReader(),
            TextReader(),
            BinaryReader(),
            StructuredReader(),
        ]

        # All document content must be normalized to a CanonicalDocument before
        # extraction. The CanonicalSegmenter is the only document segmenter; the
        # legacy MarkdownSegmenter is no longer registered.
        self.adaptive_segmenter = AdaptiveSegmenter(
            [
                CanonicalSegmenter(),
                HeadingSegmenter(),
                ParagraphSegmenter(),
                CodeSegmenter(),
                TableSegmenter(),
                StructuralSegmenter(),
            ]
        )
        self.segmenters: list[Segmenter] = [self.adaptive_segmenter]

        self.canonical_validator = CanonicalValidator()

        self.extractors: list[Extractor] = [RuleBasedExtractor()]

        self.builders: list[CandidateBuilder] = [DefaultKnowledgeObjectBuilder()]

        self.candidate_validators: list[CandidateValidator] = [
            RequiredFieldsCandidateValidator(),
            RegisteredTypeCandidateValidator(),
        ]

    def load_plugins(self, plugin_registry: Any) -> None:
        """Extend the pipeline with plugin-provided components."""
        for reader in plugin_registry.resolve("reader"):
            self.register_reader(self._instantiate(reader))
        for segmenter in plugin_registry.resolve("segmenter"):
            self.register_segmenter(self._instantiate(segmenter))
        for extractor in plugin_registry.resolve("extractor"):
            self.register_extractor(self._instantiate(extractor))
        for builder in plugin_registry.resolve("candidate_builder"):
            self.register_builder(self._instantiate(builder))
        for validator in plugin_registry.resolve("candidate_validator"):
            self.register_candidate_validator(self._instantiate(validator))

    def register_reader(self, reader: Reader) -> None:
        # Plugin readers are prepended so they can override built-in fallbacks.
        self.readers.insert(0, reader)

    def register_segmenter(self, segmenter: Segmenter) -> None:
        if isinstance(segmenter, AdaptiveSegmenter):
            self.adaptive_segmenter = segmenter
            # Ensure the primary list reflects the chosen adaptive segmenter.
            self.segmenters = [segmenter]
        else:
            self.adaptive_segmenter.add_segmenter(segmenter)

    def register_extractor(self, extractor: Extractor) -> None:
        # Plugin extractors are prepended so they can short-circuit defaults.
        self.extractors.insert(0, extractor)

    def register_builder(self, builder: CandidateBuilder) -> None:
        # Plugin builders are prepended so they take priority over the default.
        self.builders.insert(0, builder)

    def register_candidate_validator(self, validator: CandidateValidator) -> None:
        self.candidate_validators.insert(0, validator)

    @staticmethod
    def _instantiate(component: Any) -> Any:
        return component() if isinstance(component, type) else component

    def extract(
        self,
        artifact: Artifact,
        content: bytes | str,
        project_id: str | None = None,
    ) -> ExtractionResult:
        """Run the full extraction pipeline on an artifact."""
        context = ExtractionContext(
            framework=self.framework,
            observability=self.observability,
            project_id=project_id,
            source_uri=artifact.relative_path,
        )

        source = self._artifact_source(artifact)

        reader = self._resolve_reader(artifact.mime_type)
        if reader is None:
            return self._error(
                artifact,
                f"No reader registered for mime type {artifact.mime_type!r}",
            )

        normalized = reader.read(artifact, content, context)

        # Validate the canonical document contract before extraction.
        if normalized.kind == ContentKind.DOCUMENT:
            canonical_validation = self.canonical_validator.validate(
                normalized.content,
                source_ref=artifact.relative_path,
            )
            for diag in canonical_validation.diagnostics:
                context.emit(diag)
            if not canonical_validation.ok:
                return ExtractionResult(
                    ok=False,
                    objects=[],
                    diagnostics=context.diagnostics,
                    candidate_count=0,
                )

        segments: list[Any] = []
        for segmenter in self.segmenters:
            if segmenter.can_segment(normalized.kind):
                try:
                    segments.extend(segmenter.segment(normalized, context))
                except Exception as exc:  # noqa: BLE001
                    context.emit(
                        Diagnostic(
                            "error",
                            "segmentation_failed",
                            f"Segmenter {type(segmenter).__name__} failed: {exc}",
                            source_ref=artifact.relative_path,
                        )
                    )

        candidates: list[Any] = []
        for extractor in self.extractors:
            try:
                candidates.extend(extractor.extract(segments, source, context))
            except Exception as exc:  # noqa: BLE001
                context.emit(
                    Diagnostic(
                        "error",
                        "extraction_failed",
                        f"Extractor {type(extractor).__name__} failed: {exc}",
                        source_ref=artifact.relative_path,
                    )
                )

        objects: list[Any] = []
        for candidate in candidates:
            candidate.source = candidate.source or source

            for validator in self.candidate_validators:
                validation = validator.validate(candidate, context)
                if not validation.ok:
                    for diag in validation.diagnostics:
                        context.emit(
                            Diagnostic(
                                "error",
                                "candidate_validation_failed",
                                diag.message,
                                source_ref=artifact.relative_path,
                            )
                        )
                    break
            else:
                builder = self.builders[0]
                try:
                    obj = builder.build(candidate, source, context)
                except Exception as exc:  # noqa: BLE001
                    context.emit(
                        Diagnostic(
                            "error",
                            "object_build_failed",
                            f"Builder failed: {exc}",
                            source_ref=artifact.relative_path,
                        )
                    )
                    continue

                validation = self.framework.validate_object(obj)
                if not validation.ok:
                    for diag in validation.diagnostics:
                        context.emit(diag)

                objects.append(obj)

        return ExtractionResult(
            ok=not any(diag.level == "error" for diag in context.diagnostics),
            objects=objects,
            diagnostics=context.diagnostics,
            candidate_count=len(candidates),
        )

    def can_extract(self, mime_type: str) -> bool:
        """Return whether the pipeline has a reader for ``mime_type``."""
        return any(reader.can_read(mime_type) for reader in self.readers)

    def _resolve_reader(self, mime_type: str) -> Reader | None:
        for reader in self.readers:
            if reader.can_read(mime_type):
                return reader
        return None

    def _artifact_source(self, artifact: Artifact) -> KnowledgeSource:
        kind = self._source_kind_from_mime(artifact.mime_type)
        return KnowledgeSource(
            kind=kind,
            uri=artifact.relative_path or artifact.name,
            mime_type=artifact.mime_type,
        )

    @staticmethod
    def _source_kind_from_mime(mime_type: str) -> str:
        major, _, minor = mime_type.partition("/")
        if major == "text":
            if "markdown" in minor:
                return "markdown"
            if "html" in minor:
                return "html"
            return "manual"
        if major == "image":
            return "image"
        if major == "audio":
            return "audio"
        if major == "video":
            return "video"
        if "json" in mime_type or "yaml" in mime_type:
            return "code"
        if "pdf" in mime_type:
            return "pdf"
        if "wordprocessing" in mime_type or "docx" in mime_type:
            return "docx"
        return "unknown"

    def _error(self, artifact: Artifact, message: str) -> ExtractionResult:
        """Record an extraction failure for an unsupported artifact."""
        diag = Diagnostic(
            "error",
            "extraction_failed",
            message,
            source_ref=artifact.relative_path,
        )
        if self.observability:
            self.observability.diagnostic(diag)
        return ExtractionResult(ok=False, diagnostics=[diag], candidate_count=0)
