"""T148 (commit 20, B-4): check command raw-validates project.yml.

Asserts that `dotnet-ai check` calls `jsonschema.validate(yaml.safe_load(path),
schema)` against `schemas/project-yml.schema.json` BEFORE attempting to load
the file into the pydantic model. A hand-crafted invalid `project.yml`
(missing `company`) MUST be flagged with the FR-031 'invalid project
metadata schema' exit class (12) — or, when other host-environment checks
also fail, with the multi-class exit code (10) as long as
`project_yml_schema` is among the failing checks.

Commit 33 (ci/019-plugin-native-arch): loosened the exit-code assertion
from strict `== 12` to "`12` if isolated, `10` if multi-class". The
previous strict form passed only on developer machines that happened to
have a Claude install and csharp-ls on PATH (masking the host-binary
checks); on a clean CI runner the other host-binary checks fail, kicking
the exit class into multi-class `10`. The signal that matters for FR-031
is that `project_yml_schema` is identified — `exit_code in {10, 12}`
preserves that signal across both environments.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from dotnet_ai_kit.cli import app

runner = CliRunner()


def _seed_invalid_project_yml(tmp_path: Path) -> None:
    """Write an invalid project.yml (missing required `company` field).

    Also writes a minimal manifest.json plus the source directory referenced
    by `detected_paths.src` so that the host-binary-independent checks
    (`manifest_integrity`, `detected_paths`) can pass on CI runners that
    lack a Claude install or csharp-ls. The host-binary checks themselves
    (`claude_plugin_install`, `csharp_ls_binary`) still fail on those
    runners — which is why the test's exit-code assertion is loosened
    below.
    """
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
    # Ensure the detected_paths entry resolves on disk (the check otherwise
    # adds a `detected_paths` failure that obscures the schema signal).
    (tmp_path / "src").mkdir(exist_ok=True)
    # Minimal manifest.json so the manifest_integrity check passes — content
    # is irrelevant because the schema check fires first and is what we're
    # asserting; we just don't want manifest absence to confuse the exit class.
    (cfg_dir / "manifest.json").write_text('{"files": [], "version": "1.0.0"}\n', encoding="utf-8")


def test_check_raw_validates_missing_required_field(tmp_path: Path, monkeypatch) -> None:
    """Missing `company` → check reports project_yml_schema fail; exit in {10, 12}.

    FR-031 reserves exit class 12 for "invalid project metadata schema". When
    that is the *only* failing check class, the exit code is 12. When other
    checks fail simultaneously (e.g., `claude_plugin_install` on a CI runner
    without a Claude install), the multi-class exit code 10 is returned. Both
    forms satisfy the FR-031 contract — what matters is that
    `project_yml_schema` is among the failures.
    """
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
    # FR-031: exit class 12 (schema-only) OR 10 (multi-class with schema among
    # failures) — both preserve the FR-031 signal. The choice depends on
    # whether host-binary checks (claude_plugin_install / csharp_ls_binary)
    # also fail on the runner.
    assert data.get("exit_code") in (10, 12), (
        f"Expected exit class 10 (multi-class) or 12 (FR-031 schema-only): {data!r}"
    )
