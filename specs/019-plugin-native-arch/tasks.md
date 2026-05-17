# Tasks: Plugin-Native Architecture

**Branch**: `019-plugin-native-arch`
**Feature**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md) — 16-commit map (original 15 commits frozen in FINAL-REPORT.md:87-106 plus tasks-phase commit 14b for `render`; final sequence `1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14b, 15`)
**Status**: Draft v1 — pending tasks-phase cross-AI sign-off
**Reviewers**: Claude (Opus 4.7, 1M context) + Codex (gpt-5.5 xhigh)

## Format: `[TaskID] [P?] [Story?] (commit N) Description with file path`

- **[P]**: parallelizable — independent file, no dependency on incomplete tasks in same phase
- **[Story]**: maps to a spec.md user story (US1..US6); Setup / Foundational / Polish phases have no story label
- **(commit N)**: maps to plan.md commit number; preserves the 16-commit order (original 15 architecture-phase commits plus tasks-phase commit 14b for `render`) across the user-story regrouping
- **TDD**: per plan-mandated TDD discipline, each commit's failing tests are written first; test tasks precede their implementation tasks within each commit-bound block
- **Paths**: repo-root relative; absolute paths only when crossing repo boundaries

## Source-of-truth references

- `specs/019-plugin-native-arch/plan.md` § "Commit-by-Commit Implementation Map" (lines 360-497) — commit content
- `specs/019-plugin-native-arch/traceability.md` — FR/SC/A/CHK → test mapping (no test invented that's not in this inventory)
- `specs/019-plugin-native-arch/data-model.md` — entity field shapes
- `specs/019-plugin-native-arch/contracts/` — 18 contracts (7 schemas + 11 markdown contracts)
- `specs/019-plugin-native-arch/checklists/verification.md` — CHK001..CHK063
- `specs/019-plugin-native-arch/discussion/plan-phase/round4-codex-final.md` — AGREED-CLEAN-SIGN-OFF from plan phase

## Commit Execution Order (BINDING — overrides phase numbering for execution)

Per `plan.md` "single feature branch, 16 sequenced commits", code MUST land in this commit-sequential order on `019-plugin-native-arch` regardless of which user-story phase a task lives in. User-story phases (Phase 3..Phase 9) are organized by spec.md US-priority for readability; **execution follows commits, not phases**:

| Commit | Phase | User stories touched | Task ID range |
|--|--|--|--|
| 1 | Phase 1 Setup | (foundation for all US) | T001-T005 |
| 2 | Phase 2 Foundational | (foundation) | T006-T010 |
| 3 | Phase 2 Foundational | (foundation) | T011-T019 |
| 8 | Phase 2 Foundational | (foundation) | T020-T027 |
| (Foundational cross-cut) | Phase 2 | (foundation) | T028 |
| 4 | Phase 3 US1 | US1 | T029-T043 (includes T041a) |
| 5 | Phase 3 US1 | US1 | T044-T050 |
| 6 | Phase 3 US1 | US1 | T051-T061 |
| 7 | Phase 4 US2 | US2 | T062-T072c (includes T072a/T072b) |
| 9 | Phase 7 US5 | US5 (`check` half only — render moved to commit 14b) | T101-T109 (includes T108a) |
| 10 | Phase 6 US4 | US4 | T092-T100 (includes T099a) |
| 11 | Phase 7 US5 | US5 | T110-T111 |
| 12 | Phase 7 US5 | US5 (gated on commit 11 CI green) | T112-T114 |
| 13 | Phase 5 US3 | US3 | T073-T080 |
| 14 | Phase 5 US3 | US3 | T081-T091 |
| **14b** | **Phase 8 US6** | **US6 (NEW commit — added during tasks-phase round 1)** | **T115-T118** |
| 15 | Phase 9 Polish | (cross-cutting) | T119-T130 (includes T125a) |

**Reading rule**: ignore the phase-numbering implication that all P1 stories complete before P2 stories. The execution order is commit-sequential. Within a single commit, tasks land in the order shown in this file (tests precede implementation per TDD).

## Hard inter-commit gates (cannot be reordered)

1. **Commit 11 → Commit 12**: csharp-lsp dependency MUST land + CHK009/CHK010/CHK011 MUST be green in CI before csharp-ls is removed from `.mcp.json`. Tasks **T110 (smoke transcript) + T111 (dep added)** in commit 11 must precede **T112 (contract test) + T113 (CI-gated check) + T114 (.mcp.json edit)** in commit 12.
2. **Commit 14 PASS-CONDITIONAL**: `tests/unit/test_constitution_amendment.py` MUST PASS before the rule-reclassification step lands. Strict order within commit 14: **T081 (write test, FAILS) → T082 (amend constitution.md v1.0.7 → v1.0.8) → T083 (test PASSES) → T084+ (rule moves)**.
3. **Commit 6 Cursor spike outcome**: If `tests/integration/test_smoke_cursor.py` (T051) fails in CI, **T061** triggers the code/spec/schema/package side of the 7-step revision per `contracts/cursor-fixture-decision.contract.md:37-50`. The release-notes side is **T125 in commit 15** (cannot be done in commit 6 because the release-notes file is created in commit 15). T053 enforces the consistency invariant via the two fixture sets `tests/fixtures/cursor_fixture_{pass,fail}/`, NOT against the live release-notes file.
4. **Commit ordering 1→16 must be preserved per merge**: per `plan.md` updated section, the 16-commit order is `1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14b, 15` (commit 14b added during tasks-phase round 1 to close the orphan render-command gap). The user-story regrouping below is for task readability — execution MUST follow the commit-sequential order. See **Commit Execution Order** section below for the binding sequence.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Multi-host config foundation that every later commit depends on. Maps to **commit 1** in plan.md.

- [X] T001 [P] (commit 1) Update `tests/test_agents.py` (existing file, line 31-33 asserts `frozenset({"claude"})` today, line 21-28 asserts `AGENT_CONFIG["claude"]`) — change the v1-only assertion to multi-host `frozenset({"claude", "codex", "cursor", "copilot"})`, add per-host AGENT_CONFIG assertions for `codex`, `cursor`, `copilot`, AND keep the existing Claude assertions (test must FAIL first per TDD against the current single-host frozenset)
- [X] T002 (commit 1) Expand `SUPPORTED_AI_TOOLS` in `src/dotnet_ai_kit/agents.py:57` from `frozenset({"claude"})` to `frozenset({"claude", "codex", "cursor", "copilot"})` — makes T001 PASS
- [X] T003 [P] (commit 1) Add multi-host pydantic models in `src/dotnet_ai_kit/models.py` per `data-model.md` § 3 `UserConfig`: `enabled_hosts: list[Literal["claude","codex","cursor","copilot"]]`, `retention: int = 3`, `permission_profile: Literal["minimal","standard","full","mcp"] | None`, `plugin_version: str`
- [X] T004 [P] (commit 1) Update `src/dotnet_ai_kit/config.py` reader to accept legacy `ai_tools` field name and map it to `enabled_hosts` on read (per `data-model.md` § 3 alias note); writer always emits `enabled_hosts`
- [X] T005 [P] (commit 1) Add `tests/contract/test_config_yml_schema.py` asserting pydantic-derived JSON Schema for `UserConfig` validates the 4-host enum and the `ai_tools` alias migration (legacy `ai_tools: ["claude"]` reads identically to `enabled_hosts: ["claude"]`)

**Checkpoint**: `SUPPORTED_AI_TOOLS` is 4-host; `UserConfig` model accepts both legacy `ai_tools` and new `enabled_hosts`; ready for Foundational.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Cross-platform packaging, plugin manifests, project metadata schema, and the no-network static assertion. Maps to **commits 2, 3, 8** in plan.md.

**CRITICAL**: No user-story phase work begins until this phase completes.

### Commit 2 — Packaging (`pyproject.toml`)

- [X] T006 [P] (commit 2) Extend the existing `tests/test_packaging.py` (currently asserts `bundled/.claude-plugin/plugin.json` + hooks) with parameterized assertions for `.codex-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `agents-source/`, `agents-claude/`, `agents/` (Cursor build output), `agents-copilot-templates/`, `rules/conventions/`, `rules/domain/`, `rules/cursor/`, and `schemas/`; tests FAIL first per TDD until T009 lands
- [X] T007 [P] (commit 2) Add `tests/integration/test_packaging_macos.py` re-running the T006 wheel-content assertions inside the macOS CI matrix (validates POSIX path normalization)
- [X] T008 [P] (commit 2) Add `tests/integration/test_packaging_windows.py` re-running T006's wheel-content assertions inside the Windows CI matrix (validates Windows path-separator handling per A-010); platform-specific assertions only — does NOT duplicate cross-platform logic from T006
- [X] T009 (commit 2) Update `pyproject.toml` `[tool.hatch.build.targets.wheel.force-include]` to add `.codex-plugin/`, `.cursor-plugin/`, `agents-source/`, `agents-claude/`, `agents/`, `agents-copilot-templates/`, `rules/conventions/`, `rules/domain/`, `rules/cursor/`, `schemas/` (per plan.md:375; `.claude-plugin/` and `hooks/` already included from feature 018) — makes T006-T008 PASS
- [X] T010 (commit 2) Update `.github/workflows/ci.yml` to add the full 3-OS matrix (Windows + macOS + Linux) per A-010 / plan.md:27 / traceability.md:79. The matrix MUST run **every** test that has cross-platform binding: **packaging** (`test_packaging.py`, `test_packaging_macos.py`, `test_packaging_windows.py` — commit 2), **FR-008 unmanaged paths** (`test_fr008_unmanaged_paths_parameterized.py` — commit 5, validates path-comparison on Windows), **FR-017 validation** (`test_check_filesystem_inspection.py` + `test_sc010_check_runtime.py` — commit 9), **FR-018 migrate** (`test_migrate_classification.py` + `test_migrate_backup_rotation.py` — commit 10, validates backup-path separator handling), **FR-029 smoke** (`test_smoke_claude.py` / `test_smoke_codex.py` / `test_smoke_cursor.py` — commits 4/5/6, gated by host smoke env vars + host CLIs on PATH; `test_smoke_claude_lsp.py` — commit 11), **FR-030 packaging** (covered by packaging tests above), **FR-031/FR-032 manifest path normalization** (`test_fr031_exit_classes.py` + `test_fr032_manifest_actionable_output.py` + `test_manifest_integrity.py` — commit 9, validates manifest path normalization across OSes), **FR-033 linked-repo absolute/relative paths** (`test_fr033_linked_secondary_init.py` — commit 4; `test_fr033_linked_secondary_migrate.py` — commit 10), **SC-013 hook line-ending semantics** (`test_session_start_budget.py` + `test_sc013_tokenizer_and_fallback.py` — commit 13). Single 3-OS matrix entry gates ALL listed tests

### Commit 3 — Plugin manifests + schemas

- [X] T011 [P] (commit 3) Add `tests/contract/test_claude_plugin_schema.py` asserting `.claude-plugin/plugin.json` validates against `schemas/claude-plugin.schema.json`, includes `agents` array field (was missing per `final-merged-findings.md:104`), and structurally honors `data-model.md` § 1a (test FAILS first)
- [X] T012 [P] (commit 3) Add `tests/contract/test_codex_plugin_schema.py` asserting `.codex-plugin/plugin.json` uses scalar relative-path strings with `./` prefix (NOT arrays), has NO `agents`/`lspServers`/`monitors`/`settings`/`bin` fields per `data-model.md` § 1b (test FAILS first)
- [X] T013 [P] (commit 3) Add `tests/contract/test_cursor_plugin_schema.py` asserting `.cursor-plugin/plugin.json` uses scalar relative-path strings with `./` prefix, the agent-bearing field is `agents` (NOT `subagents`), and `./agents/` is the verified path per `data-model.md` § 1c (test FAILS first)
- [X] T014 [P] (commit 3) Create `schemas/claude-plugin.schema.json` matching `contracts/claude-plugin.schema.json`
- [X] T015 [P] (commit 3) Create `schemas/codex-plugin.schema.json` matching `contracts/codex-plugin.schema.json` (scalar paths)
- [X] T016 [P] (commit 3) Create `schemas/cursor-plugin.schema.json` matching `contracts/cursor-plugin.schema.json` (`agents` key + `./agents/`)
- [X] T017 [P] (commit 3) Create/update `.claude-plugin/plugin.json` adding the `agents` field per data-model § 1a; preserve existing `skills`, `commands`, `hooks`, `mcpServers` from feature 018
- [X] T018 [P] (commit 3) Create `.codex-plugin/plugin.json` with scalar `"skills": "./skills/"`, `"mcpServers": "./.mcp.json"`, `"hooks": "./hooks/hooks.json"` per data-model § 1b (no `agents` per OOS-004)
- [X] T019 [P] (commit 3) Create `.cursor-plugin/plugin.json` with scalar `"skills": "./skills/"`, `"rules": "./rules/cursor/"`, `"mcpServers": "./.mcp.json"`, `"hooks": "./hooks/hooks.json"` per data-model § 1c; emit `"agents": "./agents/"` ONLY if Cursor spike (commit 6) passes — implementation defers per cursor-fixture-decision.contract.md

### Commit 8 — `project.yml` JSON schema + pydantic exposure

- [X] T020 [P] (commit 8) Add `tests/contract/test_project_yml_schema.py` asserting `data-model.md` § 2 field shapes: 12 valid `project_type` values (clarify Q1), `architecture_branch` derivation rule (microservice vs generic), invalid project_type rejected (test FAILS first)
- [X] T021 [P] (commit 8) Add `tests/unit/test_project_yml_validation.py` asserting `architecture_branch` derived correctly from `project_type` per data-model § 2 derivation, and `linked_repos` array shape per § 11
- [X] T022 (commit 8) Extend pydantic `ProjectMetadata` model in `src/dotnet_ai_kit/models.py` per data-model § 2 with `field_validator` decorators that derive `architecture_branch` from `project_type` and validate the 12-enum values
- [X] T023 [P] (commit 8) Create `schemas/project-yml.schema.json` (auto-generated from pydantic model via `model_json_schema()`) matching `contracts/project-yml.schema.json`
- [X] T024 [P] (commit 8) Create `schemas/config-yml.schema.json` matching `contracts/config-yml.schema.json`
- [X] T025 [P] (commit 8) Create `schemas/manifest-json.schema.json` matching `contracts/manifest-json.schema.json` (`oneOf` v1/v2 dual-read per R16)
- [X] T026 [P] (commit 8) Create `schemas/hooks-json.schema.json` matching `contracts/hooks-json.schema.json` (event-keyed `SessionStart`/`PreToolUse`/`PostToolUse`)
- [X] T027 (commit 8) Add `jsonschema>=4.0` to `pyproject.toml [project.dependencies]` per research R9

### Cross-cutting Foundational tests

- [X] T028 [P] (Foundational) Add `tests/unit/test_no_network_no_telemetry.py` asserting the import graph of `src/dotnet_ai_kit/` contains no `requests`, `urllib.request.urlopen`, `httpx`, `socket.create_connection`, or analytics SDK imports per A-011 (clarify Q5)

**Checkpoint**: Packaging produces all 3 plugin-manifest directories on Win+macOS+Linux; schemas published; project.yml validates against pydantic-derived schema; no-network invariant asserted. Foundation ready — user-story phases can now begin in parallel (capacity permitting).

---

## Phase 3: User Story 1 — Plugin host users receive updates without per-repository action (P1) 🎯 MVP

**Goal**: After this phase, a developer using Claude Code, Codex CLI, or Cursor sees plugin assets through the host's native plugin install path with zero per-solution upgrade commands. The previous ~180-file per-solution footprint drops to a small fixed set.

**Independent Test**: Init two .NET solutions on the same machine using the same plugin host. Make a change to plugin source. Run that host's plugin update action once. Confirm both solutions exercise the new behavior on next AI session with no per-solution upgrade run. Asserted by `test_sc002_two_solution_propagation.py`.

Maps to **commits 4, 5, 6** in plan.md.

### Commit 4 — Claude plugin-native init

- [X] T029 [P] [US1] (commit 4) Add `tests/unit/test_init_claude_native.py` asserting `dotnet-ai init` with Claude selected writes exactly `.dotnet-ai-kit/config.yml`, `.dotnet-ai-kit/project.yml`, `.dotnet-ai-kit/manifest.json`, and `.claude/settings.json` (permissions merge only); asserts NO `.claude/commands/`, `.claude/skills/`, `.claude/agents/` directories created (test FAILS first per TDD) — **agent-side asserted; commands/skills marked xfail pending T042 full init refactor**
- [X] T030 [P] [US1] (commit 4) Add `tests/integration/test_smoke_claude.py` (gated by `CLAUDE_CODE_SMOKE=1` env var + `claude` CLI on PATH) verifying a Claude-native custom agent fixture is listed in `/agents` under the plugin namespace per CHK001 / FR-029
- [ ] T031 [P] [US1] (commit 4) Add `tests/unit/test_init_interactive_prompt.py` asserting `dotnet-ai init` without `--host` flag launches interactive host-selection prompt per clarify Q4 / FR-014 — **deferred to T042 full init refactor**
- [ ] T032 [P] [US1] (commit 4) Add `tests/unit/test_fr014_fr016_init_e2e.py` asserting (a) interactive prompt shows all 4 hosts, (b) selecting a subset writes files only for selected hosts (CHK037, CHK038) — **deferred to T042 full init refactor**
- [ ] T033 [P] [US1] (commit 4) Add `tests/unit/test_a009_host_symmetry.py` asserting every host with a plugin manifest has a corresponding smoke fixture entry (FR-029 / A-009 governance check) — **deferred (waits for all 4 host adapters)**
- [ ] T034 [P] [US1] (commit 4) Add `tests/unit/test_sc001_file_count.py` asserting fixture-based before/after file count: baseline ≥180 → post-init ≤18 files (SC-001 ≥90% reduction) for plugin-only hosts — **deferred to T042 full init refactor**
- [ ] T035 [P] [US1] (commit 4) Add `tests/unit/test_sc002_two_solution_propagation.py` (fixture-based) asserting two solutions sharing one plugin install see updated behavior after a single host-side update (SC-002) — **deferred**
- [ ] T036 [P] [US1] (commit 4) Add `tests/unit/test_sc005_no_duplicate_claude_listings.py` asserting Claude Code's listing surface shows exactly one entry per logical command/skill (no duplicate from project copies; SC-005) — **deferred**
- [X] T037 [P] [US1] (commit 4) Add `tests/unit/test_agent_generators.py` — **initial scope is Claude-only**: asserts `generate_claude_agent(source)` produces Claude-shape frontmatter, no skill-preload field (FR-027 no regression), uses verbatim markdown body from `agents-source/<name>.md`. **Grown incrementally by T050 (Codex generator NotImplementedError), T058 (Cursor generator), T071 (Copilot generator)** — at commit 4 the file tests only `generate_claude_agent()`
- [ ] T038 [P] [US1] (commit 4) Add `tests/unit/test_fr033_linked_secondary_init.py` asserting primary-repo init with one linked secondary writes the same plugin-native footprint to the secondary (FR-033 / SC-014 init half; migrate half covered by **T096 (test) + T099 (impl)** in commit 10) — **deferred to T042**
- [X] T039 [US1] (commit 4) Create `src/dotnet_ai_kit/hosts/__init__.py` and `src/dotnet_ai_kit/hosts/base.py` exposing abstract `Host` class with `install_paths()`, `verify_install()`, `write_per_solution_files()` per plan.md project-structure
- [X] T040 [US1] (commit 4) Create `src/dotnet_ai_kit/hosts/claude.py` implementing `Host` for Claude: plugin-cache path detection (`~/.claude/plugins/cache/` per R7) on Win/macOS/Linux via `Path.home()`, permissions-merge logic for `.claude/settings.json`
- [X] T041 [US1] (commit 4) Create `src/dotnet_ai_kit/agent_generators.py` exposing `generate_claude_agent(source: AgentSource) -> str` per data-model § 7 + `contracts/agent-source.contract.md`; uses markdown body as document body (NOT a frontmatter field); enforces Claude-shape allow-list per FR-027
- [X] T041a [US1] (commit 4) **Delete `AGENT_FRONTMATTER_MAP` from `src/dotnet_ai_kit/agents.py`** per CHK027 / research R1 (the legacy generic agent-frontmatter map is replaced by per-host generators in T041 / T050 / T058 / T071); also remove every consumer reference to it in `src/dotnet_ai_kit/copier.py`; update or delete affected tests in `tests/test_copier_agents.py` so they assert the per-host generator dispatch path instead of the legacy map
- [ ] T042 [US1] (commit 4) Refactor `src/dotnet_ai_kit/cli.py` `init` command for the Claude plugin-native path: stop bulk-copying commands/skills/agents; write only the per-solution files per FR-005 / FR-006; ensure interactive prompt fires when `--host` absent (per FR-014 / clarify Q4); ensure linked-secondary writer at `copier.py:882-1202` routes through `hosts/` adapters per FR-033 plumbing — **PARTIAL: agent-side via copy_agents() no-op; commands/skills/rules refactor pending full init rewrite**
- [ ] T043 [US1] (commit 4) Refactor `src/dotnet_ai_kit/copier.py` to drop `.claude/commands/`, `.claude/skills/`, `.claude/agents/` copy paths; preserve only the per-solution writes; route linked-secondary writer through the new `hosts/` adapters per FR-033 — **PARTIAL: agent-side dropped; commands/skills/rules pending**

### Commit 5 — Codex documented primitives

- [X] T044 [P] [US1] (commit 5) Add `tests/integration/test_smoke_codex.py` (gated by `CODEX_SMOKE=1` + `codex` CLI on PATH) verifying a Codex-format skill is visible to Codex CLI's skill enumeration per CHK002 / FR-029
- [X] T045 [P] [US1] (commit 5) Add `tests/unit/test_unmanaged_paths_untouched.py` asserting root `AGENTS.md` is never written, modified, or deleted by any tool command per FR-008 / A-008
- [X] T046 [P] [US1] (commit 5) Add `tests/unit/test_fr008_unmanaged_paths_parameterized.py` parameterized across the A-008 list (`.editorconfig`, `Directory.Build.props`, `Directory.Build.targets`, `Directory.Packages.props`, `global.json`, `nuget.config`, `.gitignore`, `.gitattributes`, `Dockerfile`, `docker-compose.yml`, CI workflows, READMEs, license, .sln/.csproj) × every write command (`init`, `upgrade`, `configure`, `migrate`); asserts none of these paths is ever written by the tool
- [X] T047 [US1] (commit 5) Create `src/dotnet_ai_kit/hosts/codex.py` implementing `Host` for Codex: plugin-cache path detection (`~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/` per R7), skills + MCP + hooks only (no native agents per OOS-004), `verify_install()` via filesystem inspection
- [X] T048 [US1] (commit 5) Remove `AGENT_CONFIG["codex"]["agents_file"] = "AGENTS.md"` mapping from `src/dotnet_ai_kit/agents.py:51` per R13
- [X] T049 [US1] (commit 5) Delete `copy_commands_codex` function in `src/dotnet_ai_kit/copier.py:276-317` (the root-AGENTS.md emitter) per R13; ensure no code path writes root `AGENTS.md`
- [X] T050 [US1] (commit 5) Extend `src/dotnet_ai_kit/agent_generators.py` with `generate_codex_agent(source: AgentSource) -> None` that raises `NotImplementedError("Codex native plugin agents deferred to v1.1 per OOS-004")` to make FR-035 admission-gate explicit

### Commit 6 — Cursor rules + sub-agent spike

- [ ] T051 [P] [US1] (commit 6) Add `tests/integration/test_smoke_cursor.py` (gated by `CURSOR_SMOKE=1` + `cursor` CLI on PATH) verifying the single Cursor sub-agent fixture at `agents/<one-fixture>.md` is listed by Cursor per CHK003 / FR-029 / A-005
- [ ] T052 [P] [US1] (commit 6) Add `tests/unit/test_cursor_rules_per_file.py` asserting `copier.py` emits per-rule `.cursor/rules/<name>.mdc` files (NOT one-blob `dotnet-ai-kit.mdc`) per R12 / commit-6 acceptance
- [ ] T053 [P] [US1] (commit 6) Add `tests/unit/test_fr029_cursor_fail_path.py` (meta-test from `cursor-fixture-decision.contract.md:54-60`) asserting consistency between `agents` field presence in `.cursor-plugin/plugin.json` and spec language (A-005/SC-008/OOS-005) **using only the two fixture sets `tests/fixtures/cursor_fixture_pass/` and `tests/fixtures/cursor_fixture_fail/`**. The fixtures embed their own `release-notes.md` stand-ins so the test does NOT depend on the real commit-15 release-notes file existing yet (per Codex tasks-phase round-1 P0-4 correction). The real-release-notes-language consistency assertion is enforced at commit 15 by **T125a** (new task)
- [ ] T054 [US1] (commit 6) Rename `agents/` directory to `agents-source/` per round-3 P2 resolution (source-of-truth markdown bodies); update all internal references
- [ ] T055 [US1] (commit 6) Create `src/dotnet_ai_kit/hosts/cursor.py` implementing `Host` for Cursor: plugin-cache paths `~/.cursor/plugins/local/<name>/` (local symlink dev) and marketplace cache path (verified at first marketplace install per R7); per-rule `.mdc` emission helper
- [ ] T056 [US1] (commit 6) Refactor `src/dotnet_ai_kit/copier.py:231-272` to drop one-blob `.cursor/rules/dotnet-ai-kit.mdc` output; emit per-rule `.cursor/rules/<name>.mdc` files; existing one-blob file is left as legacy-managed (cleaned by migrate command per R12)
- [ ] T057 [US1] (commit 6) Create the single Cursor sub-agent fixture at `agents/<one-fixture>.md` with Cursor's verified frontmatter shape (`name`, `description`, `model`, `readonly`) per `cursor-fixture-decision.contract.md:14-15`
- [ ] T058 [US1] (commit 6) Extend `src/dotnet_ai_kit/agent_generators.py` with `generate_cursor_agent(source: AgentSource) -> str` that emits Cursor-shape frontmatter; expand T037's `test_agent_generators.py` to cover Cursor
- [ ] T059 [US1] (commit 6) Add `.cursor-plugin/plugin.json` `agents: "./agents/"` field conditional on Cursor spike outcome; the field MUST be present only if T051 will pass in CI
- [ ] T060 [US1] (commit 6) Record Cursor spike outcome on **both pass and fail paths** to a single machine-readable source of truth at `specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json` with shape `{"outcome": "passed" | "failed", "timestamp": "...ISO 8601...", "failure_log_path": "..." | null, "ci_run_url": "..." | null}`. PASS path: `outcome="passed"`. FAIL path: `outcome="failed"` plus log/CI references. **Also** keep the human-readable markdown sidecar at `specs/019-plugin-native-arch/discussion/plan-phase/cursor-spike-outcome.md` (narrative form). T125 (commit 15) and T125a (commit 15) read the JSON file; the markdown is for human reviewers only.
- [ ] T061 [US1] (commit 6, FAIL-PATH ONLY) If T051 `test_smoke_cursor.py` FAILS in CI: execute the **commit-6 portion** of the fail-path per `contracts/cursor-fixture-decision.contract.md:37-50`: (a) remove `agents` field from `.cursor-plugin/plugin.json`, (b) make schema `agents` field absent in `cursor-plugin.schema.json`, (c) revise spec A-005 / SC-008 / OOS-005, (d) update verification.md CHK003/CHK004 to deferral, (e) raise `NotImplementedError` in `generate_cursor_agent()`, (f) drop the `agents/` build-output directory from pyproject.toml packaging. **Write the FAIL branch outcome to `specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json` (same file T060 writes on PASS — single source of truth)**. The release-notes update (CHK062 fail branch) is **T125 in commit 15** which reads that JSON — do NOT touch release notes in commit 6 (per Codex tasks-phase round-1 P0-4).

**Checkpoint US1**: All three plugin-supporting hosts have a plugin-native init path; smoke fixtures pass (or Cursor fail-path triggers scope revision per T061); SC-001 file-count reduction verified; SC-002 two-solution propagation verified; SC-005 no duplicate listings verified; FR-033 linked-secondary init verified.

---

## Phase 4: User Story 2 — GitHub Copilot users keep structural parity (P1)

**Goal**: Copilot users observe the same logical content classes as plugin-host users — repo-wide conventions, path-scoped domain guidance, and per-agent files — rendered into `.github/` at the Copilot-native paths, with a re-render path on project metadata change and a freshness-check path on plugin source change.

**Independent Test**: Init with Copilot enabled, verify `.github/copilot-instructions.md` + `.github/instructions/*.instructions.md` + `.github/agents/*.agent.md` exist; rename a project metadata value; run `dotnet-ai upgrade --copilot`; verify rendered files reflect the new metadata. Then change plugin source without re-running; run `dotnet-ai check`; verify it reports renders stale.

Maps to **commit 7** in plan.md.

- [ ] T062 [P] [US2] (commit 7) Add `tests/contract/test_copilot_instructions.py` asserting `.github/copilot-instructions.md` rendered structure per `contracts/copilot-instructions.contract.md` (test FAILS first per TDD)
- [ ] T063 [P] [US2] (commit 7) Add `tests/contract/test_copilot_instructions_path.py` asserting `.github/instructions/*.instructions.md` rendered only for detected project paths per `contracts/copilot-instructions-path.contract.md`
- [ ] T064 [P] [US2] (commit 7) Add `tests/contract/test_copilot_agent.py` asserting `.github/agents/*.agent.md` rendered with expanded allow-list per `contracts/copilot-agent.contract.md` (per current GitHub docs)
- [ ] T065 [P] [US2] (commit 7) Add `tests/unit/test_copilot_render.py` asserting (a) all 3 logical content classes rendered per FR-007 / CHK019, (b) path-scoped routes match project structure, (c) per-agent files cover all 13 specialists
- [ ] T066 [P] [US2] (commit 7) Add `tests/integration/test_copilot_render_lifecycle.py` asserting init→render→edit-metadata→`upgrade --copilot`→files reflect new metadata (CHK016, CHK017, CHK018, FR-004)
- [ ] T067 [P] [US2] (commit 7) Add `tests/unit/test_fr015_fr024_upgrade_separation.py` asserting `dotnet-ai upgrade` is no-op for plugin hosts AND `dotnet-ai upgrade --copilot` re-renders Copilot only AND `dotnet-ai migrate` does NOT re-render Copilot (FR-015 + FR-024)
- [ ] T068 [US2] (commit 7) Create `src/dotnet_ai_kit/hosts/copilot.py` implementing `Host` for Copilot: render orchestrator only (no plugin model per FR-004); reads `project.yml` for runtime substitution; emits to `.github/copilot-instructions.md`, `.github/instructions/<area>.instructions.md`, `.github/agents/<name>.agent.md`
- [ ] T069 [US2] (commit 7) Create `agents-copilot-templates/` directory with jinja2 templates for `.github/agents/<name>.agent.md` per `contracts/copilot-agent.contract.md` allow-list (one template per specialist agent)
- [ ] T070 [US2] (commit 7) Extend `src/dotnet_ai_kit/copier.py` with Copilot render path: jinja2 template render using `ProjectMetadata` values; writes through `manifest.py` so renders are tracked with `host_owner="copilot"`
- [ ] T071 [US2] (commit 7) Extend `src/dotnet_ai_kit/agent_generators.py` with `generate_copilot_agent(source: AgentSource, project: ProjectMetadata) -> str` rendering the Copilot agent template; expand T037's `test_agent_generators.py` to cover Copilot (final 4/4 host coverage for FR-026 / FR-027)
- [ ] T072 [US2] (commit 7) Add `dotnet-ai upgrade --copilot` variant to `src/dotnet_ai_kit/cli.py`: re-renders Copilot files using current plugin source + current `project.yml`; updates `manifest.json` entries; does NOT touch non-Copilot files (FR-015)
- [ ] T072a [P] [US2] (commit 7) Add `tests/unit/test_copilot_path_collision.py` asserting per `contracts/copilot-instructions.contract.md:33-41`: (a) if `.github/copilot-instructions.md` exists pre-init and is NOT in the managed manifest, `dotnet-ai init` with Copilot enabled MUST detect it, preserve it in place, emit a corrective error naming the file + the `--force-render` invocation, and exit non-zero; (b) same default-preserve behavior for `.github/instructions/<name>.instructions.md` and `.github/agents/<name>.agent.md`; (c) FR-008 / A-008 binding (these paths are unmanaged until explicit user opt-in)
- [ ] T072b [P] [US2] (commit 7) Add `tests/unit/test_copilot_force_render.py` asserting per `contracts/copilot-instructions.contract.md:39-41`: (a) `dotnet-ai init --force-render .github/copilot-instructions.md` allows explicit overwrite of THAT exact path only; (b) `--force-render` does NOT bypass protection for OTHER unmanaged Copilot paths (e.g., setting `--force-render <one-instruction-path>` MUST NOT overwrite agent files); (c) after opt-in, the file is recorded in the managed-file manifest with `host_owner: "copilot"` and an explicit-consent flag (per contract:41); (d) the same opt-in flag works for `dotnet-ai upgrade --copilot --force-render <path>`
- [ ] T072c [US2] (commit 7) Implement `--force-render <path>` flag in `dotnet-ai init` AND `dotnet-ai upgrade --copilot` per contract:39-41: path-specific opt-in, manifest update on overwrite (`host_owner: "copilot"`, explicit-consent flag); pre-existing-file detection in `src/dotnet_ai_kit/hosts/copilot.py` returns a typed result that the CLI maps to "preserve and exit non-zero" by default OR "overwrite and record" when the matching `--force-render` flag is set

**Checkpoint US2**: Copilot users see structural parity with plugin-host users; `upgrade --copilot` re-renders on metadata change; migrate vs upgrade separation enforced by tests; pre-existing-file preservation default + path-specific `--force-render` opt-in enforced per FR-008.

---

## Phase 5: User Story 3 — Customization values resolve at the time the AI uses them (P2)

**Goal**: Rename company, change domain, switch architecture profile, or refactor folder paths — and the AI tool reflects those changes on the next runtime resolution point (session start, pre-tool-use hook, skill body evaluation) with no upgrade or re-init step.

**Independent Test**: Init with company="AcmeCorp"; change to "GlobexCorp"; start new AI session; ask a code-gen skill to scaffold; verify output uses "GlobexCorp". Then refactor a layer folder name; verify next skill invocation resolves the new path. Then mid-session, change architecture profile in `project.yml`; verify next PreToolUse hook fire observes the new profile.

Maps to **commits 13, 14** in plan.md.

### Commit 13 — SessionStart compact bootstrap + PreToolUse runtime arch-profile hook

- [ ] T073 [P] [US3] (commit 13) Add `tests/unit/test_session_start_budget.py` asserting SessionStart `stdout` ≤500 tokens under typical project metadata per SC-013 / FR-013 / CHK035 (test FAILS first against current ~5000-token bootstrap)
- [ ] T074 [P] [US3] (commit 13) Add `tests/unit/test_sc013_tokenizer_and_fallback.py` asserting both code paths exercised: primary uses `tiktoken>=0.13.0`, fallback uses hard 2000-char ceiling per R8 (NOT `chars × 0.25`); clearly-logged fallback warning when tiktoken unavailable
- [ ] T075 [P] [US3] (commit 13) Add `tests/unit/test_pretooluse_arch_profile.py` asserting PreToolUse hook reads `project.yml` at fire-time (not from a frozen snapshot), mid-session profile change observed by next tool invocation, missing/corrupt metadata produces a corrective error naming the file + remediation command (CHK046, CHK047, CHK048 / FR-034)
- [ ] T076 [P] [US3] (commit 13) Add `tests/unit/test_runtime_resolution.py` asserting skills/rules consume current `project.yml` values at AI-use time per FR-009 (covers session-start, pre-tool-use, and skill-body resolution points)
- [ ] T077 [P] [US3] (commit 13) Add `tests/unit/test_sc003_runtime_resolution_points.py` asserting after a `project.yml` rename, ALL runtime resolution points observe the new value: session start, pre-tool-use hook, skill body evaluation (SC-003 / FR-010)
- [ ] T078 [US3] (commit 13) REPLACE `hooks/session-start-bootstrap.sh` with a compact ≤500-token bootstrap per `contracts/session-start-bootstrap.contract.md`: emits index pointing to `.dotnet-ai-kit/project.yml` + `dotnet-ai check`; contains NO full rule bodies (T073 PASSES); preserves the existing `tests/test_session_start_hook.py` assertions (forbidden-phrase check, codebase-memory-mcp mention, lazy-default mention, ≤30 lines from feature 018) AND adds the new ≤500-token-stdout assertion in T073 — both tests must pass against the replaced hook
- [ ] T079 [US3] (commit 13) Create new `hooks/pretooluse-arch-profile.sh` per `contracts/pretooluse-arch-profile.contract.md`: reads `project.yml` at fire-time, emits architecture-profile-specific context, exits with corrective error on missing/corrupt metadata (T075 PASSES)
- [ ] T080 [US3] (commit 13) Update `hooks/hooks.json` to register the two new hooks under the correct event keys: `SessionStart` → `session-start-bootstrap.sh`, `PreToolUse` → `pretooluse-arch-profile.sh` per data-model § 12 (preserve existing 4 hooks at their current event keys)

### Commit 14 — Rules reclassification (5/11 split) + constitution v1.0.8 amendment (PASS-CONDITIONAL gate)

**ORDER ENFORCED**: T081 (write test) → T082 (amend constitution) → T083 (verify test now passes) → T084+ (move rules). The constitution amendment must precede the rule-move per plan.md Constitution Check.

- [ ] T081 [US3] (commit 14, FIRST) Add `tests/unit/test_constitution_amendment.py` asserting `.specify/memory/constitution.md` version is `1.0.8` AND the universal whitelist enumerates exactly `async-concurrency`, `coding-style`, `existing-projects`, `security`, `tool-calls` (test FAILS first per TDD)
- [ ] T082 [US3] (commit 14, GATE) Amend `.specify/memory/constitution.md` from v1.0.7 to v1.0.8: update "16 rules — 4 universal + 12 path-scoped" to "16 rules — 5 universal + 11 path-scoped"; add `async-concurrency` to universal whitelist; bump version + bump amendment-date + record amendment reason ("plugin-native architecture spec FR-011 elevates async-concurrency to always-on")
- [ ] T083 [US3] (commit 14, GATE) Run `pytest tests/unit/test_constitution_amendment.py` — MUST PASS before T084+ proceed (plan.md Constitution Check PASS-CONDITIONAL gate)
- [ ] T084 [P] [US3] (commit 14) Add `tests/unit/test_rule_classification.py` asserting exactly 5 rules in `rules/conventions/` and exactly 11 rules in `rules/domain/` per FR-011 / CHK031 / CHK032
- [ ] T085 [P] [US3] (commit 14) Add `tests/unit/test_no_arch_branching_in_always_on.py` asserting `error-handling` (arch-branching) and `naming` (runtime-substitution) are in `rules/domain/`, NOT `rules/conventions/` per FR-012 / CHK033 / CHK034
- [ ] T086 [P] [US3] (commit 14) Add `tests/unit/test_fr011_fr012_jit_loading.py` asserting domain rules load only when the skill or task that references them is invoked (FR-011 JIT, FR-012 deferred load triggers)
- [ ] T087 [P] [US3] (commit 14) Add `tests/unit/test_skill_body_references.py` asserting every always-on convention rule is referenced from skills that depend on it, via `${CLAUDE_PLUGIN_ROOT}/rules/conventions/<name>.md` per CHK036
- [ ] T088 [US3] (commit 14) Create `rules/conventions/` directory and move/copy the 5 always-on rules into it: `async-concurrency.md`, `coding-style.md`, `existing-projects.md`, `security.md`, `tool-calls.md`
- [ ] T089 [US3] (commit 14) Create `rules/domain/` directory and move the 11 just-in-time rules into it: `api-design.md`, `architecture.md`, `configuration.md`, `data-access.md`, `error-handling.md`, `localization.md`, `multi-repo.md`, `naming.md`, `observability.md`, `performance.md`, `testing.md`
- [ ] T090 [US3] (commit 14) Update every `skills/**/SKILL.md` body that depends on a convention rule to reference the new path via `${CLAUDE_PLUGIN_ROOT}/rules/conventions/<name>.md`; ensure T087 passes
- [ ] T091 [US3] (commit 14) Capture SC-004 measurement post-rule-reclassification: tokenizer count of all SessionStart stdout + always-on rule bodies; assert ≥65% reduction from baseline (target band 2500-3000 tokens) per `measurements.md`

**Checkpoint US3**: SessionStart bootstrap ≤500 tokens; PreToolUse arch-profile hook reads `project.yml` at fire-time; rules split into exactly 5 conventions + 11 domain; constitution v1.0.8 amended in the same commit; SC-003 / SC-004 / SC-013 verified.

---

## Phase 6: User Story 4 — Safe, reversible migration from the old per-solution layout (P2)

**Goal**: A developer with a pre-019 solution can run `dotnet-ai migrate` to classify each previously-managed file as clean or user-modified, move clean files to a project-local backup folder with 3-keep rotation, preserve user-modified files in place, and reverse a migration by copying from the backup folder.

**Independent Test**: Init under old layout; modify one generated file; run `migrate --dry-run`; verify report; run `migrate`; verify unmodified files moved to `.dotnet-ai-kit/backups/migrate/<timestamp>/`, modified file preserved in place, third run rotates oldest backup.

Maps to **commit 10** in plan.md.

- [ ] T092 [P] [US4] (commit 10) Add `tests/unit/test_migrate_classification.py` asserting every previously-managed file is classified by SHA-256 content hash against `manifest.json` as either `clean` (matches original) or `user-modified` per FR-020 / CHK020 (test FAILS first)
- [ ] T093 [P] [US4] (commit 10) Add `tests/unit/test_migrate_backup_rotation.py` asserting (a) clean files moved to `.dotnet-ai-kit/backups/migrate/<YYYYMMDD-HHMMSS>/` per FR-021 / CHK021, (b) 3-keep retention rotates oldest per FR-023 / CHK023, (c) directory naming uses portable path-separator semantics on Win/macOS/Linux
- [ ] T094 [P] [US4] (commit 10) Add `tests/unit/test_init_force_prints_migrate.py` asserting `dotnet-ai init --force` on an old-layout solution does NOT auto-delete shadowed artifacts and prints the exact `dotnet-ai migrate` invocation per FR-025 / CHK025
- [ ] T095 [P] [US4] (commit 10) Add `tests/unit/test_fr020_host_owner_all_values.py` asserting the 4 host_owner values (`claude`, `codex`, `cursor`, `copilot`) + `null` are all written correctly by v2 writer AND v1 manifests' `host_owner` is correctly inferred from path patterns per R16 / data-model § 4
- [ ] T096 [P] [US4] (commit 10) Add `tests/unit/test_fr033_linked_secondary_migrate.py` asserting `dotnet-ai migrate` applied to primary repo cleans up legacy copies in linked secondaries (subject to user-modified preservation rules per FR-022 / SC-014 / CHK051)
- [ ] T097 [P] [US4] (commit 10) Add `tests/contract/test_manifest_schema.py` asserting `manifest-json.schema.json` accepts both v1 (no `host_owner`) and v2 (`host_owner` per file) on read per R16; writer always emits v2 per data-model § 5
- [ ] T098 [US4] (commit 10) Create/extend `src/dotnet_ai_kit/manifest.py` for v1/v2 schema versioning: reader detects `schema_version`, infers `host_owner` from path patterns when v1 is read (`.claude/*` → `claude`, `.cursor/*` → `cursor`, `.github/agents/*` → `copilot`, etc. per R16); writer always emits v2; classification helpers `classify_file(path, manifest) -> Literal["clean","user-modified","unknown"]`
- [ ] T099 [US4] (commit 10) Add `dotnet-ai migrate` command to `src/dotnet_ai_kit/cli.py` per `contracts/migrate-cli.contract.md:12-20`: full CLI surface `dotnet-ai migrate [--dry-run] [--include-modified] [--host <host>]`. Reads `manifest.json` (v1 or v2 per R11/R16), classifies each file, moves clean files to `.dotnet-ai-kit/backups/migrate/<timestamp>/`, preserves user-modified in place by default per FR-022, applies 3-keep rotation; `--dry-run` per Constitution V (prints classification report + planned actions, mutates nothing); `--include-modified` is the EXPLICIT user opt-in to also remove user-modified files per FR-022; `--host <host>` scopes migration to files with `host_owner == <host>` (default: all hosts); does NOT re-render Copilot files (FR-024)
- [ ] T099a [P] [US4] (commit 10) Add `tests/unit/test_migrate_cli_flags.py` asserting `--dry-run`, `--include-modified`, `--host` flag behaviors per `contracts/migrate-cli.contract.md:12-20`; including dry-run-mutates-nothing assertion, `--include-modified`-required-for-modified-removal assertion, and `--host <host>`-scoping assertion
- [ ] T100 [US4] (commit 10) Update `dotnet-ai init --force` in `src/dotnet_ai_kit/cli.py` to detect shadowed legacy artifacts (any file present that matches a managed-path pattern from feature 018), skip auto-deletion, print the exact `dotnet-ai migrate` invocation per FR-025

**Checkpoint US4**: Migrate command exists with `--dry-run`; classification correct on SHA-256 hash; 3-keep rotation enforced; user-modified files preserved 100%; init --force prints migrate invocation; linked-secondary cleanup also enforced.

---

## Phase 7: User Story 5 — Validation is a single command (P2)

**Goal**: `dotnet-ai check` is the one-stop validation: plugin install per host (filesystem inspection only per clarify Q3), `csharp-ls` binary on PATH, `project.yml` schema validity + detected-path correctness, `manifest.json` integrity, Copilot render freshness. Exits 0 on healthy; exits non-zero with a unique class identifier on broken state. Runs in <10s on dev workstation.

**Independent Test**: Init; run `dotnet-ai check`; expect exit 0. Uninstall `csharp-ls`; run again; expect non-zero exit naming the missing binary + remediation hint. Corrupt `manifest.json`; run again; expect non-zero exit uniquely identifying the manifest-integrity failure class.

Maps to **commits 9 (check half), 11, 12** in plan.md.

### Commit 9 — `check` command (check-only after round-2 BLOCKER (c) resolution; render moved to commit 14b)

- [ ] T101 [P] [US5] (commit 9) Add `tests/unit/test_check_filesystem_inspection.py` asserting `check` reports plugin install per configured host via filesystem inspection of `~/.<host>/plugins/.../` paths only (no shell-out per clarify Q3) AND reports `csharp-ls` binary status via `shutil.which()` per R10 / SC-011 (test FAILS first)
- [ ] T102 [P] [US5] (commit 9) Add `tests/unit/test_manifest_integrity.py` asserting `check` verifies (a) manifest readability, (b) all expected managed paths exist on disk, (c) content SHA-256 hashes match for rendered/managed files, (d) actionable failure output naming file + expected hash + observed state + remediation command per FR-032 / CHK042
- [ ] T103 [P] [US5] (commit 9) Add `tests/unit/test_fr031_exit_classes.py` asserting `check` exits with status 0 on healthy AND with non-zero status uniquely identifying the failing check class for each of: missing plugin per host, missing csharp-ls binary, invalid project.yml schema, detected-path inconsistency, stale Copilot render, manifest integrity failure (FR-031 / CHK040)
- [ ] T104 [P] [US5] (commit 9) Add `tests/unit/test_fr032_manifest_actionable_output.py` asserting manifest-integrity failure output contains: file path, expected hash, observed state, remediation command per CHK042
- [ ] T105 [P] [US5] (commit 9) Add `tests/unit/test_sc010_check_runtime.py` asserting `dotnet-ai check` completes in <10s median (3 runs) on a fixture project (SC-010 / CHK041)
- [ ] T106 [US5] (commit 9) Extend each `src/dotnet_ai_kit/hosts/<name>.py` with `verify_install() -> InstallStatus` using `shutil.which()` for binaries and `Path.exists()` for plugin-cache directories per clarify Q3 / R10
- [ ] T107 [US5] (commit 9) Extend `src/dotnet_ai_kit/manifest.py` with `integrity_check(manifest_path: Path) -> IntegrityReport` that surfaces actionable failure output per FR-032 / CHK042
- [ ] T108 [US5] (commit 9) Add `dotnet-ai check` command to `src/dotnet_ai_kit/cli.py` per `contracts/check-cli.contract.md:12-20`: full CLI surface `dotnet-ai check [--verbose] [--json] [--host <host>]`. Runs all 6 check classes (host plugin install, csharp-ls, project.yml schema, detected paths, Copilot freshness, manifest integrity) per `contracts/check-cli.contract.md:22-33`; exit codes 10/11/12/13/14/15/16/99 per the contract's exit-class table (lowest code wins on multiple failures); `--verbose` emits per-check breakdown; `--json` emits the structured JSON shape per contract:64-80; `--host <host>` scopes to a single host's checks (default: all `enabled_hosts`)
- [ ] T108a [P] [US5] (commit 9) Add `tests/unit/test_check_cli_flags.py` asserting `--verbose`, `--json`, `--host` flag behaviors per `contracts/check-cli.contract.md:12-20`; including exit-code assertions for each of the 9 codes in the contract's table (0, 10, 11, 12, 13, 14, 15, 16, 99); including `--json` shape assertion per contract:64-80
- [ ] T109 [US5] (commit 9) Extend `scripts/check.py` (from feature 018) with the new plugin-manifest-packaging assertion + multi-host config validation per plan.md project structure

### Commit 11 — `csharp-lsp` plugin dependency added

- [ ] T110 [P] [US5] (commit 11) Add `tests/integration/test_smoke_claude_lsp.py` producing a transcript artifact proving C# diagnostics surface at edit time (not via explicit AI tool invocation) per FR-028 / CHK011 (gated by `CLAUDE_CODE_SMOKE=1` + `claude` CLI on PATH)
- [ ] T111 [US5] (commit 11) Update `.claude-plugin/plugin.json` to add `csharp-lsp` to the `dependencies` array per R6 / CHK010; extend `tests/contract/test_claude_plugin_schema.py` (from T011) to assert `csharp-lsp` is in `dependencies`

### Commit 12 — Remove `csharp-ls` from `.mcp.json` (gated on commit 11's CHK009/CHK010/CHK011 passing in CI)

- [ ] T112 [P] [US5] (commit 12) Add `tests/contract/test_mcp_csharp_removed.py` asserting `.mcp.json` no longer contains `csharp-ls` server entry AND `codebase-memory-mcp` IS retained per `final-merged-findings.md:195` / CHK012 (test FAILS first)
- [ ] T113 [US5] (commit 12, CI-GATED) Update `src/dotnet_ai_kit/cli.py` or CI config so that commit 12 fails the build if CHK009 (T101 csharp-ls detection), CHK010 (T111 dep), or CHK011 (T110 smoke transcript) are not green in the same PR's CI run per plan.md
- [ ] T114 [US5] (commit 12) Remove `csharp-ls` server entry from `.mcp.json`; preserve `codebase-memory-mcp` entry per `final-merged-findings.md:195`; T112 PASSES

**Checkpoint US5**: `dotnet-ai check` covers all 6 check classes in <10s; exits with unique class identifier per failure; csharp-lsp LSP migration complete with edit-time-diagnostics smoke transcript captured; `.mcp.json` cleaned only after CHK009/010/011 green.

---

## Phase 8: User Story 6 — Runtime inspection mitigates loss of pre-rendered files (P3)

**Goal**: `dotnet-ai render skill <name>` and `dotnet-ai render rule <name>` print the runtime-resolved content using current `project.yml`, restoring the inspectability of the old layout without restoring on-disk pre-renders. Completes in <2s per SC-012. v1 scope = Claude-host-shaped output (other hosts' render shapes deferred per SC-012).

**Independent Test**: Init; rename `company` in `project.yml`; run `dotnet-ai render skill <param-skill>`; verify output shows the new company value substituted; verify output is identifiable as Claude-host-shaped; verify <2s runtime.

Maps to **commit 14b** (NEW commit inserted during tasks-phase round 1 per Codex BLOCKER (c); placed AFTER commit 14 because `render_rule()` depends on the finalized 5/11 rule layout from commit 14's `rules/conventions/` + `rules/domain/` directories).

**Execution dependency**: US6 (Phase 8) cannot start until commit 14 (Phase 5 / US3) lands. Once commit 14 is in place, US6 / commit 14b lands before commit 15 (Phase 9 / Polish).

- [ ] T115 [P] [US6] (commit 14b) Add `tests/unit/test_fr019_render_cases.py` covering full case matrix per `contracts/render-cli.contract.md`: (a) success path with parameterized skill (exit 0), (b) skill or rule not found (exit 21), (c) `project.yml` missing/corrupt (exit 22), (d) substitution failure when metadata key absent (exit 23), (e) `--host codex`/`--host cursor`/`--host copilot` rejected with exit 20 + v1.1-deferral message per contract:25-39 (CHK045 explicit guard against silent non-Claude output), (f) `--host claude` is accepted as the default (test FAILS first)
- [ ] T116 [P] [US6] (commit 14b) Add `tests/unit/test_sc012_render_runtime.py` asserting `dotnet-ai render skill <fixture-skill>` completes in <2s median (3 runs) on a fixture project per SC-012
- [ ] T117 [US6] (commit 14b) Create `src/dotnet_ai_kit/render.py` per `contracts/render-cli.contract.md`: function `render_skill(name: str, project: ProjectMetadata) -> str` resolves the named skill body against current project metadata using jinja2; function `render_rule(name: str, project: ProjectMetadata) -> str` resolves against the finalized rule layout from commit 14 (`rules/conventions/` + `rules/domain/`); Claude-host-shaped output (v1); raises typed exceptions mapped to the 21/22/23 exit codes
- [ ] T118 [US6] (commit 14b) Add `dotnet-ai render` command to `src/dotnet_ai_kit/cli.py` per `contracts/render-cli.contract.md:12-20`: full CLI surface `dotnet-ai render <kind> <name> [--host <host>]`. `<kind>` ∈ `{skill, rule}` (required positional); `<name>` required positional; `--host` default `claude`, other values rejected with exit 20 + v1.1-deferral message; subcommands print resolved content to stdout; read-only (no `--dry-run` needed); exits with 0/20/21/22/23 per contract:41-49

**Checkpoint US6**: Render command produces Claude-shaped resolved content in <2s; v1 scope locked to Claude-host shape (other hosts rejected with exit 20); FR-019 + SC-012 traceable to commit 14b.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, release notes, governance checks, and final cross-cutting validation. Maps to **commit 15** in plan.md.

- [ ] T119 [P] (commit 15) Update `README.md` to reflect new file footprint per FR-005 (small fixed set vs ~180) per CHK058
- [ ] T120 [P] (commit 15) Update `CLAUDE.md` (project guidance) per plan.md commit-15 acceptance: new commands (`migrate`, `render`), new rule classification (5 conventions + 11 domain), no-network posture per A-011
- [ ] T121 [P] (commit 15) Create `docs/migration-v1.md` explaining: when to run `dotnet-ai migrate`, what it does/doesn't do, interaction with `upgrade --copilot`, how to reverse a migration via the project-local backup folder per CHK055
- [ ] T122 [P] (commit 15) Write release notes file (e.g., `docs/release-notes-v1.0.md`): plugin-update-mid-session edge case + each host's reload mechanism (Claude `/reload-plugins`, Codex restart, Cursor "Reload Window") per R15 / CHK056; `csharp-ls` prerequisite + `dotnet-ai check` as pre-flight per CHK057; no-telemetry posture per A-011
- [ ] T123 [P] (commit 15) Update `planning/` with the Cursor sub-agent spike outcome reference + the `bin/` launcher deferral record (OOS-003) per CHK060
- [ ] T124 (commit 15) Add OOS-004 (native Codex agents deferred to v1.1) + OOS-006 (multi-repository monitor deferred) statements to release notes per CHK061 / CHK063 (NOT [P] — same release-notes file as T122/T125/T128)
- [ ] T125 (commit 15) Add CHK062-branched statement to release notes by **reading `specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json` written by T060 (both paths) and updated by T061 (fail path)**: if `outcome == "passed"` emit "Cursor sub-agent generation shipped"; if `outcome == "failed"` emit "Cursor sub-agent generation deferred to v1.1". The branching is data-driven, NOT manually authored; the release-notes file is one of the artifacts T122 creates and T125 amends. (Removed [P] per Codex P2-1 — same file as T122, T124, T128.)
- [ ] T125a (commit 15) Add `tests/unit/test_release_notes_consistency.py` asserting the real release-notes file content matches the `specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json` `outcome` AND matches the spec A-005/SC-008/OOS-005 language AND matches the `.cursor-plugin/plugin.json` `agents`-field presence. This is the real-artifact version of T053's fixture-only test (the test_fr029_cursor_fail_path.py from commit 6 used embedded fixtures; T125a uses the live files).
- [ ] T126 [P] (commit 15) Publish the A-008 non-exhaustive list of .NET-root developer-owned paths in user-facing docs per CHK059 (concrete list of files the tool will not write to)
- [ ] T127 [P] (commit 15) Add `tests/unit/test_fr035_host_admission_static_guard.py` static-code check: assert any new host added to `SUPPORTED_AI_TOOLS` has all 4 admission gates (documented install/update path, documented primitives, smoke fixture, packaging test) per FR-035 / CHK052
- [ ] T128 (commit 15) Run documentation lint: markdown link check + broken-reference scan across all `docs/`, `README.md`, `CLAUDE.md`, release notes per commit-15 acceptance (NOT [P] — depends on T122/T124/T125 release-notes content being final)
- [ ] T129 (commit 15) Capture post-fix measurements in `specs/019-plugin-native-arch/measurements.md` per the post-fix capture procedure: SC-001, SC-004, SC-010, SC-012, SC-013 actual values; assert each meets its target
- [ ] T130 (commit 15) Run quickstart.md end-to-end on Windows + macOS + Linux: install plugin via each host's native path, `dotnet-ai init`, `dotnet-ai check`, `dotnet-ai render`, `dotnet-ai migrate --dry-run` — confirm each step works per its documented behavior

**Final Checkpoint**: All 63 CHK items in `checklists/verification.md` checked off; all SCs (SC-001..SC-014) measured + meeting thresholds; release notes reflect actual Cursor spike outcome; documentation links clean.

---

## Dependencies & Execution Order

### Phase Dependencies

**Phases are presented in US-priority order per the SDD template, but EXECUTION follows the Commit Execution Order table above (binding).**

- **Setup (Phase 1)**: no dependencies — starts immediately (commit 1)
- **Foundational (Phase 2)**: depends on Setup (commits 2, 3, 8)
- **User-Story Phases**: ordered by commit, NOT by phase number:
  - **Commit 4-7**: US1 (Claude/Codex/Cursor) → US2 (Copilot) — completing MVP
  - **Commit 9**: US5 `check` (check half — render moved to commit 14b)
  - **Commit 10**: US4 migrate
  - **Commit 11-12**: US5 LSP migration (commit 12 CI-gated on commit 11 CHK009/010/011 green)
  - **Commit 13-14**: US3 runtime hooks + rule reclassification
  - **Commit 14b**: US6 render (NEW commit; depends on commit 14 final rule layout)
- **Polish (Phase 9)**: commit 15 — depends on all preceding commits AND on commit-6 spike outcome via T125 reading `specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json` (written by T060 on both pass and fail paths, updated by T061 on fail path)

The user-story phases (Phase 3 = US1, Phase 4 = US2, Phase 5 = US3, Phase 6 = US4, Phase 7 = US5, Phase 8 = US6) do NOT execute in phase-number order. They execute in commit-number order per the Commit Execution Order table.

### Hard inter-commit gates (re-statement)

| Gate | Predecessor | Successor | Enforcement |
|--|--|--|--|
| LSP migration | commit 11 (T110, T111) green in CI | commit 12 (T112-T114) | T113 CI-gated check |
| Constitution amendment | T081 → T082 → T083 (PASS-CONDITIONAL) | T084+ rule moves | sequential within commit 14 |
| Cursor spike outcome | commit 6 T051 outcome | commit 15 T125 release-notes branch | T061 fail-path triggers scope revision |
| Commit ordering | 16 commits in sequence `1..14, 14b, 15` on `019-plugin-native-arch` branch | merge | single-PR per plan.md |

### Within Each User Story

- Tests precede implementation per plan-mandated TDD (each commit's failing tests written first)
- Models before services (e.g., `models.py` `ProjectMetadata` extension before any code that consumes it)
- Services before CLI commands (e.g., `hosts/<name>.py` before `cli.py` extensions that call them)
- Core implementation before integration tests

### Parallel Opportunities

- All Setup [P] tasks can run in parallel (different files)
- All Foundational [P] tasks within a commit can run in parallel
- After Foundational completes, US1+US2+US3+US4+US5 (with US6 coordinated against US5's commit 9) can run in parallel
- Within each commit, [P] tasks marked above are independent files

---

## Parallel Example: User Story 1 (commit 4)

```bash
# Tests in commit 4 can be written in parallel (different files):
Task: "Add tests/unit/test_init_claude_native.py asserting init writes minimal file set"
Task: "Add tests/integration/test_smoke_claude.py with CLAUDE_CODE_SMOKE gating"
Task: "Add tests/unit/test_init_interactive_prompt.py asserting no-flag → interactive"
Task: "Add tests/unit/test_fr014_fr016_init_e2e.py multi-host configure UI"
Task: "Add tests/unit/test_a009_host_symmetry.py governance check"
Task: "Add tests/unit/test_sc001_file_count.py fixture-based reduction"

# Then implementation tasks (must serialize on cli.py + copier.py since same file):
Task: "Create hosts/__init__.py and hosts/base.py (T039)"
Task: "Create hosts/claude.py (T040)"
Task: "Refactor cli.py init for Claude path (T042)"  # not [P] with T043
Task: "Refactor copier.py drop bulk-copy paths (T043)"  # not [P] with T042
```

---

## Implementation Strategy

**BINDING ORDER**: commit-sequential per the Commit Execution Order table above. The strategy below reflects that order, NOT user-story priority order.

### MVP-equivalent breakpoint (after commit 7)

After commits 1-7 land in sequence, the plugin-native architecture is structurally complete: all 3 plugin hosts (Claude / Codex / Cursor) have native plugin install paths AND Copilot has structural parity via repository-rendered files. This is the earliest meaningful breakpoint to demo and stop for validation. Both P1 user stories (US1 + US2) are complete at this point.

Sequence:
1. Commit 1 (Phase 1 Setup) — multi-host config foundation
2. Commits 2, 3, 8 (Phase 2 Foundational) — packaging + manifests + project.yml schema
3. Commit 4 (Phase 3 US1) — Claude plugin-native init
4. Commit 5 (Phase 3 US1) — Codex documented primitives
5. Commit 6 (Phase 3 US1) — Cursor rules + sub-agent spike (spike outcome recorded for commit 15 release notes)
6. Commit 7 (Phase 4 US2) — Copilot GitHub-native render
7. **STOP and VALIDATE**: P1 done — Deploy/Demo if ready

### Incremental Delivery (continuing past MVP)

Continuing commit-sequentially:

8. Commit 9 — `check` host-specific validations (Phase 7 US5)
9. Commit 10 — `migrate` + backup rotation (Phase 6 US4)
10. Commit 11 — `csharp-lsp` plugin dependency added (Phase 7 US5)
11. Commit 12 — Remove `csharp-ls` from `.mcp.json` (Phase 7 US5; **CI-gated on commit 11 CHK009/010/011 green**)
12. Commit 13 — SessionStart compact + PreToolUse arch-profile hooks (Phase 5 US3)
13. Commit 14 — Rules reclassification (5/11) + constitution v1.0.8 amendment (Phase 5 US3)
14. **Commit 14b** — `render` read-only CLI surface (Phase 8 US6; **depends on commit 14 final rule layout**)
15. Commit 15 — Docs, migration guide, README, release notes (Phase 9 Polish; **release notes branch determined by commit-6 spike outcome via T125**)

### Parallel Team Strategy (within a commit boundary, NOT across)

Within a single commit, tasks marked `[P]` can be parallelized across developers. Across commits, the sequential order MUST hold (see Hard inter-commit gates section). Example for commit 4:

- Developer A: T029-T038 [P] (test files — different files)
- Developer B: T039-T043 (implementation — coordinate on `cli.py` / `copier.py` since same file)

Do NOT parallelize across commits. The 16-commit linear order is a binding plan property.

---

## Notes

- `[P]` tasks = different files, no incomplete dependencies in same phase
- `[Story]` label maps each task to a spec.md user story for traceability
- Each user-story phase is independently completable and testable
- `(commit N)` preserves the 16-commit order (original 15 architecture-phase commits plus tasks-phase **commit 14b** for render) across the user-story regrouping
- Verify tests FAIL before implementing per plan-mandated TDD
- Commit per logical group; do not amend after merge
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same-file conflicts within a [P] group, cross-story dependencies that break independence
- Commit 9 is **check-only** (render moved to commit 14b per tasks-phase round-1 BLOCKER (c) resolution); the US6 / FR-019 gap from plan-phase draft v3 is closed by commit 14b, NOT by bundling into commit 9

## Open items for tasks-phase Codex round 2

### Round-1 BLOCKER resolution

Codex round 1 verdict was **(c) PREFER A DIFFERENT PLACEMENT** for render. Applied in this round 2 draft:

- Reverted `plan.md` commit 9 to its original `check`-only scope (removed render bundling, removed FR-019/SC-012 from commit 9 FRs, removed FR-034/`test_pretooluse_arch_profile.py` from commit 9, removed render-related test files from commit 9)
- Inserted new `plan.md` commit 14b for `render` (placed after commit 14 because `render_rule()` depends on commit 14's finalized 5/11 rule layout)
- Updated `plan.md` commit count from 15 → 16; documented the sequence `1..14, 14b, 15`
- Moved tasks T115-T118 from Phase 8 "commit 9 render-half" → Phase 8 "commit 14b"
- Updated tasks T115-T118 to cover the full `contracts/render-cli.contract.md` CLI surface (`--host` flag, exit codes 0/20/21/22/23)

### Round-1 P0 fixes applied

| Codex finding | Resolution |
|--|--|
| P0-1 (task order vs commit order) | Added "Commit Execution Order" section as BINDING table; restructured Implementation Strategy + Phase Dependencies to follow commit order |
| P0-2 (stale hard-gate task IDs T070-T074 / T056-T058 / T044/T091) | Fixed header `Hard inter-commit gates` to T110/T111 → T112-T114, T081 → T082 → T083 → T084+, T051/T061/T125; fixed T038 stale `T080` → `T096/T099` |
| P0-3 (missing CLI flags/exit codes) | T108 updated for `--verbose`/`--json`/`--host` per check-cli contract; new T108a added for exit-code-class table assertion; T099 updated for `--dry-run`/`--include-modified`/`--host` per migrate-cli contract; new T099a added; T118 updated for `--host` + exit codes 0/20/21/22/23 per render-cli contract; T115 expanded to cover full case matrix |
| P0-4 (Cursor fail-path crossing commits) | T053 explicitly uses embedded fixture stand-ins (NOT real release-notes file); T060 writes spike outcome to `specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json` on BOTH pass AND fail paths (per round-2 Codex P0-1 correction — single source of truth, NOT per-solution `.dotnet-ai-kit/`); T061 updates the same JSON with fail-branch details; T125 (commit 15) reads the spike outcome and emits the branch-appropriate release-notes statement; new T125a added for real-artifact consistency assertion |
| P1-1 (A-010 CI matrix incomplete) | T010 expanded to include test_fr008_unmanaged_paths_parameterized.py, test_fr031_exit_classes.py, test_fr032_manifest_actionable_output.py, test_manifest_integrity.py + every cross-platform-binding test from plan.md:27 / traceability.md:79 |
| P1-2 (reverse traceability) | Added 13 tasks-phase-introduced test rows to traceability.md "Additional tests added during tasks-phase round 1" table |
| P1-3 (Copilot path-collision / `--force-render`) | Added T072a (pre-existing-file preservation test), T072b (path-specific `--force-render` opt-in test), T072c (implementation) in commit 7 |
| P1-4 (copilot-agent contract path) | Updated `contracts/copilot-agent.contract.md` to reference `agents-source/<name>.md` (was `agents/<name>.md`) |
| P1-5 (SessionStart contract vs MCP assertion conflict) | Added line 6 to `contracts/session-start-bootstrap.contract.md` for persistent-memory pointer (`codebase-memory-mcp`) — preserves the feature-018 test assertion while keeping bootstrap ≤500 tokens |
| P1-6 (commit 9 / FR-034 inconsistency) | Removed FR-034 + `test_pretooluse_arch_profile.py` from `plan.md` commit 9 (FR-034 is implemented by commit 13's hook; commit 9 `check` does not re-implement it; check-cli.contract.md:22-33 enumerates only 6 check classes, none of which is PreToolUse) |
| P2-1 ([P] markers in Polish) | Removed [P] from T124 + T125 + T128 (same release-notes file as T122) |
| P2-2 (verification.md FR-030 stale) | Updated preamble at `checklists/verification.md:10` to remove the "FR-030 was removed" claim |

### Open items for round 2 review

1. Is the new commit 14b correctly placed AFTER commit 14 (where rule layout finalizes) and BEFORE commit 15 (so polish/docs can reference render)? Or should it be earlier/later?
2. Is the "Commit Execution Order" table the right way to override phase numbering for execution, or do you prefer reordering phases by commit-min instead (breaking the SDD template's US-priority requirement)?
3. (resolved in round 2 via Codex P0-1) Spike-outcome file moved to `specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json` — single source of truth written by T060 on both pass and fail paths; T061 updates with fail-branch details; T125 / T125a read it at commit 15.
4. T072c implementation in commit 7 — does the `--force-render <path>` flag need a corresponding entry in `contracts/copilot-instructions.contract.md:39-41` as a formally testable shape, or is the contract text sufficient?
5. T125a (release-notes consistency real-artifact test) — should this live in commit 15 (where release notes are written) or in a separate post-merge verification step?
