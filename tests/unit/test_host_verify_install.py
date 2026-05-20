"""Tests for plugin-native host verify_install() marketplace scanning paths.

Covers the directory-walk branches inside ClaudeHost, CursorHost, and
CodexHost that are only exercised when the plugin cache contains a properly
structured install (marketplace_dir / plugin / version / manifest).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dotnet_ai_kit.hosts.claude import ClaudeHost
from dotnet_ai_kit.hosts.codex import CodexHost
from dotnet_ai_kit.hosts.cursor import CursorHost


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_marketplace_install(
    cache_root: Path,
    marketplace: str,
    plugin: str,
    version: str,
    manifest_filename: str,
) -> Path:
    """Create the nested cache structure and return the version dir."""
    version_dir = cache_root / marketplace / plugin / version
    manifest_dir = version_dir / manifest_filename.rsplit("/", 1)[0]
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (version_dir / manifest_filename.rsplit("/", 1)[0] / manifest_filename.rsplit("/", 1)[-1]).touch()
    return version_dir


def _make_manifest(version_dir: Path, subdir: str) -> None:
    """Create a plugin.json at version_dir / subdir / plugin.json."""
    d = version_dir / subdir
    d.mkdir(parents=True, exist_ok=True)
    (d / "plugin.json").touch()


# ---------------------------------------------------------------------------
# ClaudeHost
# ---------------------------------------------------------------------------


class TestClaudeHostVerifyInstall:
    def test_not_installed_returns_false(self, tmp_path: Path, monkeypatch) -> None:
        host = ClaudeHost()
        cache = tmp_path / "cache"
        local = tmp_path / "local" / "dotnet-ai-kit"
        monkeypatch.setattr(host, "install_paths", lambda: [cache, local])

        status = host.verify_install()
        assert not status.installed
        assert "no install found" in status.notes

    def test_local_install_detected(self, tmp_path: Path, monkeypatch) -> None:
        host = ClaudeHost()
        cache = tmp_path / "cache"
        local = tmp_path / "local" / "dotnet-ai-kit"
        (local / ".claude-plugin").mkdir(parents=True)
        (local / ".claude-plugin" / "plugin.json").touch()
        monkeypatch.setattr(host, "install_paths", lambda: [cache, local])

        status = host.verify_install()
        assert status.installed
        assert "local dev install" in status.notes

    def test_marketplace_install_detected(self, tmp_path: Path, monkeypatch) -> None:
        """Covers lines 66-80, 89 — marketplace cache directory walk."""
        host = ClaudeHost()
        cache = tmp_path / "cache"
        local = tmp_path / "local" / "dotnet-ai-kit"

        # Build marketplace structure: cache/mymarket/dotnet-ai-kit/1.0.0/.claude-plugin/plugin.json
        version_dir = cache / "mymarket" / "dotnet-ai-kit" / "1.0.0"
        _make_manifest(version_dir, ".claude-plugin")
        monkeypatch.setattr(host, "install_paths", lambda: [cache, local])

        status = host.verify_install()
        assert status.installed
        assert "marketplace cache" in status.notes
        assert "1 version(s)" in status.notes

    def test_marketplace_dir_without_manifest_not_counted(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """A version dir missing .claude-plugin/plugin.json must NOT be counted."""
        host = ClaudeHost()
        cache = tmp_path / "cache"
        local = tmp_path / "local" / "dotnet-ai-kit"

        # Create the version dir but omit the manifest file
        version_dir = cache / "mymarket" / "dotnet-ai-kit" / "1.0.0"
        version_dir.mkdir(parents=True)
        monkeypatch.setattr(host, "install_paths", lambda: [cache, local])

        status = host.verify_install()
        assert not status.installed


# ---------------------------------------------------------------------------
# CursorHost
# ---------------------------------------------------------------------------


class TestCursorHostVerifyInstall:
    def test_not_installed_returns_false(self, tmp_path: Path, monkeypatch) -> None:
        host = CursorHost()
        cache = tmp_path / "cache"
        local = tmp_path / "local" / "dotnet-ai-kit"
        monkeypatch.setattr(host, "install_paths", lambda: [cache, local])

        status = host.verify_install()
        assert not status.installed
        assert "no Cursor install found" in status.notes

    def test_marketplace_install_detected(self, tmp_path: Path, monkeypatch) -> None:
        """Covers lines 55-68, 76 — Cursor marketplace cache directory walk."""
        host = CursorHost()
        cache = tmp_path / "cache"
        local = tmp_path / "local" / "dotnet-ai-kit"

        version_dir = cache / "mymarket" / "dotnet-ai-kit" / "1.0.0"
        _make_manifest(version_dir, ".cursor-plugin")
        monkeypatch.setattr(host, "install_paths", lambda: [cache, local])

        status = host.verify_install()
        assert status.installed
        assert "Cursor marketplace cache" in status.notes

    def test_local_install_detected(self, tmp_path: Path, monkeypatch) -> None:
        host = CursorHost()
        cache = tmp_path / "cache"
        local = tmp_path / "local" / "dotnet-ai-kit"
        (local / ".cursor-plugin").mkdir(parents=True)
        (local / ".cursor-plugin" / "plugin.json").touch()
        monkeypatch.setattr(host, "install_paths", lambda: [cache, local])

        status = host.verify_install()
        assert status.installed
        assert "Cursor local dev install" in status.notes


# ---------------------------------------------------------------------------
# CodexHost
# ---------------------------------------------------------------------------


class TestCodexHostVerifyInstall:
    def test_not_installed_returns_false(self, tmp_path: Path, monkeypatch) -> None:
        host = CodexHost()
        cache = tmp_path / "cache"
        local = tmp_path / "local" / "dotnet-ai-kit"
        monkeypatch.setattr(host, "install_paths", lambda: [cache, local])

        status = host.verify_install()
        assert not status.installed
        assert "no Codex install found" in status.notes

    def test_marketplace_install_detected(self, tmp_path: Path, monkeypatch) -> None:
        """Covers lines 60-73, 81 — Codex marketplace cache directory walk."""
        host = CodexHost()
        cache = tmp_path / "cache"
        local = tmp_path / "local" / "dotnet-ai-kit"

        version_dir = cache / "mymarket" / "dotnet-ai-kit" / "1.0.0"
        _make_manifest(version_dir, ".codex-plugin")
        monkeypatch.setattr(host, "install_paths", lambda: [cache, local])

        status = host.verify_install()
        assert status.installed
        assert "Codex marketplace cache" in status.notes

    def test_local_install_detected(self, tmp_path: Path, monkeypatch) -> None:
        """Covers line 81 — local dev install notes path."""
        host = CodexHost()
        cache = tmp_path / "cache"
        local = tmp_path / "local" / "dotnet-ai-kit"
        (local / ".codex-plugin").mkdir(parents=True)
        (local / ".codex-plugin" / "plugin.json").touch()
        monkeypatch.setattr(host, "install_paths", lambda: [cache, local])

        status = host.verify_install()
        assert status.installed
        assert "Codex local dev install" in status.notes
