#!/usr/bin/env python
"""Token measurement harness (T006 / FR-028, SC-001/002/003/007).

Usage:
    python scripts/measure.py --scenario startup --label baseline
    python scripts/measure.py --scenario implement --label post-fix
    python scripts/measure.py --scenario review --label baseline
    python scripts/measure.py --scenario graph-question --label post-fix

The script drives the Claude Code CLI 3 times for the chosen scenario, parses
the `/cost` output, takes the median, and appends one row to
`specs/018-fix-token-burn/measurements.md`. Each row records:

  - Claude Code version (``claude --version``)
  - Active model id (from the session)
  - Plugin commit SHA (``git rev-parse HEAD``)
  - Python version

Smoke tests gate any *automatic* invocation: the script will refuse to run
unless ``CLAUDE_CODE_SMOKE=1`` is set, so CI does not call out to a real LLM
by accident.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCENARIOS = {
    "startup": "Open the project; load nothing.",
    "implement": (
        "Run /dotnet-ai.implement against the 5-task fixture in tests/fixtures/measurement_project."
    ),
    "review": "Run /dotnet-ai.review on the changes proposed for SC-003 baseline.",
    "graph-question": (
        "Answer the structural query: 'Which command handlers in the Orders aggregate "
        "publish OrderPlaced events?' using the project context."
    ),
}

LABELS = {"baseline", "post-fix"}
MEASUREMENTS_PATH = Path("specs/018-fix-token-burn/measurements.md")
COST_RE = re.compile(r"input[:\s]+(\d[\d,]*)\s*tokens", re.IGNORECASE)


def claude_version() -> str:
    try:
        out = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unavailable"


def git_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def run_scenario(scenario: str) -> int:
    """Drive Claude Code once for the named scenario; return the parsed token count.

    Real implementation requires CLAUDE_CODE_SMOKE=1 and a live `claude` CLI.
    Returns -1 when the CLI is unavailable.
    """
    if shutil.which("claude") is None:
        return -1
    prompt = SCENARIOS[scenario]
    proc = subprocess.run(
        ["claude", "--print", "/cost"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=300,
    )
    match = COST_RE.search(proc.stdout)
    if not match:
        return -1
    return int(match.group(1).replace(",", ""))


def median_of_3(scenario: str) -> int:
    runs = [run_scenario(scenario) for _ in range(3)]
    if any(r < 0 for r in runs):
        return -1
    return int(statistics.median(runs))


def append_row(scenario: str, label: str, value: int) -> None:
    MEASUREMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    header_id = {
        "startup": "## Session startup (SC-001)",
        "implement": "## Implementation (SC-002)",
        "review": "## Review (SC-003)",
        "graph-question": "## Graph question (SC-007)",
    }[scenario]
    row = (
        f"- **{label}** | tokens={value if value >= 0 else 'DEFERRED'} | "
        f"claude={claude_version()} | sha={git_sha()} | "
        f"python={sys.version_info.major}.{sys.version_info.minor} | "
        f"at={datetime.now(timezone.utc).isoformat()}"
    )

    existing = MEASUREMENTS_PATH.read_text(encoding="utf-8") if MEASUREMENTS_PATH.exists() else ""
    if header_id not in existing:
        existing = existing.rstrip() + f"\n\n{header_id}\n\n"
    existing = existing.rstrip() + "\n" + row + "\n"
    MEASUREMENTS_PATH.write_text(existing, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure token burn for a scenario.")
    parser.add_argument("--scenario", choices=list(SCENARIOS), required=True)
    parser.add_argument("--label", choices=sorted(LABELS), required=True)
    parser.add_argument(
        "--allow-offline",
        action="store_true",
        help="Append a DEFERRED row instead of erroring when claude is unavailable.",
    )
    args = parser.parse_args()

    if not args.allow_offline and os.environ.get("CLAUDE_CODE_SMOKE") != "1":
        print(
            "Refusing to drive Claude Code: set CLAUDE_CODE_SMOKE=1 or pass --allow-offline.",
            file=sys.stderr,
        )
        return 2

    if args.allow_offline:
        value = -1
    else:
        value = median_of_3(args.scenario)

    append_row(args.scenario, args.label, value)
    print(json.dumps({"scenario": args.scenario, "label": args.label, "tokens": value}))
    return 0 if value >= 0 or args.allow_offline else 1


if __name__ == "__main__":
    raise SystemExit(main())
