# Implementation Plan: Tool-Wide Quality Hardening

**Branch**: `016-tool-quality-hardening` | **Date**: 2026-04-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/016-tool-quality-hardening/spec.md`

## Summary

Fix 30 issues across the dotnet-ai-kit codebase identified in the tool review (2 critical, 4 high, 10 medium, 14 low). Changes span build packaging (pyproject.toml), 12 command markdown files, 4 Python source modules (cli.py, copier.py, config.py, models.py, extensions.py), ~72 skill files, and 1 config template. Organized into 8 independently testable parts, prioritized by severity.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: typer, pydantic v2, jinja2, rich, pyyaml, questionary, filelock
**Storage**: File-based (YAML config, JSON permissions, Markdown commands/rules/skills)
**Testing**: pytest, pytest-cov (263 existing tests, all passing)
**Target Platform**: Cross-platform CLI (Windows, macOS, Linux)
**Project Type**: CLI tool / developer tooling plugin
**Performance Goals**: `check` command completes in <5 seconds
**Constraints**: Commands ≤200 lines, rules ≤100 lines, skills ≤400 lines, profiles ≤100 lines
**Scale/Scope**: 27 commands, 120 skills, 15 rules, 13 agents, 12 profiles

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Detect-First | PASS | No .NET code generation. Profile deployment respects detected project type. |
| II. Pattern Fidelity | PASS | All Python changes follow existing codebase patterns (pathlib, encoding="utf-8", pydantic v2). |
| III. Architecture Agnostic | PASS | All 12 project types retain profiles. Multi-tool deployment preserved. |
| IV. Best Practices | PASS | Tests required for all code changes. TDD approach. |
| V. Safety & Token Discipline | PASS | Line budgets enforced: clarify.md stays <200, implement.md stays <200, skills stay <400. `--dry-run` support maintained. |

No violations. No Complexity Tracking entries needed.

## Project Structure

### Documentation (this feature)

```text
specs/016-tool-quality-hardening/
├── plan.md              # This file
├── research.md          # Phase 0 output — 10 research decisions
├── data-model.md        # Phase 1 output — model changes, new constants, config changes
├── quickstart.md        # Phase 1 output — implementation order and verification
├── contracts/
│   ├── cli-changes.md   # CLI command contract changes (init, check, configure, upgrade)
│   └── command-changes.md # Command file contract changes (branch safety, flags, steps)
├── checklists/
│   └── requirements.md  # Spec quality checklist (all passing)
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/dotnet_ai_kit/
├── cli.py               # Modified: init (profile+hook+default), check (new fields),
│                        #   configure (guard+re-deploy), upgrade (warnings)
├── copier.py            # Modified: COMMAND_SHORT_ALIASES, copy_commands alias logic,
│                        #   deploy_to_linked_repos (style+git add)
├── config.py            # Modified: yaml.YAMLError catch in load_config
├── models.py            # Modified: KNOWN_PATH_KEYS, detected_paths validator
└── extensions.py        # Modified: after_remove hook execution

commands/
├── clarify.md           # Modified: add branch safety section
├── implement.md         # Modified: add branch safety section
├── plan.md              # Modified: add event-flow.md generation step
├── specify.md           # Modified: reorder steps (4b before 5)
├── do.md                # Modified: clarify artifact ownership
├── add-aggregate.md     # Modified: --dry-run → --dry-run + --list
├── add-crud.md          #   (same change in all 9 code-gen commands)
├── add-endpoint.md
├── add-entity.md
├── add-event.md
├── add-page.md
├── add-tests.md
├── docs.md
└── explain.md

skills/                  # ~72 SKILL.md files modified (when-to-use + paths additions)

templates/
└── config-template.yml  # Modified: remove integrations section

pyproject.toml           # Modified: add profiles/ and prompts/ to force-include

tests/
├── test_cli.py          # Modified: new tests for init profile, check fields,
│                        #   configure guard, upgrade warnings, init auto-default
├── test_copier.py       # Modified: new tests for COMMAND_SHORT_ALIASES
├── test_config.py       # Modified: new test for YAML error handling
├── test_models.py       # Modified: new test for detected_paths validator
├── test_extensions.py   # Modified: new test for after_remove hooks
└── test_multi_repo_deploy.py  # Modified: new tests for style + git add
```

**Structure Decision**: Existing single-project Python CLI structure. No new directories or modules needed — all changes are modifications to existing files.

## Complexity Tracking

No constitution violations. No entries needed.

## Phase 0 Output

See [research.md](research.md) — 10 research decisions, all resolved. Key findings:

- **R1**: profiles/ and prompts/ missing from pyproject.toml force-include (confirmed)
- **R2**: Short-prefix generation uses raw stems, needs alias mapping (confirmed)
- **R3**: init() deploys 5 asset types but not profiles/hooks (confirmed)
- **R4**: check() reports 4 columns, missing 4+ new fields (confirmed)
- **R5**: load_config() missing yaml.YAMLError catch (confirmed)
- **R6**: deploy_to_linked_repos hardcodes primary config + .claude/ in git add (confirmed)
- **R7**: 11/120 skills have when-to-use, 3/120 have paths (confirmed)
- **R8**: remove_extension() never executes after_remove hooks (confirmed)
- **R9**: permissions-bypass.json does not exist on disk — FR-028 resolved, no action
- **R10**: configure() has no init guard (confirmed)

## Phase 1 Output

See:
- [data-model.md](data-model.md) — KNOWN_PATH_KEYS constant, COMMAND_SHORT_ALIASES constant, detected_paths validator, config template change, check output schema, skill frontmatter changes
- [contracts/cli-changes.md](contracts/cli-changes.md) — init(), check(), configure(), upgrade(), deploy_to_linked_repos() contract changes
- [contracts/command-changes.md](contracts/command-changes.md) — Branch safety, event-flow.md, --dry-run/--list split, specify.md reorder, do.md ownership

## Constitution Re-Check (Post-Design)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Detect-First | PASS | Profile deployment gated on project type detection. |
| II. Pattern Fidelity | PASS | All code changes follow existing module patterns. |
| III. Architecture Agnostic | PASS | All 12 profiles and multi-tool support preserved. |
| IV. Best Practices | PASS | New tests for each code change. ~18 new test functions across 15 test tasks. |
| V. Safety & Token Discipline | PASS | Line budgets verified: clarify ~185, implement ~196, all skills <400. |

## Next Step

Run `/speckit.tasks` to generate task breakdown from this plan.
