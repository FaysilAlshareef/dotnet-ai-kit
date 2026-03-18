"""Tests for file copy and Jinja2 template rendering."""

from __future__ import annotations

from pathlib import Path

import pytest

from dotnet_ai_kit.copier import (
    CopyError,
    copy_commands,
    copy_commands_codex,
    copy_commands_cursor,
    copy_rules,
    render_template,
    scaffold_project,
)
from dotnet_ai_kit.models import DotnetAiConfig


def _create_command_files(source_dir: Path, names: list[str]) -> None:
    """Create sample command .md files in a directory."""
    source_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        (source_dir / f"{name}.md").write_text(
            f"---\ndescription: {name} command\n---\n\n"
            f"# /dotnet-ai.{name}\n\n"
            f"Run the {name} command with $ARGUMENTS.\n",
            encoding="utf-8",
        )


def _create_rule_files(source_dir: Path, names: list[str]) -> None:
    """Create sample rule .md files in a directory."""
    source_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        (source_dir / f"{name}.md").write_text(
            f"---\ndescription: {name} rule\n---\n\n# {name}\n\nFollow {name} conventions.\n",
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# render_template
# ---------------------------------------------------------------------------


def test_render_template_replaces_placeholders(tmp_path: Path) -> None:
    """Jinja2 template rendering should replace {Company} style placeholders."""
    template = tmp_path / "template.cs"
    template.write_text(
        "namespace {Company}.{Domain}.{Layer};\n\npublic class {Company}Service { }\n",
        encoding="utf-8",
    )
    output = tmp_path / "output.cs"

    render_template(template, output, {"Company": "Acme", "Domain": "Orders", "Layer": "API"})

    content = output.read_text(encoding="utf-8")
    assert "namespace Acme.Orders.API;" in content
    assert "public class AcmeService { }" in content


def test_render_template_creates_parent_dirs(tmp_path: Path) -> None:
    """render_template should create parent directories."""
    template = tmp_path / "template.md"
    template.write_text("Hello {Company}!\n", encoding="utf-8")
    output = tmp_path / "deep" / "nested" / "output.md"

    render_template(template, output, {"Company": "Test"})

    assert output.is_file()
    assert "Hello Test!" in output.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# copy_commands
# ---------------------------------------------------------------------------


def test_copy_commands_full_style(tmp_path: Path) -> None:
    """copy_commands with 'full' style should create only full-name files."""
    source = tmp_path / "commands_src"
    _create_command_files(source, ["specify", "plan", "implement"])
    target = tmp_path / "project"
    target.mkdir()

    agent_config = {
        "commands_dir": ".claude/commands",
        "command_ext": ".md",
        "command_prefix": "dotnet-ai",
        "args_placeholder": "$ARGUMENTS",
    }
    config = DotnetAiConfig(ai_tools=["claude"], command_style="full")

    count = copy_commands(source, target, agent_config, config)

    assert count == 3
    assert (target / ".claude" / "commands" / "dotnet-ai.specify.md").is_file()
    assert (target / ".claude" / "commands" / "dotnet-ai.plan.md").is_file()
    assert (target / ".claude" / "commands" / "dotnet-ai.implement.md").is_file()
    # No short aliases
    assert not (target / ".claude" / "commands" / "dai.specify.md").exists()


def test_copy_commands_both_style(tmp_path: Path) -> None:
    """copy_commands with 'both' style should create full names and short aliases."""
    source = tmp_path / "commands_src"
    _create_command_files(source, ["specify"])
    target = tmp_path / "project"
    target.mkdir()

    agent_config = {
        "commands_dir": ".claude/commands",
        "command_ext": ".md",
        "command_prefix": "dotnet-ai",
        "args_placeholder": "$ARGUMENTS",
    }
    config = DotnetAiConfig(ai_tools=["claude"], command_style="both")

    count = copy_commands(source, target, agent_config, config)

    assert count == 2  # 1 full + 1 alias
    assert (target / ".claude" / "commands" / "dotnet-ai.specify.md").is_file()
    assert (target / ".claude" / "commands" / "dai.specify.md").is_file()


def test_copy_commands_short_style(tmp_path: Path) -> None:
    """copy_commands with 'short' style should create only short-name files."""
    source = tmp_path / "commands_src"
    _create_command_files(source, ["specify"])
    target = tmp_path / "project"
    target.mkdir()

    agent_config = {
        "commands_dir": ".claude/commands",
        "command_ext": ".md",
        "command_prefix": "dotnet-ai",
        "args_placeholder": "$ARGUMENTS",
    }
    config = DotnetAiConfig(ai_tools=["claude"], command_style="short")

    count = copy_commands(source, target, agent_config, config)

    assert count == 1
    assert (target / ".claude" / "commands" / "dai.specify.md").is_file()
    assert not (target / ".claude" / "commands" / "dotnet-ai.specify.md").exists()


def test_copy_commands_no_commands_dir(tmp_path: Path) -> None:
    """copy_commands should return 0 when agent has no commands_dir."""
    source = tmp_path / "commands_src"
    _create_command_files(source, ["specify"])
    target = tmp_path / "project"
    target.mkdir()

    agent_config = {"commands_dir": None}
    config = DotnetAiConfig(ai_tools=["cursor"])

    count = copy_commands(source, target, agent_config, config)
    assert count == 0


# ---------------------------------------------------------------------------
# copy_rules
# ---------------------------------------------------------------------------


def test_copy_rules_to_claude(tmp_path: Path) -> None:
    """copy_rules should copy rule files to the rules directory."""
    source = tmp_path / "rules_src"
    _create_rule_files(source, ["naming", "coding-style"])
    target = tmp_path / "project"
    target.mkdir()

    agent_config = {"rules_dir": ".claude/rules"}

    count = copy_rules(source, target, agent_config)

    assert count == 2
    assert (target / ".claude" / "rules" / "naming.md").is_file()
    assert (target / ".claude" / "rules" / "coding-style.md").is_file()


def test_copy_rules_no_rules_dir(tmp_path: Path) -> None:
    """copy_rules should return 0 when agent has no rules_dir."""
    source = tmp_path / "rules_src"
    _create_rule_files(source, ["naming"])
    target = tmp_path / "project"
    target.mkdir()

    agent_config = {"rules_dir": None}
    count = copy_rules(source, target, agent_config)
    assert count == 0


# ---------------------------------------------------------------------------
# Cursor and Codex
# ---------------------------------------------------------------------------


def test_copy_commands_cursor_creates_mdc(tmp_path: Path) -> None:
    """Cursor mode should create a single .mdc file combining commands and rules."""
    source = tmp_path / "commands_src"
    _create_command_files(source, ["specify", "plan"])
    rules = tmp_path / "rules_src"
    _create_rule_files(rules, ["naming"])
    target = tmp_path / "project"
    target.mkdir()

    agent_config = {"rules_dir": ".cursor/rules"}

    count = copy_commands_cursor(source, target, agent_config, rules)

    assert count == 1
    mdc_path = target / ".cursor" / "rules" / "dotnet-ai-kit.mdc"
    assert mdc_path.is_file()
    content = mdc_path.read_text(encoding="utf-8")
    assert "Rule: naming" in content
    assert "Command: dotnet-ai.specify" in content
    assert "Command: dotnet-ai.plan" in content


def test_copy_commands_codex_creates_agents_md(tmp_path: Path) -> None:
    """Codex mode should create an AGENTS.md file."""
    source = tmp_path / "commands_src"
    _create_command_files(source, ["specify", "plan"])
    target = tmp_path / "project"
    target.mkdir()

    agent_config = {"agents_file": "AGENTS.md"}

    count = copy_commands_codex(source, target, agent_config)

    assert count == 1
    agents_path = target / "AGENTS.md"
    assert agents_path.is_file()
    content = agents_path.read_text(encoding="utf-8")
    assert "dotnet-ai.specify" in content
    assert "dotnet-ai.plan" in content


# ---------------------------------------------------------------------------
# scaffold_project
# ---------------------------------------------------------------------------


def test_scaffold_project_copies_template_files(tmp_path: Path) -> None:
    """scaffold_project should copy and render template files."""
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "README.md").write_text("# {Company} Project\n", encoding="utf-8")
    (template_dir / "src").mkdir()
    (template_dir / "src" / "Program.cs").write_text(
        "namespace {Company}.{Domain};\n\nclass Program { }\n",
        encoding="utf-8",
    )

    target = tmp_path / "new_project"
    config = DotnetAiConfig(company={"name": "Acme"})

    count = scaffold_project(template_dir, target, config, "command")

    assert count == 2
    readme = (target / "README.md").read_text(encoding="utf-8")
    assert "Acme" in readme
    program = (target / "src" / "Program.cs").read_text(encoding="utf-8")
    assert "namespace Acme." in program


def test_scaffold_project_missing_template_dir(tmp_path: Path) -> None:
    """scaffold_project should raise CopyError for missing template directory."""
    config = DotnetAiConfig()

    with pytest.raises(CopyError, match="Template directory not found"):
        scaffold_project(tmp_path / "nonexistent", tmp_path / "target", config, "command")
