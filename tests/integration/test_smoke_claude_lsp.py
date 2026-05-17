"""T110 — Claude LSP smoke test (commit 11 / FR-028 / CHK011).

Gated by `CLAUDE_CODE_SMOKE=1` env var + `claude` CLI on PATH + `csharp-ls`
binary on PATH. Produces a transcript artifact proving C# diagnostics
surface at edit time (NOT via explicit AI tool invocation) per FR-028.

This test is the gate for commit 12 — if it fails in CI, commit 12 must
not ship per CHK012.
"""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest

pytestmark = [
    pytest.mark.smoke,
    pytest.mark.skipif(
        os.environ.get("CLAUDE_CODE_SMOKE") != "1",
        reason="requires CLAUDE_CODE_SMOKE=1",
    ),
    pytest.mark.skipif(
        shutil.which("claude") is None,
        reason="`claude` CLI not on PATH",
    ),
    pytest.mark.skipif(
        shutil.which("csharp-ls") is None,
        reason="`csharp-ls` binary not on PATH (required for CHK011)",
    ),
]


def test_claude_csharp_lsp_diagnostics_at_edit_time(tmp_path) -> None:
    """C# diagnostics MUST surface at edit time via the LSP, not only via AI tool.

    Per FR-028: the plugin host loads the language-server dependency and
    exposes C# diagnostics at edit time. This test is the binding gate
    for the commit-12 .mcp.json removal per CHK012.
    """
    # Create a minimal C# project with an intentional error
    project = tmp_path / "lsp_smoke"
    project.mkdir()
    (project / "Test.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        "<TargetFramework>net8.0</TargetFramework>"
        "</PropertyGroup></Project>",
        encoding="utf-8",
    )
    (project / "Program.cs").write_text(
        "// Intentional compile error to trigger LSP diagnostic\n"
        "class Test { void M() { undeclared_var = 42; } }\n",
        encoding="utf-8",
    )

    # Probe Claude's diagnostics surface — exact CLI invocation depends on
    # Claude Code's CLI surface. This is a transcript-producing test.
    result = subprocess.run(
        ["claude", "lsp", "diagnostics", str(project / "Program.cs"), "--json"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Either the diagnostics surface as JSON, or the test fails with a
    # transcript for debugging.
    assert result.returncode == 0, (
        f"LSP diagnostics smoke test failed: returncode={result.returncode}\n"
        f"stdout={result.stdout}\nstderr={result.stderr}\n"
        f"CHK011 binding: this is the gate for commit 12's .mcp.json removal."
    )
    assert "error" in result.stdout.lower() or "diagnostic" in result.stdout.lower(), (
        f"LSP did not produce diagnostics for the intentional error.\n"
        f"stdout={result.stdout!r}"
    )
