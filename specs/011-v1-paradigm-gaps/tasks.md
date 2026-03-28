# Tasks: v1 Paradigm & Best Practice Gaps

**Input**: Design documents from `/specs/011-v1-paradigm-gaps/`
**Prerequisites**: plan.md (required), spec.md (required)

**Tests**: Not requested — all deliverables are Markdown SKILL.md files verified by line count and section presence.

**Organization**: Tasks grouped by user story. US1 = Paradigm Decision Guidance (P1), US2 = API Infrastructure Skills (P1), US3 = Security & Validation Skills (P1), US4 = Mapping Strategies (P2).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Create skill directories for all 10 new skills.

- [x] T001 [P] Create directory `skills/core/solid-principles/`
- [x] T002 [P] Create directory `skills/core/design-patterns/`
- [x] T003 [P] Create directory `skills/core/functional-csharp/`
- [x] T004 [P] Create directory `skills/core/fluent-validation/`
- [x] T005 [P] Create directory `skills/core/mapping-strategies/`
- [x] T006 [P] Create directory `skills/api/caching-strategies/`
- [x] T007 [P] Create directory `skills/api/rate-limiting/`
- [x] T008 [P] Create directory `skills/api/signalr-realtime/`
- [x] T009 [P] Create directory `skills/security/cors-configuration/`
- [x] T010 [P] Create directory `skills/security/input-sanitization/`

**Checkpoint**: All 10 skill directories exist. No content yet.

---

## Phase 2: User Story 1 — Paradigm Decision Guidance (Priority: P1)

**Goal**: Developers get foundational guidance on SOLID principles, design patterns, and functional programming with "when to use" and "when NOT to use" decision guides.

**Independent Test**: Load each skill and verify it has: YAML frontmatter, "When to Use" section, "When NOT to Use" section, code examples, decision guide table, anti-patterns table. Verify each is under 400 lines.

### Implementation for User Story 1

- [x] T011 [P] [US1] Create `skills/core/solid-principles/SKILL.md` (FR-001) — YAML frontmatter with name: `dotnet-ai-solid-principles`, category: `core`, agent: `dotnet-architect`. Content must include: (a) Core Principles section with 1 paragraph per SOLID letter, (b) "When to Use" section with scenarios for each principle, (c) Patterns section with C# code examples for SRP (one handler per request), OCP (strategy/decorator extension), LSP (interface contract substitution), ISP (focused interfaces like IOrderReader vs IOrderWriter), DIP (constructor injection), (d) "When Over-Applying Hurts" section covering interface explosion (one interface per class), class proliferation (too many small files), premature abstraction (extracting before duplication), (e) Decision Guide table: Scenario | Principle | Apply? | Why, (f) Anti-Patterns table: Problem | Why It Hurts | Correct Approach. Max 400 lines.

- [x] T012 [P] [US1] Create `skills/core/design-patterns/SKILL.md` (FR-002) — YAML frontmatter with name: `dotnet-ai-design-patterns`, category: `core`, agent: `dotnet-architect`. Content must include: (a) Core Principles (patterns solve recurring problems, don't force patterns), (b) "When to Use" section, (c) "When NOT to Use" section (YAGNI, language features suffice), (d) Creational Patterns section: Factory Method (with DI alternative), Builder (with C# init properties alternative), Singleton (with DI container alternative), (e) Structural Patterns section: Adapter, Decorator (pipeline behaviors example), Facade, Proxy (lazy loading, caching), (f) Behavioral Patterns section: Strategy (with delegates alternative), Observer (with C# events/MediatR alternative), Command (MediatR IRequest), Mediator, Chain of Responsibility (middleware pipeline), State, (g) "Patterns Replaced by Language Features" section — table: Pattern | Modern C# Replacement | Example, (h) Decision Guide: "What problem?" -> recommended pattern, (i) Anti-Patterns table. Each pattern entry: 2-3 line description + when to use + when NOT to use. Max 400 lines.

- [x] T013 [P] [US1] Create `skills/core/functional-csharp/SKILL.md` (FR-003) — YAML frontmatter with name: `dotnet-ai-functional-csharp`, category: `core`, agent: `dotnet-architect`. Content must include: (a) Core Principles (immutability, pure functions, composition over inheritance), (b) "When to Use" section (data transformations, error handling, validation pipelines), (c) "When NOT to Use" section (stateful UI, complex mutation workflows, team unfamiliar with FP), (d) Result<T> pattern: Success/Failure with Match method, code example, (e) Railway-Oriented Programming: Bind, Map, Then chaining, error short-circuit, (f) Pure Functions: no side effects, deterministic, testable — code example, (g) Immutability: records, init properties, readonly collections, ImmutableList, (h) Pattern Matching: switch expressions, property patterns, relational patterns, list patterns, (i) LINQ as Functional Composition: Select/Where/Aggregate pipeline, (j) "OOP vs FP Decision Matrix" — table: Scenario | Prefer OOP | Prefer FP | Why, with 8-10 rows covering common situations, (k) Anti-Patterns table. Max 400 lines.

**Checkpoint**: 3 paradigm skills exist. Each has YAML frontmatter, "When to Use", "When NOT to Use", code examples, decision guide, anti-patterns. Each under 400 lines.

---

## Phase 3: User Story 2 — API Infrastructure Skills (Priority: P1)

**Goal**: Developers get production-ready caching, rate limiting, and SignalR patterns using .NET 7+ built-in APIs.

**Independent Test**: Load each skill and verify it generates correct .NET 7+ API configuration code. Verify each is under 400 lines.

### Implementation for User Story 2

- [x] T014 [P] [US2] Create `skills/api/caching-strategies/SKILL.md` (FR-006) — YAML frontmatter with name: `dotnet-ai-caching-strategies`, category: `api`, agent: `api-designer`. Content must include: (a) Core Principles (cache close to consumer, invalidate explicitly, set TTL), (b) "When to Use" / "When NOT to Use" sections, (c) Output Caching: `builder.Services.AddOutputCache()`, `app.UseOutputCache()`, `[OutputCache(Duration = 60)]`, cache profiles, tag-based invalidation, (d) Response Caching: `AddResponseCaching()`, Cache-Control headers, Vary header, (e) Distributed Cache: `IDistributedCache` with Redis (`AddStackExchangeRedisCache`) and SQL Server, GetAsync/SetAsync patterns, (f) HybridCache (.NET 9+): `AddHybridCache()`, L1 in-memory + L2 distributed, stampede protection, (g) ETag / Conditional Requests: If-None-Match header, 304 Not Modified response, ETag generation, (h) Cache Invalidation Patterns: tag-based, event-based, TTL expiry, (i) Decision Guide table: Scenario | Cache Type | Why, (j) Anti-Patterns table. Max 400 lines.

- [x] T015 [P] [US2] Create `skills/api/rate-limiting/SKILL.md` (FR-007) — YAML frontmatter with name: `dotnet-ai-rate-limiting`, category: `api`, agent: `api-designer`. Content must include: (a) Core Principles, (b) "When to Use" / "When NOT to Use", (c) Setup: `builder.Services.AddRateLimiter()`, `app.UseRateLimiter()`, (d) Fixed Window: `AddFixedWindowLimiter("fixed", options => { options.Window = TimeSpan.FromMinutes(1); options.PermitLimit = 100; })`, (e) Sliding Window: `AddSlidingWindowLimiter()` with segments, (f) Token Bucket: `AddTokenBucketLimiter()` with replenishment, (g) Concurrency: `AddConcurrencyLimiter()` with queue, (h) Per-Endpoint: `app.MapGet().RequireRateLimiting("policy")`, (i) Custom Partitioners: by user ID, by IP, by API key using `RateLimitPartition.GetFixedWindowLimiter()`, (j) 429 Response: `OnRejected` callback with Retry-After header, (k) Chained policies, (l) Decision Guide table, (m) Anti-Patterns table. Max 400 lines.

- [x] T016 [P] [US2] Create `skills/api/signalr-realtime/SKILL.md` (FR-008) — YAML frontmatter with name: `dotnet-ai-signalr-realtime`, category: `api`, agent: `api-designer`. Content must include: (a) Core Principles, (b) "When to Use" (notifications, live dashboards, chat) / "When NOT to Use" (request-response, batch processing), (c) Hub Design: `Hub<INotificationClient>` typed clients interface, (d) Group Management: `Groups.AddToGroupAsync`, `Clients.Group("name").Method()`, (e) Authentication: `[Authorize]` on hub, bearer token in query string for WebSocket, (f) Connection Lifecycle: `OnConnectedAsync`, `OnDisconnectedAsync`, connection ID tracking, (g) JavaScript Client: `@microsoft/signalr` package, `HubConnectionBuilder`, auto-reconnect, (h) .NET Client: `Microsoft.AspNetCore.SignalR.Client`, (i) Redis Backplane: `builder.Services.AddSignalR().AddStackExchangeRedis()` for multi-server scaling, (j) Decision Guide table, (k) Anti-Patterns table. Max 400 lines.

**Checkpoint**: 3 API infrastructure skills exist. Each generates correct .NET 7+ code. Each under 400 lines.

---

## Phase 4: User Story 3 — Security & Validation Skills (Priority: P1)

**Goal**: Developers get CORS configuration, input sanitization, and standalone FluentValidation patterns.

**Independent Test**: Load each skill and verify it generates secure, correct configuration code. Verify each is under 400 lines.

### Implementation for User Story 3

- [x] T017 [P] [US3] Create `skills/security/cors-configuration/SKILL.md` (FR-009) — YAML frontmatter with name: `dotnet-ai-cors-configuration`, category: `security`, agent: `api-designer`. Content must include: (a) Core Principles (least privilege, explicit origins, no wildcard with credentials), (b) "When to Use" / "When NOT to Use", (c) Basic Setup: `builder.Services.AddCors()`, `app.UseCors("PolicyName")`, (d) Named Policies: `AddPolicy("AllowSPA", policy => policy.WithOrigins("https://app.example.com").WithMethods("GET","POST").WithHeaders("Content-Type","Authorization"))`, (e) Credentials: `AllowCredentials()` — cannot combine with `AllowAnyOrigin()`, (f) Per-Endpoint: `app.MapGet().RequireCors("policy")`, controller `[EnableCors("policy")]`, (g) Preflight: `SetPreflightMaxAge(TimeSpan.FromHours(1))`, (h) Development vs Production: different policies per environment, (i) Common Mistakes table: Mistake | Problem | Fix, (j) Decision Guide, (k) Anti-Patterns table. Max 400 lines.

- [x] T018 [P] [US3] Create `skills/security/input-sanitization/SKILL.md` (FR-010) — YAML frontmatter with name: `dotnet-ai-input-sanitization`, category: `security`, agent: `api-designer`. Content must include: (a) Core Principles (never trust input, encode output, defense in depth), (b) "When to Use" / "When NOT to Use", (c) HTML Sanitization: HtmlSanitizer NuGet, `var sanitizer = new HtmlSanitizer(); var clean = sanitizer.Sanitize(userInput);`, allowed tags/attributes, (d) Output Encoding: `HtmlEncoder.Default.Encode()`, Razor auto-encoding, `@Html.Raw()` dangers, (e) CSP Headers: `Content-Security-Policy: default-src 'self'; script-src 'self'`, middleware setup, nonce-based CSP, (f) Security Headers: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, (g) File Upload Validation: MIME type check, extension whitelist, size limits, magic bytes, (h) Input Validation vs Sanitization: when to reject vs clean, (i) Decision Guide, (j) Anti-Patterns table. Max 400 lines.

- [x] T019 [P] [US3] Create `skills/core/fluent-validation/SKILL.md` (FR-004) — YAML frontmatter with name: `dotnet-ai-fluent-validation`, category: `core`, agent: `dotnet-architect`. Content must include: (a) Core Principles (fail fast, explicit rules, reusable validators), (b) "When to Use" (DTOs, request models, form input) / "When NOT to Use" (domain invariants — use domain logic), (c) Basic Validator: `public sealed class CreateOrderValidator : AbstractValidator<CreateOrderRequest> { public CreateOrderValidator() { RuleFor(x => x.Name).NotEmpty().MaximumLength(200); } }`, (d) DI Registration: `builder.Services.AddValidatorsFromAssemblyContaining<CreateOrderValidator>()`, (e) Manual Validation: `var result = await validator.ValidateAsync(request, ct); if (!result.IsValid) { ... }`, (f) Auto-Validation in Minimal API: endpoint filter pattern, (g) Custom Validators: `Must()`, `MustAsync()`, cross-field validation, (h) Async Validators: database uniqueness checks with `MustAsync`, (i) Reusable Rules: `Include()` for shared validation, (j) Integration with ProblemDetails for API responses, (k) Decision Guide, (l) Anti-Patterns table. Max 400 lines.

**Checkpoint**: 2 security skills + 1 validation skill exist. Each generates secure code. Each under 400 lines.

---

## Phase 5: User Story 4 — Mapping Strategies (Priority: P2)

**Goal**: Developers get manual-first mapping guidance with AutoMapper/Mapster comparison for context.

**Independent Test**: Load skill and verify it recommends manual mapping by default. Verify under 400 lines.

### Implementation for User Story 4

- [x] T020 [P] [US4] Create `skills/core/mapping-strategies/SKILL.md` (FR-005) — YAML frontmatter with name: `dotnet-ai-mapping-strategies`, category: `core`, agent: `dotnet-architect`. Content must include: (a) Core Principles (explicit is better than implicit, compile-time safety, manual-first), (b) "When to Use Manual Mapping" (most projects, explicit control, compile-time errors), (c) "When to Consider a Mapper Library" (100+ similar DTOs, rapid prototyping), (d) Manual Mapping — Extension Methods: `public static OrderDto ToDto(this Order order) => new(order.Id, order.Name, order.Status.ToString());`, (e) Manual Mapping — LINQ Projections: `dbContext.Orders.Select(o => new OrderDto(o.Id, o.Name)).ToListAsync()`, (f) Manual Mapping — Static Factory: `OrderDto.FromEntity(order)`, (g) AutoMapper Comparison: `CreateMap<Order, OrderDto>()`, profile setup, risks (runtime mapping errors, hidden complexity, over-use of ProjectTo), (h) Mapster Comparison: code-gen approach, `TypeAdapterConfig`, compile-time mapping, (i) Decision Guide table: Scenario | Approach | Why — with manual as default for all but large-scale DTO explosion, (j) Anti-Patterns table: implicit mapping bugs, Mapper.Map everywhere, missing map configuration discovered at runtime. Max 400 lines.

**Checkpoint**: Mapping skill exists. Recommends manual mapping by default. Under 400 lines.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Update planning docs, plugin manifests, and project documentation to reflect 116 skills.

- [x] T021 [P] Update `planning/11-expanded-skills-inventory.md` — add 10 new skills to the inventory (FR-012): Add to CATEGORY 1 (Core): solid-principles, design-patterns, functional-csharp, fluent-validation, mapping-strategies (with agent: dotnet-architect). Add to CATEGORY 3 (Web API): caching-strategies, rate-limiting, signalr-realtime (with agent: api-designer). Add to CATEGORY 7 (Security): cors-configuration, input-sanitization (with agent: api-designer). Update total from 106 to 116. NOTE: FR-011 (version-roadmap.md) was PRE-COMPLETED earlier — no task needed.

- [x] T022 [P] Update `.claude-plugin/plugin.json` — change description from "106 skills" to "116 skills", update `skills_summary.total` from 106 to 116, add counts: core +5 (was 7, now 12), api +3 (was 7, now 10), security +2 (was 3, now 5). Add new skill entries to the `skills_summary.categories` object. (FR-013)

- [x] T023 [P] Update `.claude-plugin/marketplace.json` — change description from "27 commands, 106 skills" to "27 commands, 116 skills" (FR-014)

- [x] T024 [P] Update `CLAUDE.md` — find and replace any references to "106 skills" with "116 skills" in the project description or structure sections (FR-015)

- [x] T025 [P] Update `README.md` — replace all "106 skills" with "116 skills" (FR-016): (a) line 5 banner subtitle, (b) line 17 badge bar, (c) line 75 plugin install note, (d) line 136 skills section header, (e) line 446 project tree comment. Verify with `grep "106 skills" README.md` returns zero matches.

- [x] T026 [P] Update `CONTRIBUTING.md` — replace "106 skills" with "116 skills" in project tree (FR-017)

- [x] T027 [P] Update `.specify/memory/constitution.md` — (FR-018): (a) change line 150 from "106 skills" to "116 skills", (b) increment version from 1.0.3 to 1.0.4, (c) update Sync Impact Report HTML comment at top: add "Updated sections: Technology Constraints: skills 106 → 116 (added 10 paradigm/best-practice skills)", (d) change version line 213 to "1.0.4" and "Last Amended" to current date

- [x] T028 [P] Update remaining planning docs — replace "106" with "116" in skill references (FR-019): (a) `planning/01-vision.md` line 144, (b) `planning/02-skills-inventory.md` line 30, (c) `planning/03-agents-design.md` line 3, (d) `planning/06-build-roadmap.md` line 252, (e) `planning/07-project-structure.md` lines 40 and 148

- [x] T029 [P] Update `CHANGELOG.md` — update existing v1.0.0 entry (FR-020): (a) Replace "106 skills" with "116 skills" in all v1.0.0 references (lines 13, 19, 34), (b) Add to existing "### Added" section: "- 10 paradigm and best-practice skills: solid-principles, design-patterns, functional-csharp, fluent-validation, mapping-strategies, caching-strategies, rate-limiting, signalr-realtime, cors-configuration, input-sanitization"

- [x] T030 Verify implementation: (a) run `find skills/ -name "SKILL.md" | wc -l` (expect 116), (b) verify each new skill has YAML frontmatter with name/description/category/agent, (c) verify each is under 400 lines with `wc -l`, (d) verify plugin.json and marketplace.json say "116 skills", (e) run `grep -r "106 skills" --include="*.md" --include="*.json" . | grep -v specs/00` — expect zero matches in active docs, (f) verify constitution version is 1.0.4

**Checkpoint**: All docs, manifests, README, constitution, and counts updated. Total skills = 116. Zero "106 skills" references remain in active docs.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — create directories immediately
- **User Stories (Phases 2-5)**: Depend on Phase 1 directories existing
  - US1, US2, US3 are all P1 and can proceed in parallel
  - US4 (P2) can also proceed in parallel — no code dependencies
- **Polish (Phase 6)**: Depends on all 10 skills being created (Phases 2-5)

### User Story Dependencies

- **US1 (Paradigm)**: Independent — 3 core skills, no dependencies on other stories
- **US2 (API Infrastructure)**: Independent — 3 api skills, no dependencies on other stories
- **US3 (Security & Validation)**: Independent — 2 security + 1 core skill, no dependencies
- **US4 (Mapping)**: Independent — 1 core skill, no dependencies

### Within Each User Story

- All skills within a story are marked [P] — can be written in parallel (different files)
- No ordering constraints within a story

### Parallel Opportunities

- T001-T010: All 10 directory creations in parallel
- T011-T013: All 3 paradigm skills in parallel
- T014-T016: All 3 API skills in parallel
- T017-T019: All 3 security/validation skills in parallel
- T021-T029: All 9 doc updates in parallel
- **Maximum parallelism**: All 10 skill tasks (T011-T020) can run simultaneously since they write to different files

---

## Parallel Example: All User Stories

```
# All skills can be created in parallel (different files, no dependencies):
T011: solid-principles/SKILL.md
T012: design-patterns/SKILL.md
T013: functional-csharp/SKILL.md
T014: caching-strategies/SKILL.md
T015: rate-limiting/SKILL.md
T016: signalr-realtime/SKILL.md
T017: cors-configuration/SKILL.md
T018: input-sanitization/SKILL.md
T019: fluent-validation/SKILL.md
T020: mapping-strategies/SKILL.md

# Then all doc updates in parallel:
T021: expanded-skills-inventory.md
T022: plugin.json
T023: marketplace.json
T024: CLAUDE.md
T025: README.md
T026: CONTRIBUTING.md
T027: constitution.md
T028: planning docs (01, 02, 03, 06, 07)
T029: CHANGELOG.md
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (create directories)
2. Complete Phase 2: US1 — solid-principles, design-patterns, functional-csharp
3. **STOP and VALIDATE**: Verify 3 paradigm skills have correct structure and content
4. This alone closes the biggest gap (paradigm guidance)

### Incremental Delivery

1. Setup → directories created
2. US1 (Paradigm) → 3 foundational skills → validate
3. US2 (API Infra) → 3 API skills → validate
4. US3 (Security) → 3 security/validation skills → validate
5. US4 (Mapping) → 1 mapping skill → validate
6. Polish → update counts, manifests, docs → final validation

### Full Parallel Strategy

Since all skills are independent files:
1. Create all 10 directories (T001-T010)
2. Write all 10 skills simultaneously (T011-T020)
3. Update all docs simultaneously (T021-T024)
4. Verify (T025)
5. **Total: 3 sequential steps, maximum parallelism within each**

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 30 |
| US1 tasks | 3 (paradigm skills) |
| US2 tasks | 3 (API infrastructure skills) |
| US3 tasks | 3 (security + validation skills) |
| US4 tasks | 1 (mapping skill) |
| Setup tasks | 10 (directories) |
| Polish tasks | 10 (docs + README + constitution + changelog + verify) |
| Parallel opportunities | 10 skills + 9 doc updates can run simultaneously |
| Suggested MVP | US1 only (3 paradigm skills) |
