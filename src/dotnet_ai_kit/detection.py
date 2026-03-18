"""Project type detection algorithm for dotnet-ai-kit.

Detects .NET project type, architecture mode, and conventions by scanning
solution/project files and source code for known patterns.

Uses a signal-based scoring system where code patterns are the primary signal
and naming conventions are supplementary.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from dotnet_ai_kit.models import (
    _CONFIDENCE_WEIGHTS,
    DetectedProject,
    DetectionScoreCard,
    DetectionSignal,
)


class DetectionError(Exception):
    """Raised when project detection fails."""


# ---------------------------------------------------------------------------
# Signal pattern registry
# ---------------------------------------------------------------------------

# Each entry: (pattern_name, regex, target_project_type, signal_type,
#               confidence, is_negative)

_SIGNAL_PATTERNS: list[tuple[str, str, str, str, str, bool]] = [
    # ── Command-side positive signals ──────────────────────────────────────
    (
        "AggregateRoot base class",
        r"class\s+\w+\s*:\s*.*(?:Aggregate<|AggregateRoot)",
        "command",
        "code-pattern",
        "high",
        False,
    ),
    (
        "ICommandHandler pattern",
        r"ICommandHandler<",
        "command",
        "code-pattern",
        "high",
        False,
    ),
    (
        "Domain event classes",
        r"(?::\s*(?:DomainEvent|Event<\w)|class\s+\w+.*DomainEvent|INotification)",
        "command",
        "code-pattern",
        "medium",
        False,
    ),
    (
        "Event publishing",
        r"(?:IMediator\s*\.\s*Publish|IEventBus|OutboxMessage)",
        "command",
        "code-pattern",
        "medium",
        False,
    ),
    (
        "Event store",
        r"(?:IEventStore|EventStoreClient)",
        "command",
        "code-pattern",
        "high",
        False,
    ),
    # ── Command-side additional signals ───────────────────────────────────
    (
        "ICommitEventService (event commit)",
        r"ICommitEventService",
        "command",
        "code-pattern",
        "high",
        False,
    ),
    (
        "MapGrpcService (gRPC server, command)",
        r"MapGrpcService<",
        "command",
        "code-pattern",
        "medium",
        False,
    ),
    # ── Command-side negative signal ───────────────────────────────────────
    (
        "Query handler in command project",
        r"IQueryHandler<",
        "command",
        "code-pattern",
        "medium",
        True,
    ),
    # ── Query-sql positive signals ─────────────────────────────────────────
    (
        "IRequestHandler<Event< pattern (query)",
        r"IRequestHandler<.*Event<",
        "query-sql",
        "code-pattern",
        "medium",
        False,
    ),
    (
        "IQueryHandler pattern",
        r"IQueryHandler<",
        "query-sql",
        "code-pattern",
        "high",
        False,
    ),
    (
        "MapGrpcService (gRPC server, query)",
        r"MapGrpcService<",
        "query-sql",
        "code-pattern",
        "medium",
        False,
    ),
    # ── Query-sql negative signals ─────────────────────────────────────────
    (
        "Aggregate in query project",
        r"class\s+\w+\s*:\s*.*(?:Aggregate<|AggregateRoot)",
        "query-sql",
        "code-pattern",
        "medium",
        True,
    ),
    (
        "Event publishing in query project",
        r"(?:IMediator\s*\.\s*Publish|IEventBus|OutboxMessage)",
        "query-sql",
        "code-pattern",
        "medium",
        True,
    ),
    # ── Query-cosmos positive signal ───────────────────────────────────────
    (
        "IContainerDocument interface",
        r"IContainerDocument",
        "query-cosmos",
        "code-pattern",
        "high",
        False,
    ),
    # ── Query-cosmos negative signals ──────────────────────────────────────
    (
        "Aggregate in cosmos query project",
        r"class\s+\w+\s*:\s*.*(?:Aggregate<|AggregateRoot)",
        "query-cosmos",
        "code-pattern",
        "medium",
        True,
    ),
    (
        "Event publishing in cosmos query project",
        r"(?:IMediator\s*\.\s*Publish|IEventBus|OutboxMessage)",
        "query-cosmos",
        "code-pattern",
        "medium",
        True,
    ),
    # ── Processor positive signals ─────────────────────────────────────────
    # NOTE: IHostedService and ServiceBusProcessor exist in BOTH query and
    # processor projects. The REAL processor signal is what the handler DOES:
    #   Processor handler: receives event → REDIRECTS to another service via
    #     gRPC or PUBLISHES to a queue/topic (event orchestrator/router).
    #   Query handler: receives event → SAVES data locally (may GET via gRPC
    #     to enrich, but the purpose is local storage).
    #
    # So processor signals focus on OUTBOUND actions from handlers:
    (
        "Event publishing downstream (processor orchestrator)",
        r"(?:IServiceBusPublisher|IPointsPublisher|IEventPublisher|IMessagePublisher)",
        "processor",
        "code-pattern",
        "high",
        False,
    ),
    (
        "Sends messages to queue/topic (processor routing)",
        r"(?:SendMessageAsync|SendAsync|PublishAsync|PublishMessageAsync)",
        "processor",
        "code-pattern",
        "high",
        False,
    ),
    (
        "Calls command gRPC services (processor forwarding)",
        r"(?:CommandsClient|CommandClient|commandsClient|commandClient)\s*\.\s*\w+Async",
        "processor",
        "code-pattern",
        "high",
        False,
    ),
    # ── Processor negative signals ─────────────────────────────────────────
    (
        "Aggregate in processor project",
        r"class\s+\w+\s*:\s*.*(?:Aggregate<|AggregateRoot)",
        "processor",
        "code-pattern",
        "high",
        True,
    ),
    (
        "Database save in processor (query behavior)",
        r"(?:SaveChangesAsync|SaveAsync|Repository\s*\.\s*(?:Add|Update|Save))",
        "processor",
        "code-pattern",
        "medium",
        True,
    ),
    # ── Query-sql additional positive signals ──────────────────────────────
    # Query handlers save data locally — this is the key differentiator
    (
        "Database save (query read model sync)",
        r"(?:SaveChangesAsync|SaveAsync|Repository\s*\.\s*(?:Add|Update|Save))",
        "query-sql",
        "code-pattern",
        "medium",
        False,
    ),
    (
        "Cache/rebuild pattern (query materialization)",
        r"(?:CacheRebuilder|RebuildService|IProjection|Materialize)",
        "query-sql",
        "code-pattern",
        "medium",
        False,
    ),
    # ── Gateway positive signals ───────────────────────────────────────────
    (
        "API Controller",
        r"\[ApiController\]|ControllerBase",
        "gateway",
        "code-pattern",
        "high",
        False,
    ),
    (
        "MapControllers (REST routing)",
        r"(?:MapControllers|MapControllersWithAuthorization)",
        "gateway",
        "code-pattern",
        "medium",
        False,
    ),
    (
        "gRPC client-only protos",
        r'GrpcServices\s*=\s*"Client"',
        "gateway",
        "code-pattern",
        "high",
        False,
    ),
    (
        "HTTP client factory",
        r"(?:IHttpClientFactory|AddHttpClient)",
        "gateway",
        "code-pattern",
        "medium",
        False,
    ),
    (
        "YARP configuration",
        r"(?:AddReverseProxy|ReverseProxy|Yarp)",
        "gateway",
        "code-pattern",
        "medium",
        False,
    ),
    # ── Gateway negative signals ───────────────────────────────────────────
    (
        "Direct database access in gateway",
        r"(?:DbContext|IDbConnection|SqlConnection|CosmosClient)",
        "gateway",
        "code-pattern",
        "medium",
        True,
    ),
    (
        "ServiceBusProcessor in gateway (not a gateway)",
        r"ServiceBusProcessor|ServiceBusSessionProcessor",
        "gateway",
        "code-pattern",
        "high",
        True,
    ),
    # ── Controlpanel positive signals ──────────────────────────────────────
    (
        "Blazor components",
        r"(?:@page|\.razor|Blazor)",
        "controlpanel",
        "code-pattern",
        "high",
        False,
    ),
    (
        "ResponseResult pattern",
        r"ResponseResult<",
        "controlpanel",
        "code-pattern",
        "medium",
        False,
    ),
]

# Theoretical max positive weight per project type (for normalization).
# Pre-computed from _SIGNAL_PATTERNS — sum of positive signal weights per type.
_THEORETICAL_MAX: dict[str, float] = {}


def _compute_theoretical_max() -> None:
    """Pre-compute the theoretical max positive weight per project type."""
    for name, _regex, target, _stype, conf, is_neg in _SIGNAL_PATTERNS:
        if not is_neg:
            _THEORETICAL_MAX.setdefault(target, 0.0)
            _THEORETICAL_MAX[target] += _CONFIDENCE_WEIGHTS[conf]


_compute_theoretical_max()

# Hybrid detection threshold — if both command-side and query-side net scores
# are at or above this value, the project is classified as hybrid.
_HYBRID_THRESHOLD = 3


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_project(path: Path) -> DetectedProject:
    """Run the full detection algorithm on a directory.

    Steps:
        1. Find .sln/.csproj files, read TargetFramework
        2. Collect signals from code patterns, naming, and structure
        3. Score candidates and classify
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

    # Step 2: Collect all signals
    signals = _collect_signals(path, csproj_files)

    # Step 3: Score candidates and classify
    scorecards = _score_candidates(signals)
    mode, project_type, confidence, confidence_score, top_signals = _classify_project(
        scorecards, signals, path
    )

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
        confidence=confidence,
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
# Step 2: Signal collection
# ---------------------------------------------------------------------------


def _collect_signals(
    root: Path,
    csproj_files: list[Path],
    *,
    show_progress: bool = False,
) -> list[DetectionSignal]:
    """Scan .cs and .razor files and return a list of DetectionSignal objects.

    Collects signals from three sources:
    1. Code patterns (_SIGNAL_PATTERNS registry)
    2. Naming conventions (_detect_from_name)
    3. Structural patterns (_detect_generic)

    Args:
        root: Project root directory.
        csproj_files: List of .csproj file paths.
        show_progress: Whether to display a rich progress spinner.

    Returns:
        List of all detected signals.
    """
    signals: list[DetectionSignal] = []

    # Gather all source files once to avoid repeated rglob calls
    cs_files = list(root.rglob("*.cs"))
    razor_files = list(root.rglob("*.razor"))
    all_source_files = cs_files + razor_files

    if show_progress:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(
                "Scanning source files for patterns...",
                total=len(all_source_files),
            )
            signals.extend(_scan_code_patterns(all_source_files, progress, task))
    else:
        signals.extend(_scan_code_patterns(all_source_files))

    # Naming signals
    signals.extend(_detect_from_name(root, csproj_files))

    # Structural / architecture signals
    signals.extend(_detect_generic(root))

    return signals


def _scan_code_patterns(
    source_files: list[Path],
    progress: Optional[Progress] = None,
    task_id: Optional[object] = None,
) -> list[DetectionSignal]:
    """Scan source files against _SIGNAL_PATTERNS and produce signals.

    Each pattern is checked once per file. Multiple matches in the same file
    for the same pattern produce a single signal (with the first match as
    evidence).

    Args:
        source_files: List of .cs/.razor files to scan.
        progress: Optional rich Progress instance for UI updates.
        task_id: Optional task ID for the progress bar.

    Returns:
        List of DetectionSignal objects.
    """
    signals: list[DetectionSignal] = []
    # Track which (pattern_name, target) combos already fired to avoid
    # producing hundreds of signals for repeated patterns.
    seen: set[tuple[str, str]] = set()

    for file_path in source_files:
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            if progress and task_id is not None:
                progress.advance(task_id)
            continue

        lines = text.splitlines()

        for pattern_name, regex, target, stype, conf, is_neg in _SIGNAL_PATTERNS:
            key = (pattern_name, target)
            if key in seen:
                continue

            compiled = re.compile(regex)
            for line in lines:
                if compiled.search(line):
                    evidence = f"{file_path.name}: {line.strip()}"
                    signals.append(
                        DetectionSignal(
                            pattern_name=pattern_name,
                            signal_type=stype,
                            target_project_type=target,
                            confidence=conf,
                            weight=_CONFIDENCE_WEIGHTS[conf],
                            evidence=evidence,
                            is_negative=is_neg,
                        )
                    )
                    seen.add(key)
                    break

        if progress and task_id is not None:
            progress.advance(task_id)

    return signals


# ---------------------------------------------------------------------------
# Step 2b: Naming signals
# ---------------------------------------------------------------------------


def _detect_from_name(root: Path, csproj_files: list[Path]) -> list[DetectionSignal]:
    """Detect project type from solution/project naming convention.

    Checks for well-known suffixes like .Commands, .Queries, .Processor,
    .Gateway. Returns DetectionSignal list with signal_type="naming".
    """
    sln_files = list(root.glob("*.sln")) + list(root.glob("*.slnx"))
    names_to_check: list[str] = [f.stem for f in sln_files]
    names_to_check.extend(f.stem for f in csproj_files)
    names_to_check.append(root.name)

    combined = " ".join(names_to_check).lower()

    signals: list[DetectionSignal] = []

    _NAME_MAP: list[tuple[str, str]] = [
        ("commands", "command"),
        ("queries", "query-sql"),
        ("processor", "processor"),
        ("gateway", "gateway"),
        ("controlpanel", "controlpanel"),
    ]

    for suffix, project_type in _NAME_MAP:
        # Check for .suffix in combined names or as final segment of root name
        root_parts = root.name.lower().split(".")
        if f".{suffix}" in combined or (root_parts and root_parts[-1] == suffix):
            signals.append(
                DetectionSignal(
                    pattern_name=f"Naming convention: .{suffix.title()}",
                    signal_type="naming",
                    target_project_type=project_type,
                    confidence="medium",
                    weight=_CONFIDENCE_WEIGHTS["medium"],
                    evidence=f"Directory/solution name contains '.{suffix}'",
                    is_negative=False,
                )
            )

    return signals


# ---------------------------------------------------------------------------
# Step 2c: Structural / architecture signals
# ---------------------------------------------------------------------------


def _detect_generic(root: Path) -> list[DetectionSignal]:
    """Detect generic architecture patterns from directory structure.

    Returns DetectionSignal list with signal_type="structural".
    """
    signals: list[DetectionSignal] = []

    src_dirs: set[str] = set()
    try:
        src_dirs = {d.name.lower() for d in root.iterdir() if d.is_dir()}
    except OSError:
        return signals

    # Also check one level under src/
    src_subdir = root / "src"
    if src_subdir.is_dir():
        try:
            src_dirs.update(d.name.lower() for d in src_subdir.iterdir() if d.is_dir())
        except OSError:
            pass

    # Clean Architecture: has Domain + Application + Infrastructure layers
    clean_arch_layers = {"domain", "application", "infrastructure"}
    if clean_arch_layers.issubset(src_dirs):
        signals.append(
            DetectionSignal(
                pattern_name="Clean Architecture layers",
                signal_type="structural",
                target_project_type="clean-arch",
                confidence="high",
                weight=_CONFIDENCE_WEIGHTS["high"],
                evidence="Found Domain + Application + Infrastructure directories",
                is_negative=False,
            )
        )

    # VSA: Features folder with *Handler.cs files
    features_dirs = list(root.rglob("Features"))
    for features_dir in features_dirs:
        if features_dir.is_dir():
            handlers = list(features_dir.rglob("*Handler.cs"))
            if handlers:
                signals.append(
                    DetectionSignal(
                        pattern_name="Vertical Slice Architecture",
                        signal_type="structural",
                        target_project_type="vsa",
                        confidence="high",
                        weight=_CONFIDENCE_WEIGHTS["high"],
                        evidence=f"Features folder with handler files (e.g. {handlers[0].name})",
                        is_negative=False,
                    )
                )
                break

    # DDD: bounded context folders or explicit "BoundedContexts" dir
    if "boundedcontexts" in src_dirs or "contexts" in src_dirs:
        signals.append(
            DetectionSignal(
                pattern_name="Domain-Driven Design contexts",
                signal_type="structural",
                target_project_type="ddd",
                confidence="high",
                weight=_CONFIDENCE_WEIGHTS["high"],
                evidence="Found BoundedContexts or Contexts directory",
                is_negative=False,
            )
        )

    # Modular Monolith: multiple modules directory
    if "modules" in src_dirs:
        signals.append(
            DetectionSignal(
                pattern_name="Modular Monolith modules",
                signal_type="structural",
                target_project_type="modular-monolith",
                confidence="medium",
                weight=_CONFIDENCE_WEIGHTS["medium"],
                evidence="Found Modules directory",
                is_negative=False,
            )
        )

    return signals


# ---------------------------------------------------------------------------
# Step 3: Scoring and classification
# ---------------------------------------------------------------------------


def _score_candidates(
    signals: list[DetectionSignal],
) -> dict[str, DetectionScoreCard]:
    """Aggregate signals into DetectionScoreCard per project type.

    Args:
        signals: All collected signals.

    Returns:
        Dict mapping project_type -> DetectionScoreCard.
    """
    cards: dict[str, DetectionScoreCard] = {}

    for sig in signals:
        ptype = sig.target_project_type
        if ptype not in cards:
            cards[ptype] = DetectionScoreCard(project_type=ptype)

        card = cards[ptype]
        if sig.is_negative:
            card.negative_score += sig.weight
        else:
            card.positive_score += sig.weight
        card.signal_count += 1
        card.net_score = card.positive_score - card.negative_score

    return cards


def _classify_project(
    scorecards: dict[str, DetectionScoreCard],
    signals: list[DetectionSignal],
    root: Path,
) -> tuple[str, str, str, float, list[DetectionSignal]]:
    """Pick the highest-scoring project type, compute confidence, select top signals.

    Handles hybrid detection: if both a command-side type and a query-side type
    have net_score >= _HYBRID_THRESHOLD, classify as "hybrid".

    Args:
        scorecards: Scored candidates.
        signals: All detected signals.
        root: Project root (unused currently but available for future use).

    Returns:
        Tuple of (mode, project_type, confidence_label, confidence_score, top_3_signals).
    """
    if not scorecards:
        # No signals at all — fall back to generic
        return "generic", "generic", "low", 0.0, []

    # Check for hybrid: command + query both above threshold
    command_score = scorecards.get("command", DetectionScoreCard(project_type="command")).net_score
    query_types = ["query-sql", "query-cosmos"]
    max_query_score = max(
        (scorecards.get(qt, DetectionScoreCard(project_type=qt)).net_score for qt in query_types),
        default=0.0,
    )

    microservice_types = {
        "command",
        "query-sql",
        "query-cosmos",
        "processor",
        "gateway",
        "controlpanel",
        "hybrid",
    }

    if command_score >= _HYBRID_THRESHOLD and max_query_score >= _HYBRID_THRESHOLD:
        # Hybrid detection
        combined_score = command_score + max_query_score
        # Use combined theoretical max
        t_max = _THEORETICAL_MAX.get("command", 1.0) + max(
            _THEORETICAL_MAX.get(qt, 1.0) for qt in query_types
        )
        confidence_score = min(combined_score / t_max, 1.0) if t_max > 0 else 0.0
        confidence_label = _score_to_label(confidence_score)

        # Top signals: pick top 3 across both command and query signals
        relevant = [
            s
            for s in signals
            if s.target_project_type in {"command"} | set(query_types) and not s.is_negative
        ]
        top = sorted(relevant, key=lambda s: s.weight, reverse=True)[:3]

        return "microservice", "hybrid", confidence_label, round(confidence_score, 2), top

    # Find highest net-score candidate
    best = max(scorecards.values(), key=lambda c: c.net_score)

    if best.net_score <= 0:
        return "generic", "generic", "low", 0.0, []

    # Compute confidence score
    t_max = _THEORETICAL_MAX.get(best.project_type, 1.0)
    confidence_score = min(best.net_score / t_max, 1.0) if t_max > 0 else 0.0
    confidence_label = _score_to_label(confidence_score)

    # Pick mode
    if best.project_type in microservice_types:
        mode = "microservice"
    else:
        mode = "generic"

    # Top 3 positive signals for the winning type
    relevant = [
        s for s in signals if s.target_project_type == best.project_type and not s.is_negative
    ]
    top = sorted(relevant, key=lambda s: s.weight, reverse=True)[:3]

    return mode, best.project_type, confidence_label, round(confidence_score, 2), top


def _score_to_label(score: float) -> str:
    """Convert a numeric confidence score to a label."""
    if score > 0.8:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Step 4 helpers — conventions
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
    _display_detection_summary(result, console)

    response = console.input("\n[bold]Is this correct?[/bold] [Y/n/change]: ").strip().lower()

    if response in ("", "y", "yes"):
        return result

    if response in ("change", "c"):
        valid_types = [
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
        ]
        console.print(f"\nValid types: {', '.join(valid_types)}")
        new_type = console.input("[bold]Enter project type:[/bold] ").strip().lower()

        if new_type not in valid_types:
            raise DetectionError(
                f"Invalid project type '{new_type}'. Must be one of: {', '.join(valid_types)}"
            )

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
        return result

    # n or anything else — reject
    raise DetectionError("Detection rejected by user.")
