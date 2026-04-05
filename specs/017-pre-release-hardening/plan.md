# Implementation Plan: Pre-Release v1.0.0 Hardening

**Branch**: `017-pre-release-hardening` | **Date**: 2026-04-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/017-pre-release-hardening/spec.md`

---

## Summary

50 targeted changes: 29 code/markdown fixes (FR-001–029) + 21 documentation sync items (FR-030–050). Touches 7 Python source files, 1 new module, 14 command files, 2 skill files, 1 new rule file, 8 planning docs, README.md, and CHANGELOG.md. No new external dependencies. No breaking changes. Target: 280 → ≥ 295 tests, 0 ruff errors, all docs accurate at v1.0.0 release.

---

## Technical Context

**Language/Version**: Python 3.10+ (runtime: 3.12.10)
**Primary Dependencies**: typer 0.24.1, pydantic 2.12.5, pyyaml, rich, jinja2
**Storage**: YAML files (`.dotnet-ai-kit/config.yml`, `project.yml`)
**Testing**: pytest, pytest-cov, ruff
**Target Platform**: Windows / macOS / Linux (cross-platform, pathlib throughout)
**Project Type**: CLI tool + knowledge base (markdown assets)
**Performance Goals**: N/A (bug fixes, no performance-sensitive paths changed)
**Constraints**: commands ≤ 200 lines, rules ≤ 100 lines, skills ≤ 400 lines
**Scale/Scope**: ~4,500 lines Python, 27 command files, 120 skill files, 15 rule files

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Detect-First | ✅ Pass | No generated code changes; no AI tool detection logic changed |
| II. Pattern Fidelity | ✅ Pass | All Python changes follow existing patterns (logging, pydantic validators, typer exits) |
| III. Architecture Agnostic | ✅ Pass | No architecture assumptions; CLI tool changes are platform-neutral |
| IV. Best Practices | ✅ Pass | Atomic writes, debug logging, consistent error handling added |
| V. Safety / Token Discipline | ✅ Pass | 14 command files trimmed to stay ≤ 200 lines; new rule file ≤ 100 lines |

No violations. Complexity Tracking table not required.

---

## Project Structure

### Documentation (this feature)

```text
specs/017-pre-release-hardening/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── contracts/
│   ├── cli-interface.md ← new flags + commands
│   └── command-files.md ← Usage/Examples contract
├── quickstart.md        ← Phase 1 output
└── tasks.md             ← Phase 2 output (/speckit.tasks)
```

### Source Code Changes

```text
src/dotnet_ai_kit/
├── utils.py             ← NEW: parse_version() shared utility
├── copier.py            ← MODIFIED: aliases, _HOOK_MODEL/_HOOK_TIMEOUT_MS, deploy loop, token logging
├── extensions.py        ← MODIFIED: catalog error, after_remove, conflict check, CatalogInstallError
├── models.py            ← MODIFIED: DotnetAiConfig model_validator for unknown keys
├── config.py            ← MODIFIED: atomic writes in save_config() + save_project()
├── agents.py            ← MODIFIED: get_agent_config() unsupported tool warning
└── cli.py               ← MODIFIED: --permissions on init, changelog command, verbose except blocks,
                            configure dry-run guard, upgrade --force, extension-list empty, JSON warnings,
                            check --verbose enrichment

tests/
├── test_utils.py        ← NEW: parse_version() tests
├── test_cli.py          ← MODIFIED: ~10 new tests
├── test_copier.py       ← MODIFIED: alias tests for configure/crud/page
├── test_extensions.py   ← MODIFIED: catalog, after_remove, rule conflicts
├── test_models.py       ← MODIFIED: unknown key warning
└── test_config.py       ← MODIFIED: atomic write test

commands/                ← 14 files MODIFIED: Usage + Examples added
├── analyze.md
├── clarify.md
├── configure.md
├── detect.md
├── do.md
├── implement.md
├── init.md
├── learn.md
├── plan.md
├── pr.md
├── review.md
├── specify.md
├── tasks.md
└── verify.md

rules/
└── multi-repo.md        ← NEW

skills/workflow/
├── plan-artifacts/SKILL.md   ← MODIFIED: add category: workflow
└── plan-templates/SKILL.md   ← MODIFIED: add category: workflow

planning/                     ← 8 docs MODIFIED: sync with 015/016/017 built state
├── 04-commands-design.md     ← COMMAND_SHORT_ALIASES 10→13 entries
├── 05-rules-design.md        ← rule count 15→16, add multi-repo.md entry
├── 06-build-roadmap.md       ← all 15 v1.0 phases: Planned→Complete; rule count 6→16
├── 07-project-structure.md   ← src/ tree (3→10 files), rules list (6→16), test files (6→13)
├── 08-multi-repo-orchestration.md ← add tooling deploy, profile, hook, linked_from, FeatureBrief, branch safety
├── 10-permissions-config.md  ← permissions.level→permissions_level flat key
├── 12-version-roadmap.md     ← v1.0 phases Complete; 015/016/017 late additions; changelog + --permissions
├── 13-handoff-schemas.md     ← add feature-brief.md schema
└── 16-cli-implementation.md  ← config schema, extension names, check/init output, new functions, guards

README.md                     ← MODIFIED: rule counts, skill table, test count, extension commands
CHANGELOG.md                  ← MODIFIED: add spec-015/016/017 entries, fix counts, fix extension names
```

**Structure Decision**: Single-package Python CLI. All changes are modifications to the existing flat `src/dotnet_ai_kit/` package. One new module (`utils.py`) is added. Markdown assets are modified in-place.

---

## Complexity Tracking

No constitution violations.
