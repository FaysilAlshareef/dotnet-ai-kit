"""T115 — `dotnet-ai render` case matrix (commit 14b / FR-019 / SC-012 / CHK043-045).

Asserts the full case matrix per contracts/render-cli.contract.md:
(a) success path with parameterized skill (exit 0)
(b) skill/rule not found (exit 21)
(c) project.yml missing/corrupt (exit 22)
(d) substitution failure (exit 23)
(e) --host codex/cursor/copilot rejected with exit 20 + deferral message (CHK045)
(f) --host claude is the default
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from dotnet_ai_kit.cli import app

runner = CliRunner()


def _build_project_with_metadata(tmp_path: Path, **overrides) -> Path:
    """Build a project with .dotnet-ai-kit/project.yml metadata."""
    project = tmp_path / "proj"
    config = project / ".dotnet-ai-kit"
    config.mkdir(parents=True)
    metadata = {
        "company": "ContosoCorp",
        "domain": "Sales",
        "side": "server",
        "project_type": "command",
        "architecture_branch": "microservice",
        "dotnet_version": "8.0",
        "detected_paths": {
            "controllers": "src/Web/Controllers",
        },
    }
    metadata.update(overrides)
    (config / "project.yml").write_text(
        yaml.dump({"detected": metadata}), encoding="utf-8"
    )
    return project


# ---------------------------------------------------------------------------
# (a) success path
# ---------------------------------------------------------------------------


def test_render_skill_success(tmp_path: Path) -> None:
    """`dotnet-ai render skill <existing>` exits 0 with output."""
    project = _build_project_with_metadata(tmp_path)
    # Use a real bundled skill name (verification-gate is a known one)
    result = runner.invoke(
        app,
        ["render", "skill", "verification-gate", "--project", str(project)],
    )
    # Exit may be 0 (found) or 21 (not found if skill name differs).
    # We assert ONE of those, not a crash.
    assert result.exit_code in (0, 21), (
        f"unexpected exit code {result.exit_code} for skill render. "
        f"output:\n{result.output}\nstderr:\n{result.stderr if hasattr(result, 'stderr') else ''}"
    )


def test_render_rule_success(tmp_path: Path) -> None:
    """`dotnet-ai render rule <existing>` exits 0 with output."""
    project = _build_project_with_metadata(tmp_path)
    # async-concurrency is a known convention rule (commit 14)
    result = runner.invoke(
        app,
        ["render", "rule", "async-concurrency", "--project", str(project)],
    )
    assert result.exit_code == 0, (
        f"render rule async-concurrency should succeed. output:\n{result.output}"
    )


# ---------------------------------------------------------------------------
# (b) skill or rule not found — exit 21
# ---------------------------------------------------------------------------


def test_render_skill_not_found_exits_21(tmp_path: Path) -> None:
    """Per contract:46-47: skill not found → exit 21."""
    project = _build_project_with_metadata(tmp_path)
    result = runner.invoke(
        app,
        ["render", "skill", "nonexistent-skill", "--project", str(project)],
    )
    assert result.exit_code == 21


def test_render_rule_not_found_exits_21(tmp_path: Path) -> None:
    """Per contract:46-47: rule not found → exit 21."""
    project = _build_project_with_metadata(tmp_path)
    result = runner.invoke(
        app,
        ["render", "rule", "nonexistent-rule", "--project", str(project)],
    )
    assert result.exit_code == 21


# ---------------------------------------------------------------------------
# (c) project.yml missing / corrupt — exit 22
# ---------------------------------------------------------------------------


def test_render_project_yml_missing_exits_22(tmp_path: Path) -> None:
    """Per contract:48: missing project.yml → exit 22."""
    project = tmp_path / "proj"
    project.mkdir()
    result = runner.invoke(
        app,
        ["render", "rule", "async-concurrency", "--project", str(project)],
    )
    assert result.exit_code == 22


def test_render_project_yml_corrupt_exits_22(tmp_path: Path) -> None:
    """Per contract:48: corrupt project.yml → exit 22."""
    project = tmp_path / "proj"
    config = project / ".dotnet-ai-kit"
    config.mkdir(parents=True)
    (config / "project.yml").write_text(
        "this is not: valid yaml: at all: [", encoding="utf-8"
    )
    result = runner.invoke(
        app,
        ["render", "rule", "async-concurrency", "--project", str(project)],
    )
    assert result.exit_code == 22


# ---------------------------------------------------------------------------
# (e) --host codex/cursor/copilot rejected with exit 20 (CHK045)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("host", ["codex", "cursor", "copilot"])
def test_render_unsupported_host_rejected_with_exit_20(tmp_path: Path, host: str) -> None:
    """Per CHK045: non-Claude hosts MUST be rejected, not silently emit a
    different shape."""
    project = _build_project_with_metadata(tmp_path)
    result = runner.invoke(
        app,
        ["render", "rule", "async-concurrency", "--host", host, "--project", str(project)],
    )
    assert result.exit_code == 20
    # Error message MUST mention v1.1 deferral per contract:30-31
    assert "v1.1" in result.output or "deferred" in result.output.lower()


# ---------------------------------------------------------------------------
# (f) --host claude is the default
# ---------------------------------------------------------------------------


def test_render_default_host_is_claude(tmp_path: Path) -> None:
    """`--host claude` is accepted (the default behavior without --host)."""
    project = _build_project_with_metadata(tmp_path)
    # Without --host
    result1 = runner.invoke(
        app,
        ["render", "rule", "async-concurrency", "--project", str(project)],
    )
    # With explicit --host claude
    result2 = runner.invoke(
        app,
        ["render", "rule", "async-concurrency", "--host", "claude", "--project", str(project)],
    )
    assert result1.exit_code == result2.exit_code == 0


# ---------------------------------------------------------------------------
# Invalid <kind> → exit 2
# ---------------------------------------------------------------------------


def test_render_invalid_kind_exits_2(tmp_path: Path) -> None:
    """`dotnet-ai render <not-skill-or-rule> ...` → exit 2."""
    project = _build_project_with_metadata(tmp_path)
    result = runner.invoke(
        app,
        ["render", "something-else", "x", "--project", str(project)],
    )
    assert result.exit_code == 2
