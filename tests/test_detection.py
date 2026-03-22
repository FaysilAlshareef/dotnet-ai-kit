"""Tests for detection helpers.

Note: The full project type detection algorithm has been moved to the AI
smart-detect skill (skills/detection/smart-detect/SKILL.md). These tests
cover only the remaining helper functions in detection.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dotnet_ai_kit.detection import (
    DetectionError,
    describe_architecture,
    display_detection_summary,
    grep_file,
    grep_files,
)
from dotnet_ai_kit.models import DetectedProject

# ---------------------------------------------------------------------------
# DetectionError
# ---------------------------------------------------------------------------


def test_detection_error_is_exception() -> None:
    """DetectionError should be a standard Exception subclass."""
    with pytest.raises(DetectionError, match="test error"):
        raise DetectionError("test error")


# ---------------------------------------------------------------------------
# grep_file
# ---------------------------------------------------------------------------


def test_grep_file_finds_matching_lines(tmp_path: Path) -> None:
    """grep_file should return lines matching the regex pattern."""
    cs_file = tmp_path / "Test.cs"
    cs_file.write_text(
        "using System;\n"
        "namespace Foo.Bar;\n"
        "public class MyService {}\n"
        "public class OtherService {}\n",
        encoding="utf-8",
    )

    matches = grep_file(cs_file, r"class\s+\w+Service")
    assert len(matches) == 2
    assert "MyService" in matches[0]
    assert "OtherService" in matches[1]


def test_grep_file_returns_empty_for_no_match(tmp_path: Path) -> None:
    """grep_file should return empty list when no lines match."""
    cs_file = tmp_path / "Empty.cs"
    cs_file.write_text("// nothing here\n", encoding="utf-8")

    matches = grep_file(cs_file, r"IRequestHandler")
    assert matches == []


def test_grep_file_returns_empty_for_missing_file(tmp_path: Path) -> None:
    """grep_file should return empty list for non-existent files."""
    missing = tmp_path / "does_not_exist.cs"
    matches = grep_file(missing, r"anything")
    assert matches == []


def test_grep_file_strips_results(tmp_path: Path) -> None:
    """grep_file should strip whitespace from matched lines."""
    cs_file = tmp_path / "Indented.cs"
    cs_file.write_text("    public class Foo {}\n", encoding="utf-8")

    matches = grep_file(cs_file, r"class\s+Foo")
    assert matches == ["public class Foo {}"]


# ---------------------------------------------------------------------------
# grep_files
# ---------------------------------------------------------------------------


def test_grep_files_searches_recursively(tmp_path: Path) -> None:
    """grep_files should search all matching files in subdirectories."""
    sub = tmp_path / "sub"
    sub.mkdir()

    (tmp_path / "A.cs").write_text("class Alpha {}\n", encoding="utf-8")
    (sub / "B.cs").write_text("class Beta {}\n", encoding="utf-8")
    (tmp_path / "C.txt").write_text("class Gamma {}\n", encoding="utf-8")

    matches = grep_files(tmp_path, r"class \w+")
    assert len(matches) == 2  # Only .cs files
    names = " ".join(matches)
    assert "Alpha" in names
    assert "Beta" in names


def test_grep_files_custom_glob(tmp_path: Path) -> None:
    """grep_files should respect custom glob patterns."""
    (tmp_path / "A.cs").write_text("hello\n", encoding="utf-8")
    (tmp_path / "B.txt").write_text("hello\n", encoding="utf-8")

    matches = grep_files(tmp_path, r"hello", glob_pattern="*.txt")
    assert len(matches) == 1


# ---------------------------------------------------------------------------
# describe_architecture
# ---------------------------------------------------------------------------


def test_describe_architecture_microservice_types() -> None:
    """describe_architecture should return descriptions for microservice types."""
    assert "Command" in describe_architecture("microservice", "command")
    assert "SQL" in describe_architecture("microservice", "query-sql")
    assert "Cosmos" in describe_architecture("microservice", "query-cosmos")
    assert "Processor" in describe_architecture("microservice", "processor")
    assert "Gateway" in describe_architecture("microservice", "gateway")
    assert "Blazor" in describe_architecture("microservice", "controlpanel")
    assert "Hybrid" in describe_architecture("microservice", "hybrid")


def test_describe_architecture_generic_types() -> None:
    """describe_architecture should return descriptions for generic types."""
    assert "Vertical Slice" in describe_architecture("generic", "vsa")
    assert "Clean Architecture" in describe_architecture("generic", "clean-arch")
    assert "Domain-Driven" in describe_architecture("generic", "ddd")
    assert "Modular Monolith" in describe_architecture("generic", "modular-monolith")
    assert "Generic" in describe_architecture("generic", "generic")


def test_describe_architecture_unknown_type() -> None:
    """describe_architecture should fall back for unknown types."""
    result = describe_architecture("custom", "unknown-type")
    assert "custom" in result
    assert "unknown-type" in result


# ---------------------------------------------------------------------------
# display_detection_summary
# ---------------------------------------------------------------------------


def test_display_detection_summary_renders(capsys) -> None:
    """display_detection_summary should render without errors."""
    from rich.console import Console

    console = Console(no_color=True, width=120)
    result = DetectedProject(
        mode="microservice",
        project_type="command",
        dotnet_version="10.0",
        architecture="Event-sourced Command service (CQRS write side)",
        confidence="high",
        confidence_score=0.85,
        top_signals=[
            {
                "pattern_name": "Serves gRPC endpoints",
                "signal_type": "build-config",
                "confidence": "high",
                "evidence": "MapGrpcService found",
                "is_negative": False,
            },
        ],
    )

    # Should not raise
    display_detection_summary(result, console)


def test_display_detection_summary_with_override(capsys) -> None:
    """display_detection_summary should show user override when present."""
    from rich.console import Console

    console = Console(no_color=True, width=120)
    result = DetectedProject(
        mode="generic",
        project_type="vsa",
        architecture="Vertical Slice Architecture",
        user_override="vsa",
    )

    # Should not raise
    display_detection_summary(result, console)
