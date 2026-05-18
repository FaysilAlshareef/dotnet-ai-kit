"""Configuration management for dotnet-ai-kit.

Handles loading, saving, and validating YAML configuration files
using pydantic models and pyyaml serialization.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from dotnet_ai_kit.models import (
    DetectedProject,
    DotnetAiConfig,
    ProjectMetadata,
    UserConfig,
    derive_architecture_branch,
)

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
        config = DotnetAiConfig(**data)
    except ValidationError as exc:
        raise ValueError(f"Invalid configuration in {path}: {exc}") from exc

    # Feature 019 / commit 19 / B-2: reattach runtime/diff-tracking state from
    # the sidecar file (kept out of config.yml so the strict v1 UserConfig
    # schema validates). Missing sidecar is fine — those fields stay at their
    # pydantic defaults.
    sidecar = _state_path_for(path)
    if sidecar.is_file():
        try:
            state = yaml.safe_load(sidecar.read_text(encoding="utf-8")) or {}
            if isinstance(state, dict):
                if "managed_permissions" in state and isinstance(
                    state["managed_permissions"], list
                ):
                    config.managed_permissions = [str(x) for x in state["managed_permissions"]]
        except yaml.YAMLError:
            # Tolerate a corrupt sidecar — runtime state will be regenerated
            # on the next copy_permissions call.
            pass

    return config


_STATE_SIDECAR = ".state.yml"

# Feature 019 / commit 19 / B-2: fields that belong in DotnetAiConfig as
# runtime/diff-tracking state, NOT in the strict v1 UserConfig YAML. These
# are stripped from `config.yml` on save and persisted to a hidden sidecar
# at `.dotnet-ai-kit/.state.yml` to keep `config.yml` valid per
# `schemas/config-yml.schema.json` (additionalProperties: false).
_STATE_ONLY_FIELDS: frozenset[str] = frozenset({"managed_permissions"})


def _state_path_for(config_path: Path) -> Path:
    """Sidecar state file path next to a config.yml."""
    return config_path.parent / _STATE_SIDECAR


def save_config(config: DotnetAiConfig, path: Path) -> None:
    """Save a DotnetAiConfig to a YAML file.

    Feature 019 / B-2 / T143: writer emits `enabled_hosts:` (the canonical
    v1 alias) instead of `ai_tools:` via `by_alias=True`. Empty default fields
    (e.g., `company.name = ""`, `repos` all None) are excluded via
    `exclude_defaults=True` so an init that never invoked `configure` emits a
    slim file that validates against `schemas/config-yml.schema.json`.

    Runtime/diff-tracking fields (`managed_permissions`) are NOT emitted to
    config.yml — they are persisted to a sibling `.state.yml` sidecar to keep
    config.yml strict-schema-compliant. Loading reattaches the sidecar state.

    Args:
        config: The configuration to save.
        path: Destination file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    data = config.model_dump(
        mode="json",
        exclude_defaults=True,
        by_alias=True,
    )

    # Always emit the v1 UserConfig fields if they have any meaningful value
    # (even when equal to their pydantic default). Pydantic's exclude_defaults
    # would otherwise drop them and break the strict v1 schema's required
    # set (`enabled_hosts`, `plugin_version`).
    if "enabled_hosts" not in data and config.ai_tools:
        data["enabled_hosts"] = list(config.ai_tools)
    if "plugin_version" not in data and config.plugin_version:
        data["plugin_version"] = config.plugin_version
    # `permission_profile` (the serialization alias for `permissions_level`):
    # emit explicitly whenever set, regardless of default-match.
    if "permission_profile" not in data and config.permissions_level:
        data["permission_profile"] = config.permissions_level

    # Split: state-only fields go to the sidecar; UserConfig fields stay here.
    state_data = {f: data.pop(f) for f in list(_STATE_ONLY_FIELDS) if f in data}
    # Also persist managed_permissions from in-memory config even if empty (==default)
    if "managed_permissions" not in state_data and config.managed_permissions:
        state_data["managed_permissions"] = list(config.managed_permissions)

    text = yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )

    tmp = path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)

    # Sidecar
    sidecar = _state_path_for(path)
    if state_data:
        sidecar.write_text(
            yaml.dump(state_data, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
    elif sidecar.is_file():
        # No state to persist — remove stale sidecar so check/upgrade don't
        # re-load yesterday's managed_permissions.
        try:
            sidecar.unlink()
        except OSError:
            pass


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
    """Save a DetectedProject to a YAML file (legacy `detected:`-nested shape).

    Feature 019 / commit 20 / B-3: prefer `save_project_metadata()` for new
    code — it emits the canonical top-level shape matching
    `schemas/project-yml.schema.json`. This legacy function is kept for the
    migrate path that still produces DetectedProject instances.

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


# Feature 019 / commit 20 / B-3: canonical ProjectMetadata writer/loader.
# Emits top-level keys per `schemas/project-yml.schema.json`; reader tolerates
# both top-level and legacy `detected:`-nested shapes.


def save_project_metadata(metadata: ProjectMetadata, path: Path) -> None:
    """Save a ProjectMetadata to a YAML file with top-level keys.

    Per data-model.md § 2 and `schemas/project-yml.schema.json`, the canonical
    v1 project.yml shape lists fields at the top level (NOT under a `detected:`
    wrapper). Emit `architecture_branch` explicitly even though it is derived
    from `project_type` — the schema's allOf rule asserts consistency.

    Args:
        metadata: ProjectMetadata to save.
        path: Destination file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    data = metadata.model_dump(mode="json", exclude_none=True, by_alias=True)
    # Strip optional fields that are empty so the on-disk file is minimal but
    # still schema-valid. `detected_paths` may legitimately be empty {} per
    # T147 derivation table; but the schema requires `minProperties: 1` for
    # detected_paths. The init flow ensures at least one entry is present.

    text = yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )

    tmp = path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def load_project_metadata(path: Path) -> ProjectMetadata:
    """Load and validate a ProjectMetadata from a YAML file.

    Tolerates both the canonical top-level shape and the legacy
    `detected:`-nested shape (for backward compatibility with pre-019
    project.yml files written by `save_project()`). Emits a deprecation log
    when reading the legacy shape per T152.

    Args:
        path: Path to the project.yml file.

    Returns:
        Validated ProjectMetadata instance.

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

    # Legacy: nested under `detected:`. Hoist to top-level + derive missing
    # ProjectMetadata fields where possible.
    if "detected" in data and isinstance(data["detected"], dict):
        import logging

        logging.getLogger(__name__).debug(
            "Reading legacy `detected:`-nested project.yml at %s; "
            "re-run `dotnet-ai migrate` to write the canonical top-level shape.",
            path,
        )
        nested = data["detected"]
        # Try to hoist what we have; fill missing required fields with
        # safe placeholders so check can flag them.
        hoisted: dict = {
            "company": data.get("company") or "<unset>",
            "domain": data.get("domain") or "<unset>",
            "side": data.get("side") or "server",
            "project_type": nested.get("project_type") or "generic",
            "dotnet_version": nested.get("dotnet_version") or "8.0",
            "detected_paths": nested.get("detected_paths") or {"src": "src"},
        }
        hoisted["architecture_branch"] = derive_architecture_branch(hoisted["project_type"])
        data = hoisted

    try:
        return ProjectMetadata(**data)
    except ValidationError as exc:
        raise ValueError(f"Invalid project metadata in {path}: {exc}") from exc


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
