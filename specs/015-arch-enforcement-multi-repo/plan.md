# Implementation Plan: Architecture Profiles, Multi-Repo Deployment, and Enforcement Optimization

**Branch**: `015-arch-enforcement-multi-repo` | **Date**: 2026-04-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/015-arch-enforcement-multi-repo/spec.md`

## Summary

The dotnet-ai-kit currently applies 15 generic rules to all project types and has no enforcement mechanism beyond design-time text. This feature adds: (1) 12 per-project-type architecture profile files deployed as always-loaded rules, (2) multi-repo tooling deployment to linked secondary repos during configure/upgrade, (3) branch safety for all auto-commits to secondary repos, (4) a Claude Code PreToolUse prompt hook that uses haiku to validate writes against profile constraints, (5) universal agent frontmatter with per-tool transformation in copier.py, (6) skill auto-activation via detected paths and behavioral `when-to-use` triggers, and (7) command context forking for review/verify/check commands. All changes are additive — existing projects continue working without modification.

## Technical Context

**Language/Version**: Python 3.10+ (CLI tool); targets .NET 8.0+/9.0+/10.0+ projects  
**Primary Dependencies**: typer, pydantic v2, jinja2, rich, pyyaml  
**Storage**: YAML files (config.yml, project.yml), JSON (settings.json), Markdown (profiles, agents, skills, commands, rules)  
**Testing**: pytest, pytest-cov; mock filesystem and subprocess calls  
**Target Platform**: Windows, macOS, Linux (cross-platform via pathlib.Path)  
**Project Type**: CLI tool / AI dev tool plugin  
**Performance Goals**: Profile deployment <1s per project; hook validation <15s per write; multi-repo deployment <30s per repo  
**Constraints**: Rules ≤100 lines each, ~900 total budget; Commands ≤200 lines; Skills ≤400 lines; no shell=True; no os.path  
**Scale/Scope**: 12 profiles, 13 agents, ~10 skills updated, 6 commands updated, 6 new test files; deploys to 1-5 linked repos

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Detect-First, Respect-Existing | PASS | Profiles are deployed based on detected project type from project.yml. No existing code is refactored. |
| II. Pattern Fidelity | PASS | Profile constraints are derived from existing skills/rules — no new conventions introduced. |
| III. Architecture & Platform Agnostic | PASS | Profiles cover all supported architectures. Cross-platform via pathlib. Cross-tool via universal schema. |
| IV. Best Practices & Quality | PASS | 6 new test files. Token budgets enforced. SOLID patterns in copier functions. |
| V. Safety & Token Discipline | PASS | Branch safety for all auto-commits. Profile ≤100 lines. Rules budget stays within ~900. Hooks are fail-open. |
| Token discipline: rules | PASS | 15 existing (803 lines) + 1 profile (≤100 lines) = ≤903 lines, within ~900 budget. |
| Token discipline: commands | PASS | Updated commands stay within 200-line limit. |
| Token discipline: skills | PASS | Updated skills stay within 400-line limit. |
| Multi-repo orchestration | PASS | Constitution explicitly supports 3-6 repo orchestration. This feature adds the deployment mechanism. |

No violations. No entries needed in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/015-arch-enforcement-multi-repo/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
# New directories
profiles/
├── microservice/
│   ├── command.md
│   ├── query-sql.md
│   ├── query-cosmos.md
│   ├── processor.md
│   ├── gateway.md
│   ├── controlpanel.md
│   └── hybrid.md
└── generic/
    ├── vsa.md
    ├── clean-arch.md
    ├── ddd.md
    ├── modular-monolith.md
    └── generic.md

templates/
└── hook-prompt-template.md    # Template for building hook prompt string

# Modified files
src/dotnet_ai_kit/
├── models.py                  # +detected_paths on DetectedProject, +linked_from on DotnetAiConfig
├── copier.py                  # +copy_profile(), +copy_hook(), +deploy_to_linked_repos()
│                              #  update copy_agents() for frontmatter transform
│                              #  update copy_skills() for ${detected_paths.*} resolution
├── agents.py                  # +AGENT_FRONTMATTER_MAP dict
└── cli.py                     # extend configure() and upgrade() for profiles/hooks/multi-repo

agents/                        # 13 files: replace frontmatter with universal schema
commands/                      # 6 files: dai.specify, dai.plan, dai.tasks (branch fix),
                               #          dai.review, dai.verify, dai.analyze (context fork)
skills/                        # ~10 SKILL.md files: +when-to-use, +paths tokens

# New test files
tests/
├── test_copier_profiles.py
├── test_copier_agents.py
├── test_copier_skills.py
├── test_copier_hooks.py
├── test_multi_repo_deploy.py
└── test_models_new_fields.py
```

**Structure Decision**: Single-project CLI tool. No new directories beyond `profiles/` (content files) and the hook prompt template. All Python changes are in the existing `src/dotnet_ai_kit/` package. Tests follow existing `tests/test_*.py` convention.

## Complexity Tracking

> No Constitution violations detected. Table not needed.

## Phase 0: Research

See [research.md](research.md) for full findings.

**Key decisions**:
1. Profile-to-project-type mapping uses a simple dict in copier.py keyed by project_type string.
2. AGENT_FRONTMATTER_MAP uses callables (lambdas) for fields that need value transformation (expertise, max_iterations) and nested dicts for enum mappings (role, complexity).
3. Hook prompt template uses Jinja2 `{{ constraints }}` placeholder filled at deployment time.
4. Multi-repo deployment reuses existing copy_* functions with a target_root parameter override.
5. Detected paths stored as `Optional[dict[str, str]]` on DetectedProject — simple flat dict, not nested.
6. Branch operations in cli.py use `subprocess.run(["git", ...])` with list args per project conventions.

## Phase 1: Design

See [data-model.md](data-model.md) for entity changes.
See [contracts/](contracts/) for interface contracts.
See [quickstart.md](quickstart.md) for implementation guide.

## Constitution Re-Check (Post-Design)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Detect-First | PASS | copy_profile() reads project_type from project.yml (detected state). deploy_to_linked_repos() reads each repo's project.yml. No assumptions made. |
| II. Pattern Fidelity | PASS | Profiles derive from existing skills/rules. Agent frontmatter transform preserves body content. No new patterns introduced. |
| III. Agnostic | PASS | PROFILE_MAP covers all 12 project types. AGENT_FRONTMATTER_MAP has v1.0.1 stubs. Cross-platform via pathlib throughout. |
| IV. Quality | PASS | 6 test files cover all new functions. Contracts define clear interfaces. Token budgets validated in tests. |
| V. Safety | PASS | Branch safety in deploy_to_linked_repos(). Fail-open hooks. No deployment capability added. All changes reversible via upgrade. |

All gates pass. Ready for `/speckit.tasks`.
