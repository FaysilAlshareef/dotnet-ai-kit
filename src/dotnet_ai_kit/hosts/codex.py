"""Codex CLI host adapter (feature 019 / T047 + OOS-004 partial lift).

Implements the `Host` interface for Codex CLI's plugin model:
- Plugin cache path: `~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/`
  (per research R7 / Codex docs `developers.openai.com/codex/plugins/build`).
- Plugin-bundled primitives: skills, MCP, hooks. Plugin manifest does NOT
  bundle subagents (no documented `agents` field — OOS-004 plugin-bundling
  portion still deferred to v1.1).
- Per-solution writes (OOS-004 partial lift, May 2026): `.codex/agents/*.toml`
  subagent files rendered from `agents-source/<name>.md` per
  `https://developers.openai.com/codex/subagents` (retrieved 2026-05-19).
  Codex loads subagents from `~/.codex/agents/` (user) or `.codex/agents/`
  (project) — the kit writes them at the project scope so they ride with
  the solution and survive without per-user installation steps.
- The legacy AGENTS.md emitter (copy_commands_codex) was removed in T049
  and is NOT restored — root AGENTS.md remains user-owned per FR-008 / A-008.
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

    def verify_install(self, project_root: Path | None = None) -> InstallStatus:
        """Filesystem inspection only — clarify Q3 / no shell-out.

        Per FR-017 + clarify Q3 (`spec.md:174, :28`), the plugin is considered
        installed only if the Codex plugin manifest file
        (`.codex-plugin/plugin.json`) is present at the expected path — not
        merely the containing directory.

        The `project_root` argument is unused by this plugin-native host
        (kept for ABC compatibility with the render-only Copilot host).
        """
        del project_root  # plugin-native host: project root not consulted
        marketplace_cache, local_path = self.install_paths()

        marketplace_present = False
        marketplace_versions: list[Path] = []
        if marketplace_cache.is_dir():
            for marketplace_dir in marketplace_cache.iterdir():
                if not marketplace_dir.is_dir():
                    continue
                plugin_dir = marketplace_dir / "dotnet-ai-kit"
                if not plugin_dir.is_dir():
                    continue
                for version_dir in plugin_dir.iterdir():
                    if not version_dir.is_dir():
                        continue
                    # B-CX-1: require the Codex plugin manifest, not just
                    # the directory (FR-017 + clarify Q3).
                    if (version_dir / ".codex-plugin" / "plugin.json").is_file():
                        marketplace_present = True
                        marketplace_versions.append(version_dir)

        # Developer-local install requires the manifest, not just the dir.
        local_present = (local_path / ".codex-plugin" / "plugin.json").is_file()
        installed = marketplace_present or local_present

        notes_parts = []
        if marketplace_present:
            notes_parts.append(
                f"Codex marketplace cache: {len(marketplace_versions)} version(s) with manifest"
            )
        if local_present:
            notes_parts.append(f"Codex local dev install (with manifest) at {local_path}")
        if not installed:
            notes_parts.append(
                "no Codex install found — run `codex plugin install` or symlink under "
                f"{local_path.parent}"
            )

        return InstallStatus(
            host_name=self.name,
            installed=installed,
            expected_paths=[marketplace_cache, local_path],
            missing_paths=[p for p in (marketplace_cache, local_path) if not p.exists()]
            if not installed
            else [],
            notes="; ".join(notes_parts),
        )

    def write_per_solution_files(
        self,
        project_root: Path,
        *,
        permission_profile: Optional[str] = None,
        plugin_root: Optional[Path] = None,
    ) -> list[Path]:
        """Render `.codex/agents/<name>.toml` subagent files for each
        `agents-source/<name>.md` in the plugin.

        Per `https://developers.openai.com/codex/subagents` (retrieved
        2026-05-19), Codex loads subagents from `~/.codex/agents/` (user)
        or `.codex/agents/` (project). We write to the project scope so
        subagents ride with the solution.

        **Conflict policy (v1.0)**: if a target file already exists, the
        existing content is PRESERVED (user customizations win) and the
        skip is logged. To regenerate, delete the file and re-run init.
        Manifest-SHA-based conflict detection (like Copilot's render
        orchestrator) is a follow-up; the v1.0 contract is render-once.

        Args:
            project_root: Project root receiving `.codex/agents/*.toml`.
            permission_profile: Unused — accepted for ABC compatibility
                with other hosts.
            plugin_root: Optional override for the plugin source root
                (containing `agents-source/`). Defaults to auto-detection.

        Returns:
            List of paths the adapter actually wrote (excludes skipped
            pre-existing files).
        """
        del permission_profile  # unused for Codex subagent render

        if plugin_root is None:
            from dotnet_ai_kit.cli import _get_package_dir  # noqa: PLC0415

            plugin_root = _get_package_dir()

        agents_source = plugin_root / "agents-source"
        if not agents_source.is_dir():
            logger.debug(
                "CodexHost: no agents-source/ dir at %s — nothing to render",
                agents_source,
            )
            return []

        from dotnet_ai_kit.agent_generators import generate_codex_agent  # noqa: PLC0415

        agents_dir = project_root / ".codex" / "agents"
        written: list[Path] = []

        for source_path in sorted(agents_source.glob("*.md")):
            target = agents_dir / f"{source_path.stem}.toml"
            if target.is_file():
                logger.debug(
                    "CodexHost: %s already exists — preserving user content "
                    "(delete file and re-run to regenerate)",
                    target,
                )
                continue
            try:
                content = generate_codex_agent(source_path)
            except (ValueError, AssertionError) as exc:
                logger.warning(
                    "CodexHost: skipping %s — generator rejected source: %s",
                    source_path.name,
                    exc,
                )
                continue
            agents_dir.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written.append(target)

        return written
