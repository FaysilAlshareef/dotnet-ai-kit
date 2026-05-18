"""`dotnet-ai render` implementation (feature 019 / commit 14b / T117).

Per contracts/render-cli.contract.md. v1 produces Claude-host-shaped output
only; other hosts rejected at exit code 20.

The render command is the inspectability mitigation for the plugin-native
architecture: pre-rendered files no longer live on disk; this command lets
users inspect what a skill or rule resolves to *right now* with current
project metadata.
"""

from __future__ import annotations

from pathlib import Path


class RenderError(Exception):
    """Base for render errors."""

    exit_code: int = 99


class SkillOrRuleNotFound(RenderError):
    """Skill or rule name not found under search paths (exit 21)."""

    exit_code = 21


class ProjectMetadataMissing(RenderError):
    """project.yml missing or corrupt (exit 22)."""

    exit_code = 22


class SubstitutionFailure(RenderError):
    """Substitution failed: metadata key referenced but absent (exit 23)."""

    exit_code = 23


class UnsupportedHost(RenderError):
    """--host value not supported in v1 (exit 20)."""

    exit_code = 20


# Allowed --host values for v1 per CHK045.
SUPPORTED_HOSTS_V1: frozenset[str] = frozenset({"claude"})

# Hosts that exist but are deferred to v1.1 — they MUST be rejected, not
# silently produce a different shape per CHK045.
DEFERRED_HOSTS_V1_1: frozenset[str] = frozenset({"codex", "cursor", "copilot"})


def validate_host(host: str) -> None:
    """Raise UnsupportedHost when --host is not 'claude' (v1 binding)."""
    if host == "claude":
        return
    if host in DEFERRED_HOSTS_V1_1:
        raise UnsupportedHost(
            f"--host {host} is not supported in v1 of dotnet-ai render.\n\n"
            f"The render command produces Claude Code-shaped output in v1.\n"
            f"Support for other hosts (Codex CLI, Cursor, GitHub Copilot) is\n"
            f"deferred to v1.1.\n\n"
            f"Run without --host to get Claude-shaped output:\n"
            f"  dotnet-ai render <kind> <name>"
        )
    raise UnsupportedHost(f"Unknown --host value: {host!r}")


def find_skill(plugin_root: Path, name: str) -> Path:
    """Locate `skills/**/<name>/SKILL.md` under the plugin root.

    Returns the resolved path or raises SkillOrRuleNotFound (exit 21).
    """
    skills_root = plugin_root / "skills"
    if not skills_root.is_dir():
        raise SkillOrRuleNotFound(
            f"Skill '{name}' not found.\n\nSkills directory missing: {skills_root}"
        )
    # Look for skills/<category>/<name>/SKILL.md
    for candidate in skills_root.rglob("SKILL.md"):
        if candidate.parent.name == name:
            return candidate
    available = sorted({p.parent.name for p in skills_root.rglob("SKILL.md")})
    sample = ", ".join(available[:5]) + (
        f", ... ({len(available)} total)" if len(available) > 5 else ""
    )
    raise SkillOrRuleNotFound(
        f"Skill '{name}' not found.\n\nSearched in: {skills_root}\nAvailable skills: {sample}"
    )


def find_rule(plugin_root: Path, name: str) -> Path:
    """Locate `rules/{conventions,domain}/<name>.md` under the plugin root.

    Returns the resolved path or raises SkillOrRuleNotFound (exit 21).
    """
    rules_root = plugin_root / "rules"
    for sub in ("conventions", "domain"):
        candidate = rules_root / sub / f"{name}.md"
        if candidate.is_file():
            return candidate
    # Legacy fallback (pre-feature-019 layout)
    legacy = rules_root / f"{name}.md"
    if legacy.is_file():
        return legacy

    available_paths = list((rules_root / "conventions").glob("*.md")) + list(
        (rules_root / "domain").glob("*.md")
    )
    available = sorted({p.stem for p in available_paths})
    sample = ", ".join(available[:8]) + (
        f", ... ({len(available)} total)" if len(available) > 8 else ""
    )
    raise SkillOrRuleNotFound(
        f"Rule '{name}' not found.\n\n"
        f"Searched in: {rules_root}/conventions/, {rules_root}/domain/\n"
        f"Available rules: {sample}"
    )


def load_project_metadata(project_root: Path) -> dict:
    """Load `.dotnet-ai-kit/project.yml` and return its detected metadata.

    Raises ProjectMetadataMissing (exit 22) on missing/corrupt file.
    """
    import yaml as _yaml

    pym = project_root / ".dotnet-ai-kit" / "project.yml"
    if not pym.is_file():
        raise ProjectMetadataMissing(
            f"Project metadata not found at {pym}.\nRun `dotnet-ai init {project_root}` first."
        )
    try:
        data = _yaml.safe_load(pym.read_text(encoding="utf-8")) or {}
    except _yaml.YAMLError as exc:
        raise ProjectMetadataMissing(
            f"project.yml is corrupt: {exc}\nRun `dotnet-ai check` for details."
        ) from exc
    if isinstance(data, dict) and "detected" in data:
        data = data["detected"]
    if not isinstance(data, dict):
        raise ProjectMetadataMissing(f"project.yml expected a mapping, got {type(data).__name__}")
    return data


def substitute_metadata(body: str, metadata: dict) -> str:
    """Resolve ${Var} / ${detected_paths.key} tokens against metadata.

    Per FR-019: runtime substitution at render time. Raises
    SubstitutionFailure (exit 23) when a referenced key is absent.

    Supported tokens:
      - ${Company} → metadata['company']
      - ${Domain}  → metadata['domain']
      - ${Side}    → metadata['side']
      - ${detected_paths.<key>} → metadata['detected_paths'][<key>]
      - ${project_type} → metadata['project_type']
      - ${dotnet_version} → metadata['dotnet_version']
    """
    import re as _re

    detected_paths = metadata.get("detected_paths") or {}
    if not isinstance(detected_paths, dict):
        detected_paths = {}

    # First: ${detected_paths.<key>}
    def _resolve_detected_path(match: _re.Match) -> str:
        key = match.group(1)
        if key not in detected_paths:
            raise SubstitutionFailure(
                f"Token ${{detected_paths.{key}}} references key '{key}' which "
                f"is absent in project.yml.detected_paths. Run "
                f"`dotnet-ai detect` to regenerate detected_paths."
            )
        return str(detected_paths[key])

    body = _re.sub(r"\$\{detected_paths\.([A-Za-z_][A-Za-z0-9_]*)\}", _resolve_detected_path, body)

    # Then: simple ${Var} substitutions
    _simple_vars = {
        "Company": metadata.get("company", ""),
        "Domain": metadata.get("domain", ""),
        "Side": metadata.get("side", ""),
        "project_type": metadata.get("project_type", ""),
        "dotnet_version": metadata.get("dotnet_version", ""),
        "architecture_branch": metadata.get("architecture_branch", ""),
    }
    for key, value in _simple_vars.items():
        body = body.replace(f"${{{key}}}", str(value))

    return body


def render_skill(name: str, plugin_root: Path, project_root: Path, host: str = "claude") -> str:
    """Render a skill body with current project metadata substituted.

    Per FR-019 / SC-012 / contracts/render-cli.contract.md.
    """
    validate_host(host)
    skill_path = find_skill(plugin_root, name)
    metadata = load_project_metadata(project_root)
    body = skill_path.read_text(encoding="utf-8")
    return substitute_metadata(body, metadata)


def render_rule(name: str, plugin_root: Path, project_root: Path, host: str = "claude") -> str:
    """Render a rule body with current project metadata substituted.

    Per FR-019 / contracts/render-cli.contract.md. The rule body lives under
    `rules/conventions/<name>.md` or `rules/domain/<name>.md` per feature 019
    commit 14 reclassification.
    """
    validate_host(host)
    rule_path = find_rule(plugin_root, name)
    metadata = load_project_metadata(project_root)
    body = rule_path.read_text(encoding="utf-8")
    return substitute_metadata(body, metadata)
