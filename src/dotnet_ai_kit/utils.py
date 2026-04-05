"""Shared utility functions for dotnet-ai-kit."""

from __future__ import annotations

# Update when a new Haiku model is released
HOOK_MODEL: str = "claude-haiku-4-5-20251001"
HOOK_TIMEOUT_MS: int = 15_000


def parse_version(version_str: str) -> tuple[int, ...]:
    """Parse a version string into a comparable tuple of ints.

    Pre-release suffixes (e.g., -beta, -rc1) are stripped before parsing.
    Non-numeric parts are treated as 0.

    Examples:
        parse_version("1.0.0")       -> (1, 0, 0)
        parse_version("1.2.3")       -> (1, 2, 3)
        parse_version("1.0.0-beta")  -> (1, 0, 0)   # equal to stable
        parse_version("1.0.0-rc.1")  -> (1, 0, 0)   # suffix stripped at -
        parse_version("1.a.0")       -> (1, 0, 0)    # non-numeric -> 0
        parse_version("")            -> (0,)
    """
    base = version_str.strip().split("-")[0]  # strip pre-release suffix
    if not base:
        return (0,)
    parts: list[int] = []
    for part in base.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    return tuple(parts) if parts else (0,)
