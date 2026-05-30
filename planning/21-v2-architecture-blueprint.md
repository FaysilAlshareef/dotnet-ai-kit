# dotnet-ai-kit v2 — Full-Rewrite Architecture Blueprint (.NET 10)

**Date:** 2026-05-30
**Author:** lead-architect synthesis for Faysil Alshareef
**Status:** design blueprint — the spec for the v2 rewrite
**Decision baseline:** The maintainer has chosen a **full rewrite**: re-implement the CLI in **.NET 10** and re-author **every artifact** (skills, agents, rules, commands, profiles), with **richer artifacts** (bundled scripts/examples), **intelligent invocation**, **clean multi-tool support**, and **rebuild + expand** coverage.

**Inputs (all grounded):** the v1 codebase scan + [planning/20-rewrite-strategy-net10.md](20-rewrite-strategy-net10.md); five dated research tracks (auto-triggering · routing · bundled-resource model · expansion domains · .NET 10 clean architecture); and a verification pass on every recommendation-driving external claim. Items not confirmed against a primary source are marked **[ungrounded]**.

> **The one rule that governs this rewrite:** *Full rewrite, yes — but the current repo and its 717 tests are the **reference spec**, not the starting code.* We re-author from a clean model; we mine v1 for the behavioral contracts and bugs already fixed (the rule-delivery gap, manifest invariants, no-network rule, token budgets) so v2 leapfrogs instead of re-walking the same potholes.

---

## 0. The v2 thesis in one picture

```
            ┌─────────────────────── ONE SOURCE OF TRUTH ───────────────────────┐
            │  artifacts/  — authored once, tool-agnostic                         │
            │    skills/<name>/   SKILL.md + scripts/ + examples/ + references/   │
            │                     + assets/ + evals/      ← THE ATOMIC UNIT       │
            │    agents/<name>.md   (frontmatter + body; references skills)       │
            │    rules/<name>.md    (body + paths: + scope:)                      │
            │    profiles/<name>.md (architecture hard-constraints)               │
            │    fragments/         (shared command/skill stanzas, authored once) │
            │    graph.json         (generated: owns / relates / triggers edges)  │
            └───────────────────────────────┬────────────────────────────────────┘
                                             │  PROJECTION ENGINE (CI-gated, git diff --exit-code)
        ┌────────────────────┬───────────────┼───────────────┬────────────────────┐
        ▼                    ▼               ▼               ▼                     ▼
   Claude Code           Codex CLI         Cursor       GitHub Copilot      Roslyn analyzer
   .claude-plugin/       .codex/agents     .cursor-     .github/ +          NuGet
   (also serves          *.toml +          plugin/      .claude-plugin/     Dotnet.Ai.Kit
    Copilot CLI +        AGENTS.md         *.mdc        auto-detect          .Analyzers
    VS Code)                                            (cloud = render)     (deterministic
                                                                              enforcement)
```

**Three convergent ideas drive everything below:**

1. **The skill is the atomic unit.** It is the only artifact type every tool lets bundle resources. Agents, commands, and rules become *thin per-tool wrappers that reference skills.* This dissolves the "give every artifact type its own resource folder" idea (no tool supports it) into something cleaner that every tool *does* support.
2. **Intelligence = description engineering + a light disambiguator, not a heavy router.** Skills ≠ tools; the scary router statistics are about MCP tools. For 124 skills the problem is *selection precision among overlapping descriptions*, solved by a strict description standard + the artifact graph + an opt-in `/dai.do` disambiguator.
3. **One source projected per host, CI-gated.** This single change dissolves the entire class of v1 pain (5-commit manifest churn, 17/27 duplicated command stanzas, the agents `source→generated` drift, the fixture leak).

---

## 1. Design tenets (the constitution v2 obeys)

| # | Tenet | Why (grounded) |
|---|---|---|
| T1 | **Single source of truth → projection per host, CI-gated** | v1's mess is drift between 5 agent dirs + 4 manifest copies. `git diff --exit-code` on the generator makes drift structurally impossible. |
| T2 | **Skill = atomic resource-bearing unit; agents/commands/rules reference it** | Only skills bundle `scripts/`/`references/`/`assets/` across all four tools (Agent Skills open standard). |
| T3 | **Descriptions are the trigger; gate them with evals** | The `description` is loaded into the model's context and fuzzy-matched. Triggering becomes a CI-gated metric, not a vibe. |
| T4 | **Two enforcement layers that mirror each other** | Markdown rules *guide* (probabilistic); a Roslyn analyzer NuGet *enforces* (deterministic). This is the cure for the `issues/rule-enforcement-gap/` bug. |
| T5 | **Portable core frontmatter; per-host extensions gated at projection** | `name`/`description`/`license`/`compatibility`/`metadata` are the open standard; `disable-model-invocation`/`paths`/skill-`hooks` are Claude-specific. |
| T6 | **Preserve the won invariants** | No-network (A-011), token budgets, the 8-exit-code contract (FR-031), ≤18-file footprint (SC-001) — re-expressed as the .NET acceptance suite. |
| T7 | **AOT-clean by construction** | Reflection-free serialization + validation everywhere, so the tool ships as a fast Native-AOT `dotnet tool`. |
| T8 | **No hard dependency on preview features** | Agent teams + dynamic workflows are preview/experimental; ship subagent *definitions*, let runtime orchestration compose them opt-in. |

---

## 2. The artifact model (the heart of the rewrite)

### 2.1 The unified source tree

```
artifacts/                              # ONE authored source, tool-agnostic
  skills/<skill-name>/
    SKILL.md                            # ≤500 lines; standard-only frontmatter
    scripts/                            # executable helpers the AI runs
      do-thing.py                       #   PORTABLE DEFAULT (stdlib, cross-OS)
      do-thing.ps1   do-thing.sh        #   optional per-OS siblings
    examples/
      MinimalSample/ (.csproj+Program.cs)   # compilable C# example, not inline
    references/
      REFERENCE.md  <domain>.md         # Tier-3, loaded on demand
    assets/
      schema.json  template.cs.tmpl  appsettings.sample.json  diagram.svg
    evals/
      cases.jsonl  expected/            # triggering + golden-output fixtures
  agents/<name>.md                      # frontmatter + body; `skills:` reference list
  rules/<name>.md                       # body + paths: glob + scope: universal|domain
  profiles/<name>.md                    # architecture hard-constraints (path-scoped)
  fragments/<name>.md                   # shared stanzas (FR-012, dry-run) authored once
```

**Why this shape (grounded in the bundled-resource research, fetched 2026-05-30):** the Agent Skills open standard (`SKILL.md` + `scripts/`/`references/`/`assets/`, 3-level progressive disclosure, ≤500-line body) is now implemented by Claude Code, Codex, Cursor, and Copilot. Agents/commands across all four tools **reference** skills (Claude `skills:` frontmatter, Codex `skills.config`, Copilot/Cursor markdown links) and **cannot** bundle their own resource dirs. So resources live in skills; everything else points at them.

### 2.2 Format decisions (the "what files / what format" question, answered)

| Resource | Format | Rationale |
|---|---|---|
| Executable script | **`.py` (stdlib)** default; optional `.ps1`/`.sh` siblings | Only format that runs on Win/macOS/Linux *and* is "common" to every tool; `.sh` fails on bare Windows, `.ps1` is Windows-only. |
| Example code | **compilable C# mini-project** (`.csproj`+`Program.cs`) in `examples/` | The .NET audience builds them; superior to `.csx` or inline. |
| Reference docs | **`.md`** in `references/` | Spec-canonical Tier-3, loaded on demand. |
| Schemas | **`.json`** (JSON Schema) in `assets/` | Validate-able, universal. |
| Templates | source-ext `.tmpl` in `assets/` | Static fill-in templates. |
| Eval/golden fixtures | `.jsonl` + `expected/` in `evals/` | Drives the triggering harness (§4) and Verify golden tests (§10). |

### 2.3 The artifact graph (what makes invocation "intelligent")

v1 already carries the **edges of a graph in embryo** — formalize them into a generated `graph.json`:

| Edge | Source in v1 | v2 use |
|---|---|---|
| skill **owned-by** agent | `metadata.agent: command-architect` ([aggregate-design/SKILL.md:6](skills/microservice/command/aggregate-design/SKILL.md)) | agent preloads its skills via `skills:` frontmatter |
| skill **relates-to** skill | `## Related Skills` ([error-handling.md:45](rules/domain/error-handling.md)) | disambiguation + "see also" |
| agent **triggered-by** intent | `## Routing` ([dotnet-architect.md:33](agents-source/dotnet-architect.md)) | the `/dai.do` disambiguator's routing table |
| rule **enforced-by** analyzer | *(new in v2)* | the deterministic/advisory pairing (§7) |

The graph is **generated from frontmatter at build time** (never hand-maintained) and is what powers both the disambiguator (§4 L2) and validation (broken links fail CI).

### 2.4 Frontmatter contract (portable core + gated extensions)

```yaml
# PORTABLE (Agent Skills standard — safe on all four tools)
name: query-entity                      # ≤64 chars, lowercase-hyphen, == dir name
description: >-                          # ≤1024 chars; action-first + use-when + do-NOT-use
  Generates a query-side (read-model) entity with its projection handler for
  CQRS/event-sourced .NET. Use when adding a read model, projection, or query-side
  entity. Do NOT use for command-side aggregates (use add-aggregate) or a full CRUD
  stack (use add-crud).
metadata: { category: microservice/query, agent: query-architect }

# PER-HOST EXTENSIONS (injected only into the host that understands them, at projection)
x-claude: { paths: "${detected_paths.entities}/**/*.cs", disable-model-invocation: false }
x-cursor: { globs: "...", alwaysApply: false }
```

`x-<host>` blocks are stripped/translated by the projector; the committed `SKILL.md` for each host carries only that host's fields. (Claude extension fields — `disable-model-invocation`, `user-invocable`, `paths`, skill-`hooks` — are Claude-only; keeping them in `x-claude` preserves portability.)

### 2.5 Token substitution stays trivial (de-risks the .NET port)

Rendering is **regex token substitution, not a template engine** — `${Company}`, `${Domain}`, `${detected_paths.<key>}` ([render.py:148](src/dotnet_ai_kit/render.py)). This ports to .NET as a `Regex` + dictionary. **No Scriban/Handlebars parity is needed for the 124-skill corpus.** Real templating (Jinja2) is confined to a handful of scaffolding templates and becomes the *only* place a .NET template engine (Scriban) is considered — a tiny surface.

---

## 3. Intelligent invocation (the "smart" pillar)

Per your selection — **sharper auto-triggering + a routing brain** (you correctly skipped runtime orchestration and heavy composition). The routing research delivered a load-bearing correction: **a heavyweight router is an anti-pattern here.**

### 3.1 The skills ≠ tools distinction (why no big router)

All the "30–50 item degradation," RAG-MCP 3×, 85%-token-cut figures are about **MCP tools**, whose full schemas load upfront. **Skills** use progressive disclosure (~100 tokens each in the always-on listing). 124 skills ≈ 12–14K tokens (~6–7% of a 200K window) — **token bloat is not the problem; selection precision is.** Anthropic's own guidance favors native selection over custom routers, and the Agent Skills engineering post contains zero router guidance.

### 3.2 The three-layer light model

| Layer | What | Build it? |
|---|---|---|
| **L1 — Description engineering (≈90% of the value)** | The strict description standard below + the artifact graph's disambiguation edges. Zero per-request token cost, no single-point-of-failure. | **Yes — primary** |
| **L2 — Thin disambiguator** | Enhance the existing `/dai.do` with a curated decision table over the genuinely ambiguous clusters (`add-entity`/`add-aggregate`/`add-crud`; `review`/`verify`). **Guidance, not a gate.** | **Yes — small** |
| **L3 — Retrieval MCP router** | Only if MCP **tools** ever exceed ~30–50; then use native Tool Search (`defer_loading`), as a **separate** sibling MCP (not bolted onto `codebase-memory-mcp`, to keep the no-network `init/check/render` paths clean). **Never route the 124 skills through it.** | **Deferred / maybe never** |

### 3.3 The description standard (CI-enforced)

Every artifact description: **(1)** action-verb first, third person; **(2)** key use case before the **1,536-char** cap; **(3)** explicit positive triggers ("Use when the user…", with the words users actually say); **(4)** explicit **negative scope** ("Do NOT use when… use X instead") naming the sibling — *this is what makes 124 artifacts distinguishable*; **(5)** concrete nouns (framework names, file extensions, paths).

### 3.4 Invocation policy (the token lever)

| Frontmatter | User invokes | Model invokes | In `/` menu | Costs budget | Use for |
|---|---|---|---|---|---|
| *(default)* | ✓ | ✓ | ✓ | **yes** | read-only/safe skills you want auto-fired |
| `disable-model-invocation: true` | ✓ | ✗ | ✓ | **no** | **side-effecting commands** (`pr`, `wrap-up`, anything that commits/pushes/deploys) |
| `user-invocable: false` | ✗ | ✓ | ✗ | yes | pure background knowledge |

**Critical constraint for a plugin:** plugin skills **ignore** per-user `skillOverrides`, and these invocation fields are **Claude-Code-specific** `[unverified for Cursor/Copilot/Codex]`. So budget control must be **baked into authored descriptions + consolidation at build time**, not deferred to user settings. Concretely: mark the side-effecting commands `disable-model-invocation` (removes them from the listing), consolidate the duplicate skill pairs, and use argument-driven parents (your `/dotnet-ai.docs [readme|api|adr|…]` pattern) to collapse many behaviors into one budget entry.

---

## 4. Multi-tool projection engine (clean per-tool support)

### 4.1 Generalize the one proven projector

v1 already proves the model in one place: [render_cursor_rule_mdc()](src/dotnet_ai_kit/render.py:266) reads a source rule and projects it to Cursor's `.mdc` (conventions→`alwaysApply`, domain→`globs` from `paths:`). **v2 generalizes that single function into the projection engine** for every artifact × every host, behind an `IHostAdapter` port (§5).

### 4.2 Per-tool projection matrix (grounded, fetched 2026-05-30)

| Concern | Claude Code | Codex CLI | Cursor | GitHub Copilot |
|---|---|---|---|---|
| Plugin manifest | `.claude-plugin/plugin.json` | `.codex-plugin/plugin.json` (no `agents` field) | `.cursor-plugin/plugin.json` (`agents` field) | **auto-detects `.claude-plugin/plugin.json`** (IDE/CLI); cloud = render-only |
| Skills | `.claude/skills/` or plugin `skills/` | `.agents/skills/` / `.codex/skills/` | `.agents/skills/` (+ reads `.claude/skills/`) | `.agents/skills/` (+ reads `.claude/skills/`) |
| Agents | `agents/*.md` | `.codex/agents/*.toml` | `agents/*.md` | `.github/agents/*.agent.md` |
| Rules/instructions | `.claude/rules/*.md` + `paths:` | `AGENTS.md` (no glob scope) | `.cursor/rules/*.mdc` | `copilot-instructions.md` + `*.instructions.md` (`applyTo`) |
| Commands | merged into skills (legacy `commands/` still works) | skills (custom prompts deprecated) | `.cursor/commands/*.md` | `.github/prompts/*.prompt.md` |

**Leverage points (layout-robustness first):** the projection engine writes each host's skills into *that host's own* directory, so the file layout never *depends* on cross-tool reading. On top of that baseline, two **verified** optimizations: (1) **`.agents/skills/` is read by Cursor, Codex, and Copilot** (verified against each tool's skills docs, 2026-05-30 — Codex reads *only* `.agents/skills/`; Cursor and Copilot read it *plus* `.claude/skills/` for compatibility), so a single authored skills location can serve three tools, while Claude uses `.claude/skills/` + the plugin path; (2) **one `.claude-plugin/plugin.json` serves Claude Code + Copilot CLI + VS Code Copilot** (keep `name` identical) — collapsing three hosts into one manifest. The render-to-files track survives **only for the Copilot cloud agent.** Neither optimization is load-bearing: if a tool changes its discovery dirs, the projector simply writes that tool's own path.

### 4.3 CI gate kills drift

A single `gen` step regenerates every host's files + all manifests from `artifacts/` in one pass; a CI test runs it and asserts `git diff --exit-code`. The manifest can never again diverge from source (the cause of the 5-commit churn). Schemas are **tightened** to pin the exact intended shape (and `hooks`/`mcpServers`/`lspServers` are removed — Claude auto-discovers them).

---

## 5. The .NET 10 solution architecture (clean / hexagonal)

### 5.1 Project layout

```
dotnet-ai-kit.sln
├── src/
│   ├── DotnetAiKit.Core/            # Domain. NO I/O, NO deps.
│   │     Skill, Agent, Rule, Command, Profile, Manifest, ProjectConfig, ArtifactGraph
│   ├── DotnetAiKit.Application/     # Use-cases + PORTS. → Core only.
│   │     UseCases/  InitService, CheckService, RenderService, MigrateService, GenerateService
│   │     Ports/     IFileSystem, IGitClient, IProcessRunner, IHostAdapter,
│   │               IArtifactSerializer, IConsoleReporter
│   ├── DotnetAiKit.Infrastructure/  # Adapter impls. → Application, Core.
│   │     PhysicalFileSystem, GitCliClient, ProcessRunner,
│   │     JsonArtifactSerializer (STJ src-gen), YamlFrontmatterParser (YamlDotNet static ctx)
│   ├── DotnetAiKit.Hosts/           # Per-tool IHostAdapter. → Application, Core.
│   │     ClaudeHostAdapter, CodexHostAdapter, CursorHostAdapter, CopilotHostAdapter
│   └── DotnetAiKit.Cli/             # Composition root + System.CommandLine tree. → all.
│         Program.cs, Commands/, Output/SpectreConsoleReporter, Json/AppJsonContext, Yaml/YamlStaticContext
└── tests/
      Core.Tests, Application.Tests (fake ports), Cli.Tests (Verify golden-output)
```

Dependency direction: `Cli → {Hosts, Infrastructure, Application, Core}`; `Hosts/Infrastructure → Application → Core → (nothing)`. **The `IHostAdapter` port is the direct descendant of v1's `hosts/base.py`** — the cleanest seam in v1 becomes the backbone in v2. (Single `Hosts` project, one class per adapter; split per-host only if one pulls a heavy/conflicting dependency.)

### 5.2 The stack (verified versions, 2026-05-30)

| Concern | Choice | Status / note |
|---|---|---|
| CLI parsing | **System.CommandLine 2.0.8** | stable, 2026-05-12 (verified NuGet); use `SetAction` (not `SetHandler`); `Parse` then `InvokeAsync`; async actions must forward `CancellationToken` |
| DI | **manual `ServiceCollection` → `BuildServiceProvider`**, resolve in `SetAction` | `System.CommandLine.Hosting` is **deprecated**; avoid keyed DI under AOT (select host adapter via a `ToolName` dictionary) |
| Terminal UI | **Spectre.Console** (rendering only) | **never `Spectre.Console.Cli`** — it is `RequiresDynamicCode`, breaks AOT |
| Config (tool's own) | **System.Text.Json source-gen** → prefer **JSON** | in-box, AOT-clean |
| Artifact YAML frontmatter | **YamlDotNet + `Vecc.YamlDotNet.Analyzers.StaticGenerator`** | YAML can't be dropped; needs static context for AOT |
| Config binding/validation | **`EnableConfigurationBindingGenerator` + `[OptionsValidator]`** | reflection-free pydantic-equivalent; mandatory once `PublishAot=true` (else IL2026) |
| Token counting (NEW capability) | **Microsoft.ML.Tokenizers** (`TiktokenTokenizer`) | upgrades v1's line-count budget check to real token counts in `check` |
| Testing | **xUnit v3 (4.0+) or TUnit** + **Verify** | Verify golden-output snapshots every generated artifact — the regression contract |
| Distribution | **hybrid: per-RID Native AOT + `any` CoreCLR fallback `dotnet tool`** | ~2.5 MB / fast cold start where AOT exists; `ToolPackageRuntimeIdentifiers`, per-RID `dotnet pack`, pointer package last; AOT builds only on matching-OS CI |

### 5.3 Port the v1 gems, don't redesign them

`manifest.py` (sha256 + traversal guard) → `System.Security.Cryptography`; `upgrade.py` (atomic backup→rollback→rotate) → `System.IO`; subprocess probes → `System.Diagnostics.Process`. These were exemplary in v1; port their *design*.

---

## 6. Enforcement: deterministic + advisory (cures the v1 rule bug)

The first report's load-bearing finding: for a plugin-native Claude install, **domain rules never reach the model** (`copy_rules` is in a dead `else` branch, [cli.py:1334](src/dotnet_ai_kit/cli.py:1334); the only other write path writes `settings.json` only, [claude.py:110](src/dotnet_ai_kit/hosts/claude.py:110)). v2 fixes this *and* adds a hard backstop:

1. **Deliver rules natively.** `init` writes domain rules into the project `.claude/rules/*.md` **with `paths:` frontmatter** (the native JIT path); Cursor `.mdc` (already correct); Codex `AGENTS.md`; Copilot `*.instructions.md` (`applyTo`).
2. **Ship a Roslyn analyzer NuGet — `Dotnet.Ai.Kit.Analyzers`.** A subset of the markdown rules (naming, layer-dependency, banned APIs, public-setters-on-aggregates) become **compile-time build errors** via an `IIncrementalGenerator`/`DiagnosticAnalyzer` + `.editorconfig` severity. *Analyzers enforce; markdown rules guide; the two mirror each other.* This is the deterministic backstop the field report (`issues/rule-enforcement-gap/`) calls for.
3. **A `deterministic-enforcement` rule** declares which markdown rules have a paired analyzer, keeping the layers in sync.
4. **Profiles are the architecture-aware enforcement tier.** Each `profiles/<arch>.md` ships path-scoped *hard constraints* (e.g. Clean Architecture's layer-dependency direction, [clean-arch.md](profiles/generic/clean-arch.md)) injected by a `PreToolUse` hook on Write/Edit so the model has the active architecture's rules in context. Where a constraint is mechanically checkable (layer references, private setters, banned APIs) it is **also** emitted as an analyzer diagnostic — so profiles span *both* enforcement layers: advisory in-context (the hook) and deterministic at build (the analyzer). This is the "profiles" leg of the rewrite the user named explicitly.

---

## 7. Rebuild + expand: the coverage roadmap (your scope choice)

### 7.1 Rebuild (clean, while porting)

- Consolidate near-duplicate skills (`api/controllers`≈`controller-patterns`; `api/scalar`≈`openapi-scalar`; `cqrs-basics`→decision-guide linking `cqrs/`).
- Kill the `when_to_use` = `description` no-op (folds into the description standard, §3.3).
- Fix the broken sample at [event-catalogue/SKILL.md:189](skills/microservice/event-catalogue/SKILL.md) (`Activator.CreateInstance` on a positional record).
- Make the `dotnet-ai-architect` fixture first-class or move it to `tests/fixtures/` (fixes the Codex/Copilot leak by construction).

### 7.2 ⚠️ Foundation risk — verified, act on it

**MediatR now ships a commercial license-key model** (README: "register for your license key at MediatR.io"; latest 14.1.0; per the author's announcement, dual RPL-1.5/commercial since 2025-07, **versions < 13.0.0 remain free**). **MassTransit v9 is a commercial release** under the new company "Massient" (`masstransit.io` → `masstransit.massient.com`); v8 stays Apache-2.0 but loses support end-2026 `[secondary]`. Five v1 CQRS skills depend on MediatR.

→ **`mediator-abstraction` rule** (dispatch through a thin `ISender` port; concrete mediator swappable) + **`mediator-migration` skill** (free alternatives: **Mediator** by Martin Othamar — source-gen, MIT; **Wolverine** — MIT, also messaging; or pin MediatR < 13). Same pattern for messaging via a `messaging-bus-selection` rule.

### 7.3 New coverage (spans skills + rules + agents, anchored to .NET 10 GA 2025-11-11)

| Domain | New artifacts | Status |
|---|---|---|
| **.NET Aspire 13.1** (rebranded, decoupled, `aspire` CLI + `aspire agent init` MCP) | refresh `aspire-orchestration`; new `aspire-integrations`, `aspire-deployment`, `aspire-testing`; **`aspire-architect` agent** | grounded |
| **AI integration** | `extensions-ai-chat`, `extensions-ai-embeddings`; `ai-integration` rule; **`ai-engineer` agent** | **Microsoft.Extensions.AI GA 10.6.0 (verified)**; Agent Framework on watch `[ungrounded]` |
| **Minimal APIs / ASP.NET Core 10** | `minimal-api-patterns`, `endpoint-filters`, `minimal-api-validation` (source-gen `AddValidation`), `server-sent-events`; deepen `openapi-scalar` → OpenAPI 3.1 default | grounded |
| **Messaging** | `masstransit-consumers`, `masstransit-sagas` (w/ license caveat), `dapr-building-blocks`, `dapr-pubsub`, `dapr-workflow`, `wolverine-messaging` | grounded |
| **Roslyn** (see §6) | `roslyn-analyzer`, `incremental-source-generator`, `analyzer-packaging` + the NuGet | grounded |
| **Modern testing** | `playwright-e2e`, `mutation-testing` (Stryker), `tunit-testing` (opt-in), `testing-platform` rule (MTP) | grounded |
| **Blazor** | `blazor-render-modes`, `blazor-persistent-state` (`[PersistentState]`); deepen MudBlazor skills | grounded |
| **Auth** | `entra-id-auth`, `openiddict-server` (CVE-2026-40372 patch), `passkeys-webauthn` | grounded |
| **GraphQL** | `graphql-hotchocolate` (HotChocolate v15) | `[secondary]` |

Priority: (1) MediatR/MassTransit mitigation; (2) the Roslyn analyzer NuGet; (3) Aspire refresh; (4) AI integration; (5) Minimal API/ASP.NET 10; (6) messaging; (7) testing; (8) Blazor/auth/GraphQL; MAUI last.

---

## 8. Token / context strategy (managing the burn)

- **Progressive disclosure tiers:** Tier-1 description (budgeted) → Tier-2 `SKILL.md` ≤500 lines (loaded on invoke) → Tier-3 `references/`/`scripts/` (free until needed). Push spec/detail to Tier-3.
- **JIT path-scoping:** the 11 domain rules + location-specific code-gen skills carry `paths:` globs → load only when a matching file is touched. Narrow the two `**/*.cs` globs that defeat JIT today.
- **Consolidation + invocation policy** (§3.4) keep the model-invocable listing inside the ~1% budget.
- **Measurement as governance:** make `/context` (and `TiktokenTokenizer.CountTokens` in `check`) the canonical always-on metric in CI — replacing v1's line-count proxy. Re-anchor the "68% reduction" claim on this live measure (report #1 showed it measured the wrong layer).

---

## 9. Testing & quality (the cross-language gate)

- **Golden-output (Verify):** drive each `init`/`render`/`migrate`/`generate` use-case against a temp/in-memory `IFileSystem`, snapshot every emitted file. The committed `*.verified.*` files become the contract for generated artifacts — the safety net a full rewrite needs.
- **Triggering eval harness:** skill-creator-style — ~20 queries/skill (8–10 should-trigger, 8–10 tricky near-miss), 60/40 train/test, 3× runs, select on held-out score — **plus a cross-skill confusion matrix** (assert the correct skill fires and siblings don't). Gate description edits on held-out trigger rate.
- **Preserved invariants → .NET acceptance suite:** A-011 no-network (process-level network-deny), token budgets (`TiktokenTokenizer`), FR-031 8-exit-code, SC-001 ≤18-file footprint, SC-003 runtime resolution, host-symmetry. ~40 v1 artifact/contract tests port near-verbatim and become the gate the .NET binary must satisfy.

---

## 10. Phased roadmap (full rewrite, spec-preserving)

The two tracks run in parallel; the contract tests (§9) let them proceed independently.

**Track A — Artifacts & projection (tool-agnostic, start here)**
- **A0** Author the v2 source model (`artifacts/` tree, frontmatter contract, `fragments/`) + the description standard + the graph generator.
- **A1** Build the projection engine (`IHostAdapter` per host) + the `gen` entrypoint + the `git diff --exit-code` CI gate. Generalize the Cursor `.mdc` projector to all artifacts × hosts.
- **A2** Generate all manifests from one descriptor; tighten schemas; move path/shape validation into shipped `check`.
- **A3** Rebuild + consolidate the corpus (§7.1) to the new model; apply invocation policy + token strategy; stand up the triggering eval harness.
- **A4** Expansion coverage (§7.3) + the MediatR/MassTransit mitigation (§7.2).

**Track B — The .NET 10 CLI**
- **B0** Scaffold the clean solution (§5.1) + the stack (§5.2) + AOT packaging.
- **B1** Promote A-011/budgets/FR-031/SC-001 into the language-neutral acceptance suite (§9); add tests for v1's under-covered verbs (`render`/`detect`/`learn`).
- **B2** Port the trivial ~70% (file-copy/scaffold/host-routing, manifest, upgrade, subprocess probes) behind the gate.
- **B3** Port the hard ~30% (regex token-substitution — easy; the few Jinja2 scaffolding templates → Scriban with golden-output tests; pydantic → STJ src-gen + `[OptionsValidator]`).
- **B4** Distribution: hybrid AOT `dotnet tool` + a shared `marketplace.json` so onboarding is `/plugin install`, not pip.

**Track C — Enforcement**
- **C0** Ship `Dotnet.Ai.Kit.Analyzers` (the deterministic backstop, §6); wire rule delivery into `init`.

### Do-not-do / risk list
- **Don't** ship agent teams or dynamic workflows as a hard dependency (preview/experimental; the workflows feature is days old). Ship subagent *definitions*; compose at runtime, opt-in.
- **Don't** build a heavyweight router for the 124 skills (skills ≠ tools; it's an anti-pattern). Description engineering + the graph + the thin `/dai.do` disambiguator instead.
- **Don't** use `Spectre.Console.Cli` or `System.CommandLine.Hosting` (AOT-hostile / deprecated).
- **Don't** assume LSP for Codex/Cursor (doesn't exist agent-facing) or that user `skillOverrides` will tune a *plugin's* budget (they don't) — bake budget control into descriptions + consolidation.
- **Don't** depend on the exact MediatR/MassTransit version-cutoffs without re-checking the vendor pages at implementation time (the *commercial shift* is verified; the fine print is the authors' secondary sources).

---

## 11. Verification status & open decisions

**Verified against primary sources (2026-05-30):** System.CommandLine 2.0.8 stable (NuGet) · Microsoft.Extensions.AI GA 10.6.0 (NuGet) · MediatR commercial license-key model (GitHub README → MediatR.io) · MassTransit v9 commercial (massient.com) · Copilot auto-detects `.claude-plugin/plugin.json` + single repo serves three tools (code.visualstudio.com) · "commands merged into skills, `commands/` legacy" (code.claude.com) · the v1 rule-delivery dead branch, command duplication (17/27), agent-count drift, broken skill sample (all against v1 source) · **`.agents/skills/` discovery by Cursor + Codex + Copilot** (each tool's skills docs, 2026-05-30).

**[ungrounded] / [secondary] — confirm before they become load-bearing in code:** Microsoft Agent Framework `1.0.0-rc1` (secondary only) · MassTransit dollar pricing + v8-EOL date · TUnit pre-1.0 maturity · HotChocolate v15 specifics · System.CommandLine 2.0.0 *GA date* (the 2.0.8 *stable* version is confirmed; the GA date is not) · 3.0.0-preview API delta · exact Spectre.Console/YamlDotNet versions (target "latest at build") · keyed-DI and full Generic-Host AOT-cleanliness (design avoids both) · whether Cursor/Copilot/Codex honor Claude's invocation-control frontmatter · Aspire 13.1 rebrand + `aspire.dev` move (researcher fetch, not independently re-verified) `[secondary]`.

**Open decisions for you:**
1. **Port scope** — full parity, or only the per-solution no-network work (`init/detect/migrate` + writing `.dotnet-ai-kit/*`, `.claude/settings.json`, `.claude/rules/`), leaving the artifact corpus to the plugin install path?
2. **Config format** — JSON (frictionless AOT) vs keep YAML (needs the static generator) for the tool's own config?
3. **Marketplace** — project-scope (committed to a team repo) vs user-scope; pinned vs ship-every-commit?
4. **Copilot** — depend on the `.claude-plugin/` auto-detect (Preview) for IDE/CLI, keeping render only for the cloud agent?
5. **Skill count** — target after consolidation, and which skills are model-invocable vs user-only.
6. **Mediator replacement** — pin MediatR < 13, or migrate to Mediator (source-gen) / Wolverine as the default in generated solutions?
