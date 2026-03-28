<!--
Sync Impact Report
===================
- Version change: 1.0.5 → 1.0.6
- Modified principles: N/A
- Updated sections:
  - Technology Constraints: skills 106 → 120
- Removed sections: N/A
- Templates requiring updates: none
- Follow-up TODOs: none
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
- **AI tools**: Claude Code (v1.0), with Cursor, Copilot,
  Codex, and Antigravity planned. Core knowledge is portable
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
- Skills: maximum 400 lines per file
- Commands: maximum 200 lines per file
- Rules: maximum 100 lines per file (9 rules, ~600 lines
  total budget)
- Skills loaded on-demand by commands, not upfront
- Minimize context window usage while maximizing relevant
  knowledge

Rationale: An AI tool that can deploy is a liability. An AI
tool that overloads context produces worse results. Safety
and efficiency are two sides of the same coin.

## Technology Constraints

**Runtime requirements**:
- Python 3.10+ (CLI tool)
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

**Knowledge base composition**:
- 9 rules (always loaded)
- 13 specialist agents (routing logic in commands)
- 120 skills (loaded on demand, Agent Skills spec compliant)
- 27 commands (slash commands)
- 16 knowledge documents (reference material)
- 13 templates (project scaffolds)

## Development Workflow

**Specification-Driven Development (SDD) lifecycle**:

```
specify → clarify → plan → tasks → analyze →
implement → review → verify → pr → wrap-up
```

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

**Version**: 1.0.6 | **Ratified**: 2026-03-15 | **Last Amended**: 2026-03-28
