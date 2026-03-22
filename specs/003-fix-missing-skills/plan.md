# Implementation Plan: Fix Missing Skills and Naming Examples

**Branch**: `003-fix-missing-skills` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-fix-missing-skills/spec.md`

## Summary

Create 10 missing skill files to reach the 101-skill target from the
planning inventory, and replace production-specific domain names in
`rules/naming.md` with generic examples. Small, well-scoped content fix.

## Technical Context

**Language/Version**: Markdown files with C# code examples targeting .NET 8/9/10
**Primary Dependencies**: N/A (content files only)
**Storage**: File-based (markdown in skills/, rules/)
**Testing**: `find skills -name "SKILL.md" | wc -l` must return 101
**Target Platform**: N/A (AI assistant content)
**Project Type**: Content addition + minor fix
**Performance Goals**: N/A
**Constraints**: Skills ≤400 lines; {Company}/{Domain} placeholders
**Scale/Scope**: 10 new files + 1 file update = 11 changes

## Constitution Check

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Detect-First | PASS | New skills teach detect-existing patterns |
| II. Pattern Fidelity | PASS | Skills use version-aware code examples |
| III. Agnostic | PASS | {Company}/{Domain} placeholders; naming.md fix removes domain-specific names |
| IV. Quality | PASS | Skills follow established format with YAML frontmatter |
| V. Token Discipline | PASS | Each skill ≤400 lines |

No violations.

## Project Structure

### Documentation

```text
specs/003-fix-missing-skills/
├── plan.md          # This file
├── research.md      # Skill gap analysis
└── tasks.md         # /speckit.tasks output
```

### Files to Create/Update

```text
skills/core/modern-csharp/SKILL.md          # NEW
skills/core/coding-conventions/SKILL.md     # NEW
skills/api/controllers/SKILL.md             # NEW
skills/api/scalar/SKILL.md                  # NEW
skills/data/dapper/SKILL.md                 # NEW
skills/data/specification-pattern/SKILL.md  # NEW
skills/data/audit-trail/SKILL.md            # NEW
skills/cqrs/command-generator/SKILL.md      # NEW
skills/cqrs/query-generator/SKILL.md        # NEW
skills/architecture/advisor/SKILL.md        # NEW
rules/naming.md                             # UPDATE (replace Competition/SoldCard)
```

**Structure Decision**: 10 new subdirectories under existing skill
categories + 1 edit to existing rule file. No new categories.

## Source Mapping

| Skill | Source | Agent |
|-------|--------|-------|
| modern-csharp | planning/14-generic-skills-spec.md | dotnet-architect |
| coding-conventions | planning/14-generic-skills-spec.md, planning/05-rules-design.md | dotnet-architect |
| controllers | planning/14-generic-skills-spec.md, ../references/dotnet-clean-architecture-skills | api-designer |
| scalar | ../projects/anis.gateways-cards-store-management (Scalar setup) | gateway-architect |
| dapper | planning/14-generic-skills-spec.md, ../references/dotnet-clean-architecture-skills | ef-specialist |
| specification-pattern | planning/14-generic-skills-spec.md, ../references/dotnet-clean-architecture-skills | ef-specialist |
| audit-trail | planning/14-generic-skills-spec.md, ../references/dotnet-clean-architecture-skills | ef-specialist |
| command-generator | planning/14-generic-skills-spec.md, ../references/dotnet-clean-architecture-skills | ef-specialist |
| query-generator | planning/14-generic-skills-spec.md, ../references/dotnet-clean-architecture-skills | ef-specialist |
| advisor | planning/14-generic-skills-spec.md, planning/01-vision.md | dotnet-architect |

## Post-Design Constitution Re-Check

| Principle | Status |
|-----------|--------|
| I. Detect-First | PASS |
| II. Pattern Fidelity | PASS |
| III. Agnostic | PASS |
| IV. Quality | PASS |
| V. Token Discipline | PASS |
