"""Tests for the extension manager."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from dotnet_ai_kit.extensions import (
    CatalogInstallError,
    ExtensionError,
    install_extension,
    list_extensions,
    load_manifest,
    remove_extension,
)


def _create_extension(ext_dir: Path, ext_id: str = "test-ext", version: str = "1.0.0") -> None:
    """Create a minimal extension directory with manifest and command file."""
    ext_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "extension": {
            "id": ext_id,
            "name": f"Test Extension ({ext_id})",
            "version": version,
            "min_cli_version": "1.0.0",
        },
        "provides": {
            "commands": [
                {
                    "name": f"dotnet-ai.{ext_id}.run",
                    "file": "commands/run.md",
                    "description": "Run the extension command",
                }
            ],
            "rules": [
                {
                    "file": f"rules/{ext_id}-rule.md",
                }
            ],
        },
        "hooks": {},
    }

    manifest_path = ext_dir / "extension.yml"
    manifest_path.write_text(yaml.dump(manifest), encoding="utf-8")

    # Create command file
    cmd_dir = ext_dir / "commands"
    cmd_dir.mkdir()
    (cmd_dir / "run.md").write_text(
        f"---\ndescription: {ext_id} command\n---\n\nRun {ext_id}.\n",
        encoding="utf-8",
    )

    # Create rule file
    rules_dir = ext_dir / "rules"
    rules_dir.mkdir()
    (rules_dir / f"{ext_id}-rule.md").write_text(
        f"---\ndescription: {ext_id} rule\n---\n\n{ext_id} conventions.\n",
        encoding="utf-8",
    )


def _init_project(project_dir: Path) -> None:
    """Create a minimal initialized project for extension testing."""
    project_dir.mkdir(parents=True, exist_ok=True)
    config_dir = project_dir / ".dotnet-ai-kit"
    config_dir.mkdir()
    (config_dir / "config.yml").write_text(
        "version: '1.0'\nai_tools:\n  - claude\n",
        encoding="utf-8",
    )
    # Create AI tool directories
    (project_dir / ".claude" / "commands").mkdir(parents=True)
    (project_dir / ".claude" / "rules").mkdir(parents=True)


# ---------------------------------------------------------------------------
# load_manifest
# ---------------------------------------------------------------------------


def test_load_manifest_valid(tmp_path: Path) -> None:
    """load_manifest should parse a valid extension.yml."""
    ext_dir = tmp_path / "my-ext"
    _create_extension(ext_dir, "my-ext")

    manifest = load_manifest(ext_dir)

    assert manifest.id == "my-ext"
    assert manifest.name == "Test Extension (my-ext)"
    assert manifest.version == "1.0.0"
    assert len(manifest.commands) == 1
    assert len(manifest.rules) == 1


def test_load_manifest_missing_file(tmp_path: Path) -> None:
    """load_manifest should raise error for missing extension.yml."""
    with pytest.raises(ExtensionError, match="No extension.yml found"):
        load_manifest(tmp_path)


def test_load_manifest_missing_id(tmp_path: Path) -> None:
    """load_manifest should raise error when id is missing."""
    ext_dir = tmp_path / "bad-ext"
    ext_dir.mkdir()
    (ext_dir / "extension.yml").write_text(
        yaml.dump({"extension": {"name": "Bad", "version": "1.0.0"}}),
        encoding="utf-8",
    )

    with pytest.raises(ExtensionError, match="non-empty 'id'"):
        load_manifest(ext_dir)


def test_load_manifest_missing_name(tmp_path: Path) -> None:
    """load_manifest should raise error when name is missing."""
    ext_dir = tmp_path / "bad-ext"
    ext_dir.mkdir()
    (ext_dir / "extension.yml").write_text(
        yaml.dump({"extension": {"id": "bad", "version": "1.0.0"}}),
        encoding="utf-8",
    )

    with pytest.raises(ExtensionError, match="non-empty 'name'"):
        load_manifest(ext_dir)


def test_load_manifest_missing_version(tmp_path: Path) -> None:
    """load_manifest should raise error when version is missing."""
    ext_dir = tmp_path / "bad-ext"
    ext_dir.mkdir()
    (ext_dir / "extension.yml").write_text(
        yaml.dump({"extension": {"id": "bad", "name": "Bad"}}),
        encoding="utf-8",
    )

    with pytest.raises(ExtensionError, match="non-empty 'version'"):
        load_manifest(ext_dir)


# ---------------------------------------------------------------------------
# install_extension
# ---------------------------------------------------------------------------


def test_install_extension_dev_mode(tmp_path: Path) -> None:
    """install_extension with dev=True should copy from local path."""
    project_dir = tmp_path / "project"
    _init_project(project_dir)

    ext_dir = tmp_path / "my-ext"
    _create_extension(ext_dir, "my-ext")

    manifest = install_extension(str(ext_dir), dev=True, project_root=project_dir)

    assert manifest.id == "my-ext"

    # Check extension was registered
    extensions = list_extensions(project_dir)
    assert len(extensions) == 1
    assert extensions[0]["id"] == "my-ext"

    # Check extension files were copied
    ext_dest = project_dir / ".dotnet-ai-kit" / "extensions" / "my-ext"
    assert ext_dest.is_dir()

    # Check command was copied to Claude commands dir
    cmd_path = project_dir / ".claude" / "commands" / "dotnet-ai.my-ext.run.md"
    assert cmd_path.is_file()


def test_install_extension_conflict_detection(tmp_path: Path) -> None:
    """install_extension should detect conflicts with existing extensions."""
    project_dir = tmp_path / "project"
    _init_project(project_dir)

    ext_dir = tmp_path / "my-ext"
    _create_extension(ext_dir, "my-ext")

    # Install first time
    install_extension(str(ext_dir), dev=True, project_root=project_dir)

    # Try to install again
    with pytest.raises(ExtensionError, match="already installed"):
        install_extension(str(ext_dir), dev=True, project_root=project_dir)


def test_install_extension_catalog_not_supported(tmp_path: Path) -> None:
    """install_extension without dev should raise not-yet-supported error."""
    project_dir = tmp_path / "project"
    _init_project(project_dir)

    with pytest.raises(ExtensionError, match="not yet supported"):
        install_extension("some-extension", dev=False, project_root=project_dir)


# ---------------------------------------------------------------------------
# remove_extension
# ---------------------------------------------------------------------------


def test_remove_extension(tmp_path: Path) -> None:
    """remove_extension should remove all extension artifacts."""
    project_dir = tmp_path / "project"
    _init_project(project_dir)

    ext_dir = tmp_path / "my-ext"
    _create_extension(ext_dir, "my-ext")
    install_extension(str(ext_dir), dev=True, project_root=project_dir)

    # Verify installed
    assert len(list_extensions(project_dir)) == 1

    # Remove
    remove_extension("my-ext", project_root=project_dir)

    # Verify removed
    assert len(list_extensions(project_dir)) == 0

    ext_dest = project_dir / ".dotnet-ai-kit" / "extensions" / "my-ext"
    assert not ext_dest.exists()


def test_remove_extension_not_installed(tmp_path: Path) -> None:
    """remove_extension should raise error when extension is not installed."""
    project_dir = tmp_path / "project"
    _init_project(project_dir)

    with pytest.raises(ExtensionError, match="not installed"):
        remove_extension("nonexistent", project_root=project_dir)


# ---------------------------------------------------------------------------
# list_extensions
# ---------------------------------------------------------------------------


def test_list_extensions_empty(tmp_path: Path) -> None:
    """list_extensions should return empty list when no extensions installed."""
    project_dir = tmp_path / "project"
    _init_project(project_dir)

    extensions = list_extensions(project_dir)
    assert extensions == []


def test_list_extensions_multiple(tmp_path: Path) -> None:
    """list_extensions should return all installed extensions."""
    project_dir = tmp_path / "project"
    _init_project(project_dir)

    ext1 = tmp_path / "ext1"
    _create_extension(ext1, "ext-one")
    install_extension(str(ext1), dev=True, project_root=project_dir)

    ext2 = tmp_path / "ext2"
    _create_extension(ext2, "ext-two")
    install_extension(str(ext2), dev=True, project_root=project_dir)

    extensions = list_extensions(project_dir)
    assert len(extensions) == 2
    ids = {e["id"] for e in extensions}
    assert ids == {"ext-one", "ext-two"}


# ---------------------------------------------------------------------------
# min_cli_version validation (T020)
# ---------------------------------------------------------------------------


def test_version_parse() -> None:
    """parse_version should parse version strings into tuples."""
    from dotnet_ai_kit.utils import parse_version

    assert parse_version("1.0.0") == (1, 0, 0)
    assert parse_version("2.1.3") == (2, 1, 3)
    assert parse_version("1.0") == (1, 0)


def test_install_rejects_too_new_min_version(tmp_path: Path) -> None:
    """install_extension should reject when min_cli_version exceeds current CLI version."""
    project_dir = tmp_path / "project"
    _init_project(project_dir)

    ext_dir = tmp_path / "future-ext"
    ext_dir.mkdir(parents=True)
    manifest = {
        "extension": {
            "id": "future-ext",
            "name": "Future Extension",
            "version": "1.0.0",
            "min_cli_version": "99.0.0",
        },
        "provides": {"commands": [], "rules": []},
    }
    (ext_dir / "extension.yml").write_text(yaml.dump(manifest), encoding="utf-8")

    with pytest.raises(ExtensionError, match="requires dotnet-ai-kit >= 99.0.0"):
        install_extension(str(ext_dir), dev=True, project_root=project_dir)


def test_install_accepts_matching_version(tmp_path: Path) -> None:
    """install_extension should accept when min_cli_version matches current CLI version."""
    project_dir = tmp_path / "project"
    _init_project(project_dir)

    ext_dir = tmp_path / "ok-ext"
    ext_dir.mkdir(parents=True)
    manifest = {
        "extension": {
            "id": "ok-ext",
            "name": "OK Extension",
            "version": "1.0.0",
            "min_cli_version": "0.0.1",
        },
        "provides": {"commands": [], "rules": []},
    }
    (ext_dir / "extension.yml").write_text(yaml.dump(manifest), encoding="utf-8")

    result = install_extension(str(ext_dir), dev=True, project_root=project_dir)
    assert result.id == "ok-ext"


# ---------------------------------------------------------------------------
# Hook validation (T021)
# ---------------------------------------------------------------------------


def test_hook_validation_rejects_invalid_keys(tmp_path: Path) -> None:
    """load_manifest should reject hooks with invalid lifecycle event keys."""
    ext_dir = tmp_path / "bad-hook-ext"
    ext_dir.mkdir(parents=True)
    manifest = {
        "extension": {
            "id": "bad-hook",
            "name": "Bad Hook",
            "version": "1.0.0",
        },
        "hooks": {
            "invalid_event": ["echo hello"],
        },
    }
    (ext_dir / "extension.yml").write_text(yaml.dump(manifest), encoding="utf-8")

    with pytest.raises(ExtensionError, match="Invalid hook event"):
        load_manifest(ext_dir)


def test_hook_validation_rejects_non_list_values(tmp_path: Path) -> None:
    """load_manifest should reject hooks where values are not lists of strings."""
    ext_dir = tmp_path / "bad-hook-ext2"
    ext_dir.mkdir(parents=True)
    manifest = {
        "extension": {
            "id": "bad-hook2",
            "name": "Bad Hook 2",
            "version": "1.0.0",
        },
        "hooks": {
            "after_install": "not a list",
        },
    }
    (ext_dir / "extension.yml").write_text(yaml.dump(manifest), encoding="utf-8")

    with pytest.raises(ExtensionError, match="must be a list"):
        load_manifest(ext_dir)


# ---------------------------------------------------------------------------
# Hook execution (T022)
# ---------------------------------------------------------------------------


def test_remove_extension_executes_after_remove_hooks(tmp_path: Path) -> None:
    """remove_extension should execute after_remove hooks."""
    # Setup: create a project with an installed extension that has after_remove hooks
    project_root = tmp_path / "project"
    config_dir = project_root / ".dotnet-ai-kit"
    config_dir.mkdir(parents=True)
    (config_dir / "config.yml").write_text(
        "version: '1.0'\nai_tools:\n  - claude\n",
        encoding="utf-8",
    )
    # Create AI tool directories
    (project_root / ".claude" / "commands").mkdir(parents=True)
    (project_root / ".claude" / "rules").mkdir(parents=True)

    # Create extension directory (so remove_extension can delete it)
    ext_dir = config_dir / "extensions" / "test-ext"
    ext_dir.mkdir(parents=True)

    # Create registry with after_remove hooks
    registry = {
        "extensions": [
            {
                "id": "test-ext",
                "version": "1.0.0",
                "source": "local:test",
                "installed": "2026-01-01",
                "commands": [],
                "rules": [],
                "hooks": {"after_remove": ["echo removed"]},
            }
        ]
    }
    (config_dir / "extensions.yml").write_text(yaml.dump(registry), encoding="utf-8")

    # Mock subprocess.run to capture hook execution
    from unittest.mock import MagicMock, patch

    with patch("dotnet_ai_kit.extensions.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        remove_extension("test-ext", project_root)

    # Verify after_remove hook was called
    hook_calls = [c for c in mock_run.call_args_list if "echo" in str(c) and "removed" in str(c)]
    assert len(hook_calls) >= 1


def test_after_install_hooks_execute(tmp_path: Path) -> None:
    """install_extension should execute after_install hooks on success."""
    project_dir = tmp_path / "project"
    _init_project(project_dir)

    ext_dir = tmp_path / "hook-ext"
    ext_dir.mkdir(parents=True)

    # Create a small script the hook will run
    script = project_dir / "hook_script.py"
    marker = project_dir / "hook_ran.txt"
    script.write_text(
        f"from pathlib import Path\nPath(r'{marker}').write_text('ok')\n",
        encoding="utf-8",
    )

    manifest = {
        "extension": {
            "id": "hook-ext",
            "name": "Hook Extension",
            "version": "1.0.0",
            "min_cli_version": "0.0.1",
        },
        "provides": {"commands": [], "rules": []},
        "hooks": {
            "after_install": [f"python {script}"],
        },
    }
    (ext_dir / "extension.yml").write_text(yaml.dump(manifest), encoding="utf-8")

    install_extension(str(ext_dir), dev=True, project_root=project_dir)

    assert marker.is_file()
    assert marker.read_text() == "ok"


def test_extension_add_catalog_gives_friendly_message(tmp_path: Path) -> None:
    """install_extension without --dev should raise CatalogInstallError with --dev hint."""
    project_dir = tmp_path / "project"
    _init_project(project_dir)

    with pytest.raises(CatalogInstallError) as exc_info:
        install_extension("jira", dev=False, project_root=project_dir)

    assert "--dev" in str(exc_info.value)


def test_remove_extension_raises_on_hook_failure(tmp_path: Path) -> None:
    """remove_extension should raise ExtensionError when after_remove hook fails."""
    from subprocess import CalledProcessError
    from unittest.mock import patch

    project_root = tmp_path / "project"
    config_dir = project_root / ".dotnet-ai-kit"
    config_dir.mkdir(parents=True)
    (config_dir / "config.yml").write_text(
        "version: '1.0'\nai_tools:\n  - claude\n",
        encoding="utf-8",
    )
    (project_root / ".claude" / "commands").mkdir(parents=True)
    (project_root / ".claude" / "rules").mkdir(parents=True)

    # Create extension directory
    ext_dir = config_dir / "extensions" / "fail-ext"
    ext_dir.mkdir(parents=True)

    # Create registry with after_remove hooks
    registry = {
        "extensions": [
            {
                "id": "fail-ext",
                "version": "1.0.0",
                "source": "local:test",
                "installed": "2026-01-01",
                "commands": [],
                "rules": [],
                "hooks": {"after_remove": ["exit 1"]},
            }
        ]
    }
    (config_dir / "extensions.yml").write_text(yaml.dump(registry), encoding="utf-8")

    with patch("dotnet_ai_kit.extensions.subprocess.run") as mock_run:
        mock_run.side_effect = CalledProcessError(1, "exit 1")
        with pytest.raises(ExtensionError, match="cleanup hook"):
            remove_extension("fail-ext", project_root)


def test_extension_add_raises_on_rule_name_conflict(tmp_path: Path) -> None:
    """_check_conflicts should raise ExtensionError when rule file names collide."""
    from dotnet_ai_kit.extensions import ExtensionManifest, _check_conflicts

    # Simulate existing registry with one extension having rules: ["conventions.md"]
    registry = {
        "extensions": [
            {
                "id": "existing-ext",
                "version": "1.0.0",
                "commands": [],
                "rules": ["conventions.md"],
            }
        ]
    }

    # Create a new manifest with the same rule file name
    new_manifest = ExtensionManifest(
        id="new-ext",
        name="New Extension",
        version="1.0.0",
        rules=[{"file": "rules/conventions.md"}],
    )

    with pytest.raises(ExtensionError, match="Rule file name conflict"):
        conflict = _check_conflicts(new_manifest, registry)
        if conflict:
            raise ExtensionError(conflict)
