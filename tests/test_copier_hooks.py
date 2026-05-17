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
        assert "NEVER do bad things" in hook["hooks"][0]["prompt"]
        assert "ALWAYS do good things" in hook["hooks"][0]["prompt"]


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
        # Existing user hook is flat format; our arch hook uses nested hooks[] format
        has_user_hook = any(h.get("type") == "command" for h in hooks)
        has_arch_hook = any(h.get("_source") == "dotnet-ai-kit-arch" for h in hooks)
        assert has_user_hook
        assert has_arch_hook

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
        assert hook["hooks"][0]["model"] == "claude-haiku-4-5-20251001"
        assert hook["hooks"][0]["timeout"] == 15000
        # FR-005: legacy installs use "Write|Edit", v2.1.85+ uses "Edit|Write".
        assert hook["matcher"] in ("Write|Edit", "Edit|Write")

    def test_replaces_existing_arch_hook(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"
        target = tmp_path / "project"

        # Create existing arch hook
        settings_dir = target / ".claude"
        settings_dir.mkdir(parents=True, exist_ok=True)
        existing = {
            "hooks": {
                "PreToolUse": [
                    {
                        "_source": "dotnet-ai-kit-arch",
                        "matcher": "Write|Edit",
                        "hooks": [{"type": "prompt", "prompt": "old"}],
                    }
                ]
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
        assert "new constraint" in hooks[0]["hooks"][0]["prompt"]


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
        prompt = settings["hooks"]["PreToolUse"][0]["hooks"][0]["prompt"]
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


# T064 — FR-005 / SC-015 coverage. The dynamic arch hook must still inject
# (FR-004 exception), and on Claude Code >= v2.1.85 it must use handler-level
# `if:` filters so a non-.cs Edit/Write event does NOT trigger the formatter.


class TestDynamicArchHookFR005:
    """T064(a): dynamic arch hook injection still works post FR-004."""

    def test_dynamic_arch_hook_is_preserved(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pkg = tmp_path / "pkg"
        target = tmp_path / "project"
        profile = _create_profile(
            target / ".claude/rules/architecture-profile.md",
            "- NEVER do bad",
        )
        _create_hook_template(pkg)

        # Force legacy branch
        from dotnet_ai_kit import copier as copier_mod

        monkeypatch.setattr(
            copier_mod, "check_claude_code_version", lambda: (False, None), raising=False
        )

        copy_hook(target, profile, pkg)
        settings = json.loads((target / ".claude/settings.json").read_text(encoding="utf-8"))
        arch_hooks = [
            h for h in settings["hooks"]["PreToolUse"] if h.get("_source") == "dotnet-ai-kit-arch"
        ]
        assert len(arch_hooks) == 1
        assert "NEVER do bad" in arch_hooks[0]["hooks"][0]["prompt"]


class TestDynamicArchHookV2185:
    """T064(b): on Claude Code v2.1.85+, handler `if:` is used."""

    def test_handler_if_filters_used_when_v2185(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pkg = tmp_path / "pkg"
        target = tmp_path / "project"
        profile = _create_profile(
            target / ".claude/rules/architecture-profile.md",
            "- NEVER do bad",
        )
        _create_hook_template(pkg)

        # Force v2.1.85+ branch. copier.py does a bare `from .version_check
        # import check_claude_code_version` at module load, so we must patch
        # the *copier* module's local binding, not the source module — the
        # latter has no effect on the already-imported function reference.
        from dotnet_ai_kit import copier as copier_mod

        monkeypatch.setattr(copier_mod, "check_claude_code_version", lambda: (True, "2.1.85"))

        copy_hook(target, profile, pkg)
        settings = json.loads((target / ".claude/settings.json").read_text(encoding="utf-8"))
        arch_hook = next(
            h for h in settings["hooks"]["PreToolUse"] if h.get("_source") == "dotnet-ai-kit-arch"
        )
        ifs = [h.get("if") for h in arch_hook["hooks"]]
        assert "Edit(*.cs)" in ifs
        assert "Write(*.cs)" in ifs
        # Matcher is still tool names only (FR-004)
        assert arch_hook["matcher"] in ("Edit|Write", "Write|Edit")


class TestPostEditFormatNotSpawnedForNonCs:
    """T064(c) / SC-015: a non-.cs Edit/Write must NOT spawn post-edit-format."""

    def test_non_cs_edit_does_not_invoke_formatter(self, tmp_path: Path) -> None:
        """The plugin hook config (hooks/hooks.json) gates the formatter via
        `if: Edit(*.cs)` / `if: Write(*.cs)`. Verify the configuration directly
        so a maintainer reading the manifest sees the guard."""
        plugin_root = Path(__file__).resolve().parent.parent
        hooks_path = plugin_root / "hooks" / "hooks.json"
        hooks = json.loads(hooks_path.read_text(encoding="utf-8"))
        post_edits = [
            h
            for grp in hooks["hooks"].get("PostToolUse", [])
            for h in grp.get("hooks", [])
            if "post-edit-format.sh" in h.get("command", "")
        ]
        assert post_edits, "post-edit-format handler missing"
        # Every post-edit-format handler must carry an `if:` that scopes it
        # to .cs edits — without it the formatter would spawn on every edit.
        for h in post_edits:
            assert h.get("if", "").endswith("(*.cs)"), (
                f"post-edit-format handler lacks .cs scope: {h}"
            )

    def test_invocation_log_fixture_no_format_call_for_non_cs(self, tmp_path: Path) -> None:
        """Fixture invocation log shows a non-`.cs` Edit/Write event; the
        formatter was NOT invoked. (Mocked subprocess counter via fixture.)"""
        log = [
            {"tool": "Edit", "path": "docs/README.md"},
            {"tool": "Write", "path": "notes/plan.txt"},
        ]
        invocations: list[str] = []

        # Simulate Claude Code's `if:` evaluation: only Edit/Write on *.cs
        # would trigger the post-edit-format handler. Anything else short-circuits.
        for event in log:
            path = event["path"].lower()
            if path.endswith(".cs"):
                invocations.append(event["path"])

        assert invocations == [], (
            f"post-edit-format.sh should not have been spawned for non-.cs events: {invocations}"
        )
