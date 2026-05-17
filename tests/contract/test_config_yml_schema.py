"""Contract test for UserConfig YAML schema (T005 / feature 019 commit 1).

Asserts that the pydantic UserConfig model:
1. Validates the 4-host enum (claude, codex, cursor, copilot) per
   contracts/config-yml.schema.json.
2. Accepts the legacy `ai_tools` field on read and maps it to
   `enabled_hosts` (alias migration per data-model.md § 3).
3. Always writes the canonical `enabled_hosts` field name.
4. Rejects unknown host names.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from dotnet_ai_kit.config import load_user_config, save_user_config
from dotnet_ai_kit.models import UserConfig


def test_user_config_accepts_four_host_enum() -> None:
    """All four supported hosts are valid enabled_hosts values."""
    cfg = UserConfig(
        enabled_hosts=["claude", "codex", "cursor", "copilot"],
        plugin_version="1.0.0",
    )
    assert sorted(cfg.enabled_hosts) == ["claude", "codex", "copilot", "cursor"]


def test_user_config_rejects_unknown_host() -> None:
    """Hosts outside the {claude, codex, cursor, copilot} enum are rejected."""
    with pytest.raises(Exception):  # pydantic ValidationError
        UserConfig(enabled_hosts=["unknown-host"], plugin_version="1.0.0")


def test_user_config_rejects_duplicate_hosts() -> None:
    """Duplicate entries in enabled_hosts are rejected at validation time."""
    with pytest.raises(Exception):  # pydantic ValidationError on duplicate
        UserConfig(enabled_hosts=["claude", "claude"], plugin_version="1.0.0")


def test_user_config_accepts_legacy_ai_tools_field(tmp_path: Path) -> None:
    """A YAML file with `ai_tools: [...]` reads identically to one with `enabled_hosts: [...]`.

    Per data-model.md § 3: pydantic reader accepts the legacy `ai_tools` field
    name and maps it to `enabled_hosts` on read. The alias is one-way; writer
    always emits `enabled_hosts`.
    """
    legacy = tmp_path / "config-legacy.yml"
    legacy.write_text(
        yaml.dump({"ai_tools": ["claude"], "plugin_version": "1.0.0"}),
        encoding="utf-8",
    )

    modern = tmp_path / "config-modern.yml"
    modern.write_text(
        yaml.dump({"enabled_hosts": ["claude"], "plugin_version": "1.0.0"}),
        encoding="utf-8",
    )

    cfg_legacy = load_user_config(legacy)
    cfg_modern = load_user_config(modern)

    assert cfg_legacy.enabled_hosts == cfg_modern.enabled_hosts == ["claude"]
    assert cfg_legacy.plugin_version == cfg_modern.plugin_version == "1.0.0"


def test_user_config_writer_emits_canonical_field_name(tmp_path: Path) -> None:
    """Writer always emits `enabled_hosts`, never the legacy `ai_tools` alias."""
    target = tmp_path / "config.yml"
    save_user_config(
        UserConfig(enabled_hosts=["claude", "codex"], plugin_version="1.0.0"),
        target,
    )

    text = target.read_text(encoding="utf-8")
    assert "enabled_hosts:" in text
    assert "ai_tools:" not in text


def test_user_config_roundtrip_legacy_to_modern(tmp_path: Path) -> None:
    """Reading legacy file then saving produces canonical field name."""
    legacy = tmp_path / "config.yml"
    legacy.write_text(
        yaml.dump({"ai_tools": ["claude", "codex"], "plugin_version": "1.0.0"}),
        encoding="utf-8",
    )

    cfg = load_user_config(legacy)
    save_user_config(cfg, legacy)

    text = legacy.read_text(encoding="utf-8")
    assert "enabled_hosts:" in text
    assert "ai_tools:" not in text


def test_user_config_retention_defaults_to_three() -> None:
    """Default retention is 3 per feature 018's backup rotation."""
    cfg = UserConfig(enabled_hosts=["claude"], plugin_version="1.0.0")
    assert cfg.retention == 3


def test_user_config_permission_profile_optional() -> None:
    """permission_profile is optional; defaults to None."""
    cfg = UserConfig(enabled_hosts=["claude"], plugin_version="1.0.0")
    assert cfg.permission_profile is None

    cfg2 = UserConfig(
        enabled_hosts=["claude"],
        plugin_version="1.0.0",
        permission_profile="standard",
    )
    assert cfg2.permission_profile == "standard"


def test_user_config_permission_profile_enum_validation() -> None:
    """permission_profile must be one of minimal/standard/full/mcp when set."""
    with pytest.raises(Exception):  # pydantic ValidationError
        UserConfig(
            enabled_hosts=["claude"],
            plugin_version="1.0.0",
            permission_profile="invalid-profile",
        )
