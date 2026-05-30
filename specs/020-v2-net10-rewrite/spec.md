# Feature Specification: dotnet-ai-kit v2 — Single-Source Artifact Engine

**Feature Branch**: `020-v2-net10-rewrite`
**Created**: 2026-05-31
**Status**: Draft
**Input**: User description: "Rewrite dotnet-ai-kit as a .NET 10 clean-architecture CLI that authors every artifact once in a tool-agnostic source and projects it to Claude Code, Codex CLI, Cursor, and GitHub Copilot, with deterministic enforcement that fixes the v1 rule-delivery bug, token-frugal intelligent invocation, a full SDD lifecycle, and first-class multi-repo orchestration"

## Overview

dotnet-ai-kit is a developer tool that equips AI coding assistants (Claude Code, Codex CLI, Cursor, GitHub Copilot) with the knowledge, commands, and guardrails needed for the full .NET development lifecycle. Today (v1) every assistant's knowledge is authored separately, the corpus drifts between tools, and — most critically — the domain convention rules that are supposed to guide generated code **never actually reach** the plugin-native Claude assistant. The result is artifact drift and unenforced conventions.

v2 fixes the root causes. A maintainer authors each artifact (skill, agent, rule, profile, command) **exactly once** in a single tool-agnostic source. The tool **projects** that source into each assistant's native shape and guarantees, mechanically, that (a) the projected outputs never drift, (b) the convention rules genuinely arrive in the assistant's context when relevant code is touched, and (c) completion claims are gated on real build/test evidence rather than the assistant's say-so.

This specification is the testable requirements baseline for that rewrite. It consolidates and supersedes the v1 behavior, which serves as the reference spec. Decisions that were locked by the maintainer prior to this spec (target platform, distribution model, license posture) are recorded under **Assumptions & Constraints** rather than re-opened.

## Clarifications

> The maintainer is unavailable for interactive Q&A this session. The decisions below were resolved from the **locked decision record** (planning/26-v2-build-plan-and-decisions.md, authoritative) rather than asked, and applied to the relevant requirements. This is the autonomous equivalent of `/speckit.clarify`.

### Session 2026-05-31

- Q: For the hard enforcement tiers that require host interception (pre-edit deny) and completion blocking (Stop-hook), which hosts get them vs. a fallback? → A: **Claude-scoped**; Codex/Cursor/Copilot get documented fallbacks (Roslyn analyzer + CI gates, a generated verify command, static rule projection, host-native rule systems). No host may *claim* enforcement it cannot perform. (planning/26 AR-3 → FR-024)
- Q: Given MediatR/AutoMapper/MassTransit are now commercial, what does generated code default to? → A: **License-light by default** — manual mapping and a dispatch port, no commercial packages; commercial packages are opt-in profiles with version + license notes; free alternatives offered are Mediator (source-gen) and Wolverine. (planning/26 AR-1 → FR-031, FR-032)
- Q: What is the skill-selection mechanism — a runtime router or something lighter? → A: **Not a runtime router.** Selection is sharp per-artifact descriptions + the artifact graph + a thin disambiguator carried by the `do` command (guidance, not a gate). Skills are not tools and there is no single point of failure. (planning/26 §"Learnings" → FR-026, US6, Out of Scope)
- Q: What is the initial scope of the triggering/selection evaluation oracle? → A: **Ambiguous clusters first** (mediator, CQRS, eventing, testing, architecture, gateway/control-panel) with curated queries + expected top-k; expand to full per-skill coverage only after the harness proves stable. (planning/26 AR-6 → FR-028)
- Q: Does multi-repo orchestration run sequentially or in parallel by default? → A: **Sequential, dependency-ordered by default**; `--parallel` opts into per-repo subagent fan-out (no hard dependency on preview orchestration). (planning/26 / planning/25 D3 → FR-033)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Author an artifact once, have it reach Claude without drift (Priority: P1)

A maintainer writes or edits one artifact in the single authored source. They run a single command and the assistant-specific files for Claude Code are (re)generated. On a clean checkout, regenerating produces **no** changes — the committed outputs and the freshly generated outputs are byte-identical — so drift between the source and what the assistant actually sees is impossible to merge.

**Why this priority**: This is the core value of v2 and the minimum viable product. Without a working author-once → project → drift-gate loop for at least one host, none of the other capabilities have a foundation. It proves the single-source-of-truth architecture end to end.

**Independent Test**: Author a small corpus (~5 artifacts), run the generation command, commit the outputs. Re-run generation on the clean checkout and confirm zero changes. Delete one generated file, re-run, and confirm it is restored byte-identically.

**Acceptance Scenarios**:

1. **Given** a clean checkout with a committed authored corpus, **When** the maintainer regenerates all assistant outputs, **Then** there are no file changes (no drift).
2. **Given** a generated assistant file has been deleted, **When** the maintainer regenerates, **Then** the file is restored byte-identically to its committed form.
3. **Given** an authored artifact references a non-existent sibling artifact, **When** the maintainer regenerates, **Then** generation fails with an error naming the broken reference (no partial/garbage output is written).
4. **Given** an artifact body contains project-metadata tokens (e.g. company name, detected paths), **When** it is rendered for a specific project, **Then** the tokens are replaced with that project's values and no token markers remain.

---

### User Story 2 - Domain rules actually reach the coding assistant (Priority: P1)

A developer initializes the tool in their .NET solution. From that point on, when they (or the assistant) edit a file that a domain convention rule applies to, the relevant rule content is present in the assistant's working context. This is the defect v2 exists to fix: in v1, plugin-native Claude received no domain rules at all.

**Why this priority**: This is the motivating defect for the entire rewrite. A tool whose conventions never reach the assistant cannot enforce anything. SC for this story is part of the non-negotiable convergence anchor.

**Independent Test**: Initialize the tool in a throwaway .NET project. Confirm the project-local rule files exist with path-scoping metadata. Simulate touching a file that matches a rule's scope and confirm the rule body is what would be injected into context.

**Acceptance Scenarios**:

1. **Given** a freshly initialized Claude project, **When** initialization completes, **Then** project-local rule files exist with path-scope metadata declaring which files each rule applies to.
2. **Given** a path-scoped rule whose scope matches a file about to be edited, **When** that edit is intercepted, **Then** the active rule/profile content is supplied to the assistant as additional context.
3. **Given** a universal (always-on) rule, **When** the assistant works in the project at all, **Then** that rule is part of the always-loaded context.
4. **Given** the initialized footprint, **When** its files are counted, **Then** the per-solution footprint is small and bounded (the corpus itself is delivered from the installed tool, not copied per project).

---

### User Story 3 - The same knowledge reaches every assistant (Priority: P2)

A maintainer's single authored corpus is projected into the native shape of all four supported assistants — Claude Code, Codex CLI, Cursor, and GitHub Copilot — each receiving only the fields and file formats it understands. A published capability matrix records, per assistant, which features are supported, in preview, or unsupported, so projected artifacts never claim a capability a host lacks.

**Why this priority**: Multi-assistant reach is the headline promise, but it builds on the engine proven in US1. It is high value yet not required to prove the architecture.

**Independent Test**: Run generation and confirm each of the four assistant output locations is populated with correctly-shaped files. Confirm the capability matrix exists and that each projected artifact's declared capability dependencies are present in the matrix.

**Acceptance Scenarios**:

1. **Given** the authored corpus, **When** generation runs, **Then** each assistant's output directory contains files in that assistant's native format (e.g. markdown skills/agents/rules for one, TOML agents + an aggregated instructions file for another, scoped rule files for another, instruction/prompt files for another).
2. **Given** an artifact carries assistant-specific extension fields, **When** it is projected for a given assistant, **Then** the emitted file contains only fields that assistant understands; extension fields for other assistants are stripped or translated.
3. **Given** the capability matrix, **When** an artifact depends on a host capability, **Then** the matrix entry for that host/capability exists and is tagged with a maturity level.

---

### User Story 4 - A reliable CLI with a verifiable contract (Priority: P2)

A developer uses the command-line tool to initialize, validate, render, migrate, regenerate, configure, and detect. The tool behaves identically on Windows, macOS, and Linux, makes no network calls for local operations, returns documented exit codes for validation, and keeps the initialized footprint within a fixed bound. An automated acceptance suite encodes these invariants as the cross-cutting contract.

**Why this priority**: The CLI is the user-facing surface and the home of the behavioral contract that gates the rewrite. It depends on the engine (US1) and is required before broad corpus or enforcement work.

**Independent Test**: Run the validation command in a configured project and confirm the documented exit code. Run all local verbs under a network-deny harness and confirm zero network calls. Count the initialized footprint and confirm it is within bound.

**Acceptance Scenarios**:

1. **Given** a configured project, **When** the validation command runs, **Then** it returns the documented exit code for that project state (a fixed, enumerated set of codes), within the performance budget.
2. **Given** any local command (initialize, validate, render, migrate, regenerate), **When** it runs under a network-deny harness, **Then** it completes successfully and makes zero network calls.
3. **Given** a v1-style legacy layout, **When** migration runs, **Then** legacy artifacts are cleaned with safe, rotated backups and the legacy config alias is accepted on read.
4. **Given** the same inputs on Windows, macOS, and Linux, **When** any command runs, **Then** behavior and generated file content are identical (path handling, line endings, and shell invocation are platform-neutral).

---

### User Story 5 - Conventions are enforced deterministically, and "done" requires evidence (Priority: P3)

When generated or edited code violates a mechanical convention (naming, layering, banned APIs, mutable aggregate state), the developer gets a build-time error from a shipped analyzer — zero AI tokens spent. When the assistant tries to finish a feature/implementation flow, completion is blocked until build and tests are green, with failures fed back. Hard, mechanical violations can be intercepted before they are written.

**Why this priority**: Deterministic enforcement is the durable, token-free quality floor and a differentiator, but it layers on top of a working engine, corpus, and CLI.

**Independent Test**: Introduce a code change that violates an analyzer-backed rule and confirm the build fails with the expected diagnostic. Simulate a "done" claim while tests fail and confirm completion is blocked; make tests pass and confirm completion is allowed.

**Acceptance Scenarios**:

1. **Given** code that violates an analyzer-backed convention, **When** the project builds, **Then** the build emits an error diagnostic identifying the rule.
2. **Given** an in-progress feature/implementation flow with failing tests, **When** the assistant attempts to declare completion, **Then** completion is blocked and the failing evidence is reported.
3. **Given** the same flow with passing build and tests, **When** the assistant attempts to declare completion, **Then** completion is allowed.
4. **Given** a hard violation (forbidden path or banned API), **When** the edit is attempted, **Then** it is denied before being written (on hosts that support interception) or caught by the analyzer/CI floor (on hosts that do not).

---

### User Story 6 - Assistants pick the right knowledge without burning context (Priority: P3)

The right skill/rule fires for a given developer request, and sibling/confusable artifacts stay silent. The always-loaded context stays within a small token budget because user-invoked commands are off-budget and duplicate knowledge is consolidated. A repeatable evaluation harness guards selection accuracy and token budget in CI.

**Why this priority**: Precision and token frugality strongly affect real-world quality, but they tune a system that must first exist and be correct.

**Independent Test**: Run the triggering evaluation over curated queries for confusable artifact clusters and confirm the correct artifact is selected while siblings are not. Measure always-loaded context size and confirm it is within budget.

**Acceptance Scenarios**:

1. **Given** a curated set of should-trigger queries for a consolidated skill, **When** the selection evaluation runs, **Then** the correct skill is selected and its sibling/confusable skills are not.
2. **Given** the full artifact set, **When** the always-loaded context is measured, **Then** it is within the token budget, with user-invoked commands excluded from the always-loaded listing.
3. **Given** a change that regresses selection accuracy or grows the budget beyond target, **When** CI runs, **Then** CI fails.

---

### User Story 7 - The full SDD lifecycle and a rebuilt, license-safe corpus (Priority: P3)

A developer drives a complete spec-driven development lifecycle (constitution → specify → clarify → checklist → plan → tasks → analyze → orchestrate → implement → review → verify → fix → pr → release, plus status/undo/checkpoint/wrap-up and code-generation commands) through user-invoked commands. The rebuilt knowledge corpus consolidates v1 duplicates, fixes known content defects, and defaults generated code to license-safe choices, offering commercial packages only as opt-in.

**Why this priority**: The lifecycle and corpus breadth are the bulk of the day-to-day value, but each command and skill is incremental on top of the engine and enforcement foundation.

**Independent Test**: Confirm the full command set is present and projected as user-invoked (off the always-loaded budget). Generate code for a representative architecture and confirm it uses license-safe defaults and matches detected conventions.

**Acceptance Scenarios**:

1. **Given** the projected corpus, **When** the command set is listed, **Then** all lifecycle and code-generation commands are present and marked user-invoked (off the always-loaded budget).
2. **Given** a project that does not opt into commercial packages, **When** code is generated, **Then** it uses license-safe defaults (manual dispatch/mapping) and no commercial package is introduced.
3. **Given** consolidated skills that replace v1 near-duplicates, **When** the corpus is built, **Then** no near-duplicate skills remain and the known v1 content defects are absent.

---

### User Story 8 - Multi-repo features stay coordinated and aware (Priority: P3)

For a feature spanning multiple repositories (e.g. Command, Query, Processor, Gateway, Control Panel), every affected repository is initialized with tooling and enforcement, and every affected repository receives a feature brief describing its role and the events it consumes/produces. Cross-repo contract consistency (event producer/consumer match, client/server contracts) is validated, and progress is reported as a single multi-repo view.

**Why this priority**: Multi-repo orchestration is a major differentiator for the microservice audience, but it depends on a working single-repo lifecycle first.

**Independent Test**: Run a multi-repo specify/orchestrate over a service map and confirm every repo in the map ends up with a matching feature brief and initialized tooling. A contract test asserts awareness cannot silently regress.

**Acceptance Scenarios**:

1. **Given** a feature whose service map names multiple repositories, **When** specify/orchestrate runs, **Then** every named repository contains a feature brief carrying the matching feature identifier.
2. **Given** affected repositories, **When** orchestration initializes them, **Then** each has project configuration and the enforcement hook so conventions fire everywhere.
3. **Given** an event produced in one repo and consumed in another, **When** cross-repo analysis runs, **Then** producer/consumer mismatches are reported.

---

### User Story 9 - Install and run as a standard .NET tool (Priority: P4)

A developer installs the tool through the standard .NET tool mechanism and runs it immediately on any supported platform, with a pinned, project-scoped distribution manifest.

**Why this priority**: Packaging and distribution are the last mile; they matter for adoption but are meaningless until the tool itself is complete and green.

**Independent Test**: Pack the tool, install it from the local package, and run a basic command on a clean machine/container per supported platform.

**Acceptance Scenarios**:

1. **Given** the packaged tool, **When** a developer installs it via the standard .NET tool mechanism, **Then** the CLI is available and runs a basic command successfully.
2. **Given** the distribution manifest, **When** it is inspected, **Then** it is project-scoped and version-pinned.

---

### Edge Cases

- **Broken artifact graph**: a reference to a non-existent artifact must fail generation loudly, never emit partial output.
- **Dirty working tree in a secondary repo** during multi-repo orchestration: warn and skip rather than risk clobbering uncommitted work.
- **Host lacks a capability** an artifact depends on (e.g. cannot block completion): the projector must fall back to the documented alternative, not silently claim the capability.
- **Legacy config keys** from v1 must be accepted on read (alias) without forcing a manual migration.
- **Unicode/long paths/CRLF** differences across platforms must not change generated content or cause failures.
- **Re-running any generator** must be idempotent (no spurious diffs from nondeterministic ordering or timestamps).
- **Bundled executable scripts** shipped with skills must never auto-run without explicit consent; their trust level must be explicit.
- **User-owned files** (assistant settings, instruction files, editor rule files) must be merged/backed-up per a documented policy, never blindly overwritten.

## Requirements *(mandatory)*

### Functional Requirements

**Authoring & artifact model**

- **FR-001**: The system MUST treat a single authored source tree as the sole hand-authored origin for all artifact types (skills, agents, rules, profiles, fragments, knowledge, and the manifest descriptor). No artifact may be hand-authored in a per-assistant output location.
- **FR-002**: The system MUST model Skill, Agent, Rule, Profile, and Command as distinct artifact types; the projection step decides each artifact's surface per host (skill, command, rule, agent prompt, or manifest entry). The model MUST NOT require every artifact to be the same type on every host.
- **FR-003**: A skill MAY carry optional resource folders (scripts, examples, references, assets, evaluations) only where it needs them; resource folders MUST NOT be mandatory boilerplate on every skill. Agents, commands, and rules MUST carry no bundled resource folders and instead reference skills.
- **FR-004**: Artifact metadata MUST use a portable core field set plus namespaced host-specific extension blocks; the projector MUST strip or translate extension blocks so each emitted file carries only fields its target host understands.
- **FR-005**: Runtime project-metadata substitution MUST be token replacement only (no general template engine required for the corpus); unresolved tokens after rendering MUST be detectable.
- **FR-006**: The system MUST build an artifact graph from metadata (nodes = artifacts; edges = ownership/relation/trigger/enforced-by) and MUST fail the build when an edge references a non-existent artifact.
- **FR-007**: User-invoked lifecycle/code-gen commands MUST be authored such that they are excluded from the assistant's always-loaded listing (user-invoked, off-budget).

**Projection & multi-assistant support**

- **FR-008**: The system MUST project the authored source into each supported assistant's native shape via one projector per assistant.
- **FR-009**: Generation MUST be CI-gated: a single regeneration pass MUST (re)produce every assistant output and all manifests, and CI MUST fail if regeneration produces any change against the committed outputs (drift cannot merge).
- **FR-010**: All per-assistant plugin manifests MUST be rendered from one manifest descriptor; each host's manifest MUST conform to that host's expected schema; auto-discovered keys MUST be absent from manifests.
- **FR-011**: Generation MUST be deterministic and idempotent: repeated runs on unchanged inputs MUST produce byte-identical outputs (stable ordering, no timestamps or nondeterministic content).
- **FR-012**: A machine-readable host-capability matrix MUST exist, recording per host which capabilities are supported and at what maturity; every projected artifact MUST be able to name the host capability it depends on, and the matrix MUST cover those capabilities.

**CLI behavior & contract**

- **FR-013**: The CLI MUST expose verbs for initialize, validate, render, migrate, regenerate, configure, detect, and upgrade, each delegating to an application-level use case.
- **FR-014**: The validation verb MUST return a fixed, enumerated set of exit codes reflecting project state, and MUST complete within the performance budget.
- **FR-015**: Local operations (initialize, validate, migrate, render, regenerate) MUST make zero network calls; this MUST be enforced by an automated process-level network-deny test.
- **FR-016**: All CLI behavior and generated files MUST be identical across Windows, macOS, and Linux; file paths MUST go through a filesystem abstraction and external processes MUST be invoked with argument lists, never a shell string.
- **FR-017**: Initialization MUST write a small, bounded per-solution footprint (project/config/manifest/version metadata, assistant settings, and project-local rule files); the corpus MUST be delivered from the installed tool path, not copied per project.
- **FR-018**: Migration MUST clean v1 layout artifacts with rotated backups (retain a fixed number), and config loading MUST accept the documented v1 legacy alias on read.

**Rule delivery & enforcement** *(the v1 defect fix)*

- **FR-019**: Initialization MUST write domain rules to the project-local rule location with path-scope metadata, so path-scoped rules load only when a matching file is touched. *(This is the direct fix for the v1 defect where plugin-native Claude received no domain rules.)*
- **FR-020**: An interception hook MUST inject the active profile/rule content as additional context when a matching file is about to be edited (advisory tier).
- **FR-021**: An interception hook MUST be able to deny hard violations (forbidden path, banned API) before the edit is written, on hosts that support interception.
- **FR-022**: A shipped analyzer package MUST emit build-error diagnostics for analyzer-backed rules (naming, layer-dependency, banned APIs, mutable aggregate state); severities MUST be configurable via standard editor configuration.
- **FR-023**: A completion-gate hook MUST run build and tests when the assistant attempts to finish a feature/implementation flow and MUST block completion until green, feeding failures back. This gate MUST be scoped to feature/implement flows (not every turn) and configurable per permission profile.
- **FR-024**: Hard enforcement tiers that require host interception/blocking MUST be scoped to hosts that verifiably support them (**Claude is the verified host for v2.0**); for other hosts (Codex/Cursor/Copilot) the system MUST provide documented fallbacks (analyzer + CI gates, generated verification command, static rule projection, host-native rule systems) and MUST NOT claim unsupported enforcement.
- **FR-025**: A declaration MUST record which markdown rules/profiles have a paired analyzer, keeping advisory and deterministic layers in sync.

**Intelligent invocation & token economy**

- **FR-026**: Every artifact description MUST conform to a description standard (action-verb-first, third person, explicit "use when" triggers, explicit negative scope naming the sibling to use instead).
- **FR-027**: Path-scoped rules and location-specific skills MUST carry path globs and load only when a matching file is touched.
- **FR-028**: A triggering evaluation harness plus a cross-artifact confusion matrix MUST gate description changes in CI: the correct artifact fires for its queries and confusable siblings stay silent. The harness MUST start with the known ambiguous clusters (mediator, CQRS, eventing, testing, architecture, gateway/control-panel) and expand to full per-skill coverage only after it proves stable.
- **FR-029**: The always-loaded listing MUST stay within the token budget; the budget MUST be measured by a tokenizer-based check in the validation verb, and CI MUST fail on budget regression.

**Lifecycle, corpus, multi-repo**

- **FR-030**: The system MUST provide the complete SDD lifecycle command set and code-generation commands, authored as user-invoked commands.
- **FR-031**: Generated code MUST default to license-safe choices (manual dispatch/mapping behind a port); commercial packages (MediatR/AutoMapper/MassTransit) MUST be opt-in only, with version and license notes recorded in generated output; free alternatives (source-generated mediator, Wolverine) MUST be offered.
- **FR-032**: All v1 artifacts MUST be rebuilt into the new model; near-duplicate skills MUST be consolidated; known v1 content defects (no-op fields, the broken sample) MUST be fixed.
- **FR-033**: Multi-repo orchestration MUST initialize every affected repository with configuration and the enforcement hook, and MUST project a feature brief into every affected repository's feature folder. Orchestration MUST run sequentially in dependency order by default; a `--parallel` flag MAY opt into per-repo subagent fan-out.
- **FR-034**: Cross-repo analysis MUST validate contract consistency (event producer/consumer match, client/server contracts, sequencing/idempotency, catalogue completeness).
- **FR-035**: A contract test MUST assert that after specify/orchestrate, every repository in the service map has a feature brief with the matching feature identifier (awareness cannot silently regress).

**Trust, user files, versioning, distribution** *(new requirement areas)*

- **FR-036**: Bundled executable scripts MUST have an explicit trust/consent model and MUST NOT be auto-run without consent.
- **FR-037**: User-owned files MUST be governed by a documented merge/overwrite/backup/diff-preview policy; the tool MUST NOT blindly overwrite user edits.
- **FR-038**: Artifacts MUST carry a schema version, and the tool MUST define a migration path across schema versions.
- **FR-039**: The system MUST define a release/rollback plan (artifact form, platform matrix, upgrade path, rollback if projection output differs).
- **FR-040**: Hooks and shell commands MUST have cross-platform coverage including PowerShell, not bash only.

### Key Entities

- **Skill**: The atomic, resource-bearing unit of knowledge. Has a name (kebab, ≤64 chars, equal to its directory), a description (≤ the host cap), license, compatibility, metadata, a body (≤ a fixed line budget), and optional resource folders.
- **Agent**: A specialist persona that references skills; carries no bundled resources. Projected as an assistant-native agent/prompt.
- **Rule**: A convention that applies either universally (always loaded) or to a path scope (loaded on matching file touch). May be paired with an analyzer diagnostic.
- **Profile**: A bundle of rules/permissions for a project mode; spans the advisory (hook-injected) and deterministic (analyzer-backed) layers.
- **Command**: A user-invoked lifecycle or code-gen action, authored as a command-skill, kept off the always-loaded budget.
- **Fragment**: A reusable content snippet referenced by other artifacts.
- **Manifest Descriptor**: The single source for all per-assistant plugin manifests.
- **Artifact Graph**: The derived graph of artifacts and their edges; the integrity gate.
- **Host Capability Matrix**: The machine-readable record of which assistant supports which capability at which maturity.
- **Project Metadata**: Detected per-project values (company, paths, .NET version, architecture) used for token substitution.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (drift gate)**: On a clean checkout, regenerating all assistant outputs produces zero file changes; deleting a generated file and regenerating restores it byte-identically. *(convergence anchor)*
- **SC-002 (rule delivery — the bug fix)**: After initialization on a Claude project, domain rules exist at the project-local rule location with path-scope metadata; an automated test confirms the v1 defect is gone. *(convergence anchor)*
- **SC-003 (build & tests green)**: The solution builds with no errors and the automated test suite passes. *(convergence anchor)*
- **SC-004 (completion gate)**: The completion-gate hook blocks a simulated "done" claim when the test command fails and allows it when green, within the feature/implement flow scope.
- **SC-005 (selection precision)**: For every consolidated skill, its should-trigger queries select it and its sibling/confusable skills are not selected.
- **SC-006 (token budget)**: The always-loaded listing fits the token budget with all user-invoked commands off-listing; the measured context size is within target.
- **SC-007 (cross-cutting contract)**: An acceptance test suite passes against the built binary, covering the no-network invariant, the enumerated validation exit codes, and the bounded footprint.
- **SC-008 (multi-assistant reach)**: After generation, all four assistant output locations are populated with correctly-shaped files that pass golden-output comparison.
- **SC-009 (multi-repo awareness)**: A multi-repo specify/orchestrate run leaves a matching feature brief in every service-map repository and initializes each secondary repository's configuration.
- **SC-010 (performance)**: Validation completes in under 10 seconds and single-artifact render completes in under 2 seconds on a representative corpus.
- **SC-011 (footprint)**: The per-solution initialized footprint is within its fixed bound (the corpus is not copied per project).
- **SC-012 (cross-platform)**: The same commands produce identical generated content on Windows, macOS, and Linux.

## Assumptions & Constraints

These were locked by the maintainer before this spec and are **not** open questions (sourced from the decision record):

- **Platform**: The tool is built on **.NET 10** (SDK 10.0.300) with a clean/hexagonal architecture. This is a hard constraint — the tooling *is* the capability here, so the platform is recorded as a constraint rather than left implementation-free.
- **Distribution**: A framework-dependent **.NET tool** is the launch target; per-platform ahead-of-time native packaging is deferred until the code is trim-warning-clean.
- **License posture**: Generated code is **license-safe by default**; commercial packages are opt-in.
- **Transition**: The v1 Python implementation and its test suite are **kept in place as the runnable reference spec** until the new implementation passes the contract suite, then removed.
- **Scope**: The full scope (engine + all four host projectors + corpus rebuild + new artifacts) is built in dependency order; the MVP and convergence anchor are US1 + US2 (engine + Claude projection + rule delivery + green build/tests).
- **Reference**: The v1 behavior (its exit-code contract, footprint bound, runtime resolution, manifest/upgrade semantics) is the behavioral reference these requirements preserve.

## Dependencies

- .NET 10 SDK present on the build/dev machine.
- Git for version control and multi-repo orchestration.
- The supported assistant CLIs (Claude Code, Codex CLI, Cursor, GitHub Copilot) for per-host install smoke tests, where present.

## Out of Scope (v2.0)

- Hard dependency on assistant preview features (agent teams, dynamic workflows).
- A heavyweight runtime router over skills (selection is description + graph + a thin disambiguator).
- Deep MAUI coverage.
- Cloud-agent plugin parity beyond render-to-files.
- Per-platform native AOT packaging (deferred per Assumptions).

## Traceability

| Area | Source of decision |
|---|---|
| Requirements baseline (FR/NFR/SC) | planning/25-v2-requirements.md |
| Locked decisions, build order, accepted refinements | planning/26-v2-build-plan-and-decisions.md (authoritative) |
| Architecture, project structure, artifact catalog, selector/gates | planning/21–24 |
| Governing principles | .specify/memory/constitution.md (v1.0.8) |
| The v1 rule-delivery defect (motivating bug) | issues/rule-enforcement-gap/ |
| Adversarial design review | issues/v2-design-review/ |
