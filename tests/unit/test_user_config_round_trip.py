"""T141 (commit 19, B-2): UserConfig round-trip test.

Asserts:
- (a) UserConfig accepts legacy `ai_tools: [...]` field name on read.
- (b) save_user_config emits canonical `enabled_hosts:` with no `ai_tools:` key.
- (c) load_user_config round-trips both legacy and canonical files identically.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from dotnet_ai_kit.config import load_user_config, save_user_config
from dotnet_ai_kit.models import UserConfig


def test_user_config_accepts_legacy_ai_tools_alias() -> None:
    """UserConfig(...) construction MUST accept `ai_tools` and map to `enabled_hosts`."""
    cfg = UserConfig(ai_tools=["claude", "codex"], plugin_version="1.0.0")
    assert cfg.enabled_hosts == ["claude", "codex"]


def test_save_user_config_emits_enabled_hosts_not_ai_tools(tmp_path: Path) -> None:
    """save_user_config MUST emit `enabled_hosts:` top-level, no `ai_tools:` key."""
    cfg = UserConfig(enabled_hosts=["claude"], plugin_version="1.0.0")
    out = tmp_path / "config.yml"
    save_user_config(cfg, out)

    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert "enabled_hosts" in data
    assert data["enabled_hosts"] == ["claude"]
    assert "ai_tools" not in data, (
        f"B-2 violation: writer emitted legacy `ai_tools:` key. Data: {data!r}"
    )


def test_load_user_config_round_trips_legacy(tmp_path: Path) -> None:
    """Legacy `ai_tools:` file → load → save → file with `enabled_hosts:` (one-way migration)."""
    legacy = tmp_path / "legacy.yml"
    legacy.write_text(
        "ai_tools:\n  - claude\n  - codex\nplugin_version: '1.0.0'\n",
        encoding="utf-8",
    )

    cfg = load_user_config(legacy)
    assert cfg.enabled_hosts == ["claude", "codex"]

    canonical = tmp_path / "canonical.yml"
    save_user_config(cfg, canonical)

    cfg2 = load_user_config(canonical)
    assert cfg2.enabled_hosts == cfg.enabled_hosts
    # Canonical file MUST NOT contain `ai_tools` (one-way migration).
    text = canonical.read_text(encoding="utf-8")
    assert "ai_tools" not in text


def test_load_user_config_round_trips_canonical(tmp_path: Path) -> None:
    """Canonical `enabled_hosts:` file → load → save → identical canonical content."""
    canonical = tmp_path / "canonical.yml"
    canonical.write_text(
        "enabled_hosts:\n  - claude\nplugin_version: '1.0.0'\n",
        encoding="utf-8",
    )

    cfg = load_user_config(canonical)
    assert cfg.enabled_hosts == ["claude"]

    out = tmp_path / "out.yml"
    save_user_config(cfg, out)

    data1 = yaml.safe_load(canonical.read_text(encoding="utf-8"))
    data2 = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert data1["enabled_hosts"] == data2["enabled_hosts"]
