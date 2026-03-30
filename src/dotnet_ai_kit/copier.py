"""File copy and Jinja2 template rendering for dotnet-ai-kit.

Handles copying command/rule files to AI tool directories, rendering
Jinja2 templates with project-specific context, and scaffolding new
projects from templates.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any, Optional

import jinja2

from dotnet_ai_kit.models import DotnetAiConfig


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
            short_name = f"{short_prefix}.{cmd_name}{ext}"
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


def copy_skills(
    source_dir: Path,
    target_dir: Path,
    agent_config: dict[str, Any],
) -> int:
    """Copy skill files from the source to the AI tool's skills directory.

    Recursively copies the skills directory structure preserving
    category/subcategory organization.

    Args:
        source_dir: Directory containing skill subdirectories.
        target_dir: Root of the user's project.
        agent_config: Configuration dict for the target AI tool.

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
        dest.write_text(content, encoding="utf-8")
        count += 1

    return count


def copy_agents(
    source_dir: Path,
    target_dir: Path,
    agent_config: dict[str, Any],
) -> int:
    """Copy agent files from the source to the AI tool's agents directory.

    Flat copy of all .md files in the agents directory.

    Args:
        source_dir: Directory containing agent .md files.
        target_dir: Root of the user's project.
        agent_config: Configuration dict for the target AI tool.

    Returns:
        Number of agent files copied.
    """
    agents_dir_rel = agent_config.get("agents_dir")
    if not agents_dir_rel:
        return 0

    agents_dir = target_dir / agents_dir_rel
    # Remove existing agents directory to ensure clean overwrite
    if agents_dir.is_dir():
        shutil.rmtree(agents_dir)
    agents_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    agent_files = sorted(source_dir.glob("*.md"))

    for agent_file in agent_files:
        content = agent_file.read_text(encoding="utf-8")
        dest = agents_dir / agent_file.name
        dest.write_text(content, encoding="utf-8")
        count += 1

    return count


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
