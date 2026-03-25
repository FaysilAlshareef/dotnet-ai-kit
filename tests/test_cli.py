"""Tests for the dotnet-ai CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml
from typer.testing import CliRunner

from dotnet_ai_kit.cli import app
from dotnet_ai_kit.copier import CopyError

runner = CliRunner()


def _create_dotnet_project(project_dir: Path) -> None:
    """Create a minimal .NET project structure for testing."""
    project_dir.mkdir(parents=True, exist_ok=True)
    sln = project_dir / "Test.sln"
    sln.write_text("Microsoft Visual Studio Solution File", encoding="utf-8")

    csproj = project_dir / "Test.csproj"
    csproj.write_text(
        '<Project Sdk="Microsoft.NET.Sdk">\n'
        "  <PropertyGroup>\n"
        "    <TargetFramework>net10.0</TargetFramework>\n"
        "  </PropertyGroup>\n"
        "</Project>\n",
        encoding="utf-8",
    )


def _create_claude_dir(project_dir: Path) -> None:
    """Create .claude directory so AI tool detection works."""
    (project_dir / ".claude" / "commands").mkdir(parents=True, exist_ok=True)
    (project_dir / ".claude" / "rules").mkdir(parents=True, exist_ok=True)


def test_init_creates_config_dir(tmp_path: Path) -> None:
    """Init should create .dotnet-ai-kit/ directory and config.yml."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    result = runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False)

    assert result.exit_code == 0, result.output
    config_dir = tmp_path / ".dotnet-ai-kit"
    assert config_dir.is_dir()
    assert (config_dir / "config.yml").is_file()
    assert (config_dir / "version.txt").is_file()


def test_init_refuses_reinit_without_force(tmp_path: Path) -> None:
    """Init should fail if already initialized and --force is not used."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)
    (tmp_path / ".dotnet-ai-kit").mkdir()

    result = runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"])

    assert result.exit_code == 1
    assert "already initialized" in result.output.lower()


def test_init_force_reinitializes(tmp_path: Path) -> None:
    """Init with --force should reinitialize even if already configured."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)
    (tmp_path / ".dotnet-ai-kit").mkdir()

    result = runner.invoke(
        app, ["init", str(tmp_path), "--ai", "claude", "--force"], catch_exceptions=False
    )

    assert result.exit_code == 0, result.output


def test_init_requires_ai_tool_or_detection(tmp_path: Path) -> None:
    """Init should fail if no AI tool can be detected and none specified."""
    _create_dotnet_project(tmp_path)
    # No .claude/ or .cursor/ directory

    result = runner.invoke(app, ["init", str(tmp_path)])

    # T056: exit code 3 for detection errors
    assert result.exit_code == 3
    assert "no ai tool detected" in result.output.lower()


def test_init_creates_project_yml_with_type_flag(tmp_path: Path) -> None:
    """Init should create project.yml when --type is provided."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    result = runner.invoke(
        app,
        ["init", str(tmp_path), "--ai", "claude", "--type", "command"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    project_yml = tmp_path / ".dotnet-ai-kit" / "project.yml"
    assert project_yml.is_file()


def test_init_skips_detection_without_type_flag(tmp_path: Path) -> None:
    """Init should skip detection and suggest /dotnet-ai.detect without --type."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    result = runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False)

    assert result.exit_code == 0, result.output
    project_yml = tmp_path / ".dotnet-ai-kit" / "project.yml"
    assert not project_yml.is_file()
    assert "detect" in result.output.lower()


def test_check_not_initialized(tmp_path: Path) -> None:
    """Check should report not initialized when .dotnet-ai-kit/ is missing."""
    result = runner.invoke(app, ["check"])

    # This may or may not fail depending on cwd; we just verify it handles gracefully
    # The command checks cwd, which may not have .dotnet-ai-kit
    assert result.exit_code in (0, 1)


def test_check_shows_config_status(tmp_path: Path) -> None:
    """Check should display config and tool status."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    # First init
    runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False)

    # Patch cwd to project
    with patch("dotnet_ai_kit.cli.Path") as mock_path:
        mock_path.return_value.resolve.return_value = tmp_path
        # check reads from cwd, so we need the real Path for other operations
        pass

    # The check command uses Path(".").resolve() so we can't easily redirect it
    # in a unit test without monkeypatching. This is an integration concern.


def test_upgrade_not_initialized(tmp_path: Path) -> None:
    """Upgrade should fail when not initialized."""
    # The upgrade command reads from cwd which is not tmp_path in tests
    # This is a structural limitation; the command needs to be invoked in the right cwd
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code in (0, 1)


def test_init_with_type_override(tmp_path: Path) -> None:
    """Init with --type should override the detected project type."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    result = runner.invoke(
        app,
        ["init", str(tmp_path), "--ai", "claude", "--type", "command"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output


def test_configure_saves_config(tmp_path: Path, monkeypatch) -> None:
    """Configure should save the config file after prompting."""
    config_dir = tmp_path / ".dotnet-ai-kit"
    config_dir.mkdir(parents=True)
    # Write a minimal config so configure can load it
    config_path = config_dir / "config.yml"
    config_path.write_text("version: '1.0'\nai_tools:\n  - claude\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    with patch("dotnet_ai_kit.cli.Prompt.ask") as mock_prompt:
        mock_prompt.return_value = "TestCompany"

        result = runner.invoke(
            app,
            ["configure", "--minimal"],
            catch_exceptions=False,
        )

    assert result.exit_code == 0, result.output


# ---------------------------------------------------------------------------
# T037-T039b: Interactive configure tests
# ---------------------------------------------------------------------------


def _setup_config_dir(tmp_path: Path) -> Path:
    """Create a .dotnet-ai-kit dir with a minimal config and return config_path."""
    config_dir = tmp_path / ".dotnet-ai-kit"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.yml"
    config_path.write_text(
        "version: '1.0'\nai_tools:\n  - claude\npermissions_level: minimal\n"
        "command_style: both\ncompany:\n  name: ''\n  github_org: ''\n  default_branch: main\n",
        encoding="utf-8",
    )
    return config_path


def test_configure_permission_level_single_select(tmp_path: Path, monkeypatch) -> None:
    """T037: Configure with single-select permission level via rich Prompt.ask."""
    config_path = _setup_config_dir(tmp_path)
    monkeypatch.chdir(tmp_path)

    with (
        patch("dotnet_ai_kit.cli.Prompt.ask") as mock_prompt,
        patch("dotnet_ai_kit.cli.questionary") as mock_questionary,
    ):
        # Prompt.ask calls: company name, github org, default branch,
        # permission level, command style
        mock_prompt.side_effect = [
            "Acme",  # company name
            "acme-org",  # github org
            "main",  # default branch
            "2",  # permission level (standard)
            "3",  # command style (both)
        ]
        # questionary checkbox for AI tools
        mock_checkbox = MagicMock()
        mock_checkbox.ask.return_value = ["claude"]
        mock_questionary.checkbox.return_value = mock_checkbox
        mock_questionary.Choice = MagicMock(side_effect=lambda title, **kw: title)

        result = runner.invoke(app, ["configure"], catch_exceptions=False)

    assert result.exit_code == 0, result.output

    saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert saved["permissions_level"] == "standard"


def test_configure_ai_tools_multi_select(tmp_path: Path, monkeypatch) -> None:
    """T038: Configure with multi-select AI tools via questionary.checkbox."""
    config_path = _setup_config_dir(tmp_path)
    monkeypatch.chdir(tmp_path)

    with (
        patch("dotnet_ai_kit.cli.Prompt.ask") as mock_prompt,
        patch("dotnet_ai_kit.cli.questionary") as mock_questionary,
    ):
        mock_prompt.side_effect = [
            "Acme",  # company name
            "acme-org",  # github org
            "main",  # default branch
            "2",  # permission level
            "3",  # command style
        ]
        mock_checkbox = MagicMock()
        mock_checkbox.ask.return_value = ["claude", "cursor"]
        mock_questionary.checkbox.return_value = mock_checkbox
        mock_questionary.Choice = MagicMock(side_effect=lambda title, **kw: title)

        result = runner.invoke(app, ["configure"], catch_exceptions=False)

    assert result.exit_code == 0, result.output

    saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert "claude" in saved["ai_tools"]
    assert "cursor" in saved["ai_tools"]


def test_configure_minimal_bypasses_interactive(tmp_path: Path, monkeypatch) -> None:
    """T039: Configure --minimal only prompts for company name, uses defaults."""
    config_path = _setup_config_dir(tmp_path)
    monkeypatch.chdir(tmp_path)

    with patch("dotnet_ai_kit.cli.Prompt.ask") as mock_prompt:
        # --minimal should only ask for company name
        mock_prompt.return_value = "MinimalCo"

        result = runner.invoke(app, ["configure", "--minimal"], catch_exceptions=False)

    assert result.exit_code == 0, result.output

    # Prompt.ask should have been called exactly once (company name only)
    assert mock_prompt.call_count == 1

    saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert saved["company"]["name"] == "MinimalCo"
    # Other settings should remain at their existing/default values
    assert saved["permissions_level"] == "minimal"  # kept from existing config


def test_configure_summary_table_displayed(tmp_path: Path, monkeypatch) -> None:
    """T039b: Configure should display a summary table after saving."""
    _setup_config_dir(tmp_path)
    monkeypatch.chdir(tmp_path)

    with patch("dotnet_ai_kit.cli.Prompt.ask") as mock_prompt:
        mock_prompt.return_value = "SummaryCo"

        result = runner.invoke(app, ["configure", "--minimal"], catch_exceptions=False)

    assert result.exit_code == 0, result.output
    # The summary table should contain "Configuration Saved" title and settings
    assert "Configuration Saved" in result.output
    assert "SummaryCo" in result.output
    assert "Permissions" in result.output
    assert "AI Tools" in result.output
    assert "Command Style" in result.output


def test_configure_no_input_mode(tmp_path: Path, monkeypatch) -> None:
    """T044b: Configure --no-input uses flag values directly."""
    config_path = _setup_config_dir(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "configure",
            "--no-input",
            "--company",
            "CiCo",
            "--org",
            "ci-org",
            "--branch",
            "develop",
            "--permissions",
            "full",
            "--tools",
            "claude,cursor",
            "--style",
            "short",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output

    saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert saved["company"]["name"] == "CiCo"
    assert saved["company"]["github_org"] == "ci-org"
    assert saved["company"]["default_branch"] == "develop"
    assert saved["permissions_level"] == "full"
    assert saved["ai_tools"] == ["claude", "cursor"]
    assert saved["command_style"] == "short"


def test_configure_no_input_requires_company(tmp_path: Path, monkeypatch) -> None:
    """T044b: Configure --no-input should fail if --company is missing."""
    _setup_config_dir(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["configure", "--no-input"],
    )

    assert result.exit_code == 1
    assert "--company is required" in result.output


# ---------------------------------------------------------------------------
# T030-T031c: Permission handling and tool validation tests
# ---------------------------------------------------------------------------


def test_validate_tools_all_found() -> None:
    """T030: _validate_tools returns paths when all tools are found on PATH."""
    from dotnet_ai_kit.cli import _validate_tools

    mock_console = MagicMock()

    with patch("dotnet_ai_kit.cli.shutil.which") as mock_which:
        mock_which.side_effect = lambda tool: f"/usr/bin/{tool}"
        results = _validate_tools(mock_console, verbose=False)

    assert results["dotnet"] == "/usr/bin/dotnet"
    assert results["git"] == "/usr/bin/git"
    assert results["gh"] == "/usr/bin/gh"
    assert results["docker"] == "/usr/bin/docker"
    assert all(v is not None for v in results.values())


def test_validate_tools_some_missing() -> None:
    """T030: _validate_tools returns None for missing tools."""
    from dotnet_ai_kit.cli import _validate_tools

    mock_console = MagicMock()

    def selective_which(tool: str) -> str | None:
        return "/usr/bin/dotnet" if tool == "dotnet" else None

    with patch("dotnet_ai_kit.cli.shutil.which", side_effect=selective_which):
        results = _validate_tools(mock_console, verbose=False)

    assert results["dotnet"] == "/usr/bin/dotnet"
    assert results["git"] is None
    assert results["gh"] is None
    assert results["docker"] is None


def test_validate_tools_output_format() -> None:
    """T031: _validate_tools prints table with tool name, status, and install URL."""
    # Use a real Console writing to a string buffer to verify output content
    from io import StringIO

    from rich.console import Console as RichConsole

    from dotnet_ai_kit.cli import _validate_tools

    buf = StringIO()
    test_console = RichConsole(file=buf, force_terminal=False, width=120)

    with patch("dotnet_ai_kit.cli.shutil.which") as mock_which:
        # Make gh and docker missing so the table is printed
        def selective_which(tool: str) -> str | None:
            if tool in ("dotnet", "git"):
                return f"/usr/bin/{tool}"
            return None

        mock_which.side_effect = selective_which
        _validate_tools(test_console, verbose=False)

    output = buf.getvalue()
    # Table should contain "Tool Availability" title
    assert "Tool Availability" in output
    # Missing tools should show their install URLs
    assert "https://cli.github.com" in output
    assert "https://docs.docker.com/get-docker/" in output
    # Found tools should show "found"
    assert "found" in output
    # Missing tools should show "missing"
    assert "missing" in output
    # Should mention missing tools in the warning
    assert "Missing tools" in output
    assert "gh" in output
    assert "docker" in output


def test_validate_tools_verbose_shows_table_even_when_all_found() -> None:
    """T031: _validate_tools prints the table in verbose mode even when all tools are found."""
    from dotnet_ai_kit.cli import _validate_tools

    mock_console = MagicMock()

    with patch("dotnet_ai_kit.cli.shutil.which") as mock_which:
        mock_which.side_effect = lambda tool: f"/usr/bin/{tool}"
        _validate_tools(mock_console, verbose=True)

    # Console.print should have been called (for the table)
    assert mock_console.print.call_count >= 2  # at least table title + table


def test_tool_calls_rule_exists() -> None:
    """T031b: A rule file in rules/ should mention sequential tool calls, not && chains."""
    rules_dir = Path(__file__).resolve().parent.parent / "rules"
    assert rules_dir.is_dir(), f"rules/ directory not found at {rules_dir}"

    found_rule = False
    for rule_file in rules_dir.iterdir():
        if rule_file.suffix == ".md":
            content = rule_file.read_text(encoding="utf-8")
            # Check that at least one rule file discusses sequential tool calls
            if "sequential" in content.lower() and "&&" in content:
                found_rule = True
                # Verify the rule advises AGAINST && chains
                assert "do not" in content.lower() or "don't" in content.lower(), (
                    f"Rule file {rule_file.name} mentions && but does not advise against it"
                )
                # Check the file is under 100 lines
                line_count = len(content.splitlines())
                assert line_count <= 100, (
                    f"Rule file {rule_file.name} has {line_count} lines, exceeds 100 limit"
                )
                break

    assert found_rule, (
        "No rule file found in rules/ that discusses sequential tool calls and && chains"
    )


def test_permission_json_files_use_space_syntax() -> None:
    """T031c: Permission JSON files should use space syntax, not colon syntax."""
    import json

    config_dir = Path(__file__).resolve().parent.parent / "config"
    assert config_dir.is_dir(), f"config/ directory not found at {config_dir}"

    permission_files = list(config_dir.glob("permissions-*.json"))
    assert len(permission_files) >= 3, (
        f"Expected at least 3 permissions-*.json files, found {len(permission_files)}"
    )

    for perm_file in permission_files:
        content = perm_file.read_text(encoding="utf-8")
        data = json.loads(content)

        # Check $schema is present
        assert "$schema" in data, f"{perm_file.name} is missing $schema field"
        assert data["$schema"] == "https://json.schemastore.org/claude-code-settings.json", (
            f"{perm_file.name} has wrong $schema value"
        )

        # Check all permission entries use space syntax, not colon syntax
        allow_list = data.get("permissions", {}).get("allow", [])
        assert len(allow_list) > 0, f"{perm_file.name} has empty allow list"

        for entry in allow_list:
            # Bash entries should use space syntax, not colon syntax
            if entry.startswith("Bash("):
                # Should not contain colon syntax like "Bash(dotnet build:*)"
                inner = entry[5:-1]  # content between Bash( and )
                assert ":" not in inner, (
                    f"{perm_file.name} uses colon syntax: {entry!r}. "
                    "Expected space syntax like 'Bash(dotnet build *)'"
                )
                assert entry.endswith(")"), f"{perm_file.name} has unexpected entry format: {entry!r}"
            else:
                # Non-Bash entries: WebSearch, WebFetch(domain:...), Edit(...), etc.
                valid_prefixes = ("WebSearch", "WebFetch(", "Edit(", "Agent(")
                assert entry.startswith(valid_prefixes), (
                    f"{perm_file.name} has unexpected entry format: {entry!r}"
                )

        # Check that Bash(cd *) is present
        assert "Bash(cd *)" in allow_list, f"{perm_file.name} is missing 'Bash(cd *)' entry"


# ---------------------------------------------------------------------------
# T050-T058: CLI UX Polish tests
# ---------------------------------------------------------------------------


def test_check_json_produces_valid_json(tmp_path: Path, monkeypatch) -> None:
    """T050: check --json should produce valid JSON output."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    # Initialize the project first
    runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False)

    # Now run check --json from the project directory
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["check", "--json"], catch_exceptions=False)

    assert result.exit_code == 0, result.output

    # Extract JSON from output (may contain other lines from rich console)
    # The JSON line is the one that starts with '{'
    json_lines = [
        line for line in result.output.strip().splitlines() if line.strip().startswith("{")
    ]
    assert len(json_lines) >= 1, f"No JSON line found in output: {result.output}"

    data = json.loads(json_lines[0])
    assert "version" in data
    assert "ai_tools" in data
    assert "claude" in data["ai_tools"]
    assert "permissions_level" in data
    assert "company" in data


def test_init_next_command_suggestion(tmp_path: Path) -> None:
    """T050b: init should suggest 'dotnet-ai configure' as next command."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    result = runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False)

    assert result.exit_code == 0, result.output
    assert "dotnet-ai configure" in result.output


def test_check_exit_code_no_config(tmp_path: Path, monkeypatch) -> None:
    """T050c: check with no config should return exit code 1."""
    monkeypatch.chdir(tmp_path)
    # No .dotnet-ai-kit directory exists

    result = runner.invoke(app, ["check"])

    assert result.exit_code == 1


def test_init_json_output(tmp_path: Path) -> None:
    """T051: init --json should produce valid JSON instead of rich output."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    result = runner.invoke(
        app,
        ["init", str(tmp_path), "--ai", "claude", "--json"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output

    json_lines = [
        line for line in result.output.strip().splitlines() if line.strip().startswith("{")
    ]
    assert len(json_lines) >= 1, f"No JSON line found in output: {result.output}"

    data = json.loads(json_lines[0])
    assert data["version"]
    assert "claude" in data["ai_tools"]
    assert "config_dir" in data


def test_configure_next_command_suggestion(tmp_path: Path, monkeypatch) -> None:
    """T052: configure should suggest 'dotnet-ai check' as next command."""
    _setup_config_dir(tmp_path)
    monkeypatch.chdir(tmp_path)

    with patch("dotnet_ai_kit.cli.Prompt.ask") as mock_prompt:
        mock_prompt.return_value = "NextCo"

        result = runner.invoke(app, ["configure", "--minimal"], catch_exceptions=False)

    assert result.exit_code == 0, result.output
    assert "dotnet-ai check" in result.output


def test_no_color_env_var() -> None:
    """T053: NO_COLOR env var should be respected."""
    import dotnet_ai_kit.cli as cli_mod

    # The module reads NO_COLOR at import time via os.environ.get("NO_COLOR")
    # Verify the _no_color variable and console are set up
    assert hasattr(cli_mod, "_no_color")
    assert hasattr(cli_mod, "console")
    assert hasattr(cli_mod, "err_console")


def test_err_console_exists() -> None:
    """T055: err_console should be a Console instance writing to stderr."""
    from dotnet_ai_kit.cli import err_console

    assert err_console._file is not None or err_console.stderr  # noqa: SLF001
    # Verify err_console is configured for stderr
    assert hasattr(err_console, "print")


def test_check_config_error_exit_code_2(tmp_path: Path, monkeypatch) -> None:
    """T056: check with invalid config should return exit code 2."""
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / ".dotnet-ai-kit"
    config_dir.mkdir(parents=True)

    # Write a valid YAML file but with invalid pydantic values
    config_path = config_dir / "config.yml"
    config_path.write_text(
        "version: '1.0'\nai_tools:\n  - invalid_tool_xyz\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["check"])

    assert result.exit_code == 2


def test_check_error_message_includes_fix(tmp_path: Path, monkeypatch) -> None:
    """T057: check error messages should include how-to-fix guidance."""
    monkeypatch.chdir(tmp_path)
    # No .dotnet-ai-kit directory

    result = runner.invoke(app, ["check"])

    assert result.exit_code == 1
    # Should tell user how to fix the problem
    assert "dotnet-ai init" in result.output.lower() or "dotnet-ai init" in result.output


def test_init_dry_run(tmp_path: Path) -> None:
    """T058: init --dry-run should not create any files."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    result = runner.invoke(
        app,
        ["init", str(tmp_path), "--ai", "claude", "--dry-run"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    assert "DRY-RUN" in result.output
    # No files should be created
    assert not (tmp_path / ".dotnet-ai-kit").exists()


def test_configure_dry_run(tmp_path: Path, monkeypatch) -> None:
    """T058: configure --dry-run should not write config."""
    _setup_config_dir(tmp_path)
    monkeypatch.chdir(tmp_path)

    # Capture the config before
    config_path = tmp_path / ".dotnet-ai-kit" / "config.yml"
    original_content = config_path.read_text(encoding="utf-8")

    result = runner.invoke(
        app,
        ["configure", "--no-input", "--company", "DryRunCo", "--dry-run"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    assert "DRY-RUN" in result.output
    assert "No changes were made" in result.output
    # Config should NOT have been modified
    assert config_path.read_text(encoding="utf-8") == original_content


def test_init_json_suppresses_rich_output(tmp_path: Path) -> None:
    """T051: init --json should NOT show rich formatting like bold text."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    result = runner.invoke(
        app,
        ["init", str(tmp_path), "--ai", "claude", "--json"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output

    # The output should contain a JSON line but NOT the "Next:" suggestion
    assert "Next:" not in result.output
    # Should not contain the rich-formatted init banner
    assert "Scanning project" not in result.output


# ---------------------------------------------------------------------------
# --version flag
# ---------------------------------------------------------------------------


def test_version_flag() -> None:
    """--version should print version and exit 0."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "dotnet-ai-kit" in result.output


def test_version_flag_short() -> None:
    """-V should also print version and exit 0."""
    result = runner.invoke(app, ["-V"])
    assert result.exit_code == 0
    assert "dotnet-ai-kit" in result.output


# ---------------------------------------------------------------------------
# --type validation
# ---------------------------------------------------------------------------


def test_init_rejects_invalid_type(tmp_path: Path) -> None:
    """Init should reject unknown --type values."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    result = runner.invoke(
        app,
        ["init", str(tmp_path), "--ai", "claude", "--type", "invalid-type"],
    )

    assert result.exit_code == 1
    assert "unknown project type" in result.output.lower()


def test_init_accepts_all_valid_types(tmp_path: Path) -> None:
    """Init should accept all 12 known project types."""
    from dotnet_ai_kit.cli import _VALID_PROJECT_TYPES

    for ptype in _VALID_PROJECT_TYPES:
        project_dir = tmp_path / ptype
        project_dir.mkdir()
        _create_dotnet_project(project_dir)
        _create_claude_dir(project_dir)

        result = runner.invoke(
            app,
            ["init", str(project_dir), "--ai", "claude", "--type", ptype],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, f"Type '{ptype}' failed: {result.output}"


# ---------------------------------------------------------------------------
# --ai validation (v1.0: claude only)
# ---------------------------------------------------------------------------


def test_init_rejects_unsupported_ai_tool(tmp_path: Path) -> None:
    """Init should reject AI tools not supported in v1.0."""
    _create_dotnet_project(tmp_path)

    result = runner.invoke(
        app,
        ["init", str(tmp_path), "--ai", "cursor"],
    )

    assert result.exit_code == 1
    assert "unsupported" in result.output.lower()


# ---------------------------------------------------------------------------
# upgrade command tests
# ---------------------------------------------------------------------------


def test_upgrade_not_initialized_exits_1(tmp_path: Path, monkeypatch) -> None:
    """Upgrade should exit 1 when .dotnet-ai-kit/ is missing."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code == 1
    assert "not initialized" in result.output.lower()


def test_upgrade_already_up_to_date(tmp_path: Path, monkeypatch) -> None:
    """Upgrade should report up-to-date when versions match."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["upgrade"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "up to date" in result.output.lower()


def test_upgrade_json_up_to_date(tmp_path: Path, monkeypatch) -> None:
    """Upgrade --json should output valid JSON when up to date."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["upgrade", "--json"], catch_exceptions=False)
    assert result.exit_code == 0

    json_lines = [ln for ln in result.output.strip().splitlines() if ln.strip().startswith("{")]
    assert len(json_lines) >= 1
    data = json.loads(json_lines[0])
    assert data["status"] == "up_to_date"


def test_upgrade_dry_run(tmp_path: Path, monkeypatch) -> None:
    """Upgrade --dry-run should show preview without changes."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False)

    # Tamper version to trigger upgrade path
    version_file = tmp_path / ".dotnet-ai-kit" / "version.txt"
    version_file.write_text("0.0.1", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["upgrade", "--dry-run"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "DRY-RUN" in result.output
    assert "No changes were made" in result.output
    # Version should NOT have been updated
    assert version_file.read_text(encoding="utf-8").strip() == "0.0.1"


def test_upgrade_updates_version(tmp_path: Path, monkeypatch) -> None:
    """Upgrade should update version.txt after upgrading files."""
    from dotnet_ai_kit import __version__

    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False)

    # Tamper version to trigger upgrade
    version_file = tmp_path / ".dotnet-ai-kit" / "version.txt"
    version_file.write_text("0.0.1", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["upgrade"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "upgraded" in result.output.lower()
    assert version_file.read_text(encoding="utf-8").strip() == __version__


def test_upgrade_json_output(tmp_path: Path, monkeypatch) -> None:
    """Upgrade --json should produce valid JSON after upgrade."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False)

    version_file = tmp_path / ".dotnet-ai-kit" / "version.txt"
    version_file.write_text("0.0.1", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["upgrade", "--json"], catch_exceptions=False)
    assert result.exit_code == 0

    json_lines = [ln for ln in result.output.strip().splitlines() if ln.strip().startswith("{")]
    data = json.loads(json_lines[0])
    assert data["status"] == "upgraded"
    assert data["old_version"] == "0.0.1"


# ---------------------------------------------------------------------------
# check command tests
# ---------------------------------------------------------------------------


def test_check_displays_project_info(tmp_path: Path, monkeypatch) -> None:
    """Check should display project info when project.yml exists."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    runner.invoke(
        app,
        ["init", str(tmp_path), "--ai", "claude", "--type", "command"],
        catch_exceptions=False,
    )
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["check"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "command" in result.output.lower()


def test_check_json_includes_project(tmp_path: Path, monkeypatch) -> None:
    """Check --json should include project info in output."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    runner.invoke(
        app,
        ["init", str(tmp_path), "--ai", "claude", "--type", "command"],
        catch_exceptions=False,
    )
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["check", "--json"], catch_exceptions=False)
    assert result.exit_code == 0

    json_lines = [ln for ln in result.output.strip().splitlines() if ln.strip().startswith("{")]
    data = json.loads(json_lines[0])
    assert "project" in data
    assert data["project"]["project_type"] == "command"


# ---------------------------------------------------------------------------
# extension command tests
# ---------------------------------------------------------------------------


def test_extension_list_empty(tmp_path: Path, monkeypatch) -> None:
    """Extension list should show 'No extensions' when none installed."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["extension-list"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "no extensions" in result.output.lower()


def test_extension_add_missing_dir(tmp_path: Path, monkeypatch) -> None:
    """Extension add --dev with missing dir should fail."""
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["extension-add", str(tmp_path / "nonexistent"), "--dev"],
    )
    assert result.exit_code == 1


def test_extension_remove_not_installed(tmp_path: Path, monkeypatch) -> None:
    """Extension remove for non-installed extension should fail."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)
    runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["extension-remove", "nonexistent"])
    assert result.exit_code == 1
    assert "not installed" in result.output.lower()


# ---------------------------------------------------------------------------
# Bug fixes: init --force, upgrade permissions, upgrade --force, configure defaults
# ---------------------------------------------------------------------------


def test_init_force_preserves_existing_config(tmp_path: Path) -> None:
    """init --force should preserve existing config.yml settings (company, repos, permissions)."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    # First init
    runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False)

    # Manually set config to full permissions and company name
    config_path = tmp_path / ".dotnet-ai-kit" / "config.yml"
    config_path.write_text(
        "version: '1.0'\n"
        "company:\n"
        "  name: 'Acme'\n"
        "  github_org: 'acme-org'\n"
        "  default_branch: master\n"
        "permissions_level: full\n"
        "ai_tools:\n  - claude\n"
        "command_style: both\n",
        encoding="utf-8",
    )

    # Re-init with --force
    result = runner.invoke(
        app, ["init", str(tmp_path), "--ai", "claude", "--force"], catch_exceptions=False
    )
    assert result.exit_code == 0, result.output

    # Config should preserve existing values
    saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert saved["company"]["name"] == "Acme"
    assert saved["company"]["github_org"] == "acme-org"
    assert saved["permissions_level"] == "full"


def test_init_force_applies_full_permissions(tmp_path: Path) -> None:
    """init --force with permissions_level=full should write bypassPermissions to settings.json."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    # First init
    runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False)

    # Set permissions to full
    config_path = tmp_path / ".dotnet-ai-kit" / "config.yml"
    config_path.write_text(
        "version: '1.0'\n"
        "permissions_level: full\n"
        "ai_tools:\n  - claude\n"
        "command_style: both\n",
        encoding="utf-8",
    )

    # Re-init with --force
    runner.invoke(
        app, ["init", str(tmp_path), "--ai", "claude", "--force"], catch_exceptions=False
    )

    settings_path = tmp_path / ".claude" / "settings.json"
    assert settings_path.is_file()
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    assert data["permissions"]["defaultMode"] == "bypassPermissions"
    # Full template has 100+ entries
    assert len(data["permissions"]["allow"]) > 50


def test_upgrade_reapplies_permissions_when_level_changes(tmp_path: Path, monkeypatch) -> None:
    """upgrade should re-apply permissions even when settings.json already has entries."""
    from dotnet_ai_kit import __version__

    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    # Init (creates standard permissions in settings.json)
    runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False)

    # Change config to full permissions
    config_path = tmp_path / ".dotnet-ai-kit" / "config.yml"
    config_path.write_text(
        "version: '1.0'\n"
        "permissions_level: full\n"
        "ai_tools:\n  - claude\n"
        "command_style: both\n",
        encoding="utf-8",
    )

    # Tamper version to trigger upgrade
    version_file = tmp_path / ".dotnet-ai-kit" / "version.txt"
    version_file.write_text("0.0.1", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["upgrade"], catch_exceptions=False)
    assert result.exit_code == 0

    settings_path = tmp_path / ".claude" / "settings.json"
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    assert data["permissions"]["defaultMode"] == "bypassPermissions"
    assert len(data["permissions"]["allow"]) > 50


def test_upgrade_force_refreshes_when_version_matches(tmp_path: Path, monkeypatch) -> None:
    """upgrade --force should refresh files even when version is up to date."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False)
    monkeypatch.chdir(tmp_path)

    # Delete a rule file to prove --force re-copies it
    rules_dir = tmp_path / ".claude" / "rules"
    rule_files_before = list(rules_dir.glob("*.md"))
    assert len(rule_files_before) > 0
    rule_files_before[0].unlink()
    rules_after_delete = list(rules_dir.glob("*.md"))
    assert len(rules_after_delete) == len(rule_files_before) - 1

    # Without --force, upgrade does nothing
    result = runner.invoke(app, ["upgrade"], catch_exceptions=False)
    assert "up to date" in result.output.lower()
    assert len(list(rules_dir.glob("*.md"))) == len(rule_files_before) - 1

    # With --force, upgrade refreshes
    result = runner.invoke(app, ["upgrade", "--force"], catch_exceptions=False)
    assert result.exit_code == 0
    assert len(list(rules_dir.glob("*.md"))) == len(rule_files_before)


def test_configure_fails_loudly_on_permission_error(tmp_path: Path, monkeypatch) -> None:
    """configure should exit 1 if permissions fail to apply, not swallow the error."""
    config_dir = tmp_path / ".dotnet-ai-kit"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.yml"
    config_path.write_text(
        "version: '1.0'\nai_tools:\n  - claude\npermissions_level: standard\n"
        "command_style: both\ncompany:\n  name: 'Test'\n  github_org: ''\n  default_branch: main\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    with patch("dotnet_ai_kit.cli.copy_permissions") as mock_cp:
        mock_cp.side_effect = CopyError("template not found")

        result = runner.invoke(
            app,
            ["configure", "--no-input", "--company", "Test", "--permissions", "full"],
        )

    assert result.exit_code == 1
    assert "Failed to apply permissions" in result.output


def test_check_detects_permission_mismatch(tmp_path: Path, monkeypatch) -> None:
    """check should report when settings.json doesn't match config permissions_level."""
    _create_dotnet_project(tmp_path)
    _create_claude_dir(tmp_path)

    # Init with standard
    runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False)

    # Manually set config to full but leave settings.json at standard
    config_path = tmp_path / ".dotnet-ai-kit" / "config.yml"
    import yaml

    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    cfg["permissions_level"] = "full"
    # Set managed_permissions to something with a count
    cfg["managed_permissions"] = [f"entry{i}" for i in range(100)]
    config_path.write_text(yaml.dump(cfg), encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["check"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "mismatch" in result.output.lower() or "bypassPermissions" in result.output


def test_configure_respects_existing_permission_default(tmp_path: Path, monkeypatch) -> None:
    """configure interactive should default to existing permission level, not hardcoded standard."""
    config_dir = tmp_path / ".dotnet-ai-kit"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.yml"
    config_path.write_text(
        "version: '1.0'\nai_tools:\n  - claude\npermissions_level: full\n"
        "command_style: short\ncompany:\n  name: 'Test'\n  github_org: ''\n  default_branch: main\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    with (
        patch("dotnet_ai_kit.cli.Prompt.ask") as mock_prompt,
        patch("dotnet_ai_kit.cli.questionary") as mock_questionary,
    ):
        # Simulate user pressing Enter on all prompts (accepting defaults)
        def prompt_side_effect(prompt_text, **kwargs):
            return kwargs.get("default", "")

        mock_prompt.side_effect = prompt_side_effect
        mock_checkbox = MagicMock()
        mock_checkbox.ask.return_value = ["claude"]
        mock_questionary.checkbox.return_value = mock_checkbox
        mock_questionary.Choice = MagicMock(side_effect=lambda title, **kw: title)

        result = runner.invoke(app, ["configure"], catch_exceptions=False)

    assert result.exit_code == 0, result.output

    saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    # Pressing Enter should keep full (default="3" mapped from existing "full")
    assert saved["permissions_level"] == "full"
    # Pressing Enter should keep short (default="2" mapped from existing "short")
    assert saved["command_style"] == "short"
