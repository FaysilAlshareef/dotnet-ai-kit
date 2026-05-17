"""T101 — `dotnet-ai check` filesystem inspection per clarify Q3 (commit 9).

Asserts that:
1. `check` reports plugin install per host via filesystem inspection only
   (no shell-out to the host CLI).
2. `csharp-ls` binary status uses `shutil.which()` per R10 / SC-011.
3. The command is read-only (does NOT mutate files).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from dotnet_ai_kit.cli import app

runner = CliRunner()


def test_check_completes_on_empty_project(tmp_path: Path) -> None:
    """`check` returns an exit code even on a fresh empty directory."""
    result = runner.invoke(app, ["check", str(tmp_path)])

    # Exit code is non-zero because plugin install is missing, but command
    # MUST have produced output (no exceptions, no hangs).
    assert result.exit_code in (10, 11, 14)  # any of the documented codes


def test_check_does_not_mutate_files(tmp_path: Path) -> None:
    """`check` is read-only per contract:90 — MUST NOT create files."""
    pre_files = set(tmp_path.rglob("*"))

    runner.invoke(app, ["check", str(tmp_path)])

    post_files = set(tmp_path.rglob("*"))
    assert pre_files == post_files, (
        f"check command created files: {post_files - pre_files}"
    )


def test_check_does_not_shell_out_for_plugin_install(monkeypatch, tmp_path: Path) -> None:
    """Per clarify Q3: check MUST NOT shell out to host CLIs (claude/codex/cursor).

    We assert that `subprocess.run` is NOT invoked with any host-CLI command
    during plugin-install verification.
    """
    import subprocess as _sp

    original_run = _sp.run
    host_cli_calls: list[list] = []

    def patched_run(cmd, *args, **kwargs):
        # Track invocations that include known host CLIs
        if isinstance(cmd, (list, tuple)) and len(cmd) > 0:
            first = str(cmd[0]).lower()
            if any(host in first for host in ("claude", "codex", "cursor")):
                host_cli_calls.append(list(cmd))
        return original_run(cmd, *args, **kwargs)

    monkeypatch.setattr(_sp, "run", patched_run)
    runner.invoke(app, ["check", str(tmp_path)])

    assert host_cli_calls == [], (
        f"check command shelled out to host CLI(s): {host_cli_calls}"
    )


def test_check_uses_shutil_which_for_binary_detection() -> None:
    """The check command MUST detect csharp-ls via shutil.which (R10)."""
    # Importing the cli module triggers no side effects; we verify the
    # function uses `shutil.which` by inspecting the implementation
    import inspect

    from dotnet_ai_kit import cli

    src = inspect.getsource(cli.check)
    assert "_shutil.which" in src or "shutil.which" in src, (
        "check command must use shutil.which() for binary detection per R10"
    )
