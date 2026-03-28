# Feature Specification: v1 Release Polish & Roadmap Alignment

**Feature Branch**: `012-v1-release-polish`
**Created**: 2026-03-28
**Status**: Draft
**Input**: User description: "v1 Release Polish & Roadmap Alignment — fix plugin.json schema, rewrite command descriptions, add security docs, fix hooks, create AGENTS.md, verify missing skills, update version roadmap for v1.1/v1.2+ corrections"

## Clarifications

### Session 2026-03-28

- Q: AGENTS.md scope for v1? -> A: Simple project context file for Claude Code. Full cross-tool support is v1.1.
- Q: Keep informational arrays in plugin.json? -> A: Yes — useful for marketplace discoverability.
- Q: Missing skills from inventory — create or defer? -> A: Verify which of #84-93 are missing and create them as v1.0 deliverables.
- Q: GraphQL promotion to v1.2? -> A: Yes, promote from v2.0 to v1.2 — HotChocolate now has Apollo Federation v2.
- Q: Wolverine in v1.1 or v1.2? -> A: v1.1 for awareness/docs, v1.2 for full skill implementation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Plugin Marketplace Compliance (Priority: P1)

A developer discovers dotnet-ai-kit on the Claude Code marketplace. The plugin manifest passes schema validation, command descriptions trigger correctly when the developer types natural language prompts, and the README builds trust with a clear security section.

**Why this priority**: Non-compliant manifest and generic descriptions block marketplace acceptance and daily usability. This is the v1.0 release gate.

**Independent Test**: Validate plugin.json schema, verify all 27 descriptions contain "Use when" triggers, verify README has security section.

**Acceptance Scenarios**:

1. **Given** the plugin.json, **When** validated against the official schema, **Then** no warnings for `tags` or `author` type.
2. **Given** any of the 27 command descriptions, **When** read by Claude's matcher, **Then** it contains "Use when" trigger language.
3. **Given** the README, **When** a team lead evaluates the plugin, **Then** a "Security & Permissions" section explains hooks, permissions, and safety guards.

---

### User Story 2 — Hook Reliability & Project Context (Priority: P2)

A developer installs the plugin and hooks work reliably without hanging. An AGENTS.md file at the root provides project context to the AI assistant.

**Why this priority**: Hanging hooks block all interactions. AGENTS.md positions for cross-tool compatibility in v1.1.

**Independent Test**: Verify all hooks have timeout fields. Verify AGENTS.md exists with tool-agnostic project context.

**Acceptance Scenarios**:

1. **Given** any hook execution, **When** a script hangs, **Then** it times out after the configured limit.
2. **Given** the AGENTS.md file, **When** read by any AI tool, **Then** it contains project setup, architecture detection, workflow, and conventions in plain markdown.

---

### User Story 3 — Complete v1.0 Skill Inventory (Priority: P2)

A developer using the tool has access to all skills that were planned for v1.0. The 10 cross-cutting skills from the expanded inventory (#84-93) all exist as SKILL.md files — none are missing.

**Why this priority**: Planned skills that don't exist as files are broken promises. Users expect the advertised skill count to be real.

**Independent Test**: For each of the 10 planned cross-cutting skills, verify the SKILL.md file exists. Create any that are missing.

**Acceptance Scenarios**:

1. **Given** the expanded skill inventory listing skills #84-93, **When** checking the filesystem, **Then** all 10 have corresponding SKILL.md files.
2. **Given** a missing skill from the inventory, **When** created, **Then** it follows the standard format (metadata block, core principles, patterns, decision guide, anti-patterns).

---

### User Story 4 — v1.0 Roadmap Documentation (Priority: P3)

A contributor reads the version roadmap and sees all v1.0 late additions properly documented — the 10 paradigm skills, 6 new rules, skill frontmatter refactor, marketplace support, and AGENTS.md.

**Why this priority**: Planning docs must reflect reality for contributor alignment.

**Independent Test**: Version roadmap v1.0 Late Additions section includes all items added during this release cycle.

**Acceptance Scenarios**:

1. **Given** the version roadmap, **When** reading v1.0 Late Additions, **Then** it lists: 10 paradigm skills, 6 enforcement rules, skill frontmatter refactor to Agent Skills spec, marketplace.json + hook registration, AGENTS.md.

---

### User Story 5 — v1.1 Roadmap Corrections (Priority: P3)

A contributor reads the v1.1 section and sees corrected priorities reflecting the 2026 .NET ecosystem: NServiceBus promoted from v2.0, MassTransit licensing warnings, Wolverine as free alternative, .NET 10 LTS explicit, Aspire expanded, cross-tool AGENTS.md support.

**Why this priority**: Roadmap accuracy ensures the right work is prioritized next.

**Independent Test**: v1.1 section contains NServiceBus, MassTransit licensing note, Wolverine, .NET 10, expanded Aspire, cross-tool support.

**Acceptance Scenarios**:

1. **Given** the v1.1 roadmap section, **When** reading messaging, **Then** NServiceBus is listed (promoted from v2.0), MassTransit has licensing warning, Wolverine is free alternative.
2. **Given** the v1.1 section, **When** reading platform, **Then** .NET 10 LTS is explicit with C# 14 features, Aspire has deep patterns.

---

### User Story 6 — v1.2+ Roadmap Additions (Priority: P3)

A contributor reads v1.2+ and sees new items: Semantic Kernel, Wolverine full support, GraphQL promoted from v2.0, Blazor United templates.

**Why this priority**: Future planning accuracy.

**Independent Test**: v1.2 section contains Semantic Kernel, Wolverine, GraphQL (promoted), Blazor United.

**Acceptance Scenarios**:

1. **Given** the v1.2 section, **When** reading new additions, **Then** Semantic Kernel, Wolverine, GraphQL (HotChocolate), and Blazor United are listed.
2. **Given** v2.0, **When** reading scope, **Then** EventStoreDB, Marten, Strangler Fig, Service Mesh, Azure Functions, Multi-Cloud remain.

---

### Edge Cases

- What if a planned skill #84-93 already exists under a different path? Search by skill name pattern, not just exact path.
- What if plugin.json has non-standard fields Claude Code ignores? Keep them — they're informational for marketplace discoverability.
- What if hook timeout is too short for `dotnet format` on large solutions? Use generous timeouts (30s).
- What if AGENTS.md conflicts with CLAUDE.md? CLAUDE.md takes precedence. AGENTS.md is supplementary context.

## Requirements

### SCOPE 1: v1.0 Implementation (CRITICAL + HIGH)

#### Plugin Manifest
- **FR-001**: Rename `tags` to `keywords` in plugin.json.
- **FR-002**: Convert `author` from string to object with `name` and `url`.
- **FR-003**: Update plugin.json description to reflect current counts (120 skills, 15 rules).

#### Command Descriptions
- **FR-004**: Rewrite all 27 command descriptions in plugin.json with action verb + "Use when..." trigger format, each under 200 characters.
- **FR-005**: Update YAML `description` field in all 27 command .md files to match plugin.json.

#### Security Documentation
- **FR-006**: Add "Security & Permissions" section to README.md with: access scope, 4 hooks table, 3 permission levels table, safety guarantees.

#### Hook Configuration
- **FR-007**: Add `timeout` to all 4 hooks in settings.json (bash-guard: 10s, commit-lint: 30s, edit-format: 30s, scaffold-restore: 15s).
- **FR-008**: Add `statusMessage` to all 4 hooks for user feedback.

#### AGENTS.md
- **FR-009**: Create AGENTS.md at root — tool-agnostic plain markdown with project setup, build/test, architecture detection, SDD workflow, conventions, testing.

#### Missing Skills Verification
- **FR-010**: Verify skills #84-93 from expanded inventory exist as SKILL.md files. List: event-versioning (#84), db-migrations (#85), rate-limiting (#86), performance-testing (#87), cors-configuration (#88), event-catalogue (#89), real-time (#90), feature-flags (#91), multi-tenancy (#92), grpc-design (#93).
- **FR-011**: Create any missing skills following standard format (metadata frontmatter, core principles, patterns, decision guide, anti-patterns, max 400 lines).

#### Marketplace JSON
- **FR-012**: Update marketplace.json to match plugin.json changes (keywords, author, description counts).

### SCOPE 2: v1.1 Roadmap Corrections (planning docs only)

- **FR-013**: Promote NServiceBus from v2.0 to v1.1 in version roadmap.
- **FR-014**: Add MassTransit v9 licensing warning to v1.1 (commercial $400+/mo, v8 EOL 2026).
- **FR-015**: Add Wolverine messaging framework to v1.1 as free open-source alternative.
- **FR-016**: Make .NET 10 LTS support explicit in v1.1 (templates, detection, C# 14 features).
- **FR-017**: Expand Aspire from "enhanced orchestration" to deep patterns (module isolation, dashboard, Polly, Directory.Build.props, CI/CD).
- **FR-018**: Add cross-tool AGENTS.md support to v1.1 (Cursor, Copilot, Codex, Windsurf).

### SCOPE 3: v1.2+ Roadmap Additions (planning docs only)

- **FR-019**: Add Semantic Kernel to v1.2 (architecture/semantic-kernel skill for AI-augmented microservices).
- **FR-020**: Add Wolverine full support to v1.2 (messaging skills).
- **FR-021**: Promote GraphQL (HotChocolate) from v2.0 to v1.2 (Apollo Federation v2 support).
- **FR-022**: Add Blazor United templates to v1.2 (unified server/client rendering, AOT).
- **FR-023**: Confirm Dapr stays in v1.2 with Aspire integration noted.
- **FR-024**: Confirm v2.0 scope unchanged (EventStoreDB, Marten, Strangler Fig, Service Mesh, Azure Functions, Multi-Cloud, Antigravity).

### v1.0 Roadmap Documentation
- **FR-025**: Update planning/12-version-roadmap.md v1.0 Late Additions with: 10 paradigm skills, 6 enforcement rules, skill frontmatter refactor, marketplace support, hook registration, AGENTS.md.

## Success Criteria

- SC-001: plugin.json uses `keywords` (not `tags`) and `author` is an object
- SC-002: All 27 command descriptions contain "Use when" trigger language
- SC-003: README.md has "Security & Permissions" section with hooks, permissions, safety
- SC-004: All 4 hooks have `timeout` and `statusMessage` fields
- SC-005: AGENTS.md exists at root with tool-agnostic project context
- SC-006: All 10 cross-cutting skills (#84-93) exist as SKILL.md files
- SC-007: Version roadmap v1.0 Late Additions is complete
- SC-008: v1.1 section has NServiceBus, MassTransit licensing, Wolverine, .NET 10, expanded Aspire, cross-tool
- SC-009: v1.2 section has Semantic Kernel, Wolverine, GraphQL (promoted), Blazor United
- SC-010: v2.0 scope unchanged
