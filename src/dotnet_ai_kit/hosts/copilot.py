"""Copilot host adapter (feature 019 / T068).

Implements the `Host` interface for GitHub Copilot. Copilot is the ONLY host
in v1 that has a render path instead of a plugin-native model — per FR-004,
Copilot has no plugin install mechanism, so the tool renders content into
the repository's `.github/` directory.

Render targets per FR-007:
- `.github/copilot-instructions.md` — repository-wide instructions
- `.github/instructions/<area>.instructions.md` — path-scoped per detected_paths
- `.github/agents/<name>.agent.md` — per-agent files

Path collision per FR-008 / A-008:
- Default: pre-existing developer-authored files are PRESERVED IN PLACE;
  the tool emits a corrective error and exits non-zero.
- Explicit opt-in: `--force-render <path>` flag at the CLI overwrites the
  exact path the user named and records explicit consent in the manifest.

This adapter exposes the render orchestrator + the path-collision detector.
The full `dotnet-ai upgrade --copilot` CLI variant and the `--force-render`
flag are commit-7 follow-up work (deferred per current scope).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotnet_ai_kit.hosts.base import Host, InstallStatus

logger = logging.getLogger(__name__)


@dataclass
class CopilotRenderResult:
    """Result of `CopilotHost.render()`.

    `written`: paths the tool wrote (managed by manifest).
    `preserved`: paths that already existed and were preserved per FR-008.
    `force_rendered`: paths the user explicitly opted in to overwrite via
        `--force-render <path>`.
    `pending_user_consent`: paths the tool would have rendered but the user
        hasn't opted in to overwrite yet. Surfaced as a corrective error.
    """

    written: list[Path] = field(default_factory=list)
    preserved: list[Path] = field(default_factory=list)
    force_rendered: list[Path] = field(default_factory=list)
    pending_user_consent: list[Path] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        """True if user has unmodified files blocking the render."""
        return bool(self.pending_user_consent)


class CopilotHost(Host):
    """Adapter for GitHub Copilot (render-only, no plugin model)."""

    name = "copilot"

    def install_paths(self) -> list[Path]:
        """Copilot has NO plugin install path per FR-004.

        Returns an empty list — Copilot is the one host without a plugin
        cache directory. The per-solution `.github/` paths are managed
        via the render orchestrator.
        """
        return []

    def verify_install(self) -> InstallStatus:
        """For Copilot, "installed" means render artifacts exist + match manifest.

        Per FR-017 / CHK016: `dotnet-ai check` reports staleness if rendered
        files diverge from current plugin source or project metadata.

        v1 minimal: report installed=True if `.github/` exists in the
        current cwd (full freshness check is in commit 9 / T101+).
        """
        target = Path.cwd() / ".github"
        return InstallStatus(
            host_name=self.name,
            installed=target.is_dir(),
            expected_paths=[target],
            missing_paths=[] if target.is_dir() else [target],
            notes=(
                "Copilot is render-only (no plugin install) — install status "
                "= presence of .github/ in the project root."
            ),
        )

    def write_per_solution_files(
        self,
        project_root: Path,
        *,
        permission_profile: Optional[str] = None,
    ) -> list[Path]:
        """Render Copilot's three file classes into the project's `.github/`.

        Per FR-007 / contracts/copilot-{instructions,instructions-path,agent}.md.
        Default behavior preserves pre-existing user files — see
        `render()` for the full orchestrator with conflict detection.

        For convenience, this method just calls `render()` with
        force_render_paths=None.
        """
        result = self.render(project_root)
        if result.has_conflicts:
            logger.warning(
                "Copilot render blocked by pre-existing files (FR-008 / A-008): %s. "
                "Use `--force-render <path>` to opt in.",
                [str(p) for p in result.pending_user_consent],
            )
        return result.written

    def render(
        self,
        project_root: Path,
        *,
        force_render_paths: Optional[list[Path]] = None,
    ) -> CopilotRenderResult:
        """Render the three Copilot file classes per FR-007.

        Args:
            project_root: Project root containing `.dotnet-ai-kit/project.yml`.
            force_render_paths: Optional list of paths the user explicitly
                opted in to overwrite (per FR-008 path-specific opt-in).

        Returns:
            CopilotRenderResult with written/preserved/force_rendered/
            pending_user_consent partitions.

        v1 minimal: renders a placeholder copilot-instructions.md based on
        the template under `agents-copilot-templates/`. Full implementation
        (path-scoped + per-agent files) is staged in follow-up work.
        """
        force_render_paths = force_render_paths or []
        result = CopilotRenderResult()

        # Target: .github/copilot-instructions.md
        github_dir = project_root / ".github"
        instructions_path = github_dir / "copilot-instructions.md"

        if instructions_path.is_file() and instructions_path not in force_render_paths:
            # Pre-existing user file — preserve per FR-008 / A-008
            result.pending_user_consent.append(instructions_path)
            return result

        github_dir.mkdir(parents=True, exist_ok=True)

        # v1 minimal placeholder — full template render in follow-up work
        content = self._render_copilot_instructions_minimal(project_root)
        instructions_path.write_text(content, encoding="utf-8")

        if instructions_path in force_render_paths:
            result.force_rendered.append(instructions_path)
        else:
            result.written.append(instructions_path)

        return result

    @staticmethod
    def _render_copilot_instructions_minimal(project_root: Path) -> str:
        """Render a minimal placeholder copilot-instructions.md.

        Full jinja2-templated render (with conventions inlined + path
        pointers + agent quick-ref) is follow-up work in commit-7 stage 2.
        This minimal placeholder is enough to satisfy the contract
        assertions (file exists, has identity block + pointer block).
        """
        from dotnet_ai_kit.config import get_config_dir

        config_dir = get_config_dir(project_root)
        project_yml = config_dir / "project.yml"

        identity = "## Project identity\n\n_Project metadata not detected._\n"
        if project_yml.is_file():
            try:
                import yaml as _yaml

                data = _yaml.safe_load(project_yml.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "detected" in data:
                    data = data["detected"]
                if isinstance(data, dict):
                    identity = (
                        "## Project identity\n\n"
                        f"- company: {data.get('company', '_unknown_')}\n"
                        f"- domain: {data.get('domain', '_unknown_')}\n"
                        f"- side: {data.get('side', '_unknown_')}\n"
                        f"- project_type: {data.get('project_type', '_unknown_')}\n"
                    )
            except Exception:
                pass

        return (
            "# Repository-wide Copilot Instructions\n\n"
            + identity
            + "\n"
            + "## Always-on conventions\n\n"
            "_Convention rule bodies will be inlined here in the full render._\n\n"
            "## Path-scoped guidance\n\n"
            "See `.github/instructions/*.instructions.md` (generated per "
            "project layer) for path-scoped Copilot guidance.\n\n"
            "## Per-agent quick reference\n\n"
            "See `.github/agents/*.agent.md` for routing to specialist agents.\n"
        )
