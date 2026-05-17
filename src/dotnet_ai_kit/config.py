"""Configuration management for dotnet-ai-kit.

Handles loading, saving, and validating YAML configuration files
using pydantic models and pyyaml serialization.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from dotnet_ai_kit.models import DetectedProject, DotnetAiConfig, UserConfig

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
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError(
            f"Invalid YAML syntax in {path}: {exc}. "
            "Fix the file manually or run 'dotnet-ai configure --reset'."
        ) from exc

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

    tmp = path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


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

    tmp = path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


# ---------------------------------------------------------------------------
# Feature 019: UserConfig load/save (T004 / plan.md commit 1)
# ---------------------------------------------------------------------------
#
# Reader accepts both legacy `ai_tools: [...]` and new `enabled_hosts: [...]`
# field names (mapped via pydantic AliasChoices on UserConfig). Writer always
# emits the canonical `enabled_hosts` so future reads do not depend on the
# alias path.


def load_user_config(path: Path) -> UserConfig:
    """Load and validate a UserConfig from a YAML file.

    Per data-model.md § 3, the reader accepts the legacy `ai_tools` field
    name and maps it to `enabled_hosts`. The model's `AliasChoices` handles
    the rename transparently.

    Args:
        path: Path to the config.yml file.

    Returns:
        Validated UserConfig instance.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the YAML content is invalid or fails validation.
    """
    if not path.is_file():
        raise FileNotFoundError(f"User config file not found: {path}")

    text = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError(
            f"Invalid YAML syntax in {path}: {exc}. "
            "Fix the file manually or run 'dotnet-ai configure --reset'."
        ) from exc

    if data is None:
        data = {}

    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in {path}, got {type(data).__name__}")

    try:
        return UserConfig(**data)
    except ValidationError as exc:
        raise ValueError(f"Invalid user config in {path}: {exc}") from exc


def save_user_config(config: UserConfig, path: Path) -> None:
    """Save a UserConfig to a YAML file.

    Always emits the canonical `enabled_hosts` field name (never the legacy
    `ai_tools` alias). Creates parent directories if they do not exist.

    Args:
        config: The UserConfig to save.
        path: Destination file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # by_alias=False forces canonical field names; ensure `enabled_hosts` not `ai_tools`
    data = config.model_dump(mode="json", exclude_none=False, by_alias=False)

    text = yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )

    tmp = path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
