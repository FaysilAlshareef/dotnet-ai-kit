<!--
Sync Impact Report
===================
- Version change: 1.0.8 → 1.1.0
- Modified principles: NONE — all five core principles (Detect-First,
  Pattern Fidelity, Architecture & Platform Agnostic, Best Practices &
  Quality, Safety & Token Discipline) are preserved verbatim and are
  upheld by the v2 rewrite.
- Updated sections (descriptive/factual only, to reflect the locked v2
  .NET 10 rewrite — feature 020-v2-net10-rewrite; see planning/26):
  - Technology Constraints → Runtime requirements: the dotnet-ai-kit
    CLI itself is now built on **.NET 10** (v2 full rewrite, replacing
    the v1 Python CLI). Target-project .NET 8/9/10 support is unchanged.
  - Token discipline: skill body cap aligned to the Agent Skills open
    standard (≤500 lines); rule total updated to 21 (5 universal +
    16 path-scoped) per the v2 artifact catalog (planning/23).
  - Knowledge base composition: counts updated to v2 (21 rules,
    15 agents, ~160 skills, 32 commands, 12 profiles).
  - Development Workflow: lifecycle extended with the v2 commands
    (constitution, checklist, fix, orchestrate, release); command total 32.
- Removed sections: NONE
- Templates requiring updates: none (principles unchanged)
- Follow-up TODOs: none
- Driver: feature 020-v2-net10-rewrite (planning/26 authoritative; AR-9
  fixes command count to 32; AR-1 license-light defaults)
- Amendment reason: the maintainer locked a full .NET 10 rewrite. The
  governing PRINCIPLES are unchanged and fully honored by v2; only the
  descriptive technology/corpus/workflow facts are updated so the
  governance document matches the implemented system. MINOR bump
  (material expansion of descriptive sections, no principle change).
-->

# dotnet-ai-kit Constitution

## Core Principles

### I. Detect-First, Respect-Existing (NON-NEGOTIABLE)

Before generating ANY code, the tool MUST scan the target project for:
- .NET version (`<TargetFramework>` in .csproj)
- Architecture pattern (folder structure, layer names)
- Naming conventions (existing classes, namespaces)
- NuGet packages (what is already used)
- Existing patterns (DI registration, error handling, logging)

Non-negotiable rules:
- NEVER change the project's .NET version
- NEVER refactor existing code while adding features
- NEVER introduce competing libraries alongside existing ones
- NEVER reorganize folder structure
- NEVER switch architectural patterns (e.g., add Dapper if
  the project uses EF Core)
- Extend, do not refactor: add new files following existing
  patterns, register services the same way, match base classes

Rationale: AI-generated changes that clash with existing
conventions create friction, break team trust, and increase
review burden. Respecting what exists is the foundation of
adoption.

### II. Pattern Fidelity

Generated code MUST be indistinguishable from hand-written
code in the target project.

- Match the team's naming conventions, code style, DI
  registration patterns, and architectural boundaries
- Use version-appropriate C# features: only features
  available for the detected .NET version (e.g., primary
  constructors for .NET 8+, collection expressions for
  .NET 8+)
- NEVER force-upgrade syntax or .NET version unless the
  user explicitly requests it
- New projects default to latest stable .NET; existing
  projects keep their version

Rationale: Code that looks foreign in a codebase is code
that gets rejected in review. Pattern fidelity is what makes
AI-assisted development sustainable.

### III. Architecture & Platform Agnostic

The tool MUST support any .NET project without assumption:

- **Architectures**: Vertical Slice, Clean Architecture, DDD,
  Modular Monolith, CQRS + Event Sourcing Microservices
- **AI tools**: Claude Code (v2.1.85+ recommended for full
  hook fidelity; v1.0 supported with reduced fidelity), with
  Cursor, Copilot, Codex, and Antigravity planned. Core
  knowledge is portable
- **Platforms**: Windows, macOS, Linux — no OS-specific shell
  commands, file path assumptions, or line ending issues
- **Company**: No hardcoded company names. All references
  resolved from configuration at runtime

Rationale: A tool that only works with one architecture or
one platform is not a tool — it is a constraint. Broad
compatibility maximizes adoption and utility.

### IV. Best Practices & Quality

All generated code MUST follow industry best practices:

- **TDD**: Red-Green-Refactor cycle. Tests written and
  failing before implementation begins
- **SOLID**: Single Responsibility, Open/Closed, Liskov
  Substitution, Interface Segregation, Dependency Inversion
- **Documentation-first**: ALWAYS check official package and
  framework documentation before using any API — never guess
- **Error handling**: Structured error handling appropriate to
  the project mode (ProblemDetails, Result<T>, gRPC status)
- **Localization**: Resource files for all user-facing strings
  when the project uses localization
- **Logging**: Structured logging with appropriate context
- **Security**: Parameterized queries, no string concatenation
  for SQL, no `async void`, no swallowed exceptions

Rationale: AI tools that generate sloppy code teach bad
habits. Quality is non-negotiable because it compounds —
good patterns today prevent bugs tomorrow.

### V. Safety & Token Discipline

The tool MUST prioritize safety and context efficiency:

**Safety**:
- AI MUST NEVER deploy to any environment. Deployments are
  handled by CI/CD pipelines (K8s manifests, GitHub Actions)
- Every command MUST support `--dry-run` for preview
- Every action MUST be reversible via `/dotnet-ai.undo`
- Client-provided IDs for idempotency — never generate
  idempotency keys server-side

**Token discipline**:
- Skills: maximum 500 lines per file (Agent Skills open-standard body cap)
- Commands: maximum 200 lines per file
- Rules: maximum 100 lines per file. 21 rules total —
  5 universal (always loaded; combined ≤300 lines) and
  16 path-scoped (loaded only when a matching file is
  touched). Universal whitelist: `async-concurrency`,
  `coding-style`, `existing-projects`, `security`,
  `tool-calls`.
- Agents: maximum 120 lines per file
- Profiles: maximum 100 lines per file
- Skills loaded on-demand by commands, not upfront
- Minimize context window usage while maximizing relevant
  knowledge

Rationale: An AI tool that can deploy is a liability. An AI
tool that overloads context produces worse results. Safety
and efficiency are two sides of the same coin.

## Technology Constraints

**Runtime requirements**:
- .NET 10 SDK (the dotnet-ai-kit CLI itself — v2 full rewrite; the v1
  Python CLI is kept as the runnable reference spec until the .NET CLI
  passes the contract suite, then removed)
- .NET SDK 8.0+ (target projects)
- Git (version control and multi-repo orchestration)

**Supported .NET versions**: 8.0, 9.0, 10.0 (latest stable).
The tool detects from `<TargetFramework>` and respects what
exists. New projects default to latest stable.

**Multi-repo orchestration**: Features MAY span 3-6
repositories (Command, Query, Processor, Gateway, Control
Panel). The tool MUST handle cross-repo branch creation,
implementation, and linked PR creation.

**File formats**:
- `.gitattributes` with `* text=auto` in all templates
- Forward slashes in config; OS-native at runtime via
  Python `pathlib.Path`
- YAML for configuration (`.dotnet-ai-kit/config.yml`)

**Knowledge base composition** (v2 targets; authored once in
`artifacts/`, projected per host):
- 21 rules total: 5 universal (always loaded) + 16 path-scoped
  (loaded only when a matching file is touched)
- 15 specialist agents (reference skills; routing intents in metadata)
- ~160 skills (loaded on demand, Agent Skills spec compliant)
- 32 commands (authored as command-skills, user-invoked / off-budget)
- 12 architecture profiles (hard constraints, path-scoped)
- knowledge documents + reusable fragments (reference material)

## Development Workflow

**Specification-Driven Development (SDD) lifecycle** (v2 — 32 commands):

```
constitution → specify → clarify → checklist → plan → tasks(→issues) →
analyze → orchestrate → implement → review → verify → fix → pr → release
```

with `status`/`undo`/`checkpoint`/`wrap-up` available at any point, `do`
chaining the core path, and the code-generation commands below.

**Quick mode** (`/dotnet-ai.do`): Chains the full lifecycle
automatically. Pauses only for complex features (multi-repo
or >10 tasks) or ambiguity (max 3 clarifying questions).

**Full lifecycle mode**: Each step is an independent command
for manual control. Features tracked in
`.dotnet-ai-kit/features/`.

**Code generation commands**: `add-aggregate`, `add-entity`,
`add-event`, `add-endpoint`, `add-page`, `add-crud`,
`add-tests` — each generates complete, pattern-compliant
code for the detected architecture.

**Review process**:
- Generated code MUST pass the project's existing linting
  and formatting rules
- Optional CodeRabbit CLI integration for automated review
- All PRs include clear description of changes and testing
  instructions

**Checkpoint discipline**: After each user story
implementation, STOP and validate independently before
proceeding to the next story.

## Governance

This constitution is the supreme governance document for the
dotnet-ai-kit project. All rules, skills, commands, agents,
and generated code MUST comply with the principles defined
here.

**Amendment procedure**:
1. Propose amendment with rationale and impact assessment
2. Document the change in this file with version increment
3. Propagate changes to all dependent templates and docs
4. Record the change in the Sync Impact Report (HTML comment
   at top of this file)

**Versioning policy**: MAJOR.MINOR.PATCH (semantic versioning)
- MAJOR: Backward-incompatible principle removal or
  redefinition
- MINOR: New principle or section added, material expansion
- PATCH: Clarifications, wording, typo fixes

**Compliance review**: All PRs and code reviews MUST verify
compliance with this constitution. Complexity that violates
a principle MUST be explicitly justified in the plan's
Complexity Tracking table.

**Version**: 1.1.0 | **Ratified**: 2026-03-15 | **Last Amended**: 2026-05-31
