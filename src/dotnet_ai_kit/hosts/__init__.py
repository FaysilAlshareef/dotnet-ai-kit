"""Host adapter package for plugin-native architecture (feature 019).

Each supported AI host (Claude Code, Codex CLI, Cursor, GitHub Copilot) has
a `Host` adapter class that knows:

- Where the host's plugin cache lives on disk (per-platform via Path.home())
- How to detect whether the plugin is installed at the host's expected path
- Which per-solution files the host needs written (init-time write surface)

The four concrete adapters are imported and registered here so callers can
look them up by host name without knowing the module layout.

Per data-model.md § 10-12 and research R7.
"""

from __future__ import annotations

from dotnet_ai_kit.hosts.base import Host, InstallStatus
from dotnet_ai_kit.hosts.claude import ClaudeHost
from dotnet_ai_kit.hosts.codex import CodexHost

# Registry of host adapters by host name. Populated incrementally across
# feature-019 commits: commit 4 ships claude; commit 5 adds codex; commit 6
# adds cursor; commit 7 adds copilot.
_HOSTS: dict[str, Host] = {}


def register_host(name: str, host: Host) -> None:
    """Register a host adapter by lowercase name."""
    _HOSTS[name.lower()] = host


def get_host(name: str) -> Host:
    """Look up a host adapter by name (case-insensitive).

    Raises KeyError if the host is not yet registered (e.g., copilot before
    commit 7 lands).
    """
    key = name.lower()
    if key not in _HOSTS:
        raise KeyError(
            f"Host '{name}' has no adapter registered. Available: "
            f"{', '.join(sorted(_HOSTS.keys())) or '(none)'}"
        )
    return _HOSTS[key]


def available_hosts() -> list[str]:
    """Return sorted list of registered host names."""
    return sorted(_HOSTS.keys())


# Commit 4: claude adapter. Commit 5: codex adapter.
# Commits 6/7 will register cursor/copilot.
register_host("claude", ClaudeHost())
register_host("codex", CodexHost())


__all__ = [
    "Host",
    "InstallStatus",
    "ClaudeHost",
    "CodexHost",
    "register_host",
    "get_host",
    "available_hosts",
]
