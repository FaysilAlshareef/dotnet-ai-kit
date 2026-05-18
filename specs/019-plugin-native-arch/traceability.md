# Traceability: FR / SC / A / CHK → Tests

**Branch**: `019-plugin-native-arch` | **Date**: 2026-05-17 | **Plan**: [plan.md](./plan.md)

Every requirement, success criterion, assumption, and verification checklist item is mapped to a test file or documented manual gate. Per Codex plan-phase round-1 critique CP4 and round-2 expansion. Follows the 018 traceability.md pattern.

## Functional Requirements

| Spec ref | Test file(s) | Notes |
|--|--|--|
| FR-001 | `tests/integration/test_smoke_claude.py`, `tests/integration/test_smoke_codex.py`, `tests/integration/test_smoke_cursor.py` | Each host's plugin installs and is loadable |
| FR-002 | `tests/contract/test_codex_plugin_schema.py`, `tests/contract/test_cursor_plugin_schema.py` | Schema rejects fields not documented by the host |
| FR-003 | `tests/test_packaging.py` (Linux/default) + `tests/integration/test_packaging_macos.py` + `tests/integration/test_packaging_windows.py` | All 3 manifest dirs present in installed wheel |
| FR-004 | `tests/integration/test_copilot_render_lifecycle.py` | Copilot renders without plugin host |
| FR-005 | `tests/unit/test_sc001_file_count.py` | Per-solution footprint matches spec named list |
| FR-006 | `tests/unit/test_init_claude_native.py` | No `.claude/commands/`, `.claude/skills/`, `.claude/agents/` written |
| FR-007 | `tests/unit/test_copilot_render.py` (3 logical content classes) + `tests/contract/test_copilot_*.py` | Repo-wide + path-scoped + per-agent files |
| FR-008 | `tests/unit/test_fr008_unmanaged_paths_parameterized.py` | A-008 list × every write command |
| FR-009 | `tests/unit/test_runtime_resolution.py` | Skills/rules read current metadata |
| FR-010 | `tests/unit/test_sc003_runtime_resolution_points.py` | Rename observed by next runtime point |
| FR-011 | `tests/unit/test_fr011_fr012_jit_loading.py`, `tests/unit/test_rule_classification.py` | Exact 5/11 split; JIT loading triggers |
| FR-012 | Same as FR-011 + `tests/unit/test_no_arch_branching_in_always_on.py` | error-handling/naming NOT in always-on |
| FR-013 | `tests/unit/test_sc013_tokenizer_and_fallback.py` | SessionStart compact |
| FR-014 | `tests/unit/test_fr014_fr016_init_e2e.py` | Interactive prompt on no-flag |
| FR-015 | `tests/unit/test_fr015_fr024_upgrade_separation.py` | Plugin no-op vs Copilot re-render |
| FR-016 | `tests/unit/test_fr014_fr016_init_e2e.py` | Multi-host configure UI |
| FR-017 | `tests/unit/test_check_filesystem_inspection.py`, `tests/unit/test_sc010_check_runtime.py` | All check classes |
| FR-018 | `tests/unit/test_migrate_classification.py` | Migrate command exists and works |
| FR-019 | `tests/unit/test_fr019_render_cases.py`, `tests/unit/test_sc012_render_runtime.py` | render CLI shape, errors, perf |
| FR-020 | `tests/unit/test_fr020_host_owner_all_values.py` | All 4 host_owners + null + legacy inference |
| FR-021 | `tests/unit/test_migrate_backup_rotation.py` | Project-local backup path |
| FR-022 | `tests/unit/test_migrate_classification.py` | User-modified preserved |
| FR-023 | `tests/unit/test_migrate_backup_rotation.py` | 3-keep policy |
| FR-024 | `tests/unit/test_fr015_fr024_upgrade_separation.py` | Migrate does NOT re-render Copilot |
| FR-025 | `tests/unit/test_init_force_prints_migrate.py` | init --force prints migrate invocation |
| FR-026 | `tests/unit/test_agent_generators.py` | One source-of-truth per logical agent |
| FR-027 | `tests/unit/test_agent_generators.py` | No field leak per host; no skill-preload regression |
| FR-028 | `tests/integration/test_smoke_claude_lsp.py` (NEW per round-3) | Edit-time diagnostics surface (CHK011) |
| FR-029 | `tests/integration/test_smoke_{claude,codex,cursor}.py`, `tests/unit/test_fr029_cursor_fail_path.py` | All 3 fixtures + Cursor fail path |
| FR-030 | `tests/test_packaging.py` (Linux/default) + `tests/integration/test_packaging_macos.py` + `tests/integration/test_packaging_windows.py` | Packaging test on each OS |
| FR-031 | `tests/unit/test_fr031_exit_classes.py` | Unique exit class per failure |
| FR-032 | `tests/unit/test_fr032_manifest_actionable_output.py`, `tests/unit/test_manifest_integrity.py` | Manifest integrity check + actionable failure |
| FR-033 | `tests/unit/test_fr033_linked_secondary_init.py`, `tests/unit/test_fr033_linked_secondary_migrate.py` | Linked-secondary back door closed |
| FR-034 | `tests/unit/test_pretooluse_arch_profile.py` | PreToolUse reads project.yml at fire-time |
| FR-035 | `tests/unit/test_fr035_host_admission_static_guard.py` | New host admission gate static check |

## Success Criteria

| Spec ref | Test file(s) | Notes |
|--|--|--|
| SC-001 | `tests/unit/test_sc001_file_count.py` + `measurements.md` | ≥90% file reduction; fixture-based |
| SC-002 | `tests/unit/test_sc002_two_solution_propagation.py` | Two solutions share one plugin update |
| SC-003 | `tests/unit/test_sc003_runtime_resolution_points.py` | Multiple runtime resolution points |
| SC-004 | `tests/unit/test_session_start_budget.py` + `measurements.md` | ≥65% always-on reduction; tokens unit |
| SC-005 | `tests/unit/test_sc005_no_duplicate_claude_listings.py` | Exactly one entry per logical command/skill |
| SC-006 | `tests/unit/test_copilot_render.py` + `tests/contract/test_copilot_*.py` | Structural parity |
| SC-007 | `tests/unit/test_migrate_classification.py` | 100% user-modified preserved |
| SC-008 | `tests/integration/test_smoke_{claude,codex,cursor}.py` + `cursor-fixture-decision.contract.md` | Pre-merge fixture gates |
| SC-009 | `tests/test_packaging.py` (Linux/default) + `tests/integration/test_packaging_macos.py` + `tests/integration/test_packaging_windows.py` | All manifest dirs present |
| SC-010 | `tests/unit/test_sc010_check_runtime.py` | <10s validation |
| SC-011 | `tests/unit/test_check_filesystem_inspection.py` | csharp-ls missing detected |
| SC-012 | `tests/unit/test_sc012_render_runtime.py` | <2s render |
| SC-013 | `tests/unit/test_sc013_tokenizer_and_fallback.py` | ≤500 tokens SessionStart + fallback |
| SC-014 | `tests/unit/test_fr033_linked_secondary_init.py` | Linked-secondary no legacy copies |

## Assumptions

| Spec ref | Test/Gate | Notes |
|--|--|--|
| A-001 | Manual gate (release context) | No public users; verified by maintainer at release time |
| A-002 | `tests/unit/test_copilot_render.py` | Copilot in scope |
| A-003 | Manual gate (no extensions subsystem changes) | Code review |
| A-004 | Manual gate (debate folder exists) | `issues/plugin-native-architecture/` + `discussion/` |
| A-005 | `cursor-fixture-decision.contract.md` + `tests/unit/test_fr029_cursor_fail_path.py` | Fixture mandatory; conditional full generation |
| A-006 | `tests/contract/test_codex_plugin_schema.py` | No native Codex agents in v1 |
| A-007 | `tests/unit/test_check_filesystem_inspection.py` | csharp-ls binary surfaced by check |
| A-008 | `tests/unit/test_fr008_unmanaged_paths_parameterized.py` | Non-exhaustive .NET root path list |
| A-009 | `tests/unit/test_a009_host_symmetry.py` (NEW) | Per-host smoke fixtures required |
| A-010 | Cross-platform CI matrix on all FR-008/021/031/032/033/SC-013 + originally listed 4 | Windows + macOS + Linux |
| A-011 | `tests/unit/test_no_network_no_telemetry.py` | No outbound network, no telemetry |

## Verification Checklist (CHK001–CHK063)

Each CHK item maps to either a test from above or a manual gate documented in `checklists/verification.md`. Where multiple CHK items share a test, the test asserts each invariant separately. The complete CHK→test mapping lives in `checklists/verification.md` itself; this section is the test→CHK reverse index for the most-cited tests:

- `tests/integration/test_smoke_claude.py` → CHK001, CHK010 (extension), CHK011 (via `test_smoke_claude_lsp.py`)
- `tests/integration/test_smoke_codex.py` → CHK002
- `tests/integration/test_smoke_cursor.py` → CHK003, CHK004
- `tests/test_packaging.py` (Linux/default) + `tests/integration/test_packaging_macos.py` + `tests/integration/test_packaging_windows.py` → CHK005, CHK006, CHK007, CHK008
- `tests/unit/test_manifest_integrity.py` → CHK019, CHK020, CHK042
- `tests/unit/test_pretooluse_arch_profile.py` → CHK046, CHK047, CHK048
- `tests/unit/test_fr033_linked_secondary_*.py` → CHK049, CHK050, CHK051
- `tests/unit/test_fr035_host_admission_static_guard.py` → CHK052
- `tests/unit/test_rule_classification.py` → CHK031, CHK032, CHK033, CHK034
- `tests/unit/test_session_start_budget.py` → CHK035
- `tests/contract/test_mcp_csharp_removed.py` (NEW per round-3) → CHK012 (commit 12 contract)

## Additional tests added during tasks-phase round 1 (per Codex P1-2)

These tests are owned by the plan-mandated TDD discipline / per-commit acceptance, not by a single FR row. They are listed here so reverse-traceability is clean (every test in `tasks.md` traces to either a row above or a row here):

| Tasks-phase test | Owner | Commit | Why added |
|--|--|--|--|
| `tests/contract/test_config_yml_schema.py` | T005 | commit 1 | FR-016 multi-host config schema + `ai_tools` legacy alias migration (data-model § 3); validates the published `schemas/config-yml.schema.json` artifact |
| `tests/unit/test_project_yml_validation.py` | T021 | commit 8 | FR-017 `architecture_branch` derivation rule + `linked_repos` array shape (data-model § 2, § 11) — finer-grained than `test_project_yml_schema.py` |
| `tests/unit/test_init_interactive_prompt.py` | T031 | commit 4 | FR-014 / clarify Q4 — no-`--host`-flag → interactive prompt baseline (paired with `test_fr014_fr016_init_e2e.py`) |
| `tests/unit/test_unmanaged_paths_untouched.py` | T045 | commit 5 | FR-008 root-`AGENTS.md` baseline assertion (paired with parameterized `test_fr008_unmanaged_paths_parameterized.py`) |
| `tests/unit/test_cursor_rules_per_file.py` | T052 | commit 6 | R12 / commit-6 acceptance — assert no one-blob `.cursor/rules/dotnet-ai-kit.mdc` output |
| `tests/contract/test_manifest_schema.py` | T097 | commit 10 | R16 v1/v2 dual-read contract test (data-model § 5); separate from `test_manifest_integrity.py` (FR-032 integrity) and `test_fr020_host_owner_all_values.py` (FR-020 host_owner) |
| `tests/unit/test_constitution_amendment.py` | T081 | commit 14 | Constitution Check PASS-CONDITIONAL gate per plan.md (4→5 universal rules amendment); not an FR — a governance gate |
| `tests/unit/test_check_cli_flags.py` | T108a | commit 9 | `contracts/check-cli.contract.md:12-20` CLI flag matrix + exit-code-class table (per Codex tasks-phase P0-3) |
| `tests/unit/test_migrate_cli_flags.py` | T099a | commit 10 | `contracts/migrate-cli.contract.md:12-20` CLI flag matrix (per Codex tasks-phase P0-3) |
| `tests/unit/test_copilot_path_collision.py` | T072a | commit 7 | `contracts/copilot-instructions.contract.md:33-41` default-preserve pre-existing-file behavior (per Codex tasks-phase P1-3) |
| `tests/unit/test_copilot_force_render.py` | T072b | commit 7 | `contracts/copilot-instructions.contract.md:39-41` path-specific `--force-render` opt-in (per Codex tasks-phase P1-3) |
| `tests/unit/test_release_notes_consistency.py` | T125a | commit 15 | A-005 / SC-008 / OOS-005 real-artifact consistency assertion (per Codex tasks-phase P0-4); separate from T053's fixture-only meta-test |
| `tests/unit/test_skill_body_references.py` | T087 | commit 14 | CHK036 — every always-on convention rule referenced from skills that depend on it via `${CLAUDE_PLUGIN_ROOT}/rules/conventions/<name>.md` |

## Additional tests added during Phase 10 (post-review corrections)

These **21 Phase-10 test/gate rows** (mix of pytest files, workflow
rewrites, and CI-only gates — see the "Owner" column for the exact
artifact) close the **8 BLOCKERS (B-1 → B-8: 4 P0 + 4 P1)** + 8
round-3 plan corrections identified in the cross-AI review-phase
debate. See `discussion/review-phase/claude/final-consolidated-review.md`
(canonical fix plan) + `discussion/review-phase/round4-codex-reply.md`
(round-4 verification refinements).

| Phase-10 test | Owner | Commit | Why added |
|--|--|--|--|
| `tests/unit/test_init_claude_native.py` (strengthened) | T134 | 18 | B-1 — assert NO `.claude/rules/` post-init for Claude |
| `tests/test_copier_hooks.py` (rewrites) | T135 | 18 | B-1 — flip 8 refs from "exists" to "not exists" for plugin-native |
| `tests/test_cli.py` rewrites (T136) | T136 | 18 | B-1 — flip `test_init_force_profile`/`test_upgrade_force_calls_profile` |
| `tests/test_multi_repo_deploy.py:486-491` rewrite | T137 | 18 | B-1 — flip linked-secondary profile-exists assertion |
| `tests/unit/test_b1_linked_secondary_stale_profile.py` | T138 | 18 | B-1 — stale-profile trap regression (Codex round-3 trap) |
| `tests/contract/test_config_yml_emit.py` | T140 | 19 | B-2 — emit-side schema validation; replaces T005's contract-only check |
| `tests/unit/test_user_config_round_trip.py` | T141 | 19 | B-2 — UserConfig from_legacy_dict ↔ save_user_config round trip |
| `tests/contract/test_project_yml_emit.py` | T146 | 20 | B-3 — emit-side schema validation for `project.yml` |
| `tests/unit/test_init_required_field_strategy.py` | T147 | 20 | B-3 — `company`/`domain`/`side`/`dotnet_version` derivation at init |
| `tests/unit/test_check_raw_schema_validation.py` | T148 | 20 | B-4 — `check` raw-validates against schema, not legacy load_project |
| `tests/unit/test_b5_copilot_metadata_staleness.py` | T154 | 21 | B-5 — rename company → check reports stale |
| `tests/unit/test_b5_copilot_source_staleness.py` | T155 | 21 | B-5 — template change → check reports stale |
| `tests/unit/test_configure_multi_host_picker.py` | T132 | 17 | B-6 — interactive `configure` shows all 4 hosts |
| `.github/workflows/ci.yml::smoke` rewrite | T157-T160 | 22 | B-7 — 3-OS matrix + 4 binaries + preflight + 4 fixture files |
| (ruff cleanup is not a test — verified by `ruff check` exit 0) | T131 | 16 | B-8 |
| `tests/contract/test_agent_source_shape.py` | T161 | 23 | F-F — no host-allow-list fields at top level outside `host_overrides` |
| `tests/content/test_csharp_skill_snippets_compile.py` | T178 | 26 | Compile-check scaffold for C-Q1/C-Q2/C-Q4 fixes (per Codex r3 R5) |
| `tests/content/test_bin_wrappers.py` | T182 | 27 | OOS-003 — `bin/dotnet-ai --version` works on 3 OSes |
| `tests/fixtures/cursor_fixture_pending/` + test extension | T169 | 25 | OOS-005 pending-branch fixture (release-note neutralization) |
| `tests/unit/test_release_notes_consistency.py` rewrite | T168 | 25 | OOS-005 — assert pending state requires neutral language |
| `tests/contract/test_plugin_manifest_paths.py` | T196 | 29 | F6 — every manifest path resolves on disk |

## How to use this file

- When adding a new test, update the corresponding row to include it
- When removing or renaming a test, update the corresponding row
- CI gates: every cell SHOULD reference at least one automated test. Manual gates are documented at `checklists/verification.md`.
- Before merge: this file SHOULD be consulted to confirm every FR/SC/A has at least one passing test reference
