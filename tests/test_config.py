"""Tests for configuration load/save and validation."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from dotnet_ai_kit.config import (
    get_config_dir,
    load_config,
    load_project,
    save_config,
    save_project,
)
from dotnet_ai_kit.models import (
    CompanyConfig,
    DetectedProject,
    DotnetAiConfig,
)

# ---------------------------------------------------------------------------
# Config directory
# ---------------------------------------------------------------------------


def test_get_config_dir(tmp_path: Path) -> None:
    """get_config_dir should return .dotnet-ai-kit/ under the project root."""
    result = get_config_dir(tmp_path)
    assert result == tmp_path / ".dotnet-ai-kit"


# ---------------------------------------------------------------------------
# Config load/save round-trip
# ---------------------------------------------------------------------------


def test_save_and_load_config(tmp_path: Path) -> None:
    """Config should survive a save/load round-trip."""
    config = DotnetAiConfig(
        company=CompanyConfig(name="Acme", github_org="acme-corp"),
        ai_tools=["claude"],
        permissions_level="standard",
        command_style="both",
    )
    config_path = tmp_path / "config.yml"
    save_config(config, config_path)

    loaded = load_config(config_path)
    assert loaded.company.name == "Acme"
    assert loaded.company.github_org == "acme-corp"
    assert loaded.ai_tools == ["claude"]
    assert loaded.permissions_level == "standard"
    assert loaded.command_style == "both"


def test_load_config_file_not_found(tmp_path: Path) -> None:
    """load_config should raise FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nonexistent.yml")


def test_load_config_invalid_yaml(tmp_path: Path) -> None:
    """load_config should raise ValueError for non-mapping YAML."""
    bad_path = tmp_path / "bad.yml"
    bad_path.write_text("- just\n- a\n- list\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Expected a YAML mapping"):
        load_config(bad_path)


def test_load_config_empty_file(tmp_path: Path) -> None:
    """load_config should return defaults for empty YAML file."""
    empty_path = tmp_path / "empty.yml"
    empty_path.write_text("", encoding="utf-8")

    config = load_config(empty_path)
    assert config.version == "1.0"
    assert config.company.name == ""


def test_save_creates_parent_dirs(tmp_path: Path) -> None:
    """save_config should create parent directories if needed."""
    config = DotnetAiConfig()
    nested_path = tmp_path / "deep" / "nested" / "config.yml"

    save_config(config, nested_path)

    assert nested_path.is_file()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_company_name_valid_csharp_identifier() -> None:
    """Valid C# identifiers should pass validation."""
    config = CompanyConfig(name="Acme")
    assert config.name == "Acme"

    config2 = CompanyConfig(name="_Private")
    assert config2.name == "_Private"

    config3 = CompanyConfig(name="Company123")
    assert config3.name == "Company123"


def test_company_name_invalid_csharp_identifier() -> None:
    """Invalid C# identifiers should raise ValidationError."""
    with pytest.raises(ValueError, match="valid C# identifier"):
        CompanyConfig(name="123Invalid")

    with pytest.raises(ValueError, match="valid C# identifier"):
        CompanyConfig(name="has-hyphen")

    with pytest.raises(ValueError, match="valid C# identifier"):
        CompanyConfig(name="has space")


def test_company_name_empty_is_allowed() -> None:
    """Empty company name should be allowed (not yet configured)."""
    config = CompanyConfig(name="")
    assert config.name == ""


def test_permissions_level_validation() -> None:
    """Only minimal/standard/full should be accepted."""
    config = DotnetAiConfig(permissions_level="minimal")
    assert config.permissions_level == "minimal"

    with pytest.raises(ValueError):
        DotnetAiConfig(permissions_level="invalid")


def test_command_style_validation() -> None:
    """Only full/short/both should be accepted."""
    config = DotnetAiConfig(command_style="full")
    assert config.command_style == "full"

    with pytest.raises(ValueError):
        DotnetAiConfig(command_style="tiny")


# ---------------------------------------------------------------------------
# Project load/save
# ---------------------------------------------------------------------------


def test_save_and_load_project(tmp_path: Path) -> None:
    """DetectedProject should survive a save/load round-trip."""
    project = DetectedProject(
        mode="microservice",
        project_type="command",
        dotnet_version="10.0",
        architecture="Event-sourced Command service",
        namespace_format="{Company}.{Domain}.{Side}.{Layer}",
        packages=["MediatR", "FluentValidation"],
    )
    project_path = tmp_path / "project.yml"
    save_project(project, project_path)

    loaded = load_project(project_path)
    assert loaded.mode == "microservice"
    assert loaded.project_type == "command"
    assert loaded.dotnet_version == "10.0"
    assert "MediatR" in loaded.packages


def test_load_project_with_nested_detected_key(tmp_path: Path) -> None:
    """load_project should handle the 'detected' wrapper key."""
    data = {
        "detected": {
            "mode": "generic",
            "project_type": "vsa",
            "dotnet_version": "8.0",
        }
    }
    project_path = tmp_path / "project.yml"
    project_path.write_text(yaml.dump(data), encoding="utf-8")

    loaded = load_project(project_path)
    assert loaded.project_type == "vsa"
    assert loaded.dotnet_version == "8.0"
