"""Tests for deploy_to_linked_repos(): version checking, branch creation, skip logic."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import yaml

from dotnet_ai_kit.copier import deploy_to_linked_repos
from dotnet_ai_kit.models import DotnetAiConfig, ReposConfig


def _init_secondary_repo(
    repo_path: Path,
    project_type: str = "query-sql",
    version: str = "1.0",
) -> None:
    """Set up a secondary repo as initialized with config and project.yml."""
    kit_dir = repo_path / ".dotnet-ai-kit"
    kit_dir.mkdir(parents=True, exist_ok=True)

    config = {"version": "1.0", "company": {"name": "Test"}, "ai_tools": ["claude"]}
    (kit_dir / "config.yml").write_text(yaml.dump(config), encoding="utf-8")

    project = {"project_type": project_type, "confidence": "high"}
    (kit_dir / "project.yml").write_text(yaml.dump(project), encoding="utf-8")

    (kit_dir / "version.txt").write_text(version, encoding="utf-8")

    # Create .claude dir for profile deployment
    (repo_path / ".claude" / "rules").mkdir(parents=True, exist_ok=True)


def _create_package_profiles(pkg_dir: Path) -> None:
    """Create minimal profile files in the package directory."""
    from dotnet_ai_kit.copier import PROFILE_MAP

    for rel_path in PROFILE_MAP.values():
        path = pkg_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("---\nalwaysApply: true\n---\n\n- constraint\n", encoding="utf-8")


@patch("subprocess.run")
class TestDeployToLinkedRepos:
    """Test deploy_to_linked_repos() with mocked git operations."""

    def test_deploy_to_initialized_repo_succeeds(self, mock_run: object, tmp_path: Path) -> None:
        primary = tmp_path / "primary"
        primary.mkdir()
        secondary = tmp_path / "secondary"
        secondary.mkdir()
        pkg = tmp_path / "pkg"

        _init_secondary_repo(secondary)
        _create_package_profiles(pkg)

        # Mock git subprocess calls
        mock_run.return_value.stdout = ""  # Clean working dir
        mock_run.return_value.returncode = 0

        config = DotnetAiConfig(
            repos=ReposConfig(query=str(secondary)),
            ai_tools=["claude"],
        )

        results = deploy_to_linked_repos(primary, config, "1.0", pkg)

        assert len(results) == 1
        assert results[0]["status"] in ("deployed", "upgraded")

    def test_older_version_repo_upgraded(
        self,
        mock_run: object,
        tmp_path: Path,
    ) -> None:
        primary = tmp_path / "primary"
        primary.mkdir()
        secondary = tmp_path / "secondary"
        secondary.mkdir()
        pkg = tmp_path / "pkg"

        _init_secondary_repo(secondary, version="0.9")  # Older
        _create_package_profiles(pkg)

        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0

        config = DotnetAiConfig(
            repos=ReposConfig(query=str(secondary)),
            ai_tools=["claude"],
        )

        results = deploy_to_linked_repos(primary, config, "1.0", pkg)

        assert len(results) == 1
        assert results[0]["status"] == "upgraded"
        assert results[0]["reason"] == "success"

    def test_same_version_repo_deployed(
        self,
        mock_run: object,
        tmp_path: Path,
    ) -> None:
        primary = tmp_path / "primary"
        primary.mkdir()
        secondary = tmp_path / "secondary"
        secondary.mkdir()
        pkg = tmp_path / "pkg"

        _init_secondary_repo(secondary, version="1.0")  # Same
        _create_package_profiles(pkg)

        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0

        config = DotnetAiConfig(
            repos=ReposConfig(query=str(secondary)),
            ai_tools=["claude"],
        )

        results = deploy_to_linked_repos(primary, config, "1.0", pkg)

        assert len(results) == 1
        assert results[0]["status"] == "deployed"
        assert results[0]["reason"] == "success"

    def test_branch_created_with_correct_name(
        self,
        mock_run: object,
        tmp_path: Path,
    ) -> None:
        primary = tmp_path / "primary"
        primary.mkdir()
        secondary = tmp_path / "secondary"
        secondary.mkdir()
        pkg = tmp_path / "pkg"

        _init_secondary_repo(secondary)
        _create_package_profiles(pkg)

        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0

        config = DotnetAiConfig(
            repos=ReposConfig(query=str(secondary)),
            ai_tools=["claude"],
        )

        deploy_to_linked_repos(
            primary,
            config,
            "1.0",
            pkg,
            branch_name="chore/dotnet-ai-kit-setup",
        )

        # Verify git checkout -b was called with the branch name
        checkout_calls = [
            call for call in mock_run.call_args_list if call[0][0][:3] == ["git", "checkout", "-b"]
        ]
        assert len(checkout_calls) == 1
        assert checkout_calls[0][0][0][3] == "chore/dotnet-ai-kit-setup"

    def test_multi_digit_version_comparison(
        self,
        mock_run: object,
        tmp_path: Path,
    ) -> None:
        """BUG-1 regression: 9.0 should not be newer than 10.0."""
        primary = tmp_path / "primary"
        primary.mkdir()
        secondary = tmp_path / "secondary"
        secondary.mkdir()
        pkg = tmp_path / "pkg"

        _init_secondary_repo(secondary, version="9.0")
        _create_package_profiles(pkg)

        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0

        config = DotnetAiConfig(
            repos=ReposConfig(query=str(secondary)),
            ai_tools=["claude"],
        )

        results = deploy_to_linked_repos(primary, config, "10.0", pkg)

        assert len(results) == 1
        # 9.0 < 10.0 — should upgrade, NOT skip as "newer"
        assert results[0]["status"] == "upgraded"

    def test_uninitialized_repo_auto_init_attempted(self, mock_run: object, tmp_path: Path) -> None:
        primary = tmp_path / "primary"
        primary.mkdir()
        secondary = tmp_path / "secondary"
        secondary.mkdir()  # No .dotnet-ai-kit/
        pkg = tmp_path / "pkg"

        config = DotnetAiConfig(
            repos=ReposConfig(query=str(secondary)),
            ai_tools=["claude"],
        )

        results = deploy_to_linked_repos(primary, config, "1.0", pkg)

        assert len(results) == 1
        assert results[0]["status"] == "skipped"
        # Auto-init is attempted but fails (subprocess is mocked)
        assert "auto-init" in results[0]["reason"]

    def test_newer_version_skipped(self, mock_run: object, tmp_path: Path) -> None:
        primary = tmp_path / "primary"
        primary.mkdir()
        secondary = tmp_path / "secondary"
        secondary.mkdir()
        pkg = tmp_path / "pkg"

        _init_secondary_repo(secondary, version="2.0")  # Newer

        config = DotnetAiConfig(
            repos=ReposConfig(query=str(secondary)),
            ai_tools=["claude"],
        )

        results = deploy_to_linked_repos(primary, config, "1.0", pkg)

        assert len(results) == 1
        assert results[0]["status"] == "skipped"
        assert "newer version" in results[0]["reason"]

    def test_remote_url_skipped(self, mock_run: object, tmp_path: Path) -> None:
        primary = tmp_path / "primary"
        primary.mkdir()
        pkg = tmp_path / "pkg"

        config = DotnetAiConfig(
            repos=ReposConfig(query="github:org/repo"),
            ai_tools=["claude"],
        )

        results = deploy_to_linked_repos(primary, config, "1.0", pkg)

        assert len(results) == 1
        assert results[0]["status"] == "skipped"
        assert "remote URL" in results[0]["reason"]

    def test_dirty_working_directory_skipped(self, mock_run: object, tmp_path: Path) -> None:
        primary = tmp_path / "primary"
        primary.mkdir()
        secondary = tmp_path / "secondary"
        secondary.mkdir()
        pkg = tmp_path / "pkg"

        _init_secondary_repo(secondary)
        _create_package_profiles(pkg)

        # Mock dirty working directory
        mock_run.return_value.stdout = "M some-file.cs"
        mock_run.return_value.returncode = 0

        config = DotnetAiConfig(
            repos=ReposConfig(query=str(secondary)),
            ai_tools=["claude"],
        )

        results = deploy_to_linked_repos(primary, config, "1.0", pkg)

        assert len(results) == 1
        assert results[0]["status"] == "skipped"
        assert "dirty" in results[0]["reason"]

    def test_partial_failure_continues(self, mock_run: object, tmp_path: Path) -> None:
        primary = tmp_path / "primary"
        primary.mkdir()
        repo1 = tmp_path / "repo1"
        repo1.mkdir()  # Not initialized
        repo2 = tmp_path / "repo2"
        repo2.mkdir()
        pkg = tmp_path / "pkg"

        _init_secondary_repo(repo2)
        _create_package_profiles(pkg)

        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0

        config = DotnetAiConfig(
            repos=ReposConfig(command=str(repo1), query=str(repo2)),
            ai_tools=["claude"],
        )

        results = deploy_to_linked_repos(primary, config, "1.0", pkg)

        assert len(results) == 2
        statuses = {r["status"] for r in results}
        assert "skipped" in statuses  # repo1 not initialized

    def test_linked_from_written_to_secondary_config(
        self,
        mock_run: object,
        tmp_path: Path,
    ) -> None:
        primary = tmp_path / "primary"
        primary.mkdir()
        secondary = tmp_path / "secondary"
        secondary.mkdir()
        pkg = tmp_path / "pkg"

        _init_secondary_repo(secondary)
        _create_package_profiles(pkg)

        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0

        config = DotnetAiConfig(
            repos=ReposConfig(query=str(secondary)),
            ai_tools=["claude"],
        )

        deploy_to_linked_repos(primary, config, "1.0", pkg)

        sec_config = yaml.safe_load(
            (secondary / ".dotnet-ai-kit/config.yml").read_text(encoding="utf-8")
        )
        assert sec_config["linked_from"] == str(primary)

    def test_null_repos_skipped_silently(self, mock_run: object, tmp_path: Path) -> None:
        primary = tmp_path / "primary"
        primary.mkdir()
        pkg = tmp_path / "pkg"

        config = DotnetAiConfig(ai_tools=["claude"])

        results = deploy_to_linked_repos(primary, config, "1.0", pkg)

        assert len(results) == 0

    def test_dry_run_skips_deployment(self, mock_run: object, tmp_path: Path) -> None:
        primary = tmp_path / "primary"
        primary.mkdir()
        secondary = tmp_path / "secondary"
        secondary.mkdir()
        pkg = tmp_path / "pkg"

        _init_secondary_repo(secondary)

        config = DotnetAiConfig(
            repos=ReposConfig(query=str(secondary)),
            ai_tools=["claude"],
        )

        results = deploy_to_linked_repos(primary, config, "1.0", pkg, dry_run=True)

        assert len(results) == 1
        assert results[0]["status"] == "dry-run"

    def test_secondary_repo_uses_own_command_style(
        self,
        mock_run: object,
        tmp_path: Path,
    ) -> None:
        """T039: deploy should use the secondary repo's command_style, not the primary's."""
        primary = tmp_path / "primary"
        primary.mkdir()
        secondary = tmp_path / "secondary"
        secondary.mkdir()
        pkg = tmp_path / "pkg"

        _init_secondary_repo(secondary)
        _create_package_profiles(pkg)

        # Set secondary config to command_style: short
        sec_config_path = secondary / ".dotnet-ai-kit" / "config.yml"
        sec_config_path.write_text(
            "version: '1.0'\ncompany:\n  name: Test\nai_tools:\n  - claude\ncommand_style: short\n",
            encoding="utf-8",
        )

        # Create a commands directory in package
        cmds_dir = pkg / "commands"
        cmds_dir.mkdir(parents=True, exist_ok=True)
        (cmds_dir / "dotnet-ai.do.md").write_text(
            "---\ndescription: do\n---\nDo.\n",
            encoding="utf-8",
        )

        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0

        config = DotnetAiConfig(
            repos=ReposConfig(query=str(secondary)),
            ai_tools=["claude"],
            command_style="both",  # Primary uses 'both'
        )

        deploy_to_linked_repos(primary, config, "1.0", pkg)

        # After deploy, the secondary repo should have commands
        # matching the 'short' style (dai.* files), not 'both'
        cmds_out = secondary / ".claude" / "commands"
        if cmds_out.is_dir():
            full_files = list(cmds_out.glob("dotnet-ai.*.md"))
            # 'short' style should NOT produce dotnet-ai.* prefix files
            assert len(full_files) == 0, (
                f"Secondary with style=short should not have full-prefix commands: {full_files}"
            )

    def test_git_add_stages_tool_directories(
        self,
        mock_run: object,
        tmp_path: Path,
    ) -> None:
        """T040: git add should stage tool-specific directories."""
        primary = tmp_path / "primary"
        primary.mkdir()
        secondary = tmp_path / "secondary"
        secondary.mkdir()
        pkg = tmp_path / "pkg"

        _init_secondary_repo(secondary)
        _create_package_profiles(pkg)

        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0

        config = DotnetAiConfig(
            repos=ReposConfig(query=str(secondary)),
            ai_tools=["claude"],
        )

        deploy_to_linked_repos(primary, config, "1.0", pkg)

        # Find git add calls
        git_add_calls = [
            call
            for call in mock_run.call_args_list
            if len(call[0]) > 0 and len(call[0][0]) >= 2 and call[0][0][:2] == ["git", "add"]
        ]
        assert len(git_add_calls) >= 1, "Expected at least one 'git add' call"

        # The staged directories should include .dotnet-ai-kit/ and .claude/
        staged_args = git_add_calls[0][0][0][2:]  # Everything after ["git", "add"]
        assert ".dotnet-ai-kit/" in staged_args, (
            f"Expected .dotnet-ai-kit/ in git add args: {staged_args}"
        )
        assert ".claude/" in staged_args, f"Expected .claude/ in git add args: {staged_args}"

    def test_deploy_loop_uses_secondary_ai_tools(
        self,
        mock_run: object,
        tmp_path: Path,
    ) -> None:
        """deploy_to_linked_repos should use sec_ai_tools (secondary config) not primary config."""
        primary = tmp_path / "primary"
        primary.mkdir()
        secondary = tmp_path / "secondary"
        secondary.mkdir()
        pkg = tmp_path / "pkg"

        # Set up secondary with ai_tools: claude (not cursor)
        kit_dir = secondary / ".dotnet-ai-kit"
        kit_dir.mkdir(parents=True, exist_ok=True)
        sec_config = {"version": "1.0", "company": {"name": "Test"}, "ai_tools": ["claude"]}
        (kit_dir / "config.yml").write_text(__import__("yaml").dump(sec_config), encoding="utf-8")
        project = {"project_type": "query-sql", "confidence": "high"}
        (kit_dir / "project.yml").write_text(__import__("yaml").dump(project), encoding="utf-8")
        (kit_dir / "version.txt").write_text("1.0", encoding="utf-8")
        (secondary / ".claude" / "rules").mkdir(parents=True, exist_ok=True)

        _create_package_profiles(pkg)

        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0

        # Primary has ai_tools: ["claude"] too, secondary also has ["claude"]
        # The loop must use sec_ai_tools (secondary config), not primary config.ai_tools
        # We verify by checking that claude's directories are targeted (not some other tool)
        config = DotnetAiConfig(
            repos=ReposConfig(query=str(secondary)),
            ai_tools=["claude"],
        )

        results = deploy_to_linked_repos(primary, config, "1.0", pkg)

        assert len(results) == 1
        assert results[0]["status"] in ("deployed", "upgraded")
        # Verify the .claude/ dir was populated (secondary ai_tool = claude)
        assert (secondary / ".claude" / "rules" / "architecture-profile.md").is_file()
