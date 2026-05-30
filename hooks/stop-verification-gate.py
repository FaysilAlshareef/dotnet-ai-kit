#!/usr/bin/env python3
"""Claude Stop/SubagentStop hook (T4 completion gate, Claude-scoped — FR-023, SC-004).

Blocks the assistant from declaring a feature/implement flow "done" until `dotnet build`
and `dotnet test` are both green. Mirrors VerificationGateService. No network calls.
Emits the Claude hook decision protocol on stdout.
"""
import json
import subprocess
import sys


def run(args: list[str]) -> int:
    return subprocess.run(args, capture_output=True, text=True).returncode


def block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


def main() -> None:
    if run(["dotnet", "build", "--nologo"]) != 0:
        block("dotnet build failed — fix the build before completing.")
    if run(["dotnet", "test", "--nologo"]) != 0:
        block("dotnet test failed — fix the failing tests before completing.")
    # green: allow completion (no output = no block)
    sys.exit(0)


if __name__ == "__main__":
    main()
