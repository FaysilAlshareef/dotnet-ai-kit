"""T147 (commit 20, B-3): required-field derivation strategy for init.

Covers the derivation table:
- `company` from `--company` flag (placeholder `<unset>` otherwise)
- `domain` from `--domain` flag (placeholder otherwise)
- `side` from `--side` flag (default `server`)
- `project_type` from `--type` flag or detection
- `architecture_branch` derived from `project_type`
- `dotnet_version` from detection or default `"8.0"`
- `detected_paths` from detection (default `{"src": "src"}` for minProperties:1)
"""

from __future__ import annotations

from pathlib import Path

import yaml
from typer.testing import CliRunner

from dotnet_ai_kit.cli import app

runner = CliRunner()


def _create_dotnet_project(tmp_path: Path) -> None:
    (tmp_path / "MyApp.sln").write_text("x", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "MyApp.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        "<TargetFramework>net8.0</TargetFramework>"
        "</PropertyGroup></Project>",
        encoding="utf-8",
    )


def test_init_all_flags_provided(tmp_path: Path) -> None:
    """All flags provided → those values land in project.yml verbatim."""
    _create_dotnet_project(tmp_path)
    result = runner.invoke(
        app,
        [
            "init",
            str(tmp_path),
            "--ai",
            "claude",
            "--type",
            "command",
            "--company",
            "Contoso",
            "--domain",
            "Billing",
            "--side",
            "client",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    data = yaml.safe_load((tmp_path / ".dotnet-ai-kit" / "project.yml").read_text(encoding="utf-8"))
    assert data["company"] == "Contoso"
    assert data["domain"] == "Billing"
    assert data["side"] == "client"
    assert data["project_type"] == "command"
    assert data["architecture_branch"] == "microservice"


def test_init_no_company_flag_uses_placeholder(tmp_path: Path) -> None:
    """No --company flag → init emits placeholder + warns. Doesn't raise."""
    _create_dotnet_project(tmp_path)
    result = runner.invoke(
        app,
        [
            "init",
            str(tmp_path),
            "--ai",
            "claude",
            "--type",
            "generic",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    data = yaml.safe_load((tmp_path / ".dotnet-ai-kit" / "project.yml").read_text(encoding="utf-8"))
    # Placeholder accepted; check command will flag this later.
    assert data["company"]  # must be non-empty for schema minLength:1


def test_init_partial_flags(tmp_path: Path) -> None:
    """Some flags provided → those are honored, others fall back to defaults."""
    _create_dotnet_project(tmp_path)
    result = runner.invoke(
        app,
        [
            "init",
            str(tmp_path),
            "--ai",
            "claude",
            "--type",
            "vsa",
            "--company",
            "Acme",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    data = yaml.safe_load((tmp_path / ".dotnet-ai-kit" / "project.yml").read_text(encoding="utf-8"))
    assert data["company"] == "Acme"
    # Default --side is "server" per derivation table
    assert data["side"] == "server"
    assert data["project_type"] == "vsa"
    assert data["architecture_branch"] == "generic"
    # dotnet_version defaults to "8.0" or detected value
    assert data["dotnet_version"]
