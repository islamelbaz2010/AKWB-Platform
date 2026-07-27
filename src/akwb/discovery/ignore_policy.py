"""Production-grade ignore policy for the Discovery Engine.

The ``IgnorePolicy`` encapsulates built-in, project-level, and user-supplied
ignore rules. It supports directory-only patterns, anchored paths, archive
handling, and safe binary detection without emitting warnings for intentionally
ignored paths.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class IgnoreReason(str, Enum):
    """Categorize why a path was ignored."""

    NOT_IGNORED = "not_ignored"
    BUILT_IN = "built_in"
    USER = "user"
    ARCHIVE = "archive"
    BINARY = "binary"
    EXPLICIT = "explicit"


@dataclass
class IgnoreRule:
    """A single ignore rule with provenance and metadata."""

    pattern: str
    source: IgnoreReason = IgnoreReason.EXPLICIT
    directory_only: bool = False
    negation: bool = False
    line: int | None = None

    def __post_init__(self) -> None:
        """Derive directory-only and negation flags from the raw pattern."""
        raw = self.pattern
        if not self.negation and raw.startswith("!"):
            self.negation = True
            raw = raw[1:]
        self.directory_only = raw.endswith("/")
        # Keep a leading slash so anchored patterns can be detected later.
        self.pattern = raw.rstrip("/")


# Built-in ignore patterns are intentionally conservative. They cover common
# operating-system artifacts, editor metadata, caches, generated folders, and
# archives. Users can override any of these with a ``!pattern`` entry in
# ``.akwbignore`` or via ``discovery.ignore_patterns``.
BUILT_IN_IGNORE_PATTERNS: list[str] = [
    # --- Operating-system artifacts ---
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    "*.lnk",
    # --- Editor and IDE metadata ---
    ".vscode",
    ".idea",
    "*.swp",
    "*.swo",
    "*~",
    "*.tmp",
    ".editorconfig",
    # --- Caches, temporary, and coverage outputs ---
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".sass-cache",
    ".cache",
    "*.cache",
    "*.log",
    ".coverage",
    "coverage",
    ".tox",
    ".nox",
    "*.egg-info",
    # --- Generated and dependency directories ---
    "node_modules",
    "bower_components",
    "vendor",
    "dist",
    "build",
    "target",
    ".next",
    ".nuxt",
    "out",
    "public/build",
    # --- Virtual environments ---
    "venv",
    ".venv",
    "env",
    "virtualenv",
    # --- Version control ---
    ".git",
    ".hg",
    ".svn",
    # --- AKWB workspace (always ignored at root level) ---
    ".akwb",
    # --- Archives (ignored unless explicitly supported by a plugin) ---
    "*.zip",
    "*.tar",
    "*.gz",
    "*.bz2",
    "*.xz",
    "*.rar",
    "*.7z",
    "*.tar.gz",
    "*.tgz",
    "*.tar.bz2",
    "*.tar.xz",
]


class IgnorePolicy:
    """Resolve ignore status for filesystem paths against layered rules.

    Rules are applied in order:

    1. User rules from ``.akwbignore`` and config overrides.
    2. Built-in operating-system, editor, cache, generated, and archive patterns.
    3. Binary content detection as a final safety net.

    User negation patterns (``!pattern``) can override built-ins.
    """

    def __init__(
        self,
        project_root: Path,
        explicit_patterns: list[str] | None = None,
        use_built_ins: bool = True,
        binary_detection: bool = True,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.use_built_ins = use_built_ins
        self.binary_detection = binary_detection

        self.user_rules = self._load_user_rules()
        self.user_rules.extend(
            self._parse_patterns(explicit_patterns or [], source=IgnoreReason.EXPLICIT)
        )
        self.built_in_rules = (
            self._parse_patterns(BUILT_IN_IGNORE_PATTERNS, source=IgnoreReason.BUILT_IN)
            if use_built_ins
            else []
        )

    def is_ignored(self, path: Path, is_dir: bool | None = None) -> bool:
        """Return True if ``path`` should be skipped by the scanner."""
        return self.check(path, is_dir=is_dir).ignored

    def check(self, path: Path, is_dir: bool | None = None) -> "IgnoreCheck":
        """Return an ``IgnoreCheck`` describing whether and why a path is ignored."""
        abs_path = self._normalize(path)
        if abs_path == self.project_root:
            return IgnoreCheck(False, IgnoreReason.NOT_IGNORED, path)

        is_directory = self._is_directory(abs_path, is_dir)
        rel_parts, name = self._parts_and_name(abs_path)

        user = self._apply_rules(self.user_rules, rel_parts, name, is_directory)
        if user is not None:
            return IgnoreCheck(user, self._reason_for_match(IgnoreReason.USER), path)

        built_in = self._apply_rules(self.built_in_rules, rel_parts, name, is_directory)
        if built_in:
            return IgnoreCheck(True, IgnoreReason.BUILT_IN, path)

        if (
            not is_directory
            and self.binary_detection
            and self._is_binary_file(abs_path)
        ):
            return IgnoreCheck(True, IgnoreReason.BINARY, path)

        return IgnoreCheck(False, IgnoreReason.NOT_IGNORED, path)

    def _load_user_rules(self) -> list[IgnoreRule]:
        """Load ``.akwbignore`` rules if present."""
        ignore_file = self.project_root / ".akwbignore"
        if not ignore_file.exists():
            return []
        try:
            lines = ignore_file.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        patterns = [
            line.strip()
            for idx, line in enumerate(lines, start=1)
            if line.strip() and not line.startswith("#")
        ]
        return self._parse_patterns(patterns, source=IgnoreReason.USER)

    @staticmethod
    def _parse_patterns(patterns: list[str], source: IgnoreReason) -> list[IgnoreRule]:
        """Parse a list of raw patterns into ``IgnoreRule`` instances."""
        return [
            IgnoreRule(pattern=pattern, source=source)
            for pattern in patterns
            if pattern.strip()
        ]

    @staticmethod
    def _reason_for_match(source: IgnoreReason) -> IgnoreReason:
        """Return the reason that should be reported for a user match."""
        # A negation rule still originates from user configuration.
        return IgnoreReason.USER

    def _normalize(self, path: Path | str) -> Path:
        """Resolve ``path`` to an absolute Path."""
        return Path(path).expanduser().resolve()

    def _is_directory(self, abs_path: Path, is_dir: bool | None) -> bool:
        """Determine whether ``abs_path`` is a directory, with a safe fallback."""
        if is_dir is not None:
            return is_dir
        try:
            return abs_path.is_dir()
        except OSError:
            return False

    def _parts_and_name(self, abs_path: Path) -> tuple[tuple[str, ...], str]:
        """Return the path parts relative to the project root and the basename."""
        try:
            rel_parts = abs_path.relative_to(self.project_root).parts
        except ValueError:
            rel_parts = abs_path.parts
        return rel_parts, abs_path.name

    def _apply_rules(
        self,
        rules: list[IgnoreRule],
        rel_parts: tuple[str, ...],
        name: str,
        is_dir: bool,
    ) -> bool | None:
        """Apply a rule list and return the final match state, or None if no rule matched."""
        matched: bool | None = None
        for rule in rules:
            if self._matches(rule, rel_parts, name, is_dir):
                matched = not rule.negation
        return matched

    def _matches(
        self,
        rule: IgnoreRule,
        rel_parts: tuple[str, ...],
        name: str,
        is_dir: bool,
    ) -> bool:
        """Check whether a single rule matches the given path."""
        if rule.directory_only and not is_dir:
            return False

        pattern = rule.pattern
        if not pattern:
            return False

        # Anchored patterns start with a leading slash in the raw form.
        raw = rule.pattern
        is_anchored = raw.startswith("/")
        raw = raw.lstrip("/")

        if is_anchored:
            pat_parts = raw.split("/")
            if len(pat_parts) > len(rel_parts):
                return False
            for pat_part, rel_part in zip(pat_parts, rel_parts):
                if not fnmatch.fnmatch(rel_part, pat_part):
                    return False
            return True

        if fnmatch.fnmatch(name, raw):
            return True

        for part in rel_parts:
            if fnmatch.fnmatch(part, raw):
                return True

        return False

    def _is_binary_file(self, abs_path: Path) -> bool:
        """Detect binary files by sampling their first bytes.

        This avoids reading large files into memory. A file is considered binary
        if it contains a null byte or cannot be decoded as UTF-8.
        """
        try:
            with abs_path.open("rb") as fh:
                sample = fh.read(1024)
        except OSError:
            return False

        if not sample:
            return False

        if b"\x00" in sample:
            return True

        try:
            sample.decode("utf-8")
        except UnicodeDecodeError:
            return True

        return False


@dataclass
class IgnoreCheck:
    """Result of an ignore policy check for a single path."""

    ignored: bool
    reason: IgnoreReason
    path: Path
    metadata: dict[str, object] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.ignored
