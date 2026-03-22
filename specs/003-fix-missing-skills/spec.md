# Feature Specification: Fix Missing Skills and Naming Examples

**Feature Branch**: `003-fix-missing-skills`
**Created**: 2026-03-16
**Status**: Draft
**Input**: User description: "Fix 10 missing skills and rules/naming.md production examples"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Complete the 101 Skill Target (Priority: P1)

A developer using dotnet-ai-kit has access to all 101 planned skills as
documented in the planning inventory. Currently 91 of 101 skills exist.
10 skills from the planning docs (02-skills-inventory.md,
11-expanded-skills-inventory.md) were not created during initial
implementation.

**Why this priority**: The tool advertises 101 skills. Missing skills
mean incomplete coverage for generic .NET patterns (modern C#, Dapper,
audit trail, architecture advisor, CQRS generators, specification pattern).

**Independent Test**: Run `find skills -name "SKILL.md" | wc -l` and
verify the count is exactly 101.

**Acceptance Scenarios**:

1. **Given** the current 91 skill files, **When** the 10 missing skills
   are created, **Then** the total count is exactly 101.

2. **Given** each new skill file, **When** inspected, **Then** it has
   YAML frontmatter (name, description, category, agent), version-aware
   code examples, "Detect Existing Patterns" section, "Adding to
   Existing Project" section, and stays ≤400 lines.

---

### User Story 2 - Replace Production Names in Rules (Priority: P2)

The `rules/naming.md` file uses "Competition" and "SoldCard" as naming
examples. While technically used with "Acme" (not "Anis"), these names
match the production domain and could confuse users into thinking the
tool is tied to a specific company's domain. Replace with obviously
generic examples.

**Why this priority**: Rules are always-loaded files. Every user sees
them. Production-specific domain names reduce perceived generality.

**Independent Test**: Search `rules/naming.md` for "Competition" and
"SoldCard" — neither should appear. Generic names like "Order",
"Invoice", "Product" should be used instead.

**Acceptance Scenarios**:

1. **Given** `rules/naming.md`, **When** searched for "Competition" or
   "SoldCard", **Then** zero matches are found.

2. **Given** the updated naming examples, **When** a developer reads
   them, **Then** the examples use obviously generic domain names
   (Order, Invoice, Product, Customer) that could apply to any company.

---

### Edge Cases

- What if a missing skill overlaps with an existing skill? The new skill
  must be distinct — check content against existing skills in the same
  category and ensure no duplication.

- What if a missing skill's planned name conflicts with an existing
  directory? Check for empty directories or differently-named files and
  resolve before creating.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Create 10 missing skill files to reach the 101 target:
  1. `skills/core/modern-csharp/SKILL.md` — C# 12/13/14 features
  2. `skills/core/coding-conventions/SKILL.md` — Company-agnostic naming
  3. `skills/api/controllers/SKILL.md` — RESTful controller patterns
  4. `skills/api/scalar/SKILL.md` — Scalar UI setup and themes
  5. `skills/data/dapper/SKILL.md` — Dapper queries and multi-mapping
  6. `skills/data/specification-pattern/SKILL.md` — Composable queries
  7. `skills/data/audit-trail/SKILL.md` — IAuditable, EF interceptor
  8. `skills/cqrs/command-generator/SKILL.md` — Command + handler + validator
  9. `skills/cqrs/query-generator/SKILL.md` — Query + handler + DTO
  10. `skills/architecture/advisor/SKILL.md` — Architecture recommendation

- **FR-002**: Each new skill MUST follow the standard format: YAML
  frontmatter (name, description, category, agent), ≤400 lines,
  version-aware C# examples, detect/add sections.

- **FR-003**: Replace "Competition" and "SoldCard" in `rules/naming.md`
  with generic domain names (Order, Invoice, Product, Customer).

- **FR-004**: Source content from `planning/14-generic-skills-spec.md`,
  `planning/02-skills-inventory.md`, `planning/11-expanded-skills-inventory.md`,
  and `../references/dotnet-clean-architecture-skills` for patterns.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `find skills -name "SKILL.md" | wc -l` returns exactly 101.

- **SC-002**: All 10 new skill files have valid YAML frontmatter and are
  ≤400 lines.

- **SC-003**: Zero occurrences of "Competition" or "SoldCard" in
  `rules/naming.md`.

- **SC-004**: No duplicate content between new skills and existing skills
  in the same category.
