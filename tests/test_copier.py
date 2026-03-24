"""Tests for file copy and Jinja2 template rendering."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dotnet_ai_kit.copier import (
    CopyError,
    copy_agents,
    copy_commands,
    copy_commands_codex,
    copy_commands_cursor,
    copy_permissions,
    copy_rules,
    copy_skills,
    merge_permissions,
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


# ---------------------------------------------------------------------------
# copy_skills
# ---------------------------------------------------------------------------


def _create_skill_files(source_dir: Path) -> None:
    """Create a sample skills directory structure."""
    skills = [
        ("core", "configuration", "SKILL.md"),
        ("core", "dependency-injection", "SKILL.md"),
        ("microservice", "command", "SKILL.md"),
        ("microservice", "query", "SKILL.md"),
    ]
    for cat, subcat, filename in skills:
        skill_dir = source_dir / cat / subcat
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / filename).write_text(
            f"# {cat}/{subcat}\n\nSkill content for {subcat}.\n",
            encoding="utf-8",
        )


def test_copy_skills_preserves_directory_structure(tmp_path: Path) -> None:
    """copy_skills should recursively copy skills preserving category structure."""
    source = tmp_path / "skills_src"
    _create_skill_files(source)
    target = tmp_path / "project"
    target.mkdir()

    agent_config = {"skills_dir": ".claude/skills"}

    count = copy_skills(source, target, agent_config)

    assert count == 4
    assert (target / ".claude" / "skills" / "core" / "configuration" / "SKILL.md").is_file()
    assert (target / ".claude" / "skills" / "core" / "dependency-injection" / "SKILL.md").is_file()
    assert (target / ".claude" / "skills" / "microservice" / "command" / "SKILL.md").is_file()
    assert (target / ".claude" / "skills" / "microservice" / "query" / "SKILL.md").is_file()

    content = (target / ".claude" / "skills" / "core" / "configuration" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "Skill content for configuration" in content


def test_copy_skills_overwrites_existing(tmp_path: Path) -> None:
    """copy_skills should overwrite existing skills directory with latest version."""
    source = tmp_path / "skills_src"
    _create_skill_files(source)
    target = tmp_path / "project"
    target.mkdir()

    agent_config = {"skills_dir": ".claude/skills"}

    # First copy
    copy_skills(source, target, agent_config)

    # Add an extra file that should be removed on re-copy
    old_file = target / ".claude" / "skills" / "old" / "stale" / "SKILL.md"
    old_file.parent.mkdir(parents=True, exist_ok=True)
    old_file.write_text("stale content", encoding="utf-8")

    # Second copy should overwrite
    count = copy_skills(source, target, agent_config)

    assert count == 4
    assert not old_file.exists()


def test_copy_skills_no_skills_dir(tmp_path: Path) -> None:
    """copy_skills should return 0 when agent has no skills_dir."""
    source = tmp_path / "skills_src"
    _create_skill_files(source)
    target = tmp_path / "project"
    target.mkdir()

    agent_config = {"skills_dir": None}
    count = copy_skills(source, target, agent_config)
    assert count == 0


# ---------------------------------------------------------------------------
# copy_agents
# ---------------------------------------------------------------------------


def _create_agent_files(source_dir: Path) -> None:
    """Create sample agent .md files."""
    source_dir.mkdir(parents=True, exist_ok=True)
    agents = ["command-architect", "query-architect", "processor-architect"]
    for name in agents:
        (source_dir / f"{name}.md").write_text(
            f"# {name}\n\n**Role**: Specialist for {name}.\n",
            encoding="utf-8",
        )


def test_copy_agents_flat_copy(tmp_path: Path) -> None:
    """copy_agents should flat-copy all agent .md files."""
    source = tmp_path / "agents_src"
    _create_agent_files(source)
    target = tmp_path / "project"
    target.mkdir()

    agent_config = {"agents_dir": ".claude/agents"}

    count = copy_agents(source, target, agent_config)

    assert count == 3
    assert (target / ".claude" / "agents" / "command-architect.md").is_file()
    assert (target / ".claude" / "agents" / "query-architect.md").is_file()
    assert (target / ".claude" / "agents" / "processor-architect.md").is_file()


def test_copy_agents_overwrites_existing(tmp_path: Path) -> None:
    """copy_agents should overwrite existing agents directory."""
    source = tmp_path / "agents_src"
    _create_agent_files(source)
    target = tmp_path / "project"
    target.mkdir()

    agent_config = {"agents_dir": ".claude/agents"}

    # First copy
    copy_agents(source, target, agent_config)

    # Add stale file
    stale = target / ".claude" / "agents" / "stale-agent.md"
    stale.write_text("stale", encoding="utf-8")

    # Second copy should overwrite
    count = copy_agents(source, target, agent_config)

    assert count == 3
    assert not stale.exists()


def test_copy_agents_no_agents_dir(tmp_path: Path) -> None:
    """copy_agents should return 0 when agent has no agents_dir."""
    source = tmp_path / "agents_src"
    _create_agent_files(source)
    target = tmp_path / "project"
    target.mkdir()

    agent_config = {"agents_dir": None}
    count = copy_agents(source, target, agent_config)
    assert count == 0


# ---------------------------------------------------------------------------
# Jinja2 StrictUndefined
# ---------------------------------------------------------------------------


def test_render_template_strict_undefined_raises(tmp_path: Path) -> None:
    """render_template should raise on missing variables with StrictUndefined."""
    import jinja2

    template = tmp_path / "template.md"
    template.write_text("Hello {{ MissingVar }}!\n", encoding="utf-8")
    output = tmp_path / "output.md"

    with pytest.raises(jinja2.UndefinedError):
        render_template(template, output, {})


# ---------------------------------------------------------------------------
# merge_permissions
# ---------------------------------------------------------------------------


def test_merge_permissions_empty_settings() -> None:
    """merge_permissions with empty settings returns template entries."""
    result = merge_permissions({}, ["Bash(ls *)"], [], "standard")
    assert result["permissions"]["allow"] == ["Bash(ls *)"]
    assert "defaultMode" not in result["permissions"]


def test_merge_permissions_preserves_user_entries() -> None:
    """User-added entries not in managed list are preserved."""
    existing = {"permissions": {"allow": ["Bash(my-custom *)"]}}
    result = merge_permissions(existing, ["Bash(ls *)"], [], "standard")
    assert "Bash(my-custom *)" in result["permissions"]["allow"]
    assert "Bash(ls *)" in result["permissions"]["allow"]


def test_merge_permissions_replaces_managed_entries() -> None:
    """Old managed entries are removed and replaced by new template."""
    existing = {"permissions": {"allow": ["Bash(old *)", "Bash(user *)"]}}
    managed = ["Bash(old *)"]
    result = merge_permissions(existing, ["Bash(new *)"], managed, "standard")
    assert "Bash(old *)" not in result["permissions"]["allow"]
    assert "Bash(new *)" in result["permissions"]["allow"]
    assert "Bash(user *)" in result["permissions"]["allow"]


def test_merge_permissions_preserves_deny_ask() -> None:
    """deny and ask rules are never modified."""
    existing = {
        "permissions": {
            "allow": [],
            "deny": ["Bash(rm -rf *)"],
            "ask": ["Bash(git push *)"],
        }
    }
    result = merge_permissions(existing, ["Bash(ls *)"], [], "standard")
    assert result["permissions"]["deny"] == ["Bash(rm -rf *)"]
    assert result["permissions"]["ask"] == ["Bash(git push *)"]


def test_merge_permissions_full_sets_bypass() -> None:
    """Full level sets defaultMode to bypassPermissions."""
    result = merge_permissions({}, ["Bash(ls *)"], [], "full")
    assert result["permissions"]["defaultMode"] == "bypassPermissions"


def test_merge_permissions_standard_no_bypass() -> None:
    """Standard level does NOT set defaultMode."""
    result = merge_permissions({}, ["Bash(ls *)"], [], "standard")
    assert "defaultMode" not in result["permissions"]


def test_merge_permissions_removes_bypass_on_downgrade() -> None:
    """Downgrading from full removes defaultMode."""
    existing = {"permissions": {"defaultMode": "bypassPermissions", "allow": []}}
    result = merge_permissions(existing, ["Bash(ls *)"], [], "standard")
    assert "defaultMode" not in result["permissions"]


def test_merge_permissions_deduplication() -> None:
    """User entry matching template entry is not duplicated."""
    existing = {"permissions": {"allow": ["Bash(ls *)"]}}
    result = merge_permissions(existing, ["Bash(ls *)"], [], "standard")
    assert result["permissions"]["allow"].count("Bash(ls *)") == 1


def test_merge_permissions_preserves_other_keys() -> None:
    """Top-level keys like hooks and env are preserved."""
    existing = {"hooks": {"preToolUse": ["./check.sh"]}, "permissions": {"allow": []}}
    result = merge_permissions(existing, ["Bash(ls *)"], [], "standard")
    assert result["hooks"] == {"preToolUse": ["./check.sh"]}


# ---------------------------------------------------------------------------
# copy_permissions
# ---------------------------------------------------------------------------


def _create_permission_template(config_dir: Path, level: str, entries: list[str]) -> None:
    """Create a permission template JSON in the config dir."""
    config_dir.mkdir(parents=True, exist_ok=True)
    data: dict = {"permissions": {"allow": entries}}
    if level == "full":
        data["permissions"]["defaultMode"] = "bypassPermissions"
    (config_dir / f"permissions-{level}.json").write_text(
        json.dumps(data), encoding="utf-8"
    )


def test_copy_permissions_creates_settings_file(tmp_path: Path) -> None:
    """copy_permissions creates .claude/settings.json when missing."""
    import json

    pkg = tmp_path / "pkg"
    _create_permission_template(pkg / "config", "standard", ["Bash(ls *)"])
    target = tmp_path / "project"
    target.mkdir()
    config = DotnetAiConfig(permissions_level="standard")

    result = copy_permissions(target, config, pkg)

    settings_path = target / ".claude" / "settings.json"
    assert settings_path.is_file()
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    assert "Bash(ls *)" in data["permissions"]["allow"]
    assert result["changed"] is True


def test_copy_permissions_preserves_existing(tmp_path: Path) -> None:
    """copy_permissions preserves user entries in existing settings."""
    import json

    pkg = tmp_path / "pkg"
    _create_permission_template(pkg / "config", "standard", ["Bash(ls *)"])
    target = tmp_path / "project"
    claude_dir = target / ".claude"
    claude_dir.mkdir(parents=True)
    (claude_dir / "settings.json").write_text(
        json.dumps({"permissions": {"allow": ["Bash(my-custom *)"]}}),
        encoding="utf-8",
    )
    config = DotnetAiConfig(permissions_level="standard")

    copy_permissions(target, config, pkg)

    data = json.loads((claude_dir / "settings.json").read_text(encoding="utf-8"))
    assert "Bash(my-custom *)" in data["permissions"]["allow"]
    assert "Bash(ls *)" in data["permissions"]["allow"]


def test_copy_permissions_invalid_json_raises(tmp_path: Path) -> None:
    """copy_permissions raises CopyError on invalid JSON."""
    pkg = tmp_path / "pkg"
    _create_permission_template(pkg / "config", "standard", ["Bash(ls *)"])
    target = tmp_path / "project"
    claude_dir = target / ".claude"
    claude_dir.mkdir(parents=True)
    (claude_dir / "settings.json").write_text("{bad json", encoding="utf-8")
    config = DotnetAiConfig(permissions_level="standard")

    with pytest.raises(CopyError, match="Invalid JSON"):
        copy_permissions(target, config, pkg)


def test_copy_permissions_missing_template_raises(tmp_path: Path) -> None:
    """copy_permissions raises CopyError when template file is missing."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    target = tmp_path / "project"
    target.mkdir()
    config = DotnetAiConfig(permissions_level="full")

    with pytest.raises(CopyError, match="Permission template not found"):
        copy_permissions(target, config, pkg)


def test_copy_permissions_full_sets_bypass(tmp_path: Path) -> None:
    """Full level writes bypassPermissions to settings."""
    import json

    pkg = tmp_path / "pkg"
    _create_permission_template(pkg / "config", "full", ["Bash(ls *)"])
    target = tmp_path / "project"
    target.mkdir()
    config = DotnetAiConfig(permissions_level="full")

    result = copy_permissions(target, config, pkg)

    data = json.loads(
        (target / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    assert data["permissions"]["defaultMode"] == "bypassPermissions"
    assert result["mode"] == "bypassPermissions"


def test_copy_permissions_dry_run_no_write(tmp_path: Path) -> None:
    """dry_run=True computes result but does not write to disk."""
    pkg = tmp_path / "pkg"
    _create_permission_template(pkg / "config", "standard", ["Bash(ls *)"])
    target = tmp_path / "project"
    target.mkdir()
    config = DotnetAiConfig(permissions_level="standard")

    result = copy_permissions(target, config, pkg, dry_run=True)

    assert result["changed"] is True
    assert not (target / ".claude" / "settings.json").exists()


def test_copy_permissions_creates_backup(tmp_path: Path) -> None:
    """copy_permissions backs up existing settings before overwriting."""
    import json

    pkg = tmp_path / "pkg"
    _create_permission_template(pkg / "config", "standard", ["Bash(ls *)"])
    target = tmp_path / "project"
    claude_dir = target / ".claude"
    claude_dir.mkdir(parents=True)
    original = {"permissions": {"allow": ["Bash(old *)"]}}
    (claude_dir / "settings.json").write_text(
        json.dumps(original), encoding="utf-8"
    )
    config = DotnetAiConfig(permissions_level="standard")

    copy_permissions(target, config, pkg)

    backup = target / ".dotnet-ai-kit" / "backups" / "settings.json.bak"
    assert backup.is_file()
    backup_data = json.loads(backup.read_text(encoding="utf-8"))
    assert backup_data == original


# ---------------------------------------------------------------------------
# Permission template validation
# ---------------------------------------------------------------------------


def _get_real_config_dir() -> Path:
    """Get the config/ directory in the repo root."""
    return Path(__file__).resolve().parent.parent / "config"


@pytest.mark.parametrize(
    "level",
    ["minimal", "standard", "full"],
)
def test_permission_template_valid_json(level: str) -> None:
    """Each permission template must be valid JSON with correct structure."""
    config_dir = _get_real_config_dir()
    path = config_dir / f"permissions-{level}.json"
    assert path.is_file(), f"Template missing: {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "permissions" in data
    assert "allow" in data["permissions"]
    assert isinstance(data["permissions"]["allow"], list)
    assert len(data["permissions"]["allow"]) > 0


def test_permission_template_full_has_bypass() -> None:
    """Full template must set defaultMode to bypassPermissions."""
    config_dir = _get_real_config_dir()
    data = json.loads(
        (config_dir / "permissions-full.json").read_text(encoding="utf-8")
    )
    assert data["permissions"].get("defaultMode") == "bypassPermissions"


def test_permission_template_standard_no_bypass() -> None:
    """Standard template must NOT set defaultMode."""
    config_dir = _get_real_config_dir()
    data = json.loads(
        (config_dir / "permissions-standard.json").read_text(encoding="utf-8")
    )
    assert "defaultMode" not in data["permissions"]


def test_permission_template_no_duplicates() -> None:
    """No permission template should have duplicate entries."""
    config_dir = _get_real_config_dir()
    for level in ["minimal", "standard", "full"]:
        data = json.loads(
            (config_dir / f"permissions-{level}.json").read_text(encoding="utf-8")
        )
        entries = data["permissions"]["allow"]
        assert len(entries) == len(set(entries)), f"Duplicates in {level} template"
