"""Tests for copy_profile(): profile selection, fallback, cross-tool, budget validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from dotnet_ai_kit.copier import PROFILE_MAP, copy_profile


def _create_profile(package_dir: Path, rel_path: str, lines: int = 50) -> Path:
    """Create a stub profile file with the given number of lines."""
    path = package_dir / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "---\nalwaysApply: true\ndescription: test\n---\n"
    content += "\n".join(f"- constraint line {i}" for i in range(lines - 4))
    path.write_text(content, encoding="utf-8")
    return path


def _setup_all_profiles(package_dir: Path) -> None:
    """Create all profile files as stubs."""
    for rel_path in PROFILE_MAP.values():
        _create_profile(package_dir, rel_path)


class TestCopyProfileSelection:
    """Verify correct profile is selected based on project_type."""

    def test_command_type_selects_command_profile(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"
        _setup_all_profiles(pkg)
        target = tmp_path / "project"

        result = copy_profile(target, "claude", "command", pkg)

        assert result is not None
        assert result.name == "architecture-profile.md"
        assert result.parent.name == "rules"
        assert result.is_file()

    def test_vsa_type_selects_vsa_profile(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"
        _setup_all_profiles(pkg)
        target = tmp_path / "project"

        result = copy_profile(target, "claude", "vsa", pkg)
        assert result.is_file()
        # Verify only one profile deployed
        profiles = list((target / ".claude" / "rules").glob("architecture-profile*"))
        assert len(profiles) == 1

    def test_each_project_type_has_profile(self) -> None:
        expected_types = {
            "command",
            "query-sql",
            "query-cosmos",
            "processor",
            "gateway",
            "controlpanel",
            "hybrid",
            "vsa",
            "clean-arch",
            "ddd",
            "modular-monolith",
            "generic",
        }
        assert set(PROFILE_MAP.keys()) == expected_types


class TestCopyProfileFallback:
    """Verify generic fallback behavior."""

    def test_low_confidence_uses_generic(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"
        _setup_all_profiles(pkg)
        target = tmp_path / "project"

        result = copy_profile(target, "claude", "command", pkg, confidence="low")
        assert result is not None
        # Verify it used the generic profile (check content matches generic)
        generic_content = (pkg / "profiles/generic/generic.md").read_text(encoding="utf-8")
        deployed_content = result.read_text(encoding="utf-8")
        assert deployed_content == generic_content

    def test_unknown_type_uses_generic(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"
        _setup_all_profiles(pkg)
        target = tmp_path / "project"

        result = copy_profile(target, "claude", "unknown-type", pkg)
        assert result is not None
        generic_content = (pkg / "profiles/generic/generic.md").read_text(encoding="utf-8")
        deployed_content = result.read_text(encoding="utf-8")
        assert deployed_content == generic_content

    def test_empty_type_uses_generic(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"
        _setup_all_profiles(pkg)
        target = tmp_path / "project"

        result = copy_profile(target, "claude", "", pkg)
        assert result is not None


class TestCopyProfileCrossTool:
    """Verify cross-tool deployment."""

    def test_claude_deploys_to_claude_rules(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"
        _setup_all_profiles(pkg)
        target = tmp_path / "project"

        result = copy_profile(target, "claude", "command", pkg)
        assert ".claude/rules" in str(result).replace("\\", "/")

    def test_cursor_deploys_to_cursor_rules(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"
        _setup_all_profiles(pkg)
        target = tmp_path / "project"

        result = copy_profile(target, "cursor", "command", pkg)
        assert ".cursor/rules" in str(result).replace("\\", "/")

    def test_codex_returns_none_no_rules_dir(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"
        _setup_all_profiles(pkg)
        target = tmp_path / "project"

        result = copy_profile(target, "codex", "command", pkg)
        assert result is None

    def test_copilot_returns_none_no_rules_dir(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"
        _setup_all_profiles(pkg)
        target = tmp_path / "project"

        result = copy_profile(target, "copilot", "command", pkg)
        assert result is None


class TestCopyProfileErrors:
    """Verify error handling."""

    def test_missing_source_raises_file_not_found(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"  # No profiles created
        target = tmp_path / "project"

        with pytest.raises(FileNotFoundError):
            copy_profile(target, "claude", "command", pkg)


class TestCopyProfileFallbackContent:
    """Verify fallback profile content is correct."""

    def test_empty_type_uses_generic_content(self, tmp_path: Path) -> None:
        pkg = tmp_path / "pkg"
        _setup_all_profiles(pkg)
        target = tmp_path / "project"

        result = copy_profile(target, "claude", "", pkg)
        assert result is not None
        generic_content = (pkg / "profiles/generic/generic.md").read_text(encoding="utf-8")
        deployed_content = result.read_text(encoding="utf-8")
        assert deployed_content == generic_content


class TestProfileLineCounts:
    """Verify all real profile files are under 100 lines."""

    def test_profile_map_has_12_entries(self) -> None:
        assert len(PROFILE_MAP) == 12

    def test_all_real_profiles_under_100_lines(self) -> None:
        """FR-002: Each profile MUST be under 100 lines."""
        package_root = Path(__file__).resolve().parent.parent
        for project_type, rel_path in PROFILE_MAP.items():
            profile_path = package_root / rel_path
            if not profile_path.is_file():
                continue  # Skip if not yet created
            line_count = len(profile_path.read_text(encoding="utf-8").splitlines())
            assert line_count <= 100, (
                f"Profile {rel_path} has {line_count} lines "
                f"(max 100) for project_type={project_type}"
            )
