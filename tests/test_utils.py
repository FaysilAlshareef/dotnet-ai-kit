"""Tests for dotnet_ai_kit.utils shared utilities."""

from __future__ import annotations

from dotnet_ai_kit.utils import HOOK_MODEL, HOOK_TIMEOUT_MS, parse_version

# ---------------------------------------------------------------------------
# parse_version tests
# ---------------------------------------------------------------------------


def test_parse_version_basic() -> None:
    assert parse_version("1.2.3") == (1, 2, 3)


def test_parse_version_major_only() -> None:
    assert parse_version("1") == (1,)


def test_parse_version_two_parts() -> None:
    assert parse_version("1.0") == (1, 0)


def test_parse_version_pre_release_beta() -> None:
    """Pre-release suffix stripped; equals the stable version."""
    assert parse_version("1.0.0-beta") == (1, 0, 0)


def test_parse_version_pre_release_rc() -> None:
    assert parse_version("1.1.0-rc1") == (1, 1, 0)


def test_parse_version_pre_release_rc_with_dot() -> None:
    assert parse_version("1.0.0-rc.1") == (1, 0, 0)


def test_parse_version_pre_release_equals_stable() -> None:
    """1.0.0-beta must not compare GREATER THAN 1.0.0 (old bug)."""
    assert parse_version("1.0.0-beta") == parse_version("1.0.0")
    assert not (parse_version("1.0.0-beta") > parse_version("1.0.0"))


def test_parse_version_non_numeric() -> None:
    assert parse_version("1.a.0") == (1, 0, 0)


def test_parse_version_empty() -> None:
    assert parse_version("") == (0,)


def test_parse_version_whitespace() -> None:
    assert parse_version("  1.2.3  ") == (1, 2, 3)


# ---------------------------------------------------------------------------
# Hook constants tests
# ---------------------------------------------------------------------------


def test_hook_constants_model_is_string() -> None:
    assert isinstance(HOOK_MODEL, str)
    assert len(HOOK_MODEL) > 0


def test_hook_constants_timeout_is_positive_int() -> None:
    assert isinstance(HOOK_TIMEOUT_MS, int)
    assert HOOK_TIMEOUT_MS > 0


def test_hook_constants_values() -> None:
    assert "haiku" in HOOK_MODEL.lower()
    assert HOOK_TIMEOUT_MS == 15_000
