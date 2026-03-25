"""CLI commands for dotnet-ai-kit.

Provides the `dotnet-ai` command-line interface using typer with rich
formatting for terminal output.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Optional

import questionary
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from dotnet_ai_kit import __version__
from dotnet_ai_kit.agents import SUPPORTED_AI_TOOLS, detect_ai_tools, get_agent_config
from dotnet_ai_kit.config import (
    get_config_dir,
    load_config,
    load_project,
    save_config,
    save_project,
)
from dotnet_ai_kit.copier import (
    CopyError,
    copy_agents,
    copy_commands,
    copy_commands_codex,
    copy_commands_cursor,
    copy_permissions,
    copy_rules,
    copy_skills,
    verify_permissions,
)
from dotnet_ai_kit.detection import describe_architecture
from dotnet_ai_kit.extensions import (
    ExtensionError,
    install_extension,
    list_extensions,
    remove_extension,
)
from dotnet_ai_kit.models import DetectedProject, DotnetAiConfig

# All valid --type values for init
_VALID_PROJECT_TYPES = {
    "command",
    "query-sql",
    "query-cosmos",
    "processor",
    "gateway",
    "controlpanel",
    "hybrid",
    "vsa",
    "clean-arch",
    "ddd",
    "modular-monolith",
    "generic",
}


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"dotnet-ai-kit {__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="dotnet-ai",
    help="AI dev tool plugin for the full .NET development lifecycle.",
    add_completion=False,
)


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """AI dev tool plugin for the full .NET development lifecycle."""


# T053 - NO_COLOR support (clig.dev best practice)
_no_color = os.environ.get("NO_COLOR") is not None
console = Console(no_color=_no_color)

# T055 - stderr console for error/warning output
err_console = Console(stderr=True, no_color=_no_color)


def _get_package_dir() -> Path:
    """Get the directory containing bundled assets (commands, rules, etc.).

    Checks two locations:
    1. Wheel install: assets are at {package}/bundled/
    2. Dev mode: assets are at repo root (3 levels up from src/dotnet_ai_kit/)
    """
    pkg_dir = Path(__file__).resolve().parent
    bundled = pkg_dir / "bundled"
    if bundled.is_dir():
        return bundled
    # Dev mode: repo root is 3 levels up from src/dotnet_ai_kit/cli.py
    return pkg_dir.parent.parent


def _find_commands_source() -> Path:
    """Find the commands source directory in the package."""
    pkg = _get_package_dir()
    candidates = [
        pkg / "commands",
        pkg / "templates" / "commands",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return pkg / "commands"


def _find_rules_source() -> Path:
    """Find the rules source directory in the package."""
    pkg = _get_package_dir()
    return pkg / "rules"


def _find_skills_source() -> Path:
    """Find the skills source directory in the package."""
    pkg = _get_package_dir()
    return pkg / "skills"


def _find_agents_source() -> Path:
    """Find the agents source directory in the package."""
    pkg = _get_package_dir()
    return pkg / "agents"


def _verbose_log(verbose: bool, message: str) -> None:
    """Print a verbose log message if verbose mode is enabled."""
    if verbose:
        console.print(f"  [dim]{message}[/dim]")


# Tool install URLs for pre-flight validation
_TOOL_INSTALL_URLS: dict[str, str] = {
    "dotnet": "https://dot.net/download",
    "git": "https://git-scm.com/downloads",
    "gh": "https://cli.github.com",
    "docker": "https://docs.docker.com/get-docker/",
}


def _validate_tools(
    target_console: Console,
    verbose: bool = False,
) -> dict[str, str | None]:
    """Check PATH for required and optional development tools.

    Returns a dict mapping tool name to its resolved path (or None if missing).
    Prints warnings for any missing tools with their install URLs.
    """
    tools = ["dotnet", "git", "gh", "docker"]
    results: dict[str, str | None] = {}

    table = Table(title="Tool Availability")
    table.add_column("Tool", style="bold")
    table.add_column("Status")
    table.add_column("Path / Install URL")

    for tool in tools:
        resolved = shutil.which(tool)
        results[tool] = resolved

        if resolved:
            table.add_row(tool, "[green]found[/green]", resolved)
        else:
            install_url = _TOOL_INSTALL_URLS.get(tool, "")
            table.add_row(
                tool,
                "[yellow]missing[/yellow]",
                install_url,
            )

    if verbose or any(v is None for v in results.values()):
        target_console.print()
        target_console.print(table)

    missing = [t for t, p in results.items() if p is None]
    if missing:
        target_console.print(
            f"\n[yellow]Missing tools: {', '.join(missing)}. "
            "Some features may not work until they are installed.[/yellow]"
        )

    return results


# ---------------------------------------------------------------------------
# init command
# ---------------------------------------------------------------------------


@app.command()
def init(
    path: Path = typer.Argument(
        Path("."),
        help="Target directory (default: current directory).",
    ),
    ai: Optional[list[str]] = typer.Option(
        None,
        "--ai",
        help="AI tool to configure (claude). Repeatable.",
    ),
    project_type: Optional[str] = typer.Option(
        None,
        "--type",
        help="Override detected project type.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Reinitialize even if already configured.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output JSON.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Preview without making changes.",
    ),
) -> None:
    """Initialize dotnet-ai-kit in a .NET project directory."""
    target = path.resolve()

    # Validate --type value
    if project_type and project_type.lower() not in _VALID_PROJECT_TYPES:
        err_console.print(
            f"[red]Unknown project type '{project_type}'. "
            f"Valid types: {', '.join(sorted(_VALID_PROJECT_TYPES))}[/red]"
        )
        raise typer.Exit(code=1)

    # Validate --ai values (v1.0: claude only)
    if ai:
        unsupported = [t for t in ai if t.lower() not in SUPPORTED_AI_TOOLS]
        if unsupported:
            err_console.print(
                f"[red]Unsupported AI tool(s): {', '.join(unsupported)}. "
                f"v1.0 supports: {', '.join(sorted(SUPPORTED_AI_TOOLS))}.[/red]"
            )
            raise typer.Exit(code=1)

    if not json_output:
        if dry_run:
            console.print("\n[bold][DRY-RUN] dotnet-ai-kit init preview[/bold]\n")
        else:
            console.print(f"\n[bold]dotnet-ai-kit v{__version__}[/bold]\n")

    # Check if already initialized
    config_dir = get_config_dir(target)
    if config_dir.is_dir() and not force:
        err_console.print(
            "[yellow]dotnet-ai-kit is already initialized in this directory.\n"
            "To update commands/rules, run: dotnet-ai upgrade\n"
            "To reinitialize from scratch, run: dotnet-ai init --force[/yellow]"
        )
        raise typer.Exit(code=1)

    # Step 1: Project type (AI detection is done via /dotnet-ai.detect command)
    detected = None
    if project_type:
        # --type flag: create a basic DetectedProject
        microservice_types = {
            "command",
            "query-sql",
            "query-cosmos",
            "processor",
            "gateway",
            "controlpanel",
            "hybrid",
        }
        mode = "microservice" if project_type in microservice_types else "generic"
        detected = DetectedProject(
            mode=mode,
            project_type=project_type,
            architecture=describe_architecture(mode, project_type),
        )
        _verbose_log(verbose, f"Project type set to: {project_type}")
    elif not json_output:
        console.print(
            "  [dim]Project detection skipped. "
            "Run /dotnet-ai.detect to classify your project.[/dim]"
        )

    # Step 2: Detect or configure AI tools
    if ai:
        ai_tools = [t.lower() for t in ai]
    else:
        ai_tools = detect_ai_tools(target)
        if not ai_tools:
            err_console.print(
                "\n[yellow]No AI tool detected. Use --ai flag "
                "(e.g., --ai claude). "
                "Example: dotnet-ai init --ai claude[/yellow]"
            )
            raise typer.Exit(code=3)

    _verbose_log(verbose, f"AI tools: {', '.join(ai_tools)}")

    # T058 - Dry run: show what WOULD be done, skip file operations
    if dry_run:
        console.print("[bold]Would perform the following actions:[/bold]")
        console.print(f"  Create directory: {config_dir.relative_to(target)}")
        console.print(f"  Create directory: {config_dir.relative_to(target)}/memory")
        console.print(f"  Create directory: {config_dir.relative_to(target)}/features")
        console.print(f"  Create config: {config_dir.relative_to(target)}/config.yml")
        if detected:
            console.print(f"  Create project: {config_dir.relative_to(target)}/project.yml")
        console.print(f"  Create version: {config_dir.relative_to(target)}/version.txt")
        console.print(f"  AI tools: {', '.join(ai_tools)}")
        console.print("\n[dim]No changes were made (dry run).[/dim]")
        return

    # Step 3: Create config directory
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "memory").mkdir(parents=True, exist_ok=True)
    (config_dir / "features").mkdir(parents=True, exist_ok=True)

    # Step 4: Save config (preserve existing config on --force)
    config_path = config_dir / "config.yml"
    if force and config_path.is_file():
        try:
            config = load_config(config_path)
            if ai:
                config.ai_tools = ai_tools
            _verbose_log(verbose, "Loaded existing config (--force preserves settings).")
        except (FileNotFoundError, ValueError):
            config = DotnetAiConfig(ai_tools=ai_tools)
    else:
        config = DotnetAiConfig(ai_tools=ai_tools)
    save_config(config, config_path)
    if not json_output:
        console.print(f"  Created: {config_path.relative_to(target)}")

    # Step 5: Save project detection results
    if detected:
        project_path = config_dir / "project.yml"
        save_project(detected, project_path)
        if not json_output:
            console.print(f"  Created: {project_path.relative_to(target)}")

    # Step 6: Write version file
    version_path = config_dir / "version.txt"
    version_path.write_text(__version__, encoding="utf-8")

    # Step 7: Copy commands, rules, skills, and agents for each AI tool
    commands_source = _find_commands_source()
    rules_source = _find_rules_source()
    skills_source = _find_skills_source()
    agents_source = _find_agents_source()

    total_cmds = 0
    total_rules = 0
    total_skills = 0
    total_agents = 0

    for tool_name in ai_tools:
        try:
            tool_config = get_agent_config(tool_name)
        except ValueError:
            if not json_output:
                err_console.print(f"  [yellow]Skipping unknown tool: {tool_name}[/yellow]")
            continue

        tool_display = tool_config.get("name", tool_name)
        if not json_output:
            console.print(f"\n[bold]Initializing for {tool_display}...[/bold]")

        cmd_count = 0
        rule_count = 0
        skill_count = 0
        agent_count = 0

        if tool_name == "cursor":
            cmd_count = copy_commands_cursor(commands_source, target, tool_config, rules_source)
        elif tool_name == "codex":
            cmd_count = copy_commands_codex(commands_source, target, tool_config)
        else:
            cmd_count = copy_commands(commands_source, target, tool_config, config)
            rule_count = copy_rules(rules_source, target, tool_config)

        # Copy skills and agents for all tools
        if skills_source.is_dir():
            skill_count = copy_skills(skills_source, target, tool_config)
        if agents_source.is_dir():
            agent_count = copy_agents(agents_source, target, tool_config)

        total_cmds += cmd_count
        total_rules += rule_count
        total_skills += skill_count
        total_agents += agent_count

        if not json_output:
            if cmd_count:
                console.print(
                    f"  Copied: {cmd_count} commands -> "
                    f"{tool_config.get('commands_dir') or tool_config.get('rules_dir', '')}"
                )
            if rule_count:
                console.print(f"  Copied: {rule_count} rules -> {tool_config.get('rules_dir', '')}")
            if skill_count and tool_config.get("skills_dir"):
                console.print(f"  Copied: {skill_count} skills -> {tool_config['skills_dir']}")
            if agent_count and tool_config.get("agents_dir"):
                console.print(f"  Copied: {agent_count} agents -> {tool_config['agents_dir']}")

    # Step 8: Apply permissions to .claude/settings.json
    try:
        if config.permissions_level == "full" and not json_output:
            console.print(
                "\n[yellow bold]Warning:[/yellow bold] Full permission mode enables "
                "bypassPermissions — the AI assistant will execute all operations "
                "without prompting. Only use in trusted environments.\n"
            )
        perm_result = copy_permissions(target, config, _get_package_dir())
        save_config(config, config_dir / "config.yml")
        if not json_output and perm_result["changed"]:
            console.print(
                f"  Permissions: {perm_result['entries_count']} rules applied "
                f"(mode: {perm_result['mode']}) -> {perm_result['settings_path']}"
            )
    except CopyError as exc:
        err_console.print(
            f"[red bold]Error:[/red bold] Failed to apply permissions: {exc}\n"
            "Run 'dotnet-ai configure' to set permissions after init."
        )
        raise typer.Exit(code=1) from exc

    # Step 9: Validate development tools
    if not json_output:
        _validate_tools(console, verbose=verbose)

    # T051 - JSON output mode
    if json_output:
        data: dict = {
            "version": __version__,
            "ai_tools": ai_tools,
            "commands_copied": total_cmds,
            "rules_copied": total_rules,
            "skills_copied": total_skills,
            "agents_copied": total_agents,
            "config_dir": str(config_dir),
        }
        if detected:
            data["project"] = {
                "project_type": detected.project_type,
                "dotnet_version": detected.dotnet_version or "unknown",
                "architecture": detected.architecture,
                "mode": detected.mode,
            }
        print(json.dumps(data))
        return

    # Summary
    console.print(f"\n[green bold]dotnet-ai-kit initialized for {', '.join(ai_tools)}[/green bold]")
    # T052 - Next-command suggestion
    console.print("\nNext: Run [bold]dotnet-ai configure[/bold] to customize settings.\n")


# ---------------------------------------------------------------------------
# check command
# ---------------------------------------------------------------------------


@app.command()
def check(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output JSON.",
    ),
) -> None:
    """Report the current state of dotnet-ai-kit in the project."""
    target = Path(".").resolve()

    if not json_output:
        console.print(f"\n[bold]dotnet-ai-kit v{__version__}[/bold]\n")

    config_dir = get_config_dir(target)
    if not config_dir.is_dir():
        # T057 - Improved error message with how-to-fix
        err_console.print(
            "[yellow]dotnet-ai-kit is not initialized in this directory. "
            "Run 'dotnet-ai init' first to set up the project.[/yellow]"
        )
        raise typer.Exit(code=1)

    # Load config (T056 - exit code 2 for config errors)
    config_path = config_dir / "config.yml"
    try:
        config = load_config(config_path)
    except FileNotFoundError as exc:
        err_console.print(
            f"[red]Configuration file not found at {config_path}. "
            "Run 'dotnet-ai init' first to set up the project.[/red]"
        )
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        err_console.print(
            f"[red]Invalid configuration: {exc}. "
            "Run 'dotnet-ai configure --reset' to fix the configuration.[/red]"
        )
        raise typer.Exit(code=2) from exc

    # Load project info
    project_path = config_dir / "project.yml"
    detected = None
    try:
        detected = load_project(project_path)
    except (FileNotFoundError, ValueError):
        _verbose_log(verbose, "No project.yml found.")

    # T051 - JSON output mode
    if json_output:
        data: dict = {
            "version": __version__,
            "ai_tools": config.ai_tools,
            "permissions_level": config.permissions_level,
            "command_style": config.command_style,
            "company": {
                "name": config.company.name,
                "github_org": config.company.github_org,
                "default_branch": config.company.default_branch,
            },
        }
        if detected:
            data["project"] = {
                "project_type": detected.project_type,
                "dotnet_version": detected.dotnet_version or "unknown",
                "architecture": detected.architecture,
                "mode": detected.mode,
            }
        # Tool status
        tools_status = {}
        for tool_name in config.ai_tools:
            try:
                tool_config = get_agent_config(tool_name)
            except ValueError:
                tools_status[tool_name] = {"status": "unknown"}
                continue

            cmd_dir_rel = tool_config.get("commands_dir")
            rules_dir_rel = tool_config.get("rules_dir")
            cmd_count = 0
            rule_count = 0
            if cmd_dir_rel:
                cmd_dir = target / cmd_dir_rel
                if cmd_dir.is_dir():
                    cmd_count = len(list(cmd_dir.iterdir()))
            if rules_dir_rel:
                rules_dir = target / rules_dir_rel
                if rules_dir.is_dir():
                    rule_count = len(list(rules_dir.iterdir()))
            tools_status[tool_name] = {
                "status": "configured" if (cmd_count + rule_count) > 0 else "empty",
                "commands": cmd_count,
                "rules": rule_count,
            }
        data["tools"] = tools_status

        print(json.dumps(data))
        return

    # Project info
    if detected:
        console.print(f"Project Type: {detected.project_type.title()}")
        console.print(f"Mode: {detected.mode.title()} ({detected.architecture})")
        console.print(f".NET: {detected.dotnet_version or 'unknown'}")
    console.print()

    # AI Tools status
    table = Table(title="AI Tools")
    table.add_column("Tool", style="bold")
    table.add_column("Status")
    table.add_column("Commands")
    table.add_column("Rules")

    for tool_name in config.ai_tools:
        try:
            tool_config = get_agent_config(tool_name)
        except ValueError:
            table.add_row(tool_name, "[red]unknown[/red]", "-", "-")
            continue

        display = tool_config.get("name", tool_name)
        cmd_dir_rel = tool_config.get("commands_dir")
        rules_dir_rel = tool_config.get("rules_dir")

        cmd_count = 0
        rule_count = 0

        if cmd_dir_rel:
            cmd_dir = target / cmd_dir_rel
            if cmd_dir.is_dir():
                cmd_count = len(list(cmd_dir.iterdir()))

        if rules_dir_rel:
            rules_dir = target / rules_dir_rel
            if rules_dir.is_dir():
                rule_count = len(list(rules_dir.iterdir()))

        is_configured = (cmd_count + rule_count) > 0
        status = "[green]configured[/green]" if is_configured else "[yellow]empty[/yellow]"
        table.add_row(display, status, str(cmd_count), str(rule_count))

    console.print(table)
    console.print()

    # Extensions
    extensions = list_extensions(target)
    if extensions:
        ext_table = Table(title="Extensions")
        ext_table.add_column("Extension", style="bold")
        ext_table.add_column("Version")
        ext_table.add_column("Commands")

        for ext in extensions:
            ext_table.add_row(
                ext.get("id", "?"),
                ext.get("version", "?"),
                str(len(ext.get("commands", []))),
            )
        console.print(ext_table)
        console.print()

    # Config status
    config_panel_lines = []
    if config.company.name:
        config_panel_lines.append(f"  [green]Company:[/green] {config.company.name}")
    else:
        config_panel_lines.append("  [yellow]Company:[/yellow] not set")

    if config.company.github_org:
        config_panel_lines.append(f"  [green]GitHub Org:[/green] {config.company.github_org}")
    else:
        config_panel_lines.append("  [dim]GitHub Org:[/dim] not set")

    repos_configured = sum(
        1
        for v in [
            config.repos.command,
            config.repos.query,
            config.repos.processor,
            config.repos.gateway,
            config.repos.controlpanel,
        ]
        if v
    )
    config_panel_lines.append(f"  Repos: {repos_configured} of 5 configured")
    config_panel_lines.append(f"  Permissions: {config.permissions_level}")

    console.print(Panel("\n".join(config_panel_lines), title="Config"))
    console.print()

    # Permission consistency check
    settings_path = target / ".claude" / "settings.json"
    if settings_path.is_file() and config.permissions_level:
        expected_count = len(config.managed_permissions) if config.managed_permissions else 0
        if expected_count > 0:
            verify_result = verify_permissions(
                settings_path, config.permissions_level, expected_count
            )
            if not verify_result["ok"]:
                err_console.print(
                    f"[red bold]Permission mismatch:[/red bold] {verify_result['reason']}\n"
                    f"  Config says: {config.permissions_level}\n"
                    f"  Expected: {verify_result['expected']}\n"
                    f"  Actual:   {verify_result['actual']}\n"
                    "  Fix: Run 'dotnet-ai upgrade --force' or 'dotnet-ai configure'"
                )
            elif verbose:
                console.print(
                    f"  [green]Permissions OK:[/green] {verify_result['actual']}"
                )
    elif not settings_path.is_file() and config.permissions_level:
        err_console.print(
            "[yellow]settings.json not found — permissions not applied.\n"
            "  Fix: Run 'dotnet-ai upgrade --force'[/yellow]"
        )

    # Version info
    version_path = config_dir / "version.txt"
    if version_path.is_file():
        installed_version = version_path.read_text(encoding="utf-8").strip()
        if installed_version != __version__:
            err_console.print(
                f"[yellow]Version mismatch: installed={installed_version}, "
                f"CLI={__version__}. Run 'dotnet-ai upgrade' to update "
                f"commands and rules to the latest version.[/yellow]"
            )
        else:
            _verbose_log(verbose, f"Version: {__version__} (up to date)")


# ---------------------------------------------------------------------------
# upgrade command
# ---------------------------------------------------------------------------


@app.command()
def upgrade(
    force: bool = typer.Option(
        False,
        "--force",
        help="Force upgrade even if version is up to date.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output JSON.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Preview without making changes.",
    ),
) -> None:
    """Upgrade command and rule files to the latest CLI version."""
    target = Path(".").resolve()

    if not json_output:
        if dry_run:
            console.print("\n[bold][DRY-RUN] dotnet-ai-kit upgrade preview[/bold]\n")
        else:
            console.print(f"\n[bold]dotnet-ai-kit v{__version__}[/bold]\n")

    config_dir = get_config_dir(target)
    if not config_dir.is_dir():
        # T057 - Improved error message
        err_console.print(
            "[yellow]dotnet-ai-kit is not initialized. "
            "Run 'dotnet-ai init' first to set up the project.[/yellow]"
        )
        raise typer.Exit(code=1)

    # Compare versions
    version_path = config_dir / "version.txt"
    old_version = ""
    if version_path.is_file():
        old_version = version_path.read_text(encoding="utf-8").strip()

    if old_version == __version__ and not force:
        if json_output:
            print(json.dumps({"status": "up_to_date", "version": __version__}))
        else:
            console.print("[green]Already up to date.[/green]\n")
        return

    if not json_output:
        console.print(f"Upgrading from {old_version or 'unknown'} to {__version__}...")

    # Load config (T056 - exit code 2 for config errors)
    config_path = config_dir / "config.yml"
    try:
        config = load_config(config_path)
    except FileNotFoundError as exc:
        err_console.print(
            f"[red]Configuration file not found at {config_path}. "
            "Run 'dotnet-ai init' first to set up the project.[/red]"
        )
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        err_console.print(
            f"[red]Invalid configuration: {exc}. "
            "Run 'dotnet-ai configure --reset' to fix the configuration.[/red]"
        )
        raise typer.Exit(code=2) from exc

    commands_source = _find_commands_source()
    rules_source = _find_rules_source()
    skills_source = _find_skills_source()
    agents_source = _find_agents_source()

    # T058 - Dry run: show what WOULD be done
    if dry_run:
        console.print("[bold]Would perform the following actions:[/bold]")
        console.print(f"  Upgrade from {old_version or 'unknown'} to {__version__}")
        for tool_name in config.ai_tools:
            try:
                tool_config = get_agent_config(tool_name)
            except ValueError:
                continue
            tool_display = tool_config.get("name", tool_name)
            cmd_dir_rel = tool_config.get("commands_dir")
            rules_dir_rel = tool_config.get("rules_dir")
            skills_dir_rel = tool_config.get("skills_dir")
            agents_dir_rel = tool_config.get("agents_dir")
            if cmd_dir_rel:
                console.print(f"  Backup and update: {cmd_dir_rel}")
            if rules_dir_rel:
                console.print(f"  Backup and update: {rules_dir_rel}")
            if skills_dir_rel:
                console.print(f"  Update: {skills_dir_rel}")
            if agents_dir_rel:
                console.print(f"  Update: {agents_dir_rel}")
        console.print(f"  Update version file to {__version__}")
        console.print("\n[dim]No changes were made (dry run).[/dim]")
        return

    total_cmds = 0
    total_rules = 0
    total_skills = 0
    total_agents = 0

    for tool_name in config.ai_tools:
        try:
            tool_config = get_agent_config(tool_name)
        except ValueError:
            continue

        tool_display = tool_config.get("name", tool_name)
        _verbose_log(verbose, f"Upgrading {tool_display}...")

        # Backup existing command/rule directories
        cmd_dir_rel = tool_config.get("commands_dir")
        rules_dir_rel = tool_config.get("rules_dir")

        if cmd_dir_rel:
            cmd_dir = target / cmd_dir_rel
            if cmd_dir.is_dir():
                backup_dir = target / f"{cmd_dir_rel}.bak"
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)
                shutil.copytree(cmd_dir, backup_dir)
                _verbose_log(verbose, f"Backed up: {cmd_dir_rel} -> {cmd_dir_rel}.bak")

        if rules_dir_rel:
            rules_dir = target / rules_dir_rel
            if rules_dir.is_dir():
                backup_dir = target / f"{rules_dir_rel}.bak"
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)
                shutil.copytree(rules_dir, backup_dir)
                _verbose_log(verbose, f"Backed up: {rules_dir_rel} -> {rules_dir_rel}.bak")

        # Re-copy commands and rules
        if tool_name == "cursor":
            total_cmds += copy_commands_cursor(commands_source, target, tool_config, rules_source)
        elif tool_name == "codex":
            total_cmds += copy_commands_codex(commands_source, target, tool_config)
        else:
            total_cmds += copy_commands(commands_source, target, tool_config, config)
            total_rules += copy_rules(rules_source, target, tool_config)

        # Re-copy skills and agents for all tools
        if skills_source.is_dir():
            total_skills += copy_skills(skills_source, target, tool_config)
        if agents_source.is_dir():
            total_agents += copy_agents(agents_source, target, tool_config)

    # Update version file
    version_path.write_text(__version__, encoding="utf-8")

    # Always re-apply permissions to ensure settings.json matches config.yml
    if config.permissions_level:
        try:
            perm_result = copy_permissions(target, config, _get_package_dir())
            save_config(config, config_path)
            if not json_output and perm_result["changed"]:
                console.print(
                    f"  Permissions: {perm_result['entries_count']} rules applied "
                    f"(mode: {perm_result['mode']}) -> {perm_result['settings_path']}"
                )
        except CopyError as exc:
            err_console.print(
                f"[red bold]Error:[/red bold] Failed to apply permissions: {exc}\n"
                "Run 'dotnet-ai configure' to fix permissions."
            )

    # T051 - JSON output mode
    if json_output:
        print(
            json.dumps(
                {
                    "status": "upgraded",
                    "old_version": old_version or "unknown",
                    "new_version": __version__,
                    "commands_updated": total_cmds,
                    "rules_updated": total_rules,
                    "skills_updated": total_skills,
                    "agents_updated": total_agents,
                }
            )
        )
        return

    console.print(
        f"\n[green bold]Upgraded from {old_version or 'unknown'} to {__version__}.[/green bold]"
    )
    parts = [f"{total_cmds} commands", f"{total_rules} rules"]
    if total_skills:
        parts.append(f"{total_skills} skills")
    if total_agents:
        parts.append(f"{total_agents} agents")
    console.print(f"  {', '.join(parts)} updated.\n")
    # T052 - Next-command suggestion
    console.print("Next: Run [bold]dotnet-ai check[/bold] to verify the upgrade.\n")


# ---------------------------------------------------------------------------
# configure command
# ---------------------------------------------------------------------------


@app.command()
def configure(
    minimal: bool = typer.Option(
        False,
        "--minimal",
        help="Only prompt for required fields.",
    ),
    no_input: bool = typer.Option(
        False,
        "--no-input",
        help="Non-interactive mode for CI/CD.",
    ),
    company: Optional[str] = typer.Option(
        None,
        "--company",
        help="Company name.",
    ),
    org: Optional[str] = typer.Option(
        None,
        "--org",
        help="GitHub organization.",
    ),
    branch: Optional[str] = typer.Option(
        None,
        "--branch",
        help="Default git branch.",
    ),
    permissions: Optional[str] = typer.Option(
        None,
        "--permissions",
        help="Permission level (minimal/standard/full).",
    ),
    tools: Optional[str] = typer.Option(
        None,
        "--tools",
        help="Comma-separated AI tools.",
    ),
    style: Optional[str] = typer.Option(
        None,
        "--style",
        help="Command style (full/short/both).",
    ),
    reset: bool = typer.Option(
        False,
        "--reset",
        help="Reset all configuration to defaults before prompting.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output JSON.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Preview without making changes.",
    ),
    global_install: bool = typer.Option(
        False,
        "--global",
        help="Apply permissions to global user settings (~/.claude/settings.json).",
    ),
) -> None:
    """Interactive configuration wizard."""
    target = Path(".").resolve()

    if not json_output:
        if dry_run:
            console.print("\n[bold][DRY-RUN] dotnet-ai-kit configure preview[/bold]\n")
        else:
            console.print("\n[bold]dotnet-ai-kit Configuration[/bold]\n")

    config_dir = get_config_dir(target)
    config_path = config_dir / "config.yml"

    # Load existing config or start fresh
    if reset or not config_path.is_file():
        config = DotnetAiConfig()
        _verbose_log(verbose, "Starting with default configuration.")
    else:
        try:
            config = load_config(config_path)
        except (FileNotFoundError, ValueError):
            config = DotnetAiConfig()

    # --no-input mode: use flag values directly, no interactive prompts
    if no_input:
        if not company:
            err_console.print(
                "[red]Error: --company is required when using --no-input. "
                "Example: dotnet-ai configure --no-input --company MyCompany[/red]"
            )
            raise typer.Exit(code=1)
        config.company.name = company
        if org is not None:
            config.company.github_org = org
        if branch is not None:
            config.company.default_branch = branch
        if permissions is not None:
            config.permissions_level = permissions
        if tools is not None:
            config.ai_tools = [t.strip() for t in tools.split(",") if t.strip()]
        if style is not None:
            config.command_style = style
    elif minimal:
        # --minimal mode: only prompt for company name, use defaults for everything else
        company_name = Prompt.ask(
            "Company name (used in C# namespaces)",
            default=config.company.name or "",
        )
        config.company.name = company_name
    else:
        # Full interactive mode

        # Company name (always required)
        company_name = Prompt.ask(
            "Company name (used in C# namespaces)",
            default=config.company.name or "",
        )
        config.company.name = company_name

        # GitHub org
        github_org = Prompt.ask(
            "GitHub organization",
            default=config.company.github_org or "",
        )
        config.company.github_org = github_org

        # Default branch
        default_branch = Prompt.ask(
            f"Default git branch (current: {config.company.default_branch})",
            default=config.company.default_branch,
        )
        config.company.default_branch = default_branch

        # Permission level (T040)
        perm_default_map = {"minimal": "1", "standard": "2", "full": "3"}
        perm_default = perm_default_map.get(config.permissions_level, "2")
        perm_choice = Prompt.ask(
            "Permission level\n"
            "  [bold]1[/bold]. Minimal   - Only dotnet build/test/restore\n"
            "  [bold]2[/bold]. Standard  - Common dev commands (recommended)\n"
            "  [bold]3[/bold]. Full      - All commands including Docker",
            choices=["1", "2", "3"],
            default=perm_default,
        )
        perm_map = {"1": "minimal", "2": "standard", "3": "full"}
        config.permissions_level = perm_map.get(perm_choice, "standard")

        # AI tools multi-select (T041) — v1.0: Claude only
        current_tools = config.ai_tools or []
        tools_result = questionary.checkbox(
            "AI tools to configure:",
            choices=[
                questionary.Choice(
                    "Claude Code",
                    value="claude",
                    checked="claude" in current_tools,
                ),
            ],
        ).ask()
        if tools_result is not None:
            config.ai_tools = tools_result

        # Command style single-select (T042)
        style_default_map = {"full": "1", "short": "2", "both": "3"}
        style_default = style_default_map.get(config.command_style, "3")
        style_choice = Prompt.ask(
            "Command style\n"
            "  [bold]1[/bold]. Full   - Full command names only\n"
            "  [bold]2[/bold]. Short  - Short aliases only\n"
            "  [bold]3[/bold]. Both   - Both full names and short aliases",
            choices=["1", "2", "3"],
            default=style_default,
        )
        style_map = {"1": "full", "2": "short", "3": "both"}
        config.command_style = style_map.get(style_choice, "both")

    # T058 - Dry run: show what WOULD be saved
    if dry_run:
        console.print("[bold]Would save the following configuration:[/bold]")
        console.print(f"  Company: {config.company.name}")
        console.print(f"  GitHub Org: {config.company.github_org or '(not set)'}")
        console.print(f"  Default Branch: {config.company.default_branch}")
        console.print(f"  Permissions: {config.permissions_level}")
        console.print(f"  AI Tools: {', '.join(config.ai_tools) if config.ai_tools else '(none)'}")
        console.print(f"  Command Style: {config.command_style}")
        console.print(f"  Config path: {config_path}")
        console.print("\n[dim]No changes were made (dry run).[/dim]")
        return

    # Save config
    config_dir.mkdir(parents=True, exist_ok=True)
    save_config(config, config_path)

    # Apply permissions to .claude/settings.json
    try:
        if config.permissions_level == "full" and not json_output:
            console.print(
                "\n[yellow bold]Warning:[/yellow bold] Full permission mode enables "
                "bypassPermissions — the AI assistant will execute all operations "
                "without prompting. Only use in trusted environments."
            )
        perm_result = copy_permissions(
            target, config, _get_package_dir(), global_install=global_install
        )
        save_config(config, config_path)
        if not json_output and perm_result["changed"]:
            scope = "global" if global_install else "project"
            console.print(
                f"\n  Permissions ({scope}): {perm_result['entries_count']} rules applied "
                f"(mode: {perm_result['mode']}) -> {perm_result['settings_path']}"
            )
    except CopyError as exc:
        err_console.print(
            f"[red bold]Error:[/red bold] Failed to apply permissions: {exc}\n"
            "Config was saved but permissions were NOT applied to settings.json.\n"
            "Run 'dotnet-ai upgrade --force' to retry."
        )
        raise typer.Exit(code=1) from exc

    # T051 - JSON output mode
    if json_output:
        print(
            json.dumps(
                {
                    "company": config.company.name,
                    "github_org": config.company.github_org,
                    "default_branch": config.company.default_branch,
                    "permissions_level": config.permissions_level,
                    "ai_tools": config.ai_tools,
                    "command_style": config.command_style,
                    "config_path": str(config_path),
                }
            )
        )
        return

    console.print(f"\n[green]Configuration saved to {config_path.relative_to(target)}[/green]\n")

    # Configuration summary table (T045)
    summary = Table(title="Configuration Saved")
    summary.add_column("Setting", style="bold")
    summary.add_column("Value")
    summary.add_row("Company", config.company.name)
    summary.add_row("GitHub Org", config.company.github_org or "(not set)")
    summary.add_row("Default Branch", config.company.default_branch)
    summary.add_row("Permissions", config.permissions_level)
    summary.add_row("AI Tools", ", ".join(config.ai_tools) if config.ai_tools else "(none)")
    summary.add_row("Command Style", config.command_style)
    console.print(summary)

    # Validate development tools
    _validate_tools(console, verbose=verbose)

    # T052 - Next-command suggestion
    console.print("\nNext: Run [bold]dotnet-ai check[/bold] to verify your setup.\n")


# ---------------------------------------------------------------------------
# extension commands
# ---------------------------------------------------------------------------


@app.command("extension-add")
def extension_add(
    name: str = typer.Argument(
        ...,
        help="Extension name or local path (with --dev).",
    ),
    dev: bool = typer.Option(
        False,
        "--dev",
        help="Install from a local directory.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output.",
    ),
) -> None:
    """Install an extension."""
    target = Path(".").resolve()

    try:
        manifest = install_extension(name, dev=dev, project_root=target)
    except ExtensionError as exc:
        err_console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    cmd_count = len(manifest.commands)
    rule_count = len(manifest.rules)
    console.print(
        f"[green]Extension '{manifest.name}' installed. "
        f"{cmd_count} commands, {rule_count} rules added.[/green]"
    )


@app.command("extension-remove")
def extension_remove_cmd(
    name: str = typer.Argument(
        ...,
        help="Extension ID to remove.",
    ),
) -> None:
    """Remove an installed extension."""
    target = Path(".").resolve()

    try:
        remove_extension(name, project_root=target)
    except ExtensionError as exc:
        err_console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Extension '{name}' removed.[/green]")


@app.command("extension-list")
def extension_list_cmd() -> None:
    """List installed extensions."""
    target = Path(".").resolve()
    extensions = list_extensions(target)

    if not extensions:
        console.print("No extensions installed.\n")
        return

    table = Table(title="Installed Extensions")
    table.add_column("ID", style="bold")
    table.add_column("Version")
    table.add_column("Source")
    table.add_column("Installed")
    table.add_column("Commands")

    for ext in extensions:
        table.add_row(
            ext.get("id", "?"),
            ext.get("version", "?"),
            ext.get("source", "?"),
            ext.get("installed", "?"),
            str(len(ext.get("commands", []))),
        )

    console.print(table)
    console.print()


# T054 - Ctrl-C handler
if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
        raise SystemExit(130)
