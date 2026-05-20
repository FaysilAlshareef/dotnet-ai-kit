"""T101 — `dotnet-ai check` filesystem inspection per clarify Q3 (commit 9).

Asserts that:
1. `check` reports plugin install per host via filesystem inspection only
   (no shell-out to the host CLI).
2. `csharp-ls` binary status uses `shutil.which()` per R10 / SC-011.
3. The command is read-only (does NOT mutate files).
"""

from __future__ import annotations

from pathlib import Path

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
    assert pre_files == post_files, f"check command created files: {post_files - pre_files}"


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

    assert host_cli_calls == [], f"check command shelled out to host CLI(s): {host_cli_calls}"


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


# ---------------------------------------------------------------------------
# B-CX-1 (round-2 codex review): host install verifies the plugin MANIFEST
# file, not just the install directory. Per FR-017 + clarify Q3, the host
# adapter MUST treat a bare directory as "not installed" — only the presence
# of `<host>-plugin/plugin.json` counts as a real install.
# ---------------------------------------------------------------------------

from dotnet_ai_kit.hosts.claude import ClaudeHost  # noqa: E402
from dotnet_ai_kit.hosts.codex import CodexHost  # noqa: E402
from dotnet_ai_kit.hosts.cursor import CursorHost  # noqa: E402


def _make_local_install(
    home: Path,
    host_dir: str,
    manifest_rel: str,
    *,
    with_manifest: bool,
) -> Path:
    """Create either a bare directory or a directory+manifest at the host's
    local install path. Returns the directory path."""
    install_dir = home / host_dir / "plugins" / "local" / "dotnet-ai-kit"
    install_dir.mkdir(parents=True, exist_ok=True)
    if with_manifest:
        manifest_path = install_dir / manifest_rel
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text('{"name": "dotnet-ai-kit"}', encoding="utf-8")
    return install_dir


def test_b_cx_1_claude_bare_directory_is_not_installed(tmp_path, monkeypatch):
    """B-CX-1 (FR-017): an empty local install dir without the plugin
    manifest must NOT be reported as installed."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    _make_local_install(tmp_path, ".claude", ".claude-plugin/plugin.json", with_manifest=False)
    status = ClaudeHost().verify_install()
    assert not status.installed, (
        f"Bare local-install directory must not be 'installed' per FR-017. Status: {status}"
    )


def test_b_cx_1_claude_with_manifest_is_installed(tmp_path, monkeypatch):
    """B-CX-1 positive case: directory + .claude-plugin/plugin.json → installed."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    _make_local_install(tmp_path, ".claude", ".claude-plugin/plugin.json", with_manifest=True)
    status = ClaudeHost().verify_install()
    assert status.installed, f"Local install with manifest must be detected. Status: {status}"


def test_b_cx_1_codex_bare_directory_is_not_installed(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    _make_local_install(tmp_path, ".codex", ".codex-plugin/plugin.json", with_manifest=False)
    status = CodexHost().verify_install()
    assert not status.installed


def test_b_cx_1_codex_with_manifest_is_installed(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    _make_local_install(tmp_path, ".codex", ".codex-plugin/plugin.json", with_manifest=True)
    status = CodexHost().verify_install()
    assert status.installed


def test_b_cx_1_cursor_bare_directory_is_not_installed(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    _make_local_install(tmp_path, ".cursor", ".cursor-plugin/plugin.json", with_manifest=False)
    status = CursorHost().verify_install()
    assert not status.installed


def test_b_cx_1_cursor_with_manifest_is_installed(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    _make_local_install(tmp_path, ".cursor", ".cursor-plugin/plugin.json", with_manifest=True)
    status = CursorHost().verify_install()
    assert status.installed
