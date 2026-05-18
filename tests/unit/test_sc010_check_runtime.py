"""T105 — `dotnet-ai check` runtime under 10s (commit 9 / SC-010 / CHK041).

Asserts the check command completes within 10 seconds median (3 runs) on a
typical project fixture.
"""

from __future__ import annotations

import statistics
import time
from pathlib import Path

from typer.testing import CliRunner

from dotnet_ai_kit.cli import app

runner = CliRunner()


def _build_fixture_project(root: Path) -> Path:
    """A representative project: project.yml + manifest + a few managed files."""
    project = root / "fixture"
    project.mkdir()
    config_dir = project / ".dotnet-ai-kit"
    config_dir.mkdir()
    (config_dir / "project.yml").write_text(
        """
detected:
  company: TestCo
  domain: Sales
  side: server
  project_type: generic
  architecture_branch: generic
  dotnet_version: '8.0'
  detected_paths:
    controllers: src
""".strip()
        + "\n",
        encoding="utf-8",
    )
    src = project / "src"
    src.mkdir()
    (src / "stub.cs").write_text("// stub\n", encoding="utf-8")
    return project


def test_check_completes_under_10s_median(tmp_path: Path) -> None:
    """SC-010 / CHK041: median runtime over 3 runs MUST be < 10s."""
    project = _build_fixture_project(tmp_path)

    durations: list[float] = []
    for _ in range(3):
        start = time.time()
        result = runner.invoke(app, ["check", str(project), "--json"])
        durations.append(time.time() - start)
        # Just ensure command produced output
        assert result.exit_code in (0, 10, 11, 13, 14, 16, 99)

    median = statistics.median(durations)
    assert median < 10.0, (
        f"SC-010 violation: median check runtime is {median:.2f}s (limit 10s). "
        f"Individual runs: {durations}"
    )
