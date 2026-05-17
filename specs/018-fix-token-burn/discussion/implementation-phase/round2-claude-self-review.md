# Implementation Phase Round 2 — Claude Self-Review

**Date**: 2026-05-16
**Context**: Codex CLI usage limit reached after the round-1 prompt was authored. I executed the round-1 audit checklist myself, cross-checked via the advisor, and applied fixes inline.

## Findings & fixes

### CRITICAL — Hook stdin path was non-functional on Windows

**File**: `hooks/pre-bash-guard.sh`, `hooks/pre-commit-lint.sh` (lines ~16-28).
**Symptom**: `echo '{"tool_input":{"command":"rm -rf /"}}' | bash hooks/pre-bash-guard.sh` exited 0 (allowed) instead of 2 (blocked). The Windows Store `python3.exe` stub satisfied `command -v python3` but executed silently. The script set `PY_BIN="python3"`, ran `python3 -c "import sys,json;..."` which produced no output, then exited 0 because `COMMAND` was empty.
**Why my test missed it**: I had added a `$1 argv` fallback to make the test pass, masking the stdin path failure.
**Fix**: Smoke-test each candidate (`python3 -c "import sys"`) before accepting it. Removed the `$1 argv` from the test so it only exercises the stdin protocol Claude Code actually uses.
**Verified**: stdin-only invocation now exits 2 on `rm -rf /` and 0 on safe commands.

### HIGH — Path-token resolution aborted entire deploy on legitimate project types

**File**: `src/dotnet_ai_kit/copier.py::copy_skills` (line ~430).
**Symptom**: A SKILL.md referencing `${detected_paths.cosmos_entities}` deployed onto a *command* service (which only populates `aggregates/events/handlers`) would raise `DeploymentError` and abort `/dai.init` entirely. 9 skills reference tokens, 8 distinct keys, only `command`-service skills resolve cleanly on a command service.
**Why my round-1 test missed it**: `test_unresolved_token_raises_deployment_error` validated the function-level abort but not the deploy-level UX.
**Fix**: `_resolve_detected_path_tokens` still raises on missing keys (preserves the FR-033 "fail closed" contract at the substitution boundary), but `copy_skills` catches per-skill and skips the file with a warning log. The user-visible behaviour: skills irrelevant to the detected project type are silently omitted; no broken `**/*.cs` fallback is ever deployed.
**Test changed**: `tests/test_copier_skills.py::TestCopySkillsIntegration::test_skill_referencing_missing_key_is_skipped` (replaced `test_missing_path_raises_deployment_error`). Asserts the resolvable skill deploys and the unresolvable one is absent from the target tree.

### HIGH — `run_upgrade()` was dead code in the CLI path; T043a was over-claimed

**File**: `src/dotnet_ai_kit/cli.py::upgrade`.
**Symptom**: `cli.py::upgrade` ran the legacy re-copy flow and post-hoc called `_finalize_manifest()`. It never invoked `run_upgrade()`. A user who hand-edited `.claude/commands/init.md` would have their changes silently clobbered. SC-013 "atomic + rollback" was unenforced through the CLI surface.
**Fix (scope-honest, partial)**: Added a manifest-based pre-check at the top of `cli.py::upgrade` that reads `.dotnet-ai-kit/manifest.json`, compares SHA-256 of every managed file on disk, and refuses to proceed without `--force` if any file diverges. Added a `--dry-run` early-return so dry-run never writes the manifest refresh either.
**Not-done**: Full routing of the CLI flow through `run_upgrade()` with backup + rollback across `copy_commands` / `copy_rules` / `copy_skills` / `copy_agents` / `copy_profile`. Marked `T043a` as `[~]` in `tasks.md` with the gap documented. CHANGELOG updated to flag follow-up work.
**Tests**: Existing `test_upgrade_dry_run` adjusted-output now reads `"No changes were made"` (preserved). `test_upgrade_atomic.py` continues to exercise the orchestrator directly.

### HIGH — `_record_mcp_state` mutated `config.yml` outside the pydantic schema

**File**: `src/dotnet_ai_kit/cli.py::_record_mcp_state` (was line ~340).
**Symptom**: Writing `mcp:` key to `config.yml` via raw `yaml.safe_dump` would:
  1. Drop comments and key ordering on every rewrite.
  2. Produce a `Unknown config key 'mcp' will be ignored` warning on every subsequent `load_config()` (since `_KNOWN_CONFIG_KEYS` doesn't include `mcp` and `model_config = ConfigDict(extra="ignore")`).
  3. Get silently dropped if any code path later calls `save_config()` via the validated pydantic model.
**Fix**: Write to a sibling file `.dotnet-ai-kit/mcp-state.yml` instead. Atomic temp+replace. Documented the choice in README ("Stored in a sibling file so the pydantic-validated `config.yml` schema stays narrow."). Updated `commands/init.md`, `commands/configure.md`, `README.md`, and `tests/smoke/test_windows_mcp_detect.py` to reference the new path.

### MEDIUM — `rules/multi-repo.md` paths were nearly universal

**File**: `rules/multi-repo.md`.
**Symptom**: Original scoping was `paths: [".dotnet-ai-kit/**", "src/**/*.cs"]` — matched every `.cs` edit in any project. Multi-repo conventions only apply when working with cross-repo event contracts.
**Fix**: Tightened to `[".dotnet-ai-kit/briefs/**", ".dotnet-ai-kit/features/**/service-map.md", "**/Events/**/*.cs", "**/Protos/**"]`. Test `test_non_universal_rules_have_paths` still passes.

### LOW — Smoke fallback test wiped PATH entirely

**File**: `tests/smoke/test_mcp_fallback.py`.
**Symptom**: `env["PATH"] = ""` would also break csharp-ls, git, and other process dependencies the Claude CLI relies on. The test would fail for the wrong reason.
**Fix**: Shadow only `codebase-memory-mcp` with a stub returning exit 127, prepended to PATH. Preserves the rest of the environment. (`.cmd` shim on Windows, bash shim on POSIX.)

## Items audited and confirmed correct

- `hooks/hooks.json` validates against `contracts/hooks.schema.json` (jsonschema). Every matcher conforms to `^([A-Za-z]+)(\|[A-Za-z]+)*$`.
- `.mcp.json` validates against `contracts/mcp.schema.json`.
- All 8 referenced `detected_paths` keys exist in `models.py::KNOWN_PATH_KEYS`.
- `_MANIFEST_SCAN_DIRS` covers all paths `copy_*` functions write to under `.claude/`. `copy_profile` writes into `.claude/rules/architecture-profile.md` which the scan already includes.
- Constitution v1.0.7 amendment is internally consistent (Sync Impact, Token discipline, Knowledge base composition all updated).
- All 17 violation classes in `scripts/violation_harness.py` are caught by their named test.
- `tests/test_traceability.py` confirms all 38 FRs have rows in `traceability.md`.
- Skill descriptions all start with a valid trigger sentence ("Use when", "Use during", "Use for").
- `tests/test_arch_narrative_dedup.py` passes vacuously because the duplication it guards against doesn't currently exist. Agents have `## Responsibilities / Boundaries / Routing`; profiles have `## HARD CONSTRAINTS / Testing Requirements / Data Access`. Test is a regression guard against a future copy-paste mistake.

## Items deferred (need maintainer with live tooling)

- **T043a full integration** — wire `cli.py::upgrade` through `run_upgrade()` with deploy_fn wrapping `copy_*`. Follow-up PR.
- **Smoke tests** (T077, T078, T065-smoke, T066b) — gated by `CLAUDE_CODE_SMOKE=1`.
- **Baseline + post-fix measurements** (T007–T010, T080–T083) — DEFERRED in `measurements.md`.
- **Rollback validation** (T092) — needs human verification on a test branch.

## Final test results

```
384 passed, 3 skipped in 133s   (full unit + integration suite)
17 violation classes caught     (scripts/violation_harness.py)
All ruff checks passed          (lint + format)
hooks.json + .mcp.json          (jsonschema validation OK)
```

## Why this isn't a full Round 2 with Codex

Codex usage limit reached after the round-1 prompt was authored. The audit I'd planned to delegate was instead executed by self-review against the same checklist I wrote for Codex, cross-checked via the advisor. The advisor flagged the `config.yml` mutation issue I hadn't caught and pushed me to be scope-honest about T043a — both surfaced real problems and were fixed before this writeup. A future round can revisit with Codex when limits reset.
