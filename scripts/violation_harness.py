#!/usr/bin/env python
"""SC-010 violation harness (T087).

For each of the 17 violation classes catalogued in the spec, copy the repo
into a temp directory, mutate one file to introduce the violation, run
``scripts/check.py`` against the temp copy, and assert the named test
fails (i.e. the check catches the planted regression).

Usage:
    python scripts/violation_harness.py
    python scripts/violation_harness.py --filter F05
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


@dataclass
class Violation:
    id: str
    description: str
    mutate: callable
    test_node: str  # pytest node id substring expected to fail


def _mutate_alwaysapply_skill(root: Path) -> None:
    f = next(iter((root / "skills").rglob("SKILL.md")))
    raw = f.read_text(encoding="utf-8")
    new = raw.replace("---\n", "---\nalwaysApply: true\n", 1)
    f.write_text(new, encoding="utf-8")


def _mutate_alwaysapply_rule(root: Path) -> None:
    f = next(iter((root / "rules").glob("*.md")))
    raw = f.read_text(encoding="utf-8")
    new = raw.replace("---\n", "---\nalwaysApply: true\n", 1)
    f.write_text(new, encoding="utf-8")


def _mutate_skills_loaded_section(root: Path) -> None:
    f = next(iter((root / "agents").glob("*.md")))
    raw = f.read_text(encoding="utf-8")
    f.write_text(raw + "\n## Skills Loaded\n1. nothing\n", encoding="utf-8")


def _mutate_session_start_forbidden(root: Path) -> None:
    f = root / "hooks" / "session-start-bootstrap.sh"
    f.write_text("#!/usr/bin/env bash\necho 'MIGHT apply'\n", encoding="utf-8")


def _mutate_pre_bash_exit_1(root: Path) -> None:
    f = root / "hooks" / "pre-bash-guard.sh"
    raw = f.read_text(encoding="utf-8")
    f.write_text(raw.replace("exit 2", "exit 1"), encoding="utf-8")


def _mutate_pre_commit_exit_1(root: Path) -> None:
    f = root / "hooks" / "pre-commit-lint.sh"
    raw = f.read_text(encoding="utf-8")
    f.write_text(raw.replace("exit 2", "exit 1", 1), encoding="utf-8")


def _mutate_hooks_matcher_abuse(root: Path) -> None:
    f = root / "hooks" / "hooks.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    data["hooks"]["PreToolUse"][1]["matcher"] = "Bash(git commit*)"
    f.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _mutate_settings_duplicates_plugin(root: Path) -> None:
    f = root / ".claude" / "settings.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    data["hooks"] = {
        "PreToolUse": [
            {
                "matcher": "Bash",
                "hooks": [{"type": "command", "command": "bash hooks/pre-bash-guard.sh"}],
            }
        ]
    }
    f.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _mutate_load_all_skills(root: Path) -> None:
    f = root / "commands" / "implement.md"
    raw = f.read_text(encoding="utf-8")
    f.write_text(
        raw + "\nLoad all skills listed in the agent's Skills Loaded section.\n", encoding="utf-8"
    )


def _mutate_command_over_budget(root: Path) -> None:
    f = root / "commands" / "implement.md"
    raw = f.read_text(encoding="utf-8")
    f.write_text(raw + ("\nfiller line" * 250), encoding="utf-8")


def _mutate_rule_missing_paths(root: Path) -> None:
    f = root / "rules" / "api-design.md"
    raw = f.read_text(encoding="utf-8").splitlines()
    out = [
        line for line in raw if not (line.startswith("paths:") or line.lstrip().startswith('- "'))
    ]
    f.write_text("\n".join(out) + "\n", encoding="utf-8")


def _mutate_profile_missing_paths(root: Path) -> None:
    f = root / "profiles" / "generic" / "clean-arch.md"
    raw = f.read_text(encoding="utf-8").splitlines()
    out = [
        line for line in raw if not (line.startswith("paths:") or line.lstrip().startswith('- "'))
    ]
    f.write_text("\n".join(out) + "\n", encoding="utf-8")


def _mutate_skill_metadata_paths(root: Path) -> None:
    f = next(iter((root / "skills").rglob("SKILL.md")))
    raw = f.read_text(encoding="utf-8")
    f.write_text(
        raw.replace("metadata:\n", "metadata:\n  paths: '**/*.cs'\n", 1),
        encoding="utf-8",
    )


def _mutate_description_not_use_when(root: Path) -> None:
    f = next(iter((root / "skills").rglob("SKILL.md")))
    raw = f.read_text(encoding="utf-8")
    f.write_text(raw.replace("description:", "description: not-a-trigger", 1), encoding="utf-8")


def _mutate_session_hook_too_long(root: Path) -> None:
    f = root / "hooks" / "session-start-bootstrap.sh"
    f.write_text("#!/usr/bin/env bash\n" + "echo line\n" * 40, encoding="utf-8")


def _mutate_universal_rules_over_budget(root: Path) -> None:
    f = root / "rules" / "existing-projects.md"
    f.write_text(f.read_text(encoding="utf-8") + ("\nfiller" * 320), encoding="utf-8")


def _mutate_dynamic_arch_hook_removed(root: Path) -> None:
    f = root / "src" / "dotnet_ai_kit" / "copier.py"
    raw = f.read_text(encoding="utf-8")
    f.write_text(
        raw.replace('"_source": "dotnet-ai-kit-arch"', '"_source": "removed"'), encoding="utf-8"
    )


VIOLATIONS: list[Violation] = [
    Violation(
        "V01-alwaysApply-skill",
        "skill carries alwaysApply",
        _mutate_alwaysapply_skill,
        "test_no_alwaysApply_anywhere",
    ),
    Violation(
        "V02-alwaysApply-rule",
        "rule carries alwaysApply",
        _mutate_alwaysapply_rule,
        "test_rules_have_no_alwaysApply",
    ),
    Violation(
        "V03-skills-loaded-section",
        "agent has Skills Loaded",
        _mutate_skills_loaded_section,
        "test_no_skills_loaded_section",
    ),
    Violation(
        "V04-session-forbidden-phrase",
        "forbidden phrase in session hook",
        _mutate_session_start_forbidden,
        "test_session_start_hook_lacks_forbidden_phrases",
    ),
    Violation(
        "V05-pre-bash-exit1",
        "pre-bash-guard exit 1",
        _mutate_pre_bash_exit_1,
        "test_pre_bash_guard_blocks_rm_rf_with_exit_2",
    ),
    Violation(
        "V06-pre-commit-exit1",
        "pre-commit-lint exit 1",
        _mutate_pre_commit_exit_1,
        "test_pre_commit_lint_blocks_on_format_failure",
    ),
    Violation(
        "V07-matcher-abuse",
        "matcher carries permission pattern",
        _mutate_hooks_matcher_abuse,
        "test_hooks_json_matchers_are_tool_names_only",
    ),
    Violation(
        "V08-settings-duplicate",
        "settings.json duplicates plugin hook",
        _mutate_settings_duplicates_plugin,
        "test_static_claude_settings_does_not_duplicate_plugin_hooks",
    ),
    Violation(
        "V09-load-all-skills",
        "command bulk-load instruction",
        _mutate_load_all_skills,
        "test_no_load_all_skills_block_in_any_command",
    ),
    Violation(
        "V10-command-budget",
        "command over 200 lines",
        _mutate_command_over_budget,
        "test_command_budget",
    ),
    Violation(
        "V11-rule-no-paths",
        "non-universal rule missing paths",
        _mutate_rule_missing_paths,
        "test_non_universal_rules_have_paths",
    ),
    Violation(
        "V12-profile-no-paths",
        "profile missing paths",
        _mutate_profile_missing_paths,
        "test_profiles_have_top_level_paths",
    ),
    Violation(
        "V13-skill-metadata-paths",
        "skill nests paths under metadata",
        _mutate_skill_metadata_paths,
        "test_no_forbidden_nested_metadata_fields",
    ),
    Violation(
        "V14-bad-description",
        "skill description without trigger",
        _mutate_description_not_use_when,
        "test_top_level_description_is_use_when_trigger",
    ),
    Violation(
        "V15-session-hook-too-long",
        "session-start hook over 30 lines",
        _mutate_session_hook_too_long,
        "test_session_start_hook_is_under_30_lines",
    ),
    Violation(
        "V16-universal-budget",
        "universal rules over 300 lines",
        _mutate_universal_rules_over_budget,
        "test_universal_rules_combined_line_budget",
    ),
    Violation(
        "V17-dynamic-arch-source",
        "dynamic arch _source marker removed",
        _mutate_dynamic_arch_hook_removed,
        "test_dynamic_arch_hook_source_marker_preserved",
    ),
]


def _copy_repo(dest: Path) -> Path:
    shutil.copytree(
        REPO,
        dest,
        ignore=shutil.ignore_patterns("__pycache__", "*.egg-info", ".pytest_cache", "node_modules"),
    )
    return dest


def _run_test(temp: Path, node: str) -> int:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-x", "-q", "-k", node, "--rootdir", str(temp)],
        cwd=str(temp),
        capture_output=True,
        text=True,
        timeout=180,
    )
    return proc.returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--filter", help="run only this violation id")
    args = ap.parse_args()

    failures = 0
    for v in VIOLATIONS:
        if args.filter and args.filter not in v.id:
            continue
        with tempfile.TemporaryDirectory() as td:
            temp = _copy_repo(Path(td) / "repo")
            try:
                v.mutate(temp)
            except StopIteration:
                print(f"{v.id}: SKIPPED (mutation target missing)")
                continue
            code = _run_test(temp, v.test_node)
            ok = code != 0  # we expect the planted violation to fail the test
            status = "OK" if ok else "MISS"
            if not ok:
                failures += 1
            print(f"{v.id} ({v.description}) -> test {v.test_node!r}: {status}")
    print(f"\n{failures} violation(s) not caught")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
