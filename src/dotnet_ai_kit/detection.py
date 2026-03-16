"""Project type detection algorithm for dotnet-ai-kit.

Detects .NET project type, architecture mode, and conventions by scanning
solution/project files and source code for known patterns.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from dotnet_ai_kit.models import DetectedProject


class DetectionError(Exception):
    """Raised when project detection fails."""


def detect_project(path: Path) -> DetectedProject:
    """Run the full detection algorithm on a directory.

    Steps:
        1. Find .sln/.csproj files, read TargetFramework
        2. Detect architecture mode (microservice patterns, then generic)
        3. Learn conventions (namespace, packages, DI style)

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

    # Step 2: Detect architecture mode
    mode, project_type, alt_matches = _detect_architecture(path, csproj_files)

    # Step 3: Learn conventions
    namespace_format = _detect_namespace_format(path)
    architecture = _describe_architecture(mode, project_type)

    return DetectedProject(
        mode=mode,
        project_type=project_type,
        dotnet_version=dotnet_version,
        architecture=architecture,
        namespace_format=namespace_format,
        packages=packages,
    )


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

    if len(set(versions)) > 1:
        # Multiple versions found — use highest
        pass

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
# Step 2 helpers — microservice detection
# ---------------------------------------------------------------------------

_MICROSERVICE_PATTERNS: list[tuple[str, str, str, list[str]]] = [
    # (project_type, primary_pattern, secondary_pattern_or_empty, description_parts)
    (
        "command",
        r"class\s+\w+\s*:\s*.*Aggregate<",
        "",
        ["Aggregate<T> base class"],
    ),
    (
        "command",
        r"Event<",
        r"OutboxMessage",
        ["Event<TData>", "OutboxMessage"],
    ),
    (
        "query-cosmos",
        r"IContainerDocument",
        "",
        ["IContainerDocument interface"],
    ),
    (
        "query-sql",
        r"IRequestHandler<.*Event<",
        "",
        ["IRequestHandler<Event< pattern"],
    ),
    (
        "query-sql",
        r"private\s+set\s*;",
        r"(sequence|Sequence)",
        ["Private setters + sequence field"],
    ),
    (
        "processor",
        r"IHostedService",
        r"ServiceBusSessionProcessor",
        ["IHostedService", "ServiceBusSessionProcessor"],
    ),
    (
        "gateway",
        r"\[ApiController\]|ControllerBase",
        r"AddGrpcClient<",
        ["REST Controllers", "AddGrpcClient<"],
    ),
    (
        "controlpanel",
        r"(Blazor|@page|\.razor)",
        r"ResponseResult<",
        ["Blazor", "ResponseResult<T>"],
    ),
]

# Priority for resolving ambiguous microservice detection
_MICROSERVICE_PRIORITY = {
    "command": 1,
    "processor": 2,
    "query-sql": 3,
    "query-cosmos": 3,
    "gateway": 4,
    "controlpanel": 5,
}


def _detect_microservice(root: Path, csproj_files: list[Path]) -> tuple[Optional[str], list[str]]:
    """Check for microservice-specific patterns.

    Returns:
        Tuple of (project_type or None, list of all matched types).
    """
    matched_types: list[str] = []

    for project_type, primary, secondary, _desc in _MICROSERVICE_PATTERNS:
        primary_hits = grep_files(root, primary)
        if not primary_hits:
            continue

        if secondary:
            secondary_hits = grep_files(root, secondary)
            if not secondary_hits:
                continue

        if project_type not in matched_types:
            matched_types.append(project_type)

    if not matched_types:
        return None, []

    if len(matched_types) == 1:
        return matched_types[0], matched_types

    # Ambiguous — pick highest priority (lowest number)
    matched_types.sort(key=lambda t: _MICROSERVICE_PRIORITY.get(t, 99))
    return matched_types[0], matched_types


def _detect_generic(root: Path) -> Optional[str]:
    """Detect generic architecture patterns from directory structure.

    Checks for:
        - Vertical Slice Architecture: Feature folders with handlers
        - Clean Architecture: Domain/Application/Infrastructure/API layers
        - DDD: Bounded context folders
        - Modular Monolith: Multiple project modules
    """
    src_dirs = {d.name.lower() for d in root.iterdir() if d.is_dir()}

    # Also check one level under src/
    src_subdir = root / "src"
    if src_subdir.is_dir():
        src_dirs.update(d.name.lower() for d in src_subdir.iterdir() if d.is_dir())

    # Clean Architecture: has Domain + Application + Infrastructure layers
    clean_arch_layers = {"domain", "application", "infrastructure"}
    if clean_arch_layers.issubset(src_dirs):
        return "clean-arch"

    # Check for Features folder (VSA)
    features_dirs = list(root.rglob("Features"))
    if features_dirs:
        # If feature folders contain handler files, it's VSA
        for features_dir in features_dirs:
            if features_dir.is_dir():
                handlers = list(features_dir.rglob("*Handler.cs"))
                if handlers:
                    return "vsa"

    # DDD: bounded context folders or explicit "BoundedContexts" dir
    if "boundedcontexts" in src_dirs or "contexts" in src_dirs:
        return "ddd"

    # Modular Monolith: multiple modules directory
    if "modules" in src_dirs:
        return "modular-monolith"

    return None


def _detect_architecture(
    root: Path, csproj_files: list[Path]
) -> tuple[str, str, list[str]]:
    """Run the two-phase detection: microservice first, then generic.

    Returns:
        Tuple of (mode, project_type, alternative_matches).
    """
    # Phase 1: microservice patterns (more specific)
    micro_type, micro_matches = _detect_microservice(root, csproj_files)
    if micro_type:
        return "microservice", micro_type, micro_matches

    # Phase 2: generic architecture detection
    generic_type = _detect_generic(root)
    if generic_type:
        return "generic", generic_type, []

    # No match — default to generic
    return "generic", "generic", []


# ---------------------------------------------------------------------------
# Step 3 helpers — conventions
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
    # E.g., "Company.Domain.Layer" -> "{Company}.{Domain}.{Layer}"
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
        "vsa": "Vertical Slice Architecture",
        "clean-arch": "Clean Architecture",
        "ddd": "Domain-Driven Design",
        "modular-monolith": "Modular Monolith",
        "generic": "Generic .NET project",
    }
    return descriptions.get(project_type, f"{mode} - {project_type}")
