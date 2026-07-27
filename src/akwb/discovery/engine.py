"""Discovery Engine orchestration for scanning and inventorying project artifacts."""

from __future__ import annotations

import os
from pathlib import Path

from akwb.config import Config
from akwb.discovery.classifier import FileClassifier
from akwb.discovery.fingerprint import FingerprintEngine
from akwb.discovery.ignore import IgnoreEngine
from akwb.discovery.incremental import IncrementalDetector
from akwb.discovery.metadata import MetadataExtractor
from akwb.discovery.models import ArtifactEntry, ArtifactRegistry
from akwb.discovery.scanner import RecursiveScanner
from akwb.domain.events import DiscoveryCompleted
from akwb.domain.ports import EventBus, Observability, StoragePort
from akwb.types import Diagnostic, Result


class DiscoveryEngine:
    """Scan a project and produce a canonical artifact registry."""

    def __init__(
        self,
        config: Config,
        storage: StoragePort,
        event_bus: EventBus,
        observability: Observability,
        ignore_engine: IgnoreEngine | None = None,
        classifier: FileClassifier | None = None,
        fingerprint_engine: FingerprintEngine | None = None,
        metadata_extractor: MetadataExtractor | None = None,
        scanner: RecursiveScanner | None = None,
        incremental_detector: IncrementalDetector | None = None,
    ) -> None:
        self._config = config
        self._storage = storage
        self._event_bus = event_bus
        self._observability = observability

        ignore_patterns = list(config.discovery.default_ignored) + list(config.discovery.ignore_patterns)
        if config.workspace_dir not in ignore_patterns:
            ignore_patterns.append(config.workspace_dir)
        self._ignore = ignore_engine or IgnoreEngine(
            project_root=storage.root().parent,
            patterns=ignore_patterns,
        )
        self._classifier = classifier or FileClassifier()
        self._fingerprint = fingerprint_engine or FingerprintEngine(
            algorithm=config.discovery.hash_algorithm,
            max_file_size_bytes=config.discovery.max_file_size_bytes,
        )
        self._metadata = metadata_extractor or MetadataExtractor(self._fingerprint)
        self._scanner = scanner or RecursiveScanner(
            ignore_engine=self._ignore,
            follow_symlinks=config.discovery.follow_symlinks,
            include_directories=config.discovery.include_directories,
        )
        self._incremental = incremental_detector or IncrementalDetector()

    def discover(self, project_root: Path) -> Result[ArtifactRegistry, Diagnostic]:
        """Discover all artifacts under ``project_root`` and persist the registry."""
        try:
            project_root = project_root.resolve()
            registry_filename = self._config.discovery.registry_file

            previous = ArtifactRegistry.load(
                self._storage,
                filename=registry_filename,
                project_root=str(project_root),
            )
            previous_by_path = {a.relative_path: a for a in previous.all()}
            current = ArtifactRegistry(project_root=str(project_root))

            for item in self._scanner.scan(project_root):
                resolved = item.path.resolve()
                try:
                    stat = resolved.stat()
                except OSError:
                    continue

                if item.is_directory:
                    artifact = self._metadata.extract_directory(
                        item.path, item.relative_path, project_root, stat=stat
                    )
                else:
                    artifact_type, category = self._classifier.classify(
                        item.path, is_directory=False
                    )
                    content_hash = self._reuse_or_hash(
                        item.relative_path, stat, previous_by_path
                    )
                    if content_hash is None:
                        content_hash = self._fingerprint.hash_file(
                            item.path, stat=stat
                        )
                    artifact = self._metadata.extract(
                        item.path,
                        item.relative_path,
                        project_root,
                        artifact_type,
                        category,
                        content_hash,
                        stat=stat,
                    )

                current.add(artifact)

            changes = self._incremental.detect(previous, current)

            # Sort artifacts by relative path for stable, canonical output.
            current.artifacts.sort(key=lambda a: a.relative_path)
            current.save(self._storage, registry_filename)

            self._observability.info(
                f"Discovered {len(current.artifacts)} artifacts; "
                f"added={len(changes.added)}, modified={len(changes.modified)}, "
                f"deleted={len(changes.deleted)}, renamed={len(changes.renamed)}"
            )

            self._event_bus.publish(
                DiscoveryCompleted(
                    project_root=str(project_root),
                    artifact_count=len(current.artifacts),
                    registry_path=str(self._storage.root() / registry_filename),
                )
            )

            return Result.success(current)
        except Exception as exc:  # noqa: BLE001
            diagnostic = Diagnostic(
                "error",
                "discovery_failed",
                f"Discovery failed: {exc}",
            )
            self._observability.diagnostic(diagnostic)
            return Result.failure(diagnostic)

    def _reuse_or_hash(
        self,
        relative_path: str,
        stat: os.stat_result,
        previous_by_path: dict[str, ArtifactEntry],
    ) -> str | None:
        """Return a cached hash if the file size and mtime are unchanged."""
        prev = previous_by_path.get(relative_path)
        if prev is None:
            return None
        if prev.size != stat.st_size:
            return None
        current_mtime = self._metadata._format_time(stat.st_mtime)
        if prev.modified_time != current_mtime:
            return None
        return prev.hash
