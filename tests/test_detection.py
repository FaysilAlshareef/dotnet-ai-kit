"""Tests for the behavioral project type detection algorithm."""

from __future__ import annotations

from pathlib import Path

import pytest

from dotnet_ai_kit.detection import (
    DetectionError,
    _analyze_handler_behavior,
    _analyze_program_config,
    _analyze_project_structure,
    _describe_architecture,
    _display_detection_summary,
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
# Command-side detection by behavioral patterns
# ---------------------------------------------------------------------------


def test_detects_command_by_aggregate_and_commit(tmp_path: Path) -> None:
    """Should detect Command from aggregate manipulation + event commit behavior."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Domain" / "Order.cs",
        "public class Order : Aggregate<OrderId>\n{\n}\n",
    )
    _create_cs_file(
        tmp_path / "Application" / "Handlers" / "CreateOrderHandler.cs",
        (
            "public class CreateOrderHandler : IRequestHandler<CreateOrderCommand>\n"
            "{\n"
            "    private readonly IUnitOfWork _unitOfWork;\n"
            "    private readonly ICommitEventService _commitEventsService;\n"
            "    public async Task Handle(CreateOrderCommand cmd, CancellationToken ct)\n"
            "    {\n"
            "        var events = await _unitOfWork.Events.GetAllByAggregateIdAsync(cmd.Id, ct);\n"
            "        var order = Order.Create(cmd);\n"
            "        await _commitEventsService.CommitNewEventsAsync(order);\n"
            "    }\n"
            "}\n"
        ),
    )
    _create_cs_file(
        tmp_path / "Program.cs",
        "app.MapGrpcService<OrderService>();\n",
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "command"
    assert result.confidence != ""
    assert result.confidence_score > 0.0
    assert len(result.top_signals) > 0


def test_detects_command_by_command_handler(tmp_path: Path) -> None:
    """Should detect Command from ICommandHandler<T> pattern with event commit."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Domain" / "Order.cs",
        "public class Order : Aggregate<OrderId>\n{\n}\n",
    )
    _create_cs_file(
        tmp_path / "Handlers" / "CreateOrderHandler.cs",
        (
            "public class CreateOrderHandler : ICommandHandler<CreateOrderCommand>\n"
            "{\n"
            "    public async Task Handle(CreateOrderCommand cmd) {\n"
            "        var events = await _unitOfWork.Events.GetAllByAggregateIdAsync(cmd.Id, ct);\n"
            "        await _commitEventsService.CommitNewEventsAsync(order);\n"
            "    }\n"
            "}\n"
        ),
    )
    _create_cs_file(
        tmp_path / "Program.cs",
        "app.MapGrpcService<OrderService>();\n",
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "command"


def test_detects_command_by_event_store(tmp_path: Path) -> None:
    """Should detect Command from event commit pattern."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Application" / "Handlers" / "Handler.cs",
        (
            "public class CreateHandler : IRequestHandler<CreateCommand>\n"
            "{\n"
            "    private readonly ICommitEventService _commitEventsService;\n"
            "    public async Task Handle(CreateCommand cmd, CancellationToken ct) {\n"
            "        var events = await _repo.GetAllByAggregateIdAsync(cmd.Id, ct);\n"
            "        var agg = MyAggregate.Rebuild(events);\n"
            "        agg.DoSomething(cmd);\n"
            "        await _commitEventsService.CommitNewEventsAsync(agg);\n"
            "    }\n"
            "}\n"
        ),
    )
    _create_cs_file(
        tmp_path / "Domain" / "MyAggregate.cs",
        "public class MyAggregate : Aggregate<MyAggregate> { }\n",
    )
    _create_cs_file(
        tmp_path / "Program.cs",
        "app.MapGrpcService<MyService>();\n",
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "command"


# ---------------------------------------------------------------------------
# Query-sql detection by behavioral patterns
# ---------------------------------------------------------------------------


def test_detects_query_sql_by_event_save_behavior(tmp_path: Path) -> None:
    """Should detect query-sql from event handler that saves to database."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Application" / "Features" / "Events" / "OrderCreatedHandler.cs",
        (
            "public class OrderCreatedHandler : IRequestHandler<Event<OrderCreatedData>, bool>\n"
            "{\n"
            "    private readonly IUnitOfWork _unitOfWork;\n"
            "    public async Task<bool> Handle(\n"
            "        Event<OrderCreatedData> @event, CancellationToken ct)\n"
            "    {\n"
            "        var order = new Order(@event);\n"
            "        await _unitOfWork.Orders.AddAsync(order);\n"
            "        await _unitOfWork.SaveChangesAsync();\n"
            "        return true;\n"
            "    }\n"
            "}\n"
        ),
    )
    _create_cs_file(
        tmp_path / "Program.cs",
        "app.MapGrpcService<OrderQueriesService>();\n",
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "query-sql"


def test_detects_query_sql_with_servicebus_and_db(tmp_path: Path) -> None:
    """Should detect query-sql from ServiceBus listener + DB save pattern."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Application" / "Features" / "Events" / "Handler.cs",
        (
            "public class AccountCreatedHandler :\n"
            "    IRequestHandler<Event<AccountCreatedData>, bool>\n"
            "{\n"
            "    private readonly IUnitOfWork _unitOfWork;\n"
            "    public async Task<bool> Handle(\n"
            "        Event<AccountCreatedData> @event, CancellationToken ct)\n"
            "    {\n"
            "        var account = new Account(@event);\n"
            "        await _unitOfWork.Accounts.AddAsync(account);\n"
            "        await _unitOfWork.SaveChangesAsync();\n"
            "        return true;\n"
            "    }\n"
            "}\n"
        ),
    )
    _create_cs_file(
        tmp_path / "Infra" / "ServiceBus" / "Listeners" / "Listener.cs",
        (
            "public class CompetitionsListener : IHostedService\n"
            "{\n"
            "    private readonly ServiceBusSessionProcessor _processor;\n"
            "}\n"
        ),
    )
    _create_cs_file(
        tmp_path / "Program.cs",
        (
            "builder.Services.RegisterServiceBus(config);\n"
            "app.MapGrpcService<QueriesService>();\n"
        ),
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "query-sql"


# ---------------------------------------------------------------------------
# Query-cosmos detection by behavioral patterns
# ---------------------------------------------------------------------------


def test_detects_query_cosmos_by_container_document(tmp_path: Path) -> None:
    """Should detect query-cosmos from Cosmos DB usage + event handler saves."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Domain" / "Entities" / "OrderDocument.cs",
        "public class OrderDocument : IContainerDocument\n{\n}\n",
    )
    _create_cs_file(
        tmp_path / "Application" / "Features" / "Events" / "CardCreatedHandler.cs",
        (
            "public class CardCreatedHandler : IRequestHandler<Event<CardCreatedData>, bool>\n"
            "{\n"
            "    private readonly ICardCacheRepository _cacheRepository;\n"
            "    public Task<bool> Handle(Event<CardCreatedData> request, CancellationToken ct)\n"
            "    {\n"
            "        var card = CachedCard.Create(request);\n"
            "        _cacheRepository.Add(card);\n"
            "        return Task.FromResult(true);\n"
            "    }\n"
            "}\n"
        ),
    )
    _create_cs_file(
        tmp_path / "Infra" / "Persistence" / "CosmosDbExtension.cs",
        (
            "public static class CosmosDbExtension\n"
            "{\n"
            "    public static void AddCosmosDb(this IServiceCollection services) { }\n"
            "}\n"
        ),
    )
    _create_cs_file(
        tmp_path / "Infra" / "ServiceBus" / "Listener.cs",
        "private readonly ServiceBusSessionProcessor _processor;\n",
    )
    _create_cs_file(
        tmp_path / "Program.cs",
        (
            "builder.Services.UseServiceBus(config);\n"
            "app.MapGrpcService<ReportService>();\n"
        ),
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "query-cosmos"


# ---------------------------------------------------------------------------
# Processor detection by behavioral patterns
# ---------------------------------------------------------------------------


def test_detects_processor_by_event_and_grpc_forwarding(tmp_path: Path) -> None:
    """Should detect Processor when handler receives events and calls other gRPC services."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Application" / "Features" / "AccountEvents" / "AccountConfirmedHandler.cs",
        (
            "public class AccountConfirmedHandler :\n"
            "    IRequestHandler<Event<AccountConfirmedData>, bool>\n"
            "{\n"
            "    private readonly AccountCommandsClient _accountCommandsClient;\n"
            "    public async Task<bool> Handle(\n"
            "        Event<AccountConfirmedData> @event, CancellationToken ct)\n"
            "    {\n"
            "        await _accountCommandsClient.CreateFromGatewayAsync(new CreateRequest());\n"
            "        return true;\n"
            "    }\n"
            "}\n"
        ),
    )
    _create_cs_file(
        tmp_path / "Setup" / "ExternalServicesRegistration.cs",
        (
            "services.AddGrpcClient<AccountCommandsClient>((provider, configure) => {});\n"
            "services.AddGrpcClient<AccountQueriesClient>((provider, configure) => {});\n"
        ),
    )
    _create_cs_file(
        tmp_path / "Infra" / "ServiceBus" / "Client.cs",
        "public ServiceBusClient Client { get; }\n",
    )
    _create_cs_file(
        tmp_path / "Program.cs",
        (
            "builder.Services.RegisterServiceBus(config);\n"
            "builder.Services.RegisterExternalServices(config);\n"
            "app.MapGrpcService<ProcessorService>();\n"
        ),
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "processor"


def test_detects_processor_by_event_publishing(tmp_path: Path) -> None:
    """Should detect Processor when handler publishes events downstream (orchestrator pattern)."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Application" / "Features" / "PointsExchange" / "Handler.cs",
        (
            "public class PointsExchangeHandler : IRequestHandler<Event<PointsData>, bool>\n"
            "{\n"
            "    private readonly IServiceBusPublisher _publisher;\n"
            "    public async Task<bool> Handle(Event<PointsData> ev, CancellationToken ct) {\n"
            "        await _publisher.StartPublish(new Message());\n"
            "        return true;\n"
            "    }\n"
            "}\n"
        ),
    )
    _create_cs_file(
        tmp_path / "Program.cs",
        "app.MapGrpcService<ProcessorService>();\n",
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "processor"


# ---------------------------------------------------------------------------
# Gateway detection by behavioral patterns
# ---------------------------------------------------------------------------


def test_detects_gateway_by_controller_and_grpc_clients(tmp_path: Path) -> None:
    """Should detect Gateway from REST Controllers + gRPC clients (no ServiceBus)."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Controllers" / "OrderController.cs",
        "[ApiController]\npublic class OrderController : ControllerBase\n{\n}\n",
    )
    _create_cs_file(
        tmp_path / "Program.cs",
        (
            "builder.Services.AddControllersWithConfigurations();\n"
            "builder.Services.AddGrpcClients(builder.Configuration);\n"
            "builder.Services.AddSwaggerApiDocumentation(builder.Environment);\n"
            "builder.Services.AddJwtAuthentication(builder.Configuration);\n"
            "app.MapControllersWithAuthorization();\n"
        ),
    )

    result = detect_project(tmp_path)
    assert result.mode == "microservice"
    assert result.project_type == "gateway"


def test_detects_gateway_by_controller_and_addgrpcclient(tmp_path: Path) -> None:
    """Should detect Gateway from REST Controllers + AddGrpcClient<."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Controllers" / "OrderController.cs",
        "[ApiController]\npublic class OrderController : ControllerBase\n{\n}\n",
    )
    _create_cs_file(
        tmp_path / "GrpcClients" / "Registration.cs",
        "services.AddGrpcClient<OrderService.OrderServiceClient>();\n",
    )
    _create_cs_file(
        tmp_path / "Program.cs",
        (
            "builder.Services.AddControllers();\n"
            "builder.Services.AddGrpcClients(config);\n"
            "app.MapControllers();\n"
        ),
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
            "builder.Services.AddControllers();\n"
            "builder.Services.AddReverseProxy()\n"
            '    .LoadFromConfig(builder.Configuration.GetSection("ReverseProxy"));\n'
            "app.MapControllers();\n"
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
# Hybrid detection (both command + query behavioral patterns)
# ---------------------------------------------------------------------------


def test_detects_hybrid_command_and_query(tmp_path: Path) -> None:
    """Should detect hybrid when both command and query behavioral patterns are strong."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")

    # Command behavior: receives commands, manipulates domain, commits events
    _create_cs_file(
        tmp_path / "Application" / "Commands" / "CreateOrderHandler.cs",
        (
            "public class CreateOrderHandler : IRequestHandler<CreateOrderCommand>\n"
            "{\n"
            "    public async Task Handle(CreateOrderCommand cmd, CancellationToken ct) {\n"
            "        var events = await _repo.GetAllByAggregateIdAsync(cmd.Id, ct);\n"
            "        var order = Order.Rebuild(events);\n"
            "        order.Create(cmd);\n"
            "        await _commitEventsService.CommitNewEventsAsync(order);\n"
            "    }\n"
            "}\n"
        ),
    )
    _create_cs_file(
        tmp_path / "Domain" / "Order.cs",
        "public class Order : Aggregate<Order> { }\n",
    )

    # Query behavior: receives events, saves to DB
    _create_cs_file(
        tmp_path / "Application" / "Events" / "OrderCreatedHandler.cs",
        (
            "public class OrderCreatedHandler :\n"
            "    IRequestHandler<Event<OrderCreatedData>, bool>\n"
            "{\n"
            "    public async Task<bool> Handle(\n"
            "        Event<OrderCreatedData> ev, CancellationToken ct) {\n"
            "        var order = new OrderReadModel(ev);\n"
            "        await _unitOfWork.Orders.AddAsync(order);\n"
            "        await _unitOfWork.SaveChangesAsync();\n"
            "        return true;\n"
            "    }\n"
            "}\n"
        ),
    )

    _create_cs_file(
        tmp_path / "Program.cs",
        "app.MapGrpcService<OrderService>();\n",
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
    """Should detect project type from behavioral patterns even with generic naming."""
    project_dir = tmp_path / "MyProject"
    project_dir.mkdir()
    _create_sln(project_dir / "MyProject.sln")
    _create_csproj(project_dir / "src" / "MyProject" / "MyProject.csproj")
    _create_cs_file(
        project_dir / "src" / "MyProject" / "Domain" / "Order.cs",
        "public class Order : Aggregate<OrderId>\n{\n}\n",
    )
    _create_cs_file(
        project_dir / "src" / "MyProject" / "Application" / "Handlers" / "CreateHandler.cs",
        (
            "public class CreateHandler : IRequestHandler<CreateOrderCommand>\n"
            "{\n"
            "    public async Task Handle(CreateOrderCommand cmd, CancellationToken ct) {\n"
            "        var events = await _repo.GetAllByAggregateIdAsync(cmd.Id, ct);\n"
            "        var order = Order.Rebuild(events);\n"
            "        await _commitEventsService.CommitNewEventsAsync(order);\n"
            "    }\n"
            "}\n"
        ),
    )
    _create_cs_file(
        project_dir / "src" / "MyProject" / "Program.cs",
        "app.MapGrpcService<OrderService>();\n",
    )

    result = detect_project(project_dir)
    assert result.mode == "microservice"
    assert result.project_type == "command"


# ---------------------------------------------------------------------------
# Confidence scoring levels
# ---------------------------------------------------------------------------


def test_high_confidence_with_multiple_layers(tmp_path: Path) -> None:
    """All 3 layers agreeing should produce high confidence."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    # Layer 1: Program.cs with gRPC (no ServiceBus)
    _create_cs_file(
        tmp_path / "Program.cs",
        "app.MapGrpcService<OrderService>();\n",
    )
    # Layer 2: Command handlers with domain manipulation
    _create_cs_file(
        tmp_path / "Application" / "Handlers" / "CreateOrderHandler.cs",
        (
            "public class CreateOrderHandler : IRequestHandler<CreateOrderCommand>\n"
            "{\n"
            "    public async Task Handle(CreateOrderCommand cmd, CancellationToken ct) {\n"
            "        var events = await _repo.GetAllByAggregateIdAsync(cmd.Id, ct);\n"
            "        await _commitEventsService.CommitNewEventsAsync(order);\n"
            "    }\n"
            "}\n"
        ),
    )
    # Layer 3: Domain layer with aggregates
    _create_cs_file(
        tmp_path / "Domain" / "Order.cs",
        "public class Order : Aggregate<OrderId>\n{\n}\n",
    )
    _create_cs_file(
        tmp_path / "Domain" / "Events" / "OrderCreated.cs",
        "public class OrderCreated : DomainEvent { }\n",
    )

    result = detect_project(tmp_path)
    assert result.project_type == "command"
    assert result.confidence == "high"
    assert result.confidence_score > 0.7


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
    # No behavioral patterns -> generic -> low confidence
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
                "pattern_name": "Handlers manipulate domain aggregates",
                "signal_type": "code-pattern",
                "confidence": "high",
                "evidence": "Load events -> rebuild aggregate -> call method -> commit pattern",
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
    assert "Handlers manipulate domain aggregates" in output


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

    # Command behavioral patterns in domain project
    _create_cs_file(
        tmp_path / "src" / "Domain" / "Aggregates" / "Order.cs",
        "public class Order : Aggregate<OrderId>\n{\n}\n",
    )
    _create_cs_file(
        tmp_path / "src" / "Domain" / "Events" / "OrderCreated.cs",
        "public class OrderCreated : DomainEvent\n{\n}\n",
    )
    _create_cs_file(
        tmp_path / "src" / "Api" / "Handlers" / "CreateHandler.cs",
        (
            "public class CreateHandler : IRequestHandler<CreateOrderCommand>\n"
            "{\n"
            "    public async Task Handle(CreateOrderCommand cmd, CancellationToken ct) {\n"
            "        var events = await _repo.GetAllByAggregateIdAsync(cmd.Id, ct);\n"
            "        await _commitEventsService.CommitNewEventsAsync(order);\n"
            "    }\n"
            "}\n"
        ),
    )
    _create_cs_file(
        tmp_path / "src" / "Api" / "Program.cs",
        "app.MapGrpcService<OrderService>();\n",
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
# Layer 1: Program.cs configuration analysis
# ---------------------------------------------------------------------------


def test_program_config_detects_grpc(tmp_path: Path) -> None:
    """_analyze_program_config should detect gRPC service mapping."""
    _create_cs_file(
        tmp_path / "Program.cs",
        (
            "app.MapGrpcService<OrderService>();\n"
            "app.MapGrpcService<AccountService>();\n"
        ),
    )
    config = _analyze_program_config(tmp_path)
    assert config.serves_grpc is True
    assert config.serves_grpc_count == 2


def test_program_config_detects_rest(tmp_path: Path) -> None:
    """_analyze_program_config should detect REST controller mapping."""
    _create_cs_file(
        tmp_path / "Program.cs",
        "app.MapControllers();\n",
    )
    config = _analyze_program_config(tmp_path)
    assert config.serves_rest is True


def test_program_config_detects_servicebus(tmp_path: Path) -> None:
    """_analyze_program_config should detect ServiceBus registration."""
    _create_cs_file(
        tmp_path / "Program.cs",
        "builder.Services.RegisterServiceBus(config);\n",
    )
    config = _analyze_program_config(tmp_path)
    assert config.has_service_bus is True


def test_program_config_detects_grpc_clients(tmp_path: Path) -> None:
    """_analyze_program_config should detect gRPC client registration."""
    _create_cs_file(
        tmp_path / "Setup" / "ExternalServices.cs",
        "services.AddGrpcClient<OrderService.Client>();\n",
    )
    config = _analyze_program_config(tmp_path)
    assert config.has_grpc_clients is True


# ---------------------------------------------------------------------------
# Layer 2: Handler behavior analysis
# ---------------------------------------------------------------------------


def test_handler_behavior_detects_command_pattern(tmp_path: Path) -> None:
    """_analyze_handler_behavior should detect command receipt + domain manipulation."""
    _create_cs_file(
        tmp_path / "Application" / "Handlers" / "CreateHandler.cs",
        (
            "public class CreateHandler : IRequestHandler<CreateOrderCommand>\n"
            "{\n"
            "    public async Task Handle(CreateOrderCommand cmd, CancellationToken ct) {\n"
            "        var events = await _repo.GetAllByAggregateIdAsync(cmd.Id, ct);\n"
            "        var order = Aggregate<Order>.Rebuild(events);\n"
            "        await _commitEventsService.CommitNewEventsAsync(order);\n"
            "    }\n"
            "}\n"
        ),
    )
    behavior = _analyze_handler_behavior(tmp_path)
    assert behavior.receives_commands is True
    assert behavior.manipulates_domain is True


def test_handler_behavior_detects_event_save_pattern(tmp_path: Path) -> None:
    """_analyze_handler_behavior should detect event receipt + DB save."""
    _create_cs_file(
        tmp_path / "Application" / "Features" / "Events" / "Handler.cs",
        (
            "public class Handler :\n"
            "    IRequestHandler<Event<OrderCreatedData>, bool>\n"
            "{\n"
            "    public async Task<bool> Handle(\n"
            "        Event<OrderCreatedData> ev, CancellationToken ct) {\n"
            "        await _unitOfWork.SaveChangesAsync();\n"
            "        return true;\n"
            "    }\n"
            "}\n"
        ),
    )
    behavior = _analyze_handler_behavior(tmp_path)
    assert behavior.receives_events is True
    assert behavior.saves_to_database is True


def test_handler_behavior_detects_service_calls(tmp_path: Path) -> None:
    """_analyze_handler_behavior should detect outbound gRPC calls."""
    _create_cs_file(
        tmp_path / "Application" / "Handlers" / "Handler.cs",
        (
            "public class Handler : IRequestHandler<Event<Data>, bool>\n"
            "{\n"
            "    private readonly AccountCommandsClient _accountCommandsClient;\n"
            "    public async Task<bool> Handle(Event<Data> ev, CancellationToken ct) {\n"
            "        await _accountCommandsClient.CreateAsync(new Req());\n"
            "        return true;\n"
            "    }\n"
            "}\n"
        ),
    )
    behavior = _analyze_handler_behavior(tmp_path)
    assert behavior.receives_events is True
    assert behavior.calls_other_services is True


# ---------------------------------------------------------------------------
# Layer 3: Project structure analysis
# ---------------------------------------------------------------------------


def test_structure_detects_domain_layer(tmp_path: Path) -> None:
    """_analyze_project_structure should detect Domain/ directory."""
    (tmp_path / "Domain").mkdir()
    (tmp_path / "Application").mkdir()
    (tmp_path / "Infrastructure").mkdir()

    structure = _analyze_project_structure(tmp_path, [])
    assert structure.has_domain_layer is True
    assert structure.layer_count >= 3


def test_structure_detects_controllers(tmp_path: Path) -> None:
    """_analyze_project_structure should detect Controllers/ directory."""
    (tmp_path / "Controllers").mkdir()
    (tmp_path / "GrpcClients").mkdir()

    structure = _analyze_project_structure(tmp_path, [])
    assert structure.has_controllers_dir is True
    assert structure.has_grpc_clients_dir is True


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
# Confidence scoring
# ---------------------------------------------------------------------------


def test_confidence_score_between_zero_and_one(tmp_path: Path) -> None:
    """confidence_score should always be between 0.0 and 1.0."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")
    _create_cs_file(
        tmp_path / "Domain" / "Order.cs",
        "public class Order : Aggregate<OrderId>\n{\n}\n",
    )
    _create_cs_file(
        tmp_path / "Application" / "Handlers" / "Handler.cs",
        (
            "public class H : IRequestHandler<CreateOrderCommand>\n"
            "{\n"
            "    public async Task Handle(CreateOrderCommand cmd, CancellationToken ct) {\n"
            "        var events = await _repo.GetAllByAggregateIdAsync(cmd.Id, ct);\n"
            "        await _commitEventsService.CommitNewEventsAsync(order);\n"
            "    }\n"
            "}\n"
        ),
    )
    _create_cs_file(
        tmp_path / "Program.cs",
        "app.MapGrpcService<OrderService>();\n",
    )

    result = detect_project(tmp_path)
    assert 0.0 <= result.confidence_score <= 1.0


# ---------------------------------------------------------------------------
# Top signals selection
# ---------------------------------------------------------------------------


def test_top_signals_limited_to_three(tmp_path: Path) -> None:
    """Detection result should contain at most 3 top signals."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")

    # Create many signals from a command project
    _create_cs_file(
        tmp_path / "Domain" / "Order.cs",
        "public class Order : Aggregate<OrderId>\n{\n}\n",
    )
    _create_cs_file(
        tmp_path / "Application" / "Handlers" / "Handler.cs",
        (
            "public class H : IRequestHandler<CreateOrderCommand>\n"
            "{\n"
            "    public async Task Handle(CreateOrderCommand cmd, CancellationToken ct) {\n"
            "        var events = await _repo.GetAllByAggregateIdAsync(cmd.Id, ct);\n"
            "        await _commitEventsService.CommitNewEventsAsync(order);\n"
            "    }\n"
            "}\n"
        ),
    )
    _create_cs_file(
        tmp_path / "Program.cs",
        "app.MapGrpcService<OrderService>();\n",
    )

    result = detect_project(tmp_path)
    assert len(result.top_signals) <= 3


# ---------------------------------------------------------------------------
# Test exclusion of test directories
# ---------------------------------------------------------------------------


def test_excludes_test_directories(tmp_path: Path) -> None:
    """Signals from test directories should be excluded."""
    _create_sln(tmp_path / "Test.sln")
    _create_csproj(tmp_path / "Test.csproj")

    # Only put query patterns in a test directory
    _create_cs_file(
        tmp_path / "Tests" / "TestHandlers" / "Handler.cs",
        (
            "public class Handler : IRequestHandler<Event<TestData>, bool>\n"
            "{\n"
            "    await _unitOfWork.SaveChangesAsync();\n"
            "}\n"
        ),
    )

    result = detect_project(tmp_path)
    # Should be generic since the only signals are in test dirs
    assert result.project_type == "generic"
