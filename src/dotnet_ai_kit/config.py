"""Configuration management for dotnet-ai-kit.

Handles loading, saving, and validating YAML configuration files
using pydantic models and pyyaml serialization.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from dotnet_ai_kit.models import DetectedProject, DotnetAiConfig


# Name of the configuration directory inside a project root
_CONFIG_DIR_NAME = ".dotnet-ai-kit"


def get_config_dir(project_root: Path) -> Path:
    """Return the path to the .dotnet-ai-kit/ configuration directory.

    Args:
        project_root: The root directory of the .NET project.

    Returns:
        Path to the .dotnet-ai-kit/ directory (may not exist yet).
    """
    return project_root / _CONFIG_DIR_NAME


def load_config(path: Path) -> DotnetAiConfig:
    """Load and validate a DotnetAiConfig from a YAML file.

    Args:
        path: Path to the config.yml file.

    Returns:
        Validated DotnetAiConfig instance.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the YAML content is invalid or fails validation.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)

    if data is None:
        data = {}

    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in {path}, got {type(data).__name__}")

    try:
        return DotnetAiConfig(**data)
    except ValidationError as exc:
        raise ValueError(f"Invalid configuration in {path}: {exc}") from exc


def save_config(config: DotnetAiConfig, path: Path) -> None:
    """Save a DotnetAiConfig to a YAML file.

    Creates parent directories if they do not exist.

    Args:
        config: The configuration to save.
        path: Destination file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    data = config.model_dump(mode="json", exclude_none=False)

    text = yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )

    path.write_text(text, encoding="utf-8")


def load_project(path: Path) -> DetectedProject:
    """Load and validate a DetectedProject from a YAML file.

    The YAML file may have the detected fields nested under a 'detected' key
    or at the top level.

    Args:
        path: Path to the project.yml file.

    Returns:
        Validated DetectedProject instance.

    Raises:
        FileNotFoundError: If the project file does not exist.
        ValueError: If the YAML content is invalid or fails validation.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Project file not found: {path}")

    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)

    if data is None:
        data = {}

    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in {path}, got {type(data).__name__}")

    # Support nested 'detected' key from the spec format
    if "detected" in data and isinstance(data["detected"], dict):
        data = data["detected"]

    try:
        return DetectedProject(**data)
    except ValidationError as exc:
        raise ValueError(f"Invalid project configuration in {path}: {exc}") from exc


def save_project(project: DetectedProject, path: Path) -> None:
    """Save a DetectedProject to a YAML file.

    Wraps the data under a 'detected' key to match the spec format.
    Creates parent directories if they do not exist.

    Args:
        project: The detected project info to save.
        path: Destination file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {"detected": project.model_dump(mode="json", exclude_none=False)}

    text = yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )

    path.write_text(text, encoding="utf-8")
