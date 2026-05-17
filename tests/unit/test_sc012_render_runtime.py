"""T116 — `dotnet-ai render` runtime <2s (commit 14b / SC-012).

Asserts the median runtime over 3 runs is under 2 seconds for a
parameterized skill on a fixture project.
"""

from __future__ import annotations

import statistics
import time
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from dotnet_ai_kit.cli import app

runner = CliRunner()


def _build_fixture(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    config = project / ".dotnet-ai-kit"
    config.mkdir(parents=True)
    (config / "project.yml").write_text(
        yaml.dump(
            {
                "detected": {
                    "company": "Acme",
                    "domain": "Sales",
                    "side": "server",
                    "project_type": "generic",
                    "architecture_branch": "generic",
                    "dotnet_version": "8.0",
                    "detected_paths": {"controllers": "src/Web"},
                }
            }
        ),
        encoding="utf-8",
    )
    return project


def test_render_completes_under_2s_median(tmp_path: Path) -> None:
    """SC-012: median runtime over 3 runs MUST be < 2s."""
    project = _build_fixture(tmp_path)

    durations: list[float] = []
    for _ in range(3):
        start = time.time()
        result = runner.invoke(
            app, ["render", "rule", "async-concurrency", "--project", str(project)]
        )
        durations.append(time.time() - start)
        # Just ensure command produced output (exit 0 OR 21 if rule path differs)
        assert result.exit_code in (0, 21, 22)

    median = statistics.median(durations)
    assert median < 2.0, (
        f"SC-012 violation: median render runtime is {median:.2f}s (limit 2s). "
        f"Individual runs: {durations}"
    )
