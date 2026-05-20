"""T140 (commit 19, B-2): contract test for emitted config.yml shape.

Per FR-016 / data-model.md § 3 and `schemas/config-yml.schema.json`, the
`dotnet-ai init` command MUST emit a `.dotnet-ai-kit/config.yml` that:
1. Contains a top-level `enabled_hosts:` key (NOT `ai_tools:`).
2. Validates against `schemas/config-yml.schema.json` via `jsonschema.validate`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import yaml

REPO = Path(__file__).resolve().parent.parent.parent
SCHEMA = REPO / "schemas" / "config-yml.schema.json"


def _create_dotnet_project(tmp_path: Path) -> None:
    (tmp_path / "MyApp.sln").write_text("Microsoft Visual Studio Solution File\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "MyApp.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        "<TargetFramework>net8.0</TargetFramework>"
        "</PropertyGroup></Project>",
        encoding="utf-8",
    )


def test_init_emits_enabled_hosts_in_config_yml(tmp_path: Path) -> None:
    """init . --ai claude → config.yml has `enabled_hosts: [claude]`, NO `ai_tools:`."""
    _create_dotnet_project(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "dotnet_ai_kit.cli",
            "init",
            str(tmp_path),
            "--ai",
            "claude",
            "--type",
            "generic",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"init failed: {result.stderr or result.stdout}"

    cfg_path = tmp_path / ".dotnet-ai-kit" / "config.yml"
    assert cfg_path.is_file()

    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    assert "enabled_hosts" in data, (
        f"B-2 violation: config.yml missing top-level `enabled_hosts:` key. "
        f"Got: {sorted(data.keys())}"
    )
    assert data["enabled_hosts"] == ["claude"], (
        f"Expected enabled_hosts=['claude'], got {data['enabled_hosts']!r}"
    )
    assert "ai_tools" not in data, (
        "B-2 violation: writer emitted legacy `ai_tools:` key. Per data-model.md "
        f"§ 3 the writer must emit only `enabled_hosts:`. File contents: {data!r}"
    )


def test_init_config_yml_validates_against_schema(tmp_path: Path) -> None:
    """init . --ai claude → config.yml validates against schemas/config-yml.schema.json."""
    _create_dotnet_project(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "dotnet_ai_kit.cli",
            "init",
            str(tmp_path),
            "--ai",
            "claude",
            "--type",
            "generic",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0

    cfg_path = tmp_path / ".dotnet-ai-kit" / "config.yml"
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    # jsonschema.validate raises ValidationError on failure
    jsonschema.validate(instance=data, schema=schema)
