"""CLI commands for dotnet-ai-kit.

Provides the `dotnet-ai` command-line interface using typer with rich
formatting for terminal output.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dotnet_ai_kit import __version__
from dotnet_ai_kit.agents import AGENT_CONFIG, detect_ai_tools, get_agent_config
from dotnet_ai_kit.config import (
    get_config_dir,
    load_config,
    load_project,
    save_config,
    save_project,
)
from dotnet_ai_kit.copier import (
    copy_commands,
    copy_commands_codex,
    copy_commands_cursor,
    copy_rules,
)
from dotnet_ai_kit.detection import DetectionError, detect_project
from dotnet_ai_kit.extensions import (
    ExtensionError,
    install_extension,
    list_extensions,
    remove_extension,
)
from dotnet_ai_kit.models import DotnetAiConfig

app = typer.Typer(
    name="dotnet-ai",
    help="AI dev tool plugin for the full .NET development lifecycle.",
    add_completion=False,
)

console = Console()


def _get_package_dir() -> Path:
    """Get the dotnet-ai-kit package installation directory.

    Used to locate bundled templates, commands, and rules.
    """
    return Path(__file__).resolve().parent.parent.parent


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


def _verbose_log(verbose: bool, message: str) -> None:
    """Print a verbose log message if verbose mode is enabled."""
    if verbose:
        console.print(f"  [dim]{message}[/dim]")


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
        help="AI tool(s) to configure (claude, cursor, copilot, codex, antigravity). Repeatable.",
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
) -> None:
    """Initialize dotnet-ai-kit in a .NET project directory."""
    target = path.resolve()
    console.print(f"\n[bold]dotnet-ai-kit v{__version__}[/bold]\n")

    # Check if already initialized
    config_dir = get_config_dir(target)
    if config_dir.is_dir() and not force:
        console.print(
            "[yellow]dotnet-ai-kit already initialized. "
            "Use --force to reinitialize.[/yellow]"
        )
        raise typer.Exit(code=1)

    # Step 1: Detect project type
    console.print("[bold]Scanning project...[/bold]")
    try:
        detected = detect_project(target)
    except DetectionError:
        # No .NET project found — this might be a new project scenario
        detected = None
        console.print("  [dim]No .NET project detected (new project mode).[/dim]")

    if detected:
        console.print(f"  Found project in: {target}")
        console.print(f"  .NET Version: {detected.dotnet_version or 'unknown'}")
        console.print(f"  Project Type: {detected.project_type.title()}")
        console.print(f"  Architecture: {detected.architecture}")

    # Override project type if specified
    if project_type and detected:
        detected.project_type = project_type
        detected.architecture = project_type
        _verbose_log(verbose, f"Project type overridden to: {project_type}")

    # Step 2: Detect or configure AI tools
    if ai:
        ai_tools = [t.lower() for t in ai]
    else:
        ai_tools = detect_ai_tools(target)
        if not ai_tools:
            console.print(
                "\n[yellow]No AI tool detected. Use --ai flag "
                "(e.g., --ai claude).[/yellow]"
            )
            raise typer.Exit(code=1)

    _verbose_log(verbose, f"AI tools: {', '.join(ai_tools)}")

    # Step 3: Create config directory
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "memory").mkdir(parents=True, exist_ok=True)
    (config_dir / "features").mkdir(parents=True, exist_ok=True)

    # Step 4: Save config
    config = DotnetAiConfig(ai_tools=ai_tools)
    config_path = config_dir / "config.yml"
    save_config(config, config_path)
    console.print(f"  Created: {config_path.relative_to(target)}")

    # Step 5: Save project detection results
    if detected:
        project_path = config_dir / "project.yml"
        save_project(detected, project_path)
        console.print(f"  Created: {project_path.relative_to(target)}")

    # Step 6: Write version file
    version_path = config_dir / "version.txt"
    version_path.write_text(__version__, encoding="utf-8")

    # Step 7: Copy commands and rules for each AI tool
    commands_source = _find_commands_source()
    rules_source = _find_rules_source()

    for tool_name in ai_tools:
        try:
            tool_config = get_agent_config(tool_name)
        except ValueError:
            console.print(f"  [yellow]Skipping unknown tool: {tool_name}[/yellow]")
            continue

        tool_display = tool_config.get("name", tool_name)
        console.print(f"\n[bold]Initializing for {tool_display}...[/bold]")

        cmd_count = 0
        rule_count = 0

        if tool_name == "cursor":
            cmd_count = copy_commands_cursor(
                commands_source, target, tool_config, rules_source
            )
        elif tool_name == "codex":
            cmd_count = copy_commands_codex(commands_source, target, tool_config)
        else:
            cmd_count = copy_commands(commands_source, target, tool_config, config)
            rule_count = copy_rules(rules_source, target, tool_config)

        if cmd_count:
            console.print(
                f"  Copied: {cmd_count} commands -> "
                f"{tool_config.get('commands_dir') or tool_config.get('rules_dir', '')}"
            )
        if rule_count:
            console.print(
                f"  Copied: {rule_count} rules -> {tool_config.get('rules_dir', '')}"
            )

    # Summary
    console.print(
        f"\n[green bold]dotnet-ai-kit initialized for "
        f"{', '.join(ai_tools)}[/green bold]"
    )
    console.print("  Run [bold]/dotnet-ai.configure[/bold] to set up company name and repos.\n")


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
) -> None:
    """Report the current state of dotnet-ai-kit in the project."""
    target = Path(".").resolve()
    console.print(f"\n[bold]dotnet-ai-kit v{__version__}[/bold]\n")

    config_dir = get_config_dir(target)
    if not config_dir.is_dir():
        console.print("[yellow]dotnet-ai-kit is not initialized in this directory.[/yellow]")
        console.print("Run: [bold]dotnet-ai init .[/bold]\n")
        raise typer.Exit(code=1)

    # Load config
    config_path = config_dir / "config.yml"
    try:
        config = load_config(config_path)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]Error loading config: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    # Load project info
    project_path = config_dir / "project.yml"
    detected = None
    try:
        detected = load_project(project_path)
    except (FileNotFoundError, ValueError):
        _verbose_log(verbose, "No project.yml found.")

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

        status = "[green]configured[/green]" if (cmd_count + rule_count) > 0 else "[yellow]empty[/yellow]"
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
        1 for v in [
            config.repos.command,
            config.repos.query,
            config.repos.processor,
            config.repos.gateway,
            config.repos.controlpanel,
        ] if v
    )
    config_panel_lines.append(f"  Repos: {repos_configured} of 5 configured")
    config_panel_lines.append(f"  Permissions: {config.permissions_level}")

    console.print(Panel("\n".join(config_panel_lines), title="Config"))
    console.print()

    # Version info
    version_path = config_dir / "version.txt"
    if version_path.is_file():
        installed_version = version_path.read_text(encoding="utf-8").strip()
        if installed_version != __version__:
            console.print(
                f"[yellow]Version mismatch: installed={installed_version}, "
                f"CLI={__version__}. Run 'dotnet-ai upgrade'.[/yellow]"
            )
        else:
            _verbose_log(verbose, f"Version: {__version__} (up to date)")


# ---------------------------------------------------------------------------
# upgrade command
# ---------------------------------------------------------------------------

@app.command()
def upgrade(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output.",
    ),
) -> None:
    """Upgrade command and rule files to the latest CLI version."""
    target = Path(".").resolve()
    console.print(f"\n[bold]dotnet-ai-kit v{__version__}[/bold]\n")

    config_dir = get_config_dir(target)
    if not config_dir.is_dir():
        console.print("[yellow]dotnet-ai-kit is not initialized. Run 'dotnet-ai init' first.[/yellow]")
        raise typer.Exit(code=1)

    # Compare versions
    version_path = config_dir / "version.txt"
    old_version = ""
    if version_path.is_file():
        old_version = version_path.read_text(encoding="utf-8").strip()

    if old_version == __version__:
        console.print("[green]Already up to date.[/green]\n")
        return

    console.print(f"Upgrading from {old_version or 'unknown'} to {__version__}...")

    # Load config
    config_path = config_dir / "config.yml"
    try:
        config = load_config(config_path)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]Error loading config: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    commands_source = _find_commands_source()
    rules_source = _find_rules_source()

    total_cmds = 0
    total_rules = 0

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
            total_cmds += copy_commands_cursor(
                commands_source, target, tool_config, rules_source
            )
        elif tool_name == "codex":
            total_cmds += copy_commands_codex(commands_source, target, tool_config)
        else:
            total_cmds += copy_commands(commands_source, target, tool_config, config)
            total_rules += copy_rules(rules_source, target, tool_config)

    # Update version file
    version_path.write_text(__version__, encoding="utf-8")

    console.print(
        f"\n[green bold]Upgraded from {old_version or 'unknown'} to {__version__}.[/green bold]"
    )
    console.print(f"  {total_cmds} commands updated, {total_rules} rules updated.\n")


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
) -> None:
    """Interactive configuration wizard."""
    target = Path(".").resolve()
    console.print(f"\n[bold]dotnet-ai-kit Configuration[/bold]\n")

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

    # Prompt for company name (always required)
    company_name = typer.prompt(
        "Company name (used in C# namespaces)",
        default=config.company.name or "",
    )
    config.company.name = company_name

    if not minimal:
        # GitHub org
        github_org = typer.prompt(
            "GitHub organization",
            default=config.company.github_org or "",
        )
        config.company.github_org = github_org

        # Default branch
        default_branch = typer.prompt(
            "Default git branch",
            default=config.company.default_branch,
        )
        config.company.default_branch = default_branch

        # Permission level
        console.print("\nPermission levels:")
        console.print("  1. Minimal   - Only build/test")
        console.print("  2. Standard  - Build, test, git, gh CLI (recommended)")
        console.print("  3. Full      - All operations in working directory")

        perm_choice = typer.prompt("Permission level (1/2/3)", default="2")
        perm_map = {"1": "minimal", "2": "standard", "3": "full"}
        config.permissions_level = perm_map.get(perm_choice, "standard")

    # Save config
    config_dir.mkdir(parents=True, exist_ok=True)
    save_config(config, config_path)

    console.print(f"\n[green]Configuration saved to {config_path.relative_to(target)}[/green]\n")


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
        console.print(f"[red]Error: {exc}[/red]")
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
        console.print(f"[red]Error: {exc}[/red]")
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


if __name__ == "__main__":
    app()
