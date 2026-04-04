"""Tests for deploy_to_linked_repos(): version checking, branch creation, skip logic."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import yaml

from dotnet_ai_kit.copier import deploy_to_linked_repos
from dotnet_ai_kit.models import DotnetAiConfig, ReposConfig


def _init_secondary_repo(
    repo_path: Path, project_type: str = "query-sql", version: str = "1.0",
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
        self, mock_run: object, tmp_path: Path,
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
        self, mock_run: object, tmp_path: Path,
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
        self, mock_run: object, tmp_path: Path,
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
            primary, config, "1.0", pkg,
            branch_name="chore/dotnet-ai-kit-setup",
        )

        # Verify git checkout -b was called with the branch name
        checkout_calls = [
            call
            for call in mock_run.call_args_list
            if call[0][0][:3] == ["git", "checkout", "-b"]
        ]
        assert len(checkout_calls) == 1
        assert checkout_calls[0][0][0][3] == "chore/dotnet-ai-kit-setup"

    def test_multi_digit_version_comparison(
        self, mock_run: object, tmp_path: Path,
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

    def test_uninitialized_repo_skipped(self, mock_run: object, tmp_path: Path) -> None:
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
        assert "not initialized" in results[0]["reason"]

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
        self, mock_run: object, tmp_path: Path,
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
