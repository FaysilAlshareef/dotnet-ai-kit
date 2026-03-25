"""Extension manager for dotnet-ai-kit.

Handles installing, removing, and listing extensions. Extensions provide
additional commands, rules, and hooks that integrate with the base
dotnet-ai-kit tooling.
"""

from __future__ import annotations

import logging
import platform
import shlex
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml
from filelock import FileLock

from dotnet_ai_kit import __version__ as CLI_VERSION
from dotnet_ai_kit.agents import AGENT_CONFIG

logger = logging.getLogger(__name__)


_VALID_HOOK_EVENTS = {"after_install", "after_remove"}


def _parse_version_tuple(version_str: str) -> tuple[int, ...]:
    """Parse a version string like '1.2.3' into a tuple of ints for comparison."""
    parts = []
    for part in version_str.strip().split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    return tuple(parts)


class ExtensionError(Exception):
    """Raised when an extension operation fails."""


class ExtensionManifest:
    """Parsed and validated extension manifest (extension.yml)."""

    def __init__(
        self,
        id: str,
        name: str,
        version: str,
        min_cli_version: str = "1.0.0",
        commands: Optional[list[dict[str, str]]] = None,
        rules: Optional[list[dict[str, str]]] = None,
        hooks: Optional[dict[str, Any]] = None,
    ) -> None:
        self.id = id
        self.name = name
        self.version = version
        self.min_cli_version = min_cli_version
        self.commands = commands or []
        self.rules = rules or []
        self.hooks = hooks or {}


def _validate_manifest_data(data: dict[str, Any]) -> ExtensionManifest:
    """Validate raw YAML data and return an ExtensionManifest.

    Args:
        data: Parsed YAML dictionary.

    Returns:
        Validated ExtensionManifest.

    Raises:
        ExtensionError: If required fields are missing or invalid.
    """
    ext = data.get("extension", {})
    if not isinstance(ext, dict):
        raise ExtensionError("extension.yml must have an 'extension' mapping at the top level.")

    ext_id = ext.get("id")
    if not ext_id or not isinstance(ext_id, str):
        raise ExtensionError("Extension manifest must have a non-empty 'id' field.")

    name = ext.get("name")
    if not name or not isinstance(name, str):
        raise ExtensionError("Extension manifest must have a non-empty 'name' field.")

    version = ext.get("version")
    if not version or not isinstance(version, str):
        raise ExtensionError("Extension manifest must have a non-empty 'version' field.")

    min_cli = ext.get("min_cli_version", "1.0.0")

    provides = data.get("provides", {})
    commands = provides.get("commands", []) if isinstance(provides, dict) else []
    rules = provides.get("rules", []) if isinstance(provides, dict) else []
    hooks = data.get("hooks", {})

    # Validate hook structure: keys must be valid lifecycle events, values must be lists of strings
    if hooks and isinstance(hooks, dict):
        for key, value in hooks.items():
            if key not in _VALID_HOOK_EVENTS:
                raise ExtensionError(
                    f"Invalid hook event '{key}'. Must be one of: {_VALID_HOOK_EVENTS}"
                )
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                raise ExtensionError(
                    f"Hook '{key}' must be a list of command strings, got: {type(value).__name__}"
                )

    return ExtensionManifest(
        id=ext_id,
        name=name,
        version=version,
        min_cli_version=str(min_cli),
        commands=commands if isinstance(commands, list) else [],
        rules=rules if isinstance(rules, list) else [],
        hooks=hooks if isinstance(hooks, dict) else {},
    )


def load_manifest(ext_path: Path) -> ExtensionManifest:
    """Load and validate an extension manifest from a directory.

    Args:
        ext_path: Path to the extension directory containing extension.yml.

    Returns:
        Validated ExtensionManifest.

    Raises:
        ExtensionError: If manifest file is missing or invalid.
    """
    manifest_path = ext_path / "extension.yml"
    if not manifest_path.is_file():
        raise ExtensionError(f"No extension.yml found in {ext_path}")

    text = manifest_path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)

    if not isinstance(data, dict):
        raise ExtensionError(f"Invalid extension.yml in {ext_path}: expected a YAML mapping.")

    return _validate_manifest_data(data)


def _load_extensions_registry(project_root: Path) -> dict[str, Any]:
    """Load the extensions registry file.

    Args:
        project_root: Root of the user's project.

    Returns:
        Dictionary with 'extensions' key containing a list of installed extensions.
    """
    registry_path = project_root / ".dotnet-ai-kit" / "extensions.yml"
    if not registry_path.is_file():
        return {"extensions": []}

    text = registry_path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        return {"extensions": []}

    return data


def _save_extensions_registry(project_root: Path, registry: dict[str, Any]) -> None:
    """Save the extensions registry file.

    Args:
        project_root: Root of the user's project.
        registry: Registry data to save.
    """
    registry_path = project_root / ".dotnet-ai-kit" / "extensions.yml"
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    text = yaml.dump(registry, default_flow_style=False, sort_keys=False, allow_unicode=True)
    registry_path.write_text(text, encoding="utf-8")


def _check_conflicts(
    manifest: ExtensionManifest,
    registry: dict[str, Any],
) -> Optional[str]:
    """Check if the extension conflicts with already installed extensions.

    Args:
        manifest: The extension being installed.
        registry: Current extensions registry.

    Returns:
        Error message if conflict found, None otherwise.
    """
    existing = registry.get("extensions", [])

    for ext in existing:
        if ext.get("id") == manifest.id:
            return (
                f"Extension '{manifest.id}' is already installed (v{ext.get('version', '?')}). "
                f"Remove it first with: dotnet-ai extension remove {manifest.id}"
            )

        # Check for command name conflicts
        existing_commands = set(ext.get("commands", []))
        new_commands = {cmd.get("name", "") for cmd in manifest.commands}
        overlap = existing_commands & new_commands
        if overlap:
            return (
                f"Command {overlap.pop()} already exists from extension '{ext.get('id')}'. "
                f"Remove conflicting extension first."
            )

    return None


def install_extension(
    name_or_path: str,
    dev: bool,
    project_root: Path,
) -> ExtensionManifest:
    """Install an extension from a local path or catalog name.

    Args:
        name_or_path: Extension name (catalog lookup) or local path (with --dev).
        dev: If True, treat name_or_path as a local filesystem path.
        project_root: Root of the user's project.

    Returns:
        The installed extension manifest.

    Raises:
        ExtensionError: If installation fails.
    """
    if dev:
        ext_source = Path(name_or_path).resolve()
        if not ext_source.is_dir():
            raise ExtensionError(f"Extension directory not found: {ext_source}")
    else:
        # Catalog-based installation: look for extension in a known catalog directory
        # For now, only local path via --dev is fully supported
        raise ExtensionError(
            f"Catalog-based extension install for '{name_or_path}' is not yet supported. "
            f"Use --dev with a local path instead."
        )

    # Load and validate manifest
    manifest = load_manifest(ext_source)

    # Validate min_cli_version requirement
    cli_version = _parse_version_tuple(CLI_VERSION)
    min_version = _parse_version_tuple(manifest.min_cli_version)
    if cli_version < min_version:
        raise ExtensionError(
            f"Extension '{manifest.id}' requires dotnet-ai-kit >= {manifest.min_cli_version}, "
            f"but current version is {CLI_VERSION}. Please upgrade."
        )

    # Lock the registry to prevent concurrent modifications
    registry_path = project_root / ".dotnet-ai-kit" / "extensions.yml"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(registry_path.with_suffix(".lock"))

    with lock:
        # Check for conflicts
        registry = _load_extensions_registry(project_root)
        conflict = _check_conflicts(manifest, registry)
        if conflict:
            raise ExtensionError(conflict)

        # Copy extension files to project
        ext_dest = project_root / ".dotnet-ai-kit" / "extensions" / manifest.id
        if ext_dest.exists():
            shutil.rmtree(ext_dest)
        try:
            shutil.copytree(ext_source, ext_dest)
        except Exception:
            # Clean up partial copy on failure
            if ext_dest.exists():
                shutil.rmtree(ext_dest)
            raise

        # Copy command and rule files to AI tool directories
        _register_extension_files(manifest, ext_source, project_root)

        # Register in extensions.yml
        extensions_list = registry.get("extensions", [])
        entry = {
            "id": manifest.id,
            "version": manifest.version,
            "source": f"local:{ext_source}" if dev else f"catalog:{name_or_path}",
            "installed": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "commands": [cmd.get("name", "") for cmd in manifest.commands],
            "rules": [rule.get("file", "") for rule in manifest.rules],
        }
        if manifest.hooks:
            entry["hooks"] = manifest.hooks

        extensions_list.append(entry)
        registry["extensions"] = extensions_list
        _save_extensions_registry(project_root, registry)

    # Execute after_install hooks
    after_install_hooks = manifest.hooks.get("after_install", [])
    for hook_cmd in after_install_hooks:
        try:
            if platform.system() == "Windows":
                args = hook_cmd.split()
            else:
                args = shlex.split(hook_cmd)
            subprocess.run(args, check=True, cwd=str(project_root))
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            raise ExtensionError(
                f"Extension '{manifest.id}' after_install hook failed: {hook_cmd!r} — {exc}"
            ) from exc

    return manifest


def _register_extension_files(
    manifest: ExtensionManifest,
    ext_source: Path,
    project_root: Path,
) -> None:
    """Copy extension command and rule files to AI tool directories.

    Args:
        manifest: The extension manifest.
        ext_source: Source directory of the extension.
        project_root: Root of the user's project.
    """
    # Detect which AI tools are configured by checking for their directories
    for tool_name, tool_config in AGENT_CONFIG.items():
        commands_dir_rel = tool_config.get("commands_dir")
        rules_dir_rel = tool_config.get("rules_dir")

        # Only copy to tools that have directories present
        if commands_dir_rel:
            commands_dir = project_root / commands_dir_rel
            if commands_dir.is_dir():
                ext = tool_config.get("command_ext", ".md")
                for cmd in manifest.commands:
                    cmd_file = cmd.get("file", "")
                    cmd_name = cmd.get("name", "")
                    src = ext_source / cmd_file
                    if src.is_file():
                        dest = commands_dir / f"{cmd_name}{ext}"
                        content = src.read_text(encoding="utf-8")
                        dest.write_text(content, encoding="utf-8")
                    elif cmd_file:
                        logger.warning(
                            "Extension '%s': command file '%s' not found",
                            manifest.id,
                            cmd_file,
                        )

        if rules_dir_rel:
            rules_dir = project_root / rules_dir_rel
            if rules_dir.is_dir():
                for rule in manifest.rules:
                    rule_file = rule.get("file", "")
                    src = ext_source / rule_file
                    if src.is_file():
                        dest = rules_dir / src.name
                        content = src.read_text(encoding="utf-8")
                        dest.write_text(content, encoding="utf-8")
                    elif rule_file:
                        logger.warning(
                            "Extension '%s': rule file '%s' not found",
                            manifest.id,
                            rule_file,
                        )


def remove_extension(name: str, project_root: Path) -> None:
    """Remove an installed extension.

    Removes the extension files from AI tool directories and the registry.

    Args:
        name: Extension ID to remove.
        project_root: Root of the user's project.

    Raises:
        ExtensionError: If the extension is not installed.
    """
    # Lock the registry to prevent concurrent modifications
    registry_path = project_root / ".dotnet-ai-kit" / "extensions.yml"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(registry_path.with_suffix(".lock"))

    with lock:
        registry = _load_extensions_registry(project_root)
        extensions_list = registry.get("extensions", [])

        target_entry = None
        for entry in extensions_list:
            if entry.get("id") == name:
                target_entry = entry
                break

        if target_entry is None:
            raise ExtensionError(f"Extension '{name}' is not installed.")

        # Remove command files from AI tool directories
        for tool_name, tool_config in AGENT_CONFIG.items():
            commands_dir_rel = tool_config.get("commands_dir")
            rules_dir_rel = tool_config.get("rules_dir")
            ext = tool_config.get("command_ext", ".md")

            if commands_dir_rel:
                commands_dir = project_root / commands_dir_rel
                for cmd_name in target_entry.get("commands", []):
                    cmd_path = commands_dir / f"{cmd_name}{ext}"
                    if cmd_path.is_file():
                        cmd_path.unlink()

            if rules_dir_rel:
                rules_dir = project_root / rules_dir_rel
                for rule_file in target_entry.get("rules", []):
                    rule_path = rules_dir / Path(rule_file).name
                    if rule_path.is_file():
                        rule_path.unlink()

        # Remove extension directory
        ext_dir = project_root / ".dotnet-ai-kit" / "extensions" / name
        if ext_dir.is_dir():
            shutil.rmtree(ext_dir)

        # Update registry
        extensions_list = [e for e in extensions_list if e.get("id") != name]
        registry["extensions"] = extensions_list
        _save_extensions_registry(project_root, registry)


def list_extensions(project_root: Path) -> list[dict[str, Any]]:
    """List all installed extensions.

    Args:
        project_root: Root of the user's project.

    Returns:
        List of extension registry entries.
    """
    registry = _load_extensions_registry(project_root)
    return registry.get("extensions", [])
