# Feature Specification: dotnet-ai-kit v2 - Profile, Rule, and Dynamic Delivery

**Feature Branch**: `024-v2-profile-rule-and-dynamic-delivery`  
**Created**: 2026-06-02  
**Status**: Draft  
**Input**: User description: "Make authored profiles and dynamic guidance delivery real while reducing duplicate or misleading rule/profile injection. Deliver profiles in two tiers (architecture-tier always-on, role/band-tier path-scoped), fix the Claude output-style that names a profile it never delivers, deduplicate profiles against universal rules, narrow the agreed broad rule globs, make deterministic-enforcement universal/doc-only, and project MCP/LSP host configuration as static artifacts. Keep the kit's own MCP server runtime, new W7 skills/agents, script porting, and analyzer expansion out of scope."

## Overview

The 12 authored profiles are length-validated and present in the corpus graph, yet they reach **no host by any channel**: no projector emits them, and the Claude output-style names an architecture profile whose content never ships. Separately, several rules over-claim path scope (narrow-slice constraints that load into every C# edit), `deterministic-enforcement` carries a false just-in-time glob, and several profiles restate universal-rule content verbatim — so turning on always-on profile delivery would double-inject those generic constraints. Finally, MCP and LSP configuration live only as repo-root developer config, projected by nothing and wired into no agent.

This feature makes profile delivery real (two tiers), removes the duplicate rule/profile injection so always-on profile delivery is safe, narrows the dishonest rule globs, and projects MCP/LSP host configuration as static artifacts. It builds directly on the `023` corpus-correctness foundation and precedes the script (`025`), progressive-disclosure (`026`), analyzer (`027`), and expansion (`028`) work. It corresponds to `planning/29-v2-execution-plan-fidelity-and-enhancement.md` Phases C, D2, and D3 (supported by `planning/28` W1.1, W1.3, W5.1, W5.2).

## Clarifications

### Session 2026-06-02

- Q: When `project.yml` declares no architecture or an unrecognized value, should architecture-profile delivery default or fail? → A: Default to the `generic` architecture profile (the catch-all), delivered always-on like any other architecture-tier selection; a strict-mode error is out of scope for this feature.
- Q: Should `deterministic-enforcement` become a universal always-on rule or a doc-only reference? → A: Universal (always-apply, no path glob), carried as a concise registry/pointer to its analyzer-backed constraints — universal scope with doc-like content, not a path-scoped rule (per `planning/29` M1).

Deferred to `/speckit.plan` (recorded so they are not lost; both are HOW decisions rather than WHAT ambiguities):

- The Claude always-on profile **content**-delivery mechanism (embed the selected profile into a per-project output-style generated at `init` vs. a hook channel) carries a determinism/drift implication, because per-project files lie outside the `build/` baseline. Captured in Edge Cases and Assumptions.
- Final confirmation of the 6/6 architecture-vs-role tier split (`planning/29` M3) — the split is specified; confirmation is a design-time check.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Architecture Profile Reaches the Project as Always-On Guidance (Priority: P1)

A developer who initializes or projects the kit into a .NET solution with a declared architecture (clean-arch, ddd, modular-monolith, vsa, hybrid, or generic) receives that one architecture profile's guidance as always-on project context, and the Claude output-style both names it and delivers its content.

**Why this priority**: Profiles are the single highest-value authored-but-undelivered asset, and the output-style currently references a profile whose content never ships — a visible broken promise. Delivering the architecture profile is the headline outcome of this feature.

**Independent Test**: Initialize or project a solution whose `project.yml` declares an architecture, then confirm the matching profile's content is present in the host's always-on context and that no other architecture profile is delivered.

**Acceptance Scenarios**:

1. **Given** a project that declares `architecture: clean-arch`, **When** the kit is initialized/projected, **Then** the clean-arch profile content is delivered as always-on project context and the other architecture profiles are not.
2. **Given** the Claude output-style references the selected architecture profile, **When** delivery runs, **Then** the profile's content actually reaches the host, not merely its name.
3. **Given** a declared architecture with no matching profile, or an absent architecture value, **When** delivery runs, **Then** the system delivers the `generic` architecture profile as the default — never a silent omission.

---

### User Story 2 - Guidance Is Not Duplicated Across Rules and Profiles (Priority: P1)

A developer does not receive the same generic constraint twice — once from an always-on universal rule and once from an always-on profile. Profiles carry only architecture- or role-specific constraints and reference the universal rules for everything generic.

**Why this priority**: This is a hard prerequisite for safe always-on profile delivery (US1). If profiles still restate universal-rule content, turning on always-on profile delivery double-injects every duplicated constraint.

**Independent Test**: Inspect each profile against the universal rules and assert that no profile restates a universal-rule constraint; a deduplication check passes over the corpus.

**Acceptance Scenarios**:

1. **Given** profiles that previously restated universal-rule content (e.g., generic, vsa, clean-arch, ddd, modular-monolith), **When** they are deduplicated, **Then** they retain only architecture-specific guidance and reference the universal rules.
2. **Given** always-on delivery of a profile alongside the always-on universal rules, **When** both are delivered, **Then** no single generic constraint is stated by both.

---

### User Story 3 - Role/Band Profiles Deliver Additively and Path-Scoped (Priority: P2)

A developer working in a specific area (command, query-cosmos, query-sql, gateway, processor, or controlpanel) receives the matching role profile only where it applies (path-scoped), additively — never all six injected always-on.

**Why this priority**: Role profiles target specific folders. Always-on injection of all six would multi-inject and bloat context. Path scoping preserves the just-in-time value without the bloat.

**Independent Test**: Confirm role-tier profiles are delivered path-scoped (not always-on) on hosts that support path scoping, and explicitly degraded to a static fallback where path scoping is unsupported.

**Acceptance Scenarios**:

1. **Given** a host that supports path scoping, **When** projection runs, **Then** role profiles are delivered path-scoped, not always-on.
2. **Given** a host without path scoping, **When** projection runs, **Then** role-profile guidance is delivered statically with the scope limitation acknowledged rather than silently always-on.

---

### User Story 4 - Rule Path-Scoping Is Honest (Priority: P2)

A developer editing C# does not load narrow-slice rules into every edit. The three agreed over-broad globs are narrowed to their real scopes, the meta-registry rule is universal/doc-only rather than a fake path-scoped rule, and genuinely broad rules stay broad.

**Why this priority**: JIT-defeating globs bloat always-on tokens and tell a false just-in-time story; they also undermine the credibility of the path-scoping mechanism that US3 relies on.

**Independent Test**: Inspect rule scoping and assert that mediator-abstraction, messaging-bus-selection, and ai-integration are narrowed, that error-handling and performance remain broad, and that deterministic-enforcement is universal/doc-only.

**Acceptance Scenarios**:

1. **Given** mediator-abstraction, messaging-bus-selection, and ai-integration previously scoped to all C#, **When** narrowed, **Then** each applies only to its real scope.
2. **Given** error-handling and performance, **When** scoping is reviewed, **Then** they remain broad because coverage outweighs idle-token economy.
3. **Given** deterministic-enforcement (a registry pointing at analyzers), **When** scoping is reviewed, **Then** it is universal/doc-only with no false path glob.

---

### User Story 5 - MCP and LSP Configuration Is Projected to Hosts (Priority: P2)

A user installing the kit receives host MCP configuration generated from a single descriptor, deterministically, with LSP configuration where the host supports it and an explicit unsupported marker where it does not. Navigation-capable agents are guided to prefer symbol-precise navigation when LSP is available.

**Why this priority**: MCP and LSP are repo-root developer config today, projected by nothing and wired into no agent. Projecting them from one source closes a real delivery gap and sets up later MCP-server install wiring.

**Independent Test**: Generate output and assert each supported host receives its MCP configuration from the single descriptor, LSP configuration is present for supported hosts and explicitly absent/marked for unsupported ones, and the generated files are byte-stable.

**Acceptance Scenarios**:

1. **Given** a single MCP descriptor, **When** projection runs, **Then** each supported host receives its MCP configuration form from that one source.
2. **Given** LSP support that differs by host, **When** projection runs, **Then** LSP configuration is projected where supported and explicitly marked unsupported where not.
3. **Given** the navigation-capable agents, **When** their guidance is reviewed, **Then** it prefers symbol-precise navigation when LSP is available.

---

### Edge Cases

- **Missing or unknown `architecture:`** in `project.yml` -> deliver the `generic` architecture profile as the default; never silently omit profile delivery.
- **Always-on profile content requires a per-project generated artifact** (e.g., emitted at `init` because architecture is per-project, not known at build time) -> the artifact's determinism must be defined, because per-project files lie outside the `build/` drift baseline. The exact Claude content-delivery mechanism (embed the selected profile into a per-project output-style vs. a hook channel) is a design decision deferred to planning.
- **Two role-profile path scopes overlap** -> delivery must not multi-inject the same profile for one edit.
- **A host lacks a capability** (always-on, path scoping, dynamic gating, or LSP) -> the capability is represented explicitly with the closest static fallback, never a silent gap.
- **MCP/LSP descriptor changes** -> all host configurations regenerate deterministically from the single source with no drift.

## Requirements *(mandatory)*

### Functional Requirements

**Profile delivery**

- **FR-001**: The system MUST deliver authored profiles to supported hosts rather than only loading them into the corpus.
- **FR-002**: The system MUST classify profiles into an architecture tier (clean-arch, ddd, modular-monolith, vsa, hybrid, generic) and a role/band tier (command, query-cosmos, query-sql, gateway, processor, controlpanel).
- **FR-003**: The system MUST select exactly one architecture-tier profile based on the project's declared architecture and deliver its content as always-on project context.
- **FR-004**: Architecture-profile delivery MUST deliver profile content, not only the profile name, resolving the Claude output-style that references a profile whose content never ships.
- **FR-005**: Role/band-tier profiles MUST be delivered additively and path-scoped where the host supports path scoping; they MUST NOT all be injected always-on.
- **FR-006**: When the declared architecture has no matching profile or is absent, the system MUST deliver the `generic` architecture profile as the default and MUST NOT silently omit profile delivery; a strict-mode error for unmatched values is out of scope for this feature.

**Per-host channel**

- **FR-007**: Profile delivery MUST define a delivery channel per host: Claude (always-on content), Codex (static guidance, no dynamic gating), Cursor (path-scoped projected guidance), Copilot (instruction guidance with `applyTo` where supported).
- **FR-008**: Where a host cannot honor a delivery capability (always-on, path scoping, or dynamic gating), the limitation MUST be represented explicitly rather than silently dropped.

**Deduplication / coherence (prerequisite for always-on delivery)**

- **FR-009**: Before always-on profile delivery, profiles MUST be deduplicated against the universal rules so a generic constraint is not delivered by both a rule and a profile.
- **FR-010**: Profiles MUST carry only architecture- or role-specific constraints and reference the universal rules for generic constraints.

**Rule scoping**

- **FR-011**: The system MUST narrow the three agreed over-broad rule globs (mediator-abstraction, messaging-bus-selection, ai-integration) to their real scopes.
- **FR-012**: The system MUST keep genuinely broad rules (error-handling, performance) broad, prioritizing coverage over idle-token economy.
- **FR-013**: The deterministic-enforcement rule MUST be represented as a universal (always-apply) registry/pointer to its analyzer-backed constraints — universal scope with doc-like content — rather than a path-scoped rule that tells a false just-in-time story.
- **FR-014**: Touched testing-rule guidance MUST be free of v1/Python residue, verifying and completing the removal begun in feature `023`.

**MCP / LSP projection (static configuration only)**

- **FR-015**: The system MUST project host MCP configuration from a single descriptor into each supported host's generated output.
- **FR-016**: The system MUST project LSP configuration for hosts where agent-facing LSP is supported or preview-supported and MUST mark it explicitly unsupported for the others.
- **FR-017**: Navigation-capable agents MUST be updated to prefer symbol-precise navigation when LSP is available.
- **FR-018**: Projected MCP and LSP files MUST be deterministic (byte-stable across regenerations).

**Single-source / process**

- **FR-019**: All delivered profile, rule, MCP, and LSP outputs MUST be single-source from `artifacts/` and host projectors; this feature MUST NOT rely on hand edits to generated files.
- **FR-020**: Generated `build/` output MUST remain drift-clean after this feature.
- **FR-021**: The feature's `tasks.md` MUST include a `Review & Verification` phase after implementation phases and before final polish.
- **FR-022**: The `Review & Verification` phase MUST verify profile content reaches initialized/projected host outputs, no duplicate profile/rule injection is introduced, generated MCP/LSP files are deterministic, and the standing gates pass.

### Key Entities

- **Profile (tiered)**: An authored guidance unit classified as architecture-tier (single-select, always-on) or role-tier (additive, path-scoped), with a name, an architecture mapping, and a scope.
- **Architecture selector**: The project's declared architecture, used to pick the single architecture-tier profile.
- **Delivery channel**: The per-host mechanism (always-on, path-scoped, or static) by which a profile or rule reaches a host.
- **MCP descriptor**: The single source from which each host's MCP configuration is projected.
- **LSP descriptor**: The single source from which LSP configuration is projected for supported hosts.
- **Duplication item**: A generic constraint stated by both a universal rule and a profile that must be removed from the profile.

### Assumptions

- The architecture-to-profile mapping is by name convention (`architecture: clean-arch` -> `clean-arch.md`), per `planning/29` M2; a mapping table is added only if the architecture value-space diverges from profile names.
- The 6/6 architecture-vs-role tier split is taken from the prompt and planning and is confirmed during design (`planning/29` M3).
- v1/Python residue in `rules/domain/testing.md` was already removed by feature `023`; FR-014 verifies and completes rather than re-does that removal.
- Codex `AGENTS.md` size trimming is out of scope here (it belongs to feature `026` / `planning/29` I3); this feature only adds static profile guidance to the Codex surface.
- The always-on profile content-delivery mechanism on Claude (embedding the selected profile into a per-project output-style generated at `init` vs. a hook channel) is a planning-time design decision; if a per-project artifact is required, its determinism must be defined because per-project files lie outside the `build/` drift baseline.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After init/projection of a solution declaring an architecture, the matching architecture profile's content is present in the host's always-on context (profile-delivery test), and no other architecture profile is delivered.
- **SC-002**: A rule/profile deduplication check passes: no profile restates a universal-rule constraint, so always-on delivery of profile-plus-rules injects each generic constraint at most once.
- **SC-003**: All standing gates pass (`dotnet build dotnet-ai-kit.slnx -warnaserror`, `dotnet test dotnet-ai-kit.slnx`, `dotnet format dotnet-ai-kit.slnx --verify-no-changes`, `dotnet run --project src/DotnetAiKit.Cli -- generate --check`) and generated `build/` output is drift-clean.
- **SC-004**: Each supported host receives MCP configuration projected from the single descriptor; LSP configuration is present for supported hosts and explicitly marked unsupported for the rest.
- **SC-005**: The three agreed over-broad rule globs are narrowed, error-handling and performance remain broad, and deterministic-enforcement is universal/doc-only — all verifiable by inspection or test.
- **SC-006**: Role/band-tier profiles are delivered path-scoped (not always-on) on path-capable hosts, with an explicit static fallback where path scoping is unsupported.
- **SC-007**: The feature's `tasks.md` contains an explicit `Review & Verification` phase before final polish.
