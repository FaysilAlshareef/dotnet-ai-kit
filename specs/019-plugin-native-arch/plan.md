# Implementation Plan: Plugin-Native Architecture

**Branch**: `019-plugin-native-arch` | **Date**: 2026-05-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/019-plugin-native-arch/spec.md`
**Status**: Draft v3 (post-round-3 plan-phase debate; all 27 round-2 + round-3 edits applied)
**Reviewers**: Claude (Opus 4.7, 1M context) + Codex (gpt-5.5 xhigh)

## Summary

Deliver the converged plugin-native architecture refactor agreed in `issues/plugin-native-architecture/FINAL-REPORT.md`. Three AI hosts with first-class plugin models (Claude Code, Codex CLI, Cursor) consume `dotnet-ai-kit` through native plugin manifests; GitHub Copilot consumes rendered repository-native instruction files at `.github/`. Per-solution footprint drops from ~180 files to a small fixed set (project metadata + user configuration + permissions merge, plus Copilot renders when enabled). Customization values resolve at runtime against current project metadata, not frozen at init time. The migration command uses the existing manifest hash tracking and 3-keep backup rotation to safely move legacy per-solution copies into a project-local backup folder. Validation centralizes plugin install + binary prerequisites + project schema + manifest integrity + Copilot freshness into a single `dotnet-ai check` invocation.

**Delivery**: single feature branch, **31 sequenced commits** total (Phase 1-9 commits 1-15 originally frozen at 15 in `issues/plugin-native-architecture/FINAL-REPORT.md` lines 87-106; commit 14b inserted during tasks-phase round-1 Codex review per `discussion/tasks-phase/round1-codex-reply.md` BLOCKER (c); Phase 10 commits 16-30 added during review-phase rounds 1-4 to close 8 BLOCKERS). Phase 1-9 order: `1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14b, 15`. Phase 10 order: `16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30`. No multi-PR split; per-commit reviewability is the mitigation for review burden. Pre-v1.0.0 status removes backward-compatibility tax. See "Review-Phase Outcome" section below for Phase 10 details.

## Technical Context

**Language/Version**: Python 3.10+ (CLI), bash for hooks (existing - no rewrite of the 4 existing hooks; one new SessionStart bootstrap + one new PreToolUse arch-profile hook)
**Primary Dependencies**: typer, pydantic v2, jinja2, pyyaml, rich (existing in `pyproject.toml`); jsonschema (new — project.yml + plugin.json schema validation); pytest + pytest-cov + ruff (`[dev]`); tiktoken or character-length fallback for SC-013 token counting
**Storage**:
- YAML: `.dotnet-ai-kit/config.yml` (user configuration), `.dotnet-ai-kit/project.yml` (project metadata)
- JSON: `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `.cursor-plugin/plugin.json` (plugin manifests); `.mcp.json` (MCP servers); `.dotnet-ai-kit/manifest.json` (managed-file manifest with SHA-256 per file, extended from feature 018's manifest); `schemas/*.schema.json` (JSON Schema files)
- Markdown: all skills, commands, rules, agents, profiles
**Testing**: pytest, four categories matching 018's pattern extended for multi-host:
- **Static checks** — frontmatter + grep + line-count assertions over `commands/`, `rules/`, `skills/`, `agents/`, `profiles/`, `hooks/`, `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`. Runs every commit (target ≤30s).
- **Unit tests** — Python module behaviour for `agent_generators.py` (new), `manifest.py` (extended), `hosts/*.py` (new), `cli.py` (new commands: `migrate`, `render`; modified: `init`, `upgrade`, `configure`, `check`), `copier.py` (refactored for plugin-native).
- **Smoke/transcript tests** — three host-specific fixtures per FR-029 / SC-008. Gated by per-host env vars (`CLAUDE_CODE_SMOKE`, `CODEX_SMOKE`, `CURSOR_SMOKE`) and host CLIs on PATH. Run nightly + on `[smoke]` PR label + as mandatory pre-merge gate (SC-008).
- **Packaging tests** — pip install from built distribution into isolated venv on Windows, macOS, Linux per A-010; assert every host-specific plugin manifest directory present in installed location (SC-009, FR-030).
**Target Platform**: Windows + macOS + Linux per spec A-010 (clarify Q2). CI matrix triples to three OSes for the expanded set per Codex plan-phase round-2 CP5 acceptance: FR-008 (unmanaged-path detection — Windows path-comparison gotchas), FR-017 (validation), FR-018 (migrate), FR-021 (backup-path separator handling), FR-029 (host smoke fixtures), FR-030 (packaging), FR-031/FR-032 (manifest path normalization), FR-033 (linked-repo absolute/relative paths), SC-013 (hook line-ending semantics). Constitution Check below.
**Project Type**: CLI tool + three host-specific plugin packages + Copilot render target (no plugin model)
**Performance Goals** (per spec SCs):
- SC-001: ≥90% file reduction (~180 → ≤18 per-solution files for plugin-only hosts; concretely target ≤10 baseline files + Copilot renders only when Copilot selected)
- SC-002: zero per-solution upgrade commands required for plugin-supporting hosts
- SC-004: ≥65% always-on context reduction; target band 2500–3000 tokens (was ~9000)
- SC-010: validation command <10s on developer workstation
- SC-012: render command <2s for Claude-host-shaped output
- SC-013: SessionStart bootstrap ≤500 tokens of stdout
**Constraints**:
- A-001 pre-v1.0.0: no backward-compatibility tax, but validation gates remain mandatory
- A-005 Cursor sub-agent fixture mandatory; full Cursor sub-agent generation conditional on fixture passing (binding scope branch)
- A-007 C# language-server binary external dependency
- A-010 cross-platform binding on all three OSes (clarify Q2)
- A-011 zero outbound network calls, zero telemetry (clarify Q5)
- Constitution v1.0.7 says 4 universal rules; spec FR-011 says 5 (adds `async-concurrency`) — Constitution Check violation requiring v1.0.8 amendment in this PR
- Clarify Q3: filesystem inspection only for plugin-install check; no host-CLI shell-out
- Clarify Q4: init without `--host` flag triggers interactive prompt; no silent defaults
**Scale/Scope** (verified file inventory at `2026-05-17`):
- 124 SKILL.md (no body changes; metadata refresh only where needed)
- 16 rules total → 5 conventions + 11 domain (FR-011)
- 12 profiles already split (7 microservice + 5 generic) — clarify Q1 preserves them
- 13 specialist agents (per CLAUDE.md "13 specialist agents")
- 27 commands (per CLAUDE.md table); none removed in this feature
- 6 hook scripts (4 existing kept; 2 new for SessionStart compact bootstrap + PreToolUse arch-profile)
- 3 plugin manifests (one per plugin host)
- 1 Copilot render template set (repo-wide + path-scoped + per-agent)
- 4 new Python modules (`agent_generators.py`, `manifest.py` extensions, `hosts/{claude,codex,cursor,copilot}.py`, `render.py`)
- 2 modified Python modules (`cli.py` for new commands, `copier.py` for plugin-native refactor)
- 1 packaging update (`pyproject.toml` adds `.codex-plugin/`, `.cursor-plugin/` to `[tool.hatch.build.targets.wheel.force-include]`)
- ~12 new JSON schema files (one per plugin manifest variant + project.yml + config.yml + manifest.json + hooks.json)

## Constitution Check

Evaluated against `.specify/memory/constitution.md` v1.0.7 (2026-05-16).

### I. Detect-First, Respect-Existing (NON-NEGOTIABLE) — ✅ PASS

The plugin-native refactor reuses existing detection logic. The migration command uses the existing managed-file manifest at `src/dotnet_ai_kit/cli.py:399-438` and existing backup rotation at `src/dotnet_ai_kit/cli.py:505-537`. FR-022 mandates preservation of user-modified files. FR-008 (clarify Q1 extended) treats every unmanaged path as user-owned; non-exhaustive list documented in A-008.

### II. Pattern Fidelity — ✅ PASS

All new Python code matches existing style: `pathlib.Path` not `os.path`, `subprocess.run([...])` without `shell=True`, pydantic v2 + `from __future__ import annotations`, explicit `encoding="utf-8"`, ruff-clean. New host-specific install logic under `src/dotnet_ai_kit/hosts/` mirrors the existing `AGENT_CONFIG` dispatch pattern in `agents.py`.

### III. Architecture & Platform Agnostic — ✅ PASS

A-010 binds all three OSes; CI matrix triples. All paths via `pathlib.Path`. No `shell=True`. No hardcoded `~`, `$HOME`, `%USERPROFILE%`, `/tmp`, or `%TEMP%`. Plugin-cache paths per host are abstracted behind `hosts/{claude,codex,cursor}.py` modules that compute paths from `Path.home()` + platform-specific subpath rules. Constitution III explicitly lists Cursor, Copilot, Codex as planned (now realized in this feature).

### IV. Best Practices & Quality — ✅ PASS

TDD enforced via per-commit test additions (each commit in the 16-commit order `1..14, 14b, 15` ships its failing tests first). SOLID respected in new modules. Documentation-first: host plugin docs were verified during architecture-phase (`issues/plugin-native-architecture/codex/final-merged-findings.md` "Verified facts that drove the design" table); Cursor's loader docs status will be re-verified in research.md before the spike commits. A-011 binds no network calls / no telemetry. FR-029 mandates host smoke fixtures as merge gates (SC-008 binding).

### V. Safety & Token Discipline — ⚠️ PASS-CONDITIONAL

- **Token budgets**: spec SC-004 mandates ≥65% always-on context reduction (target 2500–3000 tokens); spec SC-013 mandates SessionStart bootstrap ≤500 tokens. Verified by tokenizer count with character-length fallback.
- **File-size limits**: rules ≤100, commands ≤200, skills ≤400, agents ≤120, profiles ≤100 (constitution V). No file in this feature changes limit.
- **Rule classification**: constitution v1.0.7 says **4 universal rules** with whitelist `existing-projects`, `tool-calls`, `coding-style`, `security`. Spec FR-011 says **5 universal** adding `async-concurrency`. This is a documented governance change introduced by the architecture-phase cross-AI debate (`issues/plugin-native-architecture/codex/final-merged-findings.md:284-293`). **This is PASS-CONDITIONAL on commit 14's FIRST acceptance check**: `tests/unit/test_constitution_amendment.py` MUST PASS before the rule-reclassification step in commit 14 lands. The test asserts constitution version is `1.0.8` AND the universal whitelist includes `async-concurrency`. The amendment is governance, not implementation complexity, so it is NOT a Complexity Tracking entry (the row previously listing it has been removed in round-3 edits per Codex CP2 verdict).
- **`--dry-run` support**: `migrate` MUST support `--dry-run` (constitution V mandates it for every command; SC-007 protects user-modified files; `migrate` is the highest-risk new command). `render` is read-only, no `--dry-run` needed. `init`, `upgrade`, `configure`, `check` keep their existing `--dry-run` support.
- **Reversibility**: `migrate` backups under `.dotnet-ai-kit/backups/migrate/<timestamp>/` with 3-keep retention (FR-021, FR-023). `init --force` does NOT auto-migrate (FR-025).
- **No deploys**: feature touches no CI/CD or environment.
- **A-011 no-network**: constitution V mandates safety; A-011 strengthens to no outbound HTTP, no telemetry, no auto-update check.

**Verdict**: 4 gates ✅ PASS, 1 gate ⚠️ PASS-CONDITIONAL on commit 14 constitution amendment.

## Project Structure

### Documentation (this feature)

```text
specs/019-plugin-native-arch/
├── plan.md                         # This file
├── research.md                     # Phase 0 output (next step)
├── data-model.md                   # Phase 1 output
├── quickstart.md                   # Phase 1 output
├── contracts/                      # Phase 1 output (18 files: 7 schemas + 11 markdown contracts after round-3 expansion)
│   ├── claude-plugin.schema.json   # `.claude-plugin/plugin.json` schema (tightened lspServers)
│   ├── codex-plugin.schema.json    # `.codex-plugin/plugin.json` schema (REWRITE: scalar relative paths with `./`)
│   ├── cursor-plugin.schema.json   # `.cursor-plugin/plugin.json` schema (REWRITE: `agents` key + `./agents/`)
│   ├── project-yml.schema.json     # `.dotnet-ai-kit/project.yml` schema
│   ├── config-yml.schema.json      # `.dotnet-ai-kit/config.yml` schema (with `ai_tools` alias note)
│   ├── manifest-json.schema.json   # `.dotnet-ai-kit/manifest.json` schema (REWRITE: v1/v2 dual-read)
│   ├── hooks-json.schema.json      # `hooks/hooks.json` schema (REWRITE: event-keyed SessionStart/PreToolUse/PostToolUse)
│   ├── copilot-instructions.contract.md   # Copilot render contract (with --force-render opt-in)
│   ├── copilot-instructions-path.contract.md  # generated only for detected paths
│   ├── copilot-agent.contract.md   # expanded allow-list per current GitHub docs
│   ├── session-start-bootstrap.contract.md  # ≤500 tokens; 2000-char hard fallback
│   ├── pretooluse-arch-profile.contract.md  # PreToolUse runtime arch-profile contract
│   ├── agent-source.contract.md    # NEW — `agents-source/<name>.md` source-of-truth format
│   ├── check-cli.contract.md       # NEW — `dotnet-ai check` CLI + exit class enumeration
│   ├── migrate-cli.contract.md     # NEW — `dotnet-ai migrate` CLI + legacy read behavior
│   ├── render-cli.contract.md      # NEW — `dotnet-ai render` CLI + v1 Claude-only behavior
│   ├── linked-secondary.contract.md  # NEW — Linked-secondary writer footprint (FR-033)
│   └── cursor-fixture-decision.contract.md  # NEW — A-005 binding rule
├── traceability.md                 # FR → test mapping (NEW — 018 pattern; round-2 acceptance)
├── measurements.md                 # SC baseline + post-fix capture (NEW — 018 pattern; round-2 acceptance)
├── spec.md
├── checklists/
│   ├── requirements.md
│   └── verification.md
├── discussion/
│   ├── spec-phase/                 # closed; converged at round2-codex-verify.md
│   └── plan-phase/                 # this round's Codex discussion (created next)
└── tasks.md                        # Phase 2 (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/dotnet_ai_kit/
├── __init__.py                # __version__ — plugin_version for all 3 manifests
├── cli.py                     # MODIFIED: new `migrate`, `render` commands; refactored `init`, `upgrade`, `configure`, `check` for multi-host
├── config.py                  # MODIFIED: multi-host config schema (was Claude-only); pydantic validation
├── copier.py                  # MODIFIED: drop project-local copy paths for plugin-supporting hosts; keep Copilot render path; linked-secondary-repo writer (existing at cli.py:882-1202 per merged-findings) constrained per FR-033
├── models.py                  # MODIFIED: pydantic models for ProjectMetadata, UserConfig, ManagedFile, etc. Existing 12 project_type values preserved (clarify Q1)
├── agents.py                  # MODIFIED: `AGENT_FRONTMATTER_MAP` deleted (R1 resolution); `SUPPORTED_AI_TOOLS` expanded from `{"claude"}` to all 4
├── agent_generators.py        # NEW: per-host generators — `generate_claude_agent()`, `generate_codex_agent()` (no-op for v1; OOS-004), `generate_cursor_agent()`, `generate_copilot_agent()`
├── manifest.py                # NEW: extended managed-file manifest with SHA-256 per file, supports `migrate` classification + `check` integrity
├── render.py                  # NEW: `dotnet-ai render <skill|rule>` implementation; Claude-host-shaped output in v1
├── hosts/                     # NEW package: per-host install/detect/check
│   ├── __init__.py
│   ├── base.py                # Abstract Host base class
│   ├── claude.py              # Claude Code: plugin-cache path detection on Win/macOS/Linux, install verification (filesystem only per clarify Q3)
│   ├── codex.py               # Codex CLI: skills + MCP + hooks; no native agents per OOS-004
│   ├── cursor.py              # Cursor: rules + sub-agent spike fixture loader detection
│   └── copilot.py             # GitHub Copilot: render orchestrator (no plugin model per FR-004)
├── detection.py               # UNCHANGED in core logic
└── extensions.py              # UNCHANGED (extensions subsystem OOS per OOS-002)

.claude-plugin/                # MODIFIED
└── plugin.json                # `agents` field added (was missing per merged-findings); `lspServers` references `csharp-lsp` after commit 11

.codex-plugin/                 # NEW directory + manifest
└── plugin.json                # Skills + MCP + hooks only (no native agents per OOS-004)

.cursor-plugin/                # NEW directory + manifest
└── plugin.json                # Rules + sub-agent spike fixture; full sub-agent set conditional on A-005 / SC-008

skills/                        # UNCHANGED — 124 skills; references convention rules via ${CLAUDE_PLUGIN_ROOT}/rules/conventions/
commands/                      # UNCHANGED — 27 commands; bare names exposed via plugin namespace
agents-source/                 # MODIFIED — renamed from agents/ in commit 4 (per round-3 P2 resolution). Source-of-truth markdown bodies (one per logical agent). 13 specialist agents. Host-specific build outputs generated from here.

agents-claude/                 # NEW — generated at build by `generate_claude_agent()`; referenced by `.claude-plugin/plugin.json` `agents` field
agents/                        # MODIFIED (was source-of-truth pre-019; now Cursor build output per round-3 P2 resolution) — generated by `generate_cursor_agent()` if Cursor spike passes. Referenced by `.cursor-plugin/plugin.json` `agents: "./agents/"` per verified Cursor evidence.
agents-copilot-templates/      # NEW — jinja2 templates for `.github/agents/*.agent.md` rendering

rules/
├── conventions/               # NEW directory — 5 always-on (FR-011): async-concurrency, coding-style, existing-projects, security, tool-calls
├── domain/                    # NEW directory — 11 JIT (FR-011): api-design, architecture, configuration, data-access, error-handling, localization, multi-repo, naming, observability, performance, testing
└── cursor/*.mdc               # MODIFIED — generated Cursor rule format (was: one blob `.cursor/rules/dotnet-ai-kit.mdc` per merged-findings:94)

profiles/                      # UNCHANGED — clarify Q1 preserves 7 microservice + 5 generic

hooks/
├── hooks.json                 # MODIFIED — adds SessionStart compact bootstrap entry + PreToolUse arch-profile entry; existing 4 hooks untouched
├── pre-bash-guard.sh          # UNCHANGED (from feature 018)
├── pre-commit-lint.sh         # UNCHANGED (from feature 018)
├── post-edit-format.sh        # UNCHANGED (from feature 018)
├── post-scaffold-restore.sh   # UNCHANGED (from feature 018)
├── session-start-bootstrap.sh # MODIFIED — replaced with ≤500-token compact bootstrap; outputs index pointing to project.yml + `dotnet-ai check` (SC-013)
└── pretooluse-arch-profile.sh # NEW — reads project.yml at fire-time, emits architecture-profile-specific context (FR-034)

.mcp.json                      # MODIFIED — `csharp-ls` REMOVED only after commit 11 (`csharp-lsp` plugin dependency lands and CHK009-CHK011 pass in CI); `codebase-memory-mcp` retained

schemas/                       # NEW directory
├── claude-plugin.schema.json
├── codex-plugin.schema.json
├── cursor-plugin.schema.json
├── project-yml.schema.json
├── config-yml.schema.json
├── manifest-json.schema.json
└── hooks-json.schema.json

pyproject.toml                 # MODIFIED — [tool.hatch.build.targets.wheel.force-include] adds `.codex-plugin/`, `.cursor-plugin/`, `agents-source/`, `agents-claude/`, `agents/` (Cursor build output), `agents-copilot-templates/`, `rules/conventions/`, `rules/domain/`, `rules/cursor/`, `schemas/`. `.claude-plugin/` and `hooks/` already included from feature 018.

.github/workflows/ci.yml       # MODIFIED — adds Windows + macOS + Linux matrix for FR-017/FR-018/FR-029/FR-030 per A-010; nightly job gates SC-008 host smoke fixtures

tests/
├── contract/                  # NEW — spec contract tests
│   ├── test_claude_plugin_schema.py     # plugin.json structural conformance
│   ├── test_codex_plugin_schema.py      # scalar relative paths with `./` prefix
│   ├── test_cursor_plugin_schema.py     # `agents` (not `subagents`) + `./agents/` path
│   ├── test_project_yml_schema.py
│   ├── test_config_yml_schema.py        # includes `ai_tools` alias migration
│   ├── test_manifest_schema.py          # v1 read + v2 read/write per R11/R16
│   ├── test_hooks_schema.py             # event-keyed object (SessionStart/PreToolUse/PostToolUse)
│   └── test_mcp_csharp_removed.py       # NEW per round-3 — commit-12 contract test
├── integration/               # NEW — host smoke fixtures + packaging
│   ├── test_packaging_windows.py        # CI matrix only on Windows
│   ├── test_packaging_macos.py          # CI matrix only on macOS
│   # Linux/default packaging coverage = existing tests/test_packaging.py (feature 018, extended in commit 2)
│   ├── test_smoke_claude.py             # SC-008 host smoke (FR-029) — CHK001
│   ├── test_smoke_claude_lsp.py         # NEW per round-3 — CHK011 LSP fixture transcript
│   ├── test_smoke_codex.py              # SC-008 host smoke (FR-029) — CHK002
│   └── test_smoke_cursor.py             # SC-008 host smoke (FR-029) — CHK003/CHK004
├── unit/                      # extended from existing tests/
│   ├── test_agent_generators.py         # FR-026, FR-027 — no field leak per host; no skill-preload regression
│   ├── test_manifest_integrity.py       # FR-032
│   ├── test_migrate_classification.py   # FR-020, FR-022, SC-007
│   ├── test_migrate_backup_rotation.py  # FR-021, FR-023
│   ├── test_check_filesystem_inspection.py  # clarify Q3 — filesystem-only, no shell-out
│   ├── test_init_force_prints_migrate.py # FR-025
│   ├── test_pretooluse_arch_profile.py  # FR-034 — CHK046/047/048
│   ├── test_session_start_budget.py     # SC-013 token count
│   ├── test_no_network_no_telemetry.py  # A-011 — assert no `requests`, no `urllib.request.urlopen`, etc.
│   ├── test_constitution_amendment.py   # PASS-CONDITIONAL gate (commit 14 first acceptance check)
│   ├── test_a009_host_symmetry.py       # NEW — per-host smoke fixtures required
│   ├── test_unmanaged_paths_untouched.py  # FR-008, A-008 baseline
│   ├── test_fr008_unmanaged_paths_parameterized.py  # NEW per round-2 — A-008 list × every write command
│   ├── test_fr011_fr012_jit_loading.py  # NEW per round-2 — JIT load triggers
│   ├── test_rule_classification.py      # FR-011/012 exact 5/11 split
│   ├── test_no_arch_branching_in_always_on.py  # NEW — error-handling/naming NOT in always-on
│   ├── test_fr014_fr016_init_e2e.py     # NEW per round-2 — interactive prompt + selected-host-only writes
│   ├── test_fr015_fr024_upgrade_separation.py  # NEW per round-2 — plugin no-op vs Copilot re-render
│   ├── test_fr019_render_cases.py       # NEW per round-2 — success/missing/stale/Claude-shape/<2s
│   ├── test_fr020_host_owner_all_values.py     # NEW per round-2 — 4 host_owners + null + legacy inference
│   ├── test_fr029_cursor_fail_path.py   # NEW per round-2 — Cursor fixture fail triggers scope-revision
│   ├── test_fr031_exit_classes.py       # NEW per round-2 — unique exit class per broken state
│   ├── test_fr032_manifest_actionable_output.py  # NEW per round-2
│   ├── test_fr033_linked_secondary_init.py     # NEW per round-2 — FR-033, SC-014
│   ├── test_fr033_linked_secondary_migrate.py  # NEW per round-2 — FR-033, SC-014
│   ├── test_fr035_host_admission_static_guard.py  # NEW per round-2
│   ├── test_runtime_resolution.py       # FR-009/010
│   ├── test_init_claude_native.py       # commit 4 acceptance
│   ├── test_init_interactive_prompt.py  # clarify Q4 baseline (paired with test_fr014_fr016_init_e2e.py)
│   ├── test_copilot_render.py           # FR-007 / SC-006 structural parity
│   ├── test_cursor_rules_per_file.py    # commit 6 — assert no one-blob output
│   ├── test_sc001_file_count.py         # NEW per round-2 — fixture-based before/after
│   ├── test_sc002_two_solution_propagation.py  # NEW per round-2
│   ├── test_sc003_runtime_resolution_points.py  # NEW per round-2 — all runtime points observe rename
│   ├── test_sc005_no_duplicate_claude_listings.py  # NEW per round-2
│   ├── test_sc010_check_runtime.py      # NEW per round-2 — perf budget
│   ├── test_sc012_render_runtime.py     # NEW per round-2 — perf budget
│   └── test_sc013_tokenizer_and_fallback.py  # NEW per round-2 — both tokenizer + fallback paths
└── conftest.py                # extended for per-host smoke env-gating

scripts/
└── check.py                   # EXTENDED from 018 — adds plugin-manifest packaging assertion + multi-host config validation

.dotnet-ai-kit/                # Per-project deployment artifact, not in plugin repo. After init:
                               #   config.yml                          (existing)
                               #   project.yml                         (existing)
                               #   manifest.json                       (existing from 018, extended for plugin-native)
                               #   backups/upgrade/<run_id>/           (existing from 018)
                               #   backups/migrate/<timestamp>/        (NEW — FR-021)
                               #   .gitignore                          (existing)
```

**Structure Decision**: Continue the existing flat `src/dotnet_ai_kit/` package layout. Introduce one new package (`hosts/`) for per-host concerns to keep the dispatch surface coherent. New modules (`agent_generators.py`, `render.py`, `manifest.py` extensions) follow the single-responsibility pattern from 018. The plugin source root grows by three manifest directories (`.codex-plugin/`, `.cursor-plugin/`) plus rule sub-directories (`rules/conventions/`, `rules/domain/`). Existing `.claude-plugin/` and `hooks/` directories are kept and extended.

## Complexity Tracking

| Violation / Complexity | Why Needed | Simpler Alternative Rejected Because |
|--|--|--|
| Three plugin manifests in one repo (`.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`) | Each host's documented plugin model has different manifest fields; merged-findings table verified at architecture-phase | One unified manifest format does not exist across hosts; runtime translation defeats per-host smoke fixture clarity |
| Cross-platform CI matrix tripled for FR-017/FR-018/FR-029/FR-030 | A-010 binds all three OSes (clarify Q2); host plugin-cache paths differ per OS; smoke fixtures need real host CLIs which behave differently | Single-OS CI hides path-handling regressions; CLAUDE.md convention 2 already mandates cross-platform; cost is bounded by smoke fixtures being minimal |
| Cursor sub-agent fixture conditional scope (A-005, OOS-005) | Cursor's loader docs do not yet describe sub-agent file layout precisely; the architecture-phase verified marketplace announcement but the loader spec is incomplete | Committing unconditionally risks shipping a non-loading capability as "supported"; abandoning Cursor sub-agents loses verified marketplace primitive |
| Legacy manifest compatibility (schema_version + host_owner inference) | Feature 018 manifests exist in dogfood repos; migration must read them without breakage | New schema rejecting v1 manifests forces a separate pre-migration step or breaks dogfood workflows; v1/v2 dual-read is the converged design (research R11/R16) |
| Host-doc volatility for plugin-cache paths (R7) | Per-OS plugin-cache paths depend on host-published docs that may shift between commits 4–10 | Hardcoding paths without re-verification leads to silent breakage; re-verify-before-commit gate adds explicit owner per commit |
| Linked-secondary writer refactor through host adapters | `copier.py:1090-1147` is the FR-033 back door; the bulk-copy paths must be deleted, not just "constrained" | Leaving the writer as-is preserves the legacy per-solution copy architecture in sibling repos, violating SC-014 |
| New `hosts/` package + new `agent_generators.py` + new `manifest.py` extensions + new `render.py` | Per-host install/detect/check logic differs structurally; single dispatch table is the architecture-phase R1 resolution | Generic runtime field map (the deleted `AGENT_FRONTMATTER_MAP`) earned nothing for non-Claude hosts; explicit per-host generators are the converged decision |
| Two new hook scripts (SessionStart compact bootstrap + PreToolUse arch-profile) on top of existing 4 hooks | SessionStart contract is ≤500 tokens (SC-013); PreToolUse arch-profile resolves at fire-time (FR-034); these are different fire events and cannot share a script | One mega-hook concatenating both responsibilities increases failure surface; existing 4 hooks remain untouched for stability |
| Linked-secondary-repository constraint (FR-033, SC-014) | Existing writer at `copier.py:882-1202` could preserve the legacy copy architecture as a back door per merged-findings; the architecture monitor is OOS-006 but the back door is not | Leaving the writer unchanged means plugin-served-artifact drift is only solved for primary repos; FR-033 closes the back door without shipping the deferred monitor |

All other plan choices flow directly from the spec's FRs and clarify Q1-Q5 — no other complexity needs justification beyond what the FRs already demand.

## Phase 0: Outline & Research

See `research.md` (generated in the same drop as this plan; finalized before Codex round 1).

Research tasks (consolidated; some already resolved during architecture-phase):

- **R1 (resolved during architecture-phase)**: Claude Code plugin manifest schema, including `agents`, `skills`, `commands`, `hooks`, `mcpServers`, `lspServers`, `outputStyles`, `dependencies`, `userConfig`, `channels` fields. Source: `https://code.claude.com/docs/en/plugins-reference` lines 365-485. Confirmed in `issues/plugin-native-architecture/codex/final-merged-findings.md:45`.
- **R2 (resolved during architecture-phase)**: Codex CLI plugin schema = `.codex-plugin/plugin.json` + `skills/` + `.mcp.json` + `hooks/hooks.json` + `.app.json` + `assets/`. No `agents/`, LSP, monitors, settings, bin. Source: `https://developers.openai.com/codex/plugins/build` lines 811-836.
- **R3 (resolved during architecture-phase)**: Cursor plugin packages subagents per `https://cursor.com/blog/marketplace/` lines 268-273 and `https://github.com/cursor/plugins` lines 288-297. Cursor rules use `.mdc` format.
- **R4 (re-verify before commit 6 ships)**: Cursor sub-agent **loader behaviour** — does the docs site or plugin registry now publish the file-layout spec for sub-agent discovery? Last verified at architecture-phase round 1: marketplace announces, loader-layout undocumented. A-005 gates full Cursor sub-agent generation on the fixture passing; if loader docs land before commit 6, the fixture can use them; otherwise the fixture relies on the marketplace registry's `agent-compatibility` plugin file shape as the reference. Source: `https://cursor.com/marketplace/cursor/agent-compatibility` lines 45-55.
- **R5 (resolved during architecture-phase)**: GitHub Copilot custom agents at `.github/agents/*.agent.md`. Source: `https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli` lines 542-550. Repo-wide instructions at `.github/copilot-instructions.md`. Path-scoped at `.github/instructions/*.instructions.md`. Source: `https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot` lines 730-735.
- **R6 (resolved during architecture-phase)**: `csharp-lsp` plugin requires `csharp-ls` binary on PATH. Source: `https://code.claude.com/docs/en/discover-plugins` lines 131-155.
- **R7 (plan-phase needed)**: Per-OS plugin-cache directories for each host (clarify Q3 requires filesystem inspection):
  - Claude Code: documented at `~/.claude/plugins/cache/` (verified via live disk inspection during architecture-phase: `~/.claude/plugins/cache/claude-plugins-official/coderabbit/1.1.1/`). Re-verify on each OS (`%USERPROFILE%\.claude\plugins\cache\` on Windows).
  - Codex CLI: needs Codex plugin install docs lookup — likely `~/.codex/plugins/` or similar. Source: `https://developers.openai.com/codex/plugins/build` install section.
  - Cursor: needs Cursor plugin docs lookup — likely `~/.cursor/plugins/` or similar. Source: `https://github.com/cursor/plugins` repository structure.
- **R8 (plan-phase needed)**: Token-counting library for SC-004 and SC-013 verification on Windows/macOS/Linux. Candidates: `tiktoken` (Python wrapper, requires Rust build chain — Windows tested?), character-length fallback (chars ÷ 4 = tokens approximation). Decision: use `tiktoken` when available; fall back to character-length × 0.25 otherwise. Pin a measurement methodology in `tests/unit/test_session_start_budget.py`.
- **R9 (plan-phase needed)**: JSON schema validation library. Candidates: `jsonschema` (mature, cross-platform, no compiled deps). Pin to a minimum version; add to `pyproject.toml` dependencies.
- **R10 (plan-phase needed)**: Cross-platform binary-on-PATH detection for `csharp-ls`. Use `shutil.which()` from stdlib; verified cross-platform. Document in `hosts/claude.py` LSP check helper.
- **R11 (plan-phase needed)**: Manifest hash algorithm. Feature 018 introduced SHA-256 per file in `.dotnet-ai-kit/manifest.json`. This feature reuses that exact format; no new algorithm. Verify the existing format covers Copilot rendered files (it does per current `manifest.json` shape).
- **R12 (plan-phase needed)**: Cursor's existing one-blob `.cursor/rules/dotnet-ai-kit.mdc` migration path. Existing code at `copier.py:231-272` (per merged-findings). Plan: drop the one-blob path; emit per-rule `.cursor/rules/<name>.mdc` files. Migrate users via `migrate` command (existing one-blob file gets backed up if it matches the legacy hash).
- **R13 (plan-phase needed)**: Codex CLI's stub today writes root `AGENTS.md` (per merged-findings:95 + `agents.py:51`). Plan: remove that code path entirely; root `AGENTS.md` becomes user-owned (FR-008 / A-008 binding).

**Output**: `research.md` with R1–R13 resolutions and the verified URLs/lines.

## Phase 1: Design & Contracts

See `data-model.md`, `contracts/`, `quickstart.md`.

**Entities** (full schemas in `data-model.md`):

- `PluginManifest` (3 variants for Claude / Codex / Cursor): host name, version, primitive fields per host
- `ProjectMetadata` (was nested-yaml; now schema-validated per FR-017): company, domain, side, project_type (one of 12 per clarify Q1), detected_paths, architecture_profile_name
- `UserConfig`: enabled_hosts (subset of 4), retention, permission_profile
- `ManagedFile` (extended from 018): path, sha256, plugin_version, deployed_at, source_template, **host_owner** (NEW — which host's render this is; null for non-host-specific managed files)
- `Manifest` (extended): plugin_version, created_at, last_upgrade_at, files
- `MigrationBackup` (NEW): timestamp, original_path, original_sha256, classification (`clean` | `user-modified`)
- `Agent` (new generation model): name, body, host_overrides (per-host frontmatter additions/exclusions)
- `Rule` (subtypes): `ConventionRule` (always-on, 5 instances) and `DomainRule` (JIT, 11 instances)
- `ArchitectureProfile`: name (one of 12), branch (microservice|generic), body
- `SmokeFixture` (per host): host_name, fixture_path, expected_listing_path, verification_command
- `LinkedSecondaryRepo` (constrained by FR-033): primary_repo_path, secondary_repo_path, hosts_selected

**Contracts** (in `contracts/`):

- `claude-plugin.schema.json` — schema for `.claude-plugin/plugin.json` (all manifest fields)
- `codex-plugin.schema.json` — schema for `.codex-plugin/plugin.json` (skills + MCP + hooks only)
- `cursor-plugin.schema.json` — schema for `.cursor-plugin/plugin.json` (skills + rules + sub-agent fixture)
- `project-yml.schema.json` — schema for `.dotnet-ai-kit/project.yml` (FR-017 validation target)
- `config-yml.schema.json` — schema for `.dotnet-ai-kit/config.yml`
- `manifest-json.schema.json` — schema for `.dotnet-ai-kit/manifest.json` (FR-032 integrity verification target)
- `hooks-json.schema.json` — schema for `hooks/hooks.json` (existing 4 + 2 new)
- `copilot-instructions.contract.md` — repository-wide Copilot render contract (FR-007)
- `copilot-instructions-path.contract.md` — path-scoped Copilot render contract (FR-007)
- `copilot-agent.contract.md` — per-agent `.github/agents/*.agent.md` contract (FR-007)
- `session-start-bootstrap.contract.md` — ≤500 token compact bootstrap format (SC-013, FR-013)
- `pretooluse-arch-profile.contract.md` — PreToolUse runtime arch-profile contract (FR-034)

**Quickstart** (`quickstart.md`):

- Install the plugin via host-native install (per host: `/plugin install dotnet-ai-kit` for Claude; equivalent for Codex; `/add-plugin dotnet-ai-kit` for Cursor)
- `dotnet-ai init` in your .NET solution → interactive host selection → minimal files written
- `dotnet-ai check` to verify state
- Slash commands (`/dotnet-ai-kit:do`, etc.) available immediately
- For Copilot users: `.github/` files rendered automatically; `dotnet-ai upgrade --copilot` refreshes
- Migration from old layout: `dotnet-ai migrate` with `--dry-run` first
- Inspection: `dotnet-ai render <skill|rule>`

## Commit-by-Commit Implementation Map

The original 15-commit order is frozen in `issues/plugin-native-architecture/FINAL-REPORT.md` lines 87-106. **Tasks-phase round 1 added commit 14b for `render`** per Codex's PUSH-BACK-WITH-EVIDENCE; final binding sequence is `1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14b, 15` (16 commits). Each commit ships its tests in the same commit.

### Commit 1 — Expand `SUPPORTED_AI_TOOLS` frozenset + multi-host config tests

**Touches**: `src/dotnet_ai_kit/agents.py:57` (expand frozenset from `{"claude"}` to `{"claude", "codex", "cursor", "copilot"}`), `tests/test_agents.py:31-33` (update Claude-only assertions to multi-host contract), `src/dotnet_ai_kit/models.py` (multi-host config schema).

**FRs**: FR-016 (configure UI multi-host), supporting all later commits.
**Tests**: `tests/test_agents.py` (updated), `tests/contract/test_config_yml_schema.py` (new), `tests/unit/test_init_interactive_prompt.py` (new — for clarify Q4 binding).

**Acceptance**: `pytest tests/` shows the supported set is 4; configure flow shows all 4 hosts as selectable; init without `--host` triggers the interactive prompt.

### Commit 2 — Update `pyproject.toml` packaging to include `.codex-plugin/`, `.cursor-plugin/`

**Touches**: `pyproject.toml` (`[tool.hatch.build.targets.wheel.force-include]`). Adds `.codex-plugin/`, `.cursor-plugin/`, `agents-source/`, `agents-claude/`, `agents/` (Cursor build output per round-3 P2 — was `agents-cursor/` in earlier draft), `agents-copilot-templates/`, `rules/conventions/`, `rules/domain/`, `rules/cursor/`, `schemas/`. `.claude-plugin/` and `hooks/` already included from feature 018.

**FRs**: FR-003 (distribution package includes all host manifests), FR-030 (packaging test).
**Tests**: `tests/test_packaging.py` (existing from feature 018 — Linux/default matrix entry; extended in commit 2 to assert the new manifest directories per tasks.md T006), `tests/integration/test_packaging_macos.py` (new — macOS CI matrix), `tests/integration/test_packaging_windows.py` (new — Windows CI matrix). All three run on their matching CI matrix OS. **Linux/default packaging coverage remains in the existing `tests/test_packaging.py` to avoid duplicating the feature-018 wheel-content baseline.**

**Acceptance**: `python -m build` produces wheel containing all three manifest directories at the installed location on Windows + macOS + Linux.

### Commit 3 — Add `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/` manifests

**Touches**: `.claude-plugin/plugin.json` (add `agents` field that was missing; preserve existing structure); new `.codex-plugin/plugin.json`; new `.cursor-plugin/plugin.json`. Schema files: new `schemas/claude-plugin.schema.json`, `schemas/codex-plugin.schema.json`, `schemas/cursor-plugin.schema.json`.

**FRs**: FR-001 (host-native plugin packages), FR-002 (only documented primitives per host).
**Tests**: `tests/contract/test_claude_plugin_schema.py`, `tests/contract/test_codex_plugin_schema.py`, `tests/contract/test_cursor_plugin_schema.py`.

**Acceptance**: each manifest validates against its schema; Claude manifest has `agents` (array); Codex manifest has no `agents`/`lspServers`/`monitors`/`settings`/`bin` and uses scalar relative paths with `./` prefix; Cursor manifest uses scalar relative paths (`skills`, `rules`, `mcpServers`, `hooks`) plus a conditional `agents: "./agents/"` (NOT `subagents`) per the verified Cursor evidence — conditional emission is gated by the A-005 spike outcome.

### Commit 4 — Claude plugin-native init

**Touches**: `src/dotnet_ai_kit/cli.py` (refactor `init` for Claude path); `src/dotnet_ai_kit/copier.py` (drop `.claude/commands/`, `.claude/skills/`, `.claude/agents/` copy paths); `src/dotnet_ai_kit/hosts/claude.py` (new module with install detection + permissions merge logic).

**FRs**: FR-005 (per-solution file list), FR-006 (no project-local plugin-served copies), FR-014 (init thin host-aware setup).
**Tests**: `tests/unit/test_init_claude_native.py` (new), `tests/integration/test_smoke_claude.py` (FR-029 host smoke).

**Acceptance**: `dotnet-ai init` with Claude selected writes exactly `.dotnet-ai-kit/config.yml`, `.dotnet-ai-kit/project.yml`, `.claude/settings.json` (permissions merge only). No `.claude/commands/`, no `.claude/skills/`, no `.claude/agents/` directories created. SC-001 measurement passes.

### Commit 5 — Codex documented primitives

**Touches**: `src/dotnet_ai_kit/copier.py` (drop `copy_commands_codex` root-AGENTS.md emitter at `copier.py:276-317` per merged-findings:95); `src/dotnet_ai_kit/hosts/codex.py` (new module); `src/dotnet_ai_kit/agents.py:51` (remove `AGENT_CONFIG["codex"]["agents_file"] = "AGENTS.md"`).

**FRs**: FR-002 (only documented primitives), FR-008 (unmanaged paths untouched — root `AGENTS.md` is user-owned).
**Tests**: `tests/integration/test_smoke_codex.py` (FR-029 host smoke), `tests/unit/test_unmanaged_paths_untouched.py` (assert root `AGENTS.md` is never written/modified).

**Acceptance**: `dotnet-ai init` with Codex selected does NOT write root `AGENTS.md`; root `AGENTS.md` left untouched if developer-authored.

### Commit 6 — Cursor rules + sub-agent spike

**Touches**: `src/dotnet_ai_kit/copier.py:231-272` (drop one-blob `.cursor/rules/dotnet-ai-kit.mdc`; emit per-rule `.cursor/rules/<name>.mdc`); `src/dotnet_ai_kit/hosts/cursor.py` (new module); `.cursor-plugin/plugin.json` (`agents: "./agents/"` field added conditionally); `agents/<one-fixture>.md` (single sub-agent fixture in the Cursor build-output directory per round-3 P2 resolution).

**FRs**: FR-001 (Cursor plugin), A-005 + SC-008 binding (fixture mandatory, full generation conditional).
**Tests**: `tests/integration/test_smoke_cursor.py` (FR-029 host smoke; gates A-005 outcome), `tests/unit/test_cursor_rules_per_file.py` (assert no one-blob output).

**Acceptance**: Cursor sees the sub-agent fixture; per-rule `.mdc` files exist; spike outcome recorded in `discussion/plan-phase/cursor-spike-outcome.md`. If fixture fails, A-005 binding triggers — full Cursor sub-agent generation removed from this release; spec/plan revised accordingly.

### Commit 7 — Copilot GitHub-native render

**Touches**: `src/dotnet_ai_kit/copier.py` (Copilot render orchestrator); `src/dotnet_ai_kit/hosts/copilot.py` (new module); `agents-copilot-templates/` (new jinja2 templates for `.github/agents/*.agent.md`).

**FRs**: FR-004 (Copilot support via render), FR-007 (3 logical content classes: repo-wide + path-scoped + per-agent), FR-015 (Copilot-targeted upgrade variant).
**Tests**: `tests/unit/test_copilot_render.py` (assert 3 logical content classes; verify path-scoped routes match project structure), `tests/contract/test_copilot_instructions.py`, `tests/contract/test_copilot_instructions_path.py`, `tests/contract/test_copilot_agent.py`.

**Acceptance**: `dotnet-ai init` with Copilot selected renders all three logical content classes at Copilot-native paths; `dotnet-ai upgrade --copilot` re-renders against current project metadata.

### Commit 8 — `project.yml` JSON schema + validation

**Touches**: `src/dotnet_ai_kit/models.py` (extend pydantic models to expose JSON schema); `schemas/project-yml.schema.json` (new); `tests/contract/test_project_yml_schema.py` (new). Add `jsonschema` to `pyproject.toml` dependencies.

**FRs**: FR-017 (validation command verifies schema), CHK013-CHK015 (verification.md schema checks).
**Tests**: `tests/contract/test_project_yml_schema.py`, `tests/unit/test_project_yml_validation.py`.

**Acceptance**: invalid `project.yml` files (schema-violations, missing required fields, unknown project_type) fail validation; the 12 valid project_type values from clarify Q1 pass.

### Commit 9 — `check` host-specific validations

**Touches**: `src/dotnet_ai_kit/cli.py` (add/refactor `check` command); `src/dotnet_ai_kit/hosts/{claude,codex,cursor,copilot}.py` (each gets a `verify_install()` method using filesystem inspection per clarify Q3); `src/dotnet_ai_kit/manifest.py` (manifest integrity check per FR-032).

**FRs**: FR-017 (validation scope), FR-031 (exit status uniquely identifies failing check class), FR-032 (manifest integrity), SC-010 (<10s), SC-011 (csharp-ls detection).
**Tests**: `tests/unit/test_check_filesystem_inspection.py`, `tests/unit/test_manifest_integrity.py`, `tests/unit/test_fr031_exit_classes.py`, `tests/unit/test_fr032_manifest_actionable_output.py`, `tests/unit/test_sc010_check_runtime.py`.

**Acceptance**: `dotnet-ai check` reports plugin install per configured host (filesystem inspection only — no shell-out per clarify Q3), C# language-server binary status, project metadata schema status, detected-path correctness, Copilot render freshness, manifest integrity. Exit zero on healthy, non-zero with unique class identifier on any failure. Runtime <10s. CLI surface includes `--verbose`, `--json`, `--host <host>` flags per `contracts/check-cli.contract.md:12-20`.

**Note**: FR-019 / SC-012 (`render` command) is NOT in this commit — `render` is commit 14b (after commit 14's rule layout is finalized) per tasks-phase round-1 Codex feedback. FR-034 PreToolUse arch-profile validation is implemented by commit 13's hook; commit 9's `check` does not re-implement it (`contracts/check-cli.contract.md:22-33` enumerates the 6 check classes — PreToolUse profile is NOT one of them).

### Commit 10 — Manifest-driven `migrate` command + backup rotation

**Touches**: `src/dotnet_ai_kit/cli.py` (new `migrate` command); `src/dotnet_ai_kit/manifest.py` (extend for classification); migrate uses existing manifest hash tracking at `cli.py:399-438` and existing backup rotation at `cli.py:505-537`.

**FRs**: FR-018 (migrate exists), FR-020 (hash classification), FR-021 (project-local backup), FR-022 (preserve user-modified), FR-023 (3-keep rotation), FR-024 (no Copilot re-render), FR-025 (init --force prints migrate invocation).
**Tests**: `tests/unit/test_migrate_classification.py`, `tests/unit/test_migrate_backup_rotation.py`, `tests/unit/test_init_force_prints_migrate.py`.

**Acceptance**: `dotnet-ai migrate` on a solution with mixed clean/user-modified files moves clean files to `.dotnet-ai-kit/backups/migrate/<timestamp>/` and preserves modified files in place. `dotnet-ai init --force` detects shadowed legacy artifacts and prints the exact `dotnet-ai migrate` invocation without auto-deleting. Backup folder rotation keeps 3 most recent. Migrate supports `--dry-run`.

### Commit 11 — `csharp-lsp` plugin dependency added

**Touches**: `.claude-plugin/plugin.json` (add `csharp-lsp` to `dependencies` field).

**FRs**: FR-028 (C# diagnostics via language-server primitive), CHK010 (LSP dependency declared), A-007 (external binary).
**Tests**: `tests/contract/test_claude_plugin_schema.py` (assert `dependencies` includes `csharp-lsp`), `tests/integration/test_smoke_claude_lsp.py` (NEW per round-3 — explicit fixture transcript proving edit-time diagnostics surface; CHK011).

**Acceptance**: Claude Code plugin install pulls `csharp-lsp` dependency; `dotnet-ai check` reports `csharp-ls` binary status (CHK009); `test_smoke_claude_lsp.py` produces a transcript artifact showing C# diagnostics surfaced at edit time (not via explicit AI tool invocation), satisfying CHK011.

### Commit 12 — Remove `csharp-ls` from `.mcp.json` (only after step 11 verified in CI)

**Touches**: `.mcp.json` (remove `csharp-ls` server entry; preserve `codebase-memory-mcp`).

**FRs**: FR-028 (C# moves off MCP), CHK012 (gated on CHK009-CHK011 passing).
**Tests**: `tests/contract/test_mcp_csharp_removed.py` (NEW per round-3 — explicit contract test asserting `.mcp.json` removes only `csharp-ls` and retains `codebase-memory-mcp` per `issues/plugin-native-architecture/codex/final-merged-findings.md:195`); CI gate enforces "do not merge commit 12 unless CHK009, CHK010, CHK011 are all green in this PR's CI run."

**Acceptance**: `.mcp.json` no longer contains `csharp-ls`; `codebase-memory-mcp` retained (asserted by contract test); CI fails if commit 12 is included without commit 11's checks passing.

### Commit 13 — New SessionStart compact bootstrap + PreToolUse runtime arch-profile hook

**Touches**: `hooks/session-start-bootstrap.sh` (REPLACED with compact ≤500-token bootstrap; index format only; no rule bodies); new `hooks/pretooluse-arch-profile.sh` (reads `project.yml` at fire-time per FR-034); `hooks/hooks.json` (register the two hooks).

**FRs**: FR-013 (compact SessionStart), FR-034 (PreToolUse arch-profile), SC-013 (≤500 token budget).
**Tests**: `tests/unit/test_session_start_budget.py` (token count + character-length fallback per R8), `tests/unit/test_pretooluse_arch_profile.py` (mid-session profile change observed).

**Acceptance**: SessionStart stdout ≤500 tokens under typical project metadata; contains no full rule bodies; provides index to `project.yml` and `dotnet-ai check`. PreToolUse hook reads `project.yml` at fire-time; mid-session profile change observed by next tool invocation.

### Commit 14 — Rules reclassification (5/11 split) + skill body references + constitution v1.0.8 amendment

**Touches**: Move existing 16 rules to `rules/conventions/` (5) and `rules/domain/` (11); update SKILL.md bodies to reference convention rules via `${CLAUDE_PLUGIN_ROOT}/rules/conventions/<name>.md`; **amend `.specify/memory/constitution.md` from v1.0.7 to v1.0.8** updating "16 rules — 4 universal + 12 path-scoped" to "16 rules — 5 universal + 11 path-scoped" with `async-concurrency` added to universal whitelist.

**FRs**: FR-011 (5/11 classification), FR-012 (JIT for architecture-branching/runtime-substitution rules), SC-004 (≥65% always-on reduction).
**Tests**: `tests/unit/test_rule_classification.py` (exact 5/11 split), `tests/unit/test_skill_body_references.py` (every always-on convention rule referenced from skills that depend on it), `tests/unit/test_constitution_amendment.py` (PASS-CONDITIONAL gate from Constitution Check above).

**Acceptance**: exactly 5 rules in `rules/conventions/` (async-concurrency, coding-style, existing-projects, security, tool-calls); exactly 11 rules in `rules/domain/`; constitution v1.0.8 amendment merged in the same commit; SC-004 measurement passes.

### Commit 14b — `render` read-only CLI surface (depends on commit 14 rule layout)

**Touches**: `src/dotnet_ai_kit/cli.py` (add `render` subcommands `skill <name>` and `rule <name>`); `src/dotnet_ai_kit/render.py` (NEW — `render_skill(name, project)` and `render_rule(name, project)` resolve against the final rule layout from commit 14 and `agents-source/` for skill-resolving paths; Claude-host-shaped output in v1 per US6 / FR-019 / SC-012).

**FRs**: FR-019 (`render` command exists per US6), SC-012 (<2s render).
**Tests**: `tests/unit/test_fr019_render_cases.py`, `tests/unit/test_sc012_render_runtime.py`.

**Acceptance**: `dotnet-ai render <kind> <name> [--host <host>]` prints the runtime-resolved content of the named skill or rule using current `project.yml` per `contracts/render-cli.contract.md:13-20`. Output is identifiable as Claude-host-shaped in v1 per US6; other host shapes deferred per SC-012. CLI rejects `--host codex`, `--host cursor`, `--host copilot` in v1 with exit code 20 per `contracts/render-cli.contract.md:39`. Runtime <2s on a fixture project. Read-only — no `--dry-run` needed per plan Constitution V.

**Rationale for placement**: per tasks-phase round-1 Codex feedback (`discussion/tasks-phase/round1-codex-reply.md` BLOCKER (c) + P0-1), `render_rule()` depends on the finalized 5/11 rule layout introduced by commit 14 (`rules/conventions/` + `rules/domain/`). Placing render before commit 14 forces the render-rule test to use the pre-commit-14 layout and rewrite when commit 14 ships. After commit 14 is the only safe position. Inserted as commit 14b (not 15) so commit 15 (docs, README, release notes) retains its identity. Net commit count: 16 (was 15 in plan-phase round-4 sign-off; render gap discovered during tasks generation; tasks-phase round 2 has Codex acknowledgment).

### Commit 15 — Docs, migration guide, README, planning/

**Touches**: `README.md` (new file footprint per SC-001 instead of ~180); `CLAUDE.md` (project guidance updated); new `docs/migration-v1.md` (user migration guide); `planning/` updates with the spike result for Cursor sub-agents and `bin/` launcher; release notes covering edge cases CHK055-CHK063.

**FRs**: documentation requirements (no FR maps directly; SC-006 structural parity tested via the docs alignment); A-005/A-008 (release notes capture binding outcomes); A-011 (no-network posture documented).
**Tests**: documentation lint (markdown link check, broken-reference scan).

**Acceptance**: README reflects new footprint; migration guide explains migrate command + backup rotation + reversal; release notes call out the host-equivalent reload action per host, csharp-ls prerequisite, Cursor spike outcome, no-telemetry posture.

## PR-by-PR or Commit Discipline

All 16 commits in the sequence `1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14b, 15` land in a single PR on branch `019-plugin-native-arch`. Pre-v1.0.0 status (A-001) plus per-commit reviewability is the mitigation for review burden. Each commit is independently revertable; the LSP migration gate (commit 11 → commit 12) is the only **mandatory** inter-commit ordering constraint that the PR's CI enforces; commit 14b's dependency on commit 14's final rule layout is a **soft** ordering (render works against pre-14 layouts but the test fixtures would need rewriting). The Cursor sub-agent fixture outcome (commit 6) is the only conditional-scope inflection point; if the fixture fails, A-005 + SC-008 + OOS-005 trigger and the PR is scope-revised (spec.md + checklists updated, the full Cursor sub-agent generation deferred to v1.1).

## Phase 2: Tasks (not in this command)

`/speckit.tasks` decomposes the 16 commits (`1..14, 14b, 15`) into per-commit task lists and per-test traceability rows. See `tasks.md` for the round-2-converged 137-task decomposition.

## Review-Phase Outcome (2026-05-18) — Phase 10 added

After commits 1-15 landed, a 4-round cross-AI review at
`discussion/review-phase/` found **8 release-gating defects** (B-1
through B-8: 4 P0 + 4 P1) the pytest suite couldn't catch (because
pre-019 tests inherited assertions that asserted the bug) plus
**8 round-3 plan corrections**. Round 4 (`round4-codex-reply.md`)
verified the artifact updates and surfaced 2 atomicity splits
(T170 → T170a/b/c, T195 → T195a/b) plus 2 acceptance-gate
broadenings (commits 25 + 29) — all incorporated below.

**Canonical fix plan**: [`discussion/review-phase/claude/final-consolidated-review.md`](./discussion/review-phase/claude/final-consolidated-review.md).

**Debate trail** (rounds 1-3):
1. `discussion/review-phase/codex/review.md` — Codex initial BLOCKED
2. `discussion/review-phase/claude/{review,tool-surface-review,content-quality-and-oos-review,consolidated-review}.md` — 4 Claude reviews
3. `discussion/review-phase/round1-claude-to-codex.md` — Claude push-back briefing
4. `discussion/review-phase/round1-codex-reply.md` — Codex r1
5. `discussion/review-phase/round2-claude-reply.md` — Claude concessions
6. `discussion/review-phase/round3-codex-verify.md` — Codex AGREED-WITH-NITS

**Defects**:

| ID | Severity | Description |
|---|---|---|
| B-1 | P0 | `copy_profile()` + `copy_hook()` still write `.claude/rules/architecture-profile.md` + embed frozen prompt for plugin-native hosts (FR-005/006/034 violation). Confirmed at `cli.py:1102, 1874, 2459` + `copier.py:1063, 1131`. |
| B-2 | P0 | `init`/`configure` writer emits legacy `ai_tools:` instead of `enabled_hosts:` (`schemas/config-yml.schema.json` violation; data-model.md:78-80 mandates canonical writer). |
| B-3 | P0 | `save_project()` emits legacy `detected:` nested shape instead of top-level `company:/domain:/...` per `schemas/project-yml.schema.json`. |
| B-4 | P0 | `dotnet-ai check` reports schema-invalid `project.yml` as `pass` (validates via legacy `load_project()`, not raw `jsonschema.validate`). |
| B-5 | P1 | Copilot freshness only hash-compares; misses metadata/source staleness. |
| B-6 | P1 | `configure` interactive picker hard-coded to "Claude Code" only (`cli.py:2286-2297`; FR-016 violation). |
| B-7 | P1 | CI smoke job runs `tests/smoke/` not the feature-019 fixtures at `tests/integration/test_smoke_*.py`; FR-029/SC-008/A-010 release gate effectively absent. |
| B-8 | P1 | 48 ruff errors + 55 format issues. CI `static-unit` job fails today. |

**Plan corrections from Codex round 3** (numbered to match `round3-codex-verify.md:240-248`):
1. **F-F**: option A, but no placeholder cursor/copilot blocks unless meaningful; test "no top-level forbidden fields", not mandatory `host_overrides` for all future files.
2. **B-2**: expand from "writer swap" to full command-path compatibility for canonical `enabled_hosts` (8 read sites consume `config.ai_tools`).
3. **B-3**: define required-field derivation for init, and test actual init output against `schemas/project-yml.schema.json`.
4. **B-4**: raw JSON Schema validate first, then parse with the runtime metadata model used by later checks.
5. **B-7**: 3-OS matrix, `workflow_dispatch`, three smoke env vars, four binaries including `csharp-ls`, preflight that fails on missing binaries, and the four `tests/integration/test_smoke_*.py` files.
6. **B-8**: include `scripts/` in ruff check/format commands.
7. **OOS-005**: neutralize release notes now and update pending-state tests.
8. **B-1**: gate both profile and hook call sites, especially linked-secondary stale-profile hook rendering at `copier.py:1131-1137`.

**Separate technical-accuracy reclassification** (out of the "plan corrections" 1-8 above; surfaced by round-1 Codex content audit but reclassified in round 2 push-back):
- **C-Q4**: `Result<T>::Error` is `string?` in the generic templates the controller skill uses → compiles but produces incomplete ProblemDetails. Fix is semantic (named-parameter `Problem(detail:, statusCode:)`), NOT a compile-error fix.

**Phase 10 (commits 16-30)** in `tasks.md` is the execution plan for
all of the above. Effort estimate: ~35-44 hours (a focused
maintainer-week). All Phase 10 tasks are atomic, file:line-targeted,
and have explicit acceptance gates. v1.0.0 tag is gated on commit 30
(`workflow_dispatch` smoke green on 3 OSes).

## Open items requiring Codex plan-phase verification

This plan is **Draft v1**. Open items for Codex plan-phase round 1:

- **P1** (resolved in tasks-phase round 1): Is the 15-commit order in this plan byte-identical to the FINAL-REPORT order? (Verified yes; tasks-phase round 1 added commit 14b for `render` per Codex's PUSH-BACK-WITH-EVIDENCE — the resulting 16-commit sequence is `1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14b, 15`.)
- **P2**: Is the Constitution Check Violation around the 4→5 universal rules correctly handled as PASS-CONDITIONAL (commit 14 bundled amendment) rather than as a Complexity Tracking entry?
- **P3**: Are the new modules under `src/dotnet_ai_kit/` (especially `hosts/`, `agent_generators.py`, `render.py`, `manifest.py` extensions) the right boundary, or have I over-segmented?
- **P4**: Is the test inventory complete? Specifically: do I have tests for FR-008, FR-011, FR-012, FR-013, FR-017, FR-018, FR-019, FR-020, FR-021, FR-022, FR-023, FR-024, FR-025, FR-026, FR-027, FR-028, FR-029, FR-030, FR-031, FR-032, FR-033, FR-034, FR-035, A-008, A-010, A-011, SC-001 through SC-014, plus all the verification checklist CHKs?
- **P5**: Is the cross-platform CI matrix (Windows + macOS + Linux) sufficiently scoped? Each smoke fixture has to run on its native host; the packaging test runs all three.
- **P6**: Is the conditional-scope handling for the Cursor sub-agent fixture (commit 6) sufficiently explicit?
- **P7**: Are R7, R8, R10, R12, R13 the right Phase 0 research items, or am I missing one?

— Claude
