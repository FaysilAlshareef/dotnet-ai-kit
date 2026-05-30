# dotnet-ai-kit v2 — Requirements Specification

**Date:** 2026-05-30 · **Status:** requirements baseline for the v2 rewrite
**Consolidates:** [20 strategy](20-rewrite-strategy-net10.md) · [21 blueprint](21-v2-architecture-blueprint.md) · [22 structure](22-v2-project-structure.md) · [23 catalog](23-v2-artifact-catalog.md) · [24 selector/gates/lifecycle](24-v2-selector-gates-lifecycle-multirepo.md)

> ⚠️ **Amended by [26](26-v2-build-plan-and-decisions.md) (authoritative)** after Codex review. Overrides where they differ: **FR-C6** → framework-dependent `dotnet tool` first, Native AOT deferred; **FR-F2/F4** → hard enforcement tiers Claude-scoped with per-host fallbacks; **FR-A2/A3** → neutral artifact model + opt-in per-skill resources; **FR-H2** → license-light generated code by default (commercial packages opt-in); **+ new FR-I…FR-N** (host-capability matrix + smoke tests, script trust/security model, user-owned-file policy, artifact schema versioning, release/rollback, Windows parity). Build order in 26 §5.

This is the formal, testable requirements baseline. Each **FR** (functional) / **NFR** (non-functional) is phrased so a test or check can verify it. Requirements trace back to the verified research and the v1 reference behavior.

## Purpose & scope

Rewrite dotnet-ai-kit as a **.NET 10** clean-architecture CLI that authors every artifact **once** in a tool-agnostic source and **projects** it to Claude Code, Codex CLI, Cursor, and GitHub Copilot — with intelligent (low-token) invocation, layered enforcement + verification gates, a complete SDD lifecycle, and first-class multi-repo orchestration. The v1 repo + its 717 tests are the **reference spec**, not the starting code.

**Goals:** clean architecture · clean per-tool separation · rich artifacts (scripts/examples/resources) · precise auto-triggering + a thin routing brain · deterministic enforcement · token-frugal, high-quality output · full SDD cycle · robust multi-repo.
**Non-goals (v2.0):** hard dependency on preview features (agent teams, dynamic workflows); a heavyweight runtime router over skills; MAUI depth; cloud-agent plugin parity beyond render-to-files.

**Resolved open decisions (this baseline):**
- **D1** `constitution` is a **new command**, split from `learn` (`learn` = extract project knowledge; `constitution` = author/amend governing principles).
- **D2** `fix` is **added** as a command (TDD bug-fix loop: reproduce → fix → verify).
- **D3** `orchestrate` defaults to **sequential, dependency-ordered** execution; `--parallel` opts into subagent fan-out.
- **D4** the **Stop-hook verification gate** is **scoped to feature/implement flows** (not every turn) and configurable per permission profile.

---

## FR-A — Artifact model & authoring

- **FR-A1** A single `artifacts/` tree is the sole authored source of truth for all artifact types (skills, agents, rules, profiles, fragments, knowledge, manifest descriptor). No artifact is hand-authored in a per-tool output location.
- **FR-A2** The **skill** is the atomic resource-bearing unit: `SKILL.md` (≤500 lines) + optional `scripts/` (`.py` default; optional `.ps1`/`.sh` siblings) + `examples/` (compilable C# projects) + `references/` (`.md`) + `assets/` (`.json`/templates/diagrams) + `evals/` (`cases.jsonl` + `expected/`).
- **FR-A3** Agents, commands, and rules carry no bundled resource directories; they **reference** skills (Claude `skills:`, Codex `skills.config`, Cursor/Copilot markdown links).
- **FR-A4** `SKILL.md`/agent frontmatter uses **portable core fields** (`name` ≤64 kebab == dir, `description` ≤1024, `license`, `compatibility`, `metadata`) plus `x-<host>` blocks for host-specific extensions; the projector strips/translates `x-<host>` so each emitted file carries only fields that host understands.
- **FR-A5** Runtime project-metadata substitution is **token replacement only** (`${Company}`, `${detected_paths.x}`, …) — no general template engine is required for the artifact corpus.
- **FR-A6** An **ArtifactGraph** is generated from frontmatter (nodes = artifacts; edges = owns/relates/triggers/enforced-by); the build fails on broken edges (a reference to a non-existent artifact).
- **FR-A7** Lifecycle commands are authored as **command-skills** with `disable-model-invocation: true` (slash-only, user-invoked, removed from the always-on listing budget).

## FR-B — Projection engine & multi-tool support

- **FR-B1** A projection engine renders `artifacts/` into each host's native shape (Claude `.md` skills/agents/rules; Codex `.toml` agents + `AGENTS.md`; Cursor `.mdc` rules + `.md`; Copilot `.instructions.md`/`.prompt.md`/`.agent.md`), one `IHostAdapter`/projector per tool.
- **FR-B2** Projection is **CI-gated**: a `generate` step regenerates every host output + all manifests in one pass; CI asserts `git diff --exit-code` (drift is impossible to merge).
- **FR-B3** All per-tool plugin manifests are rendered from **one manifest descriptor**; each host's JSON schema pins the exact intended shape; auto-discovered keys (`hooks`/`mcpServers`/`lspServers`) are absent from manifests.
- **FR-B4** Skills are also surfaced under `.agents/skills/` (read by Cursor, Codex, Copilot — verified) as an optimization; the architecture does **not depend** on cross-tool reading (the projector writes each host's own dir regardless).
- **FR-B5** One `.claude-plugin/plugin.json` serves Claude Code + Copilot CLI + VS Code Copilot (identical `name`); the render-to-files track is retained **only** for the Copilot cloud agent.
- **FR-B6** `dotnet-ai init` writes a small per-solution footprint (`.dotnet-ai-kit/{config,project,manifest,version}` + `.claude/settings.json` + `.claude/rules/*.md`); the corpus comes from the plugin install path.

## FR-C — The .NET 10 CLI

- **FR-C1** The solution follows clean/hexagonal layering with dependencies pointing inward: `Cli → {Hosts, Infrastructure, Application} → Core`; `Core` has no I/O and no third-party deps.
- **FR-C2** CLI parsing uses **System.CommandLine 2.0.8** (`SetAction`, `Parse`→`InvokeAsync`); DI is a manual `ServiceCollection` (no `System.CommandLine.Hosting`); host adapters are selected by `ToolName` (no keyed DI).
- **FR-C3** Rich terminal output is **Spectre.Console** behind an `IConsoleReporter` port (never `Spectre.Console.Cli`); use-cases never reference the console library.
- **FR-C4** The tool's own config is **JSON** via `System.Text.Json` source-gen; artifact YAML frontmatter uses **YamlDotNet + the static generator**. Both are reflection-free.
- **FR-C5** Config validation uses `[OptionsValidator]` + DataAnnotations (reflection-free); `EnableConfigurationBindingGenerator=true`.
- **FR-C6** The tool ships as a **hybrid `dotnet tool`**: per-RID Native AOT packages + an `any` CoreCLR fallback, plus a project-scope, pinned `marketplace.json`.
- **FR-C7** The CLI exposes verbs: `init`, `check`, `render`, `migrate`, `generate`, `configure`, `detect`, `upgrade` (each a thin `*Command` delegating to an Application use-case).

## FR-D — SDD lifecycle commands (32)

- **FR-D0** The complete cycle is supported, bookend to bookend:
  `constitution → specify → clarify → checklist → plan → tasks(→issues) → analyze → orchestrate → implement → review → verify → pr → release`, with `status`/`undo`/`checkpoint`/`wrap-up` available at any point and `do` chaining the core path.

| FR | Command | Alias | Requirement (testable behavior) |
|---|---|---|---|
| D1 | **do** | dai.do | Chains specify→plan→implement→review→verify→pr; pauses on complexity/ambiguity; `--dry-run`/`--no-pr`/`--no-review` |
| D2 | **constitution** 🆕 | dai.const | Creates/amends `.dotnet-ai-kit/constitution.md` (governing principles); re-sync dependent templates; gates analyze/review |
| D3 | **specify** | dai.spec | Writes `spec.md` (per [13 schema](13-handoff-schemas.md)); microservice mode adds Service Map; emits ≤3 `[NEEDS CLARIFICATION]` |
| D4 | **clarify** | dai.clarify | Resolves ambiguities; writes answers back to `spec.md`; ≤5 questions |
| D5 | **checklist** 🆕 | dai.cl | Generates a feature-specific quality checklist from the spec and runs it as a gate before implement/PR |
| D6 | **plan** | dai.plan | Writes `plan.md` (+ `service-map.md`/`event-flow.md` in microservice mode); layer/service phases |
| D7 | **tasks** | dai.tasks | Writes ordered, dependency-aware `tasks.md`; **`--issues`** converts tasks to linked GitHub issues |
| D8 | **analyze** | dai.check | Cross-artifact + cross-repo consistency (event catalogue, proto client↔server, coverage); writes `analysis.md` |
| D9 | **orchestrate** 🆕 | dai.orch | Multi-repo conductor (FR-G): init affected repos, project feature-briefs, sequence by dependency, report status; `--parallel` opt-in |
| D10 | **implement** | dai.go | Executes tasks; build/test per layer/repo; `--resume` from failed task |
| D11 | **review** | dai.review | Standards review (+ optional CodeRabbit); writes `review.md` |
| D12 | **verify** | dai.verify | Build/test/format + mode-adaptive proto/resource/k8s checks, per repo; writes `verify.md` |
| D13 | **fix** 🆕 | dai.fix | Bug-fix loop: write a failing test reproducing the symptom → fix → verify the test passes |
| D14 | **pr** | dai.pr | Per-repo PR with cross-referenced "Related PRs"; uses verify results |
| D15 | **release** 🆕 | dai.release | Post-merge close-out: version bump + changelog + tag + GitHub release (+ optional deploy hook) |
| D16-D22 | **add-aggregate / add-entity / add-event / add-endpoint / add-page / add-crud / add-tests** | dai.agg/entity/event/ep/page/crud/tests | Code-gen per [23 catalog](23-v2-artifact-catalog.md) |
| D23 | **init** | dai.init | Initialize per-solution files (FR-B6) |
| D24 | **configure** | dai.config | Interactive config wizard |
| D25 | **detect** | dai.detect | Detect architecture/.NET version/paths |
| D26 | **learn** | dai.learn | Extract project knowledge / topic split (no longer authors the constitution — see D2) |
| D27 | **docs** | dai.docs | Generate docs (readme/api/adr/deploy/release/service/code/feature/all) |
| D28 | **status** | dai.status | Feature progress + next step; multi-repo aggregate (FR-G6) |
| D29 | **undo** | dai.undo | Revert last AI-generated changes safely |
| D30 | **explain** | dai.explain | Explain a pattern with examples |
| D31 | **checkpoint** | dai.save | Save handoff checkpoint |
| D32 | **wrap-up** | dai.done | End session with summary + handoff |

- **FR-D33** All 32 are command-skills (FR-A7): `disable-model-invocation: true`; the 4 new ones each bundle their workflow `scripts/` + `examples/` per FR-A2.

## FR-E — Skill-selector / intelligent invocation

- **FR-E1** Every artifact `description` conforms to the **description standard**: action-verb first, third person, key use case before the 1,536-char cap, explicit "Use when…" triggers, and explicit "Do NOT use when… (use X)" negative scope naming the sibling.
- **FR-E2** Invocation policy is set per artifact: command-skills `disable-model-invocation: true`; pure-background skills `user-invocable: false`; auto-fire knowledge skills default. (Claude-specific fields gated in `x-claude`.)
- **FR-E3** The ArtifactGraph's confusion-pair edges drive the disambiguation text in descriptions and each agent's `skills:` preload.
- **FR-E4** Domain rules and location-specific skills carry `paths:` globs and load only when a matching file is touched (JIT).
- **FR-E5** `/dai.do` carries a curated decision table for genuinely ambiguous clusters — **guidance, not a gate** (the model may still load an artifact directly; no single point of failure).
- **FR-E6** A **triggering eval harness** (≥20 queries/skill, 60/40 train/test, 3× runs, held-out selection) plus a **cross-skill confusion matrix** gate description changes in CI (correct skill fires; siblings stay silent).
- **FR-E7** The model-invocable always-on listing stays within the ~1% budget: commands are off-budget (FR-A7), duplicate skills are consolidated, and `/context` + a `TiktokenTokenizer` check in `dotnet-ai check` is the governance metric (CI fails on regression).

## FR-F — Enforcement & verification gates

- **FR-F1 (T1 advisory)** `init` writes domain rules to the project `.claude/rules/*.md` **with `paths:`**; a **PreToolUse hook** injects the active profile/rule body (`additionalContext`) when a matching file is edited. *(Fixes the v1 bug where plugin-native Claude never received rules.)*
- **FR-F2 (T2 interceptive)** A PreToolUse hook returns `permissionDecision: deny` for hard violations (forbidden path, banned API); mechanical checks use a `command` hook, judgment calls a `prompt` (Haiku) hook.
- **FR-F3 (T3 deterministic)** A shipped `Dotnet.Ai.Kit.Analyzers` Roslyn NuGet emits build-error diagnostics for analyzer-backed rules (naming, layer-dependency, banned APIs, public setters on aggregates); `.editorconfig` sets severity.
- **FR-F4 (T4 completion gate)** A **Stop/SubagentStop hook** (`decision: block`) runs `dotnet build` + `dotnet test` (+ format) when the agent attempts to finish a **feature/implement flow** (per D4) and blocks completion until green, feeding failures back.
- **FR-F5** The advisory `verification-gate` skill, `/verify`, `/review` (+ CodeRabbit), and `SubagentStop` together enforce "no completion claim without fresh evidence; verify subagent reports yourself."
- **FR-F6** A `deterministic-enforcement` rule declares which markdown rules/profiles have a paired analyzer, keeping the advisory and deterministic layers in sync; profiles span both layers (hook-injected + analyzer-backed where mechanical).

## FR-G — Multi-repo orchestration

- **FR-G1** `orchestrate` (and `init --include-linked`) initializes **every affected repo** with `.dotnet-ai-kit/project.yml` + tooling + the PreToolUse hook, so enforcement fires in every repo. *(Closes the v1 no-op gap.)*
- **FR-G2** `specify`/`orchestrate` projects a `feature-brief.md` (role, required changes, events consumed/produced) into **every** affected repo's `.dotnet-ai-kit/features/NNN/`. *(Closes the awareness gap.)*
- **FR-G3** Implementation runs in dependency order (Command → Query/Processor → Gateway → ControlPanel); feature branches isolate until PR merge; `implement --resume` continues from the failed task.
- **FR-G4** `analyze` validates cross-repo contract consistency (event producer/consumer match, proto client↔server, sequence/idempotency, event-catalogue completeness).
- **FR-G5** `pr` creates one PR per repo with a cross-referenced "Related PRs" block.
- **FR-G6** `status` reports a single multi-repo view from each repo's `linked_from` + `feature-brief.phase`.
- **FR-G7** Secondary repos get a safe branch (`chore/feature/NNN`); dirty working trees are warned and skipped.
- **FR-G8** A **contract test** asserts that after `specify`/`orchestrate`, every repo in the service-map has a `feature-brief.md` with the matching `feature_id` (awareness cannot silently regress).
- **FR-G9** `orchestrate` is sequential/dependency-ordered by default; `--parallel` fans out per-repo work to isolated subagents (opt-in, not a hard dependency on preview orchestration).

## FR-H — Rebuild + expansion coverage

- **FR-H1** All v1 artifacts are rebuilt into the new model; near-duplicate skills are consolidated (`controllers`→`controller-patterns`, `scalar`→`openapi-scalar`, `cqrs-basics`→decision-guide); no-op `when_to_use` fields and the broken `event-catalogue` sample are fixed.
- **FR-H2** CQRS dispatch and mapping are abstracted behind ports (`mediator-abstraction` rule) given MediatR/AutoMapper/MassTransit are now commercial; `mediator-migration` + `messaging-bus-selection` offer free alternatives (Mediator source-gen, Wolverine).
- **FR-H3** New skills are added for Aspire 13.1, Microsoft.Extensions.AI, Minimal APIs/ASP.NET Core 10, Dapr, modern testing (Playwright/Stryker/TUnit), Blazor render modes/`[PersistentState]`, Entra/OpenIddict/passkeys, GraphQL, and the Roslyn analyzer/source-generator (per [23 §5.2](23-v2-artifact-catalog.md)).
- **FR-H4** New agents `aspire-architect` and `ai-engineer` are added; the v1 Cursor fixture moves to `tests/fixtures/`.
- **FR-H5** New rules `mediator-abstraction`, `messaging-bus-selection`, `deterministic-enforcement`, `testing-platform`, `ai-integration` are added.

---

## Non-functional requirements

- **NFR-1 No-network invariant (A-011):** `init`, `check`, `migrate`, `render`, `generate` make zero network calls; enforced by a process-level network-deny acceptance test.
- **NFR-2 Token budgets:** always-on context measured by `/context` + `TiktokenTokenizer`; CI fails on budget regression or a drop in triggering-eval accuracy.
- **NFR-3 Cross-platform:** all CLI behavior and generated files work identically on Windows/macOS/Linux; paths via the FS port; subprocess via list-args, never a shell.
- **NFR-4 AOT-clean:** no reflection-based serialization/validation/DI on the hot path; the tool builds and runs as Native AOT.
- **NFR-5 Performance:** `check` < 10 s; `render` < 2 s; `generate` deterministic and idempotent.
- **NFR-6 Test strategy:** golden-output (Verify) for every projected/generated file; an `Acceptance.Tests` project carrying the language-neutral invariants (NFR-1/2, FR-031 exit codes, SC-001 footprint) as the cross-language gate; analyzer tests; the triggering eval harness.
- **NFR-7 Preserved v1 contracts:** the 8-exit-code `check` contract (FR-031), ≤18-file footprint (SC-001), three-point runtime resolution (SC-003), and manifest/upgrade semantics (sha256 integrity, atomic backup/rollback/rotate) are preserved.
- **NFR-8 Migration:** `migrate` cleans v1 layout artifacts with 3-keep backup rotation; `config.yml` accepts the `ai_tools`→`enabled_hosts` legacy alias on read.

## Success criteria (acceptance)

- **SC-A** `generate` + `git diff --exit-code` is green on a clean checkout (no drift); deleting a generated file and re-running restores it byte-identically.
- **SC-B** After `init` on a Claude project, domain rules exist at `.claude/rules/*.md` with `paths:` (the v1 bug is gone), verified by an acceptance test.
- **SC-C** The Stop-hook gate blocks a simulated "done" claim when `dotnet test` fails, and allows it when green (feature-flow scope).
- **SC-D** The triggering confusion matrix passes: for every consolidated skill, its should-trigger queries fire it and its siblings do not.
- **SC-E** A multi-repo `specify`/`orchestrate` run leaves a matching `feature-brief.md` in every service-map repo (FR-G8) and each secondary repo has `project.yml` (FR-G1).
- **SC-F** The always-on listing fits the budget with all command-skills off-listing; `/context` is within target after consolidation.
- **SC-G** The Acceptance.Tests suite (the cross-language gate) passes against the .NET binary, covering NFR-1/2 and the FR-031/SC-001/SC-003 contracts.

## Traceability

| Area | Decision source |
|---|---|
| Artifact model, projection, .NET stack | [21](21-v2-architecture-blueprint.md), [22](22-v2-project-structure.md) |
| Full artifact list | [23](23-v2-artifact-catalog.md) |
| Selector, gates, token economy, SDD additions, multi-repo | [24](24-v2-selector-gates-lifecycle-multirepo.md) |
| Keep-vs-rebuild evidence (superseded) | [20](20-rewrite-strategy-net10.md) |
| Verified external facts | hooks/skills (code.claude.com), .NET stack (nuget/learn.microsoft.com), licensing (MediatR/MassTransit), Copilot manifest (code.visualstudio.com) — all 2026-05-30 |
