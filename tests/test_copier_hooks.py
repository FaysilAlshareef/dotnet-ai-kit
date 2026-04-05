"""Tests for copy_hook(): constraint extraction, prompt embedding, file scope, settings.json."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dotnet_ai_kit.copier import copy_hook


def _create_profile(path: Path, constraints: str) -> Path:
    """Create a profile file with frontmatter and constraints body."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f"---\nalwaysApply: true\ndescription: test\n---\n\n{constraints}\n"
    path.write_text(content, encoding="utf-8")
    return path


def _create_hook_template(package_dir: Path) -> Path:
    """Create the hook prompt template."""
    template = package_dir / "templates" / "hook-prompt-template.md"
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text(
        "Check constraints.\n\n{{ constraints }}\n\nRespond with JSON.\n",
        encoding="utf-8",
    )
    return template


class TestCopyHookConstraintExtraction:
    """Verify constraint text is extracted from profile after frontmatter."""

    def test_extracts_constraints_from_profile(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"
        target = tmp_path / "project"
        profile = _create_profile(
            target / ".claude/rules/architecture-profile.md",
            "- NEVER do bad things\n- ALWAYS do good things",
        )
        _create_hook_template(pkg)

        result = copy_hook(target, profile, pkg)

        assert result is True
        settings = json.loads((target / ".claude/settings.json").read_text(encoding="utf-8"))
        hook = settings["hooks"]["PreToolUse"][0]
        assert "NEVER do bad things" in hook["prompt"]
        assert "ALWAYS do good things" in hook["prompt"]


class TestCopyHookPromptEmbedding:
    """Verify hook is written to settings.json correctly."""

    def test_creates_settings_json_if_missing(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"
        target = tmp_path / "project"
        profile = _create_profile(
            target / ".claude/rules/architecture-profile.md",
            "- constraint",
        )
        _create_hook_template(pkg)

        copy_hook(target, profile, pkg)

        settings_path = target / ".claude/settings.json"
        assert settings_path.is_file()
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        assert "hooks" in settings
        assert "PreToolUse" in settings["hooks"]

    def test_preserves_existing_hooks(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"
        target = tmp_path / "project"

        # Create existing settings with other hooks
        settings_dir = target / ".claude"
        settings_dir.mkdir(parents=True, exist_ok=True)
        existing = {"hooks": {"PreToolUse": [{"type": "command", "command": "echo hi"}]}}
        (settings_dir / "settings.json").write_text(json.dumps(existing), encoding="utf-8")

        profile = _create_profile(
            target / ".claude/rules/architecture-profile.md",
            "- constraint",
        )
        _create_hook_template(pkg)

        copy_hook(target, profile, pkg)

        settings = json.loads((target / ".claude/settings.json").read_text(encoding="utf-8"))
        hooks = settings["hooks"]["PreToolUse"]
        # Should have existing hook + new arch hook
        assert len(hooks) == 2
        types = [h.get("type") for h in hooks]
        assert "command" in types
        assert "prompt" in types

    def test_hook_has_correct_model_and_timeout(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"
        target = tmp_path / "project"
        profile = _create_profile(
            target / ".claude/rules/architecture-profile.md",
            "- constraint",
        )
        _create_hook_template(pkg)

        copy_hook(target, profile, pkg)

        settings = json.loads((target / ".claude/settings.json").read_text(encoding="utf-8"))
        hook = settings["hooks"]["PreToolUse"][0]
        assert hook["model"] == "claude-haiku-4-5-20251001"
        assert hook["timeout"] == 15000
        assert hook["matcher"] == "Write|Edit"

    def test_replaces_existing_arch_hook(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"
        target = tmp_path / "project"

        # Create existing arch hook
        settings_dir = target / ".claude"
        settings_dir.mkdir(parents=True, exist_ok=True)
        existing = {
            "hooks": {
                "PreToolUse": [{"_source": "dotnet-ai-kit-arch", "type": "prompt", "prompt": "old"}]
            }
        }
        (settings_dir / "settings.json").write_text(json.dumps(existing), encoding="utf-8")

        profile = _create_profile(
            target / ".claude/rules/architecture-profile.md",
            "- new constraint",
        )
        _create_hook_template(pkg)

        copy_hook(target, profile, pkg)

        settings = json.loads((target / ".claude/settings.json").read_text(encoding="utf-8"))
        hooks = settings["hooks"]["PreToolUse"]
        assert len(hooks) == 1  # Old replaced, not duplicated
        assert "new constraint" in hooks[0]["prompt"]


class TestCopyHookFileScope:
    """Verify .NET file scope filter is present in real hook template."""

    def test_real_template_contains_dotnet_file_extensions(
        self,
        tmp_path: Path,
    ) -> None:
        """FR-019: hook MUST only validate .NET files."""
        pkg = Path(__file__).resolve().parent.parent
        template = pkg / "templates" / "hook-prompt-template.md"
        if not template.is_file():
            pytest.skip("hook-prompt-template.md not found in package")

        content = template.read_text(encoding="utf-8")
        for ext in (".cs", ".csproj", ".sln", ".razor", ".proto", ".cshtml"):
            assert ext in content, f"Hook template missing .NET extension {ext}"

    def test_hook_prompt_uses_real_template_with_scope(
        self,
        tmp_path: Path,
    ) -> None:
        """Verify rendered prompt includes the file scope filter."""
        pkg = Path(__file__).resolve().parent.parent
        template = pkg / "templates" / "hook-prompt-template.md"
        if not template.is_file():
            pytest.skip("hook-prompt-template.md not found in package")

        target = tmp_path / "project"
        profile = _create_profile(
            target / ".claude/rules/architecture-profile.md",
            "- NEVER use two aggregates",
        )

        copy_hook(target, profile, pkg)

        settings = json.loads((target / ".claude/settings.json").read_text(encoding="utf-8"))
        prompt = settings["hooks"]["PreToolUse"][0]["prompt"]
        assert ".cs" in prompt
        assert '{"ok": true}' in prompt


class TestCopyHookSkipConditions:
    """Verify hook is skipped in correct conditions."""

    def test_returns_false_if_profile_missing(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"
        target = tmp_path / "project"
        _create_hook_template(pkg)

        result = copy_hook(target, target / "nonexistent.md", pkg)
        assert result is False

    def test_returns_false_if_template_missing(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"  # No template created
        target = tmp_path / "project"
        profile = _create_profile(
            target / ".claude/rules/architecture-profile.md",
            "- constraint",
        )

        result = copy_hook(target, profile, pkg)
        assert result is False

    def test_returns_false_if_empty_constraints(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"
        target = tmp_path / "project"
        profile = _create_profile(
            target / ".claude/rules/architecture-profile.md",
            "",  # Empty body
        )
        _create_hook_template(pkg)

        result = copy_hook(target, profile, pkg)
        assert result is False
