"""Cursor host adapter (feature 019 / T055).

Implements the `Host` interface for Cursor's plugin model:
- Plugin cache paths: `~/.cursor/plugins/cache/<marketplace>/<plugin>/<version>/`
  and `~/.cursor/plugins/local/<plugin>/` (developer symlink) per research R7.
- Cursor manifest declares `agents: "./agents/"`, `rules: "./rules/cursor/"`,
  `skills: "./skills/"`, `mcpServers: "./.mcp.json"`, `hooks: "./hooks/hooks.json"`.
- Per-solution writes: NONE under feature 019 — Cursor consumes the plugin
  install path's content. The legacy one-blob `.cursor/rules/dotnet-ai-kit.mdc`
  emitter is being replaced by per-rule `.mdc` files (T056); both are
  cleaned up by the migrate command per R12.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from dotnet_ai_kit.hosts.base import Host, InstallStatus

logger = logging.getLogger(__name__)


class CursorHost(Host):
    """Adapter for Cursor."""

    name = "cursor"

    def install_paths(self) -> list[Path]:
        """Cursor plugin cache paths under ~/.cursor/ per research R7."""
        home = Path.home() / ".cursor"
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
                f"Cursor marketplace cache: {len(marketplace_versions)} version(s) found"
            )
        if local_present:
            notes_parts.append(f"Cursor local dev install at {local_path}")
        if not installed:
            notes_parts.append(
                "no Cursor install found — run Cursor plugin install or symlink under "
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
        """Cursor has NO per-solution writes under feature 019.

        Per FR-005: the plugin install path serves rules/skills/MCP/hooks/agents.
        The legacy `.cursor/rules/dotnet-ai-kit.mdc` one-blob output is left
        as legacy-managed (cleaned by the migrate command per R12).
        """
        logger.debug(
            "CursorHost.write_per_solution_files() is a no-op (plugin install "
            "serves rules/skills/MCP/hooks/agents). project_root=%s",
            project_root,
        )
        return []
