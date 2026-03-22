"""Tests for the extension manager."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from dotnet_ai_kit.extensions import (
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
                    "file": "rules/ext-rule.md",
                }
            ],
        },
        "hooks": {
            "after_tasks": {
                "command": f"dotnet-ai.{ext_id}.run",
                "optional": True,
            }
        },
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
    (rules_dir / "ext-rule.md").write_text(
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
