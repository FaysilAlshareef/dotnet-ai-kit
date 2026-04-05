"""Tests for copy_skills() token resolution: ${detected_paths.*} substitution."""

from __future__ import annotations

from pathlib import Path

from dotnet_ai_kit.copier import _resolve_detected_path_tokens, copy_skills


def _create_skill(source_dir: Path, category: str, name: str, content: str) -> Path:
    """Create a skill file in the source directory."""
    skill_dir = source_dir / category / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    path = skill_dir / "SKILL.md"
    path.write_text(content, encoding="utf-8")
    return path


class TestResolveDetectedPathTokens:
    """Verify token resolution logic."""

    def test_resolves_known_token(self) -> None:
        content = 'paths: "${detected_paths.aggregates}/**/*.cs"'
        paths = {"aggregates": "Company.Domain/Core"}
        result = _resolve_detected_path_tokens(content, paths)
        assert 'paths: "Company.Domain/Core/**/*.cs"' in result

    def test_unresolved_token_removes_paths_line(self) -> None:
        content = '---\nname: test\npaths: "${detected_paths.cosmos}/**/*.cs"\n---\n\n# Body'
        paths = {"aggregates": "Company.Domain/Core"}
        result = _resolve_detected_path_tokens(content, paths)
        assert "paths:" not in result
        assert "# Body" in result

    def test_multiple_tokens_all_resolve(self) -> None:
        content = (
            'paths: "${detected_paths.aggregates}/**/*.cs"\nextra: "${detected_paths.events}/stuff"'
        )
        paths = {"aggregates": "Domain/Core", "events": "Domain/Events"}
        result = _resolve_detected_path_tokens(content, paths)
        assert "Domain/Core" in result
        assert "Domain/Events" in result

    def test_no_tokens_unchanged(self) -> None:
        content = "---\nname: test\n---\n\n# Body"
        paths = {"aggregates": "Domain/Core"}
        result = _resolve_detected_path_tokens(content, paths)
        assert result == content


class TestCopySkillsIntegration:
    """Verify full copy_skills() with token resolution."""

    def test_resolves_tokens_during_copy(self, tmp_path: Path) -> None:
        source = tmp_path / "skills"
        target = tmp_path / "project"
        tool_config = {"skills_dir": ".claude/skills"}

        _create_skill(
            source,
            "microservice/command",
            "aggregate-design",
            '---\nname: aggregate-design\npaths: "${detected_paths.aggregates}/**/*.cs"\n'
            'when-to-use: "When working on aggregates"\n---\n\n# Aggregate Design\n',
        )

        detected_paths = {"aggregates": "Company.Domain/Core"}
        count = copy_skills(source, target, tool_config, detected_paths=detected_paths)

        assert count == 1
        deployed = (
            target / ".claude/skills/microservice/command/aggregate-design/SKILL.md"
        ).read_text(encoding="utf-8")
        assert 'paths: "Company.Domain/Core/**/*.cs"' in deployed
        assert "when-to-use" in deployed

    def test_none_detected_paths_leaves_unchanged(self, tmp_path: Path) -> None:
        source = tmp_path / "skills"
        target = tmp_path / "project"
        tool_config = {"skills_dir": ".claude/skills"}

        original = '---\nname: test\npaths: "${detected_paths.aggregates}/**/*.cs"\n---\n\n# Body\n'
        _create_skill(source, "test", "skill", original)

        count = copy_skills(source, target, tool_config, detected_paths=None)
        assert count == 1

        deployed = (target / ".claude/skills/test/skill/SKILL.md").read_text(encoding="utf-8")
        # Token should remain unresolved since detected_paths is None
        assert "${detected_paths." in deployed

    def test_missing_path_removes_paths_line(self, tmp_path: Path) -> None:
        source = tmp_path / "skills"
        target = tmp_path / "project"
        tool_config = {"skills_dir": ".claude/skills"}

        _create_skill(
            source,
            "test",
            "skill",
            '---\nname: test\npaths: "${detected_paths.cosmos}/**/*.cs"\n---\n\n# Body\n',
        )

        detected_paths = {"aggregates": "Domain/Core"}  # No cosmos key
        count = copy_skills(source, target, tool_config, detected_paths=detected_paths)

        assert count == 1
        deployed = (target / ".claude/skills/test/skill/SKILL.md").read_text(encoding="utf-8")
        assert "paths:" not in deployed
        assert "# Body" in deployed

    def test_no_skills_dir_returns_zero(self, tmp_path: Path) -> None:
        source = tmp_path / "skills"
        target = tmp_path / "project"
        tool_config = {"skills_dir": None}

        count = copy_skills(source, target, tool_config)
        assert count == 0
