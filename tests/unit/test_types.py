"""Tests for shared types."""

from akwb.types import Diagnostic, Result


def test_result_success() -> None:
    r = Result.success("value")
    assert r.ok is True
    assert r.value == "value"
    assert r.error is None
    assert r.diagnostics == []


def test_result_failure() -> None:
    diag = Diagnostic("error", "E001", "fail")
    r = Result.failure(diag)
    assert r.ok is False
    assert r.value is None
    assert r.error is diag


def test_diagnostic_string() -> None:
    d = Diagnostic("warning", "W001", "message", "src")
    assert "[WARNING:W001] message" in str(d)
