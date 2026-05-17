"""File copy and Jinja2 template rendering for dotnet-ai-kit.

Handles copying command/rule files to AI tool directories, rendering
Jinja2 templates with project-specific context, and scaffolding new
projects from templates.
"""

from __future__ import annotations

import json
import logging
import re
import shutil
from pathlib import Path
from typing import Any, Optional

import jinja2

from dotnet_ai_kit.models import DotnetAiConfig
from dotnet_ai_kit.utils import HOOK_MODEL, HOOK_TIMEOUT_MS, parse_version
from dotnet_ai_kit.version_check import check_claude_code_version

logger = logging.getLogger(__name__)

# Maps project_type → profile source path (relative to package root).
# Only ONE profile is deployed per project.
PROFILE_MAP: dict[str, str] = {
    # microservice mode
    "command": "profiles/microservice/command.md",
    "query-sql": "profiles/microservice/query-sql.md",
    "query-cosmos": "profiles/microservice/query-cosmos.md",
    "processor": "profiles/microservice/processor.md",
    "gateway": "profiles/microservice/gateway.md",
    "controlpanel": "profiles/microservice/controlpanel.md",
    "hybrid": "profiles/microservice/hybrid.md",
    # generic mode
    "vsa": "profiles/generic/vsa.md",
    "clean-arch": "profiles/generic/clean-arch.md",
    "ddd": "profiles/generic/ddd.md",
    "modular-monolith": "profiles/generic/modular-monolith.md",
    "generic": "profiles/generic/generic.md",
}
FALLBACK_PROFILE = "profiles/generic/generic.md"

COMMAND_SHORT_ALIASES: dict[str, str] = {
    "specify": "spec",
    "analyze": "check",
    "implement": "go",
    "add-aggregate": "agg",
    "add-entity": "entity",
    "add-event": "event",
    "add-endpoint": "ep",
    "add-crud": "crud",
    "add-page": "page",
    "add-tests": "tests",
    "configure": "config",
    "checkpoint": "save",
    "wrap-up": "done",
}


class CopyError(Exception):
    """Raised when a file copy operation fails."""


def render_template(template_path: Path, output_path: Path, context: dict[str, Any]) -> None:
    """Render a Jinja2 template file to an output path.

    Supports placeholders like {Company}, {Domain}, $ARGUMENTS, and
    standard Jinja2 {{ variable }} syntax.

    Args:
        template_path: Path to the template file.
        output_path: Path where the rendered file will be written.
        context: Template variable context dictionary.
    """
    text = template_path.read_text(encoding="utf-8")

    # Pre-process: convert {Company} style placeholders to Jinja2 {{ Company }}
    # Only convert single-brace placeholders that are not already Jinja2 syntax
    text = re.sub(
        r"(?<!\{)\{([A-Za-z_][A-Za-z0-9_]*)\}(?!\})",
        r"{{ \1 }}",
        text,
    )

    env = jinja2.Environment(
        undefined=jinja2.StrictUndefined,
        keep_trailing_newline=True,
    )
    template = env.from_string(text)
    rendered = template.render(**context)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")


def _clean_managed_commands(commands_dir: Path) -> int:
    """Delete all tool-managed command files from the commands directory.

    Removes files matching ``dotnet-ai.*.md`` and ``dai.*.md`` patterns.
    User-created files with other naming patterns are preserved.

    Args:
        commands_dir: Directory to clean.

    Returns:
        Number of files deleted.
    """
    if not commands_dir.is_dir():
        return 0

    deleted = 0
    for pattern in ("dotnet-ai.*.md", "dai.*.md"):
        for f in commands_dir.glob(pattern):
            f.unlink()
            deleted += 1
    return deleted


def copy_commands(
    source_dir: Path,
    target_dir: Path,
    agent_config: dict[str, Any],
    config: DotnetAiConfig,
    *,
    is_plugin: bool = False,
) -> int:
    """Copy command files from the source to the AI tool's commands directory.

    Cleans up previously managed files before writing to prevent stale
    duplicates when the command style changes.  In plugin mode, full-prefix
    files are skipped because the plugin system already serves them.

    Args:
        source_dir: Directory containing command template .md files.
        target_dir: Root of the user's project.
        agent_config: Configuration dict for the target AI tool.
        config: The dotnet-ai-kit configuration.
        is_plugin: If True, skip writing full-prefix (dotnet-ai.*) files.

    Returns:
        Number of command files copied.
    """
    commands_dir_rel = agent_config.get("commands_dir")
    if not commands_dir_rel:
        return 0

    commands_dir = target_dir / commands_dir_rel
    commands_dir.mkdir(parents=True, exist_ok=True)

    # Always clean managed files first to prevent stale duplicates
    _clean_managed_commands(commands_dir)

    # In plugin mode with full style, plugin serves everything — nothing to copy
    if is_plugin and config.command_style == "full":
        return 0

    prefix = agent_config.get("command_prefix", "dotnet-ai")
    ext = agent_config.get("command_ext", ".md")
    args_placeholder = agent_config.get("args_placeholder", "$ARGUMENTS")

    count = 0
    command_files = sorted(source_dir.glob("*.md"))

    for cmd_file in command_files:
        cmd_name = cmd_file.stem  # e.g., "specify", "plan"

        # Read template content
        content = cmd_file.read_text(encoding="utf-8")

        # Replace $ARGUMENTS with tool-specific placeholder if needed
        if args_placeholder and "$ARGUMENTS" in content:
            content = content.replace("$ARGUMENTS", args_placeholder)

        # Full command name: dotnet-ai.specify.md
        full_name = f"{prefix}.{cmd_name}{ext}"

        if not is_plugin and config.command_style in ("full", "both"):
            out_path = commands_dir / full_name
            out_path.write_text(content, encoding="utf-8")
            count += 1

        if config.command_style in ("short", "both"):
            short_prefix = "dai"
            short_alias = COMMAND_SHORT_ALIASES.get(cmd_name, cmd_name)
            short_name = f"{short_prefix}.{short_alias}{ext}"
            short_path = commands_dir / short_name
            short_path.write_text(content, encoding="utf-8")
            count += 1

    return count


def copy_rules(
    source_dir: Path,
    target_dir: Path,
    agent_config: dict[str, Any],
) -> int:
    """Copy rule files from the source to the AI tool's rules directory.

    Preserves YAML frontmatter in rule files.

    Args:
        source_dir: Directory containing rule .md files.
        target_dir: Root of the user's project.
        agent_config: Configuration dict for the target AI tool.

    Returns:
        Number of rule files copied.
    """
    rules_dir_rel = agent_config.get("rules_dir")
    if not rules_dir_rel:
        return 0

    rules_dir = target_dir / rules_dir_rel
    rules_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    rule_files = sorted(source_dir.glob("*.md"))

    for rule_file in rule_files:
        content = rule_file.read_text(encoding="utf-8")
        dest = rules_dir / rule_file.name
        dest.write_text(content, encoding="utf-8")
        count += 1

    return count


def copy_commands_cursor(
    source_dir: Path,
    target_dir: Path,
    agent_config: dict[str, Any],
    rules_dir: Optional[Path] = None,
) -> int:
    """Combine all commands and rules into a single .mdc file for Cursor.

    Cursor uses a single rules file rather than separate command files.

    Args:
        source_dir: Directory containing command template .md files.
        target_dir: Root of the user's project.
        agent_config: Configuration dict for Cursor.
        rules_dir: Optional directory containing rule files to include.

    Returns:
        1 if the combined file was created, 0 otherwise.
    """
    cursor_rules_rel = agent_config.get("rules_dir")
    if not cursor_rules_rel:
        return 0

    cursor_rules_dir = target_dir / cursor_rules_rel
    cursor_rules_dir.mkdir(parents=True, exist_ok=True)

    sections: list[str] = []

    # Include rules
    if rules_dir and rules_dir.is_dir():
        for rule_file in sorted(rules_dir.glob("*.md")):
            content = rule_file.read_text(encoding="utf-8")
            sections.append(f"## Rule: {rule_file.stem}\n\n{content}")

    # Include commands
    for cmd_file in sorted(source_dir.glob("*.md")):
        content = cmd_file.read_text(encoding="utf-8")
        sections.append(f"## Command: dotnet-ai.{cmd_file.stem}\n\n{content}")

    combined = "\n\n---\n\n".join(sections)
    out_path = cursor_rules_dir / "dotnet-ai-kit.mdc"
    out_path.write_text(combined, encoding="utf-8")
    return 1


def copy_commands_codex(
    source_dir: Path,
    target_dir: Path,
    agent_config: dict[str, Any],
) -> int:
    """Generate an AGENTS.md file for Codex CLI with all agent routing.

    Args:
        source_dir: Directory containing command template .md files.
        target_dir: Root of the user's project.
        agent_config: Configuration dict for Codex.

    Returns:
        1 if AGENTS.md was created, 0 otherwise.
    """
    agents_file = agent_config.get("agents_file")
    if not agents_file:
        return 0

    sections: list[str] = ["# dotnet-ai-kit Agent Routing\n"]

    for cmd_file in sorted(source_dir.glob("*.md")):
        cmd_name = cmd_file.stem
        content = cmd_file.read_text(encoding="utf-8")
        # Extract first non-frontmatter line as description
        lines = content.strip().splitlines()
        desc = ""
        in_frontmatter = False
        for line in lines:
            stripped = line.strip()
            if stripped == "---":
                in_frontmatter = not in_frontmatter
                continue
            if not in_frontmatter and stripped:
                desc = stripped
                break

        sections.append(f"## dotnet-ai.{cmd_name}\n\n{desc}\n")

    out_path = target_dir / agents_file
    out_path.write_text("\n".join(sections), encoding="utf-8")
    return 1


class DeploymentError(RuntimeError):
    """Raised when a skill / rule / profile cannot be deployed safely
    (FR-033 — path-token referencing a missing detected_paths key)."""


def merge_mcp_config(project_root: Path, source_mcp_json: Path) -> Path:
    """Merge the plugin's ``.mcp.json`` into the project's, preserving any
    third-party servers already registered (T066a / FR-018).

    Existing entries are NOT overwritten. New plugin entries are added.
    Returns the path of the merged file.
    """
    plugin_data = json.loads(source_mcp_json.read_text(encoding="utf-8"))
    target = project_root / ".mcp.json"

    if target.is_file():
        existing = json.loads(target.read_text(encoding="utf-8"))
    else:
        existing = {"mcpServers": {}}

    servers = existing.setdefault("mcpServers", {})
    for name, entry in plugin_data.get("mcpServers", {}).items():
        if name not in servers:
            servers[name] = entry

    target.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return target


def _resolve_detected_path_tokens(
    content: str,
    detected_paths: dict[str, str],
    *,
    source: str | None = None,
) -> str:
    """Resolve ``${detected_paths.X}`` tokens. FR-033: when ``X`` is missing
    from ``detected_paths`` (or maps to a falsy value), raise
    ``DeploymentError`` instead of silently substituting an empty string or
    a glob-only fragment like ``**/*.cs``.

    Args:
        content: File content to resolve.
        detected_paths: Mapping of key → concrete path.
        source: Optional source path for richer error messages.

    Returns:
        Content with all ``${detected_paths.X}`` tokens substituted.
    """

    missing: list[str] = []

    def _replace_token(match: re.Match) -> str:
        key = match.group(1)
        value = detected_paths.get(key)
        if not value:
            missing.append(key)
            return match.group(0)
        return value

    resolved = re.sub(r"\$\{detected_paths\.(\w+)\}", _replace_token, content)

    if missing:
        unique = sorted(set(missing))
        raise DeploymentError(
            f"missing detected_paths keys: {unique}"
            + (f" while resolving {source}" if source else "")
            + "; populate them in .dotnet-ai-kit/project.yml or re-run `/dai.detect`."
        )

    return resolved


def copy_skills(
    source_dir: Path,
    target_dir: Path,
    agent_config: dict[str, Any],
    detected_paths: Optional[dict[str, str]] = None,
) -> int:
    """Copy skill files, resolving ${detected_paths.*} tokens if provided.

    Recursively copies the skills directory structure preserving
    category/subcategory organization. When detected_paths is provided,
    resolves path tokens in SKILL.md frontmatter.

    Args:
        source_dir: Directory containing skill subdirectories.
        target_dir: Root of the user's project.
        agent_config: Configuration dict for the target AI tool.
        detected_paths: Optional mapping of path categories to filesystem paths.

    Returns:
        Number of skill files copied.
    """
    skills_dir_rel = agent_config.get("skills_dir")
    if not skills_dir_rel:
        return 0

    skills_dir = target_dir / skills_dir_rel
    # Remove existing skills directory to ensure clean overwrite
    if skills_dir.is_dir():
        shutil.rmtree(skills_dir)
    skills_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for skill_file in sorted(source_dir.rglob("*.md")):
        rel_path = skill_file.relative_to(source_dir)
        dest = skills_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        content = skill_file.read_text(encoding="utf-8")

        # FR-033 fail-closed at the SKILL level: we never deploy a SKILL.md
        # with a literal ``${detected_paths.`` substring — that would let the
        # rule router fall back to a project-root glob and load the skill on
        # every C# edit. Three branches:
        #   1. detected_paths is None / empty (legacy install, linked-repo
        #      fallback): skip every token-bearing skill.
        #   2. detected_paths is partial (e.g. command service missing
        #      ``cosmos_entities``): skip skills whose token can't resolve;
        #      deploy the rest with substituted paths.
        #   3. detected_paths is complete: resolve cleanly and deploy.
        if "${detected_paths." in content:
            if not detected_paths:
                logger.warning(
                    "skipping %s: ${detected_paths.*} tokens require "
                    "running /dai.detect (no detected_paths available)",
                    rel_path,
                )
                continue
            try:
                content = _resolve_detected_path_tokens(
                    content, detected_paths, source=str(rel_path)
                )
            except DeploymentError as exc:
                logger.warning("skipping %s: %s", rel_path, exc)
                continue

        dest.write_text(content, encoding="utf-8")
        count += 1

    return count


def _parse_yaml_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from a markdown file.

    Args:
        content: Full file content.

    Returns:
        Tuple of (frontmatter dict, markdown body after frontmatter).
    """
    import yaml

    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, content

    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        return {}, content

    fm_text = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1 :])
    fm = yaml.safe_load(fm_text) or {}
    return fm, body


def copy_agents(
    source_dir: Path,
    target_dir: Path,
    agent_config: dict[str, Any],
    tool_name: str = "claude",
) -> int:
    """Copy agent files via the feature-019 per-host generator pipeline.

    Per feature 019 / T041a / T043, this function NO LONGER does bulk-copy
    of generated agents into `.claude/agents/`. The agents are now served
    from the plugin install path; per-solution `.claude/agents/` is empty.

    The function is kept for two legacy code paths:
    1. Tests that exercise the legacy API surface.
    2. The linked-secondary-repository writer at copier.py:882-1202 (commit 4
       T042 routes this through `hosts/` adapters; until that lands, the
       function is callable but emits an empty-result + warning for Claude).

    For Claude tool: returns 0 immediately and logs a warning explaining
    the new plugin-native architecture.
    For Codex tool: returns 0 (Codex has no native agents per OOS-004).
    For Cursor/Copilot: returns 0 (handled by their respective host
    adapters in commits 6 and 7).

    Args:
        source_dir: Directory containing agent .md files (unused under v019).
        target_dir: Root of the user's project (unused under v019).
        agent_config: Configuration dict for the target AI tool (unused).
        tool_name: AI tool name. Determines the log message only.

    Returns:
        Always 0 (no files copied under plugin-native architecture).
    """
    import logging

    logger = logging.getLogger(__name__)

    # Plugin-native hosts (claude/codex/cursor): agents live in the plugin
    # install path. Per-solution .claude/agents/ MUST NOT receive copies
    # under feature 019.
    if tool_name in {"claude", "codex", "cursor"}:
        logger.debug(
            "copy_agents() is a no-op for plugin-native host '%s' under "
            "feature 019. Agents are served from the plugin install path. "
            "Per-solution path '%s' is left untouched.",
            tool_name,
            agent_config.get("agents_dir") or "(unset)",
        )
        return 0

    if tool_name == "copilot":
        # Copilot rendering is implemented in commit 7 (T070 / hosts/copilot.py)
        # via a different path. Here we just no-op.
        logger.debug(
            "copy_agents() no-op for Copilot — render path landed in commit 7."
        )
        return 0

    logger.warning(
        "Unknown tool_name '%s' in copy_agents — skipping (no host adapter known).",
        tool_name,
    )
    return 0


def copy_profile(
    target_root: Path,
    tool_name: str,
    project_type: str,
    package_dir: Path,
    confidence: str = "high",
) -> Optional[Path]:
    """Deploy the matching architecture profile to the AI tool's rules directory.

    Looks up the profile for the given project_type. Falls back to
    the generic profile when the type is unknown or confidence is low.

    Args:
        target_root: Root of the user's project.
        tool_name: AI tool name (claude, cursor, etc.).
        package_dir: The dotnet-ai-kit package installation directory.
        project_type: Detected project type from project.yml.
        confidence: Detection confidence (high, medium, low).

    Returns:
        Path to the deployed profile, or None if the tool has no rules_dir.

    Raises:
        FileNotFoundError: If the source profile file does not exist.
    """
    from dotnet_ai_kit.agents import get_agent_config

    agent_config = get_agent_config(tool_name)
    rules_dir_rel = agent_config.get("rules_dir")
    if not rules_dir_rel:
        return None

    # Select profile: fallback to generic on low confidence or unknown type
    if confidence == "low" or project_type not in PROFILE_MAP:
        profile_rel = FALLBACK_PROFILE
    else:
        profile_rel = PROFILE_MAP[project_type]

    source_path = package_dir / profile_rel
    if not source_path.is_file():
        raise FileNotFoundError(f"Architecture profile not found: {source_path}")

    rules_dir = target_root / rules_dir_rel
    rules_dir.mkdir(parents=True, exist_ok=True)

    dest = rules_dir / "architecture-profile.md"
    content = source_path.read_text(encoding="utf-8")
    dest.write_text(content, encoding="utf-8")

    return dest


def copy_hook(
    target_root: Path,
    profile_path: Path,
    package_dir: Path,
) -> bool:
    """Deploy a PreToolUse prompt hook that validates writes against profile constraints.

    Reads the profile, extracts constraints, renders the hook prompt template,
    and writes the hook configuration to .claude/settings.json.

    Args:
        target_root: Root of the user's project.
        profile_path: Path to the deployed architecture profile.
        package_dir: The dotnet-ai-kit package installation directory.

    Returns:
        True if the hook was written, False if skipped.
    """
    if not profile_path or not profile_path.is_file():
        return False

    # Extract constraints from profile (everything after frontmatter)
    content = profile_path.read_text(encoding="utf-8")
    _, body = _parse_yaml_frontmatter(content)
    constraints = body.strip()

    if not constraints:
        return False

    # Render hook prompt template
    template_path = package_dir / "templates" / "hook-prompt-template.md"
    if not template_path.is_file():
        return False

    template_text = template_path.read_text(encoding="utf-8")
    prompt = template_text.replace("{{ constraints }}", constraints)

    # Read or create settings.json
    settings_path = target_root / ".claude" / "settings.json"
    settings: dict[str, Any] = {}
    if settings_path.is_file():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    # Add/update the PreToolUse hook
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    # Remove existing architecture hook if present
    pre_tool_use = [h for h in pre_tool_use if h.get("_source") != "dotnet-ai-kit-arch"]

    # FR-005 (T018b): on Claude Code >= v2.1.85, emit the dynamic arch hook
    # with handler-level `if:` filters so the prompt only fires on .cs edits.
    # On older Claude Code, fall back to the command-pattern matcher.
    meets_minimum, _ = check_claude_code_version()
    if meets_minimum:
        pre_tool_use.append(
            {
                "_source": "dotnet-ai-kit-arch",
                "matcher": "Edit|Write",
                "hooks": [
                    {
                        "type": "prompt",
                        "prompt": prompt,
                        "model": HOOK_MODEL,
                        "timeout": HOOK_TIMEOUT_MS,
                        "if": "Edit(*.cs)",
                    },
                    {
                        "type": "prompt",
                        "prompt": prompt,
                        "model": HOOK_MODEL,
                        "timeout": HOOK_TIMEOUT_MS,
                        "if": "Write(*.cs)",
                    },
                ],
            }
        )
    else:
        pre_tool_use.append(
            {
                "_source": "dotnet-ai-kit-arch",
                "matcher": "Write|Edit",
                "hooks": [
                    {
                        "type": "prompt",
                        "prompt": prompt,
                        "model": HOOK_MODEL,
                        "timeout": HOOK_TIMEOUT_MS,
                    }
                ],
            }
        )

    hooks["PreToolUse"] = pre_tool_use
    settings["hooks"] = hooks

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return True


_QUICK_CLASSIFY_HEURISTICS: list[tuple[str, str]] = [
    ("AggregateRoot", "command"),
    ("EventSourcedAggregate", "command"),
    ("Aggregate<", "command"),
    ("IRequestHandler<Event<", "query-sql"),
    (".razor", "controlpanel"),
    ("IHostedService", "processor"),
]

_MICROSERVICE_TYPES = {
    "command",
    "query-sql",
    "query-cosmos",
    "processor",
    "gateway",
    "controlpanel",
    "hybrid",
}


def _quick_classify_repo(repo_path: Path) -> str:
    """Classify a .NET repo by scanning code for structural patterns."""
    for pattern, repo_type in _QUICK_CLASSIFY_HEURISTICS:
        for ext in ("**/*.cs", "**/*.csproj"):
            for f in repo_path.glob(ext):
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    if pattern in content:
                        return repo_type
                except OSError:
                    continue
    return "generic"


def _detect_git_default_branch(repo_path: Path) -> str:
    """Detect the default branch from git remote or current branch."""
    import subprocess

    # Try remote HEAD first
    result = subprocess.run(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD", "--short"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        # Returns "origin/main" -> extract "main"
        return result.stdout.strip().split("/", 1)[-1]

    # Fallback: current branch
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()

    return "main"


def _write_basic_project_yml(project_yml: Path, project_type: str) -> None:
    """Write a basic project.yml after auto-init."""
    import yaml

    mode = "microservice" if project_type in _MICROSERVICE_TYPES else "generic"
    data = {
        "mode": mode,
        "project_type": project_type,
        "confidence": "medium",
        "confidence_score": 0.5,
    }
    project_yml.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")


def _update_sibling_config(
    config_path: Path,
    primary_config: "DotnetAiConfig",
    default_branch: str,
) -> None:
    """Update a sibling repo's config with shared settings from primary."""
    import yaml

    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    # Company + branch
    cfg.setdefault("company", {})
    cfg["company"]["name"] = primary_config.company.name
    cfg["company"]["github_org"] = primary_config.company.github_org
    cfg["company"]["default_branch"] = default_branch

    # Naming conventions (shared across topology)
    cfg.setdefault("naming", {})
    cfg["naming"]["domain"] = primary_config.naming.domain
    cfg["naming"]["solution"] = primary_config.naming.solution
    cfg["naming"]["topic"] = primary_config.naming.topic
    cfg["naming"]["namespace"] = primary_config.naming.namespace

    # Style and permissions (match primary)
    cfg["command_style"] = primary_config.command_style
    cfg["permissions_level"] = primary_config.permissions_level

    config_path.write_text(yaml.dump(cfg, default_flow_style=False), encoding="utf-8")


def deploy_to_linked_repos(
    primary_root: Path,
    config: DotnetAiConfig,
    tool_version: str,
    package_dir: Path,
    branch_name: str = "chore/dotnet-ai-kit-setup",
    dry_run: bool = False,
) -> list[dict[str, str]]:
    """Deploy tooling to linked secondary repos during configure/upgrade.

    Iterates config.repos, checks initialization and version, deploys
    profiles/rules/agents/skills using existing copy_* functions.

    On failure for one repo, logs the error and continues to the next.

    Args:
        primary_root: Root of the primary repo.
        config: The primary repo's dotnet-ai-kit configuration.
        tool_version: Current tool version string.
        package_dir: The dotnet-ai-kit package installation directory.
        branch_name: Git branch name for commits in secondary repos.
        dry_run: If True, skip actual deployment and git operations.

    Returns:
        List of result dicts with keys: repo, status, reason.
    """
    import logging
    import subprocess

    import yaml

    from dotnet_ai_kit.agents import get_agent_config

    logger = logging.getLogger(__name__)
    results: list[dict[str, str]] = []

    repo_fields = ["command", "query", "processor", "gateway", "controlpanel"]

    for role in repo_fields:
        repo_path_str = getattr(config.repos, role, None)
        if not repo_path_str:
            continue

        # Skip remote repos
        if repo_path_str.startswith("github:"):
            logger.warning(
                "Skipping remote repo %s (%s) -- not cloned locally.",
                role,
                repo_path_str,
            )
            results.append(
                {
                    "repo": repo_path_str,
                    "status": "skipped",
                    "reason": "remote URL",
                }
            )
            continue

        repo_path = Path(repo_path_str)
        if not repo_path.is_dir():
            logger.warning("Cannot access %s — not found.", repo_path)
            results.append(
                {
                    "repo": str(repo_path),
                    "status": "skipped",
                    "reason": "directory not found",
                }
            )
            continue

        try:
            # Check initialization -- auto-init if missing
            just_initialized = False
            config_path = repo_path / ".dotnet-ai-kit" / "config.yml"
            project_yml = repo_path / ".dotnet-ai-kit" / "project.yml"
            if not config_path.is_file() or not project_yml.is_file():
                logger.info("Auto-initializing sibling repo %s...", repo_path.name)
                init_result = subprocess.run(
                    ["dotnet-ai", "init", "--force"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                )
                if init_result.returncode != 0:
                    logger.warning(
                        "Auto-init failed for %s: %s",
                        repo_path,
                        init_result.stderr.strip(),
                    )
                    results.append(
                        {
                            "repo": str(repo_path),
                            "status": "skipped",
                            "reason": "auto-init failed",
                        }
                    )
                    continue
                # Re-check after init
                if not config_path.is_file():
                    results.append(
                        {
                            "repo": str(repo_path),
                            "status": "skipped",
                            "reason": "not initialized after auto-init",
                        }
                    )
                    continue

                # Derive project type from config role
                role_to_type = {
                    "command": "command",
                    "query": "query-sql",
                    "processor": "processor",
                    "gateway": "gateway",
                    "controlpanel": "controlpanel",
                }
                detected_type = role_to_type.get(role, "generic")
                _write_basic_project_yml(project_yml, detected_type)

                # Detect git default branch and update config
                detected_branch = _detect_git_default_branch(repo_path)
                _update_sibling_config(
                    config_path,
                    config,
                    detected_branch,
                )

                just_initialized = True

            # Version check
            version_path = repo_path / ".dotnet-ai-kit" / "version.txt"
            secondary_version = ""
            if version_path.is_file():
                secondary_version = version_path.read_text(encoding="utf-8").strip()

            if secondary_version and parse_version(secondary_version) > parse_version(tool_version):
                msg = f"Secondary repo {repo_path} has newer version {secondary_version}."
                logger.warning(msg)
                results.append(
                    {
                        "repo": str(repo_path),
                        "status": "skipped",
                        "reason": "newer version",
                    }
                )
                continue

            if dry_run:
                results.append(
                    {
                        "repo": str(repo_path),
                        "status": "dry-run",
                        "reason": "would deploy",
                    }
                )
                continue

            # Check for dirty working directory (skip for self-repo and just-initialized)
            is_self_repo = repo_path.resolve() == primary_root.resolve()
            if not is_self_repo and not just_initialized:
                git_status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                )
                if git_status.stdout.strip():
                    logger.warning("Skipping %s -- dirty working directory.", repo_path)
                    results.append(
                        {
                            "repo": str(repo_path),
                            "status": "skipped",
                            "reason": "dirty working directory",
                        }
                    )
                    continue

            # Read secondary project type via load_project (FR-009).
            from .config import load_project as _load_proj

            if project_yml.is_file():
                _sec_proj = _load_proj(project_yml)
                sec_project_type = _sec_proj.project_type or "generic"
                sec_confidence = _sec_proj.confidence or "low"
            else:
                sec_project_type = "generic"
                sec_confidence = "low"
            # Create branch
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            # If branch exists, just checkout
            subprocess.run(
                ["git", "checkout", branch_name],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )

            # Read secondary detected_paths for skill token resolution
            sec_detected_paths = (
                _sec_proj.detected_paths if project_yml.is_file() and _sec_proj else None
            )

            # Deploy full tooling stack for each configured AI tool
            commands_dir = package_dir / "commands"
            rules_dir_src = package_dir / "rules"
            skills_dir_src = package_dir / "skills"
            agents_dir_src = package_dir / "agents"

            # Load secondary config once — used for command_style and ai_tools
            _sec_raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            sec_style = _sec_raw.get("command_style", "both")
            sec_ai_tools: list[str] = _sec_raw.get("ai_tools") or config.ai_tools

            for tool_name in sec_ai_tools:
                try:
                    tool_config = get_agent_config(tool_name)
                except ValueError:
                    continue

                # Deploy commands — use secondary repo's own command_style
                if commands_dir.is_dir():
                    sec_config = config.model_copy()
                    sec_config.command_style = sec_style
                    copy_commands(
                        commands_dir,
                        repo_path,
                        tool_config,
                        sec_config,
                    )

                # Deploy rules
                if rules_dir_src.is_dir():
                    copy_rules(rules_dir_src, repo_path, tool_config)

                # Deploy profile
                copy_profile(
                    repo_path,
                    tool_name,
                    sec_project_type,
                    package_dir,
                    confidence=sec_confidence,
                )

                # Deploy skills
                if skills_dir_src.is_dir():
                    copy_skills(
                        skills_dir_src,
                        repo_path,
                        tool_config,
                        detected_paths=sec_detected_paths,
                    )

                # Deploy agents
                if agents_dir_src.is_dir():
                    copy_agents(
                        agents_dir_src,
                        repo_path,
                        tool_config,
                        tool_name=tool_name,
                    )

                # Deploy hook (Claude only)
                if tool_name == "claude":
                    rules_dir = tool_config.get("rules_dir", ".claude/rules")
                    profile_deployed = repo_path / rules_dir / "architecture-profile.md"
                    if profile_deployed.is_file():
                        copy_hook(repo_path, profile_deployed, package_dir)

            # Write linked_from to secondary config
            sec_config_data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            sec_config_data["linked_from"] = str(primary_root)
            config_path.write_text(
                yaml.dump(sec_config_data, default_flow_style=False),
                encoding="utf-8",
            )

            # Update version
            version_path.parent.mkdir(parents=True, exist_ok=True)
            version_path.write_text(tool_version, encoding="utf-8")

            # Stage and commit — use secondary's ai_tools to determine directories
            staged_dirs: set[str] = {".dotnet-ai-kit/"}
            for _tool in sec_ai_tools:
                try:
                    _tc = get_agent_config(_tool)
                    for _key in ("rules_dir", "commands_dir", "skills_dir", "agents_dir"):
                        _d = _tc.get(_key, "")
                        if _d:
                            staged_dirs.add(_d.split("/")[0] + "/")
                except ValueError:
                    pass
            subprocess.run(
                ["git", "add"] + sorted(staged_dirs),
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "commit", "-m", "chore: deploy dotnet-ai-kit tooling"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )

            was_upgraded = secondary_version and parse_version(secondary_version) < parse_version(
                tool_version
            )
            action = "upgraded" if was_upgraded else "deployed"
            results.append({"repo": str(repo_path), "status": action, "reason": "success"})

        except Exception as exc:
            logger.error("Failed to deploy to %s: %s", repo_path, exc)
            results.append({"repo": str(repo_path), "status": "failed", "reason": str(exc)})

    return results


def scaffold_project(
    template_dir: Path,
    target_dir: Path,
    config: DotnetAiConfig,
    project_type: str,
) -> int:
    """Scaffold a new project from a template directory.

    Copies all files from the template, rendering Jinja2 placeholders.

    Args:
        template_dir: Path to the template directory (e.g., templates/command/).
        target_dir: Target directory for the new project.
        config: The dotnet-ai-kit configuration (provides Company, etc.).
        project_type: The project type being scaffolded.

    Returns:
        Number of files created.

    Raises:
        CopyError: If the template directory does not exist.
    """
    if not template_dir.is_dir():
        raise CopyError(f"Template directory not found: {template_dir}")

    target_dir.mkdir(parents=True, exist_ok=True)

    context = {
        "Company": config.company.name or "MyCompany",
        "company": (config.company.name or "MyCompany").lower(),
        "Domain": config.naming.domain or "Domain",
        "domain": (config.naming.domain or "Domain").lower(),
        "Side": project_type.capitalize().replace("-", ""),
        "side": project_type.lower().replace("-", ""),
        "Layer": "Application",
        "ProjectType": project_type,
    }

    count = 0
    for src_path in template_dir.rglob("*"):
        if src_path.is_dir():
            continue

        rel_path = src_path.relative_to(template_dir)
        dest_path = target_dir / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Check for template overrides in user's .dotnet-ai-kit/templates/
        override_dir = target_dir / ".dotnet-ai-kit" / "templates" / project_type
        override_path = override_dir / rel_path
        if override_path.is_file():
            src_path = override_path

        # Render as template if it's a text file
        if src_path.suffix in (".md", ".cs", ".yml", ".yaml", ".json", ".xml", ".csproj", ".sln"):
            render_template(src_path, dest_path, context)
        else:
            shutil.copy2(src_path, dest_path)

        count += 1

    return count


def merge_permissions(
    existing_settings: dict[str, Any],
    template_entries: list[str],
    managed_entries: list[str],
    level: str,
) -> dict[str, Any]:
    """Merge tool-managed permission entries into existing settings.

    Preserves user-defined allow, ask, and deny entries. Replaces
    previously managed entries with new template entries.

    Args:
        existing_settings: Current contents of the settings JSON file.
        template_entries: New permission entries from the selected template.
        managed_entries: Previously managed entries (from config.yml).
        level: Permission level ('minimal', 'standard', or 'full').

    Returns:
        Updated settings dict ready to be written to disk.
    """
    settings = dict(existing_settings)

    permissions = dict(settings.get("permissions", {}))

    current_allow = list(permissions.get("allow", []))

    managed_set = set(managed_entries)
    user_entries = [e for e in current_allow if e not in managed_set]

    template_set = set(template_entries)
    merged_allow = list(template_entries)
    for entry in user_entries:
        if entry not in template_set:
            merged_allow.append(entry)

    permissions["allow"] = merged_allow

    if level == "full":
        permissions["defaultMode"] = "bypassPermissions"
    else:
        permissions.pop("defaultMode", None)

    settings["permissions"] = permissions
    return settings


def copy_permissions(
    target_dir: Path,
    config: DotnetAiConfig,
    package_dir: Path,
    *,
    global_install: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Apply permission rules from a template to the AI assistant settings file.

    Reads the permission template for the configured level, merges with
    existing settings (preserving user entries), and writes the result.

    Args:
        target_dir: Root of the user's project.
        config: The dotnet-ai-kit configuration.
        package_dir: The dotnet-ai-kit package installation directory.
        global_install: If True, write to ~/.claude/settings.json instead.
        dry_run: If True, compute changes but do not write to disk.

    Returns:
        Dict with keys: 'settings_path', 'entries_count', 'mode', 'changed'.

    Raises:
        CopyError: If the template file is missing or settings JSON is invalid.
    """
    level = config.permissions_level

    template_path = package_dir / "config" / f"permissions-{level}.json"
    if not template_path.is_file():
        raise CopyError(
            f"Permission template not found: {template_path}. Try reinstalling dotnet-ai-kit."
        )

    template_data = json.loads(template_path.read_text(encoding="utf-8"))
    template_entries = template_data.get("permissions", {}).get("allow", [])

    if level == "full":
        mode = template_data.get("permissions", {}).get("defaultMode", "bypassPermissions")
    else:
        mode = None

    if global_install:
        settings_dir = Path.home() / ".claude"
    else:
        settings_dir = target_dir / ".claude"

    settings_path = settings_dir / "settings.json"

    existing_settings: dict[str, Any] = {}
    if settings_path.is_file():
        raw = settings_path.read_text(encoding="utf-8")
        try:
            existing_settings = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CopyError(
                f"Invalid JSON in {settings_path}: {exc}. Fix or remove the file, then re-run."
            ) from exc

    merged = merge_permissions(
        existing_settings,
        template_entries,
        config.managed_permissions,
        level,
    )

    changed = merged != existing_settings

    if not dry_run and changed:
        # Backup existing file before overwriting
        if settings_path.is_file():
            backup_dir = target_dir / ".dotnet-ai-kit" / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_dir / "settings.json.bak"
            shutil.copy2(settings_path, backup_path)

        settings_dir.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    config.managed_permissions = list(template_entries)

    # Verify write succeeded by reading back
    if not dry_run and changed:
        verify_result = verify_permissions(settings_path, level, len(template_entries))
        if not verify_result["ok"]:
            raise CopyError(
                f"Permission verification failed: {verify_result['reason']}. "
                f"Expected {verify_result['expected']}, got {verify_result['actual']}."
            )

    return {
        "settings_path": str(settings_path),
        "entries_count": len(template_entries),
        "mode": mode or "default",
        "changed": changed,
    }


def verify_permissions(
    settings_path: Path,
    expected_level: str,
    expected_count: int,
) -> dict[str, Any]:
    """Verify that settings.json matches the expected permission level.

    Reads the settings file back and checks that the allow list count
    and defaultMode are consistent with the configured level.

    Args:
        settings_path: Path to the settings.json file.
        expected_level: The configured permission level.
        expected_count: Minimum number of expected allow entries.

    Returns:
        Dict with 'ok' (bool), 'reason' (str), 'expected', 'actual'.
    """
    if not settings_path.is_file():
        return {
            "ok": False,
            "reason": "settings.json not found after write",
            "expected": f"{expected_count} entries",
            "actual": "file missing",
        }

    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {
            "ok": False,
            "reason": f"cannot read settings.json: {exc}",
            "expected": f"{expected_count} entries",
            "actual": "unreadable",
        }

    permissions = data.get("permissions", {})
    actual_count = len(permissions.get("allow", []))
    actual_mode = permissions.get("defaultMode")

    # Check entry count (allow some user-added entries, but must have at least the template count)
    if actual_count < expected_count:
        return {
            "ok": False,
            "reason": "allow list has fewer entries than expected",
            "expected": f">={expected_count} entries",
            "actual": f"{actual_count} entries",
        }

    # Check defaultMode for full level
    if expected_level == "full" and actual_mode != "bypassPermissions":
        return {
            "ok": False,
            "reason": "full mode requires bypassPermissions but it is missing",
            "expected": "bypassPermissions",
            "actual": str(actual_mode),
        }

    # Check defaultMode is NOT set for non-full levels
    if expected_level != "full" and actual_mode == "bypassPermissions":
        return {
            "ok": False,
            "reason": f"{expected_level} mode should not have bypassPermissions",
            "expected": "no defaultMode",
            "actual": "bypassPermissions",
        }

    return {
        "ok": True,
        "reason": "",
        "expected": f"{expected_count} entries, level={expected_level}",
        "actual": f"{actual_count} entries, mode={actual_mode or 'default'}",
    }


def get_template_source(
    project_root: Path,
    package_dir: Path,
    subdir: str,
) -> Path:
    """Resolve the template source directory, checking for user overrides.

    Checks for templates in:
        1. {project_root}/.dotnet-ai-kit/templates/{subdir}/
        2. {package_dir}/templates/{subdir}/  (fallback to package templates)

    Args:
        project_root: The user's project root.
        package_dir: The dotnet-ai-kit package installation directory.
        subdir: Subdirectory name (e.g., "commands", "command").

    Returns:
        Path to the template source directory.
    """
    override_dir = project_root / ".dotnet-ai-kit" / "templates" / subdir
    if override_dir.is_dir():
        return override_dir

    return package_dir / subdir
