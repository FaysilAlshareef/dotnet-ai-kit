# Implementation Plan: Multi-Repo Awareness

**Branch**: `013-multi-repo-awareness` | **Date**: 2026-03-30 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/013-multi-repo-awareness/spec.md`

## Summary

Fix two critical gaps in the multi-repo microservice workflow: (1) the configure command lacks repo auto-detection, path validation, and GitHub URL support, and (2) secondary repos have zero awareness of cross-repo features. The solution adds smart repo detection to `/dai.configure` (slash command + CLI), introduces a `feature-brief.md` projection system that writes self-contained briefs to secondary repos under a separate `briefs/` directory, and integrates brief awareness across all 15 SDD lifecycle commands.

## Technical Context

**Language/Version**: Python 3.10+ (CLI tool), Markdown (slash commands, skills)
**Primary Dependencies**: typer, pydantic v2, pyyaml, rich, questionary (CLI); no new deps needed
**Storage**: YAML config files, Markdown feature artifacts, filesystem-based briefs
**Testing**: pytest, pytest-cov
**Target Platform**: Windows, macOS, Linux (cross-platform via pathlib)
**Project Type**: CLI tool + AI assistant plugin (slash commands as markdown specs)
**Performance Goals**: Sibling repo scan completes in <5s for up to 20 repos; brief projection <2s per repo
**Constraints**: Commands ≤200 lines, skills ≤400 lines, rules ≤100 lines (constitution token budgets)
**Scale/Scope**: 15 command files to edit, 1 skill file to edit, 2 Python source files to edit, 1 new Python source file possible

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Detect-First, Respect-Existing | PASS | This feature extends existing commands; no refactoring of existing .NET code |
| II. Pattern Fidelity | PASS | All command edits follow existing command file patterns |
| III. Architecture & Platform Agnostic | PASS | Uses pathlib for all paths; no OS-specific logic; briefs are plain markdown |
| IV. Best Practices & Quality | PASS | Pydantic validation for models; test coverage for new validators |
| V. Safety & Token Discipline | PASS | All edited commands stay within 200-line budget; brief projection is best-effort (never blocks primary workflow); auto-commit skips on conflict |

**Token Budget Impact Assessment:**

| File | Current Lines | Estimated After | Budget | Status |
|------|--------------|-----------------|--------|--------|
| commands/configure.md | 121 | ~165 | 200 | OK |
| commands/specify.md | 178 | ~198 | 200 | TIGHT — must be concise |
| commands/tasks.md | 197 | ~200 | 200 | TIGHT — replacing spec-link section, net ~same |
| commands/implement.md | 182 | ~198 | 200 | TIGHT — adding to existing steps |
| commands/status.md | 132 | ~155 | 200 | OK |
| commands/init.md | 114 | ~125 | 200 | OK |
| commands/detect.md | 143 | ~160 | 200 | OK |
| commands/plan.md | 110 | ~125 | 200 | OK |
| commands/clarify.md | 170 | ~180 | 200 | OK |
| commands/review.md | 181 | ~195 | 200 | TIGHT |
| commands/pr.md | 161 | ~175 | 200 | OK |
| commands/analyze.md | 191 | ~200 | 200 | TIGHT — adding Pass 11 |
| commands/wrap-up.md | 138 | ~148 | 200 | OK |
| commands/checkpoint.md | 118 | ~128 | 200 | OK |
| multi-repo-workflow SKILL.md | 145 | ~200 | 400 | OK |

**Risk**: specify.md, tasks.md, implement.md, review.md, and analyze.md are near the 200-line limit. Edits must replace existing content where possible rather than append.

## Project Structure

### Documentation (this feature)

```text
specs/013-multi-repo-awareness/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/dotnet_ai_kit/
├── models.py            # EDIT: Add URL normalizer to ReposConfig, add FeatureBrief model
├── cli.py               # EDIT: Add repo prompts to configure()
└── config.py            # READ-ONLY: load/save already handles repos field

commands/
├── configure.md         # EDIT: Rewrite Step 3 (smart repo detection)
├── specify.md           # EDIT: Add Step 4b (brief projection)
├── clarify.md           # EDIT: Add brief re-projection after clarifications
├── plan.md              # EDIT: Add Step 7b (update briefs with approach)
├── tasks.md             # EDIT: Replace Cross-Repo Feature Tracking section
├── analyze.md           # EDIT: Add Pass 11 (Brief Consistency)
├── implement.md         # EDIT: Update Step 5a/5b (brief read/write)
├── review.md            # EDIT: Add Check 9 (Brief Compliance)
├── pr.md                # EDIT: Update Step 3 (cross-repo PR body)
├── status.md            # EDIT: Add Step 2b (linked features display)
├── init.md              # EDIT: Add briefs/ preservation
├── detect.md            # EDIT: Add Step 6b (sibling repo scan)
├── wrap-up.md           # EDIT: Add briefs status to handoff
└── checkpoint.md        # EDIT: Add briefs status to handoff

skills/workflow/multi-repo-workflow/
└── SKILL.md             # EDIT: Add Feature Brief Projection section

tests/
├── test_models.py       # EDIT: Add tests for URL normalizer and FeatureBrief
└── test_cli.py          # EDIT: Add tests for repo prompts in configure()
```

**Structure Decision**: This feature modifies existing files only. No new directories or files are created in the main source tree except potentially new test functions in existing test files.

## Implementation Approach

### Layer 1: Foundation (Models + Validators)

Edit `models.py` to:
1. Update `ReposConfig.validate_repo_path` to detect and normalize GitHub URLs and SSH URLs to `github:org/repo`
2. Add `FeatureBrief` pydantic model with phase enum validation

These are pure Python changes with no side effects. They enable all subsequent work.

### Layer 2: CLI Configure (Python)

Edit `cli.py configure()` to add repo prompts after the company settings section. This includes:
- Scanning `../` for sibling repos (using pathlib)
- Presenting detected repos with questionary
- Validating paths
- Saving to config

### Layer 3: Command Files — P1 Commands (Markdown)

Edit the 6 most critical command files that form the core brief projection lifecycle:
1. `configure.md` — Rewrite Step 3
2. `specify.md` — Add Step 4b (brief projection)
3. `tasks.md` — Replace Cross-Repo Feature Tracking
4. `implement.md` — Update Step 5a/5b
5. `init.md` — Add briefs/ preservation
6. `status.md` — Add Step 2b

### Layer 4: Command Files — P2/P3 Commands (Markdown)

Edit the remaining 8 command files with lighter-touch changes:
7. `plan.md` — Add Step 7b
8. `clarify.md` — Add brief re-projection
9. `review.md` — Add Check 9
10. `pr.md` — Update Step 3
11. `analyze.md` — Add Pass 11
12. `detect.md` — Add Step 6b
13. `wrap-up.md` — Add briefs status
14. `checkpoint.md` — Add briefs status

### Layer 5: Skill + Docs

Edit `multi-repo-workflow/SKILL.md` to add Feature Brief Projection documentation section.

### Layer 6: .slnx References

Audit all command and skill files for `.sln` references that don't also include `.slnx`. Update any that are missing.

## Brief Projection Logic (shared across commands)

This is the core algorithm used by specify, plan, tasks, clarify, and implement when projecting or updating briefs:

```
function project_brief(primary_repo, feature, target_repo_config, phase):
  1. source_name = basename(primary_repo)  # e.g., "company-domain-command"
  2. target_path = resolve(target_repo_config)  # local path or skip if github:
  3. if target_path is None or not exists(target_path): skip with note
  4. brief_dir = target_path / ".dotnet-ai-kit" / "briefs" / source_name / feature.id
  5. mkdir -p brief_dir
  6. Write feature-brief.md with:
     - Header: feature ID, date, phase, source info
     - This Repo's Role: from service-map.md filtered to this repo
     - Required Changes: from service-map/plan filtered to this repo
     - Events: produces/consumes filtered to this repo
     - Tasks: from tasks.md filtered to [Repo:this-repo] (if tasks phase)
     - Dependencies: upstream/downstream from service-map
     - Implementation Approach: from plan.md (if plan phase+)
  7. Auto-commit in target_repo:
     - git add brief_dir/feature-brief.md
     - git commit -m "chore: project feature brief {feature.id} from {source_name}"
     - If uncommitted changes conflict: warn, skip commit
```

### Layer 7: Post-Implementation Fixes

Review-discovered fixes applied after initial implementation:
1. Standardize auto-commit message format across all projection commands (FR-035)
2. Add `--repos` flag test in test_cli.py
3. Fix review.md check numbering (Check 8b → Check 9, renumber Performance to Check 10) (FR-027)
4. Add undo.md brief awareness note (FR-037)
5. Optimize `_scan_sibling_repos()` glob patterns (FR-039)
6. Update `config-template.yml` repos section docs (FR-038)

## Complexity Tracking

No constitution violations. All changes extend existing patterns.

| Concern | Mitigation |
|---------|-----------|
| 5 commands near 200-line budget | Replace existing placeholder sections rather than append; use concise phrasing |
| specify.md at 178 lines + brief projection | Brief projection step is ~15 lines; removing template comments saves ~5 lines |
| analyze.md at 191 lines + Pass 11 | Pass 11 is ~8 lines; compact format matching existing passes |
