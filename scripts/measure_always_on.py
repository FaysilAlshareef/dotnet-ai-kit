#!/usr/bin/env python
"""Measure the SC-004 always-on context token budget (feature 019 / T091 / T129).

Tokenizes the bytes that an AI host would load into context at SessionStart
under feature 019's plugin-native architecture:

  1. SessionStart hook stdout (the compact bootstrap)
  2. Always-on universal rule bodies (5 rules under rules/conventions/)

Outputs JSON to stdout for the CI workflow to consume:

  {
    "session_start_tokens": N,
    "universal_rules_tokens": N,
    "total_tokens": N,
    "target_band_low": 2500,
    "target_band_high": 3000,
    "sc004_pass": bool,
  }

Usage:
  python scripts/measure_always_on.py [--verbose]
  python scripts/measure_always_on.py --json   # default: emit JSON
  python scripts/measure_always_on.py --human  # emit a readable summary
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# SC-004 target band (per measurements.md / spec.md SC-004)
TARGET_BAND_LOW = 2500
TARGET_BAND_HIGH = 3000


def _count_tokens(text: str) -> int:
    """Best-effort token count: prefer tiktoken; fall back to chars/4 heuristic."""
    try:
        import tiktoken  # noqa: PLC0415

        enc = tiktoken.encoding_for_model("gpt-4")
        return len(enc.encode(text))
    except ImportError:
        # Fallback heuristic: 1 token ≈ 4 chars for English text.
        return max(1, len(text) // 4)


def _run_session_start_hook() -> str:
    """Run hooks/session-start-bootstrap.sh and return its stdout.

    Falls back to reading the file body if the shell can't run the script
    (e.g., Windows without Git Bash).
    """
    hook = REPO / "hooks" / "session-start-bootstrap.sh"
    try:
        result = subprocess.run(
            ["bash", str(hook)],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.stdout:
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    # Fallback: read the hook body (slight overestimate — includes shebang/comments)
    if hook.is_file():
        return hook.read_text(encoding="utf-8")
    return ""


def _read_universal_rules() -> str:
    """Concatenate all rules under rules/conventions/."""
    parts: list[str] = []
    conventions = REPO / "rules" / "conventions"
    if conventions.is_dir():
        for r in sorted(conventions.glob("*.md")):
            parts.append(r.read_text(encoding="utf-8"))
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure SC-004 always-on token budget.")
    parser.add_argument(
        "--human",
        action="store_true",
        help="Emit a human-readable summary instead of JSON.",
    )
    args = parser.parse_args()

    session_start = _run_session_start_hook()
    universal_rules = _read_universal_rules()

    session_tokens = _count_tokens(session_start)
    rules_tokens = _count_tokens(universal_rules)
    total = session_tokens + rules_tokens
    pass_band = TARGET_BAND_LOW <= total <= TARGET_BAND_HIGH
    # Per SC-004: ≥65% reduction from baseline ~9000 tokens
    baseline_estimate = 9000  # Pre-feature-019 estimate per measurements.md
    reduction_pct = 100.0 * (baseline_estimate - total) / baseline_estimate

    payload = {
        "session_start_tokens": session_tokens,
        "universal_rules_tokens": rules_tokens,
        "total_tokens": total,
        "baseline_estimate": baseline_estimate,
        "reduction_pct_vs_baseline": round(reduction_pct, 1),
        "target_band_low": TARGET_BAND_LOW,
        "target_band_high": TARGET_BAND_HIGH,
        "sc004_band_pass": pass_band,
        "sc004_reduction_pass": reduction_pct >= 65.0,
    }

    if args.human:
        print(f"SessionStart stdout: {session_tokens} tokens")
        print(f"Universal rules: {rules_tokens} tokens")
        print(f"Total always-on: {total} tokens")
        print(
            f"Target band: {TARGET_BAND_LOW}-{TARGET_BAND_HIGH} tokens "
            f"({'PASS' if pass_band else 'FAIL'})"
        )
        print(
            f"vs baseline ~{baseline_estimate}: "
            f"{reduction_pct:.1f}% reduction "
            f"({'PASS' if reduction_pct >= 65 else 'FAIL'} >=65% target)"
        )
    else:
        print(json.dumps(payload, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
