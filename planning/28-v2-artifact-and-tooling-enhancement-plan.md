# dotnet-ai-kit v2 — Artifact & Tooling Enhancement Plan

**Date:** 2026-05-31 · **Status:** PLAN — report-only, **no code changed.** Builds on the audit in [27](27-post-022-fidelity-and-defect-audit.md).
**Precedence:** This plan amended two locked decisions ([26](26-v2-build-plan-and-decisions.md) AR-5 opt-in resources; FR-A2 ".py default" scripts) — both **✅ ACCEPTED by the maintainer 2026-05-31** (see §3). Per maintainer request it also carries a **net-new expansion** workstream (§W7), so the plan now spans *deliver + right-size + dogfood + expand*.
**Method / sources (verified, latest):**
- **.NET 10 file-based apps** — [MS Learn, *File-based apps*](https://learn.microsoft.com/en-us/dotnet/core/sdk/file-based-apps) (doc updated 2026-05-21; "✔️ .NET 10 SDK and later") + the [`dotnet run app.cs` announcement](https://devblogs.microsoft.com/dotnet/announcing-dotnet-run-app/).
- **Skill best-practices** — the authoritative `anthropic-skills:skill-creator` SKILL.md + `references/schemas.md` (read this session).
- **Cross-tool capability matrix** — [20 §5](20-rewrite-strategy-net10.md) (dated 2026-05-30, one day old — cited, not re-researched).
- **Corpus state** — two evidence-backed scans this session (skills archetype/disclosure; agents/rules/profiles/MCP/LSP/hooks) + the [27](27-post-022-fidelity-and-defect-audit.md) audit.

---

## 1. Executive summary

The corpus is *structurally* complete and green, but it is **under-delivered**, not just under-resourced. Five findings drive this plan:

1. **Profiles are dead on arrival.** All 12 are authored, length-validated, and in the ArtifactGraph — yet **no host receives them by any channel** (no projector emits them; the PreToolUse hook loads only `.claude/rules/`; the Claude output-style *references* a profile that never ships). Wiring them is the single highest-value fix — and must be **architecture-gated** (read `project.yml` `architecture:`), not path-projected (they all glob `src/**/*.cs` and would multi-inject).
2. **Cursor ships a broken plugin manifest.** `.cursor-plugin/plugin.json` references 15 `./agents/*.md` that `CursorProjector` never writes. Drift-clean can't see it because the *referenced* files, not the manifest, are missing.
3. **The script-language question has a sharper answer than "Python vs C#."** Yes — a tool that *requires* the .NET runtime should ship **C# file-based scripts** (`dotnet run --file`), not Python (which isn't guaranteed present). But the deeper truth: **scripts should be rare and value-justified.** Only **2** genuine new script candidates exist (`event-catalogue`'s reflection generator, `changelog-gen`); the `add-*`/`*-generator` family is *judgment*-codegen (detect architecture → learn conventions → ask if ambiguous), not byte-deterministic, so they stay example-backed with **no** script.
4. **"Just an md file" is really progressive-disclosure debt, not thinness.** No skill exceeds 398 lines; the real issue is **code-density** — a dozen skills inline 60–78 % code that belongs in `references/<variant>.md` or `examples/`. Enriching by **archetype** (knowledge / codegen / workflow / decision-guide) serves "reach" without the blanket boilerplate AR-5 forbids.
5. **The fidelity story is one asymmetry, stated once:** **`additionalContext` JIT-injection (enforcement rules + arch-gated profiles) is Claude-only (hooks GA).** Codex gets static `AGENTS.md` (no glob/arch gating); Cursor/Copilot keep *path* gating via `.mdc globs` / `.instructions.md applyTo` but have no Stop-gate or prompt-hook. Every dynamic-delivery proposal below is tagged against this.

**Scope (updated 2026-05-31):** AM-1 and AM-2 are **accepted**, and this plan now also carries a **net-new expansion** workstream (§W7) — genuinely-new, GA-verified, deduped artifacts and tools researched against the 2026-current .NET + AI-tooling ecosystem — alongside the deliver/right-size work.

---

## 2. Guiding principles (grounded in the research)

| # | Principle | Source |
|---|---|---|
| P1 | **Progressive disclosure.** Lean `SKILL.md` (<500 lines, *and* low code-density); multi-variant/deep content → `references/<variant>.md` (loaded on demand); files used in output → `assets/`; deterministic ops → `scripts/` (execute without loading). For >300-line references add a TOC. | skill-creator |
| P2 | **Enrich by archetype, value-justified — never blanket.** Bundle a script only when the model would otherwise re-derive the same helper every run; add an example only where it pins a generated/illustrated shape; add evals only for confusable clusters. | skill-creator + AR-5 |
| P3 | **Dogfood .NET.** Skill scripts are C# file-based apps, **BCL-only / zero `#:package`** (preserve no-network), invoked `dotnet run --file` (see §4 caveats). | the kit's own thesis + MS Learn |
| P4 | **Every change is gated by "projects to which tools, at what maturity."** Each proposal carries tools + GA/Preview/Unsupported + projection mechanism (§6 matrix). | 20 §5 |
| P5 | **One delivery per constraint.** A constraint lives in exactly one of {universal rule, arch profile, Roslyn analyzer}; the others *reference* it. Kills the rule↔profile↔analyzer triple-statement drift and the double-injection that wiring profiles would otherwise cause. | scan finding |
| P6 | **Descriptions are the selector.** All "use when" lives in the description, slightly "pushy" against undertriggering; gated by the confusion-matrix eval. | skill-creator |

---

## 3. Locked-decision amendments — ✅ ACCEPTED (2026-05-31)

Both amendments are **adopted** (maintainer sign-off 2026-05-31). They govern W2 (scripts) and W3/W7 (resources) below.

- **AM-1 — amend AR-5 from "opt-in minimal" → "enrich by archetype."** AR-5 (and 022's clarification "do NOT add resource dirs to all 181 skills") was right to forbid *blanket* resources. AM-1 keeps that ban but **broadens the firm subset** to: (a) the 2 deterministic script candidates, (b) compilable `examples/` for the heavy template-code microservice band, (c) `references/` relocation for the ~12 code-dense skills, (d) `evals/` for the high-mis-trigger clusters in §W6. Rationale: the user's "skills are just md files" is a legitimate *reach* gap; archetype-targeting closes it without re-introducing boilerplate.
- **AM-2 — amend FR-A2 script default from `.py` → .NET file-based C#.** FR-A2 chose ".py default (stdlib, cross-OS)." But the kit's hooks already *require* the global `dotnet-ai` .NET tool, and skill scripts run where the user is building .NET — so **.NET is guaranteed present and Python is not.** Author scripts as C# file-based apps (`.cs`), keep optional `.ps1`/`.sh` siblings per NFR-3 where a shell one-liner is genuinely simpler. (Execution is effectively Claude-surface — see §4 — so this is not a multi-tool break.)

---

## 4. W2 — Scripts: dogfood .NET, and right-size the script surface

**The .NET file-based facts that constrain the design (verified):**
- ✔️ **GA** in .NET 10 SDK (the pinned 10.0.300; `#:include` is 10.0.300+). Invoke `dotnet run --file script.cs` (or `dotnet script.cs`).
- ⚠️ **No-network rule:** `#:package` triggers a NuGet **restore (network)**. Scripts MUST be **BCL-only with zero `#:package`** to preserve NFR-1. ✅ All 4 current Python scripts are stdlib-only, so the BCL-only port is feasible 1:1.
- ⚠️ **Cold-start:** file-based apps **compile on first run** (cached in temp). Acceptable for one-shot scaffolders; note it in the trust prompt.
- ⚠️ **Project-cone gotcha:** inside a dir containing a `.csproj`, `dotnet run file.cs` runs the **project** and passes the file as an arg — skill scripts run in the user's repo, so they **must** use `dotnet run --file`. Parent `Directory.Build.props`/`global.json` also leak into file-based apps ("avoid project-file cones") — keep scripts self-contained and document the `--file` invocation.
- ✅ Shebang `#!/usr/bin/env -S dotnet --`, **LF + no BOM** (already the kit's discipline; matches the deterministic-LF generator).
- ℹ️ **Execution is Claude-scoped.** `SkillResourceProjection` copies scripts into *all four* host skill dirs, but only Claude executes skill `scripts/`; Codex/Cursor receive `SKILL.md` (+ Codex name/description), so a bundled script there is an inert file a human may run. ⇒ the C#-vs-Python choice is a Claude-surface + human-ergonomics decision, **not** a cross-tool break.

**Work items:**
- **W2.1 (AM-2)** Port the 4 Python scaffolders → C# file-based, BCL-only: `constitution/scaffold_constitution`, `checklist/generate_checklist`, `fix/repro_test`, `release/bump_version`. Keep behavior identical; add the `dotnet run --file` usage note + shebang. Update `ScriptTrust` interpreter-from-extension to recognize `.cs`.
- **W2.2** Add the **2 genuine new C# scripts** (the first no-network `dotnet run --file` dogfood):
  - `microservice/event-catalogue/scripts/` — extract the `EventCatalogueGenerator.GenerateFromAssembly` already inlined in the body (reflection over `IEventData` → `events.json`). **Pairs with the §W3 fix of the broken `Activator` sample** (planning/27 A1) — the script becomes the corrected, tested generator.
  - `docs/changelog-gen/scripts/` — `git log` (list-arg subprocess) → group by Conventional-Commit type → Keep-a-Changelog render.
- **W2.3 (scope guard)** Do **NOT** add scripts to `add-*` / `command-generator` / `query-generator` — they are judgment-codegen (`add-crud` literally "detect architecture … learn conventions … if ambiguous: ask"). Their value is the example, not a transform.
- Tools: scripts execute on **Claude (GA)**; inert-but-copied on Codex/Cursor/Copilot. Trust model (`ScriptTrust`, consent-before-run) already exists (022 FR-022-05).

---

## 5. Workstreams W1, W3–W7

### W1 — Fix dead/broken delivery (HIGHEST VALUE)

| ID | Problem (evidence) | Proposal | Tools · maturity |
|---|---|---|---|
| **W1.1** | **Profiles reach no tool.** No projector references `corpus.Profiles`; `ClaudeHostAdapter` writes rules not profiles; `HookCommand.LoadRules` loads only `.claude/rules/`; the output-style references a profile that never ships. | Wire **architecture-gated** delivery: read `project.yml` `architecture:` → select the *single* matching profile. Claude: inject via PreToolUse `additionalContext` (extend `PreToolUseHookService`/`LoadRules` to load `.claude/profiles/<arch>.md`) and name it in the output-style. Codex: static into `AGENTS.md` (loses arch-gating). Cursor: `.mdc` + profile globs. Copilot: `.instructions.md applyTo`. **Do not path-project** (multi-inject). | Claude **GA** (JIT); Codex static; Cursor/Copilot **GA** (path only) |
| **W1.2** | **Cursor dangling agents.** `.cursor-plugin/plugin.json` lists 15 `./agents/*.md`; `CursorProjector` emits none → `build/cursor/agents/` absent. | Add an agent-projection loop to `CursorProjector` emitting `cursor/agents/<name>.md` (Cursor `.md` frontmatter, nesting/async GA 2.5), **or** drop the `agents` array. Add a manifest-reference-resolves test so this can't recur. | Cursor **GA** (shipping broken) |
| **W1.3** | **MCP/LSP not in the author-once pipeline.** `.mcp.json`/`.lsp.json` are repo-root dev config, referenced by no projector/check; absent from `build/`. LSP is wired into no agent. | Emit `.mcp.json` into each `build/<host>/` from one descriptor (Codex also needs `[mcp_servers]` in `config.toml`; Cursor `${env:}`). Emit `.lsp.json` into `build/claude/` (+`build/copilot/` Preview) and **wire LSP as agent navigation** — instruct `reviewer`/`dotnet-architect`/`ef-specialist` to prefer `goToDefinition`/`findReferences` over text search. | MCP **GA ×4**; LSP **Claude GA**, **Copilot Preview**, Codex/Cursor agent-facing **Unsupported** |

### W3 — Skill enrichment by archetype (progressive disclosure) · 🔏 AM-1

Corpus is ~110 KNOWLEDGE · ~52 WORKFLOW · ~7 DECISION-GUIDE · ~6 true CODEGEN. No length-ceiling breach; **bloat = code-density.**

- **W3.1 Relocate code-dense bodies** (top candidates, code-share in parens): multi-variant → `references/<variant>.md` — `architecture/multi-tenancy` (67 %, 3 isolation patterns), `core/fluent-validation` (60 %), `infra/feature-flags` (63 %), `security/input-sanitization` (60 %), `api/caching-strategies` (61 %), `api/signalr-realtime` (61 %); single large impl → `examples/` — `gateway/scalar-docs` (75 %), `processor/batch-processing` (78 %), `command/aggregate-testing` (75 %), `query/listener-pattern` (74 %), `command/outbox` (69 %). **Leave lean-but-long alone:** `core/design-patterns` (34 % code), `api/grpc-design` (45 %).
- **W3.2 Compilable examples** for the heavy template-code microservice band (`event-store`, `query-entity`, `aggregate-design`, `event-design`, `command-handler`, `query-handler`, `event-handler`, `outbox`, `listener-pattern`) + `cqrs/command-generator`/`query-generator` — doubles as the W3.1 relocation target. Roslyn-parse-gate them like the `add-*` examples (planning/26 FR-022-02 ceiling).
- **W3.3 Deepen genuinely thin skills** (content, not resources): `ai/extensions-ai-chat`/`extensions-ai-embeddings` (54 lines) and `blazor-hybrid` (58) are shallow vs their cluster peers (180–280).

### W4 — Agents optimization

- **W4.1** Backfill **13/15** descriptions to standard (only `aspire-architect`/`ai-engineer` conform) — lift the routing/boundary content already in the body into the description. Projects verbatim to all 4 tools.
- **W4.2** Name **sibling agents** in each `## Boundaries` line ("…does not handle Cosmos — **use cosmos-architect**"); only `query-architect` does today. Reference agents **by name, not path** (`query-architect.md:22` uses a path that won't survive projection).
- **W4.3** Use unused Claude subagent fields: emit a restricted `tools:` for read-only agents (`reviewer`, `docs-engineer`) and pin a cheaper `model:` — a concrete token/safety win (Claude GA). Restore the `## Routing` block to the two newest agents.
- **W4.4** Copilot `CopilotProjector` **drops the `skills:` preload** — add it when `.agent.md` skill/tool frontmatter GAs (Preview gap; track).

### W5 — Rules + profiles coherence

- **W5.1** Narrow the **6** over-broad `**/*.cs` globs to real scopes: `mediator-abstraction`/`messaging-bus-selection` → DI/composition (`**/Program.cs,**/*Extensions.cs,**/DependencyInjection/**`); `ai-integration` → AI namespaces; `error-handling`/`performance` → handler/repository/endpoint globs; `deterministic-enforcement` → make universal or doc-only (it's a meta-registry). Copy the well-scoped `api-design`/`data-access` exemplars.
- **W5.2 (P5)** Collapse rule↔profile↔analyzer duplication: `generic.md` restates `coding-style`/`async-concurrency`/`naming`/`error-handling`/`data-access` near-verbatim; `clean-arch` ≈ `data-access`+`performance`. Make profiles carry only **architecture-specific** constraints and *reference* the generic rules — prerequisite for W1.1 (else wiring profiles double-injects).
- **W5.3** Grow the analyzer set behind `deterministic-enforcement` (today only DAK0001 `async void`, DAK0004 aggregate setters): add Cosmos lowercase-`id`, DbContext-Scoped lifetime, parameterized-SQL, `DateTime.Now`→`TimeProvider`; **populate the dead `analyzer-backed-constraints`** profile field and fold it into the registry (FR-F6).
- **W5.4** Backfill ~11 legacy rule descriptions to standard. Trim the Python half of `rules/domain/testing.md` (v1 residue). Consider trimming Codex `AGENTS.md` (952 always-on lines) to universal + a pointer.

### W6 — Evals / triggering maturity (FR-E6 / AR-6)

- Author `evals/cases.jsonl` for the **high-mis-trigger clusters with no evals today**: auth 5-way (`auth-jwt`/`auth-policies`/`entra-id-auth`/`openiddict-server`/`passkeys-webauthn`), blazor 5-way, aspire 4-way, gateway 4-way, messaging-bus 3-way, dapr 3-way, EF/data. Run them through the existing confusion-matrix gate (correct fires, siblings silent; SC-D). *(Existing evals: advisor, command-generator, opentelemetry, polly-resilience, integration-testing.)*
- Full **≥20-queries/skill live-LLM** eval stays deferred (AR-6) — these are deterministic lexical/top-k cases.

### W7 — Net-new expansion (artifacts + tools) · per maintainer request

Researched against the 2026-current .NET + AI-tooling ecosystem (two web-grounded passes), **deduped against the existing 182 skills / 15 agents**, GA-verified with dated sources. Owning agents were **verified from `agent:` frontmatter** (security→`api-designer`; messaging→`processor-architect`; devops/IaC→`devops-engineer`; perf-testing→`test-engineer`) — which is why only **2** new agents are justified, not more. Every new artifact ships to the description standard (incl. the "Do NOT use… (use X)" sibling-scope) and follows the W3/AM-1 archetype-enrichment (codegen-ish skills get a C# `examples/`; reference-heavy ones get `references/`), so additions don't degrade selector precision.

**W7.1 — New skills, STRONG (GA, author now):**

| Proposed skill | What it is | Maturity (dated source) | Owner |
|---|---|---|---|
| `ai/mcp-server` | Author a .NET **MCP server** — `ModelContextProtocol` SDK, `[McpServerTool]`, stdio + ASP.NET (HTTP) hosting, `dotnet new mcpserver`, publish to NuGet | **GA** — SDK v1.0 (2026-03-05), 1.3.0 (2026-05-08); maintained w/ Microsoft | **mcp-engineer** 🆕 |
| `ai/extensions-ai-evaluation` | Eval LLM output in tests — `Relevance`/`Groundedness`/`Completeness` + agent evaluators (`ToolCallAccuracy`/`TaskAdherence`), `dotnet aieval` | **GA** (Quality 10.5.0 / Console 10.6.0; Learn upd 2026-05-13) — `.NLP` still preview; `.Safety` needs Foundry | `ai-engineer` |
| `ai/agent-framework` | Build agentic .NET apps + graph workflows — `Microsoft.Agents.AI` (the SK + AutoGen successor), MCP clients, multi-agent orchestration | **GA 1.0** (2026-04-03) — ~8 wks old → **pin versions**; some `.Foundry` pkgs prerelease | **mcp-engineer** 🆕 |
| `api/yarp-reverse-proxy` | Config-driven reverse proxy / gateway — routes, clusters, transforms, LB, health checks (the mainstream .NET gateway) | **GA** — Yarp.ReverseProxy 2.3.0; first-party in ASP.NET Core 10 docs | `gateway-architect` |
| `data/ef-vector-search` | EF Core 10 similarity search — `SqlVector<float>`, `EF.Functions.VectorDistance`, hybrid (RRF) | **GA for exact distance on SQL Server 2025+**; approximate (`VECTOR_SEARCH`/indexes) **experimental** (Learn upd 2026-04-14) | `ef-specialist` |
| `data/ef-advanced-mapping` | EF Core 10 complex types → SQL `json` columns + `ExecuteUpdate/Delete` bulk ops | **GA** (EF Core 10 "What's New") | `ef-specialist` |
| `performance/runtime-diagnostics` | Production-safe profiling — `dotnet-counters/-trace/-gcdump/-dump`, `dotnet-monitor`, allocation analysis | **GA**, in-box global tools | **performance-engineer** 🆕 |
| `security/supply-chain` | `NuGetAudit` (transitive) + `sbom-tool` (SPDX) + signed/audited NuGet | **GA + .NET-10-new:** transitive audit is the **default** for net10 (breaking change, Preview 3, Learn upd 2025-11-11) | `devops-engineer` |
| `security/secrets-management` | Key Vault config provider + `user-secrets` + managed identity (`DefaultAzureCredential`) | **GA** (Azure SDK stable; today only one line in `core/configuration`) | `api-designer` |
| `devops/container-hardening` | Chiseled/distroless, rootless/non-root, AOT image variants, SBOM-in-image | **GA** — .NET 10 adds Chisel manifest + Native-AOT image variants, non-root by default | `devops-engineer` |
| `devops/iac-bicep-azd` | Declarative Azure (Bicep) + `azd up` provision/deploy lifecycle (vs the kit's imperative `az`) | **GA** — azd v1.22.x (Nov 2025, +Aspire 13 / ACA GA) | `devops-engineer` |

**W7.2 — New skills, MEDIUM (author if cheap, else fold):**

| Proposed skill | What it is | Maturity | Owner / note |
|---|---|---|---|
| `core/file-based-apps` | `dotnet run app.cs` scripting — `#:package`/`#:sdk`, `dotnet project convert` | **GA** (.NET 10) | `dotnet-architect` — *documents the very mechanism AM-2 adopts for skill scripts* |
| `messaging/kafka-confluent` | Native `Confluent.Kafka` producer/consumer (KIP-848 rebalance) — distinct from Dapr's Kafka *component* | **GA** (2.14.0) | `processor-architect` |
| `messaging/event-hubs` | Azure Event Hubs streaming + `EventProcessorClient` checkpointing — distinct from Service Bus brokered messaging | **GA** (Azure.Messaging.EventHubs 5.12.2) | `processor-architect` |
| `api/webhooks` | Receive/send webhooks — HMAC verify, idempotency keys, retry/DLQ | **Pattern** skill (first-party `aspnet/WebHooks` archived 2018 — build on Minimal API + resilience) | `api-designer` |
| `devops/native-aot-publishing` | AOT/trim-safe minimal-API services — `CreateSlimBuilder`, STJ source-gen | **GA, scoped** — NOT for EF apps; cross-ref `minimal-api-validation` | `devops-engineer` — *or fold AOT-awareness into runtime-diagnostics + container-hardening* |

**W7.3 — New agents (2, the only ownership gaps):**
- **`mcp-engineer`** 🆕 — owns `mcp-server` + `agent-framework`; keeps `ai-engineer` on Extensions.AI chat/embeddings/eval.
- **`performance-engineer`** 🆕 — owns the `performance` rule + `performance-testing` + `runtime-diagnostics` + STJ-source-gen/trimming/`Span` perf. (Clearest gap: `performance-testing` is `test-engineer`'s *measurement*; production diagnostics has no owner.) *A `security-engineer` agent is **rejected** — all 8 security skills are already owned by `api-designer`.*

**W7.4 — New "tools" / roadmap (engine work, decision-deferred — not artifacts):**
- **Ship the kit's own MCP server (a 5th projection surface).** Expose the skill/knowledge/rule corpus to *any* MCP client (search/fetch tools) — the kit becomes consumable beyond the 4 file-projected tools. High strategic value, **enabled by the now-GA C# MCP SDK**, but it's a new `IHostProjector`/server + CLI surface, not an artifact → roadmap, pending sign-off.
- **`event-catalogue` MCP** — a live/queryable surface over the existing `events.json` (vs today's static doc); lands only if the server infra above exists.
- **`audit` CLI verb** — `NuGetAudit` + `sbom-tool` + secret-scan, extending `check`; pairs with `security/supply-chain`. **Park** (don't build now).

**W7.5 — Rejected (explicit, so the boundary is a stated choice):** standalone RAG/vector skill (covered by `extensions-ai-embeddings`) · standalone **Semantic Kernel** (superseded by Agent Framework, per Microsoft) · C# 14 "extension-members" skill (fold into `modern-csharp` as an update) · **OData** (niche; redundant vs REST + GraphQL + gRPC) · standalone `System.Threading.Channels` skill (already in `core/async-patterns`) · GitHub Actions "advanced/OIDC" (already in `devops/github-actions`) · **`security-engineer`** agent (security already owned by `api-designer`) · LSP-toolset-as-skill (no grounding for an authoring kit; LSP *delivery* is W1.3).

**Net effect:** +11 strong (+ up to 5 medium) skills → ~193–198 skills · +2 agents → 17 · optional paired rule(s) for secrets/supply-chain · the 3 roadmap "tools". All GA-verified, deduped, description-standard-gated. (Sources for every maturity claim are in the two research passes that produced this section; the highest-recency items — Agent Framework, EF-10 approximate vector search — carry explicit caveats above.)

---

## 6. Multi-tool fidelity matrix (every proposal is gated by this)

| Capability | Claude | Codex | Cursor | Copilot | Kit projection status |
|---|---|---|---|---|---|
| **JIT `additionalContext` injection** (rules/profiles on edit) | **GA** | Unsupported | — | — | PreToolUse hook (Claude only) |
| **Path/glob-scoped rules** | GA (`.claude/rules paths:`) | **Unsupported** (no globs → `AGENTS.md` global) | GA (`.mdc globs`) | GA (`applyTo`) | ✅ all hosts; Codex gap acknowledged in-code |
| **Arch profiles** | GA (hook/output-style) | static only | `.mdc` | `.instructions.md` | ❌ **wired to none today** → W1.1 |
| **Stop completion gate** | **GA** | Unsupported | Unsupported | Unsupported | ✅ ClaudeHooksWriter |
| **PreToolUse deny** | GA (~40 events) | command-only (10) | `beforeShellExecution`/`afterFileEdit` | 8 events (Preview) | ✅ Claude; fallbacks = analyzer+CI |
| **Output styles** | **GA** | Unsupported | Unsupported | ≈`copilot-instructions` | ✅ ClaudeOutputStyleWriter (AR-10) |
| **MCP** | GA | GA | GA | GA | ❌ **not projected** (root dev config) → W1.3 |
| **LSP (agent-facing)** | **GA** | Unsupported | Unsupported | Preview | ❌ not projected, not wired → W1.3 |
| **Skill `scripts/` (executed)** | **GA** | declared, not run | declared, not run | declared | ✅ copied ×4; executed by Claude → W2 |
| **Subagent `skills:`/`tools:`/`model:`** | GA | `.toml skills` | `.md` (GA 2.5) | `.agent.md` (Preview) | `tools:`/`model:` unused; Copilot drops `skills:` → W4 |
| **Agent files** | GA | GA | **GA (broken — none emitted)** | Preview | ❌ Cursor dangling → W1.2 |

---

## 7. Sequencing & acceptance

Each lands as an independently-testable green increment (build `-warnaserror` 0/0 · `dotnet test` · `dotnet format` · `generate --check` drift-clean · `claude plugin validate --strict`). Re-accept Verify goldens whenever projection shape changes.

1. **W1.2 + W1.1** — Cursor agents (shipping-broken first) → profiles arch-gating. Highest user-visible value; W1.1 also un-dangles the output-style.
2. **W5.1 + W5.2** — narrow globs + de-duplicate rules/profiles (prerequisite for W1.1's double-injection safety).
3. **W2** (🔏 AM-2) — port 4 scripts → C#, add the 2 deterministic ones; fix the `event-catalogue` sample (planning/27 A1) via the extracted generator.
4. **W1.3** — project MCP/LSP per host + wire LSP into agents.
5. **W3** (🔏 AM-1) — relocate code-dense bodies → references/examples; deepen thin skills.
6. **W4** — agent descriptions + sibling-naming + Claude `tools:`/`model:`.
7. **W5.3/W5.4 + W6** — grow analyzers + registry; backfill descriptions; author cluster evals.
8. **W7** — net-new expansion: the STRONG skills (YARP · EF-10 vector/advanced-mapping · supply-chain · secrets · runtime-diagnostics · mcp-server · ai-evaluation · agent-framework · container-hardening · iac-bicep-azd) + the 2 new agents. **Additive** — runs independently of W1–W6. The W7.4 roadmap tools (kit's own MCP server, `audit` verb) are decided separately.

**Acceptance additions** beyond the standing gates: a **Cursor-manifest-references-resolve** test (W1.2); a **profile-delivered** acceptance test (after `init`, the arch profile reaches the project) (W1.1); the **confusion matrix** extended to the new clusters (W6); each ported C# script proven **no-network + `dotnet run --file`** runnable (W2).

---

## 8. Out of scope / still deferred

Native-AOT packaging (BD-3) · full ≥20-queries/skill **live-LLM** eval (AR-6 — clusters-first only) · live in-session hook firing (interactive-only) · Codex/Cursor plugin-**load** parity (different discovery model) · re-litigating `planning/26` beyond AM-1/AM-2.

---

## 9. Open decisions for the maintainer

1. ✅ **AM-1 / AM-2 accepted** (2026-05-31) — resolved, no longer open.
2. **W7 expansion scope** — confirm the 2 new agents (`mcp-engineer`, `performance-engineer`); which of the 5 MEDIUM skills (W7.2) to author now vs defer; and whether to pursue the **kit's-own-MCP-server** 5th surface (W7.4) as a roadmap item or park it with the `audit` verb.
3. **Profiles delivery channel** (W1.1): PreToolUse `additionalContext` *and/or* fold into the output-style? Both are Claude-GA; the hook gives true JIT, the output-style is always-on.
4. **Cursor agents** (W1.2): emit `cursor/agents/*.md`, or drop the `agents` array from the Cursor manifest? (Emit is the higher-fidelity choice if Cursor subagents are in scope.)
5. **Analyzer growth** (W5.3): how far to push deterministic enforcement (which mechanical constraints earn a DAK rule) vs. leave advisory.
6. **Codex `AGENTS.md` size** (W5.4): trim 952 always-on lines to universal + pointer, accepting reduced Codex guidance, or keep full fidelity at idle-token cost?

---

*Plan only; nothing built. The throughline: the engine is sound — the value is in **delivering** what's already authored (profiles, MCP/LSP), **right-sizing** what's bundled (C# scripts, archetype resources, disclosure), **dogfooding** the .NET runtime the tool already requires, and **expanding** (W7) into the GA-verified 2026 gaps — MCP-server authoring, EF-10 vector search, supply-chain, runtime diagnostics.*
