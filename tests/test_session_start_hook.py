"""T013a — FR-001: session-start hook must not bulk-prompt skill loading."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "session-start-bootstrap.sh"

FORBIDDEN_PHRASES = (
    "MIGHT apply",
    "load it BEFORE acting",
    "even a small chance",
)


def test_session_start_hook_lacks_forbidden_phrases() -> None:
    body = HOOK.read_text(encoding="utf-8")
    lower = body.lower()
    for phrase in FORBIDDEN_PHRASES:
        assert phrase.lower() not in lower, (
            f"session-start hook still contains forbidden phrase '{phrase}'."
        )


def test_session_start_hook_mentions_mcp_first_and_lazy_default() -> None:
    body = HOOK.read_text(encoding="utf-8").lower()
    assert "codebase-memory-mcp" in body
    assert "on demand" in body or "lazy" in body or "do not pre-load" in body


def test_session_start_hook_is_under_30_lines() -> None:
    lines = HOOK.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 30, f"session-start hook is {len(lines)} lines (>30)"
