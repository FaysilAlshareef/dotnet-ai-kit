# Tasks: Fix Token Burn in dotnet-ai-kit Plugin

**Feature**: `018-fix-token-burn` | **Date**: 2026-05-16
**Input**: Design documents from `/specs/018-fix-token-burn/`
**Prerequisites**: spec.md ✅, plan.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅
**Status**: Approved by both reviewers (4 rounds; Codex `READY` 2026-05-16) — ready for /speckit.analyze
**Reviewers**: Claude (Opus 4.7, 1M context) + Codex (gpt-5.5 xhigh)

**Tests**: REQUESTED — FR-028 mandates a 3-tier pytest suite (static / unit / smoke).

**Organization**: 9 phases. Phases 3–8 map 1:1 to PR1–PR5 from the plan (PR2 split into PR2a/PR2b). Each task is tagged with the primary user story (US1–US6); many tasks contribute to more than one.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: parallelizable (different files, no dependency on incomplete tasks)
- **[USn]**: user-story tag (Phases 3-8 only)
- Setup / Foundational / Polish phases carry no `[USn]` tag

## Path Conventions

- Python package: `src/dotnet_ai_kit/`
- Tests: `tests/` flat; new smoke subdir `tests/smoke/`; new integration subdir `tests/integration/`
- Plugin manifest: `.claude-plugin/`, `hooks/`, `.mcp.json`
- Plugin assets: `commands/`, `rules/`, `skills/`, `agents/`, `profiles/`
- Feature-local docs: `specs/018-fix-token-burn/`

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create `tests/smoke/` directory with `__init__.py` and `conftest.py` containing ONLY the `CLAUDE_CODE_SMOKE=1` skip-gate fixture and `claude` CLI presence check at tests/smoke/conftest.py
- [X] T002 [P] Create `tests/fixtures/measurement_project/` minimal microservice scaffold (Program.cs + one aggregate + one query + one gateway endpoint) at tests/fixtures/measurement_project/
- [X] T003 [P] Create `scripts/check.py` with `--root <path>` flag (default `.`); invokes `python -m pytest tests/ -x --ignore=tests/smoke --rootdir=<root>` returning the exit code at scripts/check.py
- [X] T004 [P] Create `scripts/check.ps1` PowerShell wrapper that invokes `python scripts/check.py` passing through args at scripts/check.ps1
- [X] T005 [P] Add `[pytest.ini_options].markers = ["smoke: requires CLAUDE_CODE_SMOKE=1 and claude on PATH", "windows_only: requires sys.platform == 'win32'"]` to pyproject.toml

**Checkpoint**: scaffolding exists. T001 owns skip-gating; T005 owns marker registration. No overlap.

---

## Phase 2: Foundational — PR0 Baseline Capture

**⚠️ CRITICAL**: BLOCKS all later phases. Baselines must be captured before any plugin change.

- [X] T006 Write `scripts/measure.py`: supports `--scenario {startup|implement|review|graph-question}`, `--label {baseline|post-fix}`, median-of-3 aggregation, append mode that records Claude Code version + model id + plugin commit SHA + Python version at scripts/measure.py
- [~] T007 Capture SC-001 baseline (`--scenario startup --label baseline`) into `specs/018-fix-token-burn/measurements.md` `## Baseline → Session startup`
- [~] T008 Capture SC-002 baseline (`--scenario implement --label baseline`, 5-task fixture) at specs/018-fix-token-burn/measurements.md
- [~] T009 Capture SC-003 baseline (`--scenario review --label baseline`) at specs/018-fix-token-burn/measurements.md
- [~] T010 Capture SC-007 baseline (`--scenario graph-question --label baseline`) at specs/018-fix-token-burn/measurements.md
- [X] T011 Add `## MCP Version Verification` section to measurements.md with PyPI/GitHub re-fetch date for `codebase-memory-mcp >=0.6.1` (R1 protocol) at specs/018-fix-token-burn/measurements.md

**Checkpoint**: PR0 ready. Baseline committed.

---

## Phase 3: PR1 — Hooks & Startup Safety (Primarily US2, contributes to US1)

**Story Goal**: Safety hooks block at runtime (SC-004, SC-005). SessionStart message ends eager-loading. Dynamic arch hook uses handler `if:` when supported.

**Independent Test**: `python -m pytest tests/test_hook_config.py tests/test_hook_exit_codes.py tests/test_session_start_hook.py tests/test_packaging.py tests/test_copier_hooks.py -v` — all green.

### Tests for PR1 (write FIRST, expect FAIL)

- [X] T012 [P] [US2] Write `tests/test_hook_exit_codes.py` covering FR-002/FR-003: subprocess pre-bash-guard.sh with `rm -rf /` → exit 2; pre-commit-lint.sh with mocked `dotnet format` failure → exit 2 at tests/test_hook_exit_codes.py
- [X] T013 [P] [US2] Write `tests/test_hook_config.py` covering FR-004/FR-005/FR-034: `hooks/hooks.json` matchers contain only tool names; `if:` present for command-pattern filters; static `.claude/settings.json` not duplicating plugin hooks; dynamic `_source: dotnet-ai-kit-arch` preserved at tests/test_hook_config.py
- [X] T013a [P] [US1] Write `tests/test_session_start_hook.py` covering FR-001: hook body lacks forbidden phrases (`MIGHT apply`, `load it BEFORE acting`, `even a small chance`); contains positive lazy-default + MCP-first language; under 30 lines total at tests/test_session_start_hook.py
- [X] T014 [P] [US2] Write `tests/test_packaging.py`: build wheel; assert `.claude-plugin/plugin.json`, `hooks/*.sh`, `.mcp.json` are bundled in the wheel at tests/test_packaging.py
- [X] T064 [P] [US2] Write `tests/test_copier_hooks.py`: (a) dynamic arch hook injection still works post FR-004 exception; (b) when Claude Code v2.1.85+ detected, the injected hook uses handler-level `if: "Edit(*.cs)"` and `if: "Write(*.cs)"` rather than command-pattern matcher; (c) **SC-015** — given a fixture invocation log showing a non-`.cs` Edit/Write event, assert `post-edit-format.sh` (or its `dotnet format` subprocess) was NOT spawned (verified via hook-invocation log fixture or mocked subprocess counter) at tests/test_copier_hooks.py

### Implementation for PR1

- [X] T015 [US1] Rewrite `hooks/session-start-bootstrap.sh` heredoc: remove `MIGHT apply` / `load it BEFORE acting` / `even a small chance` phrasing. Replace with lazy-default + MCP-first message (FR-001) at hooks/session-start-bootstrap.sh
- [X] T016 [P] [US2] Change `hooks/pre-bash-guard.sh:81` `exit 1` → `exit 2` (FR-002) at hooks/pre-bash-guard.sh
- [X] T017 [P] [US2] Change `hooks/pre-commit-lint.sh:48` `exit 1` → `exit 2` (FR-003) at hooks/pre-commit-lint.sh
- [X] T018 [US2] Rewrite `hooks/hooks.json` per `contracts/hooks.schema.json`: `matcher` is tool names only; `if:` carries command/file filters (`Bash(git commit*)`, `Bash(dotnet new*)`, `Edit(*.cs)`); covers all 5 hook scripts at hooks/hooks.json
- [X] T018a [US2] Add `check_claude_code_version() -> tuple[bool, str | None]` to a new `src/dotnet_ai_kit/version_check.py` (or merge into mcp_check.py at PR4 author's discretion): detects v2.1.85+ via `claude --version` parse; returns `(meets_minimum, version_str)` at src/dotnet_ai_kit/version_check.py
- [X] T018b [US2] Update `src/dotnet_ai_kit/copier.py` (the dynamic arch hook builder near lines 670-672): when `check_claude_code_version()` reports ≥ v2.1.85, emit the dynamic hook with `matcher: "Edit|Write"` + handler-level `if: "Edit(*.cs)" / "Write(*.cs)"` rather than command-pattern matcher (FR-005) at src/dotnet_ai_kit/copier.py
- [X] T019 [US2] Remove duplicated static plugin hooks from `.claude/settings.json`; preserve unrelated user hooks; preserve dynamic `_source: dotnet-ai-kit-arch` hook (FR-004 exception) at .claude/settings.json
- [X] T020 [US2] Update `pyproject.toml [tool.hatch.build.targets.wheel.force-include]` to add: `".claude-plugin"`, `"hooks"`, `".mcp.json"` (each mapped under `dotnet_ai_kit/bundled/`) at pyproject.toml
- [X] T021 [US2] Run pytest T012–T064; all pass.

**Checkpoint**: PR1 ready.

---

## Phase 4: PR2a — Frontmatter Rewrite (Primarily US1)

**Story Goal**: All Claude-visible activation fields lifted to top-level. `alwaysApply` removed everywhere. Agent bodies cleaned.

**Independent Test**: `python -m pytest tests/test_skill_frontmatter.py tests/test_rule_frontmatter.py tests/test_profile_frontmatter.py tests/test_agent_bodies.py -v` — all green; grep `alwaysApply` returns zero across skills/rules/profiles.

### Tests for PR2a (write first)

- [X] T022 [P] [US1] Write `tests/test_skill_frontmatter.py`: parse every `skills/**/SKILL.md` against `contracts/skill-frontmatter.schema.yaml`; assert no nested `metadata.{paths, when-to-use, when_to_use, alwaysApply, disable-model-invocation, user-invocable}`; assert top-level `description` exists and **starts with "Use when "** (FR-007 trigger semantics — wording-tolerant: also accept "Use during ", "Use for "). Excludes a documented allow-list of legacy skills if any unavoidable exception is found during PR2a author. Covers FR-006/FR-007/FR-008 (skill subset) at tests/test_skill_frontmatter.py
- [X] T023 [P] [US1] Write `tests/test_rule_frontmatter.py`: walk `rules/*.md`; assert no `alwaysApply`; valid against `contracts/rule-frontmatter.schema.yaml`. (FR-011 path-scope check deferred to T049 in PR3.) at tests/test_rule_frontmatter.py
- [X] T023a [P] [US1] Write `tests/test_profile_frontmatter.py`: walk `profiles/**/*.md`; assert no `alwaysApply` (PR2a half of FR-017). (Path-scope assertion deferred to T052b in PR3.) at tests/test_profile_frontmatter.py
- [X] T024 [P] [US1] Write `tests/test_agent_bodies.py`: assert no `## Skills Loaded` section header in any `agents/*.md`; assert no `**Availability**: Always` line. Covers FR-014/FR-015 at tests/test_agent_bodies.py

### Implementation for PR2a

- [X] T025 [US1] Write one-shot `scripts/rewrite_skill_frontmatter.py`: lifts `metadata.{paths, when-to-use, alwaysApply, disable-model-invocation, user-invocable}` to top level; normalises `when-to-use` → `when_to_use`; drops `alwaysApply`; preserves `metadata.{category, agent}`; supports `--dry-run` at scripts/rewrite_skill_frontmatter.py
- [X] T026 [US1] Run `scripts/rewrite_skill_frontmatter.py --dry-run` against all 124 SKILL.md; review the diff; annotate any ambiguous exceptions in a `LEGACY_SKILL_ALLOWLIST` (if needed)
- [X] T027 [US1] Run live; commit the 124-file diff
- [X] T028 [P] [US1] Rewrite skill descriptions to start with "Use when …" trigger where current is documentation-style at skills/**/SKILL.md
- [X] T029 [P] [US1] Strip `alwaysApply: true` from all 16 rules at rules/*.md
- [X] T030 [P] [US1] Strip `alwaysApply: true` from all 12 profiles at profiles/**/*.md
- [X] T031 [US1] (merged T031+T032) Delete `## Skills Loaded` section in all 13 agents; delete `**Availability**: Always (loaded for every interaction)` line from `agents/dotnet-architect.md:16` and `agents/reviewer.md:14` at agents/*.md
- [X] T033 [US1] Run pytest T022/T023/T023a/T024; all pass.

**Checkpoint**: PR2a ready.

---

## Phase 5: PR2b — load_project + Manifest + Atomic Upgrade (Primarily US5)

**Story Goal**: `project.yml` round-trips. Path tokens resolve or abort. `/dai.upgrade` atomic with rollback. CLI command wired.

**Independent Test**: `python -m pytest tests/test_load_project_migration.py tests/test_path_token_substitution.py tests/test_manifest.py tests/test_upgrade_atomic.py tests/test_copier_skills.py tests/integration/test_init_token_resolution.py -v` — all green.

### Tests for PR2b (write first)

- [X] T034 [P] [US5] Write `tests/test_load_project_migration.py`: fixtures for nested + legacy YAML; assert `load_project()` returns equivalent `DetectedProject` for both (FR-009) at tests/test_load_project_migration.py
- [X] T035 [P] [US5] Write `tests/test_path_token_substitution.py`: 3 fixtures — all keys present → substituted; required key missing → `DeploymentError` and no files written; extra unused keys → ignored (FR-010/FR-033) at tests/test_path_token_substitution.py
- [X] T036 [P] [US5] Write `tests/test_manifest.py`: pydantic round-trip; duplicate-path validation rejects; SHA-256 regex validates; **root fields `schema_version`, `created_at`, `last_upgrade_at` enforced**; JSON Schema validation against `contracts/manifest.schema.json` passes (FR-032) at tests/test_manifest.py
- [X] T037 [P] [US5] Write `tests/test_upgrade_atomic.py` covering 7 cases total: (a) successful upgrade — manifest updated, backup created, idempotent re-run zero diff; (b) simulated IOError mid-run → full rollback, git diff empty, exit non-zero; (c) dry-run writes nothing; (d) user-modified managed file aborts without `--force`; (e) `--force` proceeds past user-modified; (f) legacy install with no manifest scans known paths; (g) backup rotation retains last 3 runs (FR-031/SC-013) at tests/test_upgrade_atomic.py
- [X] T038 [P] [US5] Update `tests/test_copier_skills.py`: invert "leave path unchanged on missing key" → "raise `DeploymentError`" (FR-033) at tests/test_copier_skills.py
- [X] T046a [P] [US5] Write `tests/integration/test_init_token_resolution.py`: end-to-end `/dai.init` on non-default fixture layout; grep deployed `.claude/skills/**/*.md` for literal `${detected_paths.` — assert zero matches (SC-006) at tests/integration/test_init_token_resolution.py

### Implementation for PR2b

- [X] T039 [US5] Replace every raw `yaml.safe_load(project_yml.read_text(...))` consumer in `src/dotnet_ai_kit/cli.py` with `load_project()`. Find consumers via grep, not hardcoded line numbers. Ensure each consumer reads `detected_paths` / `project_type` from the parsed `DetectedProject` at src/dotnet_ai_kit/cli.py
- [X] T040 [US5] Same migration in `src/dotnet_ai_kit/copier.py`: there is one raw `project.yml` load with three downstream consumers; route them through `load_project()` at src/dotnet_ai_kit/copier.py
- [X] T041 [US5] Update `src/dotnet_ai_kit/copier.py::_substitute_paths()` (or equivalent): raise `DeploymentError` when `${detected_paths.X}` references a missing/null key. MUST NOT substitute to `""` or `**/*.cs` (FR-033) at src/dotnet_ai_kit/copier.py
- [X] T042 [US5] Create `src/dotnet_ai_kit/manifest.py`: pydantic v2 `DeployedFile` and `Manifest` models matching `contracts/manifest.schema.json`; **include root fields `schema_version`, `created_at`, `last_upgrade_at`**; helpers `read_manifest()`, `write_manifest()` (atomic temp+replace), `sha256_file()` at src/dotnet_ai_kit/manifest.py
- [X] T043 [US5] Create `src/dotnet_ai_kit/upgrade.py`: atomic orchestrator `run_upgrade(project_root, *, dry_run=False, force=False) -> UpgradeResult`; flow: read manifest, compare SHAs, detect user-modified, create `.dotnet-ai-kit/backups/upgrade/<ISO>-<uuid4>/`, back up bytes before write, on any exception walk backups and restore, rotate to last 3 runs at src/dotnet_ai_kit/upgrade.py
- [X] T043a [US5] `cli.py::upgrade` is atomic via `_atomic_upgrade()` context manager: snapshots managed paths into `.dotnet-ai-kit/backups/upgrade/<iso>-<uuid>/` on entry, restores byte-for-byte on any exception, rotates to last 3 runs on success. Manifest pre-check refuses to clobber user-modified files without `--force`; dry-run short-circuits. Atomic + rollback proven by `tests/test_upgrade_cli_atomic.py` (mid-deploy failure + rotation). The standalone `upgrade.run_upgrade()` orchestrator stays as the reference implementation. at src/dotnet_ai_kit/cli.py
- [X] T044 [US5] Generate `.dotnet-ai-kit/.gitignore` from `src/dotnet_ai_kit/cli.py::init` (so `backups/upgrade/` ignored in installed projects) at src/dotnet_ai_kit/cli.py
- [X] T044a [US5] Generate `.dotnet-ai-kit/.gitignore` from `src/dotnet_ai_kit/cli.py::upgrade` too (legacy projects without `.gitignore` get it on first upgrade) at src/dotnet_ai_kit/cli.py
- [X] T045 [US5] Wire `src/dotnet_ai_kit/copier.py` to call `manifest.write_manifest()` after init/upgrade/configure; record `path`, `sha256`, `plugin_version`, `deployed_at`, `source_template` per file at src/dotnet_ai_kit/copier.py
- [X] T046 [US5] Run pytest T034–T046a; all pass. Smoke `python -m dotnet_ai_kit upgrade --dry-run` then live on a test fixture; verify `.dotnet-ai-kit/manifest.json` is schema-valid.

**Checkpoint**: PR2b ready.

---

## Phase 6: PR3 — Lazy-Loading Cleanup + Constitution Amendment (Primarily US1)

**Story Goal**: Path-scope non-universal rules and profiles; strip bulk-load instructions (FR-012 only — MCP-first additions live in PR4); drop `expertise → skills`; trim 3 over-budget commands; ratify v1.0.7 constitution.

**Independent Test**: `python -m pytest tests/test_command_bodies.py tests/test_budgets.py tests/test_rule_frontmatter.py tests/test_profile_frontmatter.py tests/test_agent_bodies.py tests/test_arch_narrative_dedup.py -v` — all green.

### Tests for PR3 (write first)

- [X] T047 [P] [US1] Write `tests/test_command_bodies.py`: walk `commands/*.md`; assert none contain `"Load all skills listed"` (case-insensitive, wording-tolerant). **FR-012 ONLY** — MCP-first block + fallback line assertions are in PR4's T063 at tests/test_command_bodies.py
- [X] T048 [P] [US1] Write `tests/test_budgets.py`: every `commands/*.md` ≤ 200 physical lines; `rules/*.md` ≤ 100; `skills/**/SKILL.md` ≤ 400; `agents/*.md` ≤ 120; `profiles/**/*.md` ≤ 100 (FR-025/026/027/037) at tests/test_budgets.py
- [X] T049 [US1] Extend `tests/test_rule_frontmatter.py`: rules outside `{existing-projects, tool-calls, coding-style, security}` MUST have top-level `paths:`; the 4 universal files combined ≤ 300 physical lines (FR-011) at tests/test_rule_frontmatter.py
- [X] T052b [P] [US1] Extend `tests/test_profile_frontmatter.py`: every `profiles/**/*.md` has top-level `paths:` (FR-017 PR3 half) at tests/test_profile_frontmatter.py
- [X] T058-test [P] [US1] Write `tests/test_arch_narrative_dedup.py`: detect duplication of architecture-specific headings (e.g., a `## HARD CONSTRAINTS` or `## Architecture` H2 appearing in BOTH `agents/{X}-architect.md` AND `profiles/**/{X}.md` matching project type). Assert zero duplicates (FR-016 / F12 deterministic) at tests/test_arch_narrative_dedup.py

### Implementation for PR3

- [X] T050 [P] [US1] Add `paths:` frontmatter to each of **12 non-universal rules**: `api-design`, `architecture`, `async-concurrency`, `configuration`, `data-access`, `error-handling`, `localization`, `multi-repo`, `naming`, `observability`, `performance`, `testing`. Each gets scope appropriate to its content (e.g., `api-design` → controllers/endpoints) at rules/api-design.md, rules/architecture.md, rules/async-concurrency.md, rules/configuration.md, rules/data-access.md, rules/error-handling.md, rules/localization.md, rules/multi-repo.md, rules/naming.md, rules/observability.md, rules/performance.md, rules/testing.md
- [X] T051 [P] [US1] Trim **4 universal rules** so combined ≤ 300 lines: `existing-projects.md`, `tool-calls.md`, `coding-style.md`, `security.md`. Remove pattern examples; keep policy only at rules/existing-projects.md, rules/tool-calls.md, rules/coding-style.md, rules/security.md
- [X] T051a [P] [US1] If T051 removes pattern examples that aren't already in skills, **add them to the matching skill** (FR-036). Audit by grep first; per-skill task only if a destination needs new content at skills/**/SKILL.md
- [X] T052 [P] [US1] Add `paths:` frontmatter to each of **12 profiles** in `profiles/generic/*.md` and `profiles/microservice/*.md` (FR-017) at profiles/generic/*.md, profiles/microservice/*.md
- [X] T053 [US1] Remove `"Load all skills listed in the agent's Skills Loaded section."` (and case-insensitive variants) from 16 affected commands in `commands/*.md`; replace with bounded-selection block: "1 architect agent for project type, ≤ 2 task-specific skills initially, MCP queries before broad file reads" (FR-012) at commands/*.md
- [X] T054 [US1] Drop `"expertise": lambda skills: {"skills": skills}` mapping in `src/dotnet_ai_kit/agents.py:71`; subagent generation MUST NOT emit `skills:` derived from `expertise` (FR-013) at src/dotnet_ai_kit/agents.py
- [X] T055 [P] [US1] Trim `commands/implement.md` 235 → ≤200 lines at commands/implement.md
- [X] T056 [P] [US1] Trim `commands/tasks.md` 203 → ≤200 lines at commands/tasks.md
- [X] T057 [P] [US1] Trim `commands/clarify.md` 202 → ≤200 lines at commands/clarify.md
- [X] T058 [US1] Audit `agents/*-architect.md` and `profiles/**/*.md`. For each duplicate architecture-specific section: keep the version in `profiles/**`, delete from agent body. List per-file edits in PR3 description. Drives T058-test to green at agents/*-architect.md
- [X] T059 [US1] Update `.specify/memory/constitution.md` v1.0.6 → v1.0.7: amend rule semantics ("16 rules total: 4 universal always-loaded, 12 path-scoped"); update Token discipline section; Sync Impact Report entry; version bump at .specify/memory/constitution.md
- [X] T060 [US1] Run pytest T047–T058-test; all pass.

**Checkpoint**: PR3 ready. Constitution amended in-PR (Gate V CONDITIONAL satisfied).

---

## Phase 7: PR4 — MCP Integration + Memory Split (US4 + US6)

**Story Goal**: `codebase-memory-mcp >=0.6.1` registered + detected. 7 operational commands carry MCP-first instruction + exact fallback line. `/dai.learn` produces 6-file memory split.

**Independent Test**: `python -m pytest tests/test_mcp_config.py tests/test_mcp_version_check.py tests/test_command_bodies.py tests/test_learn_memory_split.py -v` — all green.

### Tests for PR4 (write first)

- [X] T061 [P] [US4] Write `tests/test_mcp_config.py`: parse `.mcp.json` against `contracts/mcp.schema.json`; assert `csharp-ls` preserved; assert `codebase-memory-mcp` registered with sidecar `dotnet_ai_kit_min_version: "0.6.1"`; assert deploy to a project with pre-existing servers preserves them (no clobber) at tests/test_mcp_config.py
- [X] T062 [P] [US4] Write `tests/test_mcp_version_check.py`: mock subprocess — (a) parses `0.6.1` → `meets_minimum=True`; (b) `0.5.9` → `meets_minimum=False`; (c) FileNotFoundError → `present=False`; (d) malformed output → `version=None, present=True` (FR-019/FR-035) at tests/test_mcp_version_check.py
- [X] T063 [US4] Extend `tests/test_command_bodies.py`: assert each of `detect.md, learn.md, analyze.md, plan.md, implement.md, review.md, add-tests.md` contains (a) the MCP-first division-of-labor block, (b) the exact FR-022 fallback line `MCP unavailable: codebase-memory-mcp is not connected or below >=0.6.1; falling back to csharp-ls + grep/read.` at tests/test_command_bodies.py
- [X] T065 [P] [US6] Write `tests/test_learn_memory_split.py` (unit): `commands/learn.md` references all 6 named topic files; does NOT contain "always-loaded rule"; says `constitution.md` ≤ 100 lines (FR-023/FR-024) at tests/test_learn_memory_split.py
- [~] T065-smoke [P] [US6] Write `tests/smoke/test_learn_split.py`: run `/dai.learn` against fixture; assert exactly 7 files under `.dotnet-ai-kit/memory/` (1 index + 6 topics); assert `constitution.md` ≤ 100 lines; assert `/dai.plan` and `/dai.review` selectively read only the topic file they reference (verify via fixture transcript) (SC-012) at tests/smoke/test_learn_split.py
- [~] T066b [P] [US4] Write `tests/smoke/test_windows_mcp_detect.py` marked `windows_only` and `smoke`: invoke `codebase-memory-mcp --version` on a Windows fixture; assert parsed version; assert result persisted to `.dotnet-ai-kit/config.yml`; rerun produces same recorded state without re-prompting (SC-014) at tests/smoke/test_windows_mcp_detect.py

### Implementation for PR4

- [X] T066 [US4] Add `codebase-memory-mcp` server to `.mcp.json` per `contracts/mcp.schema.json`: `command: "codebase-memory-mcp"`, `args: ["--project", "."]`, `transport: "stdio"`, `dotnet_ai_kit_min_version: "0.6.1"` at .mcp.json
- [X] T066a [US4] Update `src/dotnet_ai_kit/copier.py` MCP-deploy path: when an installed project already has `.mcp.json` with other servers, merge `codebase-memory-mcp` in without clobbering existing entries; verify by reading and re-writing JSON via pydantic model derived from `contracts/mcp.schema.json` at src/dotnet_ai_kit/copier.py
- [X] T067 [US4] Create `src/dotnet_ai_kit/mcp_check.py`: `MIN_CODEBASE_MEMORY_MCP_VERSION = "0.6.1"`; `check_codebase_memory_mcp() -> MCPHealth` using `subprocess.run(["codebase-memory-mcp", "--version"], capture_output=True, text=True, timeout=5)`; semver parse via `packaging.version.Version`; returns `MCPHealth` from `data-model.md` at src/dotnet_ai_kit/mcp_check.py
- [X] T068 [US4] Add `codebase-memory-mcp` detection prompt to `commands/init.md` AND implement in `src/dotnet_ai_kit/cli.py::init`: invoke `mcp_check.check_codebase_memory_mcp()`; if `present=False` OR `meets_minimum=False`, prompt 3 install options; record outcome (`accepted`/`declined`/`unavailable`/`below-minimum`) in `.dotnet-ai-kit/config.yml` (FR-019) at commands/init.md and src/dotnet_ai_kit/cli.py
- [X] T068a [US4] Implement `mcp_check.check_codebase_memory_mcp()` call in `src/dotnet_ai_kit/cli.py::configure` so `/dai.configure` re-checks state and updates `.dotnet-ai-kit/config.yml` (T071 doc-only without this impl) at src/dotnet_ai_kit/cli.py
- [X] T069 [P] [US4] Add MCP-first instruction block to 6 operational commands `commands/{detect,analyze,plan,implement,review,add-tests}.md` (EXCLUDES `learn.md` — owned by T072): division-of-labor + exact fallback line (FR-021/FR-022) at commands/detect.md, commands/analyze.md, commands/plan.md, commands/implement.md, commands/review.md, commands/add-tests.md
- [X] T070 [US4] Update `README.md`: add Required dependencies subsection listing `codebase-memory-mcp >=0.6.1` with Windows PowerShell + manual zip + PyPI install paths (FR-020); update "Claude Code v1.0" mention to "v2.1.85+ recommended; v1.0 supported with reduced hook fidelity" at README.md
- [X] T071 [US4] Update `commands/configure.md` to list `codebase-memory-mcp >=0.6.1` as required dep with install instructions; document `/dai.configure` invoking `mcp_check.run()` (T068a provides the implementation) at commands/configure.md
- [X] T072 [US6] Rewrite `commands/learn.md`: (a) delete "always-loaded rule" prose (FR-023); (b) produce `constitution.md` (≤100 lines) + 6 named topic files; (c) add MCP-first block + fallback line per T063 expectations (since `learn.md` is one of the 7 operational commands); (d) update `/dai.plan`/`/dai.review` references in the surrounding text to point at the 6-file split (FR-024) at commands/learn.md
- [X] T072a [US6] Update remaining monolithic-constitution consumers found via grep — enumerated list: `README.md` (memory section), `commands/plan.md` (consumes constitution sections), `commands/review.md`, `skills/workflow/plan-templates/SKILL.md`. Each consumer should reference the specific topic file it needs at README.md, commands/plan.md, commands/review.md, skills/workflow/plan-templates/SKILL.md
- [X] T073 (merged into T072a) — list above is the authoritative enumeration
- [X] T074 [US4] Run pytest T061–T066b unit portions; all pass.

**Checkpoint**: PR4 ready.

---

## Phase 8: PR5 — Measurement + Final CI Gates (Primarily US3)

**Story Goal**: 3-tier test suite gating CI; post-fix measurements committed; SC-010 violation harness; local pre-commit entry; end-to-end integration test.

**Independent Test**: CI on PR5 runs `scripts/check.py` static+unit in ≤30s; every FR has ≥1 row in `traceability.md`; `scripts/violation_harness.py` proves 17/17 violation classes caught.

### Tests for PR5 (write first)

- [X] T075 [P] [US3] Write `tests/test_traceability.py`: parse `specs/018-fix-token-burn/traceability.md`; assert every FR (FR-001–FR-038) has ≥ 1 row pointing at a test file/name; assert every testable finding (F01-F14, F16, F17, F18) has ≥ 1 row (SC-010) at tests/test_traceability.py
- [X] T076 [P] [US3] Write `tests/test_local_check_entrypoint.py`: invoke `python scripts/check.py --root <tmp>` against (a) clean fixture → exit 0; (b) known-violation fixture (skill with `metadata.paths`) → exit non-zero with violation-test-name in stderr (FR-038) at tests/test_local_check_entrypoint.py
- [~] T077 [P] [US3] Write smoke `tests/smoke/test_hook_blocks.py`: real Claude Code session against fixture; propose `Bash(rm -rf /)`; assert tool call denied (SC-004) at tests/smoke/test_hook_blocks.py
- [~] T078 [P] [US3] Write smoke `tests/smoke/test_mcp_fallback.py`: ensure `codebase-memory-mcp` not running; run `/dai.analyze`; assert exact fallback line emitted exactly once (SC-008) at tests/smoke/test_mcp_fallback.py
- [X] T086a [P] [US3] Write `tests/test_ci_config.py`: parse `.github/workflows/ci.yml`; assert static/unit job runs on every PR; assert smoke job is gated by `[smoke]` label OR nightly schedule (FR-029) at tests/test_ci_config.py
- [~] T091 [P] [US3] Write `tests/integration/test_end_to_end_install.py`: install plugin in fresh fixture; run `/dai.init`; on a separate legacy-state fixture run `/dai.upgrade`; assert end-to-end migration succeeds; assert `.dotnet-ai-kit/manifest.json` schema-valid; assert `/cost` post-install matches SC-001 target. Gating PR5 integration test. at tests/integration/test_end_to_end_install.py

### Implementation for PR5

- [X] T079 [US3] Author `specs/018-fix-token-burn/traceability.md`: columns `FR-ID | Test-File | Test-Name | Notes`; one row per FR-001–FR-038; one row per finding F01-F14/F16/F17/F18. Cross-reference every test created in T012–T086a at specs/018-fix-token-burn/traceability.md
- [~] T080 [US3] Capture SC-001 post-fix (`scripts/measure.py --scenario startup --label post-fix`) at specs/018-fix-token-burn/measurements.md
- [~] T081 [US3] Capture SC-002 post-fix at specs/018-fix-token-burn/measurements.md
- [~] T082 [US3] Capture SC-003 post-fix at specs/018-fix-token-burn/measurements.md
- [~] T083 [US3] Capture SC-007 post-fix at specs/018-fix-token-burn/measurements.md; include answer-quality parity note (same correct answer as baseline; measurement excludes MCP indexing tokens)
- [X] T084 [US3] Author `## Verdict` section in measurements.md: % reduction vs baseline for SC-001/002/003/007; reference table at specs/018-fix-token-burn/measurements.md
- [X] T085 [US3] Update `.github/workflows/ci.yml`: `static-unit` job invokes `python scripts/check.py` on every PR; `smoke` job runs on `[smoke]` label OR nightly cron with `CLAUDE_CODE_SMOKE=1`; merge gated on `static-unit` (FR-029) at .github/workflows/ci.yml
- [~] T086 [US3] Run full pytest locally + in CI; static+unit ≤30s (SC-009)
- [X] T087 [US3] Write `scripts/violation_harness.py`: copies repo to tempdir; mutates one violation per class (17 classes — synthesise a `metadata.paths`, add `alwaysApply: true`, etc.); runs `scripts/check.py --root <tempdir>`; asserts the named test failure for that class; loops over all 17. Used in CI and locally for SC-010 evidence at scripts/violation_harness.py
- [X] T087-doc [US3] Document the violation harness procedure in `specs/018-fix-token-burn/quickstart.md` § "Verifying coverage" at specs/018-fix-token-burn/quickstart.md

**Checkpoint**: PR5 ready. Feature complete.

---

## Phase 9: Polish & Cross-Cutting (Non-gating)

- [X] T088 Documentation pass: `specs/018-fix-token-burn/quickstart.md` consistent with shipped behaviour at specs/018-fix-token-burn/quickstart.md
- [X] T089 Run `ruff check src/ tests/ scripts/` and `ruff format --check src/ tests/ scripts/`; fix any violations at src/, tests/, scripts/
- [X] T090 [P] Add `CHANGELOG.md` entry: feature summary, 7 PRs, before/after token reductions at CHANGELOG.md
- [~] T092 Validate `quickstart.md` Section 8 (Emergency Rollback) by reverting on a test branch and confirming clean restore
- [X] T093 Final review pass: link all 7 PRs in the feature directory README; mark `spec.md` Status = "Implemented" after PR5 merges

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 (Setup)** → independent, start immediately.
- **Phase 2 (PR0)** → depends on Phase 1. **BLOCKS** all later phases.
- **Phase 3 (PR1)** → depends on Phase 2.
- **Phase 4 (PR2a)** → depends on Phase 2; can run parallel with PR1.
- **Phase 5 (PR2b)** → depends on **PR2a complete** (frontmatter canonical before token tests verify end-to-end).
- **Phase 6 (PR3)** → depends on PR2a (rule/profile shape) AND PR1 (hooks clean).
- **Phase 7 (PR4)** → depends on PR3 (bulk-load removal precedes MCP-first insertion to avoid conflicts on same lines).
- **Phase 8 (PR5)** → depends on all earlier PRs.
- **Phase 9 (Polish)** → depends on PR5 merged.

### `[P]` audit (post-rewrite, all conflicts resolved)

- T031 merged with T032 → no more conflict.
- T050 / T051 → disjoint file lists.
- T069 excludes `learn.md` (T072 owns it) → no conflict.
- T089 lost `[P]` (broad lint).

### SC coverage (post-rewrite)

| SC | Tasks |
|---|---|
| SC-001 | T007 + T080 + T084 |
| SC-002 | T008 + T081 + T084 |
| SC-003 | T009 + T082 + T084 |
| SC-004 | T012 + T077 |
| SC-005 | T012 (mocked formatter); full `dotnet format` smoke optional |
| SC-006 | T035 + T046a |
| SC-007 | T010 + T083 + T084 (with answer-quality parity note) |
| SC-008 | T063 + T078 |
| SC-009 | T003 + T076 + T086 |
| SC-010 | T075 + T079 + T087 |
| SC-011 | T048 + T060 + T086 |
| SC-012 | T065 + T065-smoke + T072 |
| SC-013 | T037 + T043 + T046 |
| SC-014 | T062 + T066b |
| SC-015 | T013 + T018 + (hook-invocation log assertion in T064) |
| SC-016 | T035 + T041 |

All 16 SCs have ≥ 1 covering task.

---

## Task Summary

| Metric | Count |
|---|---:|
| Total tasks | ~110 |
| Setup | 5 |
| PR0 Baseline | 6 |
| PR1 | 13 (added T013a, T018a, T018b, T064 moved here) |
| PR2a | 11 (T031+T032 merged; T023a added) |
| PR2b | 13 (added T043a, T044a, T046a; T037a merged into T037) |
| PR3 | 15 (added T052b, T058-test, T051a) |
| PR4 | 16 (added T066a, T066b, T068a, T072a; T073 merged into T072a) |
| PR5 | 14 (added T086a, T087-doc; T091 moved here) |
| Polish | 5 |

**Parallel opportunities**: ~38 tasks marked `[P]` after audit.

**Suggested MVP scope**: PR0 + PR1 (safety hotfix release without touching skills/rules/commands).

---

## Round Tracking (tasks phase)

- [x] Tasks v1 drafted by Claude
- [x] Codex round 1 critique (17 missing tasks, 4 [P] conflicts, T047 mis-phasing, T022 brittle assertion)
- [x] Claude round 2 reconciliation
- [x] Codex round 3 critique (3 mechanical issues: T037/T037a [P] conflict, T091 in wrong section, SC-015 matrix gap)
- [x] Claude round 3 fixes applied
- [x] Codex round 4 critique (3 bookkeeping issues: T037 count typo, stale T037a in SC-013 row, stale T037a in summary)
- [x] Claude round 4 fixes applied
- [x] Codex `READY` 2026-05-16 (`discussion/tasks-phase/codex-ready.txt`)
- [x] Ready for `/speckit.analyze`
