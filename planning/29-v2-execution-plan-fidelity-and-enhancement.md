# dotnet-ai-kit v2 — Execution Plan: Fidelity & Enhancement

**Date:** 2026-06-02 · **Status:** EXECUTION PLAN — **scope locked by maintainer.** Consolidates the [27](27-post-022-fidelity-and-defect-audit.md) audit (defects/refactors) and the [28](28-v2-artifact-and-tooling-enhancement-plan.md) enhancement plan (W1–W7) into a single dependency-ordered task list, and **supersedes [28 §9](28-v2-artifact-and-tooling-enhancement-plan.md) (open decisions)** — all resolved below.
**Branch baseline:** `022-v2-fidelity-gaps` @ `7419c7e` (green: build `-warnaserror` 0/0 · 142 tests · drift-clean · `claude plugin validate --strict` pass).
**Posture:** this doc is the plan; **no code changed by authoring it.** Each increment below lands as an independently-testable green increment against the standing gates (§6).

---

## 1. Locked decisions (maintainer, 2026-05-31 → 2026-06-02)

| # | Decision | Choice | Drives |
|---|---|---|---|
| L1 | AR-5 resources | **Enrich by archetype** (AM-1 accepted) | W3, W7 |
| L2 | Script default | **.NET file-based C#** (AM-2 accepted), BCL-only, `dotnet run --file` | W2 |
| L3 | Profile delivery channel | **Always-on** (Claude output-style; Codex→`AGENTS.md`, Cursor→`.mdc`, Copilot→`.instructions.md`) | W1.1 / D2 |
| L4 | W7 expansion scope | **All confirmed, now** — 2 new agents + 11 STRONG + 5 MEDIUM skills | W7 / Phase J |
| L5 | Cursor agents | **Emit + realign the plugin dir** (not "drop the array") | W1.2 / D1 |
| L6 | Kit's-own-MCP-server (5th surface) | **Build it** (not park) — net-new engine workstream | Phase K |

## 2. Reconciled micro-decisions (defaults — say otherwise to change)

**M1 — Glob narrowing (reconciles the one real 27↔28 conflict).** [27 A5](27-post-022-fidelity-and-defect-audit.md) says narrow *3*; [28 W5.1](28-v2-artifact-and-tooling-enhancement-plan.md) says narrow *6*. Resolution:
- **Narrow the 3 both docs agree on:** `mediator-abstraction` → DI/composition (`**/Program.cs,**/*Extensions.cs,**/DependencyInjection/**`); `messaging-bus-selection` → DI/messaging; `ai-integration` → AI namespaces/features.
- **Keep `error-handling` + `performance` broad** (`**/*.cs`). 27's defense holds — these genuinely apply across most C# code; narrowing them to handler/repo/endpoint risks *under*-triggering. (This is the one spot 27 and 28 truly differ; override toward 28's narrowing only if idle-token economy is judged to outweigh coverage.)
- **`deterministic-enforcement` → universal (`alwaysApply`, no path glob) or doc-only.** It's a meta-registry pointing at analyzers; the path glob is a false JIT story (both docs effectively agree it's special).

**M2 — Profile selection mechanism.** Map `project.yml architecture:` → profile **by name/filename convention** (`clean-arch` → `clean-arch.md`). No new frontmatter field unless the architecture value-space diverges from profile names — then add a small mapping table in the adapter. (Profiles today carry only `name`/`description`/`metadata.paths`; *verified first-hand*.)

**M3 — Two-tier profile delivery** (the "always-on" choice applies to the architecture profile only):
- **Architecture-tier (single-select, always-on):** `clean-arch`, `ddd`, `modular-monolith`, `vsa`, `hybrid`, `generic` — the one matching `project.yml architecture:` is injected always-on at **`init`** (arch is per-project, unknown at build time), and it is what the Claude output-style names (fixing the "output-style references a profile that never ships" bug).
- **Role/band-tier (additive, path-scoped — NOT always-on):** `command`, `query-cosmos`, `query-sql`, `gateway`, `processor`, `controlpanel` — keep path-gated (they target specific folders; always-on would multi-inject). Narrow `controlpanel`/`vsa` broad-ish globs under M1.
- *Confirm this 6/6 split during D2; it's derived from profile glob breadth + role semantics.*

**M4 — Delivery format.** This planning doc + an in-session ordered task list drive execution (the pattern 27/28 used). The two feature-shaped workstreams (**profile delivery D2**, **MCP server K**) may *optionally* be promoted to SDD specs (`specs/023+`) if you want the full `specify→plan→tasks` ceremony; the defect/refactor increments stay direct.

**M5 — W7 maturity gate.** Every W7 skill's GA/version claim (MCP SDK 1.3.0, YARP 2.3.0, EF Core 10 vector search, Agent Framework 1.0, azd v1.22, …) is an **external dated fact not verifiable from the repo** — re-confirm via web/docs at authoring time (Phase J), pinning the highest-recency items (Agent Framework, EF-10 approximate vector) per 28's own caveats.

---

## 3. Sequenced increments

Ordered for dependency safety and value-first. Each phase = one or more green increments; re-accept Verify goldens whenever projection shape changes.

### Phase A — Shipped-sample correctness *(27 §7.1)*
- **A1** [event-catalogue/SKILL.md:187](../artifacts/skills/microservice/event-catalogue/SKILL.md) — replace `Activator.CreateInstance(type, nonPublic:true)` with `RuntimeHelpers.GetUninitializedObject(type)`. *Sound because `Type` is a computed property (`=> EventType.X`), field-independent — verified.* Add the **semantic regression guard** (compile-and-run the doc sample; Roslyn-parse won't catch it). Reconcile the "fixed" claims in [25 FR-H1 / 26 AR-9](27-post-022-fidelity-and-defect-audit.md).
- **A2** `aggregate-design` / `event-sourcing-flow` — add `private Order() { }` to the concrete aggregate so prose matches code.
- **A3** `cqrs/mediatr-handlers` + `command-generator` — add the MediatR commercial-license note + "abstract behind `ISender`; see `mediator-migration`."
- **A4** `core/mapping-strategies:3` — qualify/drop AutoMapper in the description.
- *Gate delta: regenerate `build/`, re-accept goldens.*

### Phase B — Misleading guarantees & safety nets *(27 §7.2–7.3)*
- **A7** Wire `ManifestIntegrityService` into `CheckService` exit-14 (compute+store+verify SHA-256 of `manifest.json`), **or** rename the check "manifest-present" and record NFR-7 deferred. Closes the only misleading *guarantee*.
- **A8** Add a layering **fitness test** in `Acceptance.Tests` (Core refs no `DotnetAiKit.*`-but-Core, no third-party; Application refs no Hosts/Infrastructure/Cli/Spectre). Cheap insurance for the headline invariant.
- **A9** [CompositionRoot.cs:55](../src/DotnetAiKit.Cli/CompositionRoot.cs) — reword the `NotSupportedException` to "init has no per-solution footprint for plugin-native/render-only host '{host}' (Claude only)."

### Phase C — Rules/profiles coherence *(prerequisite for profiles — 28 W5.1/W5.2 + 27 A5/A6)*
- **C1 (M1)** Narrow the 3 globs; `deterministic-enforcement` → universal/doc-only; keep `error-handling`/`performance` broad.
- **C2 (W5.2, P5)** De-duplicate `generic.md` vs the universal rules (`coding-style`/`async-concurrency`/`naming`/`error-handling`/`data-access`); `clean-arch` ≈ `data-access`+`performance`. Profiles carry only **architecture-specific** constraints and *reference* the generic rules. **Hard prerequisite for D2** (else always-on profiles double-inject the always-on rules).
- **C3 (A6)** Trim the v1 Python half of `rules/domain/testing.md`; bump `RuntimeMoniker.Net90` when a .NET 10 moniker ships.
- *Gate delta: glob changes alter projected `.mdc`/rule output → re-accept goldens + drift.*

### Phase D — Dead/broken delivery *(28 W1 — highest user-visible value)*
- **D1 (L5)** **Cursor plugin realign + agents** — see §4a. Move manifest into the plugin dir, emit `agents/<name>.md`, add the **manifest-references-resolve** acceptance test.
- **D2 (L3/M2/M3)** **Profile delivery** — arch-tier profile selected by name at `init`, injected always-on (Claude output-style + named there; Codex/Cursor/Copilot static), role/band stay path-scoped. Add the **profile-delivered** acceptance test (after `init`, the arch profile reaches the project). Depends on **C2**.
  - **⚠ Open design question (resolve first):** naming a profile in the output-style ≠ delivering its *content* — that is the current bug (the output-style references a profile that never ships). Always-on *content* delivery likely requires **embedding the selected profile's text into a per-project output-style generated at `init`** (arch is per-project), which makes the output-style an **init-generated per-project artifact** with a **determinism/drift implication** (per-project files aren't in the `build/` baseline), rather than the static plugin asset it is today — or it falls back to the PreToolUse hook L3 chose to avoid. **Verify how `ClaudeOutputStyleWriter` + `build/claude/output-styles/` work before building D2.**
- **D3 (W1.3)** **MCP/LSP projection** — project `.mcp.json` into each `build/<host>/` from one descriptor (Codex `[mcp_servers]` in `config.toml`; Cursor `mcpServers`); `.lsp.json` into `build/claude/` (+ `build/copilot/` Preview); **wire LSP into agents** (`reviewer`/`dotnet-architect`/`ef-specialist` prefer `goToDefinition`/`findReferences`). *This `.mcp.json` track is the install mechanism for Phase K.*

### Phase E — Scripts: dogfood .NET *(28 W2 · L2/AM-2)*
- **E1** Port the 4 Python scaffolders → C# file-based, BCL-only (`constitution`, `checklist`, `fix/repro_test`, `release/bump_version`); `ScriptTrust` recognizes `.cs`; add `dotnet run --file` usage note + shebang.
- **E2** Add the 2 new C# scripts: `event-catalogue/scripts/` (the corrected A1 generator) + `docs/changelog-gen/scripts/` (git-log → Keep-a-Changelog).
- **E3 (B1)** Resolve `IGitClient`/`GitCliClient` — **wire into `OrchestrateService`'s FR-G7 dirty-tree skip** (actual git-dirty check, not just missing-dir) **or** delete as dead code.
- **E4 (scope guard)** Do **not** add scripts to `add-*`/`*-generator` (judgment-codegen).
- *Gate delta: each script proven **no-network + `dotnet run --file`** runnable.*

### Phase F — Byte-stable refactors *(27 R1–R5)*
- **R1** Delete `ClaudeProjector.FrontmatterBuilder` (≈45 dead lines); reuse the shared `FrontmatterWriter`.
- **R2** Extract one `YamlScalar.Quote` (the escaper is copy-pasted in 5 files — verified).
- **R3** Introduce `PluginNativeHostBase` across the 4 projectors (shared skill+resource-emission skeleton).
- **R4** Route `FileSystemArtifactRepository` `manifest.yml` parsing through the injected `IArtifactSerializer` (drop the second `IDeserializer`).
- **R5** Populate the failure channel in `OrchestrateService`/`ConfigureService`/`MigrateService` on real failures (or drop the unused `Errors`/`Ok` field).

### Phase G — Skill enrichment by archetype *(28 W3 · L1/AM-1)*
- **G1** Relocate code-dense bodies → `references/<variant>.md` (`multi-tenancy`, `fluent-validation`, `feature-flags`, `input-sanitization`, `caching-strategies`, `signalr-realtime`) / `examples/` (`scalar-docs`, `batch-processing`, `aggregate-testing`, `listener-pattern`, `outbox`).
- **G2** Compilable `examples/` for the heavy microservice band + `command-generator`/`query-generator`; Roslyn-parse-gate them.
- **G3** Deepen genuinely thin skills (content): `extensions-ai-chat`/`-embeddings` (54 lines), `blazor-hybrid` (58).

### Phase H — Agents optimization *(28 W4)*
- **H1** Backfill 13/15 descriptions to standard (only `aspire-architect`/`ai-engineer` conform).
- **H2** Name sibling agents in each `## Boundaries` line; reference **by name, not path**.
- **H3** Emit restricted `tools:` for read-only agents (`reviewer`, `docs-engineer`) + pin a cheaper `model:` (Claude GA); restore `## Routing` blocks to the two newest agents.
- **H4** Add Copilot `skills:` preload when `.agent.md` frontmatter GAs (track Preview gap).

### Phase I — Analyzers, evals & dogfooded descriptions *(28 W5.3/W5.4 + W6 + 27 B3/B4)*
- **I1 (W5.3)** Grow the analyzer set behind `deterministic-enforcement` (Cosmos lowercase-`id`, DbContext-Scoped lifetime, parameterized-SQL, `DateTime.Now`→`TimeProvider`); populate the dead `analyzer-backed-constraints` profile field.
- **I2 (W6)** Author `evals/cases.jsonl` for the high-mis-trigger clusters (auth 5-way, blazor 5-way, aspire 4-way, gateway 4-way, messaging-bus 3-way, dapr 3-way, EF/data); run through the confusion-matrix gate.
- **I3 (B3/W5.4)** Backfill ~11 legacy rule + ~15 legacy agent/skill descriptions; consider gating *all* artifacts (not just new). Decide Codex `AGENTS.md` trim (952 always-on lines → universal + pointer?).
- **I4 (B4)** Add a `JsonSerializerContext` (realize the "source-gen" claim, relevant to deferred AOT) **or** correct the CLAUDE.md stack description.

### Phase J — W7 net-new expansion *(L4 — additive, independent of A–I)*
- **J1 (M5 gate)** Re-confirm each maturity claim via web/docs; pin highest-recency packages.
- **J2** 2 new agents: `mcp-engineer`, `performance-engineer` (verified ownership gaps).
- **J3** 11 STRONG skills: `ai/mcp-server`, `ai/extensions-ai-evaluation`, `ai/agent-framework`, `api/yarp-reverse-proxy`, `data/ef-vector-search`, `data/ef-advanced-mapping`, `performance/runtime-diagnostics`, `security/supply-chain`, `security/secrets-management`, `devops/container-hardening`, `devops/iac-bicep-azd`.
- **J4** 5 MEDIUM skills: `core/file-based-apps`, `messaging/kafka-confluent`, `messaging/event-hubs`, `api/webhooks`, `devops/native-aot-publishing`.
- *All description-standard-gated (incl. "Do NOT use… (use X)") + archetype-enriched (L1) + deduped (verified absent). `ai/mcp-server` proves the pattern Phase K dogfoods.*

### Phase K — Kit's-own-MCP-server, the 5th surface *(L6 — net-new engine)*
See §4b for design. Best sequenced **after D3** (the `.mcp.json` install track) and **after J3's `ai/mcp-server`** (the dogfood pattern).

---

## 4. Net-new workstream designs

### 4a. Cursor plugin realign *(D1)*

**Problem (verified):** Cursor's real spec ([docs](https://cursor.com/docs/reference/plugins.md)) is **one** plugin dir — `<root>/.cursor-plugin/plugin.json` with `rules/ skills/ agents/ commands/` as auto-discovered **siblings**. Claude's projection already follows this (`build/claude/.claude-plugin/plugin.json` + siblings). Cursor's does **not**: manifest at `build/.cursor-plugin/plugin.json` (build root) while components live in `build/cursor/`. So nothing auto-discovers, and the manifest's `agents` array (`./agents/*.md`) resolves to a nonexistent `build/agents/`.

**Target layout (mirror Claude):**
```
build/cursor/
├── .cursor-plugin/plugin.json     # moved INTO the plugin dir
├── rules/*.mdc
├── skills/<name>/SKILL.md
├── commands/<name>.md
└── agents/<name>.md               # NEW — emit these
```
**Agent file format (Cursor spec):** frontmatter **`name` (kebab) + `description` only** — *no* `model`/`tools` like Claude subagents. Reuse `FrontmatterWriter`, same shape as the skills loop in [CursorProjector.cs:27](../src/DotnetAiKit.Hosts/Cursor/CursorProjector.cs). Keep or drop the explicit `agents` array (auto-discovery covers it; if kept, paths plugin-root-relative).
**Test:** manifest-references-resolve (any referenced path that isn't emitted fails the build) — the class of bug the drift gate can't see.

### 4b. MCP server *(Phase K)*

**Why it's not a 5th `IHostProjector`:** that port returns `ProjectedFile(path, content)` — *static files*. An MCP server is a *live process exposing tools queried at runtime*. It is a **new runtime surface**, not a projection.

**Architecture (reuses Core + the loader):**
- **K1** New project `DotnetAiKit.Mcp` (→ Application/Core). Load the same `ArtifactCorpus` via the existing `FileSystemArtifactRepository`.
- **K2** Tool surface via `[McpServerTool]` over Core: `search_skills`, `get_skill`, `search_knowledge`, `get_rule`, `list_agents`, `get_profile`. Transport **stdio** via the GA **`ModelContextProtocol`** package (1.3.0, 2026-05-08, maintained w/ Microsoft); `.Core` for minimal deps, `.AspNetCore` only if HTTP is later wanted.
- **K3** New CLI verb `dotnet-ai mcp serve` (long-running). **Scope it OUT of the NFR-1 no-network acceptance test** (that test guards the one-shot local verbs `init/check/render/generate/migrate`; a server's networking is the point). Handle lifecycle/shutdown.
- **K4** Install wiring — project an `.mcp.json` (D3) pointing at the server; Cursor plugins bundle `mcpServers`, so the Cursor plugin (4a) can declare it; Claude/Codex configs likewise. "Install the kit" → MCP surface auto-wired.
- **K5** Tests: tool-contract + "served corpus == loaded corpus"; `mcp serve` smoke. Dogfood against `ai/mcp-server` (J3).
- **K6 (roadmap, decide separately):** `event-catalogue` MCP tool over `events.json`; the `audit` CLI verb (`NuGetAudit` + `sbom-tool` + secret-scan). Pairs with `security/supply-chain`.

**Watch:** new long-running lifecycle + a versioned tool contract (back-compat) is a bigger ongoing surface than file projection; DI/hosting adds tension with the deferred Native-AOT goal (NFR-4) — `.Core` minimizes it.

---

## 5. Standing acceptance gates (every increment)

`dotnet build dotnet-ai-kit.slnx -warnaserror` 0/0 · `dotnet test` green · `dotnet format --verify-no-changes` · `dotnet run -- generate --check --out build/` drift-clean · `claude plugin validate build/claude --strict` + marketplace `--strict` pass.

**New gates added by this plan:** A1 semantic regression guard · A8 layering fitness test · D1 Cursor manifest-references-resolve + Cursor plugin loads · D2 profile-delivered test · E no-network `dotnet run --file` · I2 confusion-matrix extended to new clusters · K `mcp serve` smoke + served-corpus parity.

## 6. Out of scope / still deferred

Native-AOT packaging (BD-3) · full ≥20-queries/skill **live-LLM** eval (AR-6 — clusters-first only) · live in-session hook firing (interactive-only) · Codex/Cursor plugin-**load** parity beyond structure · re-litigating `planning/26` beyond AM-1/AM-2. The K6 roadmap items (`event-catalogue` MCP, `audit` verb) are committed-adjacent but decided at K-time.

---

*Plan consolidated; nothing built. Sequencing: A→B→C→D (Cursor, profiles, MCP/LSP) →E→F→G→H→I, with J (W7) running in parallel as additive work and K (MCP server) after D3+J3. Phases A–B and D1 are the fastest user-visible wins.*
