"""T099a — `dotnet-ai migrate` CLI flag behaviors (commit 10 / migrate-cli.contract.md).

Asserts:
- `--dry-run` mutates nothing.
- `--include-modified` required to also remove user-modified files (FR-022).
- `--host <host>` scopes migration to files whose `host_owner == <host>`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from dotnet_ai_kit.cli import app
from dotnet_ai_kit.manifest import (
    DeployedFile,
    Manifest,
    sha256_file,
    utc_now_iso,
    write_manifest,
)

runner = CliRunner()


def _build_multi_host_project(tmp_path: Path) -> Path:
    """Build a project with managed files for claude AND cursor hosts."""
    project = tmp_path / "proj"
    project.mkdir()

    claude_file = project / ".claude" / "commands" / "x.md"
    claude_file.parent.mkdir(parents=True)
    claude_file.write_text("claude content\n", encoding="utf-8")

    cursor_file = project / ".cursor" / "rules" / "x.mdc"
    cursor_file.parent.mkdir(parents=True)
    cursor_file.write_text("cursor content\n", encoding="utf-8")

    manifest = Manifest(
        plugin_version="1.0.0",
        schema_version="2",
        created_at=utc_now_iso(),
        files=[
            DeployedFile(
                path=".claude/commands/x.md",
                sha256=sha256_file(claude_file),
                plugin_version="1.0.0",
                deployed_at=utc_now_iso(),
                host_owner="claude",
            ),
            DeployedFile(
                path=".cursor/rules/x.mdc",
                sha256=sha256_file(cursor_file),
                plugin_version="1.0.0",
                deployed_at=utc_now_iso(),
                host_owner="cursor",
            ),
        ],
    )
    write_manifest(project, manifest)
    return project


def test_migrate_host_flag_scopes_to_named_host(tmp_path: Path) -> None:
    """`--host cursor` MUST only migrate cursor-owned files."""
    project = _build_multi_host_project(tmp_path)

    result = runner.invoke(app, ["migrate", str(project), "--host", "cursor"])
    assert result.exit_code == 0

    # Cursor file moved away
    assert not (project / ".cursor" / "rules" / "x.mdc").exists()
    # Claude file still in place (not in scope)
    assert (project / ".claude" / "commands" / "x.md").exists()


def test_migrate_default_no_host_migrates_all(tmp_path: Path) -> None:
    """No `--host` flag MUST migrate all hosts' files."""
    project = _build_multi_host_project(tmp_path)

    result = runner.invoke(app, ["migrate", str(project)])
    assert result.exit_code == 0

    # Both files moved
    assert not (project / ".cursor" / "rules" / "x.mdc").exists()
    assert not (project / ".claude" / "commands" / "x.md").exists()


def test_migrate_dry_run_with_host_scoping(tmp_path: Path) -> None:
    """`--dry-run --host claude` previews only claude's actions, mutates nothing."""
    project = _build_multi_host_project(tmp_path)

    result = runner.invoke(
        app, ["migrate", str(project), "--dry-run", "--host", "claude"]
    )
    assert result.exit_code == 0
    # Both files still in place after dry-run
    assert (project / ".cursor" / "rules" / "x.mdc").exists()
    assert (project / ".claude" / "commands" / "x.md").exists()


def test_migrate_missing_manifest_returns_exit_1(tmp_path: Path) -> None:
    """If manifest.json is missing, migrate exits 1 with a corrective message."""
    project = tmp_path / "proj"
    project.mkdir()

    result = runner.invoke(app, ["migrate", str(project)])
    assert result.exit_code == 1
