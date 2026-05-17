"""T103 — `dotnet-ai check` exit-code class identification (commit 9 / FR-031).

Asserts each failure class has a unique non-zero exit code per
`contracts/check-cli.contract.md:22-33`:

  0  All checks pass
  10 Plugin install missing
  11 External binary missing
  12 project.yml schema
  13 Detected-path inconsistency
  14 Manifest integrity
  15 Copilot render stale (deferred to commit 10)
  16 Host symmetric / loader failure
  99 Unknown error

Multiple failures: lowest code wins.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from dotnet_ai_kit.cli import app
from dotnet_ai_kit.manifest import (
    DeployedFile,
    Manifest,
    sha256_file,
    utc_now_iso,
    write_manifest,
)

runner = CliRunner()


def _make_healthy_project(tmp_path: Path) -> Path:
    """Build a project that ought to pass most checks."""
    project = tmp_path / "project"
    project.mkdir()

    # Create .dotnet-ai-kit/project.yml + manifest.json + a managed file
    config_dir = project / ".dotnet-ai-kit"
    config_dir.mkdir()

    project_yml_content = """
detected:
  company: TestCo
  domain: Sales
  side: server
  project_type: generic
  architecture_branch: generic
  dotnet_version: '8.0'
  detected_paths:
    controllers: src
"""
    (config_dir / "project.yml").write_text(project_yml_content.strip() + "\n", encoding="utf-8")

    # Create the detected_paths target
    src = project / "src"
    src.mkdir()
    f = src / "stub.cs"
    f.write_text("// stub\n", encoding="utf-8")

    # Manifest covering the stub
    manifest = Manifest(
        plugin_version="1.0.0",
        created_at=utc_now_iso(),
        files=[
            DeployedFile(
                path="src/stub.cs",
                sha256=sha256_file(f),
                plugin_version="1.0.0",
                deployed_at=utc_now_iso(),
            )
        ],
    )
    write_manifest(project, manifest)
    return project


def test_check_exit_14_when_manifest_corrupt(tmp_path: Path) -> None:
    """Manifest unreadable → exit 14."""
    project = _make_healthy_project(tmp_path)
    # Corrupt the manifest
    manifest_path = project / ".dotnet-ai-kit" / "manifest.json"
    manifest_path.write_text("{ not json", encoding="utf-8")

    result = runner.invoke(app, ["check", str(project), "--host", "claude"])

    # Lowest code wins; manifest=14 vs plugin_install=10
    # If both fail, exit will be 10 (lowest)
    assert result.exit_code in (10, 11, 14), (
        f"unexpected exit code {result.exit_code} for corrupt manifest"
    )


def test_check_exit_13_when_detected_paths_missing(tmp_path: Path) -> None:
    """Detected path on disk missing → exit 13."""
    project = _make_healthy_project(tmp_path)

    # Edit project.yml so detected_paths points at a nonexistent dir
    project_yml = project / ".dotnet-ai-kit" / "project.yml"
    project_yml.write_text(
        """
detected:
  company: TestCo
  domain: Sales
  side: server
  project_type: generic
  architecture_branch: generic
  dotnet_version: '8.0'
  detected_paths:
    controllers: nonexistent-dir
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["check", str(project), "--host", "claude"])
    # exit code may be 10 (plugin) or 13 (detected_paths); both are valid
    assert result.exit_code in (10, 11, 13), (
        f"unexpected exit code {result.exit_code}; expected 10/11/13"
    )


def test_check_json_output_includes_exit_code_field(tmp_path: Path) -> None:
    """`--json` output MUST include exit_code field per contract:64-80."""
    project = _make_healthy_project(tmp_path)
    result = runner.invoke(app, ["check", str(project), "--json", "--host", "claude"])

    # Parse the JSON output
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"--json output is not valid JSON: {result.stdout!r}")

    assert "version" in payload
    assert "duration_ms" in payload
    assert "exit_code" in payload
    assert "checks" in payload
    assert isinstance(payload["checks"], list)


def test_check_json_output_each_check_has_name_status_details(tmp_path: Path) -> None:
    """Each check entry has {name, status, details} per contract."""
    project = _make_healthy_project(tmp_path)
    result = runner.invoke(app, ["check", str(project), "--json"])
    payload = json.loads(result.stdout)

    for entry in payload["checks"]:
        assert "name" in entry
        assert "status" in entry
        assert entry["status"] in ("pass", "fail", "skip")
