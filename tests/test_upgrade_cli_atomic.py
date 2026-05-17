"""T043a / FR-031 / SC-013: cli.py::upgrade is atomic with rollback.

Distinct from test_upgrade_atomic.py (which exercises the orchestrator in
isolation). This module verifies that the actual ``dotnet-ai upgrade``
command, including the legacy copy_* pipeline, snapshots the managed tree
on entry and restores it on any exception.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from dotnet_ai_kit.cli import app

runner = CliRunner()


def _init_project(tmp_path: Path) -> Path:
    """Create a minimal initialized project the upgrade command will accept."""
    project = tmp_path / "proj"
    project.mkdir()
    (project / "Solution.sln").write_text("// stub", encoding="utf-8")
    result = runner.invoke(
        app,
        ["init", str(project), "--ai", "claude", "--json"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    # Force the version to look stale so upgrade runs.
    (project / ".dotnet-ai-kit" / "version.txt").write_text("0.0.1", encoding="utf-8")
    return project


def test_upgrade_rolls_back_on_copy_failure(tmp_path: Path, monkeypatch) -> None:
    project = _init_project(tmp_path)

    commands_dir = project / ".claude" / "commands"
    assert commands_dir.is_dir()
    pre_files = sorted(p.name for p in commands_dir.rglob("*.md"))
    assert pre_files, "init should have produced commands"

    # Sentinel: leave a known marker we'll check survives the failed upgrade.
    sentinel = commands_dir / "_sentinel.md"
    sentinel.write_text("PRE-UPGRADE\n", encoding="utf-8")

    monkeypatch.chdir(project)

    # Patch copy_commands so the upgrade flow blows up MID-DEPLOY (after the
    # snapshot, after some other copies might have run).
    def boom(*_args, **_kwargs):
        raise RuntimeError("simulated mid-upgrade failure")

    with patch("dotnet_ai_kit.cli.copy_commands", side_effect=boom):
        result = runner.invoke(
            app,
            ["upgrade"],
            catch_exceptions=True,
            color=False,
        )

    # The CLI must exit non-zero and the tree must be restored verbatim.
    assert result.exit_code != 0, result.output
    # The simulated exception should bubble up to typer (caught by runner).
    assert isinstance(result.exception, RuntimeError)
    assert "simulated mid-upgrade failure" in str(result.exception)

    # Sentinel survived → snapshot was taken AND restored.
    assert sentinel.is_file()
    assert sentinel.read_text(encoding="utf-8") == "PRE-UPGRADE\n"

    # The set of commands is exactly what init produced + the sentinel.
    post_files = sorted(p.name for p in commands_dir.rglob("*.md"))
    assert post_files == sorted([*pre_files, "_sentinel.md"])

    # No `.bak` directories or any other artifact may leak past rollback —
    # the snapshot is the single source of backup truth (FR-031 / SC-013).
    bak_artifacts = list((project / ".claude").glob("*.bak")) + list(
        (project / ".claude").rglob("*.bak")
    )
    assert not bak_artifacts, f".bak leaks past rollback: {bak_artifacts}"


def test_upgrade_backup_dir_rotates_to_three(tmp_path: Path, monkeypatch) -> None:
    project = _init_project(tmp_path)
    monkeypatch.chdir(project)

    # Run a successful upgrade 5 times; backup parent should retain ≤3.
    backup_root = project / ".dotnet-ai-kit" / "backups" / "upgrade"
    for _ in range(5):
        # Tamper version to keep triggering the upgrade path each time.
        (project / ".dotnet-ai-kit" / "version.txt").write_text("0.0.1", encoding="utf-8")
        result = runner.invoke(
            app,
            ["upgrade"],
            catch_exceptions=False,
            color=False,
        )
        assert result.exit_code == 0, result.output

    backups = sorted(p for p in backup_root.iterdir() if p.is_dir())
    assert len(backups) <= 3, f"expected ≤3 backups, found {len(backups)}"
