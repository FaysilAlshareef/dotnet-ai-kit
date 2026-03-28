# Feature Specification: v1 Paradigm & Best Practice Gaps

**Feature Branch**: `011-v1-paradigm-gaps`
**Created**: 2026-03-28
**Status**: Draft
**Input**: Audit report identifying missing paradigm guidance (SOLID, Design Patterns, FP, OOP vs FP) and 7 missing practical skills (caching, rate limiting, CORS, SignalR, mapping, input sanitization, FluentValidation)

## Clarifications

### Session 2026-03-28

- Q: Mapping preference? -> A: User always prefers manual mapping. Skill should recommend manual-first, show AutoMapper/Mapster only as comparison.
- Q: SignalR was planned for v1.2 in roadmap — promote to v1? -> A: Yes, promote to v1 as a skill (hub patterns + client integration).
- Q: Builder Pattern — separate skill or fold into design-patterns? -> A: Fold into design-patterns skill (not a separate skill, covered as one pattern in the catalog).
- Q: Architecture Testing — v1 or v1.1? -> A: v1.1 (not blocking for release).
- Q: SOLID Anti-patterns — separate skill? -> A: No, fold into solid-principles skill as a dedicated section.
- Q: Modern Pattern Replacements — separate skill? -> A: No, fold into design-patterns skill as "Patterns Replaced by Language Features" section.
- Q: OOP vs FP Decision Guide — separate skill? -> A: No, fold into functional-csharp skill as decision matrix.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Paradigm Decision Guidance (Priority: P1)

A developer asks the AI "should I use inheritance or composition here?" or "when should I use the Strategy pattern?" The AI loads the SOLID principles, design patterns, and functional programming skills and provides contextual guidance with concrete C# examples, trade-offs, and anti-patterns — not just theoretical definitions.

**Why this priority**: These are foundational skills that inform every code decision. Without them, the tool teaches *what to build* but not *how to think about code design*.

**Acceptance Scenarios**:

1. **Given** the solid-principles skill is loaded, **When** the AI generates code with an interface, **Then** it can explain which SOLID principle applies and when the interface is over-engineering.
2. **Given** the design-patterns skill is loaded, **When** asked "which pattern should I use for X?", **Then** the AI provides a decision guide matching the problem to the right pattern, noting when modern C# features replace the pattern.
3. **Given** the functional-csharp skill is loaded, **When** deciding between class-based error handling and Result<T>, **Then** the AI explains when FP style is appropriate vs OOP, with a clear decision matrix.

---

### User Story 2 — API Infrastructure Skills (Priority: P1)

A developer building a .NET API needs caching, rate limiting, and real-time features. The AI loads the relevant skills and generates correct, production-ready configuration code using .NET 7+ built-in APIs.

**Why this priority**: Every production API needs these. Without them, users must write boilerplate from memory or Stack Overflow.

**Acceptance Scenarios**:

1. **Given** the caching-strategies skill, **When** asked to add caching, **Then** it generates output caching middleware + IDistributedCache + ETag patterns with correct .NET 7+ APIs.
2. **Given** the rate-limiting skill, **When** asked to protect an endpoint, **Then** it generates `AddRateLimiter()` with fixed window, sliding window, token bucket, or concurrency policies.
3. **Given** the signalr-realtime skill, **When** asked to add notifications, **Then** it generates a SignalR hub with typed clients, group management, and Redis backplane scaling.

---

### User Story 3 — Security & Validation Skills (Priority: P1)

A developer needs CORS for their SPA, input sanitization for user content, and validation for DTOs. The AI loads the appropriate skills and generates secure, correct code.

**Acceptance Scenarios**:

1. **Given** the cors-configuration skill, **When** configuring CORS for a React SPA, **Then** it generates named policies with specific origins, methods, headers, and credentials handling.
2. **Given** the input-sanitization skill, **When** accepting user HTML content, **Then** it generates HtmlSanitizer usage + CSP headers + anti-XSS middleware.
3. **Given** the fluent-validation skill, **When** validating a DTO outside CQRS, **Then** it generates standalone `AbstractValidator<T>` with DI registration and manual/auto validation.

---

### User Story 4 — Mapping Strategies (Priority: P2)

A developer needs to map between domain entities and DTOs. The AI recommends manual mapping first (user preference), shows the pattern, and explains when AutoMapper/Mapster might be justified.

**Acceptance Scenarios**:

1. **Given** the mapping-strategies skill, **When** generating mapping code, **Then** manual `Select()` projections and extension methods are used by default.
2. **Given** a question about AutoMapper, **Then** the skill explains trade-offs (runtime errors, hidden complexity) and recommends manual mapping for most cases.

---

## Requirements

### Paradigm Skills (3 new SKILL.md files)

- **FR-001**: Create `skills/core/solid-principles/SKILL.md` — All 5 SOLID principles with C# examples, "When to Apply" guidance, "When Over-Applying Hurts" anti-patterns (interface explosion, class proliferation), and a decision table. Max 400 lines.
- **FR-002**: Create `skills/core/design-patterns/SKILL.md` — Modern C# pattern catalog covering Creational (Factory, Builder, Singleton), Structural (Adapter, Decorator, Facade, Proxy), Behavioral (Strategy, Observer, Command, Mediator, Chain of Responsibility, State). Each with: when to use, when NOT to use, modern C# replacement if applicable. Include "Patterns Replaced by Language Features" section. Max 400 lines.
- **FR-003**: Create `skills/core/functional-csharp/SKILL.md` — Result<T>/Option types, railway-oriented programming, pure functions, immutability patterns (records, init, readonly), pattern matching, LINQ as functional composition. Include "OOP vs FP Decision Matrix" section. Max 400 lines.

### Practical Skills (2 new SKILL.md files)

- **FR-004**: Create `skills/core/fluent-validation/SKILL.md` — Standalone FluentValidation patterns: `AbstractValidator<T>`, DI registration (`AddValidatorsFromAssembly`), manual validation (`IValidator<T>.ValidateAndThrowAsync`), auto-validation middleware, custom validators, async validators. Max 400 lines.
- **FR-005**: Create `skills/core/mapping-strategies/SKILL.md` — Manual mapping recommended (extension methods, Select projections), AutoMapper/Mapster comparison for context, decision guide. Preference: manual-first. Max 400 lines.

### API Infrastructure Skills (3 new SKILL.md files)

- **FR-006**: Create `skills/api/caching-strategies/SKILL.md` — Output caching (`AddOutputCache`), response caching, IDistributedCache (Redis, SQL), HybridCache, ETag/conditional requests, cache-control headers, cache invalidation patterns. Max 400 lines.
- **FR-007**: Create `skills/api/rate-limiting/SKILL.md` — .NET 7+ `AddRateLimiter()` with fixed window, sliding window, token bucket, concurrency limiter. Per-endpoint policies, global policies, custom partitioners. Max 400 lines.
- **FR-008**: Create `skills/api/signalr-realtime/SKILL.md` — Hub design, typed hub clients, group management, authentication, Redis backplane scaling, client integration (JS/.NET), connection management. Max 400 lines.

### Security Skills (2 new SKILL.md files)

- **FR-009**: Create `skills/security/cors-configuration/SKILL.md` — `AddCors()` with named policies, `WithOrigins/Methods/Headers`, credentials handling, preflight, per-endpoint CORS. Max 400 lines.
- **FR-010**: Create `skills/security/input-sanitization/SKILL.md` — HTML sanitization (HtmlSanitizer), CSP headers, anti-XSS patterns, input encoding, Content-Security-Policy middleware. Max 400 lines.

### Planning & Documentation Updates

- **FR-011**: Update `planning/12-version-roadmap.md` — add v1 paradigm skills to v1.0 Late Additions, move remaining gaps to correct future versions.
- **FR-012**: Update `planning/11-expanded-skills-inventory.md` — add 10 new skills to inventory with correct categories and agent mappings.
- **FR-013**: Update `.claude-plugin/plugin.json` — update description count from 106 to 116 skills.
- **FR-014**: Update `.claude-plugin/marketplace.json` — update description count from 106 to 116 skills.
- **FR-015**: Update `CLAUDE.md` — update skill count reference.
- **FR-016**: Update `README.md` — replace all "106 skills" with "116 skills" (4 occurrences: banner subtitle, badge bar, plugin install note, skills section header, project tree).
- **FR-017**: Update `CONTRIBUTING.md` — replace "106 skills" with "116 skills" in project tree.
- **FR-018**: Update `.specify/memory/constitution.md` — change "106 skills" to "116 skills" in Technology Constraints (line 150). Increment patch version per amendment procedure.
- **FR-019**: Update remaining planning docs — replace "106 skills" with "116 skills" in `planning/01-vision.md`, `planning/02-skills-inventory.md`, `planning/03-agents-design.md`, `planning/06-build-roadmap.md`, `planning/07-project-structure.md`.
- **FR-020**: Update `CHANGELOG.md` — add 10 new paradigm/best-practice skills to the existing v1.0.0 entry under "### Added" section. Update skill count references from 106 to 116.

## Success Criteria

- SC-001: All 10 new SKILL.md files exist and are under 400 lines each
- SC-002: Each paradigm skill includes "When to Use" AND "When NOT to Use" sections
- SC-003: design-patterns skill includes "Patterns Replaced by Language Features" section
- SC-004: functional-csharp skill includes "OOP vs FP Decision Matrix"
- SC-005: mapping-strategies skill defaults to manual mapping
- SC-006: All skills have correct YAML frontmatter (name, description, category, agent)
- SC-007: Total skill count is 116 after implementation
- SC-008: Planning docs and plugin manifests reflect updated counts
- SC-009: README.md reflects "116 skills" in all 4 occurrences
- SC-010: Constitution reflects "116 skills" with version increment
- SC-011: CHANGELOG.md v1.0.0 entry includes 10 new paradigm/best-practice skills
- SC-012: Zero occurrences of "106 skills" remain in active docs (excluding historical specs/)
