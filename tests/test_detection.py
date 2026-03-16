"""Tests for the project type detection algorithm."""

from __future__ import annotations

from pathlib import Path

import pytest

from dotnet_ai_kit.detection import (
    DetectionError,
    detect_project,
    grep_file,
    grep_files,
)


def _create_csproj(path: Path, target_framework: str = "net10.0") -> None:
    """Create a minimal .csproj file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '<Project Sdk="Microsoft.NET.Sdk">\n'
        "  <PropertyGroup>\n"
        f"    <TargetFramework>{target_framework}</TargetFramework>\n"
        "  </PropertyGroup>\n"
        "</Project>\n",
        encoding="utf-8",
    )


def _create_sln(path: Path) -> None:
    """Create a minimal .sln file."""
    path.write_text("Microsoft Visual Studio Solution File\n", encoding="utf-8")


def _create_cs_file(path: Path, content: str) -> None:
    """Create a C# source file with given content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_no_dotnet_project_raises_error(tmp_path: Path) -> None:
    """Detection should raise DetectionError when no .NET files exist."""
    with pytest.raises(DetectionError, match="No .sln or .csproj"):
        detect_project(tmp_path)


def test_empty_directory_raises_error(tmp_path: Path) -> None:
    """Empty directory should raise DetectionError."""
    with pytest.raises(DetectionError):
        detect_project(tmp_path)


# ---------------------------------------------------------------------------
# .NET version detection
# ---------------------------------------------------------------------------

def test_detects_dotnet_version(tmp_path: Path) -> None:
    """Should detect .NET version from csproj TargetFramework."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj", "net10.0")

    result = detect_project(tmp_path)
    assert result.dotnet_version == "10.0"


def test_detects_highest_version_from_multiple_csproj(tmp_path: Path) -> None:
    """Should pick the highest version when multiple csproj files have different versions."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "ProjectA" / "A.csproj", "net8.0")
    _create_csproj(tmp_path / "ProjectB" / "B.csproj", "net10.0")

    result = detect_project(tmp_path)
    assert result.dotnet_version == "10.0"


# ---------------------------------------------------------------------------
# Microservice pattern detection
# ---------------------------------------------------------------------------

def test_detects_command_aggregate_pattern(tmp_path: Path) -> None:
    """Should detect Command project from Aggregate<T> base class."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Domain" / "Order.cs",
        "public class Order : Aggregate<OrderId>\n{\n}\n",
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "command"


def test_detects_query_cosmos_pattern(tmp_path: Path) -> None:
    """Should detect Cosmos Query from IContainerDocument interface."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Data" / "OrderDocument.cs",
        "public class OrderDocument : IContainerDocument\n{\n}\n",
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "query-cosmos"


def test_detects_processor_pattern(tmp_path: Path) -> None:
    """Should detect Processor from IHostedService + ServiceBusSessionProcessor."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Workers" / "EventWorker.cs",
        (
            "public class EventWorker : IHostedService\n"
            "{\n"
            "    private readonly ServiceBusSessionProcessor _processor;\n"
            "}\n"
        ),
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "processor"


def test_detects_gateway_pattern(tmp_path: Path) -> None:
    """Should detect Gateway from REST Controllers + AddGrpcClient<."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Controllers" / "OrderController.cs",
        "[ApiController]\npublic class OrderController : ControllerBase\n{\n}\n",
    )
    _create_cs_file(
        tmp_path / "Program.cs",
        'builder.Services.AddGrpcClient<OrderService.OrderServiceClient>();\n',
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "gateway"


def test_detects_controlpanel_pattern(tmp_path: Path) -> None:
    """Should detect ControlPanel from Blazor + ResponseResult<T>."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Pages" / "Orders.razor",
        '@page "/orders"\n<h1>Orders</h1>\n',
    )
    _create_cs_file(
        tmp_path / "Services" / "OrderService.cs",
        "public ResponseResult<OrderDto> GetOrders() { }\n",
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "controlpanel"


# ---------------------------------------------------------------------------
# Generic architecture detection
# ---------------------------------------------------------------------------

def test_detects_clean_architecture(tmp_path: Path) -> None:
    """Should detect Clean Architecture from layer directories."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    (tmp_path / "Domain").mkdir()
    (tmp_path / "Application").mkdir()
    (tmp_path / "Infrastructure").mkdir()
    (tmp_path / "API").mkdir()

    result = detect_project(tmp_path)
    assert result.mode == "generic"
    assert result.project_type == "clean-arch"


def test_detects_vsa_from_feature_folders(tmp_path: Path) -> None:
    """Should detect Vertical Slice Architecture from Features with handlers."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    features_dir = tmp_path / "Features" / "Orders"
    features_dir.mkdir(parents=True)
    _create_cs_file(
        features_dir / "CreateOrderHandler.cs",
        "public class CreateOrderHandler { }\n",
    )

    result = detect_project(tmp_path)
    assert result.mode == "generic"
    assert result.project_type == "vsa"


def test_detects_ddd_from_bounded_contexts(tmp_path: Path) -> None:
    """Should detect DDD from BoundedContexts directory."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    (tmp_path / "BoundedContexts" / "Ordering").mkdir(parents=True)

    result = detect_project(tmp_path)
    assert result.mode == "generic"
    assert result.project_type == "ddd"


def test_defaults_to_generic_when_no_pattern(tmp_path: Path) -> None:
    """Should default to generic mode when no patterns match."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")

    result = detect_project(tmp_path)
    assert result.mode == "generic"
    assert result.project_type == "generic"


# ---------------------------------------------------------------------------
# grep helpers
# ---------------------------------------------------------------------------

def test_grep_file_finds_pattern(tmp_path: Path) -> None:
    """grep_file should return matching lines."""
    test_file = tmp_path / "test.cs"
    test_file.write_text(
        "public class OrderAggregate : Aggregate<OrderId>\n"
        "{\n"
        "    public string Name { get; set; }\n"
        "}\n",
        encoding="utf-8",
    )

    matches = grep_file(test_file, r"Aggregate<")
    assert len(matches) == 1
    assert "Aggregate<OrderId>" in matches[0]


def test_grep_file_returns_empty_for_missing_file(tmp_path: Path) -> None:
    """grep_file should return empty list for non-existent files."""
    result = grep_file(tmp_path / "nonexistent.cs", r"pattern")
    assert result == []
