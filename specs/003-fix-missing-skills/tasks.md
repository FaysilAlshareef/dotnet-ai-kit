# Tasks: Fix Missing Skills and Naming Examples

**Input**: Design documents from `/specs/003-fix-missing-skills/`
**Prerequisites**: plan.md (required), spec.md (required)

**Tests**: No automated tests. Validation: `find skills -name "SKILL.md" | wc -l` must return 101.

**Organization**: US1 creates 10 missing skills (all parallel). US2 fixes naming.md.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1=Missing Skills, US2=Naming Fix

## Phase 1: Setup

**Purpose**: No setup needed — skill directory structure exists from feature 001.

---

## Phase 2: User Story 1 - Complete the 101 Skill Target (Priority: P1) 🎯 MVP

**Goal**: Create 10 missing skill files identified in the planning inventory gap analysis.

**Independent Test**: `find skills -name "SKILL.md" | wc -l` returns 101.

- [x] T001 [P] [US1] Create modern C# skill (C# 12/13/14 features: primary constructors, records, collection expressions, field keyword, pattern matching). Source: planning/14-generic-skills-spec.md. Write to skills/core/modern-csharp/SKILL.md

- [x] T002 [P] [US1] Create coding conventions skill (company-agnostic naming, file-scoped namespaces, sealed classes, expression bodies, var usage). Source: planning/14-generic-skills-spec.md, planning/05-rules-design.md. Write to skills/core/coding-conventions/SKILL.md

- [x] T003 [P] [US1] Create controllers skill (RESTful controllers with routing, versioning, MediatR integration, action results, model binding). Source: planning/14-generic-skills-spec.md, ../references/dotnet-clean-architecture-skills. Write to skills/api/controllers/SKILL.md

- [x] T004 [P] [US1] Create Scalar skill (Scalar UI setup, themes, authentication prefill, OpenAPI enrichment, environment-aware config). Source: ../projects/anis.gateways-cards-store-management (Scalar setup). Write to skills/api/scalar/SKILL.md

- [x] T005 [P] [US1] Create Dapper skill (multi-mapping, pagination, dynamic filtering, CTEs, raw SQL alongside EF Core). Source: planning/14-generic-skills-spec.md, ../references/dotnet-clean-architecture-skills. Write to skills/data/dapper/SKILL.md

- [x] T006 [P] [US1] Create specification pattern skill (composable query criteria, includes, ordering, pagination, ISpecification interface). Source: planning/14-generic-skills-spec.md, ../references/dotnet-clean-architecture-skills. Write to skills/data/specification-pattern/SKILL.md

- [x] T007 [P] [US1] Create audit trail skill (IAuditable interface, EF Core SaveChanges interceptor, CreatedAt/UpdatedAt/CreatedBy auto-population). Source: planning/14-generic-skills-spec.md, ../references/dotnet-clean-architecture-skills. Write to skills/data/audit-trail/SKILL.md

- [x] T008 [P] [US1] Create CQRS command generator skill (command record + handler + validator pattern using MediatR + FluentValidation). Source: planning/14-generic-skills-spec.md, ../references/dotnet-clean-architecture-skills. Write to skills/cqrs/command-generator/SKILL.md

- [x] T009 [P] [US1] Create CQRS query generator skill (query record + handler + response DTO pattern with pagination). Source: planning/14-generic-skills-spec.md, ../references/dotnet-clean-architecture-skills. Write to skills/cqrs/query-generator/SKILL.md

- [x] T010 [P] [US1] Create architecture advisor skill (questionnaire-based architecture recommendation: VSA vs Clean Arch vs DDD vs Modular Monolith vs Microservices, decision matrix, tradeoffs). Source: planning/14-generic-skills-spec.md, planning/01-vision.md. Write to skills/architecture/advisor/SKILL.md

**Checkpoint**: `find skills -name "SKILL.md" | wc -l` returns 101.

---

## Phase 3: User Story 2 - Replace Production Names in Rules (Priority: P2)

**Goal**: Replace "Competition" and "SoldCard" in `rules/naming.md` with generic domain names.

**Independent Test**: `grep -c "Competition\|SoldCard" rules/naming.md` returns 0.

- [x] T011 [US2] Replace all "Competition" and "SoldCard" examples in rules/naming.md with generic names (Order, Invoice, Product, Customer). Preserve the naming pattern structure — only change the example domain names.

**Checkpoint**: Zero occurrences of "Competition" or "SoldCard" in rules/naming.md.

---

## Phase 4: Polish & Cross-Cutting Concerns

- [x] T012 Validate total skill count is exactly 101 via `find skills -name "SKILL.md" | wc -l`
- [x] T013 [P] Validate all 10 new skill files have YAML frontmatter (name, description, category, agent) and are ≤400 lines

---

## Dependencies & Execution Order

- **US1 (Phase 2)**: All 10 tasks are [P] — can all run in parallel
- **US2 (Phase 3)**: Independent of US1 — can run in parallel
- **Polish (Phase 4)**: Depends on US1 + US2

## Implementation Strategy

### Full Parallel Execution

All 11 implementation tasks (T001-T011) can run simultaneously — they target different files with zero conflicts. Single wave execution.
