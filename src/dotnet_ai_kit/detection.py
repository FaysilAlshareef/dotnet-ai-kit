"""Project type detection algorithm for dotnet-ai-kit.

Uses 3-layer behavioral analysis instead of keyword matching:
  Layer 1: Program.cs / Startup configuration analysis
  Layer 2: Handler behavior analysis (input/processing/output patterns)
  Layer 3: Project structure analysis (folder layout)

Classification is deterministic: rules are checked in order, first match wins.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dotnet_ai_kit.models import (
    _CONFIDENCE_WEIGHTS,
    DetectedProject,
    DetectionSignal,
)


class DetectionError(Exception):
    """Raised when project detection fails."""


# ---------------------------------------------------------------------------
# Layer 1: Program.cs / Startup Configuration Analysis
# ---------------------------------------------------------------------------


@dataclass
class ProgramConfig:
    """What the application configures at startup."""

    serves_grpc: bool = False
    serves_grpc_count: int = 0
    serves_rest: bool = False
    has_service_bus: bool = False
    has_grpc_clients: bool = False
    has_reverse_proxy: bool = False
    has_database: bool = False
    has_auth: bool = False
    has_swagger: bool = False


def _analyze_program_config(root: Path) -> ProgramConfig:
    """Parse Program.cs / Startup.cs to understand app configuration.

    Reads Program.cs (or Startup.cs) content and checks for behavioral
    patterns indicating what the application serves and depends on.
    """
    config = ProgramConfig()

    # Find Program.cs and Startup.cs files (exclude test dirs)
    program_files: list[Path] = []
    for name in ("Program.cs", "Startup.cs"):
        for f in root.rglob(name):
            if not _is_test_path(f, root):
                program_files.append(f)

    # Also check DI registration files (*.cs in Setup/, Registration/, etc.)
    registration_dirs = ("Setup", "Registration", "ServiceRegistration",
                         "ServicesRegistration", "Extensions", "DependencyInjection")
    for reg_dir_name in registration_dirs:
        for reg_dir in root.rglob(reg_dir_name):
            if reg_dir.is_dir() and not _is_test_path(reg_dir, root):
                for f in reg_dir.rglob("*.cs"):
                    if not _is_test_path(f, root):
                        program_files.append(f)

    all_text = ""
    for pf in program_files:
        try:
            all_text += pf.read_text(encoding="utf-8", errors="replace") + "\n"
        except OSError:
            continue

    if not all_text:
        return config

    # Serves gRPC: MapGrpcService<> or MapGrpc
    grpc_map_matches = re.findall(r"MapGrpcService<", all_text)
    if grpc_map_matches:
        config.serves_grpc = True
        config.serves_grpc_count = len(grpc_map_matches)

    # Serves REST: MapController / MapControllerRoute / AddControllers
    if re.search(
        r"(?:MapControllers|MapControllerRoute|AddControllers"
        r"|AddControllersWithConfigurations)",
        all_text,
    ):
        config.serves_rest = True

    # Has ServiceBus: ServiceBus/queue/topic registration
    if re.search(
        r"(?:ServiceBus|RegisterServiceBus|UseServiceBus|AddServiceBus|"
        r"ServiceBusClient|ServiceBusProcessor|ServiceBusSessionProcessor|"
        r"AddMassTransit|UseRabbitMq|AddRebus)",
        all_text,
    ):
        config.has_service_bus = True

    # Has gRPC clients: AddGrpcClient<> / RegisterExternalServices
    if re.search(r"(?:AddGrpcClient<|RegisterExternalServices|AddGrpcClients)", all_text):
        config.has_grpc_clients = True

    # Has reverse proxy: YARP / reverse proxy configuration
    if re.search(r"(?:AddReverseProxy|ReverseProxy|Yarp)", all_text):
        config.has_reverse_proxy = True

    # Has database: AddDbContext / AddCosmosDb / connection string patterns / EF
    if re.search(
        r"(?:AddDbContext|AddCosmosDb|UseSqlServer|UseNpgsql|UseSqlite|"
        r"CosmosClient|CosmosDb|ConnectionString|AddEntityFramework)",
        all_text,
    ):
        config.has_database = True

    # Has auth: JWT / Authentication / Authorization
    if re.search(
        r"(?:AddJwt|AddAuthentication|AddAuthorization|UseAuthentication|UseAuthorization|"
        r"JwtBearer|AddIdentity)",
        all_text,
    ):
        config.has_auth = True

    # Has swagger: AddSwagger / UseSwagger / AddOpenApi
    if re.search(
        r"(?:AddSwagger|UseSwagger|AddOpenApi|UseOpenApi|"
        r"AddSwaggerGen|AddSwaggerApiDocumentation|AddOpenApiDocumentation)",
        all_text,
    ):
        config.has_swagger = True

    return config


# ---------------------------------------------------------------------------
# Layer 2: Handler Behavior Analysis
# ---------------------------------------------------------------------------


@dataclass
class HandlerBehavior:
    """What handlers/services DO — their input/processing/output patterns."""

    # Input patterns
    receives_commands: bool = False
    receives_events: bool = False
    receives_http: bool = False

    # Processing patterns
    manipulates_domain: bool = False
    saves_to_database: bool = False
    calls_other_services: bool = False
    publishes_messages: bool = False

    # Output patterns
    returns_data: bool = False
    returns_ack: bool = False


def _analyze_handler_behavior(root: Path) -> HandlerBehavior:
    """Find handler/service files and analyze their behavioral patterns.

    Looks in Application/, Handlers/, Features/, Controllers/, Services/
    directories and reads each file to detect data flow patterns.
    """
    behavior = HandlerBehavior()

    # Collect handler/service files from relevant directories
    handler_dirs = ("Application", "Handlers", "Features", "Controllers",
                    "Services", "EventHandlers", "CommandHandlers", "QueryHandlers")

    handler_files: list[Path] = []
    for dir_name in handler_dirs:
        for d in root.rglob(dir_name):
            if d.is_dir() and not _is_test_path(d, root):
                for f in d.rglob("*.cs"):
                    if not _is_test_path(f, root):
                        handler_files.append(f)

    # Deduplicate
    seen_paths: set[str] = set()
    unique_files: list[Path] = []
    for f in handler_files:
        key = str(f)
        if key not in seen_paths:
            seen_paths.add(key)
            unique_files.append(f)

    # Analyze each file for behavioral patterns
    for file_path in unique_files:
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        _analyze_single_handler(text, behavior)

    return behavior


def _analyze_single_handler(text: str, behavior: HandlerBehavior) -> None:
    """Analyze a single handler file's text for behavioral patterns."""

    # --- Input patterns ---

    # Receives commands: handler takes a command-like parameter, returns void/Task/Unit
    # Pattern: IRequestHandler<SomeCommand> (no second type param or Unit)
    # or ICommandHandler<>
    if re.search(r"IRequestHandler<\w+Command\s*>", text):
        behavior.receives_commands = True
    if re.search(r"ICommandHandler<", text):
        behavior.receives_commands = True
    # Handler that takes a command and commits events (behavioral: the method
    # loads aggregate, calls domain method, commits)
    if re.search(r"CommitNewEventsAsync|CommitEventsAsync", text):
        behavior.receives_commands = True

    # Receives events: handler takes event-like parameter, returns bool
    # Pattern: IRequestHandler<Event<SomeData>, bool>
    if re.search(r"IRequestHandler<.*Event<.*>,\s*bool>", text):
        behavior.receives_events = True
    # Also event notification handlers
    if re.search(r"INotificationHandler<", text):
        behavior.receives_events = True

    # Receives HTTP: controller actions
    if re.search(r"\[ApiController\]|ControllerBase|Controller\b.*:\s*ControllerBase", text):
        behavior.receives_http = True
    if re.search(r"\[Http(?:Get|Post|Put|Delete|Patch)\]", text):
        behavior.receives_http = True

    # --- Processing patterns ---

    # Manipulates domain: loads from event store, calls methods on aggregates, commits
    # Behavioral: load events by aggregate ID -> rebuild aggregate -> call method -> persist
    if re.search(r"GetAllByAggregateIdAsync", text) and re.search(
        r"CommitNewEventsAsync|CommitEventsAsync", text
    ):
        behavior.manipulates_domain = True
    # Also: creates aggregate and commits
    if re.search(r"Aggregate<|AggregateRoot", text) and re.search(
        r"CommitNewEventsAsync|CommitEventsAsync", text
    ):
        behavior.manipulates_domain = True

    # Saves to database: calls save/add/update on repositories/dbcontext/cache
    if re.search(
        r"SaveChangesAsync|\.SaveAsync|_unitOfWork\b.*Save|"
        r"_context\.\w+\.Add|_repository\.\w*Add|"
        r"_cacheRepository\.\w*Add|"
        r"\.AddAsync\(|\.UpdateAsync\(|"
        r"_\w+Repository\.Add\(",
        text,
    ):
        behavior.saves_to_database = True

    # Calls other services: makes outbound gRPC/HTTP calls
    # Behavioral: has injected client fields that call async methods
    if re.search(r"\w+Client\s+_\w+", text) and re.search(r"_\w+Client\.\w+Async\(", text):
        behavior.calls_other_services = True
    # Also: HttpClient usage
    if re.search(r"_httpClient\.\w+Async|IHttpClientFactory", text):
        behavior.calls_other_services = True

    # Publishes messages: sends to message bus/queue/topic
    if re.search(
        r"_publisher\.\w+|_sender\.\w+Send|"
        r"PublishMessageAsync|SendMessageAsync|StartPublish|"
        r"IServiceBusPublisher|IEventPublisher|IMessagePublisher|"
        r"IPublisher\b",
        text,
    ):
        behavior.publishes_messages = True

    # --- Output patterns ---

    # Returns data: handlers that return DTOs/response objects
    if re.search(r"IRequestHandler<\w+,\s*\w+(?:Dto|Response|Model|Result)\w*>", text):
        behavior.returns_data = True
    if re.search(r"IQueryHandler<", text):
        behavior.returns_data = True

    # Returns ack: handlers that return bool/Unit
    if re.search(r"IRequestHandler<.*,\s*(?:bool|Unit)>", text):
        behavior.returns_ack = True
    # Void-returning command handlers
    if re.search(r"IRequestHandler<\w+Command\s*>", text):
        behavior.returns_ack = True


# ---------------------------------------------------------------------------
# Layer 3: Project Structure Analysis
# ---------------------------------------------------------------------------


@dataclass
class ProjectStructure:
    """Folder layout and project references."""

    has_domain_layer: bool = False
    has_aggregates: bool = False
    has_entities: bool = False
    has_commands_dir: bool = False
    has_queries_dir: bool = False
    has_event_handlers_dir: bool = False
    has_listeners_dir: bool = False
    has_outbox_dir: bool = False
    has_controllers_dir: bool = False
    has_grpc_clients_dir: bool = False
    has_features_dir: bool = False
    has_modules_dir: bool = False
    has_bounded_contexts: bool = False
    layer_count: int = 0
    project_count: int = 0


def _analyze_project_structure(root: Path, csproj_files: list[Path]) -> ProjectStructure:
    """Analyze folder layout and project references."""
    structure = ProjectStructure()
    structure.project_count = len(csproj_files)

    # Gather all directory names (case-insensitive) across the project
    # Include both the full directory name AND the last segment after '.'
    # to handle .NET naming like "Company.Project.Domain" -> "domain"
    all_dir_names: set[str] = set()
    try:
        for d in root.rglob("*"):
            if d.is_dir() and not _is_test_path(d, root) and ".git" not in d.parts:
                dir_name_lower = d.name.lower()
                all_dir_names.add(dir_name_lower)
                # Also add last segment after dot (e.g. "Anis.Competition.Domain" -> "domain")
                if "." in dir_name_lower:
                    last_segment = dir_name_lower.rsplit(".", 1)[-1]
                    all_dir_names.add(last_segment)
    except OSError:
        pass

    # Domain layer
    if "domain" in all_dir_names:
        structure.has_domain_layer = True

    # Aggregates
    if "aggregates" in all_dir_names or "core" in all_dir_names:
        # Check if Core/Aggregates contain aggregate classes
        structure.has_aggregates = True

    # Entities
    if "entities" in all_dir_names or "models" in all_dir_names:
        structure.has_entities = True

    # Commands directory
    if "commands" in all_dir_names or "commandhandlers" in all_dir_names:
        structure.has_commands_dir = True

    # Queries directory
    if "queries" in all_dir_names or "queryhandlers" in all_dir_names:
        structure.has_queries_dir = True

    # Event handlers directory
    if "eventhandlers" in all_dir_names or "events" in all_dir_names:
        structure.has_event_handlers_dir = True

    # Listeners directory (ServiceBus listeners)
    if "listeners" in all_dir_names or "servicebus" in all_dir_names:
        structure.has_listeners_dir = True

    # Outbox
    if "outbox" in all_dir_names:
        structure.has_outbox_dir = True

    # Controllers
    if "controllers" in all_dir_names:
        structure.has_controllers_dir = True

    # gRPC clients directory
    if "grpcclients" in all_dir_names or "protos" in all_dir_names:
        structure.has_grpc_clients_dir = True

    # Features (VSA indicator)
    if "features" in all_dir_names:
        structure.has_features_dir = True

    # Modules (modular monolith)
    if "modules" in all_dir_names:
        structure.has_modules_dir = True

    # Bounded contexts
    if "boundedcontexts" in all_dir_names or "contexts" in all_dir_names:
        structure.has_bounded_contexts = True

    # Count distinct layers
    layer_names = {"domain", "application", "infrastructure", "infra",
                   "presentation", "api", "web", "grpc"}
    structure.layer_count = len(layer_names & all_dir_names)

    return structure


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TEST_DIR_NAMES = {"test", "tests", "test.live", "test.integration", "test.unit"}


def _is_test_path(p: Path, root: Path) -> bool:
    """Check if a path is within a test directory."""
    try:
        rel = p.relative_to(root)
    except ValueError:
        return False
    return any(
        part.lower().rstrip("s") == "test" or part.lower() in _TEST_DIR_NAMES
        for part in rel.parts
    )


def _has_cosmos(root: Path) -> bool:
    """Check if the project uses Cosmos DB."""
    for f in root.rglob("*.cs"):
        if _is_test_path(f, root):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if re.search(
            r"(?:CosmosClient|CosmosDb|IContainerDocument"
            r"|Microsoft\.Azure\.Cosmos)",
            text,
        ):
            return True
    # Also check csproj for Cosmos packages
    for f in root.rglob("*.csproj"):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if re.search(r"(?:Microsoft\.Azure\.Cosmos|CosmosDb)", text):
            return True
    return False


def _has_blazor(root: Path) -> bool:
    """Check if the project has Blazor components."""
    razor_files = list(root.rglob("*.razor"))
    return len(razor_files) > 0


def _has_feature_handlers(root: Path) -> bool:
    """Check if Features/ directories contain handler files."""
    for features_dir in root.rglob("Features"):
        if features_dir.is_dir() and not _is_test_path(features_dir, root):
            handlers = list(features_dir.rglob("*Handler.cs"))
            if handlers:
                return True
    return False


# ---------------------------------------------------------------------------
# Classification logic (deterministic rules)
# ---------------------------------------------------------------------------


def _classify(
    config: ProgramConfig,
    behavior: HandlerBehavior,
    structure: ProjectStructure,
    root: Path,
) -> tuple[str, list[DetectionSignal]]:
    """Classify project type using deterministic rules on behavioral analysis.

    Returns (project_type, signals) where signals are the top evidence.
    Rules are checked in order; first match wins.
    """
    signals: list[DetectionSignal] = []

    # --- Collect evidence signals for all layers ---

    # Layer 1 signals
    if config.serves_grpc:
        signals.append(_make_signal(
            "Serves gRPC endpoints",
            "build-config",
            f"MapGrpcService found ({config.serves_grpc_count} services)",
        ))
    if config.serves_rest:
        signals.append(_make_signal(
            "Serves REST endpoints",
            "build-config",
            "MapControllers or AddControllers found",
        ))
    if config.has_service_bus:
        signals.append(_make_signal(
            "ServiceBus/message bus configured",
            "build-config",
            "ServiceBus registration found in startup",
        ))
    if config.has_grpc_clients:
        signals.append(_make_signal(
            "gRPC clients configured",
            "build-config",
            "AddGrpcClient or RegisterExternalServices found",
        ))
    if config.has_database:
        signals.append(_make_signal(
            "Database configured",
            "build-config",
            "Database context or connection found in startup",
        ))
    if config.has_swagger:
        signals.append(_make_signal(
            "Swagger/OpenAPI configured",
            "build-config",
            "Swagger or OpenAPI documentation enabled",
        ))

    # Layer 2 signals
    if behavior.receives_commands:
        signals.append(_make_signal(
            "Handlers receive commands",
            "code-pattern",
            "Command handler pattern detected (command in, void/Unit out)",
        ))
    if behavior.receives_events:
        signals.append(_make_signal(
            "Handlers receive events",
            "code-pattern",
            "Event handler pattern detected (event in, bool out)",
        ))
    if behavior.receives_http:
        signals.append(_make_signal(
            "Controllers receive HTTP requests",
            "code-pattern",
            "[ApiController] or ControllerBase found",
        ))
    if behavior.manipulates_domain:
        signals.append(_make_signal(
            "Handlers manipulate domain aggregates",
            "code-pattern",
            "Load events -> rebuild aggregate -> call method -> commit pattern",
        ))
    if behavior.saves_to_database:
        signals.append(_make_signal(
            "Handlers save to database",
            "code-pattern",
            "SaveChangesAsync or repository Add/Update calls found",
        ))
    if behavior.calls_other_services:
        signals.append(_make_signal(
            "Handlers call other services",
            "code-pattern",
            "gRPC/HTTP client async calls found in handlers",
        ))
    if behavior.publishes_messages:
        signals.append(_make_signal(
            "Handlers publish messages",
            "code-pattern",
            "Message publisher/sender invocations found",
        ))

    # Layer 3 signals
    if structure.has_domain_layer:
        signals.append(_make_signal(
            "Domain layer present",
            "structural",
            "Domain/ directory found",
        ))
    if structure.has_controllers_dir:
        signals.append(_make_signal(
            "Controllers directory present",
            "structural",
            "Controllers/ directory found",
        ))
    if structure.has_listeners_dir:
        signals.append(_make_signal(
            "ServiceBus listeners present",
            "structural",
            "Listeners/ or ServiceBus/ directory found",
        ))

    # --- Deterministic classification rules ---

    # Control panel: Blazor UI (check early — distinctive)
    if _has_blazor(root):
        return "controlpanel", signals

    # Gateway: REST API that forwards to other services via gRPC or reverse proxy
    if config.serves_rest and config.has_grpc_clients and not config.has_service_bus:
        return "gateway", signals
    if config.serves_rest and config.has_reverse_proxy:
        return "gateway", signals

    # Hybrid: both command and query behaviors present (check BEFORE command)
    if (behavior.receives_commands and behavior.manipulates_domain
            and behavior.receives_events and behavior.saves_to_database):
        return "hybrid", signals

    # Command: receives commands, manipulates domain
    # Command projects may PUBLISH to ServiceBus (event outbox) but do NOT
    # listen/consume events. The key: receives_commands=True + receives_events=False.
    if behavior.receives_commands and behavior.manipulates_domain and not behavior.receives_events:
        return "command", signals

    # Processor: receives events AND (calls other services OR publishes)
    #            AND does NOT save to database
    if (behavior.receives_events and behavior.calls_other_services
            and not behavior.saves_to_database):
        return "processor", signals
    if (behavior.receives_events and behavior.publishes_messages
            and not behavior.saves_to_database):
        return "processor", signals
    # Processor: has ServiceBus + gRPC clients + receives events + no DB save
    if (config.has_service_bus and config.has_grpc_clients
            and behavior.receives_events and behavior.calls_other_services
            and not behavior.saves_to_database):
        return "processor", signals

    # Query: receives events, saves to DB, exposes query endpoints (gRPC or REST)
    if behavior.receives_events and behavior.saves_to_database and config.serves_grpc:
        if _has_cosmos(root):
            return "query-cosmos", signals
        return "query-sql", signals
    # Query with ServiceBus listener that saves to DB
    if config.has_service_bus and behavior.saves_to_database and behavior.receives_events:
        if _has_cosmos(root):
            return "query-cosmos", signals
        return "query-sql", signals

    # --- Fallback to generic architecture patterns ---

    if structure.has_features_dir and _has_feature_handlers(root):
        return "vsa", signals

    if structure.layer_count >= 3 and structure.has_domain_layer:
        return "clean-arch", signals

    if structure.has_bounded_contexts:
        return "ddd", signals

    if structure.has_modules_dir:
        return "modular-monolith", signals

    return "generic", signals


def _make_signal(
    name: str,
    signal_type: str,
    evidence: str,
    *,
    confidence: str = "high",
    is_negative: bool = False,
    target: str = "",
) -> DetectionSignal:
    """Create a DetectionSignal with defaults."""
    return DetectionSignal(
        pattern_name=name,
        signal_type=signal_type,
        target_project_type=target,
        confidence=confidence,
        weight=_CONFIDENCE_WEIGHTS[confidence],
        evidence=evidence,
        is_negative=is_negative,
    )


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------


def _compute_confidence(
    config: ProgramConfig,
    behavior: HandlerBehavior,
    structure: ProjectStructure,
    project_type: str,
) -> tuple[str, float]:
    """Compute confidence based on how many layers agree on the classification.

    Returns (confidence_label, confidence_score).
    """
    if project_type == "generic":
        return "low", 0.0

    # Count how many layers provide supporting evidence
    layer_agreement = 0
    total_layers = 3

    # Layer 1: Program.cs config supports the classification
    if _config_supports(config, project_type):
        layer_agreement += 1

    # Layer 2: Handler behavior supports the classification
    if _behavior_supports(behavior, project_type):
        layer_agreement += 1

    # Layer 3: Structure supports the classification
    if _structure_supports(structure, project_type):
        layer_agreement += 1

    # Score based on layer agreement
    confidence_score = layer_agreement / total_layers

    # Boost: if behavior is very strong (multiple behavioral flags match)
    behavior_strength = _behavior_strength(behavior, project_type)
    if behavior_strength >= 3:
        confidence_score = min(confidence_score + 0.15, 1.0)
    elif behavior_strength >= 2:
        confidence_score = min(confidence_score + 0.07, 1.0)

    confidence_score = round(confidence_score, 2)

    if confidence_score > 0.7:
        return "high", confidence_score
    if confidence_score >= 0.4:
        return "medium", confidence_score
    return "low", confidence_score


def _config_supports(config: ProgramConfig, project_type: str) -> bool:
    """Check if Program.cs config supports the project type."""
    if project_type == "command":
        return config.serves_grpc
    if project_type in ("query-sql", "query-cosmos"):
        return config.serves_grpc and (config.has_service_bus or config.has_database)
    if project_type == "processor":
        return config.has_service_bus and config.has_grpc_clients
    if project_type == "gateway":
        return config.serves_rest and (config.has_grpc_clients or config.has_reverse_proxy)
    if project_type == "controlpanel":
        return not config.serves_grpc and not config.serves_rest
    if project_type == "hybrid":
        return config.serves_grpc
    if project_type == "vsa":
        return True
    if project_type == "clean-arch":
        return True
    return False


def _behavior_supports(behavior: HandlerBehavior, project_type: str) -> bool:
    """Check if handler behavior supports the project type."""
    if project_type == "command":
        return behavior.receives_commands and behavior.manipulates_domain
    if project_type in ("query-sql", "query-cosmos"):
        return behavior.receives_events and behavior.saves_to_database
    if project_type == "processor":
        return behavior.receives_events and (
            behavior.calls_other_services or behavior.publishes_messages
        )
    if project_type == "gateway":
        return behavior.receives_http and behavior.calls_other_services
    if project_type == "controlpanel":
        return True  # Blazor detection is structural, not behavioral
    if project_type == "hybrid":
        return behavior.receives_commands and behavior.receives_events
    return False


def _structure_supports(structure: ProjectStructure, project_type: str) -> bool:
    """Check if project structure supports the project type."""
    if project_type == "command":
        return structure.has_domain_layer and (
            structure.has_commands_dir or structure.has_aggregates
        )
    if project_type in ("query-sql", "query-cosmos"):
        return structure.has_event_handlers_dir and (
            structure.has_listeners_dir or structure.has_queries_dir
        )
    if project_type == "processor":
        return structure.has_event_handlers_dir or structure.has_listeners_dir
    if project_type == "gateway":
        return structure.has_controllers_dir and structure.has_grpc_clients_dir
    if project_type == "controlpanel":
        return True
    if project_type == "vsa":
        return structure.has_features_dir
    if project_type == "clean-arch":
        return structure.has_domain_layer and structure.layer_count >= 3
    if project_type == "ddd":
        return structure.has_bounded_contexts
    if project_type == "modular-monolith":
        return structure.has_modules_dir
    return False


def _behavior_strength(behavior: HandlerBehavior, project_type: str) -> int:
    """Count how many behavioral flags are set for the project type."""
    count = 0
    if project_type == "command":
        if behavior.receives_commands:
            count += 1
        if behavior.manipulates_domain:
            count += 1
        if not behavior.saves_to_database:
            count += 1
        if behavior.returns_ack:
            count += 1
    elif project_type in ("query-sql", "query-cosmos"):
        if behavior.receives_events:
            count += 1
        if behavior.saves_to_database:
            count += 1
        if behavior.returns_data:
            count += 1
        if behavior.returns_ack:
            count += 1
    elif project_type == "processor":
        if behavior.receives_events:
            count += 1
        if behavior.calls_other_services:
            count += 1
        if behavior.publishes_messages:
            count += 1
        if not behavior.saves_to_database:
            count += 1
    elif project_type == "gateway":
        if behavior.receives_http:
            count += 1
        if behavior.calls_other_services:
            count += 1
        if not behavior.saves_to_database:
            count += 1
    return count


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_project(path: Path) -> DetectedProject:
    """Run the full detection algorithm on a directory.

    Steps:
        1. Find .sln/.csproj files, read TargetFramework
        2. 3-layer behavioral analysis (Program.cs, handlers, structure)
        3. Deterministic classification
        4. Learn conventions (namespace, packages)

    Args:
        path: Root directory of the .NET project.

    Returns:
        A DetectedProject with all detected fields populated.

    Raises:
        DetectionError: If no .NET project files are found.
    """
    path = path.resolve()

    # Step 1: Find .NET projects
    sln_files = list(path.glob("*.sln")) + list(path.glob("*.slnx"))
    csproj_files = list(path.rglob("*.csproj"))

    if not sln_files and not csproj_files:
        raise DetectionError(
            f"No .sln or .csproj files found in {path}. "
            "Create a new project or run in a .NET project directory."
        )

    # Read target frameworks from all csproj files
    dotnet_version = _detect_dotnet_version(csproj_files)

    # Read NuGet packages
    packages = _detect_packages(csproj_files)

    # Step 2: 3-layer behavioral analysis
    config = _analyze_program_config(path)
    behavior = _analyze_handler_behavior(path)
    structure = _analyze_project_structure(path, csproj_files)

    # Step 3: Classify
    project_type, all_signals = _classify(config, behavior, structure, path)

    # Determine mode
    microservice_types = {
        "command", "query-sql", "query-cosmos", "processor",
        "gateway", "controlpanel", "hybrid",
    }
    mode = "microservice" if project_type in microservice_types else "generic"

    # Update signal targets now that we know the classification
    for sig in all_signals:
        sig.target_project_type = project_type

    # Compute confidence
    confidence_label, confidence_score = _compute_confidence(
        config, behavior, structure, project_type
    )

    # Pick top 3 signals (prefer code-pattern, then build-config, then structural)
    signal_priority = {"code-pattern": 0, "build-config": 1, "structural": 2}
    sorted_signals = sorted(
        all_signals,
        key=lambda s: (signal_priority.get(s.signal_type, 99), -s.weight),
    )
    top_signals = sorted_signals[:3]

    # Step 4: Learn conventions
    namespace_format = _detect_namespace_format(path)
    architecture = _describe_architecture(mode, project_type)

    # Serialize top signals for storage
    top_signal_dicts = [
        {
            "pattern_name": s.pattern_name,
            "signal_type": s.signal_type,
            "confidence": s.confidence,
            "evidence": s.evidence,
            "is_negative": s.is_negative,
        }
        for s in top_signals
    ]

    return DetectedProject(
        mode=mode,
        project_type=project_type,
        dotnet_version=dotnet_version,
        architecture=architecture,
        namespace_format=namespace_format,
        packages=packages,
        confidence=confidence_label,
        confidence_score=confidence_score,
        top_signals=top_signal_dicts,
    )


# ---------------------------------------------------------------------------
# grep helpers
# ---------------------------------------------------------------------------


def grep_file(file_path: Path, pattern: str) -> list[str]:
    """Search a file's contents for lines matching a regex pattern.

    Args:
        file_path: Path to the file to search.
        pattern: Regular expression pattern to search for.

    Returns:
        List of matching lines (stripped). Empty list if file cannot be read.
    """
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    compiled = re.compile(pattern)
    return [line.strip() for line in text.splitlines() if compiled.search(line)]


def grep_files(directory: Path, pattern: str, glob_pattern: str = "*.cs") -> list[str]:
    """Search all matching files in a directory tree for a regex pattern.

    Args:
        directory: Root directory to search.
        pattern: Regular expression pattern.
        glob_pattern: File glob pattern (default: *.cs).

    Returns:
        List of matching lines across all files.
    """
    matches: list[str] = []
    for file_path in directory.rglob(glob_pattern):
        matches.extend(grep_file(file_path, pattern))
    return matches


# ---------------------------------------------------------------------------
# Step 1 helpers
# ---------------------------------------------------------------------------


def _detect_dotnet_version(csproj_files: list[Path]) -> str:
    """Extract the highest .NET version from csproj TargetFramework elements."""
    versions: list[str] = []

    for csproj in csproj_files:
        try:
            tree = ET.parse(csproj)  # noqa: S314
            root = tree.getroot()
        except (ET.ParseError, OSError):
            continue

        # Handle both with and without namespace
        for tag in ("TargetFramework", "TargetFrameworks"):
            for elem in root.iter(tag):
                if elem.text:
                    for tfm in elem.text.split(";"):
                        tfm = tfm.strip()
                        version = _parse_tfm_version(tfm)
                        if version:
                            versions.append(version)

    if not versions:
        return ""

    # Sort by semantic version and return highest
    versions.sort(key=lambda v: tuple(int(x) for x in v.split(".")), reverse=True)
    return versions[0]


def _parse_tfm_version(tfm: str) -> Optional[str]:
    """Parse a Target Framework Moniker into a version string.

    Examples:
        net10.0 -> 10.0
        net8.0  -> 8.0
        net6.0  -> 6.0
    """
    match = re.match(r"net(\d+\.\d+)", tfm)
    if match:
        return match.group(1)
    return None


def _detect_packages(csproj_files: list[Path]) -> list[str]:
    """Extract NuGet package references from csproj files."""
    packages: set[str] = set()

    for csproj in csproj_files:
        try:
            tree = ET.parse(csproj)  # noqa: S314
            root = tree.getroot()
        except (ET.ParseError, OSError):
            continue

        for elem in root.iter("PackageReference"):
            include = elem.get("Include")
            if include:
                packages.add(include)

    return sorted(packages)


# ---------------------------------------------------------------------------
# Step 4 helpers -- conventions
# ---------------------------------------------------------------------------


def _detect_namespace_format(root: Path) -> str:
    """Detect namespace format from existing C# files.

    Looks for 'namespace' declarations and infers the pattern.
    """
    namespaces: list[str] = []

    # Sample up to 10 .cs files for namespace patterns
    cs_files = list(root.rglob("*.cs"))[:10]
    for cs_file in cs_files:
        for line in grep_file(cs_file, r"^\s*namespace\s+"):
            # Extract namespace value
            match = re.match(r"\s*namespace\s+([\w.]+)", line)
            if match:
                namespaces.append(match.group(1))

    if not namespaces:
        return ""

    # Find the most common namespace pattern
    # Pick the shortest namespace as the base pattern
    namespaces.sort(key=len)
    sample = namespaces[0]

    # Count the number of parts to describe the format
    parts = sample.split(".")
    if len(parts) >= 4:
        return "{Company}.{Domain}.{Side}.{Layer}"
    elif len(parts) == 3:
        return "{Company}.{Domain}.{Layer}"
    elif len(parts) == 2:
        return "{Company}.{Domain}"
    else:
        return sample


def _describe_architecture(mode: str, project_type: str) -> str:
    """Produce a human-readable architecture description."""
    descriptions = {
        "command": "Event-sourced Command service (CQRS write side)",
        "query-sql": "SQL Server Query service (CQRS read side)",
        "query-cosmos": "Cosmos DB Query service (CQRS read side)",
        "processor": "Background event Processor service",
        "gateway": "REST API Gateway with gRPC backends",
        "controlpanel": "Blazor WASM Control Panel",
        "hybrid": "Hybrid CQRS service (command + query in same project)",
        "vsa": "Vertical Slice Architecture",
        "clean-arch": "Clean Architecture",
        "ddd": "Domain-Driven Design",
        "modular-monolith": "Modular Monolith",
        "generic": "Generic .NET project",
    }
    return descriptions.get(project_type, f"{mode} - {project_type}")


# ---------------------------------------------------------------------------
# UI helpers (called from cli.py, not from core detection)
# ---------------------------------------------------------------------------


def _display_detection_summary(result: DetectedProject, console: Console) -> None:
    """Display a rich Panel summarizing detection results.

    Args:
        result: The detected project information.
        console: Rich Console instance for output.
    """
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Label", style="bold")
    table.add_column("Value")

    table.add_row("Mode", result.mode)
    table.add_row("Project Type", result.project_type)
    table.add_row("Architecture", result.architecture)
    table.add_row(".NET Version", result.dotnet_version or "(not detected)")

    confidence_style = {
        "high": "green",
        "medium": "yellow",
        "low": "red",
    }.get(result.confidence, "dim")

    confidence_display = result.confidence or "unknown"
    if result.confidence_score > 0:
        confidence_display += f" ({result.confidence_score:.0%})"
    table.add_row("Confidence", f"[{confidence_style}]{confidence_display}[/{confidence_style}]")

    if result.top_signals:
        signal_lines: list[str] = []
        for i, sig in enumerate(result.top_signals[:3], 1):
            neg = " (negative)" if sig.get("is_negative") else ""
            signal_lines.append(
                f"  {i}. {sig.get('pattern_name', '?')} "
                f"[dim]({sig.get('confidence', '?')}{neg})[/dim]"
            )
        table.add_row("Top Signals", "\n".join(signal_lines))

    if result.user_override:
        table.add_row("User Override", result.user_override)

    panel = Panel(
        table,
        title="Detection Summary",
        border_style="blue",
        expand=False,
    )
    console.print(panel)


def _prompt_override(result: DetectedProject) -> DetectedProject:
    """Prompt the user to confirm or override the detection result.

    Asks: "Is this correct? [Y/n/change]"
    - Y (default): accept the detection as-is
    - n: abort (raises DetectionError)
    - change: prompt for a new project type and set user_override

    Args:
        result: The current detection result.

    Returns:
        The (possibly modified) DetectedProject.

    Raises:
        DetectionError: If the user rejects the detection and doesn't override.
    """
    console = Console()

    response = console.input("\n[bold]Is this correct?[/bold] [Y/n/change]: ").strip().lower()

    if response in ("", "y", "yes"):
        return result

    # n, change, or anything else -- show type selection
    valid_types = [
        ("command", "Command-side (CQRS write model)"),
        ("query-sql", "Query-side with SQL storage"),
        ("query-cosmos", "Query-side with Cosmos DB"),
        ("processor", "Event processor / router"),
        ("gateway", "API gateway / router"),
        ("controlpanel", "Blazor control panel"),
        ("hybrid", "Mixed command + query"),
        ("vsa", "Vertical Slice Architecture"),
        ("clean-arch", "Clean Architecture"),
        ("ddd", "Domain-Driven Design"),
        ("modular-monolith", "Modular Monolith"),
        ("generic", "Generic .NET project"),
    ]

    console.print("\n[bold]Select project type:[/bold]")
    for i, (type_key, desc) in enumerate(valid_types, 1):
        console.print(f"  [bold]{i:>2}[/bold]. {type_key:<18} - {desc}")

    choice = console.input("\n[bold]Your choice [1-12]:[/bold] ").strip()

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(valid_types):
            new_type = valid_types[idx][0]
        else:
            console.print("[yellow]Invalid choice. Keeping detected type.[/yellow]")
            return result
    except ValueError:
        # Try matching by name directly
        type_keys = [t[0] for t in valid_types]
        if choice.lower() in type_keys:
            new_type = choice.lower()
        else:
            console.print("[yellow]Invalid choice. Keeping detected type.[/yellow]")
            return result

    # Determine mode from type
    microservice_types = {
        "command",
        "query-sql",
        "query-cosmos",
        "processor",
        "gateway",
        "controlpanel",
        "hybrid",
    }
    new_mode = "microservice" if new_type in microservice_types else "generic"
    new_architecture = _describe_architecture(new_mode, new_type)

    result.user_override = new_type
    result.mode = new_mode
    result.project_type = new_type
    result.architecture = new_architecture
    console.print(f"\n[green]Type changed to: {new_type} ({new_architecture})[/green]")
    return result
