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


# ---------------------------------------------------------------------------
# T195b — Cursor `.mdc` rule renderer (PASS branch of OOS-005)
# ---------------------------------------------------------------------------
#
# Cursor's documented rule format (`https://cursor.com/docs/context/rules`,
# research R12) packages each rule as a `.mdc` file under the plugin's
# `rules/cursor/` directory. The frontmatter shape:
#
#   description: <string>
#   globs: <comma-separated list>     # absent when alwaysApply: true
#   alwaysApply: <true | false>
#
# Mapping for feature 019:
#   rules/conventions/*.md  →  alwaysApply: true   (universal, no globs)
#   rules/domain/*.md       →  alwaysApply: false  + globs: from `paths:`


import re as _re_for_mdc  # noqa: E402

import yaml as _yaml_for_mdc  # noqa: E402

_RULE_FRONTMATTER_RE = _re_for_mdc.compile(r"\A---\s*\n(.*?\n)---\s*\n?(.*)\Z", _re_for_mdc.DOTALL)


def _parse_rule_frontmatter(rule_path: Path) -> tuple[dict, str]:
    """Parse a `rules/conventions/*.md` or `rules/domain/*.md` source rule.

    Returns ``(frontmatter_dict, body_with_no_leading_separator)``. Raises
    ValueError if the file lacks the `---`-delimited YAML frontmatter.
    """
    text = rule_path.read_text(encoding="utf-8")
    match = _RULE_FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(
            f"Rule file {rule_path} has no YAML frontmatter "
            f"(expected '---' delimiters at file start)."
        )
    fm = _yaml_for_mdc.safe_load(match.group(1)) or {}
    if not isinstance(fm, dict):
        raise ValueError(f"Rule file {rule_path} frontmatter must be a YAML mapping")
    body = match.group(2)
    return fm, body


def render_cursor_rule_mdc(rule_path: Path) -> str:
    """Render a Cursor `.mdc` file from a `rules/{conventions,domain}/*.md` source.

    Feature 019 / commit 29 / T195b — OOS-005 PASS branch. The source rule
    file lives under `rules/conventions/` (universal) or `rules/domain/`
    (path-scoped) and uses Claude-shaped frontmatter (`description:` and
    optional `paths:` list). This renderer converts it to Cursor's `.mdc`
    frontmatter (`description:`, `globs:`, `alwaysApply:`) per research
    R12 (`https://cursor.com/docs/context/rules`).

    Mapping:
      * ``rules/conventions/<name>.md``  → ``alwaysApply: true``  (no globs)
      * ``rules/domain/<name>.md``       → ``alwaysApply: false`` + ``globs``
        (comma-separated, from the source's ``paths:`` list)

    The body is copied verbatim — no project-metadata substitution at render
    time (these .mdc files ship in the plugin package and are loaded by
    Cursor's runtime; substitution is the consumer's responsibility).

    Args:
        rule_path: ``Path`` to the source rule file under ``rules/conventions/``
            or ``rules/domain/``.

    Returns:
        The full ``.mdc`` file content (frontmatter + body) ready to be
        written to ``rules/cursor/<rule_stem>.mdc``.

    Raises:
        ValueError: if the source has no YAML frontmatter, or if a
            ``rules/domain/*.md`` source has no ``paths:`` list.
    """
    fm, body = _parse_rule_frontmatter(rule_path)

    # Classification: conventions ⇒ alwaysApply; domain ⇒ globs.
    parts = rule_path.parts
    is_convention = "conventions" in parts
    is_domain = "domain" in parts

    cursor_fm: dict = {}
    description = fm.get("description")
    if description:
        cursor_fm["description"] = description

    if is_convention:
        # Universal rule: no globs, always-on.
        cursor_fm["alwaysApply"] = True
    elif is_domain:
        # Path-scoped: glob patterns drive activation.
        paths = fm.get("paths") or []
        if not paths:
            raise ValueError(
                f"Domain rule {rule_path} has no `paths:` list — "
                f"required for Cursor `globs:` activation. Add `paths:` "
                f"under the source frontmatter or move the rule to "
                f"rules/conventions/."
            )
        if not isinstance(paths, list):
            raise ValueError(
                f"Domain rule {rule_path}: `paths:` must be a list of glob "
                f"strings, got {type(paths).__name__}."
            )
        # Cursor's `globs` frontmatter is a comma-separated string per
        # cursor.com/docs/context/rules.
        cursor_fm["globs"] = ",".join(str(p) for p in paths)
        cursor_fm["alwaysApply"] = False
    else:
        # Defensive: source not under conventions/ or domain/ — treat as
        # always-apply universal to preserve coverage.
        cursor_fm["alwaysApply"] = True

    # Render with stable key order: description, globs, alwaysApply.
    ordered: dict = {}
    if "description" in cursor_fm:
        ordered["description"] = cursor_fm["description"]
    if "globs" in cursor_fm:
        ordered["globs"] = cursor_fm["globs"]
    ordered["alwaysApply"] = cursor_fm["alwaysApply"]

    fm_yaml = _yaml_for_mdc.dump(
        ordered, default_flow_style=False, sort_keys=False, allow_unicode=True
    )
    return f"---\n{fm_yaml}---\n\n{body.lstrip(chr(10))}"


def write_cursor_rules_for_plugin(plugin_root: Path) -> list[Path]:
    """Regenerate `rules/cursor/*.mdc` from `rules/conventions/` + `rules/domain/`.

    Feature 019 / commit 29 / T195b. Used at plugin-build time to populate
    the directory referenced by `.cursor-plugin/plugin.json::rules`.

    Returns the list of `.mdc` file paths written. Sorted for determinism.
    """
    rules_root = plugin_root / "rules"
    out_dir = rules_root / "cursor"
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for sub in ("conventions", "domain"):
        sub_dir = rules_root / sub
        if not sub_dir.is_dir():
            continue
        for src in sorted(sub_dir.glob("*.md")):
            mdc_content = render_cursor_rule_mdc(src)
            out_path = out_dir / f"{src.stem}.mdc"
            out_path.write_text(mdc_content, encoding="utf-8")
            written.append(out_path)
    return sorted(written)
