# Feature Specification: Plugin Token Optimization & Sustainability

**Feature Branch**: `018-token-optimization`
**Created**: 2026-05-09
**Status**: Draft
**Input**: User description: "Use planning/19-optimization-roadmap.md Parts B-H as the reference (Part A multi-repo work is out of scope). Build a clean specification for the token-reduction and sustainability initiative across the plugin surface."

## Overview

This feature delivers an end-to-end reduction in the per-invocation token cost of the dotnet-ai-kit plugin while preserving (and ideally improving) the quality of dispatched assistance. The plugin currently emits 150K-250K tokens before any code is written on heavy lifecycle commands such as `/dai.do` and `/dai.implement`, driving a $200-300/dev/month cost on heavy use. The initiative reorganizes content discovery so the host AI tool loads only what each task needs, establishes regression-proof guardrails so future contributors cannot silently re-bloat the surface, and adds an opt-in memory/symbol-navigation integration that compounds savings further. The work is bundled into three independently-shippable phases so that even Phase 1 alone delivers a viable cost reduction; later phases compound on the foundation. Multi-tool portability is treated as a cross-cutting requirement: equivalent savings must reach users running Cursor, GitHub Copilot, Codex CLI, and Gemini CLI via the existing per-tool projection layer.

## Stakeholders

- **End users** — .NET developers invoking `/dai.*` commands during day-to-day feature work (the dollars-per-month, latency, and accuracy lens).
- **Plugin maintainers** — contributors who author and update skills, commands, agents, and rules (the regression-prevention and authoring-ergonomics lens).
- **Multi-tool integrators** — teams running dotnet-ai-kit through Cursor, Copilot, Codex, or Gemini rather than Claude Code (the portability lens).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Foundation: drop the per-invocation token cost on heavy commands (Priority: P1)

A .NET developer who today watches their token consumption climb 150K-250K every time they invoke `/dai.do` or `/dai.implement` runs the same command after Phase 1 ships and observes a substantial drop in tokens consumed before code is generated, without losing the assistance quality that made them choose the plugin.

**Why this priority**: This is the dominant cost driver and the headline outcome of the entire initiative. Foundation alone (description hygiene, removal of eager content loads from commands and agents, and rule scoping for non-Claude tools) targets a ~70% reduction. Shipping just P1 makes the plugin financially viable for heavy daily use; everything else compounds on it.

**Independent Test**: Can be fully validated by running a representative sample of `/dai.do`, `/dai.implement`, and `/dai.add-event` invocations against fixed feature inputs, measuring the per-invocation token cost from telemetry, and confirming the drop hits the targeted reduction band while a smoke-test set of dispatched skills still loads correctly.

**Acceptance Scenarios**:

1. **Given** a baseline measurement captured before the change, **When** a developer runs the same `/dai.implement` invocation after Phase 1 ships, **Then** the per-invocation token cost MUST drop by at least 60% relative to baseline.
2. **Given** a `/dai.do` full-lifecycle invocation, **When** measured after Phase 1, **Then** the per-invocation cost MUST drop from ~200K to ≤80K tokens.
3. **Given** a Cursor user with the same plugin installed, **When** a session starts after Phase 1, **Then** the always-loaded rule footprint MUST drop from ~9K tokens to ~1K tokens.
4. **Given** the standard dispatcher smoke-test suite (e.g., "add an event", "scaffold a query entity"), **When** run after Phase 1, **Then** the correct skill MUST be auto-selected on at least the same percentage of cases as the baseline (no accuracy regression).

---

### User Story 2 - Hygiene & guardrails: prevent silent regression (Priority: P2)

A plugin maintainer reviewing a contributor's pull request that adds a new skill or extends a command can rely on automated checks that reject changes which would silently re-introduce the cost patterns Phase 1 eliminated, instead of catching the regression months later when an end user complains about their bill.

**Why this priority**: Without measurement and enforcement, Phase 1 savings decay over time as contributors revert to familiar patterns. Phase 2 establishes (a) a token audit CLI that fails CI when budgets are violated, (b) hard line-count limits on skill bodies, and (c) a trimmed shipped CLAUDE.md template using the index-then-detail pattern. P2 is what makes P1 a durable platform improvement rather than a one-time cleanup.

**Independent Test**: Can be fully validated by deliberately introducing each known anti-pattern (oversized skill body, weak description, eager Read in a command, excess always-on rules) into a test branch, running the audit CLI, and confirming each violation is detected and reported with a clear remediation pointer.

**Acceptance Scenarios**:

1. **Given** a contributor commits a SKILL.md whose body exceeds the documented line limit, **When** the audit runs, **Then** the violation MUST be reported as a hard failure with the offending file and line count.
2. **Given** a command file containing eager content-load instructions that bypass dispatcher-driven loading, **When** the audit runs, **Then** the offending command and pattern MUST be flagged.
3. **Given** a freshly-initialized .NET project, **When** the shipped CLAUDE.md template is examined, **Then** it MUST be ≤50 lines and use an index-then-detail "Further Reading" pattern rather than inlining content.
4. **Given** a maintainer running the audit locally, **When** the audit completes, **Then** an estimated per-command token cost MUST be reported for every command in the surface so trends are visible across releases.

---

### User Story 3 - Advanced compounding: cache, isolation, and opt-in MCP (Priority: P3)

A developer with the plugin already on Phase 2 elects to enable the optional MCP catalog and observes a further drop on iterative loops (resuming a feature, re-running a phase) such that a full `/dai.do` lifecycle now costs roughly 1/9 of the original baseline, while a developer who chooses not to enable MCPs sees no change relative to Phase 2.

**Why this priority**: Phase 3 contains the highest-leverage compounding wins (cache-friendly prompt ordering, optional subagent isolation for the longest commands, and an opt-in MCP catalog providing persistent memory and symbol navigation), but each carries either a non-Claude portability gap or an authoring/operational risk that must be measured against P1+P2 baselines before being shipped to all users. Making them opt-in or conditional preserves the durability of the P1+P2 wins while letting power users push further.

**Independent Test**: Can be fully validated by (a) measuring iterative-invocation token cost (e.g., `/dai.implement --resume`) before and after the cache-friendly ordering ships, expecting cached-prefix invocations to cost ~10% of full-prefix invocations; and (b) installing a token-savior MCP profile via the new catalog command, re-running a sample feature lifecycle, and confirming the documented additional savings while users without the MCP installed see identical behavior to Phase 2.

**Acceptance Scenarios**:

1. **Given** a Phase 2 baseline, **When** Phase 3 ships and a developer re-runs a multi-step `/dai.implement` within the prompt-cache TTL window, **Then** subsequent invocations after the first MUST benefit from cached static-prefix tokens at the documented discount.
2. **Given** a developer who does not opt into the MCP catalog, **When** Phase 3 is installed, **Then** their token cost and behavior MUST match Phase 2 exactly (no forced dependency).
3. **Given** a developer who runs the new install-MCP catalog command for the recommended profile, **When** they re-run a sample `/dai.implement` (resume) invocation, **Then** the invocation MUST cost ≤12K tokens (down from a Phase 2 baseline of ~18K).
4. **Given** the longest commands have been refactored to delegate verbose orientation to an isolated subagent, **When** a `/dai.do` lifecycle runs, **Then** the orientation tokens MUST stay isolated from the main thread (only the subagent summary returns), AND total cost MUST NOT exceed the Phase 2 measurement (subagent overhead must not erase savings).

---

### Edge Cases

- **A skill description rewrite worsens dispatcher accuracy.** What happens when description hygiene improves dispatch on most cases but degrades it on one specialized skill (e.g., the dispatcher now picks `add-aggregate` when `add-event` is correct)? The audit MUST surface a measurable accuracy metric so this regression is detected before merge, and the spec MUST allow a per-skill description override that prioritizes correctness over hygiene if both cannot be reconciled.
- **Eager-Read removal causes a missed-skill failure on a critical workflow.** What happens when a command stops eagerly loading a skill the dispatcher fails to auto-pick in a low-frequency but critical scenario (e.g., event-sourced aggregate scaffolding)? Commands MUST retain a documented mechanism to declare "must-load" guarantees for critical paths without reverting to wholesale eager loading.
- **A contributor unaware of the line-count cap submits a 600-line SKILL.md.** What happens when the audit blocks the merge? The audit's failure message MUST point to the documented split pattern (overview-with-references) rather than only reporting the violation.
- **A Cursor user encounters an `alwaysApply` regression in a future Cursor release.** What happens if Cursor's interpretation of `alwaysApply` changes? Rule-scoping changes MUST be authored against documented Cursor semantics so the projection layer can adapt without code-side rewrites.
- **A subagent invocation hangs or runs away.** What happens when an isolated subagent for a long command does not terminate? Subagent invocations MUST have an idle/wall-clock timeout and a per-invocation token budget enforced from the calling command.
- **The MCP catalog install partially succeeds (e.g., entry written to user config, package install failed).** What happens when the install fails halfway? The catalog command MUST be transactional from the user's perspective: either both the registration and the package install succeed, or both are rolled back.
- **An existing Phase 1 user reverts to an older plugin version.** What happens when projection rules differ between versions? The shipped audit MUST be version-pinned to the plugin so older audits do not falsely flag newer constructs (and vice versa).

## Requirements *(mandatory)*

### Functional Requirements

#### Phase 1 — Foundation (token cost reduction)

- **FR-001**: The plugin MUST reduce per-invocation token cost on every command in the surface relative to a captured pre-change baseline, with documented per-command targets for the heaviest commands (`/dai.do`, `/dai.implement`, `/dai.add-event` minimum).
- **FR-002**: The plugin MUST rely primarily on description-driven dispatcher auto-loading for skills and agents rather than command-prescribed eager content loads.
- **FR-003**: Every skill description MUST be authored to documented hygiene rules (third-person voice, trigger keywords first, both *what* and *when*, within the per-description character cap).
- **FR-004**: Commands MUST retain a documented mechanism to mark critical-path skill loads where dispatcher auto-selection is insufficient, without reverting to wholesale eager loading.
- **FR-005**: Rules MUST be scoped to the file/path patterns where they apply, except for a small documented set of universal rules. A maximum of 2-3 rules MAY be declared always-on; the rest MUST be scoped.
- **FR-006**: Agent definitions MUST stop enumerating embedded skill lists in their bodies; relevant skills MUST be referenced via prose so dispatcher auto-loading remains the load mechanism.
- **FR-007**: All Phase 1 changes MUST project equivalently to non-Claude target tools (Cursor, Copilot, Codex, Gemini) through the existing projection layer, preserving ≥70% of the headline savings on those tools where the host runtime supports the underlying mechanism.

#### Phase 2 — Hygiene & guardrails (sustainability)

- **FR-008**: The plugin MUST ship an audit command that scans the surface and reports violations of token-budget rules: oversize skill bodies, oversized descriptions, excessive always-on rules, eager-Read patterns in commands, and description-quality issues (voice, missing trigger keywords).
- **FR-009**: The audit MUST report an estimated per-command token cost for every command in the surface so trend regressions across releases are visible to maintainers.
- **FR-010**: The audit MUST be runnable as a non-interactive CI step that fails the build on any hard violation.
- **FR-011**: Every skill body MUST stay within the documented line-count cap; oversized skills MUST be split using the documented overview-with-references pattern, with references kept one level deep from the parent skill.
- **FR-012**: The shipped project-level configuration template (`CLAUDE.md` template and per-tool equivalents) MUST follow the index-then-detail pattern, MUST stay within a documented size cap, and MUST NOT inline information already discoverable through dispatcher mechanisms.
- **FR-013**: The audit's failure messages MUST point users to the specific remediation pattern for each detected violation class.

#### Phase 3 — Advanced compounding (cache, isolation, opt-in MCP)

- **FR-014**: Commands that assemble prompts MUST place stable static content first and dynamic per-invocation input last so the runtime prompt cache can be reused across iterative invocations within the cache TTL.
- **FR-015**: The longest lifecycle commands MAY route their verbose orientation work into an isolated subagent so verbose context stays isolated from the main thread; if implemented, only the subagent's summary MUST return to the caller, AND the implementation MUST stay within documented hard guardrails (no upfront mass spawn, exclusion list of small commands, minimal context pass-through, idle termination, and a per-invocation token budget).
- **FR-016**: The plugin MUST ship an opt-in MCP catalog with a CLI verb that registers, installs, and configures curated MCP servers (memory, symbol navigation) and tracks installed MCPs per project.
- **FR-017**: Each catalog entry MUST ship with a tuned tool-advertising profile so that connecting the MCP does not exceed a documented per-MCP token-overhead cap.
- **FR-018**: Workflow skills MUST detect the availability of supported MCPs at runtime and conditionally use them; behavior for users without the MCP installed MUST be unchanged (filesystem-only fallback).
- **FR-019**: The MCP catalog command MUST be transactional from the user's perspective: registration in the project's MCP config, package install, and profile drop MUST all succeed or all roll back.

#### Cross-cutting (multi-tool portability & quality)

- **FR-020**: All authoring MUST treat SKILL.md as the canonical source. The projection layer MUST translate canonical content into each supported target tool's native format (Cursor `.mdc`, Copilot path-scoped instructions, Codex bundled `AGENTS.md`, Gemini SKILL.md).
- **FR-021**: Phase 1 changes MUST NOT degrade dispatcher accuracy on a documented smoke-test set of representative invocations relative to the pre-change baseline.
- **FR-022**: Each phase MUST be independently releasable: Phase 1 ships value with no dependence on Phase 2 or 3, and Phase 2 ships without requiring Phase 3.
- **FR-023**: The initiative MUST publish documented before/after measurements per phase so end users and maintainers can verify savings on their workloads.

#### Open scope decisions (require resolution before planning)

- **FR-024**: System MUST [NEEDS CLARIFICATION: subagent stubs scope — include subagent isolation (Change 9) in Phase 3 unconditionally, OR ship Phase 3 without it and reopen the decision after Phase 2 measurements? Trade-off: subagent isolation provides additional savings but introduces medium implementation risk and cannot project to non-Claude tools, while Phase 1+2 alone may already meet the cost target.]
- **FR-025**: System MUST [NEEDS CLARIFICATION: skill-surface size — keep all 124 skills as authored (Change 1 is purely a description hygiene pass), OR consolidate the surface to a smaller count (Change 1 becomes a structural restructure)? Trade-off: a hygiene-only pass is bounded effort with zero behavior change; consolidation is a larger product decision affecting end users and contributors.]
- **FR-026**: System MUST [NEEDS CLARIFICATION: MCP catalog scope — ship the catalog with the recommended memory/symbol-navigation MCP only, OR also ship documented alternatives (managed-cloud and zero-config variants)? Trade-off: a single curated entry minimizes maintenance and reputation risk; multiple entries give users choice but expand the support surface.]

### Key Entities *(include if feature involves data)*

- **Skill (canonical SKILL.md)**: A unit of dispatched expertise. Has a description (the dispatcher's match key), a body (within the line-count cap), and may have one-level-deep reference files for advanced content.
- **Command**: A user-invokable lifecycle or codegen entry point. Has a body (within the documented size cap) that delegates to dispatcher-driven skill/agent loading rather than enumerating loads up front.
- **Agent**: A specialist persona. References related skills via prose so dispatcher auto-loading drives skill selection.
- **Rule**: A convention statement. Carries metadata declaring whether it is universally always-on or scoped to specific file/path patterns.
- **Audit Report**: The output of the maintainer-facing audit. Records each violation class (oversize skill body, weak description, eager Read, excess always-on rules), per-command estimated token cost, and remediation pointers.
- **MCP Catalog Entry**: A curated MCP integration. Records the registration command, install command, tuned profile, and per-project install state.
- **Token Baseline / Measurement**: A captured per-invocation token cost for a fixed sample of representative commands, recorded per phase to verify acceptance scenarios.
- **Projection Mapping**: The rule set that translates canonical SKILL.md, command, agent, and rule content into each supported target tool's native format.

## Success Criteria *(mandatory)*

### Measurable Outcomes

#### Token cost (per-invocation, on representative samples)

- **SC-001**: After Phase 1, a `/dai.do` full-lifecycle invocation costs ≤80K tokens (baseline: ~200K) — a ≥60% reduction.
- **SC-002**: After Phase 1, a `/dai.implement` invocation costs ≤40K tokens (baseline: ~90K) — a ≥55% reduction.
- **SC-003**: After Phase 1, a `/dai.add-event` invocation costs ≤15K tokens (baseline: ~25K) — a ≥40% reduction.
- **SC-004**: After Phase 1, a Cursor user's always-loaded session footprint costs ≤1.5K tokens (baseline: ~9K) — an ≥80% reduction.
- **SC-005**: After Phase 2 ships, the cumulative reduction relative to baseline is ≥75% on `/dai.do` and ≥65% on `/dai.implement` (with no regression to the Phase 1 results).
- **SC-006**: After Phase 3 ships, an opted-in user's `/dai.do` lifecycle costs ≤25K tokens (baseline: ~200K) — an ≥85% reduction.
- **SC-007**: After Phase 3 ships, a non-opted-in user's per-invocation cost matches Phase 2 within 5% (no involuntary overhead from MCP scaffolding).

#### Cost per developer

- **SC-008**: After Phase 1, monthly heavy-use plugin token cost per developer drops from $200-300 to ≤$110 (≥55% reduction).
- **SC-009**: After Phase 3 (with opt-in MCP), monthly heavy-use plugin token cost per developer drops to ≤$45 (≥80% reduction).

#### Quality (no regression)

- **SC-010**: Dispatcher auto-selection accuracy on the documented smoke-test set after Phase 1 is at least equal to the pre-change baseline.
- **SC-011**: After Phase 2, contributor PRs that violate any token-budget rule are caught automatically before merge in 100% of detectable cases (validated against a curated set of synthetic violations).

#### Multi-tool portability

- **SC-012**: After Phase 1, equivalent measurable savings are observed on Cursor, Copilot, Codex, and Gemini targets via the projection layer, capturing at least 70% of the headline reduction where the host runtime supports the underlying mechanism.

#### Latency (qualitative)

- **SC-013**: Time-to-first-action on heavy commands (`/dai.do`, `/dai.implement`) measurably improves after Phase 1 because the host AI no longer ingests 100K+ tokens of orientation before producing output.

## Assumptions

- The host AI tool (Claude Code, Cursor, Copilot, Codex, Gemini) is responsible for description-driven skill auto-loading; this initiative does not change runtime behavior of those hosts, only the content the plugin surfaces to them.
- Baseline measurements will be captured before any Phase 1 change lands and stored as the reference point for SC-001 through SC-009.
- The 124-skill count and existing per-tool projection layer remain in place as the starting surface; structural reorganization of skills (consolidation) is gated on FR-025 resolution.
- Opt-in MCP servers are external to the plugin; this initiative ships only the catalog/installer/profile metadata, not the MCP servers themselves.
- The runtime prompt cache TTL behavior described by Anthropic (5-minute window, cache-control discount) is a host-runtime feature; cache-friendly ordering only enables it.
- Multi-tool portability targets the same five tools listed in the roadmap's Section D; expansion to additional tools is out of scope for this feature.
- The roadmap's Part A (multi-repo feature setup) is explicitly out of scope and tracked separately.

## Out of Scope

- Multi-repo feature setup decisions (Part A of the source roadmap), including bidirectional repos propagation, the `feature sync` CLI verb, `feature_status.json` artifacts, full re-detection on sibling init, and the `coordinated_branch_base` config field. These are tracked in a separate feature.
- Restructuring or consolidating the 124-skill surface, unless FR-025 is resolved in favor of consolidation.
- Bundling MCP servers as default dependencies of `dotnet-ai init`. The catalog is opt-in by design.
- Vendor selection for the MCP catalog beyond the curated entries listed in the roadmap.
- Changes to host AI tool runtimes (Claude Code, Cursor, Copilot, Codex, Gemini); this initiative changes only plugin-side authored content and tooling.
- Resolution of upstream tracker issues (e.g., the open Anthropic issue on `/context` skill body accounting); these are watched, not fixed by this feature.

## Dependencies

- Existing per-tool projection logic in the plugin (the codepath that translates canonical authored content into each supported tool's native format) must remain operational; portability requirements compose on top of it.
- The host AI tool's description-driven dispatch mechanism must function as documented; the initiative depends on this contract for FR-002.
- Captured baseline measurements (per the Assumptions section) are a precondition for verifying every quantitative success criterion.
- Resolution of FR-024, FR-025, and FR-026 before the planning phase begins, because each materially changes Phase 3 and Phase 1 scope.
