"""T146 (commit 20, B-3): contract test for emitted project.yml shape.

Per data-model.md § 2 and `schemas/project-yml.schema.json`, the
`dotnet-ai init` command MUST emit a `.dotnet-ai-kit/project.yml` whose
top-level keys match the ProjectMetadata schema (NOT the legacy
`detected:` nested wrapper) and validate against the schema.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import yaml

REPO = Path(__file__).resolve().parent.parent.parent
SCHEMA = REPO / "schemas" / "project-yml.schema.json"


def _create_dotnet_project(tmp_path: Path) -> None:
    (tmp_path / "MyApp.sln").write_text("Microsoft Visual Studio Solution File\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "MyApp.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        "<TargetFramework>net8.0</TargetFramework>"
        "</PropertyGroup></Project>",
        encoding="utf-8",
    )


def test_init_emits_project_metadata_top_level_shape(tmp_path: Path) -> None:
    """init --ai claude --type command --company Acme --domain Sales --side server
    → project.yml has top-level company/domain/side/project_type/etc., no `detected:` wrapper.
    """
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
            "command",
            "--company",
            "Acme",
            "--domain",
            "Sales",
            "--side",
            "server",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"init failed: {result.stderr or result.stdout}"

    yml = tmp_path / ".dotnet-ai-kit" / "project.yml"
    assert yml.is_file()

    data = yaml.safe_load(yml.read_text(encoding="utf-8"))
    assert "detected" not in data, (
        f"B-3 violation: legacy `detected:` wrapper still present in project.yml. Data: {data!r}"
    )
    for key in (
        "company",
        "domain",
        "side",
        "project_type",
        "architecture_branch",
        "detected_paths",
        "dotnet_version",
    ):
        assert key in data, (
            f"B-3 violation: project.yml missing top-level `{key}` key. Got: {sorted(data.keys())}"
        )

    assert data["company"] == "Acme"
    assert data["domain"] == "Sales"
    assert data["side"] == "server"
    assert data["project_type"] == "command"
    assert data["architecture_branch"] == "microservice"


def test_init_project_yml_validates_against_schema(tmp_path: Path) -> None:
    """init … → project.yml validates against `schemas/project-yml.schema.json`."""
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
            "--company",
            "Acme",
            "--domain",
            "Sales",
            "--side",
            "server",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0

    yml = tmp_path / ".dotnet-ai-kit" / "project.yml"
    data = yaml.safe_load(yml.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    jsonschema.validate(instance=data, schema=schema)
