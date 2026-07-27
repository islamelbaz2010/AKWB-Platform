"""Ignore engine for filtering paths during project discovery.

This module is a thin, backwards-compatible façade over ``akwb.discovery.ignore_policy``.
It now uses the production-grade ``IgnorePolicy`` class, which provides layered
built-in rules, user overrides, directory-aware matching, archive filtering, and
safe binary detection.
"""

from __future__ import annotations

from pathlib import Path

from akwb.discovery.ignore_policy import (
    BUILT_IN_IGNORE_PATTERNS,
    IgnoreCheck,
    IgnorePolicy,
    IgnoreReason,
    IgnoreRule,
)

__all__ = [
    "BUILT_IN_IGNORE_PATTERNS",
    "IgnoreCheck",
    "IgnoreEngine",
    "IgnorePolicy",
    "IgnoreReason",
    "IgnoreRule",
]


class IgnoreEngine:
    """Match paths against default and project-specific ignore patterns."""

    def __init__(
        self,
        project_root: Path,
        patterns: list[str],
        use_built_ins: bool = True,
        binary_detection: bool = True,
    ) -> None:
        """Initialize the ignore engine.

        Args:
            project_root: Root directory of the project.
            patterns: User-supplied ignore patterns. These are treated as explicit
                overrides and are evaluated before built-in patterns.
            use_built_ins: Whether to apply the built-in ignore rules. Defaults
                to True. Disabling this is useful for testing isolated behavior.
            binary_detection: Whether to perform safe binary content sampling.
        """
        self._root = Path(project_root).resolve()
        self._patterns = list(patterns)
        self._policy = IgnorePolicy(
            project_root=self._root,
            explicit_patterns=self._patterns,
            use_built_ins=use_built_ins,
            binary_detection=binary_detection,
        )

    def is_ignored(
        self,
        path: Path,
        is_dir: bool | None = None,
    ) -> bool:
        """Return True if ``path`` should be skipped during discovery."""
        return self._policy.is_ignored(Path(path), is_dir=is_dir)

    def check(self, path: Path, is_dir: bool | None = None) -> IgnoreCheck:
        """Return a detailed ``IgnoreCheck`` for ``path``."""
        return self._policy.check(Path(path), is_dir=is_dir)
