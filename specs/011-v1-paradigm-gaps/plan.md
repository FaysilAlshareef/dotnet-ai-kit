# Implementation Plan: v1 Paradigm & Best Practice Gaps

**Branch**: `011-v1-paradigm-gaps` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-v1-paradigm-gaps/spec.md`

## Summary

Add 10 new skills to close the v1 paradigm and best-practice gaps: 3 paradigm skills (SOLID principles, design patterns catalog, functional C#), 2 practical skills (FluentValidation standalone, mapping strategies), 3 API infrastructure skills (caching, rate limiting, SignalR), and 2 security skills (CORS, input sanitization). Update planning docs, plugin manifests, and version roadmap. Total skills: 106 -> 116.

## Technical Context

**Language/Version**: Markdown (SKILL.md files), YAML frontmatter, JSON (plugin manifests)
**Primary Dependencies**: None — all files are Markdown content (no Python code changes)
**Storage**: Skills as `skills/{category}/{name}/SKILL.md`
**Testing**: Manual verification — skill files are Markdown loaded by AI tools
**Target Platform**: Cross-platform (Markdown is universal)
**Constraints**: Skills <= 400 lines, correct YAML frontmatter format
**Scale/Scope**: 10 new SKILL.md files + 5 planning/manifest updates

## Constitution Check

*GATE: Must pass before proceeding.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Detect-First, Respect-Existing | PASS | No code generation — only knowledge/skill files |
| II. Pattern Fidelity | PASS | All patterns use modern C# 12/13+ idioms |
| III. Architecture & Platform Agnostic | PASS | Skills apply to all supported architectures |
| IV. Best Practices & Quality | PASS | Each skill includes "When to Use" and "When NOT to Use" |
| V. Safety & Token Discipline | PASS | All skills <= 400 lines per budget |

**Result**: PASS — No violations.

## Project Structure

### Files CREATED (10 new skills)

```text
skills/core/solid-principles/SKILL.md           # FR-001: SOLID + anti-patterns
skills/core/design-patterns/SKILL.md             # FR-002: Modern C# pattern catalog
skills/core/functional-csharp/SKILL.md           # FR-003: FP in C#, Result<T>, OOP vs FP
skills/core/fluent-validation/SKILL.md           # FR-004: Standalone FluentValidation
skills/core/mapping-strategies/SKILL.md          # FR-005: Manual-first mapping
skills/api/caching-strategies/SKILL.md           # FR-006: Output cache, IDistributedCache, ETag
skills/api/rate-limiting/SKILL.md                # FR-007: .NET 7+ AddRateLimiter()
skills/api/signalr-realtime/SKILL.md             # FR-008: Hub patterns + client
skills/security/cors-configuration/SKILL.md      # FR-009: AddCors() policies
skills/security/input-sanitization/SKILL.md      # FR-010: XSS, CSP headers
```

### Files MODIFIED (12 updates)

```text
planning/12-version-roadmap.md                   # FR-011: v1 late additions + future gaps (PRE-COMPLETED)
planning/11-expanded-skills-inventory.md         # FR-012: Add 10 skills to inventory
.claude-plugin/plugin.json                       # FR-013: 106 -> 116 skills
.claude-plugin/marketplace.json                  # FR-014: 106 -> 116 skills
CLAUDE.md                                        # FR-015: Update skill count
README.md                                        # FR-016: 106 -> 116 skills (4 occurrences)
CONTRIBUTING.md                                  # FR-017: 106 -> 116 skills in project tree
.specify/memory/constitution.md                  # FR-018: 106 -> 116 skills + version increment
planning/01-vision.md                            # FR-019: 106 -> 116 skills
planning/02-skills-inventory.md                  # FR-019: 106 -> 116 skills
planning/03-agents-design.md                     # FR-019: 106 -> 116 skills
planning/06-build-roadmap.md                     # FR-019: 106 -> 116 skills
planning/07-project-structure.md                 # FR-019: 106 -> 116 skills
CHANGELOG.md                                     # FR-020: Add v1.0.1 entry
```

## Skill Design Guidelines

Each SKILL.md follows this structure:

```markdown
---
name: dotnet-ai-{skill-name}
description: >
  {One-line description}.
  Trigger: {comma-separated trigger keywords}.
category: {core|api|security}
agent: {primary-agent}
---

# {Skill Title}

## Core Principles
- {3-6 bullet points}

## When to Use
- {Specific scenarios where this applies}

## When NOT to Use
- {Anti-patterns, over-engineering signals}

## Patterns
### {Pattern Name}
{Code example with explanation}

## Decision Guide
| Scenario | Recommendation |
|----------|---------------|
| ... | ... |

## Anti-Patterns
| Problem | Why It Hurts | Correct Approach |
|---------|-------------|-----------------|
| ... | ... | ... |
```

## Agent Mappings for New Skills

| Skill | Category | Primary Agent |
|-------|----------|---------------|
| `solid-principles` | core | dotnet-architect |
| `design-patterns` | core | dotnet-architect |
| `functional-csharp` | core | dotnet-architect |
| `fluent-validation` | core | dotnet-architect |
| `mapping-strategies` | core | dotnet-architect |
| `caching-strategies` | api | api-designer |
| `rate-limiting` | api | api-designer |
| `signalr-realtime` | api | api-designer |
| `cors-configuration` | security | api-designer |
| `input-sanitization` | security | api-designer |

## Phase Breakdown

### Phase 1: Paradigm Skills (FR-001, FR-002, FR-003)

**Purpose**: Create the 3 foundational paradigm skills that teach *how to think about code design*.

**Files**: `skills/core/solid-principles/`, `skills/core/design-patterns/`, `skills/core/functional-csharp/`

**Content requirements per skill**:

#### solid-principles (FR-001)
- SRP: One reason to change, handler-per-request example
- OCP: Extension via strategy/decorator, not modification
- LSP: Substitutability, interface contracts
- ISP: Focused interfaces, not fat interfaces
- DIP: Depend on abstractions, DI container
- Anti-patterns section: interface explosion, class proliferation, premature abstraction
- Decision table: "Apply when X hurts, skip when Y is simpler"

#### design-patterns (FR-002)
- Creational: Factory (DI replaces most), Builder (init props replace simple cases), Singleton (DI container)
- Structural: Adapter, Decorator (pipeline behaviors), Facade, Proxy (lazy/cache)
- Behavioral: Strategy (delegates/DI), Observer (C# events/MediatR), Command (MediatR), Mediator, Chain of Responsibility (pipeline), State
- "Patterns Replaced by Language Features" section
- Decision tree: "What problem are you solving?" -> pattern recommendation

#### functional-csharp (FR-003)
- Result<T> with Success/Failure pattern
- Railway-oriented programming (Bind, Map, Match)
- Pure functions (no side effects, testable)
- Immutability (records, init, readonly collections)
- Pattern matching (switch expressions, property patterns)
- LINQ as functional composition
- "OOP vs FP Decision Matrix" — when each style wins

### Phase 2: Practical Skills (FR-004, FR-005)

**Purpose**: FluentValidation standalone and mapping strategies.

#### fluent-validation (FR-004)
- `AbstractValidator<T>` with rules
- DI registration (`AddValidatorsFromAssembly`)
- Manual validation (`IValidator<T>.ValidateAndThrowAsync`)
- Auto-validation middleware
- Custom validators, async validators
- Validation in Minimal API endpoints
- Validation in controllers

#### mapping-strategies (FR-005)
- Manual mapping: extension methods, Select projections (RECOMMENDED)
- When manual is best (small-medium projects, explicit control)
- AutoMapper: profile setup, when it helps (large DTOs, many similar maps)
- Mapster: code-gen approach, configuration
- Decision guide: manual-first, tools only for justified cases
- Anti-patterns: hidden mapping bugs, runtime exceptions

### Phase 3: API Infrastructure Skills (FR-006, FR-007, FR-008)

**Purpose**: Caching, rate limiting, real-time — production API essentials.

#### caching-strategies (FR-006)
- Output caching: `AddOutputCache()`, `[OutputCache]`, cache profiles
- Response caching: `AddResponseCaching()`, cache-control headers
- IDistributedCache: Redis, SQL Server, in-memory
- HybridCache (.NET 9+): L1/L2 pattern
- ETag + conditional requests (If-None-Match, 304)
- Cache invalidation patterns
- Decision guide: which caching for which scenario

#### rate-limiting (FR-007)
- `AddRateLimiter()` setup
- Fixed window: `AddFixedWindowLimiter()`
- Sliding window: `AddSlidingWindowLimiter()`
- Token bucket: `AddTokenBucketLimiter()`
- Concurrency: `AddConcurrencyLimiter()`
- Per-endpoint: `RequireRateLimiting("policy")`
- Custom partitioners (by user, by IP, by API key)
- Response customization (429 + Retry-After header)

#### signalr-realtime (FR-008)
- Hub design: `Hub<IClient>` typed clients
- Group management: AddToGroupAsync, SendToGroup
- Authentication: `[Authorize]` on hubs
- Connection lifecycle: OnConnectedAsync, OnDisconnectedAsync
- Client integration (JavaScript + .NET)
- Redis backplane: `AddStackExchangeRedis()`
- Scaling considerations

### Phase 4: Security Skills (FR-009, FR-010)

**Purpose**: CORS and input sanitization for secure APIs.

#### cors-configuration (FR-009)
- `AddCors()` + `UseCors()`
- Named policies: `AddPolicy("AllowSPA", ...)`
- Origin, method, header configuration
- Credentials: `AllowCredentials()` vs `AllowAnyOrigin()`
- Per-endpoint CORS: `RequireCors("policy")`
- Preflight caching: `SetPreflightMaxAge()`
- Common mistakes (wildcard + credentials)

#### input-sanitization (FR-010)
- HTML sanitization: HtmlSanitizer NuGet package
- CSP headers: `Content-Security-Policy` middleware
- Anti-XSS: output encoding, `HtmlEncoder`
- Input validation vs sanitization distinction
- File upload validation (MIME, extension, size)
- SQL injection prevention (parameterized queries — reference only)
- Security headers middleware (X-Content-Type-Options, X-Frame-Options)

### Phase 5: Planning & Documentation Updates (FR-011 through FR-015)

**Purpose**: Update all planning docs and manifests to reflect new skill count.

- Update `planning/12-version-roadmap.md`:
  - Add "v1.0 Late Additions" section with 10 paradigm/practical skills
  - Move remaining audit gaps to future versions:
    - v1.1: Architecture Testing (ArchUnitNET), Correlation IDs, Feature Flags, GraphQL (HotChocolate)
    - v1.2: Soft Deletes, Multi-tenancy (already there for Saga/Dapr)
    - v1.3: Property-based Testing (FsCheck), Span<T>/Memory<T>
    - v2.0: Source Generators, Reactive (Rx.NET)
- Update `planning/11-expanded-skills-inventory.md`:
  - Add 10 new skills to appropriate categories with agent mappings
  - Update total from 106 to 116
- Update `.claude-plugin/plugin.json`: description "106 skills" -> "116 skills"
- Update `.claude-plugin/marketplace.json`: description "106 skills" -> "116 skills"
- Update `CLAUDE.md`: any skill count references
- Update `README.md`: 4 occurrences of "106 skills" → "116 skills" (banner subtitle, badge bar, plugin install note, project tree)
- Update `CONTRIBUTING.md`: "106 skills" → "116 skills" in project tree
- Update `.specify/memory/constitution.md`: "106 skills" → "116 skills" in Technology Constraints. Increment version 1.0.3 → 1.0.4, update Sync Impact Report header
- Update remaining planning docs (`01-vision.md`, `02-skills-inventory.md`, `03-agents-design.md`, `06-build-roadmap.md`, `07-project-structure.md`): "106 skills" → "116 skills"
- Update `CHANGELOG.md`: Add 10 new paradigm/best-practice skills to existing v1.0.0 "### Added" section. Update "106 skills" → "116 skills" in existing v1.0.0 text
- NOTE: `planning/12-version-roadmap.md` (FR-011) was PRE-COMPLETED earlier in this session — no task needed

## Future Version Items (NOT in this feature)

These gaps were identified in the audit but deferred to future versions:

| Gap | Target Version | Reason for Deferral |
|-----|---------------|-------------------|
| Architecture Testing (ArchUnitNET) | v1.1 | Specialized, not blocking |
| Correlation ID Propagation | v1.1 | Enhancement to existing observability |
| Feature Flags (Microsoft.FeatureManagement) | v1.1 | Mentioned in agents, needs dedicated skill |
| GraphQL (HotChocolate) | v1.1 (promoted from v2.0) | Growing adoption, worth earlier delivery |
| Soft Deletes (EF Core) | v1.2 | Common but not critical for v1 |
| Multi-tenancy | v1.2 | Specialized architecture |
| Builder Pattern | N/A | Covered inside design-patterns skill |
| Saga Pattern | v1.2 | Already planned |
| Property-based Testing (FsCheck) | v1.3 | Advanced testing |
| Span<T> / Memory<T> | v1.3 | Performance optimization |
| Source Generators | v2.0 | Niche |
| Reactive (Rx.NET) | v2.0 | Niche in web dev |

## Verification

After implementation:

1. Count skill files: `find skills/ -name "SKILL.md" | wc -l` should be 116
2. Verify each new skill has correct YAML frontmatter
3. Verify each paradigm skill has "When to Use" and "When NOT to Use" sections
4. Verify design-patterns has "Patterns Replaced by Language Features"
5. Verify functional-csharp has "OOP vs FP Decision Matrix"
6. Verify mapping-strategies defaults to manual mapping
7. Verify all files are under 400 lines: `wc -l skills/core/*/SKILL.md skills/api/*/SKILL.md skills/security/*/SKILL.md`
8. Verify plugin.json and marketplace.json say "116 skills"
