# Round 5 Codex Reply

Verdict: **NOT READY-IMPLEMENTATION**.

I did not write `codex-ready.txt`. One release-blocking atomicity gap remains, and two round-4 close-out claims did not fully land.

## Findings

### 1. [CRITICAL] `/dai.upgrade` still leaves `.bak` directories after rollback

`_atomic_upgrade()` snapshots only `_MANIFEST_SCAN_DIRS` (`src/dotnet_ai_kit/cli.py:375`), and `_restore_managed_state()` only restores/removes those same paths (`src/dotnet_ai_kit/cli.py:482`).

The wrapped upgrade body still creates legacy backup directories inside the atomic block:

- `src/dotnet_ai_kit/cli.py:1427` creates `target / f"{cmd_dir_rel}.bak"` (for example `.claude/commands.bak`)
- `src/dotnet_ai_kit/cli.py:1436` creates `target / f"{rules_dir_rel}.bak"` (for example `.claude/rules.bak`)

Those `.bak` paths are not in `_MANIFEST_SCAN_DIRS`, so a failure after backup creation but before completion restores `.claude/commands` / `.claude/rules` but leaves new `.claude/commands.bak` and `.claude/rules.bak` artifacts behind. That is not a byte-for-byte rollback and does not satisfy SC-013's "rollback on any failure" requirement.

The new rollback test does not catch this: `tests/test_upgrade_cli_atomic.py:70` through `tests/test_upgrade_cli_atomic.py:76` checks the sentinel and command file set, but does not assert that `.bak` directories were absent after the failed upgrade.

Suggested fix: remove the legacy `.bak` directory creation from `cli.py::upgrade` now that `_atomic_upgrade()` provides the backup mechanism, or explicitly snapshot/cleanup those `.bak` paths on rollback. I would prefer removing the legacy `.bak` branch to avoid two overlapping backup systems.

### 2. [MEDIUM] T091 still has the skip-on-missing guard

Round 4 says the T091 integration test has "no skip-on-missing", but `tests/integration/test_end_to_end_install.py:31` through `tests/integration/test_end_to_end_install.py:34` still has:

```python
@pytest.mark.skipif(
    not (REPO / "src" / "dotnet_ai_kit" / "__main__.py").exists(),
    reason="package not installed with __main__",
)
```

`src/dotnet_ai_kit/__main__.py` exists in this branch, so the test will run today, but the claimed invariant is not actually enforced. If the entry point regresses or is removed, the integration test skips instead of failing.

### 3. [LOW] A stale MCP `config.yml` reference remains in FR-019

Most of the MCP state references were updated to `.dotnet-ai-kit/mcp-state.yml`, but `specs/018-fix-token-burn/spec.md:170` still says FR-019 "MUST record the result ... in `config.yml`".

That contradicts the updated user story at `specs/018-fix-token-burn/spec.md:83`, the edge case at `specs/018-fix-token-burn/spec.md:125`, and SC-014 at `specs/018-fix-token-burn/spec.md:229`, all of which now correctly say `.dotnet-ai-kit/mcp-state.yml`.

## Atomic Upgrade Spot-Check

What looks correct:

- `_atomic_upgrade()` snapshots on entry and restores on non-zero `typer.Exit` or any other `BaseException` (`src/dotnet_ai_kit/cli.py:527` through `src/dotnet_ai_kit/cli.py:536`).
- `typer.Exit(code=0)` is not restored, which is the right behavior for clean exits. It also does not rotate backups because the exception is re-raised before `src/dotnet_ai_kit/cli.py:537`; that leaves an orphan snapshot until a later successful upgrade rotates it. I do not consider that release-blocking.
- The dry-run `return` inside the with-block at `src/dotnet_ai_kit/cli.py:1391` appears unreachable because dry-run already returns before entering `_atomic_upgrade()` at `src/dotnet_ai_kit/cli.py:1319` through `src/dotnet_ai_kit/cli.py:1336`.
- The JSON-output `return` at `src/dotnet_ai_kit/cli.py:1574` happens after version write, permission application, and manifest finalization attempt (`src/dotnet_ai_kit/cli.py:1533` through `src/dotnet_ai_kit/cli.py:1557`).
- Current primary-repo `copy_*` outputs are mostly under `_MANIFEST_SCAN_DIRS`: commands, rules/profiles, skills, agents, settings, `.mcp.json`, `.cursor`, `.codex`, and Copilot instructions are covered.

Remaining rollback scope concerns:

- The `.bak` directories above are definitely current writes inside the atomic block and are not covered.
- `version.txt`, `.dotnet-ai-kit/.gitignore`, and `manifest.json` are not in `_MANIFEST_SCAN_DIRS`. Most failures before those writes are covered, and manifest failures are swallowed, but an unexpected exception after `version.txt` is written could still leave version state advanced while managed files were restored.
- Linked-repo deployment is outside the primary snapshot. `deploy_to_linked_repos()` calls `copy_commands`, `copy_rules`, `copy_profile`, `copy_skills`, `copy_agents`, and `copy_hook` against each secondary `repo_path` (`src/dotnet_ai_kit/copier.py:1111`, `src/dotnet_ai_kit/copier.py:1120`, `src/dotnet_ai_kit/copier.py:1123`, `src/dotnet_ai_kit/copier.py:1133`, `src/dotnet_ai_kit/copier.py:1142`, `src/dotnet_ai_kit/copier.py:1154`). It catches per-repo exceptions at `src/dotnet_ai_kit/copier.py:1198` and returns failure status rather than raising into `_atomic_upgrade()`. If SC-013 is intended to cover linked secondary repos too, that path is not atomic.

## Round-4 Fix Verification Summary

Verified as landed:

- #2/#4 `copy_skills(detected_paths=None)` skips token-bearing skills with a warning (`src/dotnet_ai_kit/copier.py:433` through `src/dotnet_ai_kit/copier.py:457`), with rewritten tests in `tests/test_copier_skills.py:81` through `tests/test_copier_skills.py:112`.
- #3 FR-033 was amended to the per-skill fail-closed contract (`specs/018-fix-token-burn/spec.md:191`).
- #6 the v2.1.85 hook test patches the copier module binding (`tests/test_copier_hooks.py:278` through `tests/test_copier_hooks.py:285`).
- #7 124 `skills/**/SKILL.md` files exist; spot-check and grep found no `description:` / `when_to_use:` frontmatter using quoted or block scalar style.
- #8 missing-key skill skip uses `caplog` and asserts the skipped skill and missing key (`tests/test_copier_skills.py:113` through `tests/test_copier_skills.py:156`).
- #9 CI includes `development` on push and PR triggers (`.github/workflows/ci.yml:4` through `.github/workflows/ci.yml:7`).
- #10 FR-013 traceability points to `tests/test_copier_agents.py` (`specs/018-fix-token-burn/traceability.md:26`).
- #12 `DeploymentError` text points at `.dotnet-ai-kit/project.yml` / `/dai.detect` instead of the wrong directory (`src/dotnet_ai_kit/copier.py:386` through `src/dotnet_ai_kit/copier.py:389`).
- #13 FR-036 has a static test (`tests/test_rule_pattern_dedup.py:20` through `tests/test_rule_pattern_dedup.py:32`) and traceability points to it (`specs/018-fix-token-burn/traceability.md:50`).
- #14 `/dai.learn` smoke now invokes plan/review and asserts selective topic-file references (`tests/smoke/test_learn_split.py:48` through `tests/smoke/test_learn_split.py:89`).
- Constitution wording no longer says only "Claude Code (v1.0)" (`.specify/memory/constitution.md:71` through `.specify/memory/constitution.md:72`).

Not fully landed:

- #1 atomic upgrade still has the `.bak` rollback hole described above.
- #5 T091 still has the skip-on-missing guard described above.
- #11 FR-019 still has one stale `config.yml` reference described above.

## Verification Notes

I could not reproduce the final test state in this sandbox:

- `python` / `pytest` are not on PATH.
- `uv run python ...` could not use the default cache due permission errors.
- Redirecting `UV_CACHE_DIR` / `UV_PYTHON_INSTALL_DIR` into the workspace got as far as trying to download a managed Python, but network access is blocked.

So I verified by direct code/spec/test inspection and did not claim the `387 passed, 3 skipped` result locally.
