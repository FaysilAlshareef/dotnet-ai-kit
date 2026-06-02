# Appendix to [planning/30](30-artifacts-content-review.md) — every artifact, individually

Companion to the content-quality review. **One row per artifact (all 246), each with its own verdict + one-line reason** — the main report's §6 groups the `good`/`minor` reasons by cluster; this appendix gives each its individual line. Full `why`/`how` for every 🔴 broken and 🟠 needs-enhance item is in §2–§4 of the [main report](30-artifacts-content-review.md).

Legend: 🔴 broken · 🟠 needs-enhance · 🟡 minor · ✅ good.

## Commands (32)
| Artifact | V | Reason |
|---|---|---|
| commands/constitution | 🟠 | false 'gates analyze/review' claim; writes an orphaned path no sibling consumes |
| commands/specify | ✅ | well-structured spec generator; routes resolve; sound multi-repo brief + branch-safety |
| commands/clarify | ✅ | solid interactive-clarification flow; sensible ambiguity taxonomy; routes resolve |
| commands/plan | 🟡 | strong plan generator; constitution gate bypasses the dedicated command; `/dai.` drift |
| commands/tasks | ✅ | clear phase-ordered task generator; correct event-sourced constraint; routes resolve |
| commands/analyze | ✅ | thorough read-only 11-pass analyzer with hard write-scope; routes resolve |
| commands/implement | 🟡 | comprehensive executor w/ review gate + undo log; routes Generic CQRS to MediatR uncaveated |
| commands/verify | ✅ | clean PASS/FAIL/WARN pipeline, mode-adaptive, correct .NET 10 commands |
| commands/orchestrate | 🟡 | accurate multi-repo conductor; thinnest of peers; no boundary vs /do |
| commands/review | 🟡 | strong standards-review playbook; two Unix shell idioms; fixed sibling-path list |
| commands/pr | 🟡 | thorough gh-CLI PR flow; one Unix-only fallback command |
| commands/release | ✅ | lean correct post-merge release; model description; defers to scripts/+examples/ |
| commands/fix | ✅ | exemplary lean TDD bug-fix; compilable repro example + deterministic scaffold |
| commands/status | ✅ | clear progress dashboard; good linked-feature handling and routing table |
| commands/do | 🟡 | solid lifecycle driver; advertised stage list inconsistent with canonical SDD sequence |
| commands/checklist | ✅ | lean quality-checklist gate; precise description; deterministic skeleton generator |
| commands/add-aggregate | 🟠 | example teaches `AggregateRoot`+`Raise` vs canonical `Aggregate<T>`+`ApplyChange` |
| commands/add-crud | 🟡 | strong multi-arch CRUD generator; AutoMapper/MediatR detection targets uncaveated |
| commands/add-endpoint | ✅ | clean gateway-endpoint generator; correct .NET 10 TypedResults example |
| commands/add-entity | ✅ | query-side read-model generator; correct SQL/Cosmos branching; faithful example |
| commands/add-event | ✅ | focused add-event generator; strong cross-service impact guidance; clean record example |
| commands/add-page | 🟡 | thorough Blazor page generator; example shows client-side MudTable not the headline ServerData |
| commands/add-tests | ✅ | comprehensive test-gen w/ framework auto-detect; only FluentAssertions currency note |
| commands/init | 🟠 | `pip install dotnet-ai-kit` (v1 residue) → `dotnet tool install --global DotnetAiKit.Tool` |
| commands/detect | ✅ | thorough, well-bounded detection; mode-vs-type invariant; exact MCP fallback |
| commands/configure | 🟠 | names a nonexistent Python `mcp_check.check_codebase_memory_mcp()` |
| commands/learn | 🟡 | lean constitution+topic-split generator; one commercial-library mention uncaveated |
| commands/docs | ✅ | comprehensive docs workflow; subcommand→skill table + agent ref all resolve |
| commands/explain | 🟡 | solid teaching command; lists MediatR without commercial-license flag |
| commands/checkpoint | ✅ | clean session-save; crisp boundary vs wrap-up; coherent flags/dry-run |
| commands/undo | 🟡 | careful safety-first revert; two POSIX shell idioms in a Windows-first kit |
| commands/wrap-up | ✅ | comprehensive session close; rich handoff template; clean boundary vs checkpoint |

## API (14)
| Artifact | V | Reason |
|---|---|---|
| api/caching-strategies | 🟠 | ~50%+ inlined across 6 variants, no subdirs; MediatR notification uncaveated |
| api/content-negotiation | 🟡 | solid formatters/Accept/ProblemDetails via ISender; one latent CSV-formatter bug |
| api/controller-patterns | 🟡 | idiomatic .NET 10 controllers; names MediatR default uncaveated |
| api/endpoint-filters | ✅ | lean, correct, names both sibling skills; appropriately flat |
| api/graphql-hotchocolate | 🟡 | strong HotChocolate v15 (source-gen DataLoader, [Authorize]); passing MediatR + version note |
| api/grpc-design | 🟠 | stale `8.0.*` transcoding pin; 399-ln code-dense → references/ candidate |
| api/minimal-api | 🟠 | duplicates minimal-api-patterns; boundary doesn't disambiguate |
| api/minimal-api-patterns | 🟠 | 31-ln stub overlapping minimal-api; version floor self-contradicts |
| api/minimal-api-validation | 🔴 | `[ValidatableType]` on a property (CS0592); experimental status unstated |
| api/openapi-scalar | 🟡 | comprehensive native-OpenAPI+Scalar; self-ref description; OpenAPI v2 model risk |
| api/rate-limiting | 🟡 | accurate, all four limiters + 429/Retry-After; self-referential 'Use when' |
| api/server-sent-events | ✅ | tight, .NET 10-current SSE; boundary-rich description; clean cancellation/resume |
| api/signalr-realtime | 🟡 | strong SignalR; self-ref description; four inlined variants belong in references/ |
| api/versioning | 🟡 | accurate Asp.Versioning via ISender; self-ref description; one wrong reference URL |

## Architecture (6)
| Artifact | V | Reason |
|---|---|---|
| architecture/advisor | ✅ | solid decision-guide; clean matrix/questionnaire; evals discriminate it |
| architecture/clean-architecture | 🟡 | accurate; only gap is MediatR default uncaveated vs the rule |
| architecture/ddd-patterns | 🟠 | `IDomainEvent : INotification` domain leak; primitive `Guid` Id vs own anti-pattern |
| architecture/modular-monolith | 🟡 | strong; concrete MediatR cross-module mechanism uncaveated |
| architecture/multi-tenancy | 🟠 | **EF query-filter model-cache cross-tenant leak**; incomplete SaveChanges override |
| architecture/vertical-slice | 🟡 | clean VSA reference; MediatR named default without caveat |

## Core (12)
| Artifact | V | Reason |
|---|---|---|
| core/async-patterns | ✅ | accurate .NET 10 async; one sample uses `.Result` it flags as anti-pattern |
| core/coding-conventions | 🟡 | solid; orphaned list item after References; recommends a deprecated clock abstraction |
| core/configuration | 🔴 | IOptionsMonitor sample has duplicate ctor (CS0111) |
| core/csharp-idioms | 🟠 | duplicates modern-csharp (matrix/field keyword); false boundary |
| core/dependency-injection | 🟠 | flagship `AddMediatR` default vs the always-on rule |
| core/design-patterns | 🟠 | MediatR default across four patterns vs the rule |
| core/error-handling | 🟡 | accurate RFC 9457 + gRPC mapping; NotFoundException shown twice (won't compile standalone) |
| core/fluent-validation | ✅ | excellent, current; clean When/When-NOT boundaries |
| core/functional-csharp | ✅ | high-quality FP-in-C#; correctly reuses an existing Result lib |
| core/mapping-strategies | 🟡 | manual-mapping-first (good); omits AutoMapper's commercial-license argument |
| core/modern-csharp | 🟡 | accurate C# 12/13/14 tour; one sample has an invalid class decl (placeholder slip) |
| core/solid-principles | 🟠 | MediatR default everywhere + explicitly recommends AutoMapper |

## CQRS (7)
| Artifact | V | Reason |
|---|---|---|
| cqrs/command-generator | 🟡 | solid scaffold; MediatR/IRequest default uncaveated, no migration link |
| cqrs/mediator-migration | ✅ | exemplary: MediatR-commercial framing, ISender port, MIT/Wolverine decision table |
| cqrs/mediatr-handlers | 🟡 | accurate handlers; 'Install MediatR' default, no caveat/migration link (T1 root) |
| cqrs/notification-handlers | 🟠 | `IDomainEvent : INotification` domain leak; public-setter aggregate |
| cqrs/pipeline-behaviors | 🟠 | `AddBehavior` vs `AddOpenBehavior` latent bug; MediatR caveat missing |
| cqrs/query-generator | 🟡 | clean query+pagination; MediatR caveat + PaginatedList/Result model drift |
| cqrs/request-response | 🟡 | strong contract design (best Result model); MediatR caveat + validator drift |

## Data (8)
| Artifact | V | Reason |
|---|---|---|
| data/audit-trail | ✅ | accurate SaveChanges-interceptor audit (TimeProvider, soft-delete, query filter) |
| data/dapper | ✅ | solid Dapper-alongside-EF read skill; multi-mapping, parameterized, factory |
| data/db-transactions | 🟠 | registers commercial MediatR via `AddMediatR` uncaveated; Snapshot-isolation prereq |
| data/ef-core-basics | ✅ | accurate EF setup; configs, converters, retry, interceptors, design-time factory |
| data/ef-migrations | ✅ | complete migrations skill; idempotent CI/CD, bundles, per-module history |
| data/ef-queries | ✅ | excellent EF query skill; AsNoTracking, projections, compiled, ExecuteUpdate/Delete |
| data/repository-patterns | 🟡 | good repo+UoW; specification section uses Ardalis vs sibling's hand-rolled |
| data/specification-pattern | 🟠 | reinvents Ardalis without saying so; single-level Include / single OrderBy |

## DevOps (8)
| Artifact | V | Reason |
|---|---|---|
| devops/aspire-deployment | 🟡 | lean accurate; dated `13.1` pin + CLI verb to verify |
| devops/aspire-integrations | 🟡 | strong WithReference/WaitFor; dated `13.1` pin |
| devops/aspire-orchestration | 🟠 | names 1 of 3 siblings; older template; Unix-only detect |
| devops/aspire-testing | ✅ | accurate lean e2e; xUnit lifecycle matches pinned v2 |
| devops/azure-resources | 🟡 | accurate Azure CLI provisioning; older template + Unix detect |
| devops/dockerfile | 🟠 | dead `build` stage; no .NET 10 SDK container-publish path |
| devops/github-actions | 🟡 | correct OIDC+ACR+AKS; sed token replacement + Unix detect |
| devops/kubernetes | 🟡 | production-shaped manifests; missing securityContext given non-root theme |

## Docs (8)
| Artifact | V | Reason |
|---|---|---|
| docs/adr | ✅ | accurate MADR-format; clean template/example/index; crisp boundaries |
| docs/api-docs | 🟡 | solid OpenAPI enrichment; boundary omits confusable sibling; MVC+Minimal mix |
| docs/architecture-docs | 🟡 | strong overview; mild multi-variant-diagram density overlapping diagram-gen |
| docs/changelog-gen | 🟠 | **`git log --oneline | grep '^feat:'` matches nothing → empty changelog** |
| docs/diagram-gen | 🟠 | 7 inlined diagram variants → references/<variant>.md |
| docs/onboarding | 🟡 | practical onboarding template; one stale SQL-Server env var (SA_PASSWORD) |
| docs/readme-gen | ✅ | comprehensive README gen; clean boundaries vs onboarding/api-docs |
| docs/runbook | ✅ | well-structured ops runbook; crisp boundaries vs onboarding/changelog-gen |

## Messaging (6)
| Artifact | V | Reason |
|---|---|---|
| messaging/dapr-building-blocks | ✅ | accurate state+invocation; correct ETag; exemplary selector description |
| messaging/dapr-pubsub | 🟡 | solid broker-agnostic pub/sub; [Topic]-on-Minimal-API-lambda currency item |
| messaging/dapr-workflow | 🟠 | **timeout overload throws, compensation branch dead** → orchestrator faults |
| messaging/masstransit-consumers | ✅ | accurate v8 consumer; correct retry/redelivery; exemplary license caveat |
| messaging/masstransit-sagas | ✅ | correct v8 saga state-machine; EF persistence; license-aware redirect |
| messaging/wolverine-messaging | ✅ | exemplary; the kit's preferred MIT, ISender-replacing default, positioned right |

## Security (8)
| Artifact | V | Reason |
|---|---|---|
| security/auth-jwt | 🔴 | `sub` round-trip throws every request (MapInboundClaims default) + 4 minor bugs |
| security/auth-policies | 🟡 | strong policy-based authz; latent claim-remap pitfall + token-bloat nuance |
| security/cors-configuration | ✅ | excellent CORS guide; correct order, wildcard+credentials rule; no defects |
| security/data-protection | 🟡 | accurate; encrypt-DB-fields pattern needs non-determinism caveat + dead code |
| security/entra-id-auth | 🟡 | accurate Microsoft.Identity.Web; lighter than peers; one API name to confirm |
| security/input-sanitization | ✅ | excellent XSS/hardening; allowlist, nonce CSP, magic-byte checks |
| security/openiddict-server | 🟠 | 'OpenIddict 10.x' version almost certainly wrong; thinner than cluster peers |
| security/passkeys-webauthn | 🟠 | login may not establish a session; endpoint referenced-but-undefined; new APIs to confirm |

## Testing (7)
| Artifact | V | Reason |
|---|---|---|
| testing/integration-testing | 🟠 | 'real DB' factory unconstructable (IClassFixture on factory); InMemory lead |
| testing/mutation-testing | ✅ | accurate Stryker.NET; real CI gate; one tiny formula nit |
| testing/performance-testing | 🟠 | stale `RuntimeMoniker.Net90`; benchmarks only Newtonsoft vs STJ default |
| testing/playwright-e2e | ✅ | current Playwright-for-.NET; role/label locators, web-first Expect, net10 install |
| testing/test-fixtures | 🟠 | undeclared `cancellationToken` (won't compile); fragile name `.Replace("Data","")` |
| testing/tunit-testing | 🟡 | honest MTP-native TUnit; 'pre-1.0' framing may be stale |
| testing/unit-testing | 🟡 | clear AAA/xUnit; aggregate-construction tension; commercial FluentAssertions default |

## Quality (6)
| Artifact | V | Reason |
|---|---|---|
| quality/analyzer-packaging | ✅ | accurate NuGet-packaging guide; matches kit csproj; minor RS1038-split gap |
| quality/architectural-fitness | 🟠 | commercial FluentAssertions as default with no caveat |
| quality/code-analysis | 🟡 | useful config guide; contradicts kit LF/UTF-8 convention; beta analyzer pins |
| quality/incremental-source-generator | ✅ | accurate IIncrementalGenerator; ForAttributeWithMetadataName, EquatableArray; no issues |
| quality/review-checklist | 🟡 | strong decision-guide; one stale Newtonsoft default; project-specific ES items |
| quality/roslyn-analyzer | 🟠 | analyzer+fix co-located → fails RS1038 under EnforceExtendedAnalyzerRules |

## Observability + Resilience (6)
| Artifact | V | Reason |
|---|---|---|
| observability/health-checks | ✅ | accurate health-checks; correct probe wiring, tag filtering, degradation |
| observability/opentelemetry | 🟡 | solid OTel tracing/metrics; EF-instrumentation currency note; thin eval |
| observability/serilog-structured | ✅ | accurate Serilog; two-stage bootstrap, LogContext, enricher; exemplary description |
| resilience/circuit-breaker | 🟠 | **health-check dead code (always Healthy); inverted strategy-order comments** |
| resilience/polly-resilience | 🟡 | strong Polly v8 pipeline; keyed-injection pattern needs API verification |
| resilience/retry-patterns | 🟡 | accurate retry (backoff+jitter, EF retry); same unverified keyed-injection |

## AI + Infra + Detection (7)
| Artifact | V | Reason |
|---|---|---|
| ai/extensions-ai-chat | 🟡 | excellent IChatClient pattern; OSS-default Ollama pkg + AsChatClient comment may be stale |
| ai/extensions-ai-embeddings | 🟡 | current VectorData API used correctly; OSS-default Ollama embedding pkg likely stale |
| infra/background-jobs | 🟡 | solid Hangfire/BackgroundService; Unix-only detect; missing description-boundary nuance |
| infra/email-notifications | 🟠 | **unencoded HTML injection**; two undeclared helpers; multi-provider promise unfulfilled |
| infra/feature-flags | 🟡 | comprehensive FeatureManagement; over soft length budget; Minimal-API filter type to verify |
| infra/file-storage | 🟡 | clean IFileStorage; SAS assumes shared-key; local GetPublicUrl returns a path; validation unshown |
| detection/smart-detect | ✅ | well-structured detection; correct decision table; MediatR/AutoMapper only as signals |

## Workflow (11)
| Artifact | V | Reason |
|---|---|---|
| workflow/code-review-workflow | ✅ | accurate two-pass review; clean checklist/severity; one CodeRabbit config key to verify |
| workflow/feature-tracking | 🟡 | useful status skill; two status vocabularies disagree on `approved` phase |
| workflow/git-worktree-isolation | 🟠 | v1 Python residue ('for tools like this one'); broken `/dai.go`; mixed command forms |
| workflow/multi-repo-workflow | 🟡 | strong cross-repo coordination; uses short-alias command form vs canonical |
| workflow/plan-artifacts | 🟡 | lean artifact catalog; description names artifacts it doesn't produce |
| workflow/plan-templates | ✅ | clean mode-specific plan.md templates; faint AutoMapper-'profiles' nudge |
| workflow/receiving-review-feedback | ✅ | sharp feedback-evaluation guidance; correct boundaries; dogfood-accurate checks |
| workflow/sdd-lifecycle | 🟡 | solid phase model; workspace diverges from shipped specify/status; Unix detect |
| workflow/session-management | 🟡 | clear checkpoint/handoff templates; filename divergence; Unix-only resume snippets |
| workflow/systematic-debugging | ✅ | excellent root-cause-first discipline; 4-phase model; accurate .NET examples |
| workflow/verification-gate | 🟡 | strong evidence-before-claims gate; one row cites Python `ruff` (wrong stack) |

## Microservice — command (7)
| Artifact | V | Reason |
|---|---|---|
| microservice/command/aggregate-design | 🟡 | accurate ES aggregate; Order omits private ctor its prose/canonical example require |
| microservice/command/aggregate-testing | 🟡 | correct `GetUninitializedObject`; undeclared `cancellationToken`; assertion recomputes 'now' |
| microservice/command/command-handler | 🟠 | raw MediatR uncaveated; one handler injects an undeclared `_unitOfWork` field |
| microservice/command/event-design | 🟡 | solid event hierarchy; one self-contradictory anti-pattern row |
| microservice/command/event-store | ✅ | well-reasoned EF TPH event-store; deserialize-settings asymmetry deserves a caveat |
| microservice/command/event-versioning | 🟡 | comprehensive schema-evolution; one example contradicts its 'default null' rule |
| microservice/command/outbox | 🟠 | undeclared `cancellationToken` (won't compile); `GeOutboxMessageAsync` typo propagated |

## Microservice — controlpanel (8)
| Artifact | V | Reason |
|---|---|---|
| microservice/controlpanel/blazor-component | 🔴 | DialogService not injected + `OpenEditDialog` undefined (2 compile breaks); flat gateway |
| microservice/controlpanel/blazor-hybrid | ✅ | accurate MAUI Blazor Hybrid; only nit is missing agent metadata |
| microservice/controlpanel/blazor-persistent-state | ✅ | precise `[PersistentState]`; correctly separates prerender handoff from reconnect |
| microservice/controlpanel/blazor-render-modes | ✅ | accurate render-mode decision guide; correct registration; exemplary boundary |
| microservice/controlpanel/gateway-facade | 🔴 | calls `DeleteAsync<T>` extension its own HttpExtensions never defines |
| microservice/controlpanel/mudblazor-patterns | 🟠 | async-void await inside sync `Switch`; old-API `IsInitiallyExpanded` |
| microservice/controlpanel/query-string-bindable | 🟡 | useful URL-sync filter; one prose/code mismatch + double-reload risk |
| microservice/controlpanel/response-result | ✅ | clean discriminated result (Switch + SwitchAsync); the consistency anchor |

## Microservice — cosmos + event-catalogue (5)
| Artifact | V | Reason |
|---|---|---|
| microservice/cosmos/cosmos-entity | 🟠 | partition-key level built from a value never persisted → PK mismatch |
| microservice/cosmos/cosmos-repository | 🟡 | accurate per-container repo; only small omissions |
| microservice/cosmos/partition-strategy | 🟡 | useful hierarchical-PK guide; headline point-read mislabeled (partial key) |
| microservice/cosmos/transactional-batch | 🔴 | single-op path drops Replace/Delete writes; own ETag example hits it |
| microservice/event-catalogue | 🟠 | `Activator.CreateInstance` throws on positional records; 58% code-dense → resources |

## Microservice — gateway + grpc (7)
| Artifact | V | Reason |
|---|---|---|
| microservice/gateway/endpoint-registration | ✅ | accurate gRPC client-factory setup; exemplary selector description |
| microservice/gateway/gateway-endpoint | ✅ | correct REST-to-gRPC bridge; strong path-scoped description |
| microservice/gateway/gateway-security | ✅ | accurate JWT + policy/requirement/handler; well-chosen anti-patterns |
| microservice/gateway/scalar-docs | ✅ | correct .NET 10 Scalar + OpenAPI wiring; OpenAPI v2 types current |
| microservice/grpc/interceptors | 🟡 | correct interceptor patterns; uses Newtonsoft vs STJ stack standard |
| microservice/grpc/service-definition | 🔴 | proto `total_cents` vs mapping `r.Total` → won't compile + magnitude bug |
| microservice/grpc/validation | 🟠 | rules reference stale `x.Total`/`x.UnitPrice` vs renamed proto fields |

## Microservice — processor + query (9)
| Artifact | V | Reason |
|---|---|---|
| microservice/processor/batch-processing | 🟡 | accurate batch-session; undeclared ItemChanged type; MediatR caveat |
| microservice/processor/event-routing | 🟡 | clean inline-dispatch; STJ anti-pattern claim; MediatR caveat |
| microservice/processor/grpc-client | 🟡 | solid AddGrpcClient; the RetryCallerService it defines is never used |
| microservice/processor/hosted-service | 🟠 | StartAsync/StopAsync fire-and-forget the processor Tasks (no graceful drain) |
| microservice/query/event-handler | 🟡 | accurate idempotent projections; MediatR caveat; awkward early-return block |
| microservice/query/listener-pattern | 🟠 | returns false for unknown subjects → poison loop; fire-and-forget lifecycle |
| microservice/query/query-entity | ✅ | strong read-model entity; private setters, event ctor, sequence-idempotency |
| microservice/query/query-handler | 🟡 | accurate handler/repo; only MediatR caveat missing |
| microservice/query/sequence-checking | ✅ | focused idempotency-guard; excellent decision matrix; genuine decomposition |

## Agents (15)
| Artifact | V | Reason |
|---|---|---|
| api-designer | 🟡 | well-scoped REST/gRPC; description omits Use-when/Do-NOT; boundaries name capabilities |
| command-architect | 🟡 | accurate ES CQRS agent; shared description/boundary gap; gRPC overlap with api-designer |
| controlpanel-architect | 🟡 | correct Blazor agent; shared description/boundary gap; dated 'WASM' phrasing |
| cosmos-architect | 🟡 | accurate Cosmos query agent; shared description/boundary gap |
| devops-engineer | 🟡 | solid CI/CD/K8s agent; shared gap + Azure DevOps over-claim with no skill |
| docs-engineer | 🟡 | thorough docs agent; shared description/boundary gap |
| dotnet-architect | 🟡 | correct generic-architecture lead; shared description/boundary gap |
| ef-specialist | 🟠 | surfaces commercial MediatR as default; shared description/boundary gap |
| gateway-architect | 🟠 | boundaries name no sibling; description lacks Use-when/Do-NOT |
| processor-architect | 🟠 | MediatR as default event router uncaveated; boundaries name no sibling |
| query-architect | 🟠 | delegates Cosmos but by hardcoded path; command-side/UI boundaries un-routed |
| reviewer | 🟡 | terminal review agent (correctly no delegation); description lacks Use-when/Do-NOT |
| test-engineer | 🟠 | single boundary names no sibling; description lacks standard clause |
| aspire-architect | ✅ | exemplary v2 agent — full description standard, routing-intents, named-sibling boundaries |
| ai-engineer | ✅ | exemplary v2 agent — description standard, provider-abstraction; one non-boundary bullet |

## Rules (21)
| Artifact | V | Reason |
|---|---|---|
| conventions/async-concurrency | 🟡 | strong async set; one clause wrongly forbids sharing HttpClient across threads |
| conventions/coding-style | 🟡 | solid style rule; `field` keyword mislabeled '.NET 14+' (ships C# 14 / .NET 10) |
| conventions/existing-projects | ✅ | clear detect-respect-extend; only nit is a non-action-verb-first description |
| conventions/security | ✅ | accurate security baseline; within length; cross-refs resolve |
| conventions/tool-calls | ✅ | sensible tool-agnostic guidance; correct and within length |
| domain/api-design | 🟡 | accurate REST conventions; one broken Related-Skills path; description boundary missing |
| domain/architecture | 🟠 | presents commercial MediatR as default CQRS dispatch vs the rule/profile |
| domain/configuration | 🟡 | strong Options-pattern rule; only gap is the description boundary clause |
| domain/data-access | 🟡 | accurate EF/Dapper rule; xrefs resolve; only description boundary missing |
| domain/error-handling | 🟡 | sound dual-mode error guidance; description boundary; `**/*.cs` broad but defensible |
| domain/localization | 🟡 | practical resource-localization; one broken Related-Skills path; boundary missing |
| domain/multi-repo | 🟡 | clear cross-repo conventions; broken Related-Skills path; noun-phrase description |
| domain/naming | 🟡 | comprehensive naming w/ placeholders; one broken Related-Skills path; boundary missing |
| domain/observability | 🟡 | accurate logging/health/tracing; only gap is the description boundary |
| domain/performance | 🟡 | solid anti-pattern list for .NET 10; path-scope + description need tightening |
| domain/testing | 🟠 | stale v1 Python residue (pytest/tmp_path + 'for both .NET and Python tests') |
| domain/testing-platform | ✅ | clean MTP runner rule; proper Use-when/Do-NOT; honest pre-1.0 flag |
| domain/mediator-abstraction | ✅ | correct & current; ISender-port mandate; exemplary description; only broad glob nit |
| domain/messaging-bus-selection | 🟡 | correct MassTransit-v9 framing; Wolverine 'safe default' license needs a currency check |
| domain/ai-integration | ✅ | accurate & current; Extensions.AI behind a port; only broad glob nit |
| domain/deterministic-enforcement | 🟠 | DAK0001 async-void drift (analyzer vs rule carve-out); wrong 'security' attribution |

## Profiles (12)
| Artifact | V | Reason |
|---|---|---|
| clean-arch | 🟡 | excellent layering constraints; Testing+Data-Access tail restates always-on rules |
| ddd | 🟡 | strong DDD constraints; generic Testing+Data-Access tail is the only weakness |
| generic | 🟠 | worst duplication — ~entire body restates universal rules |
| modular-monolith | 🟡 | genuinely module-specific; only the generic Testing+Data-Access tail restates rules |
| vsa | 🟠 | strong VSA constraints but TWO `## Data Access` sections + generic-rule duplication |
| hybrid | ✅ | strongest profile — almost entirely architecture-specific; correct sequence guard |
| command | 🟡 | coherent ES write-side profile; glob-overlap + unstated commercial-default context |
| controlpanel | 🟡 | rich Blazor+MudBlazor profile; JIT-defeating broad `src/**/*.cs` glob |
| gateway | ✅ | tight REST-to-gRPC profile; correctly narrow glob; no commercial-default issues |
| processor | 🟡 | internally consistent consumer profile; IMediator should reference the port; shared glob |
| query-cosmos | ✅ | accurate Cosmos read-model profile; correct lowercase id, ETag, hierarchical PK |
| query-sql | 🟡 | precise SQL read-model + idempotency; clearest MediatR default + unexplained AsNoTracking ban |

## Knowledge (16)
| Artifact | V | Reason |
|---|---|---|
| clean-architecture-patterns | 🟡 | accurate; MediatR-as-default + two stale skill cross-refs |
| concurrency-patterns | ✅ | strong concurrency reference; only placeholder description + tiny table redundancy |
| cosmos-patterns | ✅ | accurate Cosmos reference; only the placeholder description is sub-standard |
| cqrs-patterns | 🟠 | most MediatR-dense; non-compiling duplicate-type block; stale skill cross-refs |
| ddd-patterns | 🟡 | strong tactical DDD (dogfoods aggregate rules); stale xrefs, light IMediator, placeholder desc |
| dead-letter-reprocessing | ✅ | accurate paired-DLQ-processor pattern; placeholder description + light IMediator |
| deployment-patterns | ✅ | current deployment reference (.NET 10 Dockerfile, K8s, OIDC); only placeholder description |
| documentation-standards | ✅ | strong docs-standards reference; only placeholder description + one imprecise comment |
| event-sourcing-flow | 🟠 | false at-least-once; racy guard; raw MediatR/Newtonsoft vs the rules |
| event-versioning | 🟡 | solid versioning/upcasting; model shape contradicts event-sourcing-flow; MediatR/Newtonsoft |
| grpc-patterns | 🟡 | accurate gRPC reference; off-stack serializer/MediatR; weak description |
| modular-monolith-patterns | 🟡 | strong reference; MediatR caveat + two broken skill cross-refs + description |
| outbox-pattern | 🟠 | advertises crash-safe at-least-once but omits a recovery worker; racy guard; non-atomic loop |
| service-bus-patterns | 🟡 | accurate Service Bus reference; off-stack Newtonsoft/MediatR; missing dispose/lifetime note |
| testing-patterns | 🔴 | samples reference nonexistent members; mock shape wrong; stale `RuntimeMoniker.Net90` |
| vsa-patterns | 🟡 | clear VSA reference; MediatR caveat + two broken skill cross-refs + description |
