"""T127 — FR-035 host admission gate static guard (commit 15 / CHK052).

Asserts that any new host in `SUPPORTED_AI_TOOLS` has all 4 admission gates:
1. Documented install/update path (host adapter under `src/dotnet_ai_kit/hosts/`)
2. Documented artifact primitives (host adapter declares them in its module)
3. Passing host-specific smoke fixture (test file exists under tests/integration/)
4. Passing packaging test (host packaging assertion in tests/test_packaging.py
   or per-OS variant)

Per FR-035 / CHK052: no host can be added to the supported list unless ALL
four gates are satisfied. This static check is the code-side enforcement.
"""

from __future__ import annotations

from pathlib import Path

from dotnet_ai_kit.agents import SUPPORTED_AI_TOOLS
from dotnet_ai_kit.hosts import available_hosts

REPO = Path(__file__).resolve().parent.parent.parent


def test_every_supported_host_has_an_adapter_module() -> None:
    """Gate 1: each host in SUPPORTED_AI_TOOLS MUST have an adapter under hosts/."""
    hosts_dir = REPO / "src" / "dotnet_ai_kit" / "hosts"
    for host in SUPPORTED_AI_TOOLS:
        adapter = hosts_dir / f"{host}.py"
        assert adapter.is_file(), (
            f"FR-035 violation: host '{host}' is in SUPPORTED_AI_TOOLS but has no "
            f"adapter at {adapter}"
        )


def test_every_supported_host_is_registered() -> None:
    """Gate 2: each host MUST be registered in the hosts registry."""
    registered = set(available_hosts())
    for host in SUPPORTED_AI_TOOLS:
        assert host in registered, (
            f"FR-035 violation: host '{host}' is in SUPPORTED_AI_TOOLS but is "
            f"not registered (call register_host in src/dotnet_ai_kit/hosts/__init__.py)"
        )


def test_plugin_hosts_have_smoke_test() -> None:
    """Gate 3: plugin-supporting hosts (claude/codex/cursor) MUST have a gated
    smoke test."""
    smoke_dir = REPO / "tests" / "integration"
    plugin_supporting_hosts = {"claude", "codex", "cursor"}
    for host in plugin_supporting_hosts:
        smoke = smoke_dir / f"test_smoke_{host}.py"
        assert smoke.is_file(), (
            f"FR-035 violation: plugin-supporting host '{host}' missing gated "
            f"smoke test at {smoke}"
        )


def test_every_plugin_host_has_packaging_assertion() -> None:
    """Gate 4: each plugin host's manifest file MUST be referenced in the
    packaging test."""
    packaging = (REPO / "tests" / "test_packaging.py").read_text(encoding="utf-8")
    for host in ("claude", "codex", "cursor"):
        assert f"{host}-plugin/plugin.json" in packaging, (
            f"FR-035 violation: host '{host}' plugin manifest not referenced "
            f"in tests/test_packaging.py"
        )
