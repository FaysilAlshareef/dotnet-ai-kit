"""Claude Code version detection (T018a / FR-005).

Used by copier.py to decide whether to emit `if:`-style hook handlers
(supported only on Claude Code >= v2.1.85) or fall back to the
command-pattern matcher behaviour.
"""

from __future__ import annotations

import re
import shutil
import subprocess

MIN_CLAUDE_CODE_VERSION = (2, 1, 85)
_VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


def _parse(version: str) -> tuple[int, int, int] | None:
    match = _VERSION_RE.search(version)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def check_claude_code_version() -> tuple[bool, str | None]:
    """Return ``(meets_minimum, version_string)``.

    ``version_string`` is the raw substring parsed from ``claude --version``
    (e.g. ``"2.1.85"``) or ``None`` when the CLI is absent or the output cannot
    be parsed. ``meets_minimum`` is False when either of those occur.
    """
    if shutil.which("claude") is None:
        return False, None
    try:
        proc = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False, None

    parsed = _parse(proc.stdout) or _parse(proc.stderr)
    if parsed is None:
        return False, None
    return parsed >= MIN_CLAUDE_CODE_VERSION, "{}.{}.{}".format(*parsed)
