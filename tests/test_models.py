"""Tests for pydantic models: URL normalization and FeatureBrief validation."""

from __future__ import annotations

import pytest

from dotnet_ai_kit.models import FeatureBrief, ReposConfig


# ---------------------------------------------------------------------------
# T003: URL normalization tests for ReposConfig.validate_repo_path
# ---------------------------------------------------------------------------


class TestRepoPathNormalization:
    """Verify GitHub HTTPS and SSH URLs are normalized to github:org/repo."""

    def test_github_https_url(self) -> None:
        cfg = ReposConfig(command="https://github.com/acme/my-service")
        assert cfg.command == "github:acme/my-service"

    def test_github_https_url_with_git_suffix(self) -> None:
        cfg = ReposConfig(query="https://github.com/acme/my-service.git")
        assert cfg.query == "github:acme/my-service"

    def test_github_https_url_trailing_slash(self) -> None:
        cfg = ReposConfig(gateway="https://github.com/acme/my-service/")
        assert cfg.gateway == "github:acme/my-service"

    def test_github_ssh_url(self) -> None:
        cfg = ReposConfig(processor="git@github.com:acme/my-service.git")
        assert cfg.processor == "github:acme/my-service"

    def test_github_ssh_url_no_git_suffix(self) -> None:
        cfg = ReposConfig(controlpanel="git@github.com:acme/my-service")
        assert cfg.controlpanel == "github:acme/my-service"

    def test_already_normalized_github_ref(self) -> None:
        cfg = ReposConfig(command="github:acme/my-service")
        assert cfg.command == "github:acme/my-service"

    def test_local_path_unchanged(self) -> None:
        cfg = ReposConfig(command="../company-domain-command")
        assert cfg.command == "../company-domain-command"

    def test_absolute_path_unchanged(self) -> None:
        cfg = ReposConfig(query="/home/user/repos/query-service")
        assert cfg.query == "/home/user/repos/query-service"

    def test_none_stays_none(self) -> None:
        cfg = ReposConfig(command=None)
        assert cfg.command is None

    def test_whitespace_stripped(self) -> None:
        cfg = ReposConfig(command="  ../my-repo  ")
        assert cfg.command == "../my-repo"

    def test_empty_string_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            ReposConfig(command="")

    def test_whitespace_only_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            ReposConfig(command="   ")


# ---------------------------------------------------------------------------
# T004: FeatureBrief model validation tests
# ---------------------------------------------------------------------------


def _valid_brief_kwargs() -> dict:
    """Return minimal valid kwargs for FeatureBrief."""
    return {
        "feature_name": "Order Management",
        "feature_id": "001-order-management",
        "projected_date": "2026-03-30",
        "phase": "specified",
        "source_repo": "company-domain-command",
        "source_path": "../company-domain-command",
        "source_feature_path": ".dotnet-ai-kit/features/001-order-management/",
    }


class TestFeatureBrief:
    """Verify FeatureBrief phase validation and required fields."""

    def test_valid_brief(self) -> None:
        brief = FeatureBrief(**_valid_brief_kwargs())
        assert brief.feature_name == "Order Management"
        assert brief.phase == "specified"

    @pytest.mark.parametrize(
        "phase",
        ["specified", "planned", "tasks-generated", "implementing", "implemented", "blocked"],
    )
    def test_all_valid_phases(self, phase: str) -> None:
        kwargs = _valid_brief_kwargs()
        kwargs["phase"] = phase
        brief = FeatureBrief(**kwargs)
        assert brief.phase == phase

    def test_invalid_phase_rejected(self) -> None:
        kwargs = _valid_brief_kwargs()
        kwargs["phase"] = "unknown"
        with pytest.raises(ValueError, match="phase must be one of"):
            FeatureBrief(**kwargs)

    def test_phase_case_insensitive(self) -> None:
        kwargs = _valid_brief_kwargs()
        kwargs["phase"] = "Planned"
        brief = FeatureBrief(**kwargs)
        assert brief.phase == "planned"

    def test_valid_feature_id_format(self) -> None:
        kwargs = _valid_brief_kwargs()
        kwargs["feature_id"] = "042-user-sync"
        brief = FeatureBrief(**kwargs)
        assert brief.feature_id == "042-user-sync"

    def test_invalid_feature_id_rejected(self) -> None:
        kwargs = _valid_brief_kwargs()
        kwargs["feature_id"] = "order-management"
        with pytest.raises(ValueError, match="NNN-short-name"):
            FeatureBrief(**kwargs)

    def test_defaults_for_optional_fields(self) -> None:
        brief = FeatureBrief(**_valid_brief_kwargs())
        assert brief.role == ""
        assert brief.required_changes == []
        assert brief.events_produces == []
        assert brief.events_consumes == []
        assert brief.tasks == []
        assert brief.blocked_by == []
        assert brief.blocks == []
        assert brief.implementation_approach == ""

    def test_tasks_with_data(self) -> None:
        kwargs = _valid_brief_kwargs()
        kwargs["tasks"] = [
            {"id": "T006", "description": "Create Order entity", "file": "src/Entities/Order.cs", "done": False},
        ]
        brief = FeatureBrief(**kwargs)
        assert len(brief.tasks) == 1
        assert brief.tasks[0]["id"] == "T006"
