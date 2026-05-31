# Feature Specification: dotnet-ai-kit v2 — Completion (corpus, restructure, docs, CI)

**Feature Branch**: `021-v2-completion`
**Created**: 2026-05-31
**Status**: Draft
**Input**: User description: "Complete the v2 .NET 10 rewrite end to end: migrate + re-author the full artifact corpus into `artifacts/`; finish all CLI features + engine capabilities with high test coverage; complete AI-tool + per-host plugin setup; restructure the repo and remove all dead v1 files per planning/22–23; rewrite all docs; rewrite GitHub Actions; remove the Python v1 only once the .NET CLI fully covers it."

## Overview

Feature 020 built the v2 .NET 10 engine (Core/Application/Infrastructure/Hosts/Cli/Analyzers, all four host projectors, 8 CLI verbs, the rule-delivery fix, deterministic enforcement, multi-repo awareness) on a **representative** corpus of ~8 artifacts, with all 12 success criteria green. This feature **completes** the rewrite: it migrates and re-authors the **full** artifact corpus from the v1 source, finishes every engine/CLI capability with high test coverage, makes the repository a clean single-source plugin for all four assistants, removes the dead v1 layout, rewrites the documentation and CI, and retires the Python v1 — but only once the .NET CLI demonstrably covers it.

The v1 legacy directories (`skills/` 124, `commands/` 27, `rules/` 16 source, `agents/`, `profiles/` 12, `knowledge/` 16) are the **migration source**; their content is transformed into the v2 `artifacts/` model rather than rewritten from nothing. The engine (proven in 020) is the constraint that keeps the migration honest: the corpus must load (graph-consistent), project to all four hosts, and stay drift-clean.

## Clarifications

### Session 2026-05-31

- Q: How are the ~240 artifacts authored — hand, subagent, or script? → A: **Maintainer-approved hand OR subagent** for new/structural authoring; the **bulk v1→v2 migration uses a deterministic one-off script** (consistency + zero LLM-invented cross-references), verified by `repo.Load()` + `generate --check` after each batch. (maintainer answer)
- Q: When is the Python v1 removed? → A: **Only once the .NET CLI fully covers v1** — proven by a written **parity assessment** (every v1 verb/behavior → a covered .NET capability) plus the green acceptance suite. If any gap remains, Python is retained and the gap documented. (maintainer answer → FR-020)
- Q: Where does the generated plugin ship from (root vs build/)? → A: **`build/` is authoritative** (planning/22 §1/§3): all generated host outputs + manifests + `marketplace.json` live under `build/`; the **v1 root `.claude-plugin/` + root artifact dirs are removed**; exactly one authoritative, generated manifest per host (no competing hand-authored manifest). Internal `build/` layout is finalized in implementation to be a valid installable plugin. (planning/22 → FR-010)
- Q: Does the DescriptionStandard fail the build for migrated artifacts that lack negative scope? → A: **Hard gate for new/structural artifacts; a tracked (non-failing) metric for migrated artifacts.** The standard is never weakened to hide migrated gaps; the migrated-compliance count is reported. (advisor → FR-016)
- Q: How deep are the ~30 new-domain skills authored? → A: **Consistent baseline** — a description-standard `SKILL.md` derived from the catalog one-liner + key conventions, projecting to all hosts; **not** research-exhaustive this session (explicitly noted in tasks.md + summary). (scope tiering → FR-008, US8)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The full corpus is authored once and reaches every assistant (Priority: P1)

A maintainer has the complete knowledge corpus — every skill, agent, command, rule, profile, and knowledge doc — authored exactly once in `artifacts/`, and it projects cleanly to all four assistants with no drift. The v1 near-duplicates are consolidated and the known v1 content defects are fixed.

**Why this priority**: The corpus is the product's substance. Without the full corpus, the engine (already built) has nothing real to project. This is the largest single piece of the completion.

**Independent Test**: Load `artifacts/` and confirm it is graph-consistent (no broken edges), every artifact's name equals its directory/file name, and `generate` projects it to all four hosts with `generate --check` reporting no drift.

**Acceptance Scenarios**:

1. **Given** the migrated corpus, **When** it is loaded, **Then** loading succeeds with zero broken graph edges and every agent→skill reference resolves.
2. **Given** the corpus, **When** `generate` runs, **Then** all four host trees are produced and `generate --check` reports no drift.
3. **Given** the v1 near-duplicates (controllers/scalar/cqrs-basics), **When** the corpus is built, **Then** they are consolidated (no duplicate skills) and the known broken sample is fixed.
4. **Given** every migrated skill, **When** validated, **Then** the no-op `when_to_use` field is gone and command-skills carry user-only invocation.

---

### User Story 2 - The repository is a working plugin for every assistant (Priority: P1)

A developer installs the kit and every supported assistant (Claude Code, Codex CLI, Cursor, GitHub Copilot) loads it correctly: the plugin manifest(s), settings, and per-host artifact trees are present and valid, generated from the single source, with no stale hand-authored manifest competing with the generated one.

**Why this priority**: A corpus that does not actually load in the assistants is inert. The plugin ship-path must be unambiguous and generated.

**Independent Test**: Inspect the plugin manifest(s) and per-host trees; confirm they are generated from `artifacts/` (regenerating reproduces them), the manifest is schema-valid with no auto-discovered keys, and there is exactly one authoritative manifest per host.

**Acceptance Scenarios**:

1. **Given** the generated outputs, **When** the plugin manifest is inspected, **Then** it reflects the real corpus counts and is produced from the single manifest descriptor (no stale v1 manifest remains as a competing source).
2. **Given** each host, **When** its artifact tree is inspected, **Then** it contains correctly-shaped files for that host and nothing hand-authored outside `artifacts/`.
3. **Given** the marketplace/distribution descriptor, **When** inspected, **Then** it is project-scoped and version-pinned and consistent with the manifest.

---

### User Story 3 - The repository is restructured with all dead files removed (Priority: P1)

A developer sees a clean repository matching planning/22: `artifacts/` (source), `src/` (.NET), `tests/`, `build/` (generated), `docs/`, `planning/`, and the build/config files — with the v1 layout directories (the legacy `skills/`, `commands/`, `rules/`, `agents*/`, `profiles/`, `knowledge/`, and any other dead v1 artifact/config directories) removed once their content is migrated.

**Why this priority**: Dead files are confusing and risk drift (two sources of truth). Removing them is required by planning/22–23 and makes the single-source model real.

**Independent Test**: Confirm the legacy v1 artifact directories are gone, every remaining top-level directory is referenced/needed, and the build + tests + generation still pass.

**Acceptance Scenarios**:

1. **Given** the migrated corpus, **When** the v1 artifact directories are removed, **Then** the build, tests, and `generate --check` all still pass.
2. **Given** each remaining top-level directory, **When** checked, **Then** it is referenced by the .NET solution, the SDD tooling, the generated outputs, or the docs (no orphan directories).
3. **Given** a removed directory, **When** git history is consulted, **Then** the removal is a distinct commit (the v1 source is recoverable one commit back).

---

### User Story 4 - Every feature is complete and covered by tests (Priority: P2)

A contributor sees that all planned CLI features and engine capabilities are implemented, and a high-coverage test suite proves them — including a single parametrized corpus-integrity test that exercises every artifact, and tests for the previously-deferred features (analyzer code-fix, capability-dependency validation in `check`, manifest sha256 integrity, distribution packaging).

**Why this priority**: "Complete with high coverage" is an explicit goal; the deferred refinements and the corpus test close the gap between "engine works on a sample" and "everything works."

**Independent Test**: Run the test suite; confirm the corpus-integrity test covers every artifact, the deferred-feature tests pass, and the build is warnings-clean.

**Acceptance Scenarios**:

1. **Given** the full corpus, **When** the corpus-integrity test runs, **Then** every artifact loads, has name==dir, contributes to a consistent graph, and projects to all four hosts.
2. **Given** an analyzer-backed rule violation, **When** a code-fix is offered, **Then** it transforms the code correctly.
3. **Given** `check` with the capability matrix, **When** an artifact declares a capability, **Then** `check` validates it against the matrix.
4. **Given** the tool, **When** packaged, **Then** it installs and runs via the standard .NET tool mechanism.

---

### User Story 5 - Documentation matches the new state (Priority: P2)

A new contributor reads the docs (README, contributor/architecture docs, the agent context file) and they accurately describe the v2 .NET 10 tool, its architecture, the single-source→projection model, and how to build/test/generate — with no stale v1 (Python/27-commands/124-skills) claims.

**Why this priority**: Stale docs actively mislead. Docs must reflect v2 for the rewrite to be usable.

**Independent Test**: Read each doc and confirm it describes the v2 .NET 10 tool and contains no contradictory v1-only claims; the quickstart steps work as written.

**Acceptance Scenarios**:

1. **Given** the README, **When** read, **Then** it describes the v2 .NET 10 tool, its commands, and build/test/generate flow accurately.
2. **Given** the architecture/contributor docs, **When** read, **Then** they match the implemented clean-architecture solution and single-source model.
3. **Given** the agent context file (CLAUDE.md), **When** read, **Then** it reflects v2 (no stale Python-CLI tech-stack claims as the active implementation).

---

### User Story 6 - CI builds, tests, and gates the .NET tool (Priority: P2)

A maintainer's CI runs the .NET build (warnings-as-errors), the test suite, the generation drift gate, and formatting checks — replacing the v1 Python workflows.

**Why this priority**: CI is the durable enforcement of every other guarantee. The v1 Python workflows are dead once Python is removed and misleading before then.

**Independent Test**: Inspect the workflows; confirm they run dotnet build/test/format/generate-gate and do not depend on the removed Python tooling.

**Acceptance Scenarios**:

1. **Given** the CI workflows, **When** inspected, **Then** they build/test the .NET solution, run the format check, and assert the generation drift gate.
2. **Given** the removal of Python, **When** CI runs, **Then** no workflow references the removed Python tooling.

---

### User Story 7 - The Python v1 is removed once the .NET CLI fully covers it (Priority: P3)

Once the .NET CLI demonstrably covers all v1 functionality (a parity assessment plus the green acceptance suite), the Python implementation (`src/dotnet_ai_kit/`) and its tests are removed, leaving the .NET tool as the sole implementation.

**Why this priority**: Removing the reference implementation is the final cutover; it must not happen until coverage is proven, per the maintainer's explicit gate.

**Independent Test**: Confirm a parity assessment exists mapping each v1 capability to its .NET equivalent; only if all are covered are the Python sources/tests removed and the build still green.

**Acceptance Scenarios**:

1. **Given** a parity assessment, **When** every v1 capability maps to a covered .NET capability, **Then** the Python sources and tests may be removed.
2. **Given** a v1 capability with no .NET equivalent, **When** parity is assessed, **Then** Python is retained (or the gap is closed first) and the gap is documented.
3. **Given** Python removal, **When** the build/test/generation run, **Then** all pass with no Python dependency.

---

### User Story 8 - New-domain coverage is added at a consistent baseline (Priority: P3)

The new-domain skills from the catalog (Aspire 13.1, Microsoft.Extensions.AI, Minimal API/ASP.NET 10, messaging/Dapr/Wolverine, Roslyn, modern testing, Blazor, auth, GraphQL) and the license-light migration skills exist as consistent, description-standard `SKILL.md` files derived from the catalog and key conventions.

**Why this priority**: New-domain breadth is valuable but research-heavy; a consistent baseline (not exhaustive deep authoring) is the honest, deliverable scope this session.

**Independent Test**: Confirm each new-domain skill exists, passes the description standard, projects to all hosts, and is reachable via the agent/graph that owns it.

**Acceptance Scenarios**:

1. **Given** the catalog's new-domain list, **When** the corpus is built, **Then** each new skill exists with a standard-compliant description and projects to all hosts.
2. **Given** the license-light direction, **When** a CQRS/mapping skill is read, **Then** it defaults to license-safe patterns with commercial packages opt-in.

---

### Edge Cases

- A v1 artifact references a sibling that is consolidated away → the migration updates the reference (no dangling graph edge).
- A v1 rule placed under `conventions/` that is not on the universal whitelist → it must move to `domain/` with a path scope (or fail validation).
- A top-level directory is referenced by the SDD tooling (`.specify/`) or `bin/` wrappers → it must NOT be deleted as "dead."
- Two competing plugin manifests (root v1 vs generated) → exactly one authoritative, generated manifest must remain.
- A skill's directory name does not equal its frontmatter name after migration → must be corrected, not shipped.
- Regenerating after migration must delete the stale small-corpus `build/` outputs (orphan cleanup) so `build/` matches the full corpus.

## Requirements *(mandatory)*

### Functional Requirements

**Corpus migration & authoring**
- **FR-001**: All v1 skills MUST be migrated into `artifacts/skills/<category>/<name>/SKILL.md` preserving name==dir, with `when_to_use` removed and shaping fields under `metadata:`.
- **FR-002**: All v1 commands MUST be migrated into `artifacts/skills/commands/<name>/SKILL.md` as command-skills (`kind: command`, user-only invocation).
- **FR-003**: All v1 agents MUST be migrated into `artifacts/agents/<name>.md` with a resolved `skills:` reference list (owned skills); the v1 `dotnet-ai-architect` Cursor spike moves to test fixtures, not a shipped agent.
- **FR-004**: All v1 source rules (5 universal `conventions/` + 11 path-scoped `domain/`) MUST be migrated; the 5 new rules MUST be added; universal rules MUST be exactly the whitelist.
- **FR-005**: All 12 profiles and the knowledge docs MUST be migrated into `artifacts/profiles/` and `artifacts/knowledge/`.
- **FR-006**: Near-duplicate skills MUST be consolidated (controllers→controller-patterns, scalar→openapi-scalar, cqrs-basics→decision guide) with all references updated; known content defects MUST be fixed.
- **FR-007**: The 5 new commands (constitution, checklist, orchestrate, release, fix) and 2 new agents (aspire-architect, ai-engineer) MUST be authored as command-skills/agents.
- **FR-008**: The catalog's ~30 new-domain skills MUST exist as description-standard `SKILL.md` files (baseline depth; FR-031 below applies to license posture).

**Engine, projection & plugin setup**
- **FR-009**: The migrated corpus MUST load with zero broken graph edges and project to all four hosts; `generate --check` MUST report no drift.
- **FR-010**: There MUST be exactly one authoritative, generated plugin manifest per host (no stale hand-authored manifest competing as a second source); the ship-path MUST be documented.
- **FR-011**: The marketplace/distribution descriptor MUST be project-scoped, version-pinned, and consistent with the manifest.
- **FR-012**: Generation MUST remain deterministic/idempotent and orphan-cleaning so `build/` exactly matches the corpus.

**Features & coverage**
- **FR-013**: A single parametrized corpus-integrity test MUST assert, for every artifact: it loads, name==dir, the graph is consistent, and it projects to all four hosts.
- **FR-014**: The previously-deferred features MUST be implemented and tested: analyzer code-fix, `check` capability-dependency validation against the matrix, and manifest sha256 integrity.
- **FR-015**: The tool MUST be packageable and runnable via the standard .NET tool mechanism (distribution), with a smoke test.
- **FR-016**: The DescriptionStandard MUST be a hard gate for new/structural artifacts and a tracked metric (count, non-failing) for migrated artifacts; the standard MUST NOT be weakened to hide migrated gaps.
- **FR-017**: The build MUST be warnings-clean (`-warnaserror`), `dotnet format` clean, and free of known package vulnerabilities.

**Restructure & cutover**
- **FR-018**: The v1 layout directories MUST be removed once migrated; the removal MUST be a distinct commit from the migration (v1 recoverable one commit back).
- **FR-019**: Every remaining top-level directory MUST be referenced/needed (no orphan directories); deletions MUST be preceded by a reference check (`grep`), never assumed.
- **FR-020**: The Python v1 (`src/dotnet_ai_kit/`) and its tests MUST be removed ONLY after a parity assessment confirms the .NET CLI covers all v1 functionality and the acceptance suite is green; any uncovered capability MUST be closed or the removal deferred with the gap documented.

**Docs & CI**
- **FR-021**: All documentation (README, architecture/contributor docs, the agent context file) MUST be rewritten to describe the v2 .NET 10 tool with no stale v1-only claims as the active implementation.
- **FR-022**: The GitHub Actions workflows MUST be rewritten to build/test/format/drift-gate the .NET solution and MUST NOT depend on removed Python tooling.

### Key Entities

- **Migrated artifact**: a v1 skill/agent/command/rule/profile/knowledge transformed into the v2 `artifacts/` model (portable frontmatter + `metadata:` shaping fields + body).
- **Parity assessment**: a mapping from each v1 capability (CLI verb/behavior) to its .NET equivalent, gating Python removal.
- **Plugin ship-path**: the single, generated location from which each host loads the kit.
- **Corpus-integrity test**: the parametrized test covering every artifact's load/name/graph/projection.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The full corpus (≈32 commands, 15 agents, 21 rules, 12 profiles, ≈160 skills, knowledge docs) is in `artifacts/`, loads with zero broken edges, and `generate --check` reports no drift across all four hosts.
- **SC-002**: A single corpus-integrity test passes for **every** artifact (load, name==dir, graph, 4-host projection).
- **SC-003**: The build is `-warnaserror` clean, `dotnet format` clean, and reports no package vulnerabilities; the full test suite passes.
- **SC-004**: The v1 artifact directories are removed and every remaining top-level directory is referenced; build/test/generate still pass.
- **SC-005**: Exactly one authoritative generated plugin manifest exists per host; regenerating reproduces the plugin outputs byte-identically.
- **SC-006**: The deferred features (analyzer code-fix, `check` capability validation, manifest sha256, distribution packaging) are implemented and tested.
- **SC-007**: All docs describe v2 with no stale v1-only active-implementation claims; the quickstart steps work.
- **SC-008**: CI builds/tests/formats/drift-gates the .NET solution with no Python dependency.
- **SC-009**: A parity assessment exists; Python is removed only if it shows full coverage (else the gap is documented and Python retained).
- **SC-010**: New-domain skills exist at a consistent, description-standard baseline and project to all hosts.

## Assumptions & Constraints

- Builds on feature 020 (branch `021-v2-completion` is off `020-v2-net10-rewrite`); the 020 engine + SCs are the foundation.
- **Authoring** may be by hand or delegated to subagents (maintainer-approved this session); the **bulk v1→v2 migration uses a deterministic one-off script** (consistency, zero LLM-invented cross-references), verified by `Load()` + `generate --check`.
- **Python removal is gated** on the .NET CLI fully covering v1 (maintainer-explicit); not done until proven.
- **Scope tiering** (per the build-plan discipline): the **anchor** (full migration, structural new artifacts, restructure, plugin/docs/CI, integrity test, deferred features) is built green; the **~30 new-domain skills** are authored to a consistent baseline depth (not exhaustive), explicitly noted.
- .NET 10 SDK 10.0.300; clean/hexagonal architecture; license-light generated code by default (planning/26 locked decisions).

## Dependencies

- The feature-020 engine (projection, CLI, analyzers, tests).
- The v1 source directories as the migration source (removed after migration).
- .NET 10 SDK; Git.

## Out of Scope (this feature)

- Deep, research-exhaustive authoring of every new-domain skill (baseline only this session).
- Native AOT packaging (deferred per planning/26 BD-3).
- New product capabilities beyond planning/20–26.

## Traceability

| Area | Source |
|---|---|
| Artifact catalog (the full list) | planning/23-v2-artifact-catalog.md |
| Project structure + dead-file removal | planning/22-v2-project-structure.md |
| Selector/gates/lifecycle/multi-repo | planning/24 |
| Requirements baseline + locked decisions | planning/25, planning/26 (authoritative) |
| Engine foundation + prior SCs | specs/020-v2-net10-rewrite/ |
