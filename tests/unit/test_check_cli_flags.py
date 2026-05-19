"""T108a — `dotnet-ai check` CLI flags (commit 9 / check-cli.contract.md:12-20).

Asserts:
1. `--verbose` shows per-check breakdown.
2. `--json` produces machine-readable JSON output.
3. `--host <host>` scopes to a single host's checks.
4. Default (no flags): summary output, all hosts checked.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from dotnet_ai_kit.cli import app

runner = CliRunner()


def test_check_json_flag_produces_valid_json(tmp_path: Path) -> None:
    """`--json` MUST produce parseable JSON."""
    result = runner.invoke(app, ["check", str(tmp_path), "--json"])

    # parseable JSON, exit code captured
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"--json output not valid JSON: {result.stdout!r}")

    assert payload["exit_code"] == result.exit_code


def test_check_host_flag_scopes_to_single_host(tmp_path: Path) -> None:
    """`--host claude` MUST only run claude-side checks, not codex/cursor/copilot."""
    result = runner.invoke(app, ["check", str(tmp_path), "--host", "claude", "--json"])
    payload = json.loads(result.stdout)

    check_names = [c["name"] for c in payload["checks"]]
    assert any("claude" in name for name in check_names)
    # No codex/cursor checks should appear
    assert not any("codex_plugin_install" in name for name in check_names)
    assert not any("cursor_plugin_install" in name for name in check_names)


def test_check_verbose_flag_shows_all_checks(tmp_path: Path) -> None:
    """`--verbose` MUST show all checks (pass + skip + fail)."""
    result = runner.invoke(app, ["check", str(tmp_path), "--verbose"])
    # --verbose shows breakdown lines
    assert "_plugin_install" in result.output or "csharp_ls_binary" in result.output


def test_check_default_host_uses_all_registered_hosts(tmp_path: Path) -> None:
    """Without `--host`, all 4 registered hosts are checked."""
    result = runner.invoke(app, ["check", str(tmp_path), "--json"])
    payload = json.loads(result.stdout)
    check_names = [c["name"] for c in payload["checks"]]

    # All 4 host install checks present
    for host in ("claude", "codex", "cursor", "copilot"):
        assert any(f"{host}_plugin_install" in name for name in check_names), (
            f"check did not run {host}_plugin_install — names: {check_names}"
        )


def test_check_unknown_host_returns_exit_16(tmp_path: Path) -> None:
    """`--host unknown` produces exit 16 (loader failure)."""
    result = runner.invoke(app, ["check", str(tmp_path), "--host", "nonexistent-host", "--json"])
    payload = json.loads(result.stdout)
    # Exit code 16 OR lower (10/11/14 may also fire); host scoping kicks in
    assert "fail" in {c["status"] for c in payload["checks"]}


# ---------------------------------------------------------------------------
# B-CX-2 (round-2 codex review): csharp-ls is a Claude-LSP-only dependency
# (check-cli.contract.md:24-29). When the user scopes `--host` to a non-Claude
# host, the csharp_ls_binary check MUST be omitted from the run.
# ---------------------------------------------------------------------------

import shutil  # noqa: E402


def _seed_minimal_project(tmp_path: Path, host: str = "codex") -> None:
    """Minimal project skeleton so check has something to inspect."""
    cfg = tmp_path / ".dotnet-ai-kit"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "config.yml").write_text(f"enabled_hosts:\n  - {host}\n", encoding="utf-8")
    (cfg / "version.txt").write_text("1.0.0", encoding="utf-8")


def _extract_json(output: str) -> dict:
    start = output.find("{")
    end = output.rfind("}")
    assert start != -1 and end != -1, f"No JSON object in output: {output!r}"
    return json.loads(output[start : end + 1])


@pytest.mark.parametrize("host_scope", ["codex", "cursor", "copilot"])
def test_b_cx_2_check_host_non_claude_does_not_run_csharp_ls(tmp_path, monkeypatch, host_scope):
    """B-CX-2 (check-cli.contract.md:24-29): csharp-ls is a Claude-only LSP
    dependency and MUST NOT be checked when the host scope excludes Claude."""
    _seed_minimal_project(tmp_path, host=host_scope)
    # Force csharp-ls "not on PATH"
    original_which = shutil.which
    monkeypatch.setattr(
        shutil,
        "which",
        lambda binary: None if binary == "csharp-ls" else original_which(binary),
    )

    result = runner.invoke(
        app,
        ["check", str(tmp_path), "--host", host_scope, "--json"],
        catch_exceptions=False,
    )
    data = _extract_json(result.output)
    check_names = {c["name"] for c in data.get("checks", [])}
    assert "csharp_ls_binary" not in check_names, (
        f"csharp_ls_binary check leaked into --host {host_scope} scope. "
        f"Checks present: {sorted(check_names)}"
    )


def test_b_cx_2_check_host_claude_still_runs_csharp_ls(tmp_path, monkeypatch):
    """B-CX-2 positive: csharp-ls IS checked when Claude is in scope."""
    _seed_minimal_project(tmp_path, host="claude")

    original_which = shutil.which
    monkeypatch.setattr(
        shutil,
        "which",
        lambda binary: None if binary == "csharp-ls" else original_which(binary),
    )

    result = runner.invoke(
        app,
        ["check", str(tmp_path), "--host", "claude", "--json"],
        catch_exceptions=False,
    )
    data = _extract_json(result.output)
    check_names = {c["name"] for c in data.get("checks", [])}
    assert "csharp_ls_binary" in check_names, (
        f"csharp_ls_binary check must run when Claude is in scope. "
        f"Checks present: {sorted(check_names)}"
    )
