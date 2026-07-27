"""Incremental change detection between two artifact registries."""

from __future__ import annotations

from dataclasses import dataclass, field

from akwb.discovery.models import ArtifactEntry, ArtifactRegistry


@dataclass
class ChangeSet:
    """Summary of changes between two registry snapshots."""

    added: list[ArtifactEntry] = field(default_factory=list)
    modified: list[ArtifactEntry] = field(default_factory=list)
    deleted: list[ArtifactEntry] = field(default_factory=list)
    renamed: list[ArtifactEntry] = field(default_factory=list)
    unchanged: list[ArtifactEntry] = field(default_factory=list)


class IncrementalDetector:
    """Compare a previous registry with a current one to determine statuses."""

    def detect(self, previous: ArtifactRegistry, current: ArtifactRegistry) -> ChangeSet:
        """Mutate ``current`` entry statuses and return a change summary."""
        changes = ChangeSet()
        current_paths = {a.relative_path for a in current.all()}
        previous_by_path = {a.relative_path: a for a in previous.all()}

        # Build O(1) lookup tables for rename detection from previous artifacts
        # whose paths are no longer present in the current scan.
        previous_by_hash: dict[str, list[ArtifactEntry]] = {}
        previous_by_size: dict[int, list[ArtifactEntry]] = {}
        for previous_entry in previous.all():
            if previous_entry.relative_path in current_paths:
                continue
            if previous_entry.hash is not None:
                previous_by_hash.setdefault(previous_entry.hash, []).append(previous_entry)
            else:
                previous_by_size.setdefault(previous_entry.size, []).append(previous_entry)

        used_previous: set[str] = set()

        for artifact in current.all():
            matched = previous_by_path.get(artifact.relative_path)
            if matched is None:
                # New path - check for rename by content hash (or size fallback
                # when hashing has been skipped for large files).
                rename_candidate = self._find_rename_source(
                    artifact, previous_by_hash, previous_by_size, used_previous
                )
                if rename_candidate:
                    artifact.status = "renamed"
                    artifact.previous_path = rename_candidate.relative_path
                    used_previous.add(rename_candidate.id)
                    changes.renamed.append(artifact)
                else:
                    artifact.status = "new"
                    changes.added.append(artifact)
            else:
                used_previous.add(matched.id)
                if self._content_equal(matched, artifact):
                    artifact.status = "unchanged"
                    changes.unchanged.append(artifact)
                else:
                    artifact.status = "modified"
                    changes.modified.append(artifact)

        for previous_entry in previous.all():
            if previous_entry.id in used_previous:
                continue
            previous_entry.status = "deleted"
            changes.deleted.append(previous_entry)

        return changes

    @staticmethod
    def _content_equal(prev: ArtifactEntry, curr: ArtifactEntry) -> bool:
        """Return True if two artifacts have the same content fingerprint."""
        if prev.hash is not None and curr.hash is not None:
            return prev.hash == curr.hash
        if prev.hash is None and curr.hash is None:
            return prev.size == curr.size
        return False

    @staticmethod
    def _find_rename_source(
        artifact: ArtifactEntry,
        previous_by_hash: dict[str, list[ArtifactEntry]],
        previous_by_size: dict[int, list[ArtifactEntry]],
        used: set[str],
    ) -> ArtifactEntry | None:
        """Find a previous artifact with the same content as a new path."""
        if artifact.hash is not None:
            candidates = previous_by_hash.get(artifact.hash, [])
            for candidate in candidates:
                if candidate.id in used:
                    continue
                used.add(candidate.id)
                return candidate
        elif artifact.hash is None:
            candidates = previous_by_size.get(artifact.size, [])
            for candidate in candidates:
                if candidate.id in used:
                    continue
                used.add(candidate.id)
                return candidate
        return None
