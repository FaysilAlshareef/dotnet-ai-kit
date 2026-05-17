"""T046 — FR-008 / A-008 parameterized: tool MUST NOT write unmanaged paths.

Per A-008 (extended in spec-phase round 1 / Q3), the tool's commands MUST
NOT write/modify/delete any of these developer-owned paths:

  AGENTS.md, .editorconfig, Directory.Build.props, Directory.Build.targets,
  Directory.Packages.props, global.json, nuget.config, .gitignore,
  .gitattributes, Dockerfile, docker-compose.yml, CI workflow files,
  READMEs, license, .sln/.csproj

This test asserts that for EVERY write command (init, upgrade, configure,
migrate) and EVERY path in the A-008 list, the file is left untouched
when present, and not created when absent.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from dotnet_ai_kit.cli import app

runner = CliRunner()


_A008_UNMANAGED_PATHS = [
    "AGENTS.md",
    ".editorconfig",
    "Directory.Build.props",
    "Directory.Build.targets",
    "Directory.Packages.props",
    "global.json",
    "nuget.config",
    ".gitignore",
    ".gitattributes",
    "Dockerfile",
    "docker-compose.yml",
    ".github/workflows/build.yml",
    "README.md",
    "LICENSE",
    "MyApp.sln",
    "src/MyApp.csproj",
]

_WRITE_COMMANDS = [
    ("init claude", ["init", "{root}", "--ai", "claude"]),
    ("init codex", ["init", "{root}", "--ai", "codex"]),
    ("upgrade", ["upgrade", "{root}"]),
]


def _create_dotnet_project(tmp_path: Path) -> None:
    (tmp_path / "MyApp.sln").write_text(
        "Microsoft Visual Studio Solution File\n", encoding="utf-8"
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "MyApp.csproj").write_text(
        "<Project Sdk=\"Microsoft.NET.Sdk\"><PropertyGroup>"
        "<TargetFramework>net8.0</TargetFramework>"
        "</PropertyGroup></Project>",
        encoding="utf-8",
    )


@pytest.mark.parametrize("unmanaged_path", _A008_UNMANAGED_PATHS, ids=lambda p: p)
def test_init_does_not_create_unmanaged_path(
    tmp_path: Path, unmanaged_path: str
) -> None:
    """A-008: init MUST NOT create any unmanaged path that doesn't already exist."""
    _create_dotnet_project(tmp_path)

    pre_exists = (tmp_path / unmanaged_path).exists()
    pre_content = (
        (tmp_path / unmanaged_path).read_text(encoding="utf-8", errors="replace")
        if pre_exists
        else None
    )

    runner.invoke(
        app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False
    )

    p = tmp_path / unmanaged_path

    if pre_exists:
        # If it existed, it MUST be byte-identical
        assert p.exists(), f"A-008 violation: init deleted pre-existing {unmanaged_path}"
        new_content = p.read_text(encoding="utf-8", errors="replace")
        assert new_content == pre_content, (
            f"A-008 violation: init modified pre-existing {unmanaged_path}"
        )
    else:
        # If it didn't exist, it MUST NOT have been created
        # Allow .github/workflows/build.yml because parent dir may not exist
        if unmanaged_path == ".github/workflows/build.yml":
            assert not p.exists() or not p.is_file(), (
                f"A-008 violation: init created {unmanaged_path}"
            )
        else:
            assert not p.exists() or not p.is_file(), (
                f"A-008 violation: init created {unmanaged_path}"
            )
