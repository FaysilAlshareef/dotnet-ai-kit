"""Tests for the (feature-019) `copy_agents` no-op dispatch behavior.

Feature 019 / T041a / T043 deletes the legacy universal-frontmatter →
per-tool transformation pipeline (AGENT_FRONTMATTER_MAP + the
`_transform_agent_frontmatter` helper). Per-host generation now lives in
`dotnet_ai_kit.agent_generators` and is tested in
`tests/unit/test_agent_generators.py`.

`copy_agents` is kept as a no-op compatibility shim so legacy call sites in
`cli.py` / `copier.py` linked-secondary writer keep functioning while
later feature-019 commits route them through the new `hosts/` adapters.
This file asserts the shim's no-op contract:

- For plugin-native hosts (claude/codex/cursor): MUST return 0, MUST NOT
  write any files to the target's per-solution path.
- For copilot: MUST return 0 (the Copilot render path lands in commit 7).
- For unknown hosts: MUST return 0 + warning log.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
import yaml

from dotnet_ai_kit.copier import copy_agents


def _create_agent(source_dir: Path, name: str, fm: dict) -> Path:
    source_dir.mkdir(parents=True, exist_ok=True)
    fm_yaml = yaml.dump(fm, default_flow_style=False, sort_keys=False)
    content = f"---\n{fm_yaml}---\n\n# Agent body\n\nSome instructions here.\n"
    path = source_dir / f"{name}.md"
    path.write_text(content, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "tool_name",
    ["claude", "codex", "cursor", "copilot"],
)
def test_copy_agents_is_noop_under_feature_019(tool_name: str, tmp_path: Path) -> None:
    """All 4 supported hosts: copy_agents() MUST NOT write per-solution files."""
    source = tmp_path / "agents"
    target = tmp_path / "project"
    _create_agent(source, "test-agent", {"name": "test-agent", "description": "Test"})

    tool_config = {"agents_dir": ".claude/agents"}
    count = copy_agents(source, target, tool_config, tool_name=tool_name)

    assert count == 0
    # Verify no agents directory was created in the target
    assert not (target / ".claude" / "agents").is_dir()


def test_copy_agents_logs_for_unknown_tool(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Unknown tool name emits a warning."""
    source = tmp_path / "agents"
    target = tmp_path / "project"
    _create_agent(source, "x", {"name": "x", "description": "x"})

    with caplog.at_level(logging.WARNING):
        count = copy_agents(source, target, {"agents_dir": ".x/agents"}, tool_name="bogus")

    assert count == 0
    assert "Unknown tool_name" in caplog.text or "bogus" in caplog.text


def test_copy_agents_handles_missing_source_dir(tmp_path: Path) -> None:
    """When the source directory doesn't exist, copy_agents MUST not raise."""
    source = tmp_path / "nonexistent"
    target = tmp_path / "project"

    count = copy_agents(source, target, {"agents_dir": ".claude/agents"}, tool_name="claude")
    assert count == 0
