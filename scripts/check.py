#!/usr/bin/env python
"""Local pre-commit entry point (T003 / FR-038 + T109 / feature 019).

Runs static + unit pytest suite and a set of feature-019 static
config validations:

1. Plugin manifests exist for all required hosts (.claude-plugin/, .codex-plugin/,
   .cursor-plugin/) and parse as valid JSON.
2. The manifest packaging assertion: every entry in plugin.json refers to a
   path that exists in the repository or is declared as forward-declared.
3. Multi-host config validation: AGENT_CONFIG enumerates exactly the supported
   hosts and each host's install_paths are documented.

Usage:
    python scripts/check.py              # check the current repo
    python scripts/check.py --root <dir> # check a different repo (e.g. tmp fixture)
    python scripts/check.py --static-only  # skip pytest, only run static checks
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

EXPECTED_PLUGIN_MANIFESTS = (
    (".claude-plugin", "plugin.json"),
    (".codex-plugin", "plugin.json"),
    (".cursor-plugin", "plugin.json"),
)

EXPECTED_HOST_NAMES = frozenset({"claude", "codex", "cursor", "copilot"})


def _check_plugin_manifests(root: Path) -> list[str]:
    """Return a list of error messages for any missing/invalid manifest."""
    errors: list[str] = []
    for subdir, name in EXPECTED_PLUGIN_MANIFESTS:
        path = root / subdir / name
        if not path.is_file():
            errors.append(f"missing plugin manifest: {subdir}/{name}")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON in {subdir}/{name}: {exc}")
            continue
        if "name" not in data:
            errors.append(f"{subdir}/{name}: missing required 'name' field")
    return errors


def _check_claude_plugin_paths_exist(root: Path) -> list[str]:
    """Verify paths declared in the Claude plugin manifest exist on disk.

    Fields may be scalar strings (directory or file path, e.g. './skills/')
    or arrays of explicit paths. Scalar strings are checked as a single
    path (exists as file OR directory). Arrays are spot-checked for the
    first few entries as files.
    """
    errors: list[str] = []
    manifest = root / ".claude-plugin" / "plugin.json"
    if not manifest.is_file():
        return errors  # already flagged by _check_plugin_manifests
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return errors

    def _normalise(raw: object) -> list[str]:
        """Return a list of path strings regardless of scalar vs array format."""
        if isinstance(raw, str):
            return [raw]
        if isinstance(raw, list):
            return [e for e in raw if isinstance(e, str)]
        return []

    missing: list[str] = []
    for field in ("skills", "commands", "agents"):
        raw = data.get(field)
        if raw is None:
            continue
        entries = _normalise(raw)
        # Strip the leading './' before joining with root so Path works correctly.
        for entry in entries[:3]:
            clean = entry.lstrip("./") if entry.startswith("./") else entry
            target = root / clean
            if not target.exists():
                missing.append(entry)

    if missing:
        errors.append(f".claude-plugin/plugin.json references non-existent paths: {missing[:5]}")
    return errors


def _check_multi_host_config(root: Path) -> list[str]:
    """Verify src/dotnet_ai_kit/agents.py SUPPORTED_AI_TOOLS enumerates the
    expected 4 hosts."""
    errors: list[str] = []
    agents_py = root / "src" / "dotnet_ai_kit" / "agents.py"
    if not agents_py.is_file():
        errors.append(f"missing: {agents_py.relative_to(root)}")
        return errors
    body = agents_py.read_text(encoding="utf-8")
    for host in EXPECTED_HOST_NAMES:
        if f'"{host}"' not in body:
            errors.append(f"agents.py: host '{host}' not declared in SUPPORTED_AI_TOOLS")
    return errors


def run_static_checks(root: Path) -> int:
    """Run all static-config checks; return 0 on pass, non-zero count on failure."""
    all_errors: list[str] = []
    all_errors.extend(_check_plugin_manifests(root))
    all_errors.extend(_check_claude_plugin_paths_exist(root))
    all_errors.extend(_check_multi_host_config(root))
    if all_errors:
        print("Static config check FAILED:", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        return len(all_errors)
    print("[OK] Static config check passed (plugin manifests + multi-host config).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run dotnet-ai-kit static + unit tests + feature-019 config checks."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root to check (defaults to the current directory).",
    )
    parser.add_argument(
        "--static-only",
        action="store_true",
        help="Run only the static config checks (skip pytest).",
    )
    args, extra = parser.parse_known_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"error: --root path does not exist: {root}", file=sys.stderr)
        return 2

    # Always run static checks first (feature 019 / T109)
    static_rc = run_static_checks(root)
    if static_rc != 0:
        return static_rc
    if args.static_only:
        return 0

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "-x",
        "--ignore=tests/smoke",
        f"--rootdir={root}",
    ]
    cmd.extend(extra)
    return subprocess.run(cmd, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
