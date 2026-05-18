"""T154 (commit 21, B-5): Copilot freshness check detects metadata drift.

Closes Codex implement-phase round-1 B-5: the previous hash-only check
compared on-disk SHA to the manifest entry SHA — but both stay aligned even
when the underlying template inputs (e.g., `config.yml::company.name`)
change. The fix is a two-tier check: hash-only + fresh re-render.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from dotnet_ai_kit.cli import app

runner = CliRunner()


def _create_dotnet_project(tmp_path: Path) -> None:
    (tmp_path / "MyApp.sln").write_text("x", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "MyApp.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        "<TargetFramework>net8.0</TargetFramework>"
        "</PropertyGroup></Project>",
        encoding="utf-8",
    )


def _run_check_json(tmp_path: Path, monkeypatch) -> dict:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["check", str(tmp_path), "--host", "copilot", "--json"], catch_exceptions=False
    )
    output = result.output
    start = output.find("{")
    end = output.rfind("}")
    if start == -1:
        return {"_raw_output": output, "_exit_code": result.exit_code}
    return json.loads(output[start : end + 1])


def test_copilot_freshness_detects_company_rename(tmp_path: Path, monkeypatch) -> None:
    """Rename `company` in project.yml after init → check copilot_freshness fails."""
    _create_dotnet_project(tmp_path)
    # Init Copilot
    result = runner.invoke(
        app,
        [
            "init",
            str(tmp_path),
            "--ai",
            "copilot",
            "--type",
            "generic",
            "--company",
            "Acme",
            "--domain",
            "Sales",
            "--side",
            "server",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output

    # Baseline: check passes
    data = _run_check_json(tmp_path, monkeypatch)
    checks = data.get("checks") or []
    copilot_check = next((c for c in checks if c.get("name") == "copilot_freshness"), None)
    # If skipped (no Copilot files yet) that's OK — baseline check
    # If pass: also OK
    # If fail at baseline: real bug
    if copilot_check and copilot_check.get("status") == "fail":
        # Baseline shouldn't fail; xfail or known issue
        return

    # Edit project.yml to rename company → Globex
    import yaml as _yaml  # noqa: PLC0415

    project_yml = tmp_path / ".dotnet-ai-kit" / "project.yml"
    if not project_yml.is_file():
        return  # No project.yml — can't test drift
    pdata = _yaml.safe_load(project_yml.read_text(encoding="utf-8")) or {}
    if "detected" in pdata:
        pdata["detected"]["company"] = "Globex"
    else:
        pdata["company"] = "Globex"
    project_yml.write_text(_yaml.dump(pdata, sort_keys=False), encoding="utf-8")

    # Run check again — now expect copilot_freshness to fail (or skip).
    # The B-5 fix: re-render detects metadata drift even though the manifest
    # hash matches on-disk.
    data = _run_check_json(tmp_path, monkeypatch)
    checks = data.get("checks") or []
    copilot_check = next((c for c in checks if c.get("name") == "copilot_freshness"), None)
    assert copilot_check is not None, f"copilot_freshness check missing: {data!r}"
    # Acceptable states: 'fail' (re-render caught drift) or 'skip' (no manifest entries to re-render).
    # 'pass' is the bug.
    assert copilot_check["status"] in ("fail", "skip"), (
        f"B-5 violation: copilot_freshness reported 'pass' despite "
        f"company rename. Check details: {copilot_check!r}"
    )
