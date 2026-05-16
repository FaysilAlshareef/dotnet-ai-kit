"""Tests for copy_skills() token resolution: ${detected_paths.*} substitution."""

from __future__ import annotations

from pathlib import Path

import pytest

from dotnet_ai_kit.copier import DeploymentError, _resolve_detected_path_tokens, copy_skills


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

    def test_unresolved_token_raises_deployment_error(self) -> None:
        """FR-033: a missing detected_paths key must abort the deployment
        instead of silently substituting an empty string or glob-only path."""
        content = '---\nname: test\npaths: "${detected_paths.cosmos}/**/*.cs"\n---\n\n# Body'
        paths = {"aggregates": "Company.Domain/Core"}
        with pytest.raises(DeploymentError) as exc:
            _resolve_detected_path_tokens(content, paths)
        assert "cosmos" in str(exc.value)

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

    def test_none_detected_paths_skips_token_bearing_skills(self, tmp_path: Path) -> None:
        """FR-033 fail-closed: with no detected_paths, a SKILL.md that
        references ``${detected_paths.X}`` is skipped entirely. The previous
        behaviour (deploy with literal tokens left in) was a regression
        because the rule router would silently match a glob-only path."""
        source = tmp_path / "skills"
        target = tmp_path / "project"
        tool_config = {"skills_dir": ".claude/skills"}

        # Token-bearing skill (would have been broken if deployed).
        _create_skill(
            source,
            "test",
            "token_user",
            '---\nname: token_user\npaths: "${detected_paths.aggregates}/**/*.cs"\n---\n\n# Body\n',
        )
        # Token-free skill (should still deploy).
        _create_skill(
            source,
            "test",
            "plain",
            "---\nname: plain\n---\n\n# Plain Body\n",
        )

        count = copy_skills(source, target, tool_config, detected_paths=None)
        assert count == 1

        assert not (target / ".claude/skills/test/token_user/SKILL.md").exists()
        deployed = (target / ".claude/skills/test/plain/SKILL.md").read_text(encoding="utf-8")
        assert "Plain Body" in deployed
        assert "${detected_paths." not in deployed

    def test_skill_referencing_missing_key_is_skipped(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """FR-033 fail-closed at the SKILL level: a skill referencing a
        detected_paths key the project doesn't populate is SKIPPED, not
        deployed with a broken `**/*.cs` fallback. Calling
        `_resolve_detected_path_tokens` directly still raises (see
        test_path_token_substitution.py); copy_skills catches per-file."""
        source = tmp_path / "skills"
        target = tmp_path / "project"
        tool_config = {"skills_dir": ".claude/skills"}

        # Resolvable skill
        _create_skill(
            source,
            "command",
            "ok",
            '---\nname: ok\npaths: "${detected_paths.aggregates}/**/*.cs"\n---\n\n# Body\n',
        )
        # Unresolvable skill
        _create_skill(
            source,
            "query",
            "miss",
            '---\nname: miss\npaths: "${detected_paths.cosmos}/**/*.cs"\n---\n\n# Body\n',
        )

        detected_paths = {"aggregates": "Domain/Core"}
        with caplog.at_level("WARNING", logger="dotnet_ai_kit.copier"):
            count = copy_skills(source, target, tool_config, detected_paths=detected_paths)

        assert count == 1
        deployed = target / ".claude/skills"
        files = [p.name for p in deployed.rglob("SKILL.md")]
        assert "SKILL.md" in files
        # The skipped skill must not have any artifact in the deployed tree.
        assert not (deployed / "query" / "miss" / "SKILL.md").exists()

        # Maintainer must be able to find what got skipped from the log.
        skip_lines = [r for r in caplog.records if "skipping" in r.getMessage()]
        assert any("miss" in r.getMessage() for r in skip_lines), [
            r.getMessage() for r in caplog.records
        ]
        assert any("cosmos" in r.getMessage() for r in skip_lines)

    def test_no_skills_dir_returns_zero(self, tmp_path: Path) -> None:
        source = tmp_path / "skills"
        target = tmp_path / "project"
        tool_config = {"skills_dir": None}

        count = copy_skills(source, target, tool_config)
        assert count == 0
