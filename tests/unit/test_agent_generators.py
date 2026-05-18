"""T037 — per-host agent generators (feature 019 commit 4 scope: Claude only).

Asserts:
- `generate_claude_agent(source)` produces Claude-shape frontmatter.
- The Claude path NEVER introduces a `skills:` preload field (FR-027 guard).
- The markdown body is copied verbatim.
- Unknown `host_overrides.claude.<key>` fields are rejected (FR-027).
- Cross-host leakage prevented: `host_overrides.cursor.*` fields do NOT leak
  into Claude output.

Cursor (T058 / commit 6) and Copilot (T071 / commit 7) generators are
covered by their own test additions in their commits; this file is the
test for the Claude path landed at commit 4.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from dotnet_ai_kit.agent_generators import (
    _CLAUDE_ALLOW_LIST,
    AgentSource,
    generate_claude_agent,
    generate_codex_agent,
    generate_copilot_agent,
    generate_cursor_agent,
)


def _write_agent(
    tmp_path: Path, name: str, frontmatter: dict, body: str = "# Body\n\nText.\n"
) -> Path:
    """Create a source agent file and return its path."""
    yaml_block = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    content = f"---\n{yaml_block}---\n\n{body}"
    path = tmp_path / f"{name}.md"
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# AgentSource parser
# ---------------------------------------------------------------------------


def test_agent_source_parses_required_fields(tmp_path: Path) -> None:
    path = _write_agent(
        tmp_path,
        "test-agent",
        {"name": "test-agent", "description": "Test description"},
    )
    src = AgentSource.from_file(path)
    assert src.name == "test-agent"
    assert src.description == "Test description"
    assert "# Body" in src.body


def test_agent_source_rejects_missing_frontmatter(tmp_path: Path) -> None:
    path = tmp_path / "no-fm.md"
    path.write_text("Just a body, no frontmatter\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no YAML frontmatter"):
        AgentSource.from_file(path)


def test_agent_source_rejects_missing_name(tmp_path: Path) -> None:
    path = _write_agent(tmp_path, "x", {"description": "no name"})
    with pytest.raises(ValueError, match="missing required `name`"):
        AgentSource.from_file(path)


def test_agent_source_rejects_missing_description(tmp_path: Path) -> None:
    path = _write_agent(tmp_path, "x", {"name": "x"})
    with pytest.raises(ValueError, match="missing required `description`"):
        AgentSource.from_file(path)


# ---------------------------------------------------------------------------
# Claude generator (commit 4 scope)
# ---------------------------------------------------------------------------


def test_generate_claude_agent_minimal(tmp_path: Path) -> None:
    """Source with only required fields produces a minimal Claude file."""
    path = _write_agent(tmp_path, "minimal", {"name": "minimal", "description": "Minimal"})
    output = generate_claude_agent(path)
    assert output.startswith("---\n")
    assert "name: minimal" in output
    assert "description: Minimal" in output
    assert "# Body" in output  # body preserved verbatim


def test_generate_claude_agent_lifts_host_overrides_claude(tmp_path: Path) -> None:
    """`host_overrides.claude.*` fields are lifted to top-level frontmatter."""
    path = _write_agent(
        tmp_path,
        "expert",
        {
            "name": "expert",
            "description": "Expert agent",
            "host_overrides": {
                "claude": {
                    "role": "advisory",
                    "expertise": ["clean-arch", "ddd"],
                    "complexity": "high",
                    "max_iterations": 20,
                }
            },
        },
    )
    output = generate_claude_agent(path)
    assert "role: advisory" in output
    assert "complexity: high" in output
    assert "max_iterations: 20" in output


def test_generate_claude_agent_rejects_unknown_field(tmp_path: Path) -> None:
    """Per FR-027: unknown `host_overrides.claude.<key>` fields MUST be rejected."""
    path = _write_agent(
        tmp_path,
        "bad",
        {
            "name": "bad",
            "description": "Bad",
            "host_overrides": {"claude": {"role": "advisory", "made_up_field": "x"}},
        },
    )
    with pytest.raises(ValueError, match="not in the documented allow-list"):
        generate_claude_agent(path)


def test_generate_claude_agent_never_emits_skills_field(tmp_path: Path) -> None:
    """FR-027 regression guard: Claude path MUST NOT emit `skills:` frontmatter."""
    path = _write_agent(
        tmp_path,
        "no-skills",
        {
            "name": "no-skills",
            "description": "Should never get skills",
            "host_overrides": {
                "claude": {
                    "role": "advisory",
                    "expertise": ["skill-a", "skill-b"],  # expertise allowed, skills not
                }
            },
        },
    )
    output = generate_claude_agent(path)
    # Parse the frontmatter from the output and verify no `skills:` key
    head, sep, _body = output.partition("---\n")
    assert sep == "---\n"
    fm_block, sep, _ = output[len(head) + len(sep) :].partition("---\n")
    fm = yaml.safe_load(fm_block)
    assert "skills" not in fm, (
        "FR-027 regression: Claude generator emitted forbidden `skills` frontmatter"
    )


def test_generate_claude_agent_no_cross_host_leak(tmp_path: Path) -> None:
    """Cursor- or Copilot-specific fields MUST NOT leak into Claude output."""
    path = _write_agent(
        tmp_path,
        "iso",
        {
            "name": "iso",
            "description": "Isolation test",
            "host_overrides": {
                "claude": {"role": "advisory"},
                "cursor": {"model": "claude-sonnet-4", "readonly": False},
                "copilot": {"target": "solution-root"},
            },
        },
    )
    output = generate_claude_agent(path)
    assert "model:" not in output
    assert "readonly:" not in output
    assert "target:" not in output


def test_generate_claude_agent_body_is_verbatim(tmp_path: Path) -> None:
    """The body MUST be copied verbatim — no substitution, no truncation."""
    body = (
        "# .NET Architecture Specialist\n\n"
        "**Role**: Expert in generic .NET architecture patterns\n\n"
        "## Responsibilities\n"
        "- Apply Clean Architecture\n"
        "- Apply VSA\n"
    )
    path = _write_agent(
        tmp_path,
        "body-test",
        {"name": "body-test", "description": "Body verbatim test"},
        body=body,
    )
    output = generate_claude_agent(path)
    assert body in output


# ---------------------------------------------------------------------------
# Codex generator — explicit NotImplementedError per OOS-004
# ---------------------------------------------------------------------------


def test_generate_codex_agent_raises_not_implemented(tmp_path: Path) -> None:
    """Per OOS-004 / FR-035: Codex native agents are deferred to v1.1."""
    path = _write_agent(tmp_path, "x", {"name": "x", "description": "x"})
    with pytest.raises(NotImplementedError, match="OOS-004"):
        generate_codex_agent(path)


# ---------------------------------------------------------------------------
# Cursor + Copilot generators (smoke — full coverage in commits 6 + 7)
# ---------------------------------------------------------------------------


def test_generate_cursor_agent_raises_until_a005_passes(tmp_path: Path) -> None:
    """T170c (commit 25, OOS-005 fail-safe default): generate_cursor_agent()
    MUST raise NotImplementedError until the A-005 spike fixture outcome JSON
    flips to `passed`. The previous shape-emitting behavior is restored by
    T171 (PASS branch) once Cursor's loader is verified in CI.
    """
    import pytest  # noqa: PLC0415

    path = _write_agent(
        tmp_path,
        "cur",
        {
            "name": "cur",
            "description": "Cursor agent",
            "host_overrides": {
                "cursor": {"model": "claude-sonnet-4", "readonly": False},
                "claude": {"role": "advisory"},
            },
        },
    )
    with pytest.raises(NotImplementedError, match="A-005"):
        generate_cursor_agent(path)


def test_generate_copilot_agent_emits_copilot_allow_list(tmp_path: Path) -> None:
    """Copilot allow-list: target, tools, model, etc. (per data-model § 7)."""
    path = _write_agent(
        tmp_path,
        "cop",
        {
            "name": "cop",
            "description": "Copilot agent",
            "host_overrides": {
                "copilot": {"target": "solution-root"},
                "claude": {"role": "advisory"},  # MUST NOT leak into Copilot output
            },
        },
    )
    output = generate_copilot_agent(path)
    assert "target: solution-root" in output
    assert "role:" not in output  # no claude leak


def test_claude_allow_list_completeness() -> None:
    """The Claude allow-list MUST match `contracts/agent-source.contract.md`."""
    expected = {"name", "description", "role", "expertise", "complexity", "max_iterations"}
    assert set(_CLAUDE_ALLOW_LIST) == expected
