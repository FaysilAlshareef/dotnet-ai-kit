"""Tests for copy_agents() universal→tool-specific frontmatter transformation."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
import yaml

from dotnet_ai_kit.copier import (
    _parse_yaml_frontmatter,
    _transform_agent_frontmatter,
    copy_agents,
)


def _create_agent(source_dir: Path, name: str, fm: dict) -> Path:
    """Create an agent file with universal frontmatter."""
    source_dir.mkdir(parents=True, exist_ok=True)
    fm_yaml = yaml.dump(fm, default_flow_style=False, sort_keys=False)
    content = f"---\n{fm_yaml}---\n\n# Agent body\n\nSome instructions here.\n"
    path = source_dir / f"{name}.md"
    path.write_text(content, encoding="utf-8")
    return path


class TestParseYamlFrontmatter:
    """Verify frontmatter parsing."""

    def test_parse_valid_frontmatter(self) -> None:
        content = "---\nname: test\nrole: advisory\n---\n\n# Body"
        fm, body = _parse_yaml_frontmatter(content)
        assert fm["name"] == "test"
        assert fm["role"] == "advisory"
        assert "# Body" in body

    def test_no_frontmatter(self) -> None:
        content = "# Just a markdown file"
        fm, body = _parse_yaml_frontmatter(content)
        assert fm == {}
        assert body == content


class TestTransformAgentFrontmatter:
    """Verify frontmatter transformation logic."""

    def test_advisory_role_adds_disallowed_tools(self) -> None:
        from dotnet_ai_kit.agents import AGENT_FRONTMATTER_MAP

        mapping = AGENT_FRONTMATTER_MAP["claude"]
        fm = {"name": "test", "role": "advisory"}
        result = _transform_agent_frontmatter(fm, mapping)
        assert result["disallowedTools"] == ["Write", "Edit"]

    def test_implementation_role_no_disallowed_tools(self) -> None:
        from dotnet_ai_kit.agents import AGENT_FRONTMATTER_MAP

        mapping = AGENT_FRONTMATTER_MAP["claude"]
        fm = {"name": "test", "role": "implementation"}
        result = _transform_agent_frontmatter(fm, mapping)
        assert "disallowedTools" not in result

    def test_review_role_adds_disallowed_tools(self) -> None:
        from dotnet_ai_kit.agents import AGENT_FRONTMATTER_MAP

        mapping = AGENT_FRONTMATTER_MAP["claude"]
        fm = {"name": "test", "role": "review"}
        result = _transform_agent_frontmatter(fm, mapping)
        assert result["disallowedTools"] == ["Write", "Edit"]

    def test_expertise_maps_to_skills(self) -> None:
        from dotnet_ai_kit.agents import AGENT_FRONTMATTER_MAP

        mapping = AGENT_FRONTMATTER_MAP["claude"]
        fm = {"name": "test", "expertise": ["aggregate-design", "event-design"]}
        result = _transform_agent_frontmatter(fm, mapping)
        assert result["skills"] == ["aggregate-design", "event-design"]

    def test_high_complexity_maps_to_effort_and_model(self) -> None:
        from dotnet_ai_kit.agents import AGENT_FRONTMATTER_MAP

        mapping = AGENT_FRONTMATTER_MAP["claude"]
        fm = {"name": "test", "complexity": "high"}
        result = _transform_agent_frontmatter(fm, mapping)
        assert result["effort"] == "high"
        assert result["model"] == "opus"

    def test_medium_complexity(self) -> None:
        from dotnet_ai_kit.agents import AGENT_FRONTMATTER_MAP

        mapping = AGENT_FRONTMATTER_MAP["claude"]
        fm = {"name": "test", "complexity": "medium"}
        result = _transform_agent_frontmatter(fm, mapping)
        assert result["effort"] == "medium"
        assert result["model"] == "sonnet"

    def test_low_complexity(self) -> None:
        from dotnet_ai_kit.agents import AGENT_FRONTMATTER_MAP

        mapping = AGENT_FRONTMATTER_MAP["claude"]
        fm = {"name": "test", "complexity": "low"}
        result = _transform_agent_frontmatter(fm, mapping)
        assert result["effort"] == "low"
        assert result["model"] == "haiku"

    def test_max_iterations_maps_to_max_turns(self) -> None:
        from dotnet_ai_kit.agents import AGENT_FRONTMATTER_MAP

        mapping = AGENT_FRONTMATTER_MAP["claude"]
        fm = {"name": "test", "max_iterations": 20}
        result = _transform_agent_frontmatter(fm, mapping)
        assert result["maxTurns"] == 20

    def test_preserves_name_and_description(self) -> None:
        from dotnet_ai_kit.agents import AGENT_FRONTMATTER_MAP

        mapping = AGENT_FRONTMATTER_MAP["claude"]
        fm = {"name": "my-agent", "description": "Does things", "role": "advisory"}
        result = _transform_agent_frontmatter(fm, mapping)
        assert result["name"] == "my-agent"
        assert result["description"] == "Does things"


class TestCopyAgentsIntegration:
    """Verify full copy_agents() with transformation."""

    def test_transforms_and_copies(self, tmp_path: Path) -> None:
        source = tmp_path / "agents"
        target = tmp_path / "project"
        tool_config = {"agents_dir": ".claude/agents"}

        _create_agent(source, "test-agent", {
            "name": "test-agent",
            "description": "A test agent",
            "role": "advisory",
            "expertise": ["skill-a", "skill-b"],
            "complexity": "high",
            "max_iterations": 20,
        })

        count = copy_agents(source, target, tool_config, tool_name="claude")
        assert count == 1

        deployed = (target / ".claude/agents/test-agent.md").read_text(encoding="utf-8")
        fm, body = _parse_yaml_frontmatter(deployed)

        assert fm["name"] == "test-agent"
        assert fm["disallowedTools"] == ["Write", "Edit"]
        assert fm["skills"] == ["skill-a", "skill-b"]
        assert fm["effort"] == "high"
        assert fm["model"] == "opus"
        assert fm["maxTurns"] == 20
        assert "Agent body" not in fm  # body preserved separately

    def test_unsupported_tool_logs_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture,
    ) -> None:
        source = tmp_path / "agents"
        target = tmp_path / "project"
        tool_config = {"agents_dir": ".cursor/agents"}

        _create_agent(source, "test-agent", {"name": "test", "role": "advisory"})

        with caplog.at_level(logging.WARNING):
            count = copy_agents(source, target, tool_config, tool_name="cursor")

        assert count == 0
        assert "not yet supported" in caplog.text

    def test_no_agents_dir_returns_zero(self, tmp_path: Path) -> None:
        source = tmp_path / "agents"
        target = tmp_path / "project"
        tool_config = {"agents_dir": None}

        count = copy_agents(source, target, tool_config, tool_name="claude")
        assert count == 0
