"""Codex CLI host adapter (feature 019 / T047).

Implements the `Host` interface for Codex CLI's plugin model:
- Plugin cache path: `~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/`
  (per research R7 / Codex docs `developers.openai.com/codex/plugins/build`).
- Codex documented primitives: skills, MCP, hooks. No native agents (OOS-004).
- Per-solution writes: NONE under feature 019 — the plugin install path
  serves skills/MCP/hooks; the legacy AGENTS.md emitter (copy_commands_codex)
  was removed in T049.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from dotnet_ai_kit.hosts.base import Host, InstallStatus

logger = logging.getLogger(__name__)


class CodexHost(Host):
    """Adapter for Codex CLI."""

    name = "codex"

    def install_paths(self) -> list[Path]:
        """Codex plugin cache paths under ~/.codex/ per research R7."""
        home = Path.home() / ".codex"
        return [
            home / "plugins" / "cache",  # marketplace install root
            home / "plugins" / "local" / "dotnet-ai-kit",  # developer symlink
        ]

    def verify_install(self) -> InstallStatus:
        """Filesystem inspection only — clarify Q3 / no shell-out."""
        marketplace_cache, local_path = self.install_paths()

        marketplace_present = False
        marketplace_versions: list[Path] = []
        if marketplace_cache.is_dir():
            for marketplace_dir in marketplace_cache.iterdir():
                if not marketplace_dir.is_dir():
                    continue
                plugin_dir = marketplace_dir / "dotnet-ai-kit"
                if plugin_dir.is_dir():
                    marketplace_present = True
                    marketplace_versions.extend(
                        p for p in plugin_dir.iterdir() if p.is_dir()
                    )

        local_present = local_path.is_dir()
        installed = marketplace_present or local_present

        notes_parts = []
        if marketplace_present:
            notes_parts.append(
                f"Codex marketplace cache: {len(marketplace_versions)} version(s) found"
            )
        if local_present:
            notes_parts.append(f"Codex local dev install at {local_path}")
        if not installed:
            notes_parts.append(
                "no Codex install found — run `codex plugin install` or symlink under "
                f"{local_path.parent}"
            )

        return InstallStatus(
            host_name=self.name,
            installed=installed,
            expected_paths=[marketplace_cache, local_path],
            missing_paths=[
                p for p in (marketplace_cache, local_path) if not p.exists()
            ] if not installed else [],
            notes="; ".join(notes_parts),
        )

    def write_per_solution_files(
        self,
        project_root: Path,
        *,
        permission_profile: Optional[str] = None,
    ) -> list[Path]:
        """Codex has NO per-solution writes under feature 019.

        Per FR-005: the plugin install path serves skills/MCP/hooks. The
        legacy `copy_commands_codex` (root-AGENTS.md emitter) was deleted
        in T049 — Codex now relies on the plugin manifest exclusively.
        """
        logger.debug(
            "CodexHost.write_per_solution_files() is a no-op (plugin install "
            "serves Codex skills/MCP/hooks). project_root=%s",
            project_root,
        )
        return []
