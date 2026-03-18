"""File copy and Jinja2 template rendering for dotnet-ai-kit.

Handles copying command/rule files to AI tool directories, rendering
Jinja2 templates with project-specific context, and scaffolding new
projects from templates.
"""

from __future__ import annotations

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
        undefined=jinja2.Undefined,
        keep_trailing_newline=True,
    )
    template = env.from_string(text)
    rendered = template.render(**context)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")


def copy_commands(
    source_dir: Path,
    target_dir: Path,
    agent_config: dict[str, Any],
    config: DotnetAiConfig,
) -> int:
    """Copy command files from the source to the AI tool's commands directory.

    Handles command_style (full/short/both) by creating alias files for short names.

    Args:
        source_dir: Directory containing command template .md files.
        target_dir: Root of the user's project.
        agent_config: Configuration dict for the target AI tool.
        config: The dotnet-ai-kit configuration.

    Returns:
        Number of command files copied.
    """
    commands_dir_rel = agent_config.get("commands_dir")
    if not commands_dir_rel:
        return 0

    commands_dir = target_dir / commands_dir_rel
    commands_dir.mkdir(parents=True, exist_ok=True)

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

        if config.command_style in ("full", "both"):
            out_path = commands_dir / full_name
            out_path.write_text(content, encoding="utf-8")
            count += 1

        if config.command_style in ("short", "both"):
            # Short alias: dai.specify.md that includes/references the full command
            short_prefix = "dai"
            short_name = f"{short_prefix}.{cmd_name}{ext}"
            short_path = commands_dir / short_name

            if config.command_style == "short":
                # Write the actual content with short name
                short_path.write_text(content, encoding="utf-8")
                count += 1
            elif config.command_style == "both":
                # Write an alias that references the full command
                alias_content = (
                    f"---\n"
                    f"description: Alias for /{prefix}.{cmd_name}\n"
                    f"---\n\n"
                    f"See /{prefix}.{cmd_name} for full documentation.\n\n"
                    f"Run /{prefix}.{cmd_name} with the same arguments.\n"
                )
                short_path.write_text(alias_content, encoding="utf-8")
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
        "Domain": "Domain",
        "domain": "domain",
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
