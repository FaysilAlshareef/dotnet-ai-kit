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
        plugin_root: Optional[Path] = None,
    ) -> CopilotRenderResult:
        """Render the three Copilot file classes per FR-007.

        Args:
            project_root: Project root containing `.dotnet-ai-kit/project.yml`.
            force_render_paths: Optional list of paths the user explicitly
                opted in to overwrite (per FR-008 path-specific opt-in).
            plugin_root: Plugin source root (containing
                `agents-copilot-templates/`, `rules/`, `agents-source/`).
                Defaults to the auto-detected package dir.

        Returns:
            CopilotRenderResult with written/preserved/force_rendered/
            pending_user_consent partitions.
        """
        force_render_paths = force_render_paths or []
        # Normalize paths for comparison
        force_set = {p.resolve() for p in force_render_paths}
        result = CopilotRenderResult()

        # Resolve plugin_root for template discovery
        if plugin_root is None:
            # Late import to avoid circular dependency
            from dotnet_ai_kit.cli import _get_package_dir  # noqa: PLC0415

            plugin_root = _get_package_dir()

        github_dir = project_root / ".github"

        # ---- 1. Repository-wide instructions ----
        instructions_path = github_dir / "copilot-instructions.md"
        if instructions_path.is_file() and instructions_path.resolve() not in force_set:
            result.pending_user_consent.append(instructions_path)
        else:
            github_dir.mkdir(parents=True, exist_ok=True)
            content = self._render_copilot_instructions_minimal(project_root)
            instructions_path.write_text(content, encoding="utf-8")
            if instructions_path.resolve() in force_set:
                result.force_rendered.append(instructions_path)
            else:
                result.written.append(instructions_path)

        # ---- 2. Path-scoped instructions per detected_paths ----
        detected_paths = self._load_detected_paths(project_root)
        instructions_dir = github_dir / "instructions"
        for area_key, glob_pattern in detected_paths.items():
            inst_file = instructions_dir / f"{area_key}.instructions.md"
            if inst_file.is_file() and inst_file.resolve() not in force_set:
                result.pending_user_consent.append(inst_file)
                continue
            instructions_dir.mkdir(parents=True, exist_ok=True)
            body = self._render_path_instructions(
                plugin_root, area_key, glob_pattern, project_root
            )
            if body is None:
                continue  # template missing — skip silently
            inst_file.write_text(body, encoding="utf-8")
            if inst_file.resolve() in force_set:
                result.force_rendered.append(inst_file)
            else:
                result.written.append(inst_file)

        # ---- 3. Per-agent files from agents-source/ ----
        agents_source = plugin_root / "agents-source"
        agents_dir = github_dir / "agents"
        if agents_source.is_dir():
            for agent_src in sorted(agents_source.glob("*.md")):
                agent_name = agent_src.stem
                agent_file = agents_dir / f"{agent_name}.agent.md"
                if agent_file.is_file() and agent_file.resolve() not in force_set:
                    result.pending_user_consent.append(agent_file)
                    continue
                body = self._render_agent_file(plugin_root, agent_src)
                if body is None:
                    continue
                agents_dir.mkdir(parents=True, exist_ok=True)
                agent_file.write_text(body, encoding="utf-8")
                if agent_file.resolve() in force_set:
                    result.force_rendered.append(agent_file)
                else:
                    result.written.append(agent_file)

        return result

    @staticmethod
    def _load_detected_paths(project_root: Path) -> dict[str, str]:
        """Read project.yml.detected_paths."""
        try:
            import yaml as _yaml  # noqa: PLC0415

            pym = project_root / ".dotnet-ai-kit" / "project.yml"
            if not pym.is_file():
                return {}
            data = _yaml.safe_load(pym.read_text(encoding="utf-8")) or {}
            if isinstance(data, dict) and "detected" in data:
                data = data["detected"]
            paths = data.get("detected_paths") if isinstance(data, dict) else None
            if isinstance(paths, dict):
                return {str(k): str(v) for k, v in paths.items()}
        except Exception:  # noqa: BLE001
            pass
        return {}

    @staticmethod
    def _render_path_instructions(
        plugin_root: Path,
        area_key: str,
        glob_pattern: str,
        project_root: Path,
    ) -> Optional[str]:
        """Render `.github/instructions/<area>.instructions.md` per
        contracts/copilot-instructions-path.contract.md."""
        try:
            from jinja2 import Template  # noqa: PLC0415

            template_path = plugin_root / "agents-copilot-templates" / "instructions-path.md.j2"
            if not template_path.is_file():
                return None
            tmpl = Template(template_path.read_text(encoding="utf-8"))

            # Use the matching domain rule body when available
            rule_path = plugin_root / "rules" / "domain" / f"{area_key}.md"
            domain_rule_body = (
                rule_path.read_text(encoding="utf-8") if rule_path.is_file() else ""
            )
            return tmpl.render(
                apply_to_globs=[glob_pattern],
                area_title=area_key.replace("-", " ").title(),
                domain_rule_body=domain_rule_body,
                metadata_overrides={},
            )
        except Exception:  # noqa: BLE001
            return None

    @staticmethod
    def _render_agent_file(plugin_root: Path, agent_src: Path) -> Optional[str]:
        """Render `.github/agents/<name>.agent.md` per
        contracts/copilot-agent.contract.md."""
        try:
            from jinja2 import Template  # noqa: PLC0415

            template_path = plugin_root / "agents-copilot-templates" / "agent.md.j2"
            if not template_path.is_file():
                return None
            tmpl = Template(template_path.read_text(encoding="utf-8"))

            # Parse the agent source for frontmatter + body
            text = agent_src.read_text(encoding="utf-8")
            import re as _re  # noqa: PLC0415

            m = _re.match(r"^---\n(.*?)\n---\n?(.*)$", text, _re.DOTALL)
            frontmatter: dict = {}
            body = text
            if m:
                import yaml as _yaml  # noqa: PLC0415

                frontmatter = _yaml.safe_load(m.group(1)) or {}
                body = m.group(2)
            return tmpl.render(
                name=frontmatter.get("name", agent_src.stem),
                description=frontmatter.get("description", ""),
                target=frontmatter.get("target", None),
                tools=frontmatter.get("tools", []),
                model=frontmatter.get("model", None),
                disable_model_invocation=frontmatter.get(
                    "disable_model_invocation", None
                ),
                user_invocable=frontmatter.get("user_invocable", None),
                mcp_servers=frontmatter.get("mcp_servers", []),
                body=body.strip(),
            )
        except Exception:  # noqa: BLE001
            return None

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
