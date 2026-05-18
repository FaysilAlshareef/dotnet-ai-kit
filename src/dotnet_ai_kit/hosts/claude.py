"""Claude Code host adapter (feature 019 / T040).

Implements the `Host` interface for Claude Code's plugin model:
- Plugin cache path: `~/.claude/plugins/cache/<marketplace>/dotnet-ai-kit/<version>/`
  (per research R7 / Claude Code docs)
- Developer-local install: `~/.claude/plugins/local/dotnet-ai-kit/`
- Per-solution writes: `.claude/settings.json` (permissions merge ONLY — no
  bulk-copy of commands/skills/agents per FR-005).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from dotnet_ai_kit.hosts.base import Host, InstallStatus

logger = logging.getLogger(__name__)


class ClaudeHost(Host):
    """Adapter for Claude Code (the primary plugin host in v1)."""

    name = "claude"

    def install_paths(self) -> list[Path]:
        """Plugin cache paths under ~/.claude/ per research R7.

        Returns both candidate locations: the marketplace cache (populated by
        `claude /plugin install`) and the developer-local symlink directory
        (used by local-dev workflows).
        """
        home = Path.home() / ".claude"
        return [
            home / "plugins" / "cache",  # marketplace install root
            home / "plugins" / "local" / "dotnet-ai-kit",  # developer symlink
        ]

    def verify_install(self) -> InstallStatus:
        """Filesystem inspection only — clarify Q3.

        The plugin is considered installed if EITHER the marketplace cache
        contains a `dotnet-ai-kit/<version>/` directory OR the local symlink
        path exists.
        """
        marketplace_cache, local_path = self.install_paths()

        # Marketplace install: scan marketplace cache for any dotnet-ai-kit
        # version. Cache layout per Claude Code:
        # ~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/
        marketplace_present = False
        marketplace_versions: list[Path] = []
        if marketplace_cache.is_dir():
            for marketplace_dir in marketplace_cache.iterdir():
                if not marketplace_dir.is_dir():
                    continue
                plugin_dir = marketplace_dir / "dotnet-ai-kit"
                if plugin_dir.is_dir():
                    marketplace_present = True
                    marketplace_versions.extend(p for p in plugin_dir.iterdir() if p.is_dir())

        # Developer-local install: ~/.claude/plugins/local/dotnet-ai-kit/
        local_present = local_path.is_dir()

        installed = marketplace_present or local_present
        notes_parts = []
        if marketplace_present:
            notes_parts.append(f"marketplace cache: {len(marketplace_versions)} version(s) found")
        if local_present:
            notes_parts.append(f"local dev install at {local_path}")
        if not installed:
            notes_parts.append(
                "no install found — run `claude /plugin install` or symlink under "
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
    ) -> list[Path]:
        """Write only per-solution files per FR-005.

        - `.claude/settings.json` — permissions merge only (no bulk copies).
        - Does NOT write `.claude/commands/`, `.claude/skills/`, `.claude/agents/`
          (those live in the plugin install path per FR-004).

        Returns the list of paths written.
        """
        written: list[Path] = []

        if permission_profile:
            settings_path = self._write_settings_json(project_root, permission_profile)
            written.append(settings_path)

        return written

    @staticmethod
    def _write_settings_json(project_root: Path, permission_profile: str) -> Path:
        """Write/merge `.claude/settings.json` with the chosen permission profile.

        Per data-model.md § 12, settings.json carries permissions only — not
        the bulk content from feature 018's pre-019 layout.
        """
        # Late import to avoid circular imports (cli.py imports hosts/).
        from dotnet_ai_kit.cli import _get_package_dir  # noqa: PLC0415

        # Resolve the permission preset JSON under bundled `config/`.
        # Filename convention: `permissions-<level>.json` (matches existing
        # feature-018 layout). Fall back to bare `<level>.json` for tests.
        pkg_root = _get_package_dir()
        candidates = (
            pkg_root / "config" / f"permissions-{permission_profile}.json",
            pkg_root / "config" / f"{permission_profile}.json",
        )
        preset_path: Path | None = None
        for c in candidates:
            if c.is_file():
                preset_path = c
                break
        if preset_path is None:
            raise FileNotFoundError(
                f"Permission preset '{permission_profile}' not found "
                f"(tried: {', '.join(str(c) for c in candidates)})"
            )

        preset = json.loads(preset_path.read_text(encoding="utf-8"))

        target_dir = project_root / ".claude"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / "settings.json"

        # Merge: existing user keys preserved; missing keys filled from preset.
        # This matches the pre-019 permission-merge semantics so user changes
        # to settings.json are not blown away on re-init.
        if target_path.is_file():
            try:
                existing = json.loads(target_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                logger.warning(
                    "Existing %s is not valid JSON — overwriting with preset",
                    target_path,
                )
                existing = {}
            merged = {**preset, **existing}
        else:
            merged = preset

        target_path.write_text(
            json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return target_path
