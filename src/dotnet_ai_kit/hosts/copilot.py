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

        Per Codex implement-phase round-1 blocker 4: distinguish between
        MANAGED files (sha matches manifest — safe to re-render) and
        USER-MODIFIED files (sha differs — needs --force-render). Only the
        user-modified files get the pending_user_consent treatment.

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
        force_set = {p.resolve() for p in force_render_paths}
        result = CopilotRenderResult()

        # Resolve plugin_root for template discovery
        if plugin_root is None:
            from dotnet_ai_kit.cli import _get_package_dir  # noqa: PLC0415

            plugin_root = _get_package_dir()

        # Load manifest entries (host_owner='copilot') so we can distinguish
        # MANAGED files (hash matches → safe to re-render),
        # USER-MODIFIED managed files (hash drifted → preserve, needs --force),
        # and USER-AUTHORED files (not in manifest → preserve, needs --force).
        managed_hashes = self._load_managed_copilot_hashes(project_root)

        github_dir = project_root / ".github"

        def _should_skip(target: Path) -> bool:
            """Return True if existing file is user-modified/authored and not opted in."""
            if not target.is_file():
                return False
            tr = target.resolve()
            if tr in force_set:
                return False  # explicit opt-in always wins
            try:
                rel = target.relative_to(project_root).as_posix()
            except ValueError:
                return True
            recorded_hash = managed_hashes.get(rel)
            if recorded_hash is None:
                # Not in manifest — user-authored, preserve per FR-008 / A-008
                return True
            # In manifest — check if user has modified
            try:
                from dotnet_ai_kit.manifest import sha256_file  # noqa: PLC0415

                actual = sha256_file(target)
            except Exception:  # noqa: BLE001
                return True  # safer to preserve on read failure
            if actual != recorded_hash:
                # User-modified managed file: preserve per FR-022, needs --force
                return True
            return False  # tool-managed, hash matches — safe to re-render

        # ---- 1. Repository-wide instructions ----
        instructions_path = github_dir / "copilot-instructions.md"
        if _should_skip(instructions_path):
            result.pending_user_consent.append(instructions_path)
        else:
            github_dir.mkdir(parents=True, exist_ok=True)
            content = self._render_copilot_instructions_minimal(project_root, plugin_root)
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
            if _should_skip(inst_file):
                result.pending_user_consent.append(inst_file)
                continue
            instructions_dir.mkdir(parents=True, exist_ok=True)
            body = self._render_path_instructions(plugin_root, area_key, glob_pattern, project_root)
            if body is None:
                continue
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
                if _should_skip(agent_file):
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

    @classmethod
    def re_render_for_freshness(
        cls,
        project_root: Path,
        rel_path: str,
        plugin_root: Optional[Path] = None,
    ) -> Optional[str]:
        """Re-render the expected content for a managed Copilot file.

        Feature 019 / commit 21 / B-5 (T156): the `check copilot_freshness`
        gate compares this re-rendered content's hash to the on-disk hash so
        config/template drift (e.g., `config.yml::company.name` rename) is
        caught even when the on-disk hash still matches the manifest entry.

        Args:
            project_root: solution root containing `.dotnet-ai-kit/`.
            rel_path: posix path relative to project_root, e.g.
              `.github/copilot-instructions.md` or
              `.github/instructions/<area>.instructions.md` or
              `.github/agents/<name>.agent.md`.
            plugin_root: optional plugin-source root override (mostly for tests).

        Returns:
            Re-rendered content, or `None` if the template / source isn't
            available (caller treats as 'unable to verify — skip').
        """
        if plugin_root is None:
            from dotnet_ai_kit.cli import _get_package_dir  # noqa: PLC0415

            plugin_root = _get_package_dir()

        rel = rel_path.replace("\\", "/")

        # (1) Repo-wide instructions
        if rel == ".github/copilot-instructions.md":
            try:
                return cls._render_copilot_instructions_minimal(project_root, plugin_root)
            except Exception:  # noqa: BLE001
                return None

        # (2) Path-scoped instructions: .github/instructions/<area>.instructions.md
        if rel.startswith(".github/instructions/") and rel.endswith(".instructions.md"):
            area_key = rel[len(".github/instructions/") : -len(".instructions.md")]
            detected_paths = cls._load_detected_paths(project_root)
            glob_pattern = detected_paths.get(area_key)
            if not glob_pattern:
                return None
            return cls._render_path_instructions(plugin_root, area_key, glob_pattern, project_root)

        # (3) Per-agent files: .github/agents/<name>.agent.md
        if rel.startswith(".github/agents/") and rel.endswith(".agent.md"):
            agent_name = rel[len(".github/agents/") : -len(".agent.md")]
            agent_src = plugin_root / "agents-source" / f"{agent_name}.md"
            if not agent_src.is_file():
                return None
            return cls._render_agent_file(plugin_root, agent_src)

        return None

    @staticmethod
    def _load_managed_copilot_hashes(project_root: Path) -> dict[str, str]:
        """Return {posix_relpath: sha256} for manifest entries with
        host_owner='copilot'. Empty dict if no manifest."""
        try:
            from dotnet_ai_kit.manifest import read_manifest  # noqa: PLC0415

            manifest = read_manifest(project_root)
            if manifest is None:
                return {}
            return {
                f.path.replace("\\", "/"): f.sha256
                for f in manifest.files
                if (f.host_owner or "").lower() == "copilot"
            }
        except Exception:  # noqa: BLE001
            return {}

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
            domain_rule_body = rule_path.read_text(encoding="utf-8") if rule_path.is_file() else ""
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
                disable_model_invocation=frontmatter.get("disable_model_invocation", None),
                user_invocable=frontmatter.get("user_invocable", None),
                mcp_servers=frontmatter.get("mcp_servers", []),
                body=body.strip(),
            )
        except Exception:  # noqa: BLE001
            return None

    @staticmethod
    def _render_copilot_instructions_minimal(
        project_root: Path, plugin_root: Optional[Path] = None
    ) -> str:
        """Render the full repository-wide copilot-instructions.md per the
        contract at copilot-instructions.contract.md:13-17.

        Sections:
        - Project identity (from project.yml)
        - Always-on conventions (5 universal rules inlined verbatim)
        - Architecture profile (rules/conventions/profile-<type>.md if present)
        - Path-scoped guidance (pointers to .github/instructions/*)
        - Per-agent quick reference (from agents-source/)

        Per Codex implement-phase round-1 blocker 3 (formerly placeholder).
        """
        from dotnet_ai_kit.config import get_config_dir  # noqa: PLC0415

        if plugin_root is None:
            from dotnet_ai_kit.cli import _get_package_dir  # noqa: PLC0415

            plugin_root = _get_package_dir()

        # --- Project identity ---
        meta = {
            "company": "_unknown_",
            "domain": "_unknown_",
            "side": "_unknown_",
            "project_type": "_unknown_",
            "architecture_branch": "_unknown_",
            "dotnet_version": "_unknown_",
        }
        config_dir = get_config_dir(project_root)
        project_yml = config_dir / "project.yml"
        if project_yml.is_file():
            try:
                import yaml as _yaml  # noqa: PLC0415

                data = _yaml.safe_load(project_yml.read_text(encoding="utf-8")) or {}
                if isinstance(data, dict) and "detected" in data:
                    data = data["detected"]
                if isinstance(data, dict):
                    for key in meta:
                        if data.get(key):
                            meta[key] = str(data[key])
                    detected_paths = data.get("detected_paths") or {}
            except Exception:  # noqa: BLE001
                detected_paths = {}
        else:
            detected_paths = {}

        # --- Convention rules (universal whitelist, inlined verbatim) ---
        convention_rules: dict[str, str] = {}
        conventions_dir = plugin_root / "rules" / "conventions"
        if conventions_dir.is_dir():
            for rule_file in sorted(conventions_dir.glob("*.md")):
                convention_rules[rule_file.stem] = rule_file.read_text(encoding="utf-8")

        # --- Architecture profile (optional) ---
        arch_branch = meta.get("architecture_branch", "")
        architecture_profile_body = ""
        profile_candidates = [
            plugin_root / "rules" / "domain" / f"architecture-{arch_branch}.md",
            plugin_root / "rules" / "domain" / "architecture.md",
        ]
        for cand in profile_candidates:
            if cand.is_file():
                architecture_profile_body = cand.read_text(encoding="utf-8")
                break

        # --- Path scopes from detected_paths ---
        path_scopes: dict[str, list[str]] = {}
        for area, glob in (detected_paths or {}).items():
            if isinstance(glob, str) and glob:
                path_scopes[str(area)] = [glob]

        # --- Per-agent quick reference ---
        agents: dict[str, str] = {}
        agents_source = plugin_root / "agents-source"
        if agents_source.is_dir():
            import re as _re  # noqa: PLC0415

            import yaml as _yaml  # noqa: PLC0415

            for agent_file in sorted(agents_source.glob("*.md")):
                text = agent_file.read_text(encoding="utf-8")
                m = _re.match(r"^---\n(.*?)\n---\n", text, _re.DOTALL)
                fm: dict = {}
                if m:
                    try:
                        fm = _yaml.safe_load(m.group(1)) or {}
                    except Exception:  # noqa: BLE001
                        fm = {}
                name = fm.get("name") or agent_file.stem
                description = fm.get("description") or "(no description)"
                agents[str(name)] = str(description)

        # --- Render via jinja2 template if present, else fall back to inline ---
        template_path = plugin_root / "agents-copilot-templates" / "copilot-instructions.md.j2"
        if template_path.is_file():
            try:
                from jinja2 import Template  # noqa: PLC0415

                tmpl = Template(template_path.read_text(encoding="utf-8"))
                return tmpl.render(
                    company=meta["company"],
                    domain=meta["domain"],
                    side=meta["side"],
                    project_type=meta["project_type"],
                    architecture_branch=meta["architecture_branch"],
                    dotnet_version=meta["dotnet_version"],
                    convention_rules=convention_rules,
                    architecture_profile_body=architecture_profile_body
                    or "_(no architecture profile present for this project type)_",
                    path_scopes=path_scopes,
                    agents=agents,
                )
            except Exception:  # noqa: BLE001
                pass  # fall through to inline render

        # Inline fallback (no jinja2 / no template) — same content shape
        parts: list[str] = ["# Repository-wide Copilot Instructions\n"]
        parts.append("## Project identity\n")
        for key, val in meta.items():
            parts.append(f"- **{key}**: {val}")
        parts.append("\n## Always-on conventions\n")
        for name, body in convention_rules.items():
            parts.append(f"### {name}\n\n{body}\n")
        parts.append("## Architecture profile\n")
        parts.append(
            architecture_profile_body or "_(no architecture profile present for this project type)_"
        )
        parts.append("\n## Path-scoped guidance\n")
        for area, globs in path_scopes.items():
            parts.append(
                f"- `.github/instructions/{area}.instructions.md` — applies to: {', '.join(globs)}"
            )
        parts.append("\n## Per-agent quick reference\n")
        for name, desc in agents.items():
            parts.append(f"- **{name}**: {desc}")
        return "\n".join(parts) + "\n"
