"""T028 — assert no-network / no-telemetry posture (A-011 / clarify Q5).

Per A-011: the dotnet-ai-kit CLI must not initiate outbound network calls
or load analytics SDKs. This test scans the `src/dotnet_ai_kit/` import graph
for forbidden modules — if any are present, the test fails with the
offending import location.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

# Modules that are categorically forbidden in src/dotnet_ai_kit/.
# Adding a network/analytics dependency requires explicit deviation from A-011.
_FORBIDDEN_TOP_LEVEL = {
    "requests",   # HTTP client
    "httpx",      # async HTTP client
    "aiohttp",    # async HTTP client/server
    "urllib3",    # low-level HTTP
    "grpc",       # gRPC client
    # Analytics SDKs:
    "segment",
    "mixpanel",
    "amplitude",
    "rudder_sdk",
    "posthog",
}

# Submodule imports that are forbidden even though the top-level module
# (e.g., `urllib`) has legitimate uses for path/URL parsing.
_FORBIDDEN_SUBMODULES = {
    ("urllib", "request"),       # urllib.request.urlopen / Request
    ("http", "client"),          # http.client.HTTPConnection
}

# socket may be used for non-network purposes (host detection, port-in-use
# checks) but `socket.create_connection` is forbidden. We allow `import socket`
# but flag specific function references.

SRC = Path(__file__).resolve().parent.parent.parent / "src" / "dotnet_ai_kit"


def _iter_python_files() -> list[Path]:
    return sorted(p for p in SRC.rglob("*.py") if "__pycache__" not in p.parts)


def _collect_imports(path: Path) -> list[tuple[str, int]]:
    """Return list of (module_path, lineno) imports in the file."""
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    out: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                out.append((node.module, node.lineno))
    return out


@pytest.mark.parametrize("path", _iter_python_files(), ids=lambda p: p.name)
def test_no_forbidden_network_imports(path: Path) -> None:
    """Per A-011: no top-level network / analytics imports in src/dotnet_ai_kit/."""
    imports = _collect_imports(path)
    for module, lineno in imports:
        head = module.split(".")[0]
        assert head not in _FORBIDDEN_TOP_LEVEL, (
            f"A-011 violation: {path.relative_to(SRC)}:{lineno} imports forbidden "
            f"network/analytics module '{module}'."
        )
        # Submodule paths like "urllib.request"
        parts = tuple(module.split("."))
        for forbidden in _FORBIDDEN_SUBMODULES:
            if parts[:len(forbidden)] == forbidden:
                pytest.fail(
                    f"A-011 violation: {path.relative_to(SRC)}:{lineno} imports "
                    f"forbidden submodule '{module}'."
                )


def test_no_socket_create_connection_calls() -> None:
    """Per A-011: socket.create_connection (outbound TCP) must not be called.

    Searches for the literal call expression in the import graph. Simple
    `import socket` is allowed (e.g., for hostname-based platform checks).
    """
    offenders: list[str] = []
    for path in _iter_python_files():
        text = path.read_text(encoding="utf-8")
        if "socket.create_connection" in text:
            offenders.append(str(path.relative_to(SRC)))
    assert not offenders, (
        f"A-011 violation: socket.create_connection called in: {offenders}"
    )
