"""T148 (commit 20, B-4): check command raw-validates project.yml.

Asserts that `dotnet-ai check` calls `jsonschema.validate(yaml.safe_load(path),
schema)` against `schemas/project-yml.schema.json` BEFORE attempting to load
the file into the pydantic model. A hand-crafted invalid `project.yml`
(missing `company`) MUST be flagged with the FR-031 'invalid project
metadata schema' exit class (12).
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from dotnet_ai_kit.cli import app

runner = CliRunner()


def _seed_invalid_project_yml(tmp_path: Path) -> None:
    """Write an invalid project.yml (missing required `company` field)."""
    cfg_dir = tmp_path / ".dotnet-ai-kit"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    # Minimal config.yml so check can locate the project
    (cfg_dir / "config.yml").write_text(
        "enabled_hosts:\n  - claude\nplugin_version: '1.0.0'\n",
        encoding="utf-8",
    )
    (cfg_dir / "version.txt").write_text("1.0.0", encoding="utf-8")
    # Invalid project.yml: missing `company`
    (cfg_dir / "project.yml").write_text(
        "domain: Sales\n"
        "side: server\n"
        "project_type: command\n"
        "architecture_branch: microservice\n"
        "detected_paths:\n"
        "  src: src\n"
        "dotnet_version: '8.0'\n",
        encoding="utf-8",
    )


def test_check_raw_validates_missing_required_field(tmp_path: Path, monkeypatch) -> None:
    """Missing `company` → check reports project_yml_schema fail with exit class 12."""
    _seed_invalid_project_yml(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["check", str(tmp_path), "--json"], catch_exceptions=False)

    # Check command exits non-zero on any failing check
    assert result.exit_code != 0, (
        f"Expected non-zero exit on invalid project.yml; got {result.exit_code}. "
        f"Output: {result.output}"
    )

    # Parse the multi-line JSON object from the output
    output = result.output
    start = output.find("{")
    end = output.rfind("}")
    assert start != -1 and end != -1, f"No JSON object in output: {output!r}"
    data = json.loads(output[start : end + 1])

    # Look for a project_yml_schema failure entry
    checks = data.get("checks") or []
    schema_check = next(
        (c for c in checks if c.get("name") == "project_yml_schema"),
        None,
    )
    assert schema_check is not None, f"No project_yml_schema check entry in output: {data!r}"
    assert schema_check.get("status") == "fail", (
        f"project_yml_schema MUST be 'fail' for missing-company: {schema_check!r}"
    )
    # FR-031: exit class for invalid project metadata schema is 12
    assert data.get("exit_code") == 12, (
        f"Expected exit class 12 (FR-031 schema violation): {data!r}"
    )
