"""Tests for new model fields: detected_paths on DetectedProject, linked_from on DotnetAiConfig."""

from __future__ import annotations

import yaml

from dotnet_ai_kit.models import DetectedProject, DotnetAiConfig


class TestDetectedPathsField:
    """Verify detected_paths field on DetectedProject."""

    def test_default_is_none(self) -> None:
        project = DetectedProject()
        assert project.detected_paths is None

    def test_accepts_dict(self) -> None:
        paths = {
            "aggregates": "Company.Domain/Core",
            "events": "Company.Domain/Events",
            "tests": "Company.Test/Tests",
        }
        project = DetectedProject(detected_paths=paths)
        assert project.detected_paths == paths

    def test_accepts_empty_dict(self) -> None:
        project = DetectedProject(detected_paths={})
        assert project.detected_paths == {}

    def test_serializes_to_yaml(self) -> None:
        paths = {"aggregates": "Domain/Core", "events": "Domain/Events"}
        project = DetectedProject(detected_paths=paths)
        data = project.model_dump()
        yml = yaml.dump(data, default_flow_style=False)
        loaded = yaml.safe_load(yml)
        assert loaded["detected_paths"] == paths

    def test_none_serializes_to_yaml(self) -> None:
        project = DetectedProject()
        data = project.model_dump()
        yml = yaml.dump(data, default_flow_style=False)
        loaded = yaml.safe_load(yml)
        assert loaded["detected_paths"] is None


class TestLinkedFromField:
    """Verify linked_from field on DotnetAiConfig."""

    def test_default_is_none(self) -> None:
        config = DotnetAiConfig()
        assert config.linked_from is None

    def test_accepts_string(self) -> None:
        config = DotnetAiConfig(linked_from="C:/Users/dev/repos/my-command")
        assert config.linked_from == "C:/Users/dev/repos/my-command"

    def test_serializes_to_yaml(self) -> None:
        config = DotnetAiConfig(linked_from="/home/dev/repos/primary")
        data = config.model_dump()
        yml = yaml.dump(data, default_flow_style=False)
        loaded = yaml.safe_load(yml)
        assert loaded["linked_from"] == "/home/dev/repos/primary"

    def test_none_serializes_to_yaml(self) -> None:
        config = DotnetAiConfig()
        data = config.model_dump()
        yml = yaml.dump(data, default_flow_style=False)
        loaded = yaml.safe_load(yml)
        assert loaded["linked_from"] is None
