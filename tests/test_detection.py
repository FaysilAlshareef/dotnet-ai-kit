"""Tests for the signal-based project type detection algorithm."""

from __future__ import annotations

from pathlib import Path

import pytest

from dotnet_ai_kit.detection import (
    DetectionError,
    _classify_project,
    _collect_signals,
    _describe_architecture,
    _display_detection_summary,
    _score_candidates,
    detect_project,
    grep_file,
)
from dotnet_ai_kit.models import DetectedProject


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


# ---------------------------------------------------------------------------
# Command-side detection by code patterns (no naming hints)
# ---------------------------------------------------------------------------


def test_detects_command_by_aggregate_pattern(tmp_path: Path) -> None:
    """Should detect Command project from Aggregate<T> base class without naming hints."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Domain" / "Order.cs",
        "public class Order : Aggregate<OrderId>\n{\n}\n",
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "command"
    assert result.confidence != ""
    assert result.confidence_score > 0.0
    assert len(result.top_signals) > 0


def test_detects_command_by_aggregate_root_pattern(tmp_path: Path) -> None:
    """Should detect Command from AggregateRoot base class."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Domain" / "Order.cs",
        "public class Order : AggregateRoot\n{\n}\n",
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "command"


def test_detects_command_by_command_handler(tmp_path: Path) -> None:
    """Should detect Command from ICommandHandler<T> pattern."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Handlers" / "CreateOrderHandler.cs",
        (
            "public class CreateOrderHandler : ICommandHandler<CreateOrderCommand>\n"
            "{\n"
            "    public async Task Handle(CreateOrderCommand cmd) { }\n"
            "}\n"
        ),
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "command"


def test_detects_command_by_event_store(tmp_path: Path) -> None:
    """Should detect Command from IEventStore/EventStoreClient usage."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Infrastructure" / "EventStore.cs",
        ("public class EventStoreRepository\n{\n    private readonly IEventStore _store;\n}\n"),
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "command"


# ---------------------------------------------------------------------------
# Query-sql detection by code patterns
# ---------------------------------------------------------------------------


def test_detects_query_sql_by_query_handler(tmp_path: Path) -> None:
    """Should detect query-sql from IQueryHandler<T> pattern."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Handlers" / "GetOrderHandler.cs",
        ("public class GetOrderHandler : IQueryHandler<GetOrderQuery, OrderDto>\n{\n}\n"),
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "query-sql"


def test_detects_query_sql_by_request_handler_event_pattern(tmp_path: Path) -> None:
    """Should detect query-sql from IRequestHandler<Event< pattern."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Handlers" / "OrderCreatedHandler.cs",
        (
            "public class OrderCreatedHandler :\n"
            "    IRequestHandler<Event<OrderCreatedData>, Unit>\n"
            "{\n"
            "}\n"
        ),
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "query-sql"


# ---------------------------------------------------------------------------
# Query-cosmos detection by code patterns
# ---------------------------------------------------------------------------


def test_detects_query_cosmos_by_container_document(tmp_path: Path) -> None:
    """Should detect query-cosmos from IContainerDocument interface."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Data" / "OrderDocument.cs",
        "public class OrderDocument : IContainerDocument\n{\n}\n",
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "query-cosmos"


# ---------------------------------------------------------------------------
# Processor detection by code patterns
# ---------------------------------------------------------------------------


def test_detects_processor_by_event_publishing(tmp_path: Path) -> None:
    """Should detect Processor when handler publishes events downstream (orchestrator pattern)."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Handlers" / "OrderEventHandler.cs",
        (
            "public class OrderEventHandler : IRequestHandler<Event<OrderCreatedData>, bool>\n"
            "{\n"
            "    private readonly IServiceBusPublisher _publisher;\n"
            "    public async Task Handle(Event<OrderCreatedData> ev) {\n"
            "        await _publisher.SendMessageAsync(new Message());\n"
            "    }\n"
            "}\n"
        ),
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "processor"


def test_detects_processor_by_grpc_command_forwarding(tmp_path: Path) -> None:
    """Should detect Processor when handler forwards to command services via gRPC."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Handlers" / "AccountHandler.cs",
        (
            "public class AccountHandler : IRequestHandler<Event<AccountData>, bool>\n"
            "{\n"
            "    private readonly AccountCommandsClient _commandsClient;\n"
            "    public async Task Handle(Event<AccountData> ev) {\n"
            "        await _commandsClient.ConfirmAccountAsync(new ConfirmRequest());\n"
            "    }\n"
            "}\n"
        ),
    )


# ---------------------------------------------------------------------------
# Gateway detection by code patterns
# ---------------------------------------------------------------------------


def test_detects_gateway_by_controller_and_client_protos(tmp_path: Path) -> None:
    """Should detect Gateway from REST Controllers + gRPC client-only protos."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Controllers" / "OrderController.cs",
        "[ApiController]\npublic class OrderController : ControllerBase\n{\n}\n",
    )
    _create_cs_file(
        tmp_path / "Program.cs",
        'app.MapControllers();\n',
    )
    # gRPC client-only proto reference in csproj
    (tmp_path / "Protos").mkdir()
    _create_cs_file(
        tmp_path / "Protos" / "order.cs",
        'GrpcServices="Client"\n',
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "gateway"


def test_detects_gateway_by_controller_and_grpc(tmp_path: Path) -> None:
    """Should detect Gateway from REST Controllers + AddGrpcClient<."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Controllers" / "OrderController.cs",
        "[ApiController]\npublic class OrderController : ControllerBase\n{\n}\n",
    )
    _create_cs_file(
        tmp_path / "Program.cs",
        "builder.Services.AddGrpcClient<OrderService.OrderServiceClient>();\n",
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "gateway"
    assert result.confidence_score > 0.0


def test_detects_gateway_by_yarp(tmp_path: Path) -> None:
    """Should detect Gateway from YARP reverse proxy configuration."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Program.cs",
        (
            "builder.Services.AddReverseProxy()\n"
            '    .LoadFromConfig(builder.Configuration.GetSection("ReverseProxy"));\n'
        ),
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "gateway"


# ---------------------------------------------------------------------------
# Controlpanel detection by code patterns
# ---------------------------------------------------------------------------


def test_detects_controlpanel_by_blazor(tmp_path: Path) -> None:
    """Should detect ControlPanel from Blazor/.razor files."""
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


def test_detects_controlpanel_blazor_only(tmp_path: Path) -> None:
    """Should detect ControlPanel from Blazor component alone (high-confidence signal)."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Pages" / "Index.razor",
        '@page "/"\n<h1>Home</h1>\n',
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "controlpanel"


# ---------------------------------------------------------------------------
# Hybrid detection (both command + query patterns strong)
# ---------------------------------------------------------------------------


def test_detects_hybrid_command_and_query(tmp_path: Path) -> None:
    """Should detect hybrid when both command and query patterns are strong."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")

    # Strong command signals: aggregate + command handler + event store
    _create_cs_file(
        tmp_path / "Domain" / "Order.cs",
        "public class Order : Aggregate<OrderId>\n{\n}\n",
    )
    _create_cs_file(
        tmp_path / "Handlers" / "CreateOrderHandler.cs",
        ("public class CreateOrderHandler : ICommandHandler<CreateOrderCommand>\n{\n}\n"),
    )

    # Strong query signals: query handler + request handler event pattern + hosted service
    _create_cs_file(
        tmp_path / "Queries" / "GetOrderHandler.cs",
        ("public class GetOrderHandler : IQueryHandler<GetOrderQuery, OrderDto>\n{\n}\n"),
    )
    _create_cs_file(
        tmp_path / "Queries" / "OrderCreatedHandler.cs",
        (
            "public class OrderCreatedHandler :\n"
            "    IRequestHandler<Event<OrderCreatedData>, Unit>\n"
            "{\n"
            "}\n"
        ),
    )
    _create_cs_file(
        tmp_path / "Workers" / "ProjectionWorker.cs",
        ("public class ProjectionWorker : BackgroundService\n{\n}\n"),
    )

    result = detect_project(tmp_path)
    assert result.project_type == "hybrid"
    assert result.mode == "microservice"
    assert result.confidence != ""
    assert result.confidence_score > 0.0


# ---------------------------------------------------------------------------
# Detection without naming hints (generically named project)
# ---------------------------------------------------------------------------


def test_detection_without_naming_hints(tmp_path: Path) -> None:
    """Should detect project type from code patterns even with generic naming."""
    project_dir = tmp_path / "MyProject"
    project_dir.mkdir()
    _create_sln(project_dir / "MyProject.sln")
    _create_csproj(project_dir / "src" / "MyProject" / "MyProject.csproj")
    _create_cs_file(
        project_dir / "src" / "MyProject" / "Domain" / "Order.cs",
        "public class Order : Aggregate<OrderId>\n{\n}\n",
    )

    result = detect_project(project_dir)
    assert result.mode == "microservice"
    assert result.project_type == "command"


# ---------------------------------------------------------------------------
# Confidence scoring levels
# ---------------------------------------------------------------------------


def test_high_confidence_with_multiple_signals(tmp_path: Path) -> None:
    """Multiple strong signals should produce high confidence."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    # Multiple high-confidence command signals
    _create_cs_file(
        tmp_path / "Domain" / "Order.cs",
        "public class Order : Aggregate<OrderId>\n{\n}\n",
    )
    _create_cs_file(
        tmp_path / "Handlers" / "CreateOrderHandler.cs",
        "public class CreateOrderHandler : ICommandHandler<CreateOrderCommand> { }\n",
    )
    _create_cs_file(
        tmp_path / "Infrastructure" / "EventStore.cs",
        "private readonly IEventStore _store;\n",
    )
    _create_cs_file(
        tmp_path / "Domain" / "Events" / "OrderCreated.cs",
        "public class OrderCreated : DomainEvent { }\n",
    )
    _create_cs_file(
        tmp_path / "Infrastructure" / "Outbox.cs",
        "public class OutboxMessage { }\n",
    )
    _create_cs_file(
        tmp_path / "Infrastructure" / "CommitService.cs",
        "public class CommitService : ICommitEventService { }\n",
    )
    _create_cs_file(
        tmp_path / "Program.cs",
        "app.MapGrpcService<OrderCommandService>();\n",
    )

    result = detect_project(tmp_path)
    assert result.project_type == "command"
    assert result.confidence == "high"
    assert result.confidence_score > 0.8


def test_low_confidence_with_weak_signals(tmp_path: Path) -> None:
    """A single weak signal should produce low confidence."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    # Only a low-confidence signal: private setters
    _create_cs_file(
        tmp_path / "Models" / "Order.cs",
        "public string Name { private set; }\n",
    )

    result = detect_project(tmp_path)
    # Low-weight signal — may result in low confidence
    assert result.confidence_score <= 0.5


def test_no_signals_gives_generic(tmp_path: Path) -> None:
    """No matching patterns should result in generic with low confidence."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")

    result = detect_project(tmp_path)
    assert result.mode == "generic"
    assert result.project_type == "generic"
    assert result.confidence_score == 0.0


# ---------------------------------------------------------------------------
# Detection summary output format
# ---------------------------------------------------------------------------


def test_display_detection_summary_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """_display_detection_summary should produce formatted output."""
    from rich.console import Console

    result = DetectedProject(
        mode="microservice",
        project_type="command",
        dotnet_version="10.0",
        architecture="Event-sourced Command service (CQRS write side)",
        confidence="high",
        confidence_score=0.85,
        top_signals=[
            {
                "pattern_name": "AggregateRoot base class",
                "signal_type": "code-pattern",
                "confidence": "high",
                "evidence": "Order.cs: public class Order : Aggregate<OrderId>",
                "is_negative": False,
            },
        ],
    )

    console = Console(file=None, force_terminal=False, width=120)
    # Capture via a string buffer
    from io import StringIO

    buf = StringIO()
    console = Console(file=buf, force_terminal=False, width=120)
    _display_detection_summary(result, console)
    output = buf.getvalue()

    assert "Detection Summary" in output
    assert "command" in output
    assert "microservice" in output
    assert "10.0" in output
    assert "AggregateRoot base class" in output


# ---------------------------------------------------------------------------
# Architecture pattern detection (structural signals)
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


def test_detects_modular_monolith(tmp_path: Path) -> None:
    """Should detect Modular Monolith from Modules directory."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    (tmp_path / "Modules" / "Orders").mkdir(parents=True)

    result = detect_project(tmp_path)
    assert result.mode == "generic"
    assert result.project_type == "modular-monolith"


# ---------------------------------------------------------------------------
# Multi-project solution detection
# ---------------------------------------------------------------------------


def test_multi_project_solution(tmp_path: Path) -> None:
    """Should handle multi-project solutions and pick strongest signals."""
    _create_sln(tmp_path / "Solution.sln")
    _create_csproj(tmp_path / "src" / "Domain" / "Domain.csproj")
    _create_csproj(tmp_path / "src" / "Api" / "Api.csproj")
    _create_csproj(tmp_path / "src" / "Infrastructure" / "Infrastructure.csproj")

    # Command patterns in domain project
    _create_cs_file(
        tmp_path / "src" / "Domain" / "Aggregates" / "Order.cs",
        "public class Order : Aggregate<OrderId>\n{\n}\n",
    )
    _create_cs_file(
        tmp_path / "src" / "Domain" / "Events" / "OrderCreated.cs",
        "public class OrderCreated : DomainEvent\n{\n}\n",
    )
    _create_cs_file(
        tmp_path / "src" / "Infrastructure" / "EventStore.cs",
        "private readonly IEventStore _store;\n",
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "command"
    assert result.dotnet_version == "10.0"


# ---------------------------------------------------------------------------
# Non-standard framework fallback
# ---------------------------------------------------------------------------


def test_defaults_to_generic_when_no_pattern(tmp_path: Path) -> None:
    """Should default to generic mode when no patterns match."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")

    result = detect_project(tmp_path)
    assert result.mode == "generic"
    assert result.project_type == "generic"
    assert result.confidence_score == 0.0
    assert result.confidence == "low"


def test_generic_fallback_with_plain_code(tmp_path: Path) -> None:
    """Project with no recognizable patterns should get generic + low confidence."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Program.cs",
        ('using System;\nConsole.WriteLine("Hello World");\n'),
    )

    result = detect_project(tmp_path)
    assert result.mode == "generic"
    assert result.project_type == "generic"
    assert result.confidence == "low"
    assert result.confidence_score == 0.0


# ---------------------------------------------------------------------------
# Naming signals (supplementary, not primary)
# ---------------------------------------------------------------------------


def test_name_signals_supplement_code_patterns(tmp_path: Path) -> None:
    """Naming signals should supplement code patterns, not override them."""
    project_dir = tmp_path / "Acme.Order.Queries"
    project_dir.mkdir()
    _create_sln(project_dir / "Acme.Order.Queries.sln")
    _create_csproj(project_dir / "src" / "Data" / "Data.csproj")
    _create_cs_file(
        project_dir / "src" / "Data" / "OrderDocument.cs",
        "public class OrderDocument : IContainerDocument\n{\n}\n",
    )

    result = detect_project(project_dir)
    assert result.mode == "microservice"
    # IContainerDocument (high) should beat the .Queries naming signal (medium)
    assert result.project_type == "query-cosmos"


def test_naming_signals_returned(tmp_path: Path) -> None:
    """_detect_from_name should return DetectionSignal objects with signal_type='naming'."""
    from dotnet_ai_kit.detection import _detect_from_name

    project_dir = tmp_path / "Acme.Order.Commands"
    project_dir.mkdir()
    _create_sln(project_dir / "Acme.Order.Commands.sln")
    csproj = project_dir / "src" / "App" / "App.csproj"
    _create_csproj(csproj)

    signals = _detect_from_name(project_dir, [csproj])
    assert len(signals) >= 1
    assert all(s.signal_type == "naming" for s in signals)
    assert any(s.target_project_type == "command" for s in signals)


# ---------------------------------------------------------------------------
# Structural signals
# ---------------------------------------------------------------------------


def test_structural_signals_returned(tmp_path: Path) -> None:
    """_detect_generic should return DetectionSignal objects with signal_type='structural'."""
    from dotnet_ai_kit.detection import _detect_generic

    (tmp_path / "Domain").mkdir()
    (tmp_path / "Application").mkdir()
    (tmp_path / "Infrastructure").mkdir()

    signals = _detect_generic(tmp_path)
    assert len(signals) >= 1
    assert all(s.signal_type == "structural" for s in signals)
    assert any(s.target_project_type == "clean-arch" for s in signals)


# ---------------------------------------------------------------------------
# Score candidates
# ---------------------------------------------------------------------------


def test_score_candidates_aggregation(tmp_path: Path) -> None:
    """_score_candidates should aggregate positive and negative signal weights."""
    from dotnet_ai_kit.models import DetectionSignal

    signals = [
        DetectionSignal(
            pattern_name="AggregateRoot base class",
            signal_type="code-pattern",
            target_project_type="command",
            confidence="high",
            weight=3,
            is_negative=False,
        ),
        DetectionSignal(
            pattern_name="ICommandHandler",
            signal_type="code-pattern",
            target_project_type="command",
            confidence="high",
            weight=3,
            is_negative=False,
        ),
        DetectionSignal(
            pattern_name="Query handler in command project",
            signal_type="code-pattern",
            target_project_type="command",
            confidence="medium",
            weight=2,
            is_negative=True,
        ),
    ]

    cards = _score_candidates(signals)
    assert "command" in cards
    card = cards["command"]
    assert card.positive_score == 6.0
    assert card.negative_score == 2.0
    assert card.net_score == 4.0
    assert card.signal_count == 3


# ---------------------------------------------------------------------------
# Classify project
# ---------------------------------------------------------------------------


def test_classify_picks_highest_net_score(tmp_path: Path) -> None:
    """_classify_project should pick the candidate with highest net score."""
    from dotnet_ai_kit.models import DetectionSignal

    signals = [
        DetectionSignal(
            pattern_name="AggregateRoot base class",
            signal_type="code-pattern",
            target_project_type="command",
            confidence="high",
            weight=3,
            is_negative=False,
        ),
        DetectionSignal(
            pattern_name="API Controller",
            signal_type="code-pattern",
            target_project_type="gateway",
            confidence="medium",
            weight=2,
            is_negative=False,
        ),
    ]

    cards = _score_candidates(signals)
    mode, ptype, conf_label, conf_score, top = _classify_project(cards, signals, tmp_path)
    assert ptype == "command"
    assert mode == "microservice"


def test_classify_empty_scorecards_gives_generic(tmp_path: Path) -> None:
    """Empty scorecards should result in generic classification."""
    mode, ptype, conf_label, conf_score, top = _classify_project({}, [], tmp_path)
    assert ptype == "generic"
    assert mode == "generic"
    assert conf_label == "low"
    assert conf_score == 0.0


# ---------------------------------------------------------------------------
# Describe architecture
# ---------------------------------------------------------------------------


def test_describe_architecture_hybrid() -> None:
    """_describe_architecture should handle the 'hybrid' type."""
    desc = _describe_architecture("microservice", "hybrid")
    assert "Hybrid" in desc
    assert "CQRS" in desc


def test_describe_architecture_all_types() -> None:
    """All known project types should have descriptions."""
    known_types = [
        ("microservice", "command"),
        ("microservice", "query-sql"),
        ("microservice", "query-cosmos"),
        ("microservice", "processor"),
        ("microservice", "gateway"),
        ("microservice", "controlpanel"),
        ("microservice", "hybrid"),
        ("generic", "vsa"),
        ("generic", "clean-arch"),
        ("generic", "ddd"),
        ("generic", "modular-monolith"),
        ("generic", "generic"),
    ]
    for mode, ptype in known_types:
        desc = _describe_architecture(mode, ptype)
        assert desc, f"No description for {mode}/{ptype}"
        # Should not fall through to default format
        assert " - " not in desc or ptype == "unknown"


# ---------------------------------------------------------------------------
# Negative signal impact
# ---------------------------------------------------------------------------


def test_negative_signals_reduce_score(tmp_path: Path) -> None:
    """Negative signals should reduce the net score for their target type."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")

    # Gateway positive signal
    _create_cs_file(
        tmp_path / "Controllers" / "OrderController.cs",
        "[ApiController]\npublic class OrderController : ControllerBase { }\n",
    )
    # Gateway negative signal (direct DB access)
    _create_cs_file(
        tmp_path / "Data" / "Context.cs",
        "public class AppDbContext : DbContext { }\n",
    )

    csproj_files = list(tmp_path.rglob("*.csproj"))
    signals = _collect_signals(tmp_path, csproj_files)
    cards = _score_candidates(signals)

    if "gateway" in cards:
        card = cards["gateway"]
        assert card.negative_score > 0
        assert card.net_score < card.positive_score


# ---------------------------------------------------------------------------
# Top signals selection
# ---------------------------------------------------------------------------


def test_top_signals_limited_to_three(tmp_path: Path) -> None:
    """Detection result should contain at most 3 top signals."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")

    # Create many command signals
    _create_cs_file(
        tmp_path / "Domain" / "Order.cs",
        "public class Order : Aggregate<OrderId>\n{\n}\n",
    )
    _create_cs_file(
        tmp_path / "Handlers" / "Handler.cs",
        "public class H : ICommandHandler<Cmd> { }\n",
    )
    _create_cs_file(
        tmp_path / "Events" / "Event.cs",
        "public class E : DomainEvent { }\n",
    )
    _create_cs_file(
        tmp_path / "Infrastructure" / "Outbox.cs",
        "public class OutboxMessage { }\n",
    )
    _create_cs_file(
        tmp_path / "Infrastructure" / "Store.cs",
        "private readonly IEventStore _store;\n",
    )

    result = detect_project(tmp_path)
    assert len(result.top_signals) <= 3


# ---------------------------------------------------------------------------
# Confidence score normalization
# ---------------------------------------------------------------------------


def test_confidence_score_between_zero_and_one(tmp_path: Path) -> None:
    """confidence_score should always be between 0.0 and 1.0."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Domain" / "Order.cs",
        "public class Order : Aggregate<OrderId>\n{\n}\n",
    )

    result = detect_project(tmp_path)
    assert 0.0 <= result.confidence_score <= 1.0
