"""Runtime check for ``codebase-memory-mcp`` (T067 / FR-019 / FR-035).

The shipped ``.mcp.json`` carries a ``dotnet_ai_kit_min_version`` field
that is the **single source of truth** for the minimum compatible MCP
server version. ``check_codebase_memory_mcp()`` reads that value and
returns an ``MCPHealth`` describing whether the binary is present and
whether its reported version meets the minimum.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

_FALLBACK_MIN_VERSION = "0.6.1"


def _read_min_version_from_mcp_json() -> str:
    """Read `mcpServers.codebase-memory-mcp.dotnet_ai_kit_min_version` from
    the repository `.mcp.json`. Single source of truth per H-CX-5.
    Falls back to the documented baseline if the file is unreadable
    (e.g., when the package is installed without the repo source tree)."""
    try:
        # `.mcp.json` lives at the repo root, which is the parent of `src/`.
        mcp_path = Path(__file__).resolve().parent.parent.parent / ".mcp.json"
        if not mcp_path.is_file():
            return _FALLBACK_MIN_VERSION
        data = json.loads(mcp_path.read_text(encoding="utf-8"))
        return (
            data.get("mcpServers", {})
            .get("codebase-memory-mcp", {})
            .get("dotnet_ai_kit_min_version", _FALLBACK_MIN_VERSION)
        )
    except (OSError, json.JSONDecodeError, AttributeError):
        return _FALLBACK_MIN_VERSION


MIN_CODEBASE_MEMORY_MCP_VERSION = _read_min_version_from_mcp_json()

_VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


@dataclass
class MCPHealth:
    server_name: str
    present: bool
    version: str | None
    meets_minimum: bool
    error: str | None = None


def _parse(version: str) -> tuple[int, int, int] | None:
    m = _VERSION_RE.search(version)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _min_tuple() -> tuple[int, int, int]:
    parsed = _parse(MIN_CODEBASE_MEMORY_MCP_VERSION)
    assert parsed is not None  # constant is well-formed
    return parsed


def check_codebase_memory_mcp() -> MCPHealth:
    """Detect ``codebase-memory-mcp`` and decide whether it meets the
    declared minimum version (0.6.1)."""
    name = "codebase-memory-mcp"
    if shutil.which(name) is None:
        return MCPHealth(
            server_name=name,
            present=False,
            version=None,
            meets_minimum=False,
            error="binary not on PATH",
        )

    try:
        proc = subprocess.run(
            [name, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return MCPHealth(
            server_name=name,
            present=True,
            version=None,
            meets_minimum=False,
            error=f"{type(exc).__name__}: {exc}",
        )

    output = (proc.stdout or "") + (proc.stderr or "")
    parsed = _parse(output)
    if parsed is None:
        return MCPHealth(
            server_name=name,
            present=True,
            version=None,
            meets_minimum=False,
            error=f"could not parse version from {output.strip()!r}",
        )

    version_str = "{}.{}.{}".format(*parsed)
    return MCPHealth(
        server_name=name,
        present=True,
        version=version_str,
        meets_minimum=parsed >= _min_tuple(),
    )
