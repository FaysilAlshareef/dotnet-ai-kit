# dotnet-ai-kit v2 — Artifacts Content-Quality Review

**Date:** 2026-06-02 · **Status:** REVIEW — findings only, **nothing changed.** Read-only content audit of **all 246 artifacts** (182 skills · 15 agents · 21 rules · 12 profiles · 16 knowledge), one reviewer per batch, judged against the kit's own standards (description standard · token ceilings · progressive disclosure · dogfooding) and .NET-10 currency.
**Method:** a 35-agent review workflow (`artifact-content-review`, 1.94M tokens, 565 tool calls) graded every artifact `good / minor / needs-enhance / broken` with `file:line` evidence + *why* + *how-to-fix*. The reviewers flagged 73 currency claims; the **highest-blast-radius ones were web-verified** (see §5). Complements [27](27-post-022-fidelity-and-defect-audit.md) (engine/defect audit) and feeds the execution plan in [29](29-v2-execution-plan-fidelity-and-enhancement.md).

## Tally

| Verdict | Count | Meaning |
|---|---|---|
| ✅ good | 77 (31%) | correct + meets standards |
| 🟡 minor | 107 (44%) | small fixes |
| 🟠 needs-enhance | 54 (22%) | substantive content/structure/depth work |
| 🔴 broken | 8 (3%) | incorrect, contradictory, or fails at compile/runtime |

**Headline:** the corpus is **substantively sound** (75% good/minor) but carries **one systemic policy gap** (MediatR-as-default — ~15 real fixes, the rest already covered by the kit's always-on rule), a **handful of compile/runtime-broken samples** (8), a few **genuinely serious correctness/security bugs hiding in `needs-enhance`**, and a long tail of **legacy description / progressive-disclosure / v1-residue** debt. None of it is structural — it is concentrated, well-localized cleanup.

---

## 1. Executive summary — the cross-cutting themes (ranked by impact)

| # | Theme | Reach | Verdict-driver | Fix shape |
|---|---|---|---|---|
| **T1** | **MediatR-as-default vs the kit's own always-on `mediator-abstraction` rule** — 2 Domain-layer `:INotification` leaks + ~13 skills/agents/docs teaching raw `AddMediatR` as the *default*; the remaining MediatR consumers are already covered by the always-on rule (benign) | **~15 fix · ~15 rule-covered** | drives `needs-enhance` + `minor` | abstract the root `mediatr-handlers`; add caveat + `ISender` framing only where MediatR is the *default*, not every `IMediator` use |
| **T2** | **Commercial libraries recommended as free defaults** — FluentAssertions (all test skills) and AutoMapper (`solid-principles`, weakly `mapping-strategies`) | ~8 artifacts | `needs-enhance`/`minor` | caveat + free alt (AwesomeAssertions/Shouldly; Mapperly/manual) — **web-confirmed §5** |
| **T3** | **Stale v1 Python / pre-.NET-10 residue** — `pip install`, a Python `mcp_check.*` call, a `.py` scaffold, "Python (for tools like this one)", `pytest`/`ruff`, `RuntimeMoniker.Net90` | ~8 artifacts | 1 broken + `needs-enhance` | delete the Python branches; bump monikers |
| **T4** | **Progressive-disclosure debt (code-density)** — 10+ skills inline 50–78% code with no `references/`/`examples/` | ~12 skills | `needs-enhance`/`minor` | relocate heavy/multi-variant code (Phase G) |
| **T5** | **Self-consistency / duplication / dead cross-refs** — near-duplicate skills, profiles restating universal rules, broken `skills/...` paths in knowledge docs, sibling-shape drift | ~20 artifacts | mixed | dedupe + repoint + reconcile one canonical shape |
| **T6** | **Legacy descriptions & agent boundaries** — 13/15 agents + most domain rules lack the `Use when…/Do NOT use… (use X)` selector; 5 agents' `## Boundaries` name capabilities not sibling **names**; 7 knowledge docs say `"(migrated artifact)"` | ~30 artifacts | `minor`/`needs-enhance` | backfill to standard (Phase H/I) |
| **T7** | **Cross-platform shell** — `grep -r`/`find`/`sed` in "Detect Existing Patterns" blocks on a Windows-first kit | ~10 skills | `minor` | PowerShell/`rg`/tool-agnostic prose |
| **T8** | **Version-currency pins** — Aspire `13.1`→13.4, OpenIddict `10.x` (wrong), MudBlazor `IsInitiallyExpanded`→`Expanded`, gRPC transcoding `8.0.*`→`10.0.*`, BenchmarkDotNet moniker | ~12 skills | `minor`/`needs-enhance` | bump/verify (web table §5) |

**The single most important finding (T1):** the kit *already decided* MediatR is commercial-and-abstracted (`rules/domain/mediator-abstraction.md`, the exemplary `cqrs/mediator-migration` skill), but **the corpus never propagated that decision.** It's broader than [27 A3/B3](27-post-022-fidelity-and-defect-audit.md) reported — it reaches **agents** (`ef-specialist`, `processor-architect`), **a rule** (`domain/architecture`), and the **flagship knowledge docs** (`cqrs-patterns`, `event-sourcing-flow`) — but because the rule is **always-on**, the fix is targeted (root skill + the 2 Domain-layer leaks + the ~13 raw-`AddMediatR` defaults), **not** a blanket 30-file caveat sweep (see the tiering in §4 T1).

---

## 2. 🔴 BROKEN — compile/runtime failures in shipped samples (8)

Every one is verifiable from the code alone (no runtime needed); these break the exact feature the artifact teaches.

| Artifact | Bug (`file:line`) | Fix |
|---|---|---|
| **api/minimal-api-validation** | `[ValidatableType]` placed on a **property** (`:34`) — the attribute targets `Class` only → **CS0592**; also no mention it is `[Experimental("ASP0029")]` in .NET 10 | Move `[ValidatableType]` to the nested **class** decl; add the ASP0029 experimental caveat (**web-confirmed §5**) |
| **core/configuration** | `MonitorService` declares a **primary ctor and an identical explicit ctor** (`:115-117`) → **CS0111** | Drop the primary-ctor parens; keep the explicit ctor |
| **security/auth-jwt** | writes `sub` short + reads `sub` short, but `MapInboundClaims` defaults **true** so `sub`→`NameIdentifier` → `Guid.Parse(null)` **throws on every authed request** (`:24-42,99,232`) | set `options.MapInboundClaims = false` (+ 4 minor correctness fixes: refresh-expiry option ignored, `user!` NRE, comma-packed permissions claim, legacy `JwtSecurityTokenHandler` vs the stated `JsonWebTokenHandler`) |
| **microservice/controlpanel/blazor-component** | `DialogService` never `@inject`-ed (`:104`) **and** `OpenEditDialog` never defined (`:56`) → **two compile breaks**; also flat `OrdersGateway` vs nested `Gateway.Orders` everywhere else | inject `IDialogService`; add `OpenEditDialog`; align to the nested gateway shape |
| **microservice/controlpanel/gateway-facade** | calls `http.DeleteAsync<bool>(url)` (`:65`) — no such generic extension exists (built-in `DeleteAsync` is non-generic) → compile error | add a `DeleteAsync<T>` extension or call the non-generic overload |
| **microservice/cosmos/transactional-batch** | single-op fast-path handles only Create/Upsert then `_operations.Clear()` (`:98-108`) → a lone **Replace/Delete is silently dropped (lost write)**; the skill's own ETag example exercises this path | add Replace/Delete/`default` cases, or delete the single-op special-case so all paths use the batch loop |
| **microservice/grpc/service-definition** | proto renamed to `total_cents`/`unit_price_cents` (`:60,87`) but mapping still reads `r.Total`/`i.UnitPrice` (`:128,130`) → won't compile; also a cents→decimal magnitude bug | rename **and** rescale (`/100m`) in `ToCommand` |
| **testing-patterns** (knowledge) | multiple tests reference `OutboxMessage.EventId/PublishedAt/Body`, `ICommitEventService<T>.CommitAsync`, instance `LoadFromHistory`, `Order.Create(string,decimal)` — **none exist** in the sibling `outbox-pattern`/`event-sourcing-flow` docs; plus stale `RuntimeMoniker.Net90` | rewrite tests against the real interfaces; reconcile the two docs to one aggregate API; bump the moniker |

---

## 3. 🟠 Serious correctness/security bugs hiding in `needs-enhance`

Not flagged "broken" (they compile or are partly correct) but they are **real defects a senior engineer would catch in review** — several are security- or data-integrity-grade:

- **architecture/multi-tenancy — cross-tenant data leak.** `HasQueryFilter` closes over a **scoped** `tenantProvider`; EF caches the model once, so every later request reuses the **first** tenant's filter (`:214-261`). The skill's headline promise is "one tenant must never see another's data." → reference the tenant via a context property + register an `IModelCacheKeyFactory`. Also: only `SaveChangesAsync` is overridden for tenant-stamping (sync path leaks).
- **infra/email-notifications — HTML/email injection.** Model values interpolated **unencoded** into an HTML body (`:82-91`). → `WebUtility.HtmlEncode` / a real template engine.
- **messaging/dapr-workflow — timeout never compensates.** `WaitForExternalEventAsync<bool>(name, timeout)` **throws `TaskCanceledException`** on timeout (doesn't return `false`), so the marquee compensation branch is dead and the orchestrator faults (`:35-40`). → wrap in try/catch.
- **resilience/circuit-breaker — health check always Healthy.** `GetPipeline(key)` never throws on open circuit, so the `Degraded` branch is dead code (`:159-182`); two comments also invert the actual outer/inner strategy order. → use `CircuitBreakerStateProvider`.
- **docs/changelog-gen — generates empty changelogs.** `git log --oneline | grep '^feat:'` matches nothing (subject isn't at column 0) — verified empirically (`:104,111,118`). → `--pretty=format:"%s"`.
- **microservice/{processor/hosted-service, query/listener-pattern} — fire-and-forget lifecycle.** `StartAsync`/`StopAsync` discard the processor Tasks (never await `CloseAsync`), defeating graceful shutdown; `listener-pattern` also returns `false` for unknown subjects → **poison-message redelivery loop**, contradicting its own `event-routing` sibling.
- **microservice/cosmos/cosmos-entity — partition key never persisted.** PK level built from `CreatedAt.ToString("yyyy-MM")`, a transient literal serialized to no JSON path (`:57-61`) → document lands in a different logical partition than reads target.
- **cqrs/pipeline-behaviors — behaviors may silently never run.** open generics registered via `AddBehavior(typeof(IPipelineBehavior<,>), …)` where MediatR wants `AddOpenBehavior(…)` (`:206-215`) — verify against the pinned MediatR version.
- **testing/integration-testing — canonical "real DB" factory can't be constructed.** `IClassFixture<>` on a `WebApplicationFactory` subclass is inert and its primary-ctor arg is never supplied (`:104-105`); the lead example uses EF InMemory, contradicting the skill's whole point.
- **testing/test-fixtures, microservice/command/outbox — undeclared `cancellationToken`** (won't compile); outbox also propagates a `GeOutboxMessageAsync` **typo** and tells readers to reproduce it.
- **microservice/controlpanel/mudblazor-patterns — `async void`** via awaiting inside the sync `Switch` (`:127-135`) → unobserved exceptions crash the Blazor circuit; use `SwitchAsync`.
- **knowledge/{event-sourcing-flow, outbox-pattern} — false at-least-once + racy guard.** both claim crash-safe at-least-once while explicitly shipping **no recovery poller** (fire-and-forget `Task.Run` only), and both ship a non-volatile `lockedScopes` int read/incremented outside the lock.

---

## 4. Systemic themes in depth

### T1 — MediatR-as-default (three tiers, not one flat sweep)
The kit's `rules/domain/mediator-abstraction.md` (always-on `**/*.cs`) already says: *MediatR is commercial; dispatch through an `ISender`/`IMediator` port; default to source-gen `Mediator` (MIT); MediatR opt-in with a license note.* The exemplar `cqrs/mediator-migration` does this perfectly. Because the rule is **always-on**, not every artifact that touches MediatR needs an inline caveat — the reviewers explicitly noted the house policy "keeps the caveat in `mediator-migration`, not every consumer." Scope by tier:

- **Tier A — real violations (FIX):**
  - *Domain-layer leak (most serious, fix first):* `architecture/ddd-patterns` and `cqrs/notification-handlers` declare `IDomainEvent : INotification`, forcing a commercial type into the Domain — against the rule's "MUST NOT reference MediatR from domain/application."
  - *Raw `AddMediatR`/"Install MediatR" as the unqualified default:* the **root** `cqrs/mediatr-handlers` ("Install MediatR"), `core/dependency-injection`, `core/design-patterns`, `core/solid-principles`, `data/db-transactions`, `cqrs/{command-generator,pipeline-behaviors,query-generator,request-response}`, `architecture/{clean-architecture,modular-monolith,vertical-slice}`, `api/{caching-strategies,controller-patterns}`, `microservice/command/command-handler`.
  - *Agents / rule / knowledge that NAME MediatR as the default:* agents `ef-specialist`, `processor-architect`; rule `domain/architecture` (`:21`); knowledge `cqrs-patterns`, `event-sourcing-flow` (MediatR-dense, no caveat).
- **Tier B — already covered by the always-on rule (optional one-line cross-note, NOT a blocker):** artifacts that merely *use* `IMediator`/`ISender` or mention it in passing — `testing/integration-testing`, `microservice/{grpc/service-definition, processor/{batch-processing,event-routing,hosted-service}, query/{event-handler,listener-pattern,query-handler}}`, `commands/{implement,explain,learn,add-crud}`, the lighter knowledge touches (`clean-architecture-patterns`, `ddd-patterns`, `modular-monolith-patterns`, `vsa-patterns`, `event-versioning`, `service-bus-patterns`, `grpc-patterns`), profiles `command`/`processor`/`query-sql`. The reviewers themselves called these "a light cross-note, not a blocker."
- **Root-cause fix:** abstract the **`cqrs/mediatr-handlers`** skill (the canonical "Install MediatR" source) so Tier-A skills reference it rather than restate MediatR.

Web-confirmed: **MediatR v13.0.0 (Jul 2025) is commercial; v12.x stays Apache-2.0** — so the rule's pin `[12.4.1,13.0.0)` is correct, and skills citing "v12.5" should say **v13**.

### T2 — Commercial libraries as free defaults
- **FluentAssertions** (`testing/test-fixtures`, `quality/architectural-fitness`, `testing/unit-testing`, `testing/integration-testing`, `test-engineer`, `commands/add-tests`): **v8+ is commercial** (Xceed, $130/dev/yr); v7 stays Apache-2.0. The kit *itself* doesn't pin it (uses xUnit `Assert` + Verify) — pure recommendation drift. → caveat + **AwesomeAssertions** (MIT drop-in) or **Shouldly**; note the assertions are library-agnostic.
- **AutoMapper** (`core/solid-principles` recommends it as a default; `core/mapping-strategies` argues against it only on debuggability): **commercial since v15 / Jul 2025**. → add the license argument; free source-gen alt = **Mapperly** (MIT) or manual mapping.

### T3 — v1 Python / pre-.NET-10 residue
`commands/init` (`pip install dotnet-ai-kit` → should be `dotnet tool install --global DotnetAiKit.Tool`); `commands/configure` (`mcp_check.check_codebase_memory_mcp()` — nonexistent Python fn); `commands/constitution` (`.py` scaffold script + orphaned path); `workflow/git-worktree-isolation` ("Python (for tools like this one)" + `pip`/`pytest`); `rules/domain/testing` (whole `## Python Test Patterns` section + "for both .NET and Python tests"); `workflow/verification-gate` (`ruff`); `knowledge/testing-patterns` + `testing/performance-testing` (`RuntimeMoniker.Net90`). All contradict CLAUDE.md ("the v1 Python CLI has been removed").

### T4 — Progressive-disclosure debt (relocate to `references/`/`examples/`)
`api/caching-strategies` (6 variants), `api/grpc-design` (399 ln), `architecture/multi-tenancy` (3 isolation patterns), `docs/diagram-gen` (7 diagram templates), `microservice/event-catalogue` (generator+tests+manifest), `microservice/query/listener-pattern` (205-ln monolith), `microservice/controlpanel/{mudblazor-patterns,blazor-component,gateway-facade}`, `api/signalr-realtime`, `microservice/command/outbox`. (These are exactly Phase G in [29](29-v2-execution-plan-fidelity-and-enhancement.md).)

### T5 — Self-consistency / duplication / dead cross-refs
- **Near-duplicate skills:** `api/minimal-api` ↔ `api/minimal-api-patterns` (same surface, neither's boundary names the other; the "patterns" one is a 31-ln stub); `core/csharp-idioms` ↔ `core/modern-csharp` (version matrix + field-keyword duplicated, the boundary it promises is false); `data/specification-pattern` ↔ `data/repository-patterns` (hand-rolled `ISpecification<T>` vs Ardalis — incompatible).
- **Profiles restating universal rules:** `generic` (worst — ~entire body), `vsa` (two `## Data Access` sections), `clean-arch`/`ddd`/`modular-monolith` (generic Testing/Data-Access tails). → keep only architecture-specific constraints (this is [29 C2/W5.2](29-v2-execution-plan-fidelity-and-enhancement.md), and a prerequisite for always-on profile delivery).
- **Dead cross-refs:** `knowledge/cqrs-patterns`, `clean-architecture-patterns`, `modular-monolith-patterns`, `vsa-patterns` point at `skills/architecture/cqrs-setup.md`/`mediatr-pipeline.md` (don't exist — real skills live under `skills/cqrs/*`). Several rules have a broken `Related-Skills` path (`api-design`, `localization`, `multi-repo`, `naming`).
- **Sibling-shape drift:** blazor flat `OrdersGateway` vs nested `Gateway.Orders`; gRPC `Total`/`UnitPrice` vs `TotalCents`/`UnitPriceCents` (`service-definition` ↔ `grpc/validation`); `PaginatedList` vs `PagedList`, `Result.Failure(string)` vs `Error`-based across the CQRS cluster.

### T6 — Descriptions & agent boundaries (legacy, dogfooding)
- **Agents:** only `aspire-architect` + `ai-engineer` meet the v2 description standard. The other 13 have noun-phrase descriptions with no `Use when…/Do NOT use… (use X)`; `ef-specialist`/`gateway-architect`/`processor-architect`/`query-architect`/`test-engineer` `## Boundaries` say what they *don't* do **without naming the sibling that does** (`query-architect` names Cosmos but by **path**, which won't survive projection). → [29 H1/H2](29-v2-execution-plan-fidelity-and-enhancement.md).
- **Rules:** most `domain/*` descriptions lack the boundary clause (`mediator-abstraction`, `testing-platform`, `ai-integration` are the good models).
- **Knowledge:** 7 docs ship the placeholder `"… (migrated artifact)."` description (`cqrs-patterns`, `event-sourcing-flow`, `outbox-pattern`, `concurrency-patterns`, `cosmos-patterns`, `deployment-patterns`, `documentation-standards`, etc.).
- **Self-referential skill descriptions:** `api/openapi-scalar`, `api/rate-limiting`, `api/signalr-realtime`, `api/versioning` ("Use this skill when you need this skill").

### T7 — Cross-platform shell
`grep -r --include`, `find`, `sed` in "Detect Existing Patterns" blocks across `data/specification-pattern`, `quality/{architectural-fitness,code-analysis,review-checklist}`, `devops/aspire-orchestration`, `infra/email-notifications`, `architecture` skills, several `workflow/*` — won't run in the kit's Windows-first/PowerShell default. → `Select-String`/`rg`/tool-agnostic prose.

---

## 5. Web-verification results (currency claims that change verdicts)

Verified against current (2026) sources; the rest of the 73 `webVerify` flags are lower-blast-radius pins to spot-check at authoring time.

| Claim | Verdict | Detail |
|---|---|---|
| **FluentAssertions v8 commercial** | ✅ TRUE | Xceed proprietary, ~Jan 2025, $130/dev/yr; **v7 stays Apache-2.0**; free: AwesomeAssertions (MIT), Shouldly |
| **MediatR commercial boundary** | ✅ **v13.0.0** (Jul 2 2025) | v12.x Apache-2.0 → kit's `[12.4.1,13.0.0)` pin is correct; dual RPL-1.5/commercial, Community <$5M rev |
| **AutoMapper commercial** | ✅ TRUE | v15 / Jul 2 2025 (Lucky Penny); free source-gen alt = **Mapperly** (MIT) |
| **MassTransit license** | ✅ v8 Apache-2.0 (**EOL end-2026**), **v9 commercial** ($400/mo min) | `messaging-bus-selection` rule is accurate |
| **Wolverine license** | ✅ **MIT, free** | only JasperFx *support* is paid → the rule can recommend it confidently |
| **.NET Aspire version** | 🟡 pin stale | skills pin `13.1`; **current 13.4** (Aspire 13 GA'd at .NET Conf 2025, dropped the ".NET" prefix) — bump or go version-agnostic |
| **Microsoft.Extensions.AI** | ✅ **10.6.0 GA** | the AI skills' version + `IChatClient` framing are current |
| **ValidatableTypeAttribute (.NET 10)** | ✅ **`[Experimental("ASP0029")]`**, targets **Class** | confirms the `minimal-api-validation` BROKEN verdict on both counts; needs `#pragma warning disable ASP0029` |

**Still flagged (verify at authoring time, not yet web-checked):** OpenIddict major for .NET 10 (skill's "10.x" is almost certainly wrong — historically 5.x/6.x), MudBlazor `IsInitiallyExpanded`→`Expanded` (v7/v8), BenchmarkDotNet `RuntimeMoniker.Net10_0` exact spelling, ASP.NET Core 10 passkey API surface, HotChocolate v15 currency, TUnit GA-vs-pre-1.0, EF 10 `HasData` vs `UseSeeding`, Dapr timeout semantics, Calzolari gRPC-validation package id, `Grpc.Tools`/`Google.Protobuf` pins.

*Sources:* [FluentAssertions v8 (InfoQ)](https://www.infoq.com/news/2025/01/fluent-assertions-v8-license/) · [AwesomeAssertions/Shouldly (2026)](https://codingdroplets.com/fluentassertions-vs-shouldly-vs-awesomeassertions-dotnet-2026) · [MediatR v13 commercial (Bogard)](https://www.jimmybogard.com/automapper-and-mediatr-commercial-editions-launch-today/) · [AutoMapper commercial](https://github.com/LuckyPennySoftware/AutoMapper/discussions/4536) · [MassTransit v9](https://masstransit.io/introduction/v9-announcement) · [Wolverine (GitHub)](https://github.com/JasperFx/wolverine) · [Aspire 13.2 (InfoQ)](https://www.infoq.com/news/2026/04/aspire-13-2-release/) · [Extensions.AI GA](https://devblogs.microsoft.com/dotnet/ai-vector-data-dotnet-extensions-ga/) · [ValidatableTypeAttribute (MS Learn)](https://learn.microsoft.com/en-us/dotnet/api/microsoft.extensions.validation.validatabletypeattribute?view=net-10.0-pp)

---

## 6. Per-artifact verdicts (all 246)

Every artifact, its verdict, and the one-line reason. 🔴 broken · 🟠 needs-enhance · 🟡 minor · ✅ good. *(Below, `good`/`minor` reasons are grouped by cluster for readability; each artifact also gets its own individual line in the [companion appendix](30-appendix-all-artifacts.md).)*

### Commands (32) — 13 good · 13 minor · 6 needs-enhance
| Artifact | V | Why |
|---|---|---|
| constitution | 🟠 | false "gates analyze/review" claim; writes an orphaned path no sibling reads |
| add-aggregate | 🟠 | example teaches `AggregateRoot`+`Raise` vs the canonical `Aggregate<T>`+`ApplyChange` |
| init | 🟠 | `pip install dotnet-ai-kit` (v1 residue) → `dotnet tool install --global DotnetAiKit.Tool` |
| configure | 🟠 | names a nonexistent Python `mcp_check.*` fn |
| specify · clarify · tasks · analyze · verify · release · fix · status · checklist · add-endpoint · add-entity · add-event · detect · docs · checkpoint · wrap-up | ✅ | well-structured, compliant, routes resolve |
| plan · implement · orchestrate · review · pr · do · add-crud · add-page · add-tests · learn · explain · undo | 🟡 | mostly MediatR/AutoMapper-caveat gaps, `/dai.` vs `/dotnet-ai.` drift, or Unix-only fallback |

### API (14) — 1 good · 9 minor · 3 needs-enhance · 1 broken
| Artifact | V | Why |
|---|---|---|
| minimal-api-validation | 🔴 | `[ValidatableType]` on a property (CS0592) + experimental status unstated |
| grpc-design | 🟠 | transcoding pinned `8.0.*`; 399-ln code-dense, needs `references/` |
| minimal-api | 🟠 | duplicates `minimal-api-patterns`, boundary doesn't disambiguate |
| minimal-api-patterns | 🟠 | 31-ln stub overlapping `minimal-api`; version floor self-contradicts |
| endpoint-filters | ✅ | lean, correct, names both siblings |
| caching-strategies | 🟠 | 6 inlined variants, MediatR caveat missing |
| content-negotiation · controller-patterns · graphql-hotchocolate · openapi-scalar · rate-limiting · signalr-realtime · versioning | 🟡 | self-referential descriptions / MediatR mention / minor runtime nit |
| server-sent-events | ✅ | tight, current, boundary-rich |

### Architecture (6) — 1 good · 3 minor · 2 needs-enhance
| advisor ✅ | clean-architecture 🟡 (MediatR default) | ddd-patterns 🟠 (`IDomainEvent:INotification` domain leak; primitive `Guid` Id) | modular-monolith 🟡 (MediatR) | multi-tenancy 🟠 (**EF query-filter cross-tenant leak**) | vertical-slice 🟡 (MediatR) |

### Core (12) — 3 good · 5 minor · 3 needs-enhance · 1 broken
| Artifact | V | Why |
|---|---|---|
| configuration | 🔴 | duplicate ctor (CS0111) |
| csharp-idioms | 🟠 | duplicates `modern-csharp` (matrix, field keyword); false boundary |
| dependency-injection | 🟠 | flagship `AddMediatR` default vs the rule |
| design-patterns | 🟠 | MediatR default across 4 patterns |
| solid-principles | 🟠 | MediatR + **recommends AutoMapper** |
| async-patterns · functional-csharp ✅ ; coding-conventions · error-handling · mapping-strategies · modern-csharp 🟡 | | minor self-consistency / deprecated-clock / placeholder nits |
| fluent-validation | ✅ | excellent, current |

### CQRS (7) — 1 good · 4 minor · 2 needs-enhance
| mediator-migration ✅ (the exemplar) | mediatr-handlers 🟡 ("Install MediatR", no caveat — **root of T1**) | command-generator · query-generator · request-response 🟡 (MediatR caveat) | notification-handlers 🟠 (`IDomainEvent:INotification`; public-setter aggregate) | pipeline-behaviors 🟠 (`AddBehavior` vs `AddOpenBehavior` latent bug) |

### Data (8) — 5 good · 2 minor · 1 needs-enhance
| audit-trail · dapper · ef-core-basics · ef-migrations · ef-queries ✅ | repository-patterns 🟡 (Ardalis vs sibling) | db-transactions 🟠 (`AddMediatR` default; Snapshot-isolation prereq) | specification-pattern 🟠 (reinvents Ardalis; single-level Include / single OrderBy) |

### DevOps (8) — 1 good · 5 minor · 2 needs-enhance
| aspire-testing ✅ | aspire-deployment · aspire-integrations 🟡 (`13.1` pin) | aspire-orchestration 🟠 (names 1/3 siblings; Unix detect) | dockerfile 🟠 (dead `build` stage; no SDK container-publish) | azure-resources · github-actions · kubernetes 🟡 (Unix detect / missing securityContext) |

### Docs (8) — 3 good · 3 minor · 2 needs-enhance
| readme-gen · runbook · adr ✅ | api-docs · architecture-docs · onboarding 🟡 | changelog-gen 🟠 (**`git log --oneline | grep '^feat:'` → empty**) | diagram-gen 🟠 (7 variants → `references/`) |

### Messaging (6) — 4 good · 1 minor · 1 needs-enhance
| dapr-building-blocks · masstransit-consumers · masstransit-sagas · wolverine-messaging ✅ (the last two model the license caveat) | dapr-pubsub 🟡 | dapr-workflow 🟠 (**timeout throws, compensation branch dead**) |

### Security (8) — 3 good · 3 minor · 1 needs-enhance · 1 broken
| auth-jwt 🔴 (`sub` round-trip throws every request) | cors-configuration · input-sanitization ✅ | auth-policies · data-protection · entra-id-auth 🟡 | openiddict-server 🟠 ("OpenIddict 10.x" wrong; thin) | passkeys-webauthn 🟠 (login may not sign in; endpoints undefined) |

### Testing (7) — 2 good · 2 minor · 3 needs-enhance
| playwright-e2e · mutation-testing ✅ | tunit-testing · unit-testing 🟡 (FluentAssertions) | integration-testing 🟠 (real-DB factory unconstructable; InMemory lead) | performance-testing 🟠 (`Net90`; Newtonsoft-only) | test-fixtures 🟠 (undeclared `cancellationToken`; fragile name transform) |

### Quality (6) — 2 good · 2 minor · 2 needs-enhance
| incremental-source-generator · analyzer-packaging ✅ | code-analysis · review-checklist 🟡 | architectural-fitness 🟠 (FluentAssertions default) | roslyn-analyzer 🟠 (analyzer+fix in one asm → RS1038) |

### Observability + Resilience (6) — 2 good · 3 minor · 1 needs-enhance
| health-checks · serilog-structured ✅ | opentelemetry · polly-resilience · retry-patterns 🟡 | circuit-breaker 🟠 (**health-check dead code; inverted order comments**) |

### AI + Infra + Detect (7) — 1 good · 5 minor · 1 needs-enhance
| smart-detect ✅ | extensions-ai-chat · extensions-ai-embeddings (Ollama pkg stale) · background-jobs · feature-flags · file-storage 🟡 | email-notifications 🟠 (**unencoded HTML injection**; undeclared helpers) |

### Workflow (11) — 4 good · 6 minor · 1 needs-enhance
| receiving-review-feedback · systematic-debugging · plan-templates · code-review-workflow ✅ | feature-tracking · multi-repo-workflow · plan-artifacts · sdd-lifecycle · session-management · verification-gate (`ruff`) 🟡 | git-worktree-isolation 🟠 (Python residue; `/dai.go` nonexistent) |

### Microservice (44) — 16 good · 16 minor · 8 needs-enhance · 4 broken
| Artifact | V | Why |
|---|---|---|
| controlpanel/blazor-component | 🔴 | DialogService not injected + `OpenEditDialog` undefined |
| controlpanel/gateway-facade | 🔴 | `DeleteAsync<T>` extension undefined |
| cosmos/transactional-batch | 🔴 | single-op path drops Replace/Delete (lost write) |
| grpc/service-definition | 🔴 | proto/mapping field mismatch + money magnitude |
| command/command-handler · processor/hosted-service · query/listener-pattern · controlpanel/mudblazor-patterns · cosmos/cosmos-entity · event-catalogue · grpc/validation · command/outbox | 🟠 | MediatR caveat / fire-and-forget lifecycle / poison-loop / async-void / unpersisted PK / `Activator` on positional record / undeclared ct |
| query/query-entity · query/sequence-checking · command/event-store · controlpanel/{blazor-hybrid,blazor-persistent-state,blazor-render-modes,response-result} · gateway/{endpoint-registration,gateway-endpoint,gateway-security,scalar-docs} | ✅ | self-consistent, correct, dogfood the aggregate rules |
| command/{aggregate-design,aggregate-testing,event-design,event-versioning} · cosmos/{cosmos-repository,partition-strategy} · processor/{batch-processing,event-routing,grpc-client} · query/{event-handler,query-handler} · grpc/interceptors · controlpanel/query-string-bindable | 🟡 | missing private ctor / MediatR caveat / Newtonsoft / minor nits |

### Agents (15) — 2 good · 8 minor · 5 needs-enhance
| aspire-architect · ai-engineer ✅ (the v2 models) | api-designer · command-architect · controlpanel-architect · cosmos-architect · devops-engineer · docs-engineer · dotnet-architect · reviewer 🟡 (shared description/boundary gap) | ef-specialist · processor-architect 🟠 (MediatR default) · gateway-architect · query-architect · test-engineer 🟠 (boundaries name no sibling; non-standard description) |

### Rules (21) — 5 good · 13 minor · 3 needs-enhance
| existing-projects · security · tool-calls · testing-platform · ai-integration · mediator-abstraction ✅ | async-concurrency (HttpClient clause) · coding-style (`field` mislabeled ".NET 14") · api-design · configuration · data-access · error-handling · localization · multi-repo · naming · observability · performance · messaging-bus-selection 🟡 (mostly description-boundary + broken Related-Skills paths) | architecture 🟠 (MediatR default) · testing 🟠 (Python residue) · deterministic-enforcement 🟠 (DAK0001 async-void drift; wrong "security" attribution) |

### Profiles (12) — 3 good · 7 minor · 2 needs-enhance
| hybrid · gateway · query-cosmos ✅ | clean-arch · ddd · modular-monolith · command · controlpanel (broad glob) · processor · query-sql 🟡 (generic-rule tails / glob) | generic 🟠 (worst duplication of universal rules) · vsa 🟠 (two `## Data Access` sections) |

### Knowledge (16) — 6 good · 7 minor · 3 needs-enhance
| concurrency-patterns · cosmos-patterns · dead-letter-reprocessing · deployment-patterns · documentation-standards · ddd-patterns ✅ (most carry the `(migrated artifact)` description nit) | clean-architecture-patterns · grpc-patterns · modular-monolith-patterns · service-bus-patterns · vsa-patterns · event-versioning 🟡 (MediatR + Newtonsoft + dead skill xrefs) | cqrs-patterns 🟠 (most MediatR-dense; dup type) · event-sourcing-flow 🟠 (false at-least-once; racy guard; MediatR/Newtonsoft) · outbox-pattern 🟠 (false at-least-once; racy guard; non-atomic loop) |

---

## 7. Prioritized remediation backlog (mapped to [planning/29](29-v2-execution-plan-fidelity-and-enhancement.md))

| Pri | Work | Items | Lands in 29 |
|---|---|---|---|
| **P0** | **Fix the 8 broken + the serious correctness/security bugs (§2–§3)** | 8 broken + multi-tenancy leak, email injection, dapr-workflow, circuit-breaker, changelog-gen, fire-and-forget lifecycle, cosmos PK, integration-testing factory, async-void, undeclared-ct, false-at-least-once | **Phase A** (expand it) + add doc-sample compile guards |
| **P0** | **MediatR Tier-A fixes (T1)** — abstract root `mediatr-handlers`; fix the **2 Domain-layer `:INotification` leaks**; replace raw `AddMediatR`-as-default in ~13 skills/agents/docs. Tier-B consumers are already rule-covered (optional cross-note only) | §4 T1 | **new sub-workstream** (Phase A/I; ~15 targeted fixes, not a flat 30-file sweep) |
| **P1** | **Commercial-library currency (T2)** + **v1 Python residue (T3)** + **version pins (T8)** | FluentAssertions/AutoMapper caveats; `pip`/`mcp_check`/`pytest`/`ruff`/`Net90`; Aspire 13.4, OpenIddict, MudBlazor, transcoding 10.0 | **Phase A/C** currency |
| **P1** | **Profile dedup (T5 profiles)** — strip generic-rule restatement from `generic`/`vsa`/`clean-arch`/`ddd`/`modular-monolith` | §4 T5 | **Phase C2 / W5.2** (prerequisite for always-on profile delivery) |
| **P2** | **Progressive disclosure (T4)** | the 12-skill list | **Phase G** |
| **P2** | **Agent boundaries + descriptions (T6)** | 13 agents + domain rules + 7 knowledge placeholder descriptions + self-referential skill descriptions | **Phase H / I** |
| **P3** | **Self-consistency dedup + dead cross-refs (T5)** | minimal-api/patterns, csharp-idioms/modern-csharp, specification/repository, blazor gateway shape, broken `skills/...` paths | **Phase C/G** |
| **P3** | **Cross-platform shell (T7)** + **deterministic-enforcement drift** | ~10 detect blocks; DAK0001 event-handler carve-out | **Phase I** |

**Suggested gate for the P0 correctness work:** a **doc-sample compile/parse check** (extend the FR-022-02 Roslyn-parse harness to the inline C# in flagged skills) so a "broken sample" can't silently ship again — the drift/count gates cannot see these.

---

## 8. Method, coverage & limits

- **Coverage:** 100% of artifacts (246/246) reviewed; every verdict carries `file:line` evidence + concrete `how`. Reviewers were instructed to be conservative (no invented issues; "good" stated plainly).
- **Web-verified:** the high-blast-radius licensing/version claims (§5). The remaining ~15 `webVerify` pins are listed for spot-check at authoring time — **not** yet confirmed (don't treat them as settled).
- **Not done (by design):** no adversarial second-pass verification of each finding (single capable reviewer per batch); no live build/test of samples (static reading only — though the broken set is compile-evident); no ≥20-query triggering eval.
- **Confidence:** the 8 broken are code-evident, and **5/8 were independently confirmed against source** — 3 spot-checked while finalizing this doc (`core/configuration` CS0111 at `:115-117`, `gateway-facade` undefined `DeleteAsync<T>` at `:66`, `transactional-batch` lost-write at `:98-108`), plus `event-catalogue`'s `Activator`-on-positional-record verified first-hand and `ValidatableType` via web — **0 misses**, so the sub-agent line numbers held. The §3 correctness bugs are code-evident but not all re-opened. The systemic themes (T1–T8) are corroborated across many independent reviewers, so they're robust. Individual `minor` summaries are single-reviewer leads — confirm at fix time.
- **Raw data:** the full structured findings (every issue's evidence/why/how) are in the workflow result; this doc curates them. Re-runnable via the persisted `artifact-content-review` workflow script.

---

*Review complete; no artifact or source changed. The corpus is healthy and mostly green — the value here is a precise, evidence-backed worklist: fix 8 broken samples + a dozen serious bugs, propagate the kit's own MediatR/commercial-library decisions corpus-wide, retire v1 residue, and pay down disclosure/description debt. All of it feeds [planning/29](29-v2-execution-plan-fidelity-and-enhancement.md) — most cleanly as an expanded Phase A + a dedicated MediatR sweep, ahead of the W1–W7 feature work.*
