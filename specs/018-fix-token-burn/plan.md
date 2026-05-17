# Implementation Plan: Fix Token Burn in dotnet-ai-kit Plugin

**Branch**: `018-fix-token-burn` | **Date**: 2026-05-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/018-fix-token-burn/spec.md`
**Status**: Draft v2 (post Round 2; pending Codex verification)
**Reviewers**: Claude (Opus 4.7, 1M context) + Codex (gpt-5.5 xhigh)

## Summary

Eliminate the 18 token-burn and safety findings agreed in `issues/token-burn-optimization/FINAL-REPORT.md` by (1) fixing Claude Code metadata and frontmatter so lazy loading actually works, (2) replacing eager-loading instructions in commands, agent bodies, and the SessionStart hook with MCP-first lazy defaults, (3) fixing two safety bugs in blocking hooks (`exit 1` → `exit 2`), (4) making `codebase-memory-mcp >= 0.6.1` a required graph MCP alongside `csharp-ls`, (5) splitting the always-loaded constitution into compact index + 6 on-demand topic files, and (6) landing a 3-tier test suite (static / unit / smoke) plus a generated-file manifest at `.dotnet-ai-kit/manifest.json` for atomic `/dai.upgrade`.

**Delivery**: single feature branch, **7 sequenced PRs** (PR0 baseline → PR1 hooks/safety → PR2a frontmatter rewrite → PR2b load_project+manifest+atomic upgrade → PR3 lazy-load cleanup + constitution amendment → PR4 MCP/memory → PR5 measurement/CI).

## Technical Context

**Language/Version**: Python 3.10+ (CLI), bash for hooks (existing — no rewrite)
**Primary Dependencies**: typer, pydantic v2, jinja2, pyyaml, rich (existing in `pyproject.toml`); pytest + pytest-cov + ruff (`[dev]`)
**Storage**: YAML (`.dotnet-ai-kit/config.yml`, `project.yml`), JSON (`.mcp.json`, `.dotnet-ai-kit/manifest.json` — new), markdown (all rules/skills/agents/commands)
**Testing**: pytest, three categories:
- **Static checks** — frontmatter + grep + line-count assertions over `commands/`, `rules/`, `skills/`, `agents/`, `profiles/`, `hooks/`. Runs every PR (target ≤30s).
- **Unit tests** — Python module behaviour for `config.py` (load/save roundtrip + legacy), `copier.py` (path-token substitution, manifest, atomic upgrade rollback), `manifest.py`, `upgrade.py`, `mcp_check.py`, hook script exit codes.
- **Smoke/transcript tests** — `tests/smoke/` directory + `pytest.mark.smoke` marker. Gated by `CLAUDE_CODE_SMOKE=1` env var and `claude` on PATH. Run nightly or on `[smoke]` PR label.
**Target Platform**: Windows / macOS / Linux (Python `pathlib`, no OS-specific paths)
**Project Type**: CLI tool + Claude Code plugin (single Python package + plugin manifest)
**Performance Goals**: Per spec SCs — startup tokens −50% (median of 3); `/dai.implement` −35%; `/dai.review` −30%; graph question via MCP −70%; static+unit pytest ≤30s
**Constraints**:
- Backward compatibility — `/dai.upgrade` migrates legacy installs idempotently AND atomically (FR-031, Q3 clarification); `load_project()` accepts both nested and legacy top-level YAML (FR-009).
- Cross-tool tolerance — `metadata:` block stays in skills for non-Claude consumers (Cursor/Copilot future); only Claude-visible fields move to top level (FR-006).
- Claude Code v2.1.85+ required for handler `if:` filter support (FR-005). Plan-phase decision: runtime detect in `mcp_check.py`-style helper, document min version in README. `.claude-plugin/plugin.json` schema does NOT currently expose a `minimumClaudeCodeVersion` field (verified per `code.claude.com/docs/en/plugins-reference`).
- Atomic upgrade required (Q3 clarification): full rollback on any per-file failure via per-file backups + manifest (FR-031, SC-013).
**Scale/Scope** (verified physical-line counts via `wc -l`):
- 124 skill files (frontmatter rewrite + description rewrite)
- 16 rule files (path scoping + `alwaysApply` strip)
- 12 profile files (`alwaysApply` strip + `paths:` add)
- 16 of 27 command files ("Load all skills listed" removal); 7 operational commands get MCP-first block
- **3 over-budget commands**: `commands/implement.md` 235, `commands/tasks.md` 203, `commands/clarify.md` 202 lines (verified 2026-05-16) — must trim ≤200
- 13 agent files (delete `## Skills Loaded`); 2 also need `Availability: Always` stripped
- **5 hook scripts** (corrected from 4): `pre-bash-guard.sh`, `pre-commit-lint.sh`, `post-edit-format.sh`, `post-scaffold-restore.sh`, `session-start-bootstrap.sh`. Plus `hooks/hooks.json` matcher/`if:` rewrites.
- ~9 Python module sites in `cli.py` + `copier.py` migrating to `load_project()` (6 in `cli.py`, 3 in `copier.py`)
- 1 new file: `.dotnet-ai-kit/manifest.json` schema + writer/reader
- 1 packaging gap to close: `pyproject.toml` `[tool.hatch.build.targets.wheel.force-include]` MUST add `.claude-plugin/`, `hooks/`, `.mcp.json`

## Constitution Check

Evaluated against `.specify/memory/constitution.md` v1.0.6 (2026-03-28).

### I. Detect-First, Respect-Existing (NON-NEGOTIABLE) — ✅ PASS

Feature targets the plugin's own metadata/code. The detect-first principle applies via `/dai.upgrade` — MUST NOT rewrite user-modified files. FR-031 + FR-032 + manifest checksums enforce this: ambiguous files backed up with warning; explicit `--force` to override.

### II. Pattern Fidelity — ✅ PASS

All new Python code matches existing style: `pathlib.Path` not `os.path`, `subprocess.run([...])` without `shell=True`, pydantic v2 + `from __future__ import annotations`, explicit UTF-8, ruff-clean.

### III. Architecture & Platform Agnostic — ✅ PASS

Changes affect Claude Code only; nested `metadata:` survives for Cursor/Copilot future. Hook scripts retain `command -v bash` short-circuit; manifest is portable JSON; `pathlib` everywhere.

### IV. Best Practices & Quality — ✅ PASS

TDD for new test suite — failing tests committed first per phase. SOLID respected (manifest reader, manifest writer, atomic-deploy context manager — single-responsibility each). Documentation-first: `codebase-memory-mcp >=0.6.1` verified against actual GitHub releases + PyPI on 2026-05-16. Error handling: clear messages on FR-033 fail-closed substitution; `--dry-run` for `/dai.upgrade`.

### V. Safety & Token Discipline — ⚠️ PASS-CONDITIONAL

- **Token limits**: FR-025/026/027 enforce ≤200 cmds / ≤100 rules / ≤400 skills. 3 over-budget commands trimmed in PR3.
- **Rule count semantics**: constitution v1.0.6 says "16 rules (always loaded)". Spec changes behaviour to **4 universal + 12 path-scoped** via FR-011. Per Codex round 1: **this is PASS-CONDITIONAL on PR3 including the v1.0.7 constitution amendment in the same PR**. If PR3 merges without the amendment, it becomes a violation. No Complexity Tracking entry — governance is not implementation complexity.
- **`--dry-run` support**: FR-031 mandates for `/dai.upgrade`.
- **Reversibility**: atomic rollback (Q3) preserves "every action reversible".
- **No deploys**: feature touches no CI/CD or environment.

**Verdict**: 4 gates ✅ PASS, 1 gate ⚠️ PASS-CONDITIONAL on PR3 amendment.

## Project Structure

### Documentation (this feature)

```text
specs/018-fix-token-burn/
├── plan.md                         # This file
├── research.md                     # Phase 0 output (next step after Codex READY)
├── data-model.md                   # Phase 1 output
├── quickstart.md                   # Phase 1 output
├── contracts/                      # Phase 1 output
│   ├── manifest.schema.json
│   ├── skill-frontmatter.schema.yaml
│   ├── rule-frontmatter.schema.yaml
│   ├── hooks.schema.json
│   └── mcp.schema.json
├── traceability.md                 # FR → test mapping (FR-028)
├── measurements.md                 # PR0 baseline + PR5 post-fix /cost captures (FR-030)
├── spec.md
├── checklists/requirements.md
├── discussion/
│   ├── spec-phase/                 # round 1+2 spec discussion (closed)
│   └── plan-phase/                 # this round's Codex discussion
└── tasks.md                        # Phase 2 (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/dotnet_ai_kit/
├── __init__.py                # __version__ — source of truth for manifest plugin_version field
├── cli.py                     # MODIFIED: 6 raw-YAML sites → load_project() (FR-009)
├── config.py                  # MODIFIED MINIMALLY: load_project() already handles nested+legacy; no manifest logic here
├── copier.py                  # MODIFIED: atomic deploy hook, token substitution fail-closed (FR-033), manifest writer wired in
├── agents.py                  # MODIFIED: drop expertise→skills lambda (FR-013)
├── manifest.py                # NEW: pydantic Manifest+DeployedFile models, read/write/diff for .dotnet-ai-kit/manifest.json
├── upgrade.py                 # NEW: /dai.upgrade orchestrator with atomic rollback (FR-031)
├── mcp_check.py               # NEW: codebase-memory-mcp --version detection + Claude Code version detect (FR-019, FR-035, FR-005)
└── (existing modules unchanged: detection.py, extensions.py, models.py, utils.py)

hooks/
├── session-start-bootstrap.sh # MODIFIED: lazy-default, MCP-first message (FR-001)
├── pre-bash-guard.sh          # MODIFIED: exit 2 on block (FR-002)
├── pre-commit-lint.sh         # MODIFIED: exit 2 on block (FR-003)
├── post-edit-format.sh        # MODIFIED: short-circuit retained as fallback (still self-filters non-.cs)
├── post-scaffold-restore.sh   # MODIFIED: matcher/if: cleanup (was missing from v1 plan)
└── hooks.json                 # MODIFIED: matcher contains only tool names; if: carries command/file filters (FR-004/005)

skills/**/SKILL.md             # MODIFIED ×124: top-level activation fields (FR-006/007); metadata: kept for Cursor/Copilot
rules/*.md                     # MODIFIED ×16: alwaysApply removed; 4 universal stay unscoped (≤300 lines combined); 12 path-scoped (FR-011)
profiles/**/*.md               # MODIFIED ×12: alwaysApply removed, paths: added (FR-017)
agents/*.md                    # MODIFIED ×13: drop ## Skills Loaded; 2 drop Availability: Always (FR-014/015)
commands/*.md                  # MODIFIED ×16: drop "Load all skills listed"; ×7 add MCP-first block (FR-021); ×3 trim ≤200 lines (FR-025)
commands/learn.md              # MODIFIED: 6-file memory split (architecture/domain-model/event-flow/interfaces/dependencies/conventions), drop "always-loaded rule" (FR-023/024)

.mcp.json                      # MODIFIED: add codebase-memory-mcp registration with stable name + sidecar min-version metadata key (FR-018)
                               # Note: `.mcp.json` schema lacks native min-version; min is enforced via src/dotnet_ai_kit/mcp_check.py runtime check.

.claude/settings.json          # MODIFIED: remove duplicated plugin static hooks. EXCEPTION: dynamic `_source: dotnet-ai-kit-arch` hook
                               # (injected by copier.py:667-672) remains — it encodes project-specific architecture constraints (per FR-004 exception)
                               # but /dai.upgrade rewrites its filter to use handler-level `if:` when Claude Code v2.1.85+ detected.

pyproject.toml                 # MODIFIED: [tool.hatch.build.targets.wheel.force-include] adds `.claude-plugin/`, `hooks/`, `.mcp.json`

.github/workflows/ci.yml       # MODIFIED: invoke new pytest suite; gate merge on static+unit; smoke tests on nightly stage

tests/
├── test_skill_frontmatter.py     # NEW (static): FR-006, FR-008, FR-014, FR-015 over skills/
├── test_rule_frontmatter.py      # NEW (static): FR-008, FR-011, universal-rule whitelist + ≤300 combined
├── test_agent_bodies.py          # NEW (static): FR-014, FR-015
├── test_command_bodies.py        # NEW (static): FR-012, FR-021, FR-022 (fallback-notice string), FR-023
├── test_hook_config.py           # NEW (static): FR-004, FR-005, FR-034; hook-ownership boundary (no static-hook duplication; dynamic arch hook preserved)
├── test_hook_exit_codes.py       # NEW (unit): FR-002, FR-003 — subprocess.run script with dangerous input asserts exit 2
├── test_load_project_migration.py  # NEW (unit): FR-009 — nested vs legacy parsing parity
├── test_path_token_substitution.py # NEW (unit): FR-010 happy path; FR-033 abort-on-missing-key (3 fixtures: all keys, missing required, extra ignored)
├── test_manifest.py              # NEW (unit): Manifest+DeployedFile read/write/diff roundtrip
├── test_upgrade_atomic.py        # NEW (unit): FR-031, SC-013 — simulated mid-run failure causes full rollback; idempotent re-run produces zero diff
├── test_mcp_version_check.py     # NEW (unit): FR-019 detection logic (mocked subprocess for `codebase-memory-mcp --version`)
├── test_budgets.py               # NEW (static): FR-025/026/027/037
├── test_traceability.py          # NEW (static): traceability.md asserts every FR has ≥1 test row
├── test_packaging.py             # NEW (unit): wheel build + packaged-asset existence under _get_package_dir() for wheel + dev layouts
├── test_mcp_config.py            # NEW (unit): .mcp.json shape preserves csharp-ls, adds codebase-memory-mcp, captures sidecar min-version, no clobber
├── test_local_check_entrypoint.py  # NEW (unit): scripts/check.py runs static+unit suite, non-zero on violation
├── test_copier_skills.py         # UPDATED: invert "leave/remove path on missing key" → "raise deployment error" (FR-033)
├── test_copier_hooks.py          # UPDATED: (a) dynamic arch hook injection still works post FR-004 exception; (b) when Claude Code v2.1.85+ detected, the injected hook uses handler-level `if:` filter rather than command-pattern matcher (FR-005)
└── tests/smoke/                  # NEW directory
    ├── test_hook_blocks.py       # SMOKE: Claude Code session with `Bash(rm -rf /)` → tool call denied (SC-004)
    ├── test_mcp_fallback.py      # SMOKE: stop codebase-memory-mcp → command emits exact fallback line (SC-008)
    ├── test_learn_split.py       # SMOKE: /dai.learn produces 1 index + 6 topic files (SC-012)
    └── conftest.py               # pytest.mark.smoke + env-gating + skip-unless-claude-on-PATH

scripts/
├── check.py                   # NEW (cross-platform, FR-038): runs static + unit, non-zero on violation
├── check.ps1                  # NEW: PowerShell wrapper invoking scripts/check.py
└── rewrite_skill_frontmatter.py  # NEW (one-shot for PR2a): mechanical SKILL.md frontmatter migration

Makefile                       # NEW (optional): `make check` invokes scripts/check.py

.dotnet-ai-kit/                # ⓘ This directory is project-state (deployed by /dai.init). The plugin DOES NOT ship a .dotnet-ai-kit/
                               # at the plugin repo root. Per-project, after PR2b + PR4:
                               #   manifest.json       (NEW — generated-file manifest, JSON, SHA-256 per file)
                               #   backups/upgrade/<run_id>/  (NEW — atomic-rollback backups; gitignored)
                               #   .gitignore          (NEW — ignore backups/upgrade/)
                               #   config.yml          (existing)
                               #   project.yml         (existing)
                               #   features/           (existing)
```

**Structure Decision**: Continue the existing flat `src/dotnet_ai_kit/` package layout (no submodules) — adds 3 small modules (`manifest.py`, `upgrade.py`, `mcp_check.py`) consistent with current style. One new pytest file per testable invariant rather than one giant module.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Atomic upgrade with per-file backup + rollback (FR-031, SC-013) | Clarify Q3 chose "Stop & roll back"; protects against half-migrated state across ~150 file rewrites | Best-effort "continue on error" leaves mixed state contradicting idempotency promise; "stop & preserve partial" requires `--resume` + parallel migration state — more code surface |
| JSON manifest with SHA-256 per file (FR-032) | Clarify Q1 chose JSON; required for FR-031 atomic rollback to detect user modifications | Sidecars create tree noise (rejected Q1); embedded comments break on any user edit; SQLite overkill for ~150 files |
| Three-tier test split (static / unit / smoke) | Static must run every PR (≤30s SC-009); unit covers Python module behaviour; smoke needs real Claude Code session (not feasible in default CI) | Single tier either bloats CI (all smoke) or skips runtime invariants like hook-block-at-runtime (all static) |

All other plan choices flow directly from the spec's FRs — no other complexity needs justification beyond what the FRs already demand. Constitution amendment (v1.0.7) is governance, not implementation complexity, so it lives in PR3 docs and not this table.

## Phase 0: Outline & Research

See `research.md` (generated after Codex round 2 verification).

Research tasks already resolved during round 1 (recorded for completeness — `research.md` will cite these):

- **R1 (resolved)**: `codebase-memory-mcp` minimum version = **`>= 0.6.1`**. PyPI publishes `0.6.1`, GitHub latest release tag `v0.6.1`, Windows amd64 asset available at `https://github.com/DeusData/codebase-memory-mcp/releases/download/v0.6.1/codebase-memory-mcp-windows-amd64.zip`. Verified 2026-05-16. Phase 0 re-verifies latest before PR4 opens and records the re-verification date.
- **R2 (resolved)**: Claude Code v2.1.85+ required for handler `if:` (`https://code.claude.com/docs/en/hooks-guide`). `.claude-plugin/plugin.json` lacks `minimumClaudeCodeVersion`; **decision: runtime detect in `src/dotnet_ai_kit/mcp_check.py`** (or a sibling `claude_version_check.py`) + document in README.
- **R3 (deferred to PR3 author)**: Concrete trim targets for `implement.md`/`tasks.md`/`clarify.md`. Plan-phase notes: identify sections that are routing/load-instructions (already covered by command body changes elsewhere) and collapse those first.
- **R4 (resolved with Codex web check)**: Largest current agent ~51 lines, largest profile ~73 lines. FR-037 budgets **ratified as agents ≤ 120, profiles ≤ 100** with comfortable margin.
- **R5 (executed in PR0)**: Baseline `/cost` for SC-001/002/003 + SC-007 graph question. PR0 is the dedicated baseline-capture PR.
- **R6 (resolved)**: Manifest fields locked per spec FR-032: `path`, `sha256`, `plugin_version`, `deployed_at`, plus `source_template: str | None` (origin in the plugin repo) for diagnostic traceability. No "managed-by-version range" — single plugin version per deployed file; rotation handled by retaining last 3 backup runs.

## Phase 1: Design & Contracts

See `data-model.md`, `contracts/`, `quickstart.md`.

**Entities** (full schemas in `data-model.md`):

- `DeployedFile`: `path: str`, `sha256: str`, `plugin_version: str`, `deployed_at: datetime`, `source_template: str | None`
- `Manifest`: `plugin_version: str`, `created_at: datetime`, `last_upgrade_at: datetime | None`, `files: list[DeployedFile]`
- `UpgradeBackup` (in-memory + persisted to `.dotnet-ai-kit/backups/upgrade/<run_id>/`): `original_path`, `original_sha256`, `original_bytes`, `restored: bool`
- `MCPHealth`: `server_name`, `present: bool`, `version: str | None`, `min_required: str`, `meets_minimum: bool`

**Contracts** (in `contracts/`):

- `manifest.schema.json` — JSON Schema for `.dotnet-ai-kit/manifest.json`
- `skill-frontmatter.schema.yaml` — required top-level fields post FR-006
- `rule-frontmatter.schema.yaml` — required top-level fields post FR-008
- `hooks.schema.json` — `matcher` enum (tool names only) + `if` field permitted; blocking-hook exit-code policy
- `mcp.schema.json` — `.mcp.json` shape post FR-018 (stable server name + sidecar `dotnet_ai_kit_min_version` metadata key)

**Quickstart** (`quickstart.md`):

- Run `/dai.upgrade` on existing installed project: `--dry-run` → live → verify
- Install `codebase-memory-mcp` on Windows PowerShell / macOS+Linux PyPI / manual zip
- Run new pytest suite locally: `python scripts/check.py` (or `make check`, or `scripts/check.ps1`)
- Interpret manifest after `/dai.init` or `/dai.upgrade`
- Trigger smoke tests: `CLAUDE_CODE_SMOKE=1 pytest -m smoke`

## PR-by-PR Implementation Map

Each PR is a single, atomic delivery slice. Static-check tests run on every PR; unit tests added per PR; smoke tests aggregated and gated nightly.

### PR 0 — Baseline measurement

**Touches**: `tests/fixtures/measurement_project/` (new minimal microservice scaffold), `specs/018-fix-token-burn/measurements.md` (baseline section only), optional `scripts/measure.py` helper.

**Behaviour**: no plugin changes. Captures `/cost` baseline for SC-001/002/003/007 with pinned Claude Code version + model id. Median of 3 reads per scenario.

**Acceptance**: `measurements.md` contains `## Baseline` section with timestamp, Claude Code version, model id, scenario tables.

### PR 1 — Hooks & startup safety (Phase 0)

**Touches**: 5 hook scripts (`pre-bash-guard.sh`, `pre-commit-lint.sh`, `post-edit-format.sh`, `post-scaffold-restore.sh`, `session-start-bootstrap.sh`), `hooks/hooks.json`, `.claude/settings.json` (remove static plugin-hook duplicates; preserve dynamic `_source: dotnet-ai-kit-arch`), `pyproject.toml` (add `.claude-plugin/`, `hooks/`, `.mcp.json` to wheel force-include).

**FRs**: FR-001, FR-002, FR-003, FR-004 (incl. documented exception), FR-005, FR-034.
**SCs**: SC-004, SC-005, SC-015.
**Tests**: `test_hook_config.py`, `test_hook_exit_codes.py`, `test_packaging.py`.

**Acceptance**:
- SessionStart message removes "load skills before acting" / "MIGHT apply" phrasing.
- `pre-bash-guard.sh` and `pre-commit-lint.sh` exit `2` on block.
- `hooks/hooks.json` matchers contain only tool names; `if:` carries command/file filters.
- `.claude/settings.json` removes static-plugin-hook duplicates; dynamic arch hook (`_source: dotnet-ai-kit-arch`) preserved.
- `pip install -e .` then `python -m build` produces wheel containing `.claude-plugin/plugin.json`, `hooks/*.sh`, `.mcp.json` under `dotnet_ai_kit/bundled/` (or equivalent location).

### PR 2a — Frontmatter rewrite + static tests

**Touches**: 124 SKILL.md, 16 rules, 12 profiles, 13 agents, `scripts/rewrite_skill_frontmatter.py` (one-shot migration script), static tests.

**FRs**: FR-006, FR-007, FR-008, FR-014, FR-015, FR-017.
**Tests**: `test_skill_frontmatter.py`, `test_rule_frontmatter.py`, `test_agent_bodies.py`.

**Migration strategy**:
1. `scripts/rewrite_skill_frontmatter.py` reads each SKILL.md, lifts `metadata.{paths, when-to-use, alwaysApply, disable-model-invocation, user-invocable}` to top level, normalises `when-to-use` → `when_to_use`, drops `alwaysApply`.
2. Description rewrite pass: if `description` starts with "Use when …" keep; else prepend "Use when " + first sentence pulled from `metadata.when-to-use`. Manual review for ~30 ambiguous cases.
3. Apply same rules to rules/profiles (drop `alwaysApply` only — already in correct shape otherwise).
4. Delete `## Skills Loaded` sections from 13 agents; strip `Availability: Always` from 2 agents.

**Acceptance**: every SKILL.md passes top-level frontmatter check; no `alwaysApply` anywhere; agent `## Skills Loaded` and `Availability: Always` absent.

### PR 2b — load_project + manifest + atomic upgrade

**Touches**: `src/dotnet_ai_kit/{cli,copier}.py` (6+3 `load_project()` migrations), new `src/dotnet_ai_kit/{manifest,upgrade}.py`, `commands/upgrade.md` (operator-facing docs), `tests/`.

**FRs**: FR-009, FR-010, FR-031, FR-032, FR-033.
**SCs**: SC-006, SC-013, SC-016.
**Tests**: `test_load_project_migration.py`, `test_path_token_substitution.py`, `test_manifest.py`, `test_upgrade_atomic.py`, `test_copier_skills.py` (updated), `test_copier_hooks.py` (updated).

**Atomic upgrade design** (`upgrade.py` orchestrator):
1. Read existing `.dotnet-ai-kit/manifest.json`. If absent, treat as legacy install: scan known managed paths.
2. For each managed file: compare current SHA-256 to manifest's recorded SHA. Match = generated, differ = user-modified → require `--force` or abort.
3. Create `.dotnet-ai-kit/backups/upgrade/<ISO timestamp>-<uuid4>/` (aligned with existing `backups/` namespace per Codex correction).
4. Copy every managed file's original bytes into backup dir BEFORE any write.
5. Sequentially write new versions. On any write/IOError → walk backup dir, restore every backed-up file, exit non-zero with failing-file diagnostic.
6. On success → write new `manifest.json`, retain last 3 backup runs (rotate older).
7. `.dotnet-ai-kit/.gitignore` ensures `backups/upgrade/` isn't committed.

### PR 3 — Lazy-loading cleanup + constitution amendment (Phase 2)

**Touches**: 16 rule files (path scoping), 12 profile files (path scoping), 16 command files (drop "Load all skills listed"), 3 commands trim ≤200 lines (`implement.md` 235→≤200, `tasks.md` 203→≤200, `clarify.md` 202→≤200), `src/dotnet_ai_kit/agents.py` (drop `expertise → skills` lambda), `.specify/memory/constitution.md` (v1.0.7 amendment — rule semantics).

**FRs**: FR-011, FR-012, FR-013, FR-016, FR-025, FR-036, FR-037 (ratified ≤120 agents / ≤100 profiles per R4).
**SCs**: SC-011.
**Tests**: `test_command_bodies.py`, `test_budgets.py`.

**Constitution amendment** (PR-3 in-PR change, ratifies the PASS-CONDITIONAL Gate V):
- Version bump 1.0.6 → 1.0.7
- Sync Impact Report entry: rule semantics — "16 rules total: 4 universal (always loaded), 12 path-scoped"
- Token discipline section updated to match FR-011

### PR 4 — MCP integration + memory split (Phase 3)

**Touches**: `.mcp.json` (add `codebase-memory-mcp` registration + sidecar min-version key), `README.md`, `commands/configure.md`, 7 operational commands (`detect`, `learn`, `analyze`, `plan`, `implement`, `review`, `add-tests`) — add MCP-first instruction block + exact FR-022 fallback line, `commands/learn.md` (6-file memory split + drop "always-loaded rule"), `commands/init.md` (codebase-memory-mcp detection prompt), new `src/dotnet_ai_kit/mcp_check.py`.

**FRs**: FR-018, FR-019, FR-020, FR-021, FR-022, FR-023, FR-024, FR-035.
**SCs**: SC-007, SC-008, SC-012, SC-014.
**Tests**: `test_command_bodies.py` (MCP-first block + exact fallback line present in 7 commands), `test_mcp_version_check.py`, `test_mcp_config.py`, smoke tests for runtime fallback emission.

**Exact fallback line** (FR-022, ratified by Codex):
```
MCP unavailable: codebase-memory-mcp is not connected or below >=0.6.1; falling back to csharp-ls + grep/read.
```

**MCP min-version enforcement**: `.mcp.json` doesn't natively support min-version; `mcp_check.py` invokes `codebase-memory-mcp --version` and compares to plugin-side `MIN_CODEBASE_MEMORY_MCP_VERSION = "0.6.1"`. Sidecar key `dotnet_ai_kit_min_version: "0.6.1"` in `.mcp.json` for documentation/inspection.

### PR 5 — Final CI gates + measurements (Phase 4)

**Touches**: `.github/workflows/ci.yml`, `scripts/check.py` (+ `check.ps1` wrapper, optional `Makefile`), `specs/018-fix-token-burn/{measurements.md, traceability.md}`, remaining static + traceability tests.

**FRs**: FR-025–FR-030, FR-038.
**SCs**: SC-001, SC-002, SC-003, SC-009, SC-010.
**Tests**: `test_budgets.py` (final guard), `test_traceability.py`, `test_local_check_entrypoint.py`.

**Measurement protocol** (FR-030, uses PR0 baseline):
- Same fixture project, same Claude Code version, same model id.
- Capture 3 fresh `/cost` reads per scenario; median wins.
- Post-fix measurements stored in `measurements.md` under `## Post-fix`.
- PR5 fails to merge if any of SC-001/SC-002/SC-003 medians fail to meet target — note: spec re-cast these as **measured targets**, so plan-phase decision is: enforce as gates only after PR0 baseline + final measurement, and only flag soft regressions as warnings. Hard gate: SC-004/SC-005/SC-006/SC-013/SC-014/SC-015/SC-016 (binary safety/correctness).

## Rollout & Backward Compatibility

- **Existing installed projects**: `/dai.upgrade` handles legacy `metadata.paths` + `alwaysApply` rules. No manifest → scan known managed paths.
- **CI**: PR0 lands first; PR1 cannot merge until PR0's baseline is committed. PR2a + PR2b can be reviewed in parallel but PR2b cannot merge before PR2a.
- **No deprecation flags**: legacy YAML continues working via `load_project()`. Cursor/Copilot `metadata:` survives.
- **README**: update Claude Code version mention to "v2.1.85+ recommended; v1.0 supported with reduced hook fidelity (no `if:` filters)."
- **Constitution v1.0.7**: shipped in PR3, consumed by all later PRs.

## Phase 0 research findings (preview, from Codex web research 2026-05-16)

These will be formalised into `research.md` after round 2 verification:

| Question | Resolution | URL |
|---|---|---|
| codebase-memory-mcp version | `>= 0.6.1` (GitHub latest, PyPI current, Windows amd64 binary) | `https://github.com/DeusData/codebase-memory-mcp/releases` |
| Windows binary install | `https://github.com/DeusData/codebase-memory-mcp/releases/download/v0.6.1/codebase-memory-mcp-windows-amd64.zip` (verify with `checksums.txt`) | as above |
| PyPI install | `pip install codebase-memory-mcp==0.6.1` or `>=0.6.1` | `https://pypi.org/project/codebase-memory-mcp/` |
| Claude Code `if:` field min version | v2.1.85 | `https://code.claude.com/docs/en/hooks-guide` |
| Hook blocking semantics | exit code 2 only blocks | `https://code.claude.com/docs/en/hooks` |
| `.claude-plugin/plugin.json` schema | No `minimumClaudeCodeVersion` field; use README + runtime detect | `https://code.claude.com/docs/en/plugins-reference` |

## Open disputes — resolutions

1. **PR2 formal split**: ✅ formal — `PR2a` (frontmatter) and `PR2b` (load_project + manifest + upgrade).
2. **Dynamic arch hook FR-004 exception**: ✅ documented exception. FR-004 in spec updated (this round) to allow `_source: dotnet-ai-kit-arch` in `.claude/settings.json`. `/dai.upgrade` rewrites its filter to use handler `if:` when Claude Code v2.1.85+ detected.
3. **`.mcp.json` native min-version**: ✅ not supported — enforce via `src/dotnet_ai_kit/mcp_check.py` runtime check + sidecar `dotnet_ai_kit_min_version` metadata key.
4. **Hook scripts bash vs Python**: ✅ keep bash. `command -v bash` short-circuit already in place; Python entrypoint adds runtime burden.

## Round Tracking (plan phase)

- [x] Plan v1 drafted by Claude
- [x] Codex round 1 critique
- [x] Claude round 2 reconciliation (this version)
- [ ] Codex round 2 verification — pending (`discussion/plan-phase/codex-ready.txt`)
- [ ] Phase 0 (`research.md`) — generated after Codex `READY`
- [ ] Phase 1 (`data-model.md`, `contracts/`, `quickstart.md`) — after Phase 0
- [ ] Tasks phase (`/speckit.tasks`) — blocked until plan phases 0+1 complete
