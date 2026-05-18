"""CLI commands for dotnet-ai-kit.

Provides the `dotnet-ai` command-line interface using typer with rich
formatting for terminal output.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from contextlib import contextmanager
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
)
from dotnet_ai_kit.copier import (
    CopyError,
    copy_agents,
    copy_commands,
    # T049: copy_commands_codex removed — root AGENTS.md emitter deleted.
    copy_commands_cursor,
    copy_hook,
    copy_permissions,
    copy_profile,
    copy_rules,
    copy_skills,
    deploy_to_linked_repos,
    verify_permissions,
)
from dotnet_ai_kit.detection import describe_architecture
from dotnet_ai_kit.extensions import (
    CatalogInstallError,
    ExtensionError,
    install_extension,
    list_extensions,
    remove_extension,
)
from dotnet_ai_kit.manifest import (
    DeployedFile,
    Manifest,
    read_manifest,
    sha256_file,
    utc_now_iso,
    write_manifest,
)
from dotnet_ai_kit.mcp_check import (
    MIN_CODEBASE_MEMORY_MCP_VERSION,
    check_codebase_memory_mcp,
)
from dotnet_ai_kit.models import DetectedProject, DotnetAiConfig
from dotnet_ai_kit.utils import HOOK_MODEL, HOOK_TIMEOUT_MS

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


def _detect_plugin_mode() -> bool:
    """Check whether dotnet-ai-kit is running as a Claude Code plugin.

    Returns True when ``.claude-plugin/plugin.json`` exists in the
    package source directory, indicating the plugin system already
    serves full-prefix commands.
    """
    return (_get_package_dir() / ".claude-plugin" / "plugin.json").is_file()


# Feature 019 / T042 / T043: hosts that serve commands/skills/agents from
# their plugin install path instead of per-solution copies. For these hosts,
# `dotnet-ai init` MUST NOT bulk-copy into the solution per FR-005 / FR-006.
PLUGIN_NATIVE_HOSTS: frozenset[str] = frozenset({"claude", "codex", "cursor"})

# Feature 019 / Blocker-2 (per Codex implement-phase round 1): render-only
# hosts must SKIP the legacy bulk-copy branch. Their per-solution writes go
# through their respective host adapter (CopilotHost.render()).
RENDER_ONLY_HOSTS: frozenset[str] = frozenset({"copilot"})

# Feature 019 / T100 / FR-025: legacy managed-path patterns from feature 018.
# When `dotnet-ai init --force` detects any of these on a target solution,
# it MUST refuse auto-deletion and print the migrate invocation instead.
LEGACY_MANAGED_PATHS: tuple[str, ...] = (
    ".claude/commands",
    ".claude/rules",
    ".claude/skills",
    ".claude/agents",
    ".cursor/rules",
    ".github/agents/commands",
)


def _prompt_for_hosts(default_hosts: list[str]) -> list[str]:
    """Per FR-014 / clarify Q4: launch interactive host-selection when
    `dotnet-ai init` is invoked without `--ai`. Returns the user-selected
    subset of SUPPORTED_AI_TOOLS.

    The prompt shows all 4 hosts (claude/codex/cursor/copilot) with the
    auto-detected hosts pre-checked. Selecting nothing = pick all 4.
    """
    try:
        import questionary as _qy  # noqa: PLC0415
    except ImportError:
        # questionary missing — fall back to default hosts.
        return default_hosts or list(sorted(SUPPORTED_AI_TOOLS))

    choices = []
    for host in sorted(SUPPORTED_AI_TOOLS):
        choices.append(
            _qy.Choice(
                title=host,
                value=host,
                checked=(host in default_hosts),
            )
        )
    selected = _qy.checkbox(
        "Which AI hosts should this solution be initialized for?",
        choices=choices,
    ).ask()
    if not selected:
        # User cancelled / picked none — return the auto-detected default.
        return default_hosts or ["claude"]
    return [h.lower() for h in selected]


def _stdin_is_tty() -> bool:
    """Return True if stdin is a terminal (interactive shell).

    Used by `init` to decide whether to launch the questionary prompt
    when `--ai` is absent. Returns False in CI / piped contexts so
    non-interactive runs use auto-detected defaults.
    """
    import sys as _sys  # noqa: PLC0415

    try:
        return _sys.stdin.isatty()
    except (AttributeError, ValueError):
        return False


def _record_copilot_renders_in_manifest(target: Path, written: list[Path]) -> None:
    """Per T070 / FR-024: record Copilot-rendered files in manifest with
    `host_owner="copilot"` and explicit-consent flag for force-rendered paths.
    """
    if not written:
        return
    import hashlib  # noqa: PLC0415

    from dotnet_ai_kit.manifest import (  # noqa: PLC0415
        DeployedFile,
        manifest_path,
        read_manifest,
        utc_now_iso,
        write_manifest,
    )

    mp = manifest_path(target)
    if not mp.is_file():
        # No manifest yet — skip silently (init creates it via _finalize_manifest)
        return
    manifest = read_manifest(target)
    if manifest is None:
        return

    by_path = {f.path: f for f in manifest.files}
    now = utc_now_iso()
    for p in written:
        rel = str(p.relative_to(target)).replace("\\", "/")
        sha = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else ""
        entry = DeployedFile(
            path=rel,
            sha256=sha,
            host_owner="copilot",
            plugin_version=manifest.plugin_version,
            deployed_at=now,
        )
        by_path[rel] = entry

    new_manifest = manifest.model_copy(
        update={
            "files": list(by_path.values()),
            "last_upgrade_at": now,
        }
    )
    write_manifest(target, new_manifest)


def _detect_shadowed_legacy_paths(target: Path) -> list[Path]:
    """Return any LEGACY_MANAGED_PATHS that contain ACTUAL FILES on disk.

    Used by `init --force` (T100 / FR-025) to detect pre-019-layout artifacts
    that would shadow plugin-served files. The init flow MUST NOT auto-delete
    these — it prints the migrate invocation and exits non-zero.

    Empty marker directories (e.g., tests creating `.claude/commands/` to
    signal AI-tool presence) are NOT flagged — only directories that actually
    contain files are considered shadowed legacy artifacts.
    """
    found: list[Path] = []
    for relpath in LEGACY_MANAGED_PATHS:
        candidate = target / relpath
        if not candidate.exists():
            continue
        if candidate.is_file():
            found.append(candidate)
        elif candidate.is_dir():
            # Only flag if the dir actually contains FILES
            if any(p.is_file() for p in candidate.rglob("*")):
                found.append(candidate)
    return found


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
    """Find the source-of-truth agents directory in the package.

    Feature 019 / commit 6 / T054: agents/ -> agents-source/ rename. The
    canonical location is `agents-source/`; the legacy `agents/` path is
    kept as a fallback for installs still on the pre-rename layout (will
    be removed in a future cleanup).
    """
    pkg = _get_package_dir()
    new_dir = pkg / "agents-source"
    if new_dir.is_dir() and any(new_dir.glob("*.md")):
        return new_dir
    # Fallback (legacy install with pre-rename layout)
    return pkg / "agents"


def _verbose_log(verbose: bool, message: str) -> None:
    """Print a verbose log message if verbose mode is enabled."""
    if verbose:
        console.print(f"  [dim]{message}[/dim]")


def _get_tool_status(tool_name: str, tool_config: dict, target: Path) -> dict:
    """Collect deployment status for a single AI tool.

    Returns a dict with keys: commands, rules, skills, agents, profile, hook.
    """
    cmd_dir_rel = tool_config.get("commands_dir")
    rules_dir_rel = tool_config.get("rules_dir")
    skills_dir_rel = tool_config.get("skills_dir")
    agents_dir_rel = tool_config.get("agents_dir")

    cmd_count = 0
    rule_count = 0
    skill_count = 0
    agent_count = 0

    if cmd_dir_rel:
        cmd_dir = target / cmd_dir_rel
        if cmd_dir.is_dir():
            cmd_count = len(list(cmd_dir.iterdir()))
    if rules_dir_rel:
        rules_dir = target / rules_dir_rel
        if rules_dir.is_dir():
            rule_count = len(list(rules_dir.iterdir()))
    if skills_dir_rel:
        skills_path = target / skills_dir_rel
        if skills_path.is_dir():
            skill_count = len(list(skills_path.glob("**/SKILL.md")))
    if agents_dir_rel:
        agents_path = target / agents_dir_rel
        if agents_path.is_dir():
            agent_count = len(list(agents_path.glob("*.md")))

    has_profile = bool(
        rules_dir_rel and (target / rules_dir_rel / "architecture-profile.md").is_file()
    )

    has_hook = False
    if tool_name == "claude":
        settings_path = target / ".claude" / "settings.json"
        if settings_path.is_file():
            try:
                settings_data = json.loads(settings_path.read_text(encoding="utf-8"))
                pre_tool_use = settings_data.get("hooks", {}).get("PreToolUse", [])
                for entry in pre_tool_use:
                    if isinstance(entry, dict) and entry.get("_source") == "dotnet-ai-kit-arch":
                        has_hook = True
                        break
            except (json.JSONDecodeError, AttributeError):
                pass

    return {
        "commands": cmd_count,
        "rules": rule_count,
        "skills": skill_count,
        "agents": agent_count,
        "profile": has_profile,
        "hook": has_hook,
    }


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
# MCP detection helper (T068 / T068a / FR-019)
# ---------------------------------------------------------------------------


def _record_mcp_state(
    project_root: Path, *, verbose: bool = False, json_output: bool = False
) -> dict:
    """Detect ``codebase-memory-mcp`` and record the outcome in a sibling
    state file.

    Writes to ``.dotnet-ai-kit/mcp-state.yml`` rather than ``config.yml`` so
    we don't have to widen ``DotnetAiConfig``'s ``_KNOWN_CONFIG_KEYS`` (and
    so a future ``save_config()`` rewrite via the pydantic path doesn't drop
    the mcp section through ``extra="ignore"``).

    Returns the outcome dict for the caller to surface to the user.
    """
    config_dir = project_root / ".dotnet-ai-kit"
    config_dir.mkdir(parents=True, exist_ok=True)
    state_path = config_dir / "mcp-state.yml"

    health = check_codebase_memory_mcp()
    if not health.present:
        status = "unavailable"
    elif not health.meets_minimum:
        status = "below-minimum"
    else:
        status = "accepted"

    outcome = {
        "status": status,
        "version": health.version,
        "min_version": MIN_CODEBASE_MEMORY_MCP_VERSION,
        "error": health.error,
    }

    import yaml as _yaml

    data: dict = {}
    if state_path.is_file():
        try:
            data = _yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
        except _yaml.YAMLError:
            data = {}
    data.setdefault("mcp", {})["codebase-memory-mcp"] = outcome

    tmp = state_path.with_name("mcp-state.yml.tmp")
    tmp.write_text(
        _yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    tmp.replace(state_path)

    if not json_output and status != "accepted":
        msg = {
            "unavailable": (
                f"codebase-memory-mcp not on PATH — falling back to csharp-ls + grep. "
                f"Install with `pip install codebase-memory-mcp>={MIN_CODEBASE_MEMORY_MCP_VERSION}` "
                "for graph queries."
            ),
            "below-minimum": (
                f"codebase-memory-mcp {health.version} is below the required "
                f">= {MIN_CODEBASE_MEMORY_MCP_VERSION}. Upgrade for graph queries."
            ),
        }.get(status, "")
        if msg:
            console.print(f"[yellow]{msg}[/yellow]")

    return outcome


# ---------------------------------------------------------------------------
# manifest + .gitignore helpers (T044 / T044a / T045 / FR-032)
# ---------------------------------------------------------------------------


_MANIFEST_SCAN_DIRS: tuple[str, ...] = (
    ".claude/commands",
    ".claude/rules",
    ".claude/skills",
    ".claude/agents",
    ".claude/profiles",
    ".claude/settings.json",
    ".mcp.json",
    ".cursor",
    ".github/copilot-instructions.md",
    # Feature 019 / Blocker-5 (per Codex implement-phase round 1):
    # path-scoped Copilot files and per-agent files must be in the manifest
    # so freshness detection in `dotnet-ai check` and migrate's classification
    # can pick them up with host_owner='copilot'.
    ".github/instructions",
    ".github/agents",
    ".codex",
)


def _write_dotnet_ai_kit_gitignore(project_root: Path) -> None:
    """Generate ``.dotnet-ai-kit/.gitignore`` so backup/upgrade dirs stay out of git."""
    gi = project_root / ".dotnet-ai-kit" / ".gitignore"
    gi.parent.mkdir(parents=True, exist_ok=True)
    content = "# Auto-generated by dotnet-ai-kit. Do not commit local upgrade state.\nbackups/\nbackups/**\n"
    if not gi.is_file() or gi.read_text(encoding="utf-8") != content:
        gi.write_text(content, encoding="utf-8")


def _collect_deployed_files(project_root: Path) -> list[DeployedFile]:
    """Walk known plugin output paths and snapshot their SHA-256."""
    deployed: list[DeployedFile] = []
    seen: set[str] = set()
    now = utc_now_iso()
    for rel in _MANIFEST_SCAN_DIRS:
        candidate = project_root / rel
        if candidate.is_file():
            paths = [candidate]
        elif candidate.is_dir():
            paths = [p for p in candidate.rglob("*") if p.is_file()]
        else:
            continue
        for p in paths:
            rel_path = p.relative_to(project_root).as_posix()
            if rel_path in seen:
                continue
            seen.add(rel_path)
            # Feature 019 / commit 10: infer host_owner from path per R16.
            from dotnet_ai_kit.manifest import infer_host_owner

            deployed.append(
                DeployedFile(
                    path=rel_path,
                    sha256=sha256_file(p),
                    plugin_version=__version__,
                    deployed_at=now,
                    host_owner=infer_host_owner(rel_path),
                )
            )
    return deployed


def _finalize_manifest(project_root: Path) -> Path | None:
    """Refresh ``.dotnet-ai-kit/manifest.json`` after a successful init/upgrade."""
    files = _collect_deployed_files(project_root)
    existing = read_manifest(project_root)
    created_at = existing.created_at if existing else utc_now_iso()
    last_upgrade = utc_now_iso() if existing else None
    # Feature 019 / commit 10: writer always emits v2 (host_owner per file).
    # The model defaults schema_version to "2".
    manifest = Manifest(
        plugin_version=__version__,
        created_at=created_at,
        last_upgrade_at=last_upgrade,
        files=files,
    )
    return write_manifest(project_root, manifest)


# T043a / FR-031 / SC-013: atomic snapshot+restore for the legacy upgrade path.
# The standalone ``upgrade.run_upgrade`` orchestrator stays as the reference
# implementation (and unit-tested via test_upgrade_atomic.py); the CLI flow
# wraps the existing copy_* sequence with the same guarantees via a full
# directory snapshot of the managed scan dirs.


def _snapshot_managed_state(project_root: Path) -> Path:
    """Copy every managed directory + file into a timestamped backup dir.

    Returns the snapshot root. Callers either delete it on success or restore
    from it on failure via :func:`_restore_managed_state`.
    """
    import uuid as _uuid
    from datetime import datetime as _dt
    from datetime import timezone as _tz

    iso = _dt.now(_tz.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_parent = project_root / ".dotnet-ai-kit" / "backups" / "upgrade"
    backup_parent.mkdir(parents=True, exist_ok=True)
    backup_dir = backup_parent / f"{iso}-{_uuid.uuid4().hex[:8]}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    for rel in _MANIFEST_SCAN_DIRS:
        src = project_root / rel
        if not src.exists():
            continue
        dest = backup_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dest, dirs_exist_ok=False)
        else:
            shutil.copy2(src, dest)
    return backup_dir


def _restore_managed_state(project_root: Path, backup_dir: Path) -> None:
    """Restore every managed path from a snapshot taken by
    :func:`_snapshot_managed_state`. Replaces current contents in place."""
    for rel in _MANIFEST_SCAN_DIRS:
        live = project_root / rel
        snap = backup_dir / rel
        if snap.exists():
            if live.exists():
                if live.is_dir():
                    shutil.rmtree(live)
                else:
                    live.unlink()
            live.parent.mkdir(parents=True, exist_ok=True)
            if snap.is_dir():
                shutil.copytree(snap, live)
            else:
                shutil.copy2(snap, live)
        elif live.exists():
            # The path did not exist before the snapshot; remove what the
            # failed deploy created so the project lands back at pre-upgrade.
            if live.is_dir():
                shutil.rmtree(live)
            else:
                live.unlink()


def _rotate_upgrade_backups(project_root: Path, keep: int = 3) -> None:
    """Trim ``.dotnet-ai-kit/backups/upgrade/`` to the last ``keep`` runs."""
    parent = project_root / ".dotnet-ai-kit" / "backups" / "upgrade"
    if not parent.is_dir():
        return
    dirs = sorted([p for p in parent.iterdir() if p.is_dir()], key=lambda p: p.name)
    for old in dirs[:-keep]:
        shutil.rmtree(old, ignore_errors=True)


@contextmanager
def _atomic_upgrade(project_root: Path):
    """Snapshot the managed tree on enter; restore it if the block raises.

    Yields the backup dir path. On success, the caller is responsible for
    rotation (we call :func:`_rotate_upgrade_backups` here once the block
    exits cleanly). On failure we restore byte-for-byte and re-raise.

    typer.Exit is treated like any other exception: a non-zero exit thrown
    after partial deploys also triggers rollback. SystemExit(0) is treated
    as success.
    """
    backup_dir = _snapshot_managed_state(project_root)
    try:
        yield backup_dir
    except typer.Exit as exit_exc:
        if int(getattr(exit_exc, "exit_code", 0) or 0) != 0:
            _restore_managed_state(project_root, backup_dir)
        raise
    except BaseException:
        _restore_managed_state(project_root, backup_dir)
        raise
    _rotate_upgrade_backups(project_root)


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
    permissions: Optional[str] = typer.Option(
        None,
        "--permissions",
        help="Permission level (minimal/standard/full).",
    ),
    force_render: Optional[list[str]] = typer.Option(
        None,
        "--force-render",
        help=(
            "Per T072c: explicit opt-in to overwrite a pre-existing Copilot file. "
            "Repeatable. Each value is a path relative to the project root. "
            "(See contracts/copilot-instructions.contract.md:39-41.)"
        ),
    ),
    company: Optional[str] = typer.Option(
        None,
        "--company",
        help=(
            "Company name for ProjectMetadata.company (feature 019 / B-3). "
            "If omitted, falls back to config.yml::company.name or empty."
        ),
    ),
    domain: Optional[str] = typer.Option(
        None,
        "--domain",
        help="Logical domain for ProjectMetadata.domain (feature 019 / B-3).",
    ),
    side: Optional[str] = typer.Option(
        None,
        "--side",
        help="server | client — for ProjectMetadata.side (feature 019 / B-3).",
    ),
) -> None:
    """Initialize dotnet-ai-kit in a .NET project directory."""
    target = path.resolve()

    # Feature 019 / commit 20 / B-3: validate --side if provided
    if side is not None and side.lower() not in ("server", "client"):
        raise typer.BadParameter(f"Invalid --side '{side}'. Choose from: server, client")

    # Validate --permissions value
    if permissions is not None and permissions.lower() not in ("minimal", "standard", "full"):
        raise typer.BadParameter(
            f"Invalid permissions level '{permissions}'. Choose from: minimal, standard, full"
        )

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

    # Feature 019 / T100 / FR-025: when --force lands on an old-layout solution
    # (pre-019 paths present), refuse auto-deletion and print the migrate
    # invocation. The user must opt in explicitly via `dotnet-ai migrate`.
    if force:
        shadowed = _detect_shadowed_legacy_paths(target)
        if shadowed:
            err_console.print(
                "[red bold]Refusing to reinitialize:[/red bold] this solution has "
                "legacy dotnet-ai-kit artifacts from the pre-019 layout."
            )
            for p in shadowed:
                err_console.print(f"  - {p.relative_to(target)}")
            err_console.print(
                "\nRun the migrate command to convert legacy paths to the new "
                "plugin-native layout (with backup):\n"
                f"  [bold]dotnet-ai migrate {target}[/bold]\n"
                "\nOr inspect what migrate would do without making changes:\n"
                f"  [bold]dotnet-ai migrate --dry-run {target}[/bold]\n"
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
    # Feature 019 / T031-T032 / FR-014 / clarify Q4: when `--ai` is absent,
    # launch an interactive host-selection prompt. JSON mode skips the prompt
    # (non-interactive) and uses the auto-detect default.
    if ai:
        ai_tools = [t.lower() for t in ai]
    else:
        detected_ai = detect_ai_tools(target)
        if json_output or not _stdin_is_tty():
            # Non-interactive: pick auto-detect, fall back to Claude.
            ai_tools = detected_ai or ["claude"]
            if not json_output:
                if detected_ai:
                    console.print(f"\n[dim]Auto-detected AI tools: {', '.join(detected_ai)}.[/dim]")
                else:
                    console.print("\n[dim]No AI tool detected. Defaulting to Claude Code.[/dim]")
        else:
            # Interactive prompt per FR-014.
            ai_tools = _prompt_for_hosts(detected_ai or ["claude"])

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
    # Feature 019 / commit 19 / B-2 / T143: init writes a slim UserConfig
    # (`enabled_hosts`, `plugin_version`, optional `permission_profile`,
    # `retention`) that validates against `schemas/config-yml.schema.json`.
    # The wider DotnetAiConfig fields (`company`, `repos`, etc.) are
    # populated later by `dotnet-ai configure` and stored alongside the
    # UserConfig fields in the same file (configure's output relaxes the
    # strict schema by design — only init's output is contract-validated).
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
    if permissions is not None:
        config.permissions_level = permissions.lower()
    # Feature 019 / commit 19 / B-2 / T143: stamp plugin_version on init so
    # `migrate` can identify pre-019 layouts and `check` can validate schema.
    if not config.plugin_version:
        config.plugin_version = __version__

    # B-2 (T143): emit a slim UserConfig matching the strict schema. The
    # in-memory DotnetAiConfig is kept for downstream consumers in this
    # init call (skills/agents copy etc.) but is NOT serialised at init —
    # configure later writes the richer shape if/when the user provides
    # company/repos/etc.
    from dotnet_ai_kit.config import save_user_config  # noqa: PLC0415
    from dotnet_ai_kit.models import UserConfig  # noqa: PLC0415

    _user_cfg = UserConfig(
        enabled_hosts=list(ai_tools),
        plugin_version=__version__,
        permission_profile=config.permissions_level
        if config.permissions_level in {"minimal", "standard", "full", "mcp"}
        else None,
    )
    save_user_config(_user_cfg, config_path)
    if not json_output:
        console.print(f"  Created: {config_path.relative_to(target)}")

    # Step 5: Save project detection results
    # Feature 019 / commit 20 / B-3 / T143: emit the canonical ProjectMetadata
    # top-level shape per `schemas/project-yml.schema.json`. The legacy
    # DetectedProject info is preserved in-memory for downstream checks, but
    # what lands on disk follows the v1 contract.
    if detected:
        project_path = config_dir / "project.yml"

        # T147 derivation table: gather required ProjectMetadata fields from
        # CLI flags first, falling back to config / detection / defaults.
        from dotnet_ai_kit.config import save_project_metadata  # noqa: PLC0415
        from dotnet_ai_kit.models import (  # noqa: PLC0415
            ProjectMetadata,
            derive_architecture_branch,
        )

        pm_company = company or getattr(getattr(config, "company", None), "name", "") or ""
        pm_domain = domain or "Sales"  # placeholder when no flag/detection
        pm_side = (side or "server").lower()
        pm_type = (project_type or detected.project_type or "generic").lower()
        pm_branch = derive_architecture_branch(pm_type)
        pm_dotnet = detected.dotnet_version or "8.0"
        # detected_paths must be non-empty per schema minProperties:1
        pm_paths: dict[str, str] = {}
        for layer, p in (getattr(detected, "detected_paths", {}) or {}).items():
            if p:
                pm_paths[layer] = str(p)
        if not pm_paths:
            pm_paths = {"src": "src"}

        # T149 / T150: refuse to write if required fields cannot be derived.
        # Option A: clean — emit only when company is set (or rely on flag).
        if not pm_company:
            err_console.print(
                "[yellow]Warning:[/yellow] --company not provided and not "
                "available from config; using placeholder. Run "
                "`dotnet-ai configure --company <name>` to update."
            )
            pm_company = "<unset>"

        metadata = ProjectMetadata(
            company=pm_company,
            domain=pm_domain,
            side=pm_side,
            project_type=pm_type,
            architecture_branch=pm_branch,
            detected_paths=pm_paths,
            dotnet_version=pm_dotnet,
        )
        save_project_metadata(metadata, project_path)
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
    is_plugin = _detect_plugin_mode()

    # Load detected_paths from project.yml for skill token resolution (FR-009).
    _init_detected_paths = None
    _init_project_yml = target / ".dotnet-ai-kit" / "project.yml"
    if _init_project_yml.is_file():
        try:
            _init_proj_obj = load_project(_init_project_yml)
            _init_detected_paths = _init_proj_obj.detected_paths
        except Exception as exc:
            _verbose_log(verbose, f"Skipping detected paths from project.yml: {exc}")

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

        # Feature 019 / T042 / T043 / FR-005 / FR-006: plugin-native hosts
        # (claude, codex, cursor) get their commands/skills/agents from the
        # plugin install path — NOT bulk-copied into the solution.
        # The per-solution writes (`.dotnet-ai-kit/*`, `.claude/settings.json`)
        # land via the host adapter (see below) + the config write in step 4.
        if tool_name in PLUGIN_NATIVE_HOSTS:
            if not json_output:
                console.print(
                    f"  [dim]Plugin-native host: commands/skills/agents served from "
                    f"the {tool_display} plugin install (no per-solution copies).[/dim]"
                )
            # Cursor still emits per-rule `.cursor/rules/<name>.mdc` files
            # (T056 — already serves per-rule via copy_commands_cursor when
            # plugin install path is unavailable; preserve legacy behavior
            # for backwards compat). For Claude/Codex: zero bulk writes.
            if tool_name == "cursor" and not is_plugin:
                cmd_count = copy_commands_cursor(commands_source, target, tool_config, rules_source)
        elif tool_name in RENDER_ONLY_HOSTS:
            # Render-only hosts (copilot) — per FR-007, the host's render
            # adapter writes ONLY into the contract paths. NO bulk-copy.
            # The actual render call fires below in the per-tool host-adapter
            # section (see "Feature 019 / T070 / T072c: Copilot render path.").
            if not json_output:
                console.print(
                    "  [dim]Render-only host: writes via render contract paths only "
                    "(no bulk command/skill/agent copies).[/dim]"
                )
        else:
            # Fallback: keep legacy bulk copy for any future host registered
            # outside both PLUGIN_NATIVE_HOSTS and RENDER_ONLY_HOSTS.
            cmd_count = copy_commands(
                commands_source,
                target,
                tool_config,
                config,
                is_plugin=is_plugin,
            )
            rule_count = copy_rules(rules_source, target, tool_config)

            if skills_source.is_dir():
                skill_count = copy_skills(
                    skills_source,
                    target,
                    tool_config,
                    detected_paths=_init_detected_paths,
                )
            if agents_source.is_dir():
                agent_count = copy_agents(
                    agents_source,
                    target,
                    tool_config,
                    tool_name=tool_name,
                )

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

        # Feature 019 / T042: plugin-native hosts route through hosts/ adapter
        # for per-solution writes (currently `.claude/settings.json` for Claude
        # when permissions present). Codex / Cursor have no per-solution files.
        if tool_name == "claude":
            try:
                from dotnet_ai_kit.hosts.claude import ClaudeHost  # noqa: PLC0415

                _ch = ClaudeHost()
                _written = _ch.write_per_solution_files(
                    target,
                    permission_profile=config.permissions_level,
                )
                for p in _written:
                    if not json_output:
                        console.print(f"  Host adapter: wrote {p.relative_to(target)}")
            except Exception as _exc:
                _verbose_log(verbose, f"Claude host adapter skipped: {_exc}")

        # Feature 019 / T070 / T072c: Copilot render path.
        if tool_name == "copilot":
            try:
                from dotnet_ai_kit.hosts.copilot import CopilotHost  # noqa: PLC0415

                force_paths = [target / p for p in (force_render or [])]
                _coh = CopilotHost()
                _co_result = _coh.render(
                    target,
                    force_render_paths=force_paths,
                    plugin_root=_get_package_dir(),
                )
                for p in _co_result.written:
                    if not json_output:
                        console.print(f"  Copilot rendered: {p.relative_to(target)}")
                for p in _co_result.force_rendered:
                    if not json_output:
                        console.print(
                            f"  Copilot force-rendered: {p.relative_to(target)} (--force-render)"
                        )
                for p in _co_result.pending_user_consent:
                    err_console.print(
                        f"  [red]Copilot preserved (pre-existing):[/red] {p.relative_to(target)}\n"
                        f"    To overwrite, re-run with: --force-render {p.relative_to(target)}"
                    )
                # If unresolved conflicts AND user didn't pass any force-render,
                # exit non-zero per FR-008.
                if _co_result.has_conflicts and not force_render:
                    raise typer.Exit(code=1)
            except typer.Exit:
                raise
            except Exception as _exc:
                _verbose_log(verbose, f"Copilot render skipped: {_exc}")

    # Step 7b: Deploy architecture profile and hook (if project type known)
    _init_project_type = project_type
    if not _init_project_type and detected:
        _init_project_type = detected.project_type
    _init_confidence = "high" if project_type else (detected.confidence if detected else "low")

    _init_profile_path = None
    if _init_project_type:
        for tool_name in ai_tools:
            # Feature 019 / commit 18 / B-1: plugin-native hosts get the
            # architecture profile from the plugin install path (rules/conventions/
            # + rules/domain/) — not via per-solution `.claude/rules/`.
            if tool_name in PLUGIN_NATIVE_HOSTS:
                continue
            try:
                profile_path = copy_profile(
                    target,
                    tool_name,
                    _init_project_type,
                    _get_package_dir(),
                    confidence=_init_confidence,
                )
                if profile_path and not json_output:
                    console.print(
                        f"  Profile: {_init_project_type} -> {profile_path.relative_to(target)}"
                    )
                if profile_path and tool_name == "claude":
                    _init_profile_path = profile_path
            except (FileNotFoundError, ValueError):
                pass  # Profile not available — skip silently

        # Feature 019 / commit 18 / B-1: belt-and-braces — the hook block is
        # served by the plugin install path for plugin-native Claude, so even
        # if a stale profile exists on disk (pre-019 layout), don't re-embed.
        if _init_profile_path and "claude" in ai_tools and "claude" not in PLUGIN_NATIVE_HOSTS:
            try:
                if copy_hook(target, _init_profile_path, _get_package_dir()):
                    if not json_output:
                        console.print("  Hook: architecture enforcement hook deployed")
            except Exception as exc:
                _verbose_log(verbose, f"Skipping hook deployment: {exc}")

    # Step 8: Apply permissions to .claude/settings.json
    # Feature 019 / Blocker-1: gate on `claude in ai_tools` per spec.md:171
    # (init must write files only for selected hosts). Without this guard,
    # `dotnet-ai init --ai codex` would still create `.claude/settings.json`.
    if "claude" in ai_tools:
        try:
            if config.permissions_level == "full" and not json_output:
                console.print(
                    "\n[yellow bold]Warning:[/yellow bold] Full permission mode enables "
                    "bypassPermissions -- the AI assistant will execute all operations"
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
    else:
        # Still save config (without permissions side-effect) so config.yml is current.
        save_config(config, config_dir / "config.yml")

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
        # FR-032 / T044: also write manifest + .gitignore in JSON-output mode.
        try:
            _write_dotnet_ai_kit_gitignore(target)
            _finalize_manifest(target)
        except Exception as exc:
            _verbose_log(verbose, f"manifest write skipped: {exc}")
        return

    # Summary
    console.print(f"\n[green bold]dotnet-ai-kit initialized for {', '.join(ai_tools)}[/green bold]")

    # FR-032 / T044 / T045: generate .dotnet-ai-kit/.gitignore + manifest.json.
    try:
        _write_dotnet_ai_kit_gitignore(target)
        _finalize_manifest(target)
    except Exception as exc:
        _verbose_log(verbose, f"manifest write skipped: {exc}")

    # FR-019 / T068: detect codebase-memory-mcp and record outcome.
    try:
        _record_mcp_state(target, verbose=verbose)
    except Exception as exc:
        _verbose_log(verbose, f"mcp check skipped: {exc}")

    # T052 - Next-command suggestion
    console.print(
        "\nNext: Run [bold]dotnet-ai detect[/bold] then [bold]dotnet-ai configure[/bold].\n"
    )


# ---------------------------------------------------------------------------
# check command
# ---------------------------------------------------------------------------


@app.command("status")
def status(
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
    """Report the current state of dotnet-ai-kit in the project.

    NOTE: Feature 019 (commit 9): renamed from `check` to `status` because the
    `check` command is now the spec-mandated validation command per FR-017.
    The status command keeps the legacy informational behavior — tool tables,
    config status, project info.
    """
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

            ts = _get_tool_status(tool_name, tool_config, target)
            tools_status[tool_name] = {
                "status": "configured" if (ts["commands"] + ts["rules"]) > 0 else "empty",
                **ts,
            }
        data["tools"] = tools_status

        # Top-level: linked_from
        data["linked_from"] = getattr(config, "linked_from", None)

        # Top-level: detected_paths
        data["detected_paths"] = detected.detected_paths if detected else None

        # Top-level: linked_repos
        repo_roles_json = {
            "command": config.repos.command,
            "query": config.repos.query,
            "processor": config.repos.processor,
            "gateway": config.repos.gateway,
            "controlpanel": config.repos.controlpanel,
        }
        linked_repos_list = []
        for role, repo_path_val in repo_roles_json.items():
            if repo_path_val:
                if repo_path_val.startswith("github:"):
                    status_str = "remote"
                else:
                    status_str = "exists" if Path(repo_path_val).is_dir() else "missing"
                linked_repos_list.append(
                    {
                        "role": role,
                        "path": repo_path_val,
                        "status": status_str,
                    }
                )
        data["linked_repos"] = linked_repos_list

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
    table.add_column("Skills")
    table.add_column("Agents")
    table.add_column("Profile")
    table.add_column("Hook")

    for tool_name in config.ai_tools:
        try:
            tool_config = get_agent_config(tool_name)
        except ValueError:
            table.add_row(tool_name, "[red]unknown[/red]", "-", "-", "-", "-", "--", "--")
            continue

        display = tool_config.get("name", tool_name)
        ts = _get_tool_status(tool_name, tool_config, target)

        is_configured = (ts["commands"] + ts["rules"]) > 0
        status = "[green]configured[/green]" if is_configured else "[yellow]empty[/yellow]"
        profile_str = "deployed" if ts["profile"] else "--"
        hook_str = "deployed" if ts["hook"] else "--"
        table.add_row(
            display,
            status,
            str(ts["commands"]),
            str(ts["rules"]),
            str(ts["skills"]),
            str(ts["agents"]),
            profile_str,
            hook_str,
        )

    console.print(table)
    console.print()

    if verbose:
        for tool_name in config.ai_tools:
            try:
                tool_config = get_agent_config(tool_name)
            except ValueError:
                continue
            ts = _get_tool_status(tool_name, tool_config, target)
            rules_dir = tool_config.get("rules_dir", "")
            if ts["profile"]:
                console.print(f"  Profile: {rules_dir}/architecture-profile.md")
            if ts["hook"] and tool_name == "claude":
                console.print(f"  Hook: model={HOOK_MODEL}, timeout={HOOK_TIMEOUT_MS // 1000}s")

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

    # Linked from
    linked_from_val = getattr(config, "linked_from", None)
    if linked_from_val:
        config_panel_lines.append(f"  [green]Linked from:[/green] {linked_from_val}")
    else:
        config_panel_lines.append("  Linked from: N/A")

    # Detected paths
    if detected and detected.detected_paths:
        dp_count = len(detected.detected_paths)
        config_panel_lines.append(f"  Detected paths: {dp_count} categories")
    else:
        config_panel_lines.append("  Detected paths: not detected")

    # Linked repos — per-role status
    repo_roles = {
        "command": config.repos.command,
        "query": config.repos.query,
        "processor": config.repos.processor,
        "gateway": config.repos.gateway,
        "controlpanel": config.repos.controlpanel,
    }
    linked_repo_lines = []
    for role, repo_path_val in repo_roles.items():
        if repo_path_val:
            if repo_path_val.startswith("github:"):
                linked_repo_lines.append(f"    {role}: {repo_path_val} (remote)")
            else:
                exists = Path(repo_path_val).is_dir()
                status_label = "[green]exists[/green]" if exists else "[red]missing[/red]"
                linked_repo_lines.append(f"    {role}: {repo_path_val} ({status_label})")
    if linked_repo_lines:
        config_panel_lines.append("  Linked repos:")
        config_panel_lines.extend(linked_repo_lines)

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
                console.print(f"  [green]Permissions OK:[/green] {verify_result['actual']}")
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
    copilot: bool = typer.Option(
        False,
        "--copilot",
        help="Re-render only Copilot files (no-op for plugin-native hosts) per FR-015 / T072.",
    ),
    force_render: Optional[list[str]] = typer.Option(
        None,
        "--force-render",
        help=(
            "Explicit opt-in to overwrite a pre-existing Copilot file. "
            "Repeatable. Each value is a path relative to the project root. "
            "Per FR-008 / contract copilot-instructions:39-41 (T072c)."
        ),
    ),
) -> None:
    """Upgrade command and rule files to the latest CLI version.

    --copilot variant (FR-015 / T072): re-renders ONLY the .github/* files
    Copilot consumes, updating manifest entries with host_owner="copilot".
    Plugin-native hosts (claude/codex/cursor) are not touched.
    """
    target = Path(".").resolve()

    # Feature 019 / T072: --copilot variant short-circuits to a render-only path.
    if copilot:
        from dotnet_ai_kit.hosts.copilot import CopilotHost  # noqa: PLC0415

        config_dir = get_config_dir(target)
        if not config_dir.is_dir():
            err_console.print(
                "[yellow]dotnet-ai-kit is not initialized. Run 'dotnet-ai init' first.[/yellow]"
            )
            raise typer.Exit(code=1)

        force_render_paths = [target / p for p in (force_render or [])]
        copilot_host = CopilotHost()
        result = copilot_host.render(
            target,
            force_render_paths=force_render_paths,
            plugin_root=_get_package_dir(),
        )

        # T070: persist Copilot writes through manifest with host_owner="copilot"
        try:
            _record_copilot_renders_in_manifest(target, result.written + result.force_rendered)
        except Exception as exc:
            _verbose_log(verbose, f"manifest update skipped: {exc}")

        if json_output:
            print(
                json.dumps(
                    {
                        "command": "upgrade --copilot",
                        "written": [str(p) for p in result.written],
                        "force_rendered": [str(p) for p in result.force_rendered],
                        "preserved": [str(p) for p in result.preserved],
                        "pending_user_consent": [str(p) for p in result.pending_user_consent],
                    }
                )
            )
        else:
            for p in result.written:
                console.print(f"  [green]Rendered:[/green] {p.relative_to(target)}")
            for p in result.force_rendered:
                console.print(
                    f"  [yellow]Force-rendered:[/yellow] {p.relative_to(target)} (--force-render)"
                )
            for p in result.pending_user_consent:
                err_console.print(
                    f"  [red]Preserved (pending consent):[/red] {p.relative_to(target)}\n"
                    f"    To overwrite, re-run with: "
                    f"--force-render {p.relative_to(target)}"
                )
        # Exit non-zero when there are pending conflicts (per FR-008)
        if result.has_conflicts and not force_render:
            raise typer.Exit(code=1)
        return

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

    # T043a / FR-031 / SC-013: refuse to clobber user-modified managed files
    # without --force. Uses the manifest's recorded SHA-256 to detect drift.
    existing_manifest = read_manifest(target)
    if existing_manifest is not None:
        user_modified: list[str] = []
        for entry in existing_manifest.files:
            on_disk = target / entry.path
            if on_disk.is_file() and sha256_file(on_disk) != entry.sha256:
                user_modified.append(entry.path)
        if user_modified and not force:
            if json_output:
                print(
                    json.dumps(
                        {
                            "status": "user_modified",
                            "files": user_modified,
                            "hint": "rerun with --force to overwrite",
                        }
                    )
                )
            else:
                err_console.print(
                    "[red]Refusing to overwrite "
                    f"{len(user_modified)} user-modified managed file(s):[/red]"
                )
                for p in user_modified[:10]:
                    err_console.print(f"  • {p}")
                if len(user_modified) > 10:
                    err_console.print(f"  … and {len(user_modified) - 10} more")
                err_console.print(
                    "\nRe-run with [bold]--force[/bold] to proceed and overwrite. "
                    "A backup of the current state is written to "
                    "[bold].dotnet-ai-kit/backups/upgrade/[/bold] before any "
                    "managed file is touched."
                )
            raise typer.Exit(code=1)

    # Dry-run: don't write anything, including the manifest refresh.
    if dry_run:
        if json_output:
            print(
                json.dumps(
                    {
                        "status": "dry_run",
                        "old_version": old_version or "unknown",
                        "new_version": __version__,
                    }
                )
            )
        else:
            console.print(
                f"[bold][DRY-RUN][/bold] would upgrade "
                f"from {old_version or 'unknown'} to {__version__}. "
                "No changes were made.\n"
            )
        return

    if not json_output:
        console.print(f"Upgrading from {old_version or 'unknown'} to {__version__}...")

    # T043a / FR-031 / SC-013: atomic deploy. Snapshot the managed tree;
    # any exception inside the with-block restores byte-for-byte.
    with _atomic_upgrade(target):
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
        is_plugin = _detect_plugin_mode()

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

        # Load detected_paths for skill token resolution
        _upg_detected_paths = None
        _upg_project_yml = target / ".dotnet-ai-kit" / "project.yml"
        if _upg_project_yml.is_file():
            try:
                _upg_proj_obj = load_project(_upg_project_yml)
                _upg_detected_paths = _upg_proj_obj.detected_paths
            except Exception as exc:
                err_console.print(
                    f"[yellow]Warning: Failed to load detected paths: {exc}. "
                    "Run 'dotnet-ai configure' to retry.[/yellow]"
                )

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

            # Legacy `<dir>.bak` directory creation removed in favour of the
            # `_atomic_upgrade()` snapshot/restore at the top of this command
            # (T043a / SC-013). Maintaining two overlapping backup systems
            # leaked `.bak` directories past rollback because they sat outside
            # `_MANIFEST_SCAN_DIRS`. The container-managed snapshot is the
            # single source of rollback truth now.
            cmd_dir_rel = tool_config.get("commands_dir")
            rules_dir_rel = tool_config.get("rules_dir")

            # Feature 019 / T042 / FR-015: upgrade is a NO-OP for plugin-native
            # hosts (claude, codex, cursor in plugin mode) — the plugin install
            # path serves commands/skills/agents, not per-solution copies. The
            # only per-solution refresh is `.claude/settings.json` via the host
            # adapter. Exceptions propagate so `_atomic_upgrade` can rollback.
            if tool_name in PLUGIN_NATIVE_HOSTS:
                if tool_name == "claude":
                    from dotnet_ai_kit.hosts.claude import ClaudeHost  # noqa: PLC0415

                    ClaudeHost().write_per_solution_files(
                        target,
                        permission_profile=config.permissions_level,
                    )
                # Cursor's legacy `.cursor/rules/*.mdc` per-rule files are
                # refreshed by copy_commands_cursor only when not in plugin mode
                # (kept for backwards compat with old solutions; plugin mode
                # serves them via the cursor plugin install).
                if tool_name == "cursor" and not is_plugin:
                    total_cmds += copy_commands_cursor(
                        commands_source, target, tool_config, rules_source
                    )
            elif tool_name in RENDER_ONLY_HOSTS:
                # Codex round-2 sibling Blocker 1': render-only hosts (copilot)
                # must NOT bulk-copy on plain `upgrade`. Per FR-015, plain
                # `upgrade` is a no-op for Copilot; `upgrade --copilot` is the
                # explicit refresh entry point. Skip silently here.
                _verbose_log(
                    verbose,
                    f"Plain upgrade skips {tool_name} (render-only). "
                    "Use `dotnet-ai upgrade --copilot` to refresh Copilot files.",
                )
            else:
                # Unknown future host: keep legacy bulk-copy path.
                total_cmds += copy_commands(
                    commands_source,
                    target,
                    tool_config,
                    config,
                    is_plugin=is_plugin,
                )
                total_rules += copy_rules(rules_source, target, tool_config)

                # Re-copy skills and agents for non-plugin-native hosts only
                if skills_source.is_dir():
                    total_skills += copy_skills(
                        skills_source,
                        target,
                        tool_config,
                        detected_paths=_upg_detected_paths,
                    )
                if agents_source.is_dir():
                    total_agents += copy_agents(
                        agents_source,
                        target,
                        tool_config,
                        tool_name=tool_name,
                    )

        # Deploy architecture profile and hook
        _upgrade_profile_path = None
        project_yml = target / ".dotnet-ai-kit" / "project.yml"
        if project_yml.is_file():
            try:
                _proj_obj = load_project(project_yml)
                _project_type = _proj_obj.project_type or "generic"
                _confidence = _proj_obj.confidence or "low"
                for tool_name in config.ai_tools:
                    # Feature 019 / commit 18 / B-1: skip legacy profile copy
                    # for plugin-native hosts (served from plugin install path).
                    if tool_name in PLUGIN_NATIVE_HOSTS:
                        continue
                    try:
                        _p = copy_profile(
                            target,
                            tool_name,
                            _project_type,
                            _get_package_dir(),
                            confidence=_confidence,
                        )
                        if _p and tool_name == "claude":
                            _upgrade_profile_path = _p
                    except (FileNotFoundError, ValueError):
                        pass
            except Exception as exc:
                err_console.print(
                    f"[yellow]Warning: Profile deployment failed: {exc}. "
                    "Run 'dotnet-ai configure' to retry.[/yellow]"
                )

        # Feature 019 / commit 18 / B-1: belt-and-braces — never embed a stale
        # PreToolUse `type: prompt` hook for plugin-native Claude.
        if (
            _upgrade_profile_path
            and "claude" in config.ai_tools
            and "claude" not in PLUGIN_NATIVE_HOSTS
        ):
            try:
                copy_hook(target, _upgrade_profile_path, _get_package_dir())
            except Exception as exc:
                err_console.print(
                    f"[yellow]Warning: Hook deployment failed: {exc}. "
                    "Run 'dotnet-ai configure' to retry.[/yellow]"
                )

        # Deploy tooling to linked secondary repos (FR-012)
        has_local_repos = any(
            getattr(config.repos, r, None)
            and not getattr(config.repos, r, "").startswith("github:")
            for r in ("command", "query", "processor", "gateway", "controlpanel")
        )
        if has_local_repos:
            upgrade_branch = f"chore/dotnet-ai-kit-upgrade-{__version__}"
            try:
                deploy_to_linked_repos(
                    target,
                    config,
                    __version__,
                    _get_package_dir(),
                    branch_name=upgrade_branch,
                )
            except Exception as exc:
                err_console.print(
                    f"[yellow]Warning: Multi-repo deployment failed: {exc}. "
                    "Run 'dotnet-ai configure' to retry.[/yellow]"
                )

        # Update version file
        version_path.write_text(__version__, encoding="utf-8")

        # Always re-apply permissions to ensure settings.json matches config.yml.
        # Codex round-2 sibling Blocker 1': gate on `claude in config.ai_tools`
        # so `upgrade` on a Copilot-only / Codex-only solution does NOT create
        # `.claude/settings.json` (FR-016 / spec.md:171).
        if config.permissions_level and "claude" in config.ai_tools:
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

        # FR-032 / T044a / T045: generate / refresh .dotnet-ai-kit/.gitignore + manifest.
        try:
            _write_dotnet_ai_kit_gitignore(target)
            _finalize_manifest(target)
        except Exception as exc:
            _verbose_log(verbose, f"manifest write skipped: {exc}")

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

_REPO_ROLES = ("command", "query", "processor", "gateway", "controlpanel")

_REPO_HEURISTICS: list[tuple[str, str]] = [
    # (glob/grep pattern hint, classified type)
    ("AggregateRoot", "command"),
    ("EventSourcedAggregate", "command"),
    ("IRequestHandler<Event<", "query"),
    ("EventHandler", "query"),
    (".razor", "controlpanel"),
    ("Protos/", "gateway"),
    ("IHostedService", "processor"),
]


def _scan_sibling_repos(target: Path) -> dict[str, str]:
    """Scan ../ for sibling git repos and attempt quick classification.

    Returns a dict of {directory_name: detected_type_or_'unclassified'}.
    """
    parent = target.parent
    if not parent.is_dir():
        return {}

    results: dict[str, str] = {}
    count = 0
    for child in sorted(parent.iterdir()):
        if count >= 20:
            break
        if child == target or not child.is_dir():
            continue
        if not (child / ".git").is_dir():
            continue
        # Check for .sln, .slnx, or .csproj
        has_dotnet = (
            any(child.glob("*.sln")) or any(child.glob("*.slnx")) or any(child.glob("**/*.csproj"))
        )
        if not has_dotnet:
            continue
        count += 1
        # Quick classification by grepping for key patterns
        classified = "unclassified"
        for pattern, repo_type in _REPO_HEURISTICS:
            # Check if pattern appears in any .cs or .csproj file
            for ext in ("**/*.cs", "**/*.csproj"):
                for f in child.glob(ext):
                    try:
                        content = f.read_text(encoding="utf-8", errors="ignore")
                        if pattern in content:
                            classified = repo_type
                            break
                    except OSError:
                        continue
                if classified != "unclassified":
                    break
            if classified != "unclassified":
                break
        results[child.name] = classified
    return results


def _configure_repos(
    config: "DotnetAiConfig",
    target: Path,
    console: Console,
    verbose: bool,
) -> None:
    """Interactive repo configuration with auto-detection."""

    detected = _scan_sibling_repos(target)
    if detected:
        console.print("  [dim]Detected sibling repos:[/dim]")
        for name, rtype in detected.items():
            console.print(f"    ../{name} -> {rtype}")
        console.print()

    from dotnet_ai_kit.models import ReposConfig

    repo_updates: dict[str, str | None] = {}
    for role in _REPO_ROLES:
        current = getattr(config.repos, role, None)
        # Try to find a detected match for this role
        suggestion = current or ""
        if not suggestion:
            for name, rtype in detected.items():
                if rtype == role:
                    suggestion = f"../{name}"
                    break

        value = Prompt.ask(
            f"  {role.capitalize()} repo (path, GitHub URL, or Enter to skip)",
            default=suggestion,
        )
        value = value.strip() if value else ""
        repo_updates[role] = value or None

    # Reconstruct ReposConfig to trigger pydantic validators (URL normalization)
    current_repos = config.repos.model_dump()
    current_repos.update(repo_updates)
    config.repos = ReposConfig(**current_repos)


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
    repos: Optional[str] = typer.Option(
        None,
        "--repos",
        help="Comma-separated repo mappings (e.g. command=../cmd,query=../qry).",
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

    # Guard: require init before configure (skip when --dry-run)
    if not dry_run and not (target / ".dotnet-ai-kit").is_dir():
        err_console.print(
            "[red]dotnet-ai-kit is not initialized. "
            "Run 'dotnet-ai init' first, then 'dotnet-ai configure'.[/red]"
        )
        raise typer.Exit(code=1)

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
        if repos is not None:
            repo_updates: dict[str, str | None] = {}
            for mapping in repos.split(","):
                mapping = mapping.strip()
                if "=" in mapping:
                    role, path = mapping.split("=", 1)
                    role = role.strip().lower()
                    if role in _REPO_ROLES:
                        repo_updates[role] = path.strip() or None
            # Reconstruct ReposConfig to trigger pydantic validators (URL normalization)
            from dotnet_ai_kit.models import ReposConfig

            current = config.repos.model_dump()
            current.update(repo_updates)
            config.repos = ReposConfig(**current)
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

        # Repo configuration (microservice mode only)
        project_path = config_dir / "project.yml"
        is_microservice = False
        if project_path.is_file():
            try:
                proj = load_project(project_path)
                is_microservice = proj.mode == "microservice"
            except (FileNotFoundError, ValueError):
                pass

        if is_microservice:
            console.print("\n[bold]Repository Paths[/bold] (microservice mode)\n")
            _configure_repos(config, target, console, verbose)

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

        # AI tools multi-select (T041 / T133 commit 17, B-6) — all 4 hosts per FR-016
        current_tools = config.ai_tools or []
        tools_result = questionary.checkbox(
            "AI tools to configure:",
            choices=[
                questionary.Choice(
                    "Claude Code",
                    value="claude",
                    checked="claude" in current_tools,
                ),
                questionary.Choice(
                    "Codex CLI",
                    value="codex",
                    checked="codex" in current_tools,
                ),
                questionary.Choice(
                    "Cursor",
                    value="cursor",
                    checked="cursor" in current_tools,
                ),
                questionary.Choice(
                    "GitHub Copilot",
                    value="copilot",
                    checked="copilot" in current_tools,
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
        repo_count = sum(1 for r in _REPO_ROLES if getattr(config.repos, r, None))
        console.print(f"  Repos: {repo_count} of {len(_REPO_ROLES)} configured")
        console.print(f"  Config path: {config_path}")
        console.print("\n[dim]No changes were made (dry run).[/dim]")
        return

    # Save config
    config_dir.mkdir(parents=True, exist_ok=True)
    save_config(config, config_path)

    # Apply permissions to .claude/settings.json.
    # Codex round-2 sibling Blocker 2': gate on `claude in config.ai_tools`
    # per FR-016 / spec.md:171 (configure writes files only for selected hosts).
    if "claude" in config.ai_tools:
        try:
            if config.permissions_level == "full" and not json_output:
                console.print(
                    "\n[yellow bold]Warning:[/yellow bold] Full permission mode enables "
                    "bypassPermissions -- the AI assistant will execute all operations"
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

    # Re-copy commands so style changes take effect immediately
    commands_source = _find_commands_source()
    rules_source = _find_rules_source()
    is_plugin = _detect_plugin_mode()
    total_cmds = 0

    for tool_name in config.ai_tools:
        try:
            tool_config = get_agent_config(tool_name)
        except ValueError:
            continue

        # Codex round-2 sibling Blocker 2': route plugin-native + render-only
        # hosts away from the legacy bulk-copy branch per FR-016 + FR-007.
        if tool_name in PLUGIN_NATIVE_HOSTS or tool_name in RENDER_ONLY_HOSTS:
            if tool_name == "cursor" and not is_plugin:
                # Cursor's per-rule .mdc fallback for non-plugin solutions
                total_cmds += copy_commands_cursor(
                    commands_source,
                    target,
                    tool_config,
                    rules_source,
                )
            # All other plugin-native / render-only paths: NO bulk-copy here.
            continue

        # Legacy bulk-copy path (kept for hypothetical future non-native hosts)
        total_cmds += copy_commands(
            commands_source,
            target,
            tool_config,
            config,
            is_plugin=is_plugin,
        )

    if not json_output and total_cmds:
        console.print(f"  Commands: {total_cmds} files updated (style: {config.command_style})")

    # Re-deploy rules, skills, and agents
    skills_source = _find_skills_source()
    agents_source = _find_agents_source()

    # Load detected_paths for skill token resolution
    _cfg_detected_paths = None
    _cfg_project_yml = target / ".dotnet-ai-kit" / "project.yml"
    if _cfg_project_yml.is_file():
        try:
            _cfg_proj_obj = load_project(_cfg_project_yml)
            _cfg_detected_paths = _cfg_proj_obj.detected_paths
        except Exception as exc:
            _verbose_log(verbose, f"Skipping detected paths from project.yml: {exc}")

    for tool_name in config.ai_tools:
        try:
            tool_config = get_agent_config(tool_name)
        except ValueError:
            continue

        # Codex round-2 sibling Blocker 2': skip rules/skills/agents bulk-copy
        # for plugin-native AND render-only hosts (per FR-016 + FR-007).
        if tool_name in PLUGIN_NATIVE_HOSTS or tool_name in RENDER_ONLY_HOSTS:
            continue

        copy_rules(rules_source, target, tool_config)

        if skills_source.is_dir():
            copy_skills(
                skills_source,
                target,
                tool_config,
                detected_paths=_cfg_detected_paths,
            )
        if agents_source.is_dir():
            copy_agents(
                agents_source,
                target,
                tool_config,
                tool_name=tool_name,
            )

    if not json_output:
        console.print("  Rules, skills, and agents refreshed.")

    # Deploy architecture profile based on detected project type
    project_yml = target / ".dotnet-ai-kit" / "project.yml"
    project_type = "generic"
    confidence = "low"
    if project_yml.is_file():
        try:
            _cfg_proj2 = load_project(project_yml)
            project_type = _cfg_proj2.project_type or "generic"
            confidence = _cfg_proj2.confidence or "low"
        except Exception as exc:
            _verbose_log(verbose, f"Skipping profile type from project.yml: {exc}")

    _deployed_profile_path = None
    for tool_name in config.ai_tools:
        # Feature 019 / commit 18 / B-1: skip legacy profile copy for
        # plugin-native hosts (served from plugin install path).
        if tool_name in PLUGIN_NATIVE_HOSTS:
            continue
        try:
            profile_path = copy_profile(
                target,
                tool_name,
                project_type,
                _get_package_dir(),
                confidence=confidence,
            )
            if profile_path and not json_output:
                console.print(f"  Profile: {project_type} -> {profile_path.relative_to(target)}")
            if profile_path and tool_name == "claude":
                _deployed_profile_path = profile_path
        except (FileNotFoundError, ValueError):
            pass  # Profile not available yet — skip silently

    # Deploy Claude Code prompt hook if profile was deployed.
    # Feature 019 / commit 18 / B-1: belt-and-braces — skip for plugin-native.
    if (
        _deployed_profile_path
        and "claude" in config.ai_tools
        and "claude" not in PLUGIN_NATIVE_HOSTS
    ):
        try:
            if copy_hook(target, _deployed_profile_path, _get_package_dir()):
                if not json_output:
                    console.print("  Hook: architecture enforcement hook deployed")
        except Exception as exc:
            _verbose_log(verbose, f"Skipping hook deployment: {exc}")

    # Deploy tooling to linked secondary repos (FR-008)
    has_local_repos = any(
        getattr(config.repos, r, None) and not getattr(config.repos, r, "").startswith("github:")
        for r in ("command", "query", "processor", "gateway", "controlpanel")
    )
    if has_local_repos:
        try:
            results = deploy_to_linked_repos(
                target,
                config,
                __version__,
                _get_package_dir(),
            )
            if not json_output:
                for r in results:
                    status_color = {
                        "deployed": "green",
                        "upgraded": "green",
                        "skipped": "yellow",
                        "failed": "red",
                    }.get(r["status"], "dim")
                    console.print(
                        f"  Linked repo {r['repo']}: "
                        f"[{status_color}]{r['status']}[/{status_color}]"
                        f" ({r['reason']})"
                    )
        except Exception as exc:
            if not json_output:
                err_console.print(f"[yellow]Multi-repo deployment error: {exc}[/yellow]")

    # T051 - JSON output mode
    if json_output:
        data: dict = {
            "company": config.company.name,
            "github_org": config.company.github_org,
            "default_branch": config.company.default_branch,
            "permissions_level": config.permissions_level,
            "ai_tools": config.ai_tools,
            "command_style": config.command_style,
            "config_path": str(config_path),
            "status": "ok",
        }
        if config.permissions_level == "full":
            data["warnings"] = [
                "bypassPermissions enabled -- all operations run without confirmation"
            ]
        print(json.dumps(data))
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
    repo_count = sum(1 for r in _REPO_ROLES if getattr(config.repos, r, None))
    summary.add_row("Repos", f"{repo_count} of {len(_REPO_ROLES)} configured")
    console.print(summary)

    # Validate development tools
    _validate_tools(console, verbose=verbose)

    # FR-019 / T068a: re-check codebase-memory-mcp and refresh config.yml.
    try:
        _record_mcp_state(target, verbose=verbose)
    except Exception as exc:
        _verbose_log(verbose, f"mcp check skipped: {exc}")

    # T052 - Next-command suggestion
    console.print("\nNext: Run [bold]dotnet-ai check[/bold] to verify your setup.\n")


# ---------------------------------------------------------------------------
# Feature 019 / commit 14b / T118: `dotnet-ai render` command
# ---------------------------------------------------------------------------


@app.command()
def render(
    kind: str = typer.Argument(..., help="One of: `skill`, `rule`."),
    name: str = typer.Argument(..., help="Skill or rule name (no .md extension)."),
    host: str = typer.Option(
        "claude",
        "--host",
        help="Output shape. v1 supports `claude` only.",
    ),
    project_path: str = typer.Option(
        ".",
        "--project",
        help="Project root containing .dotnet-ai-kit/project.yml (defaults to cwd).",
    ),
) -> None:
    """Render a skill or rule with current project.yml metadata substituted.

    Per FR-019 / SC-012 / US6 / contracts/render-cli.contract.md.

    Exit codes:
      0  Success
      20 Unsupported --host shape in v1
      21 Skill or rule not found
      22 project.yml missing or corrupt
      23 Substitution failure (metadata key absent)
    """
    from dotnet_ai_kit import render as _render

    project_root = Path(project_path).resolve()
    plugin_root = _get_package_dir()

    if kind not in ("skill", "rule"):
        err_console.print(f"[red]<kind> must be 'skill' or 'rule', got {kind!r}[/red]")
        raise typer.Exit(code=2)

    try:
        if kind == "skill":
            output = _render.render_skill(name, plugin_root, project_root, host=host)
        else:
            output = _render.render_rule(name, plugin_root, project_root, host=host)
    except _render.UnsupportedHost as exc:
        err_console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(code=exc.exit_code) from None
    except _render.SkillOrRuleNotFound as exc:
        err_console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(code=exc.exit_code) from None
    except _render.ProjectMetadataMissing as exc:
        err_console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(code=exc.exit_code) from None
    except _render.SubstitutionFailure as exc:
        err_console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(code=exc.exit_code) from None

    # Use plain sys.stdout to bypass Rich color codes — keeps output
    # consumable by downstream pipes.
    import sys as _sys

    _sys.stdout.write(output)
    _sys.stdout.flush()


# ---------------------------------------------------------------------------
# Feature 019 / commit 10 / T099: `dotnet-ai migrate` command
# ---------------------------------------------------------------------------


@app.command()
def migrate(
    project_path: str = typer.Argument(
        ".",
        help="Project root to migrate (defaults to current directory).",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print classification report and planned actions without mutating files (Constitution V).",
    ),
    include_modified: bool = typer.Option(
        False,
        "--include-modified",
        help="Explicit opt-in to also remove user-modified files (per FR-022). Default: preserve in place.",
    ),
    host: str = typer.Option(
        "",
        "--host",
        help="Scope migration to files with host_owner == <host>. Default: all hosts.",
    ),
    include_linked: bool = typer.Option(
        False,
        "--include-linked",
        help="Also migrate legacy copies in linked secondary repos (FR-033 / T096).",
    ),
) -> None:
    """Migrate legacy per-solution copies to the plugin-native architecture.

    Per FR-018, FR-020-FR-025 / US4 / contracts/migrate-cli.contract.md.

    For each file in `.dotnet-ai-kit/manifest.json`:
    - **clean** (hash matches manifest): MOVE to `.dotnet-ai-kit/backups/migrate/<timestamp>/`
    - **user-modified** (hash differs): PRESERVE in place unless `--include-modified`
    - **missing**: already gone; will be removed from updated manifest

    Backups use 3-keep rotation per FR-023. Does NOT re-render Copilot
    files (FR-024 — that's `upgrade --copilot`'s job). Does NOT delete
    files outright (FR-021 — always moves to backup).

    Per FR-033 / SC-014 / T096: when `--include-linked` is set, also
    iterates the primary's `config.repos.*` linked secondaries and runs
    migrate against each (subject to the same user-modified preservation
    rules per FR-022).
    """
    import shutil as _shutil
    from datetime import datetime, timezone

    from dotnet_ai_kit.manifest import (
        classify_file,
        manifest_path,
        read_manifest,
        utc_now_iso,
        write_manifest,
    )

    target = Path(project_path).resolve()

    manifest_p = manifest_path(target)
    if not manifest_p.is_file():
        err_console.print(
            f"[red]manifest.json not found at {manifest_p}[/red]\n"
            f"Run [bold]dotnet-ai init {target}[/bold] first to (re)create it."
        )
        raise typer.Exit(code=1)

    manifest = read_manifest(target)
    assert manifest is not None  # narrowed

    # Build classification per file
    actions: dict[str, list] = {
        "move": [],  # (DeployedFile, target_in_backup)
        "preserve": [],  # DeployedFile
        "remove_modified": [],  # DeployedFile (only when --include-modified)
        "drop_from_manifest": [],  # DeployedFile (file already missing on disk)
    }

    host_filter = host.lower() if host else None

    for entry in manifest.files:
        # Host scoping
        if host_filter and (entry.host_owner or "").lower() != host_filter:
            continue

        classification = classify_file(target, entry)
        if classification == "missing":
            actions["drop_from_manifest"].append(entry)
        elif classification == "clean":
            actions["move"].append(entry)
        elif classification == "user-modified":
            if include_modified:
                actions["remove_modified"].append(entry)
            else:
                actions["preserve"].append(entry)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_folder = target / ".dotnet-ai-kit" / "backups" / "migrate" / timestamp

    # --- Print classification report ---
    console.print(f"\n[bold]dotnet-ai migrate{' (dry-run)' if dry_run else ''}[/bold]")
    console.print("=" * 32)
    console.print(f"Manifest: {manifest_p} (schema_version={manifest.schema_version})")

    if actions["move"]:
        console.print(f"\n  {len(actions['move'])} files MOVE to {backup_folder}/")
        for entry in actions["move"][:10]:
            console.print(f"    {entry.path}    [clean, host_owner={entry.host_owner or '-'}]")
        if len(actions["move"]) > 10:
            console.print(f"    ... ({len(actions['move']) - 10} more)")

    if actions["preserve"]:
        console.print(f"\n  {len(actions['preserve'])} files PRESERVE in place (user-modified):")
        for entry in actions["preserve"][:5]:
            console.print(
                f"    {entry.path}    [host_owner={entry.host_owner or '-'}, hash mismatch]"
            )
        if len(actions["preserve"]) > 5:
            console.print(f"    ... ({len(actions['preserve']) - 5} more)")

    if actions["remove_modified"]:
        console.print(
            f"\n  {len(actions['remove_modified'])} files MOVE to backup "
            "(--include-modified opt-in)"
        )

    if actions["drop_from_manifest"]:
        console.print(
            f"\n  {len(actions['drop_from_manifest'])} files already missing "
            "(will be removed from manifest):"
        )
        for entry in actions["drop_from_manifest"][:3]:
            console.print(f"    {entry.path}")

    if dry_run:
        console.print(f"\n[dim]To apply, run: dotnet-ai migrate {target}[/dim]")
        if actions["preserve"]:
            console.print(
                f"[dim]To also remove user-modified files: "
                f"dotnet-ai migrate {target} --include-modified[/dim]"
            )
        return

    # --- Apply ---
    moved_paths: list[Path] = []
    backup_folder.mkdir(parents=True, exist_ok=True)

    to_move = actions["move"] + actions["remove_modified"]
    for entry in to_move:
        src = target / entry.path
        dst = backup_folder / entry.path
        dst.parent.mkdir(parents=True, exist_ok=True)
        _shutil.move(str(src), str(dst))
        moved_paths.append(src)

    # 3-keep rotation (FR-023)
    migrate_backups_root = target / ".dotnet-ai-kit" / "backups" / "migrate"
    if migrate_backups_root.is_dir():
        existing = sorted(
            (p for p in migrate_backups_root.iterdir() if p.is_dir()),
            key=lambda p: p.name,
        )
        excess = len(existing) - 3
        if excess > 0:
            for old in existing[:excess]:
                _shutil.rmtree(old, ignore_errors=True)

    # Update manifest: keep only preserved/missing files; bump schema to v2
    moved_path_set = {entry.path for entry in to_move + actions["drop_from_manifest"]}
    remaining = [f for f in manifest.files if f.path not in moved_path_set]

    new_manifest = manifest.model_copy(
        update={
            "schema_version": "2",
            "files": remaining,
            "last_migrate_at": utc_now_iso(),
        }
    )
    write_manifest(target, new_manifest)

    console.print(f"\n[green]Migration complete. Backup at {backup_folder}.[/green]")
    if actions["preserve"]:
        console.print(
            f"[yellow]{len(actions['preserve'])} user-modified files preserved in place.[/yellow]"
        )

    # Feature 019 / T096 / FR-033 / SC-014: linked-secondary migration.
    if include_linked:
        try:
            from dotnet_ai_kit.config import load_config  # noqa: PLC0415

            cfg_path = target / ".dotnet-ai-kit" / "config.yml"
            if cfg_path.is_file():
                cfg = load_config(cfg_path)
                linked: list[Path] = []
                for role in ("command", "query", "processor", "gateway", "controlpanel"):
                    repo_str = getattr(cfg.repos, role, None)
                    if not repo_str or repo_str.startswith("github:"):
                        continue
                    p = Path(repo_str)
                    if p.is_dir() and (p / ".dotnet-ai-kit" / "manifest.json").is_file():
                        linked.append(p)
                if linked:
                    console.print(
                        f"\n[bold]Linked secondaries — applying migrate ({len(linked)}):[/bold]"
                    )
                    for sec in linked:
                        console.print(f"  -> {sec}")
                        # Recursive in-process: call migrate's core logic again.
                        # Use a fresh manifest scope, no nested --include-linked
                        # to prevent loops.
                        try:
                            sec_manifest = read_manifest(sec)
                            if sec_manifest is None:
                                continue
                            sec_backup = sec / ".dotnet-ai-kit" / "backups" / "migrate" / timestamp
                            sec_backup.mkdir(parents=True, exist_ok=True)
                            sec_moved = []
                            sec_preserved = []
                            for sec_entry in sec_manifest.files:
                                if (
                                    host_filter
                                    and (sec_entry.host_owner or "").lower() != host_filter
                                ):
                                    continue
                                klass = classify_file(sec, sec_entry)
                                if klass == "clean":
                                    src = sec / sec_entry.path
                                    dst = sec_backup / sec_entry.path
                                    dst.parent.mkdir(parents=True, exist_ok=True)
                                    if src.is_file():
                                        _shutil.move(str(src), str(dst))
                                        sec_moved.append(sec_entry.path)
                                elif klass == "user-modified":
                                    if include_modified:
                                        src = sec / sec_entry.path
                                        dst = sec_backup / sec_entry.path
                                        dst.parent.mkdir(parents=True, exist_ok=True)
                                        if src.is_file():
                                            _shutil.move(str(src), str(dst))
                                            sec_moved.append(sec_entry.path)
                                    else:
                                        sec_preserved.append(sec_entry.path)
                            console.print(
                                f"     moved {len(sec_moved)}, preserved {len(sec_preserved)}"
                            )
                            # Update secondary manifest
                            sec_remaining = [
                                f for f in sec_manifest.files if f.path not in set(sec_moved)
                            ]
                            sec_new = sec_manifest.model_copy(
                                update={
                                    "schema_version": "2",
                                    "files": sec_remaining,
                                    "last_migrate_at": utc_now_iso(),
                                }
                            )
                            write_manifest(sec, sec_new)
                        except Exception as exc:
                            console.print(f"     [yellow]skipped: {exc}[/yellow]")
        except Exception as exc:
            console.print(f"\n[yellow]linked-secondary migration skipped: {exc}[/yellow]")


# ---------------------------------------------------------------------------
# Feature 019 / commit 9 / T108: `dotnet-ai check` command
# ---------------------------------------------------------------------------


@app.command()
def check(
    project_path: str = typer.Argument(
        ".",
        help="Project root to validate (defaults to current directory).",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Per-check breakdown with status, path, details.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Machine-readable JSON output per check-cli.contract.md:64-80.",
    ),
    host: str = typer.Option(
        "",
        "--host",
        help="Scope checks to a single host (claude/codex/cursor/copilot). Default: all enabled_hosts.",
    ),
) -> None:
    """Validate the dotnet-ai-kit install + project state (feature 019 / FR-017).

    Runs the 6 check classes per `contracts/check-cli.contract.md`:
    1. Plugin install per configured host (filesystem inspection per clarify Q3)
    2. External binary prerequisites (csharp-ls on PATH)
    3. project.yml schema validity
    4. Detected-path correctness
    5. manifest.json integrity (sha256 hashes)
    6. Copilot render freshness

    Exit codes per the contract (lowest code wins on multiple failures):
      0  All checks pass
      10 Plugin install missing
      11 External binary missing
      12 project.yml schema
      13 Detected-path inconsistency
      14 Manifest integrity
      15 Copilot render stale
      16 Host symmetric / loader failure
      99 Unknown error

    Read-only — never mutates files. No network calls. No telemetry.
    """
    import json as _json
    import shutil as _shutil
    import time as _time

    from dotnet_ai_kit.config import get_config_dir as _get_cfg_dir
    from dotnet_ai_kit.config import load_project as _load_project
    from dotnet_ai_kit.hosts import available_hosts, get_host
    from dotnet_ai_kit.manifest import integrity_check as _integrity_check

    start_ts = _time.time()
    target = Path(project_path).resolve()
    checks: list[dict] = []
    exit_code = 0

    def _add(name: str, status: str, details: str = "") -> None:
        checks.append({"name": name, "status": status, "details": details})

    def _fail(name: str, details: str, code: int) -> None:
        nonlocal exit_code
        _add(name, "fail", details)
        if exit_code == 0 or code < exit_code:
            exit_code = code

    # 1. Plugin install per configured host (exit 10 on miss)
    if host:
        host_names = [host.lower()]
    else:
        config_dir = _get_cfg_dir(target)
        cfg_file = config_dir / "config.yml"
        if cfg_file.is_file():
            try:
                from dotnet_ai_kit.config import load_user_config as _load_user_cfg

                user_cfg = _load_user_cfg(cfg_file)
                host_names = user_cfg.enabled_hosts or available_hosts()
            except Exception:
                host_names = available_hosts()
        else:
            host_names = available_hosts()

    for host_name in host_names:
        try:
            host_obj = get_host(host_name)
        except KeyError:
            _fail(
                f"{host_name}_plugin_install",
                f"host '{host_name}' not registered",
                16,
            )
            continue

        status_obj = host_obj.verify_install()
        if status_obj.installed:
            _add(
                f"{host_name}_plugin_install",
                "pass",
                status_obj.notes or "installed",
            )
        else:
            # Copilot's "install" is just .github/ presence — treat absence as
            # informational rather than a hard fail at exit 10.
            if host_name == "copilot":
                _add(
                    f"{host_name}_plugin_install",
                    "skip",
                    "Copilot is render-only — no plugin install required",
                )
            else:
                _fail(
                    f"{host_name}_plugin_install",
                    status_obj.notes or "not installed",
                    10,
                )

    # 2. External binary prerequisites (exit 11 on miss)
    csharp_ls = _shutil.which("csharp-ls")
    if csharp_ls:
        _add("csharp_ls_binary", "pass", csharp_ls)
    else:
        _fail(
            "csharp_ls_binary",
            "csharp-ls binary not on PATH — install: https://github.com/razzmatazz/csharp-language-server",
            11,
        )

    # 3. project.yml schema (exit 12 on miss)
    # Feature 019 / commit 20 / B-4 / T153: raw-validate the YAML against
    # `schemas/project-yml.schema.json` BEFORE loading into the model. This
    # catches additionalProperties / type / required-field violations that the
    # pydantic loader would silently coerce or ignore.
    project_yml = _get_cfg_dir(target) / "project.yml"
    if project_yml.is_file():
        import json as _json  # noqa: PLC0415

        import jsonschema as _jsonschema  # noqa: PLC0415
        import yaml as _yaml  # noqa: PLC0415

        schema_path = _get_package_dir() / "schemas" / "project-yml.schema.json"
        if not schema_path.is_file():
            # Fallback: scripts may run outside the installed package
            schema_path = (
                Path(__file__).resolve().parents[2] / "schemas" / "project-yml.schema.json"
            )

        try:
            raw_data = _yaml.safe_load(project_yml.read_text(encoding="utf-8")) or {}
        except _yaml.YAMLError as exc:
            _fail("project_yml_schema", f"YAML parse error: {exc}", 12)
            raw_data = None

        if raw_data is not None and schema_path.is_file():
            # Skip strict raw-validate for the legacy `detected:`-nested shape;
            # the pydantic loader handles that path via `load_project_metadata`'s
            # back-compat hoisting (T152). Raw-validate only the canonical v1
            # top-level shape.
            is_legacy_nested = isinstance(raw_data, dict) and "detected" in raw_data
            if not is_legacy_nested:
                try:
                    schema = _json.loads(schema_path.read_text(encoding="utf-8"))
                    _jsonschema.validate(instance=raw_data, schema=schema)
                except _jsonschema.ValidationError as exc:
                    # FR-031 maps schema violations to exit class 12
                    _fail(
                        "project_yml_schema",
                        f"schema violation at "
                        f"{'/'.join(str(p) for p in exc.absolute_path)}: {exc.message}",
                        12,
                    )
                    raw_data = None

        if raw_data is not None:
            try:
                _load_project(project_yml)
                _add("project_yml_schema", "pass", str(project_yml))
            except Exception as exc:
                _fail("project_yml_schema", f"{exc}", 12)
    else:
        _add(
            "project_yml_schema",
            "skip",
            "project.yml not found (run `dotnet-ai detect` to create it)",
        )

    # 4. Detected-path correctness (exit 13 on miss)
    if project_yml.is_file():
        try:
            detected = _load_project(project_yml)
            missing_paths = []
            for key, value in (detected.detected_paths or {}).items():
                resolved = target / value
                if not resolved.exists():
                    missing_paths.append(f"{key}={value}")
            if missing_paths:
                _fail(
                    "detected_paths",
                    f"missing on disk: {', '.join(missing_paths)}",
                    13,
                )
            else:
                _add(
                    "detected_paths",
                    "pass",
                    f"{len(detected.detected_paths or {})} paths exist",
                )
        except Exception as exc:
            _add("detected_paths", "skip", f"could not load: {exc}")
    else:
        _add("detected_paths", "skip", "project.yml not found")

    # 5. manifest.json integrity (exit 14 on miss)
    integrity = _integrity_check(target)
    if integrity.ok:
        _add(
            "manifest_integrity",
            "pass",
            "all files tracked + hashes match",
        )
    else:
        _fail("manifest_integrity", integrity.fail_message(), 14)

    # 6. Copilot render freshness (exit 15 on stale)
    # Feature 019 / Blocker-5 (T156): two-tier check.
    #  Tier 1 — fast hash-only: on-disk SHA vs manifest SHA. Catches user
    #    modifications / missing files.
    #  Tier 2 — fresh re-render: re-execute the Copilot renderer against the
    #    CURRENT plugin source + CURRENT project.yml. Compare SHA of the
    #    re-render to the on-disk SHA. Catches metadata drift (e.g., company
    #    renamed in config.yml) AND plugin-source updates that the on-disk
    #    file hasn't yet absorbed.
    if "copilot" in host_names:
        copilot_dir = target / ".github"
        if copilot_dir.is_dir():
            try:
                import hashlib as _hashlib  # noqa: PLC0415

                from dotnet_ai_kit.hosts.copilot import CopilotHost  # noqa: PLC0415
                from dotnet_ai_kit.manifest import (  # noqa: PLC0415
                    read_manifest,
                    sha256_file,
                )

                manifest = read_manifest(target)
                stale: list[str] = []
                if manifest is not None:
                    for entry in manifest.files:
                        if (entry.host_owner or "").lower() != "copilot":
                            continue
                        on_disk = target / entry.path
                        if not on_disk.is_file():
                            stale.append(f"{entry.path} (missing)")
                            continue

                        # Tier 1 — fast hash-only vs manifest record
                        on_disk_sha = sha256_file(on_disk)
                        if on_disk_sha != entry.sha256:
                            stale.append(f"{entry.path} (hash drift vs manifest)")
                            continue

                        # Tier 2 — re-render and compare. B-5 metadata-staleness
                        # detection: if the user edited project.yml but didn't
                        # re-run `upgrade --copilot`, the re-rendered content
                        # differs from on-disk even though hashes match the
                        # manifest entry (because the manifest also has the
                        # stale hash).
                        rendered = CopilotHost.re_render_for_freshness(target, entry.path)
                        if rendered is None:
                            # Template unavailable — skip Tier 2 for this entry
                            continue
                        rendered_sha = _hashlib.sha256(rendered.encode("utf-8")).hexdigest()
                        if rendered_sha != on_disk_sha:
                            stale.append(f"{entry.path} (re-render drift)")

                if stale:
                    _fail(
                        "copilot_freshness",
                        f"{len(stale)} stale Copilot render(s): {', '.join(stale[:3])}",
                        15,
                    )
                else:
                    _add(
                        "copilot_freshness",
                        "pass",
                        f"{copilot_dir} renders match current sources",
                    )
            except Exception as exc:
                _add("copilot_freshness", "skip", f"could not verify: {exc}")
        else:
            _add("copilot_freshness", "skip", ".github/ not present")
    else:
        _add("copilot_freshness", "skip", "Copilot not enabled")

    duration_ms = int((_time.time() - start_ts) * 1000)

    if json_output:
        payload = {
            "version": "1.0.0",
            "duration_ms": duration_ms,
            "exit_code": exit_code,
            "checks": checks,
        }
        # Use plain print to avoid Rich color codes corrupting JSON output.
        import sys as _sys

        _sys.stdout.write(_json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        _sys.stdout.flush()
    else:
        # ASCII-safe markers — works across cp1252/cp1256/etc. on Windows
        _markers = {"pass": "[OK]", "fail": "[FAIL]", "skip": "[--]"}
        if verbose or exit_code != 0:
            for entry in checks:
                marker = _markers.get(entry["status"], "[?]")
                console.print(f"{marker} {entry['name']}: {entry['details'] or entry['status']}")
        else:
            for entry in checks:
                if entry["status"] == "pass":
                    console.print(f"[OK] {entry['name']}: {entry['details']}")

        if exit_code == 0:
            console.print(f"\n[green]dotnet-ai check passed in {duration_ms / 1000:.1f}s[/green]")
        else:
            console.print(
                f"\n[red]dotnet-ai check failed (exit {exit_code}) in {duration_ms / 1000:.1f}s[/red]"
            )

    raise typer.Exit(code=exit_code)


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
    except CatalogInstallError as exc:
        console.print(f"[yellow]Note:[/yellow] {exc}")
        raise typer.Exit(code=1)
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


@app.command("changelog")
def changelog() -> None:
    """Show project changelog or recent version tags."""
    package_dir = _get_package_dir()
    changelog_path = package_dir / "CHANGELOG.md"
    if changelog_path.is_file():
        console.print(changelog_path.read_text(encoding="utf-8"))
        return
    result = subprocess.run(
        ["git", "tag", "--sort=-version:refname"],
        capture_output=True,
        text=True,
    )
    tags = [t for t in result.stdout.strip().splitlines() if t][:5]
    if not tags:
        console.print("No changelog available.")
        return
    for tag in tags:
        date_result = subprocess.run(
            ["git", "log", tag, "--format=%ai", "-1"],
            capture_output=True,
            text=True,
        )
        date_str = date_result.stdout.strip()[:10]
        console.print(f"  {tag}  {date_str}")


# T054 - Ctrl-C handler
if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
        raise SystemExit(130)
