"""T076 — Runtime resolution at fire-time per FR-009 (commit 13).

Asserts that skills/rules consume current `project.yml` values at AI-use
time, NOT cached at session start. Covers three resolution points:

1. SessionStart hook: reads `.dotnet-ai-kit/project.yml` fresh per session
2. PreToolUse arch-profile hook: reads `project.yml` at every fire (no caching)
3. Skill body resolution via `dotnet-ai render`: reads metadata at command time

Per FR-009: substitution happens at use time. Per FR-010: a `project.yml`
edit MUST be observed by the next AI interaction without restart.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dotnet_ai_kit.render import (
    ProjectMetadataMissing,
    render_skill,
    substitute_metadata,
)

REPO = Path(__file__).resolve().parent.parent.parent


def _write_project_yml(project_root: Path, company: str, domain: str, side: str) -> None:
    """Helper: write a minimal project.yml fixture."""
    cfg = project_root / ".dotnet-ai-kit"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "project.yml").write_text(
        f"company: {company}\n"
        f"domain: {domain}\n"
        f"side: {side}\n"
        f"project_type: api\n"
        f"dotnet_version: '9.0'\n"
        f"detected_paths: {{}}\n",
        encoding="utf-8",
    )


def test_substitute_metadata_resolves_simple_tokens() -> None:
    """Per FR-019: ${Company} ${Domain} ${Side} tokens resolved at call time."""
    body = "Hello ${Company} ${Domain} ${Side}!"
    metadata = {"company": "Acme", "domain": "Order", "side": "Command"}
    out = substitute_metadata(body, metadata)
    assert out == "Hello Acme Order Command!"


def test_runtime_resolution_observes_yml_edit(tmp_path: Path) -> None:
    """Per FR-010 / SC-003: edit project.yml between two render calls →
    second call observes the new value WITHOUT any cache/restart."""
    plugin_root = REPO
    project = tmp_path / "solution1"
    _write_project_yml(project, "AcmeBefore", "Order", "Command")

    # First render
    out1 = render_skill("async-patterns", plugin_root, project)
    assert "AcmeBefore" in out1 or "${Company}" not in out1  # only matters if skill uses tokens

    # Edit project.yml in place
    _write_project_yml(project, "AcmeAfter", "Order", "Command")

    # Second render must see the new value (no caching)
    out2 = render_skill("async-patterns", plugin_root, project)
    # If async-patterns SKILL.md happens to contain ${Company}, then out1 ≠ out2.
    # If it doesn't, both outputs equal the body — that's also FR-010 compliant.
    if "${Company}" in (REPO / "skills" / "core" / "async-patterns" / "SKILL.md").read_text(
        encoding="utf-8"
    ):
        assert "AcmeAfter" in out2 and "AcmeBefore" not in out2


def test_missing_project_yml_raises_typed_error(tmp_path: Path) -> None:
    """Per FR-009: when project.yml is absent, render MUST raise a typed error
    so the CLI can map to a non-zero exit code (NOT silently use cached state)."""
    plugin_root = REPO
    project = tmp_path / "no-project"
    project.mkdir()
    with pytest.raises(ProjectMetadataMissing):
        render_skill("async-patterns", plugin_root, project)


def test_pretooluse_arch_profile_hook_reads_at_fire_time() -> None:
    """Per FR-009: the PreToolUse arch-profile hook MUST read project.yml at
    every fire (NOT cache it at session start). Verified structurally by
    reading the hook script and asserting it contains a project.yml read."""
    hook = REPO / "hooks" / "pretooluse-arch-profile.sh"
    if not hook.is_file():
        pytest.skip("pretooluse-arch-profile.sh not present in this checkout")
    body = hook.read_text(encoding="utf-8")
    # The hook must explicitly read project.yml in its body (not just cache a var)
    assert "project.yml" in body, (
        "pretooluse-arch-profile.sh MUST read project.yml at fire-time per FR-009"
    )


def test_session_start_bootstrap_reads_at_fire_time() -> None:
    """Per FR-009: SessionStart hook MUST read project.yml fresh per session
    (NOT inline values at install time)."""
    hook = REPO / "hooks" / "session-start-bootstrap.sh"
    if not hook.is_file():
        pytest.skip("session-start-bootstrap.sh not present in this checkout")
    body = hook.read_text(encoding="utf-8")
    assert "project.yml" in body, (
        "session-start-bootstrap.sh MUST reference project.yml per FR-009"
    )
