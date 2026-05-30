# dotnet-ai-kit v2 — Build Plan, Locked Decisions & Spec Amendments

**Date:** 2026-05-31 · **Status:** AUTHORITATIVE — this is the current decision record and execution plan.
**Precedence:** Where this doc conflicts with [21](21-v2-architecture-blueprint.md)–[25](25-v2-requirements.md), **this doc wins.** Those docs remain the detailed design/requirements; this one records the decisions made after Codex review and the order we build in.

This is written **before any code** (per the maintainer's instruction). It consolidates: the v1→v2 full-rewrite decision, the answers given this session, the accepted Codex review refinements, and a phased execution plan with per-phase acceptance.

---

## 1. Context that changed the calculus

**v1 was never released.** This moots Codex's top concern (Critical #1/#4: "ship a v1 hotfix for the rule bug before rewriting"). With no users, no live bug to triage, and no migration burden, a clean full rewrite is the right call. The `.NET 10` SDK (**10.0.300**) is installed, so we can build immediately.

---

## 2. Locked build decisions (BD)

| ID | Decision | Rationale |
|---|---|---|
| **BD-1** | **New branch off current HEAD; keep the Python `src/dotnet_ai_kit/` + `tests/` in place as the runnable reference spec.** The .NET solution coexists during the rewrite; Python is removed only once the .NET CLI passes the contract suite. | Nothing is lost mid-rewrite; the v1 behavior stays runnable to diff against. |
| **BD-2** | **Scope = everything** — full projection engine + all 4 host projectors + rebuild of the entire corpus + the ~30 new artifacts. Built in dependency order (§5), not literally simultaneously. | Maintainer's explicit choice ("everything at once"); time is available (pre-release). |
| **BD-3** | **Distribution: framework-dependent `dotnet tool` first; per-RID Native AOT deferred** until the code is trim-warning-clean and serializer choices are proven. | Codex High #5 + Medium; AOT is an optimization, not a launch blocker. **Amends FR-C6.** |

### 2.1 Repository layout during the transition (BD-1 detail)
```
dotnet-ai-kit/
├── src/
│   ├── dotnet_ai_kit/          # Python v1 — KEPT as reference until parity, then removed
│   ├── DotnetAiKit.Core/       # .NET v2 (PascalCase dirs coexist with the Python package)
│   ├── DotnetAiKit.Application/ Hosts/ Infrastructure/ Cli/ Analyzers/
├── tests/                      # Python v1 tests — KEPT as reference (the behavioral spec)
│   └── (… new .NET test projects added alongside, see §5)
├── artifacts/                  # NEW authored source of truth
├── skills/ agents*/ rules/ commands/ profiles/   # v1 artifacts — MIGRATION SOURCE, removed at parity
├── dotnet-ai-kit.slnx          # NEW .NET solution
├── Directory.Build.props  Directory.Packages.props  global.json   # NEW
└── planning/  docs/  issues/
```
**Removal at parity** (a tracked late phase): delete `src/dotnet_ai_kit/`, the Python `tests/`, and the legacy artifact dirs once their content is migrated into `artifacts/` and the .NET contract suite is green.

---

## 3. Accepted Codex refinements (AR) — folded into the plan

Each amends the referenced requirement. These are adopted in addition to the design in 21–25.

| ID | Refinement | Amends |
|---|---|---|
| **AR-1** | **License-light generated code by default** (manual mapping; no commercial packages). MediatR / AutoMapper / MassTransit become **opt-in profiles** with version + license notes in generated READMEs. | FR-H2 |
| **AR-2** | **Host-capability matrix** — a machine-readable table per host (skills, slash commands, agents, rules, hooks, deny/block, path-scoped instructions, bundled resources, packaging) each tagged **GA / Preview / Experimental / Unsupported**. Every projected artifact names the capability it depends on. Add **per-host install smoke tests**. | new FR-I; NFR-6 |
| **AR-3** | **Scope the hard enforcement tiers (T2 PreToolUse-deny, T4 Stop-hook) to Claude**, where the semantics are verified. For Codex/Cursor/Copilot, use explicit fallbacks: Roslyn analyzer + CI gates, generated `/verify`, static rule projection, host-native rule systems. Do **not** claim Stop-level enforcement on hosts that can't block completion. | FR-F2, FR-F4 |
| **AR-4** | **Neutral artifact model** — `Skill`, `Agent`, `Rule`, `Profile`, `Command` are distinct Core types; **the projection decides each host's surface** (skill / slash command / rule / agent prompt / manifest entry). Drop the "everything must be a skill everywhere" framing. | FR-A3; blueprint §3/§6a |
| **AR-5** | **Per-skill resource folders are opt-in** (`scripts/`/`examples/`/`references/`/`assets/`/`evals/` only where the skill needs them), not boilerplate on every skill. | FR-A2 |
| **AR-6** | **Selector eval oracle starts on ambiguous clusters** (mediator, CQRS, eventing, testing, architecture, gateway/control-panel) with curated queries + expected top-k; expand to full per-skill coverage only after the harness proves stable. | FR-E6 |
| **AR-7** | **Add the missing requirement areas:** (a) **trust/security model** for bundled executable scripts (which are runnable, how trusted, never auto-run without consent); (b) **user-owned-file policy** (merge / overwrite / backup / diff-preview rules for `.claude/settings.json`, `AGENTS.md`, `.cursor/rules`, `.github/*`, user edits); (c) **artifact schema versioning** + migration; (d) **release/rollback plan** (FD vs AOT artifacts, RID matrix, upgrade-from-`uv`, rollback if projection output differs); (e) **Windows parity** for hooks/shell commands (PowerShell coverage, not just bash). | new FR-J…FR-N |
| **AR-8** | **Avoid over-abstraction** — keep ports for genuinely volatile concerns (filesystem, process, package discovery, host rendering, external-tool invocation); do **not** wrap simple manifest records and projection functions in service layers until duplication proves the need. | FR-C1 |
| **AR-9** | **Doc/defect hygiene:** command count is **32** everywhere; drop hand-authored exact test counts from strategy docs; carry the **`test_budgets.py` glob defect** (`rules/*.md` → `rules/**/*.md`) forward as a v2 budget contract test. | 24, 20 |
| **AR-10** | Evaluate **forced output styles** as an additional Claude-native rule-delivery channel (per `issues/rule-enforcement-gap/RESEARCH-2`), alongside `.claude/rules` + hooks. | FR-F1 |

### 3.1 Codex recommendations NOT adopted (with rationale)
- **"Ship a v1 hotfix / phase the rewrite behind contracts first."** Not adopted — v1 is unreleased, so there is no live bug to hotfix and no migration burden; the maintainer chose a full rewrite now. *We still build the contract/acceptance suite early (P0–P5) so the rewrite is gated by behavior, not vibes.*
- **"Freeze the corpus; expand later."** Not adopted as a scope cut — the maintainer chose rebuild + expand together. *We still sequence corpus-rebuild (P6) before new-domain expansion (P9) internally, so expansion never blocks a clean core.*

---

## 4. Spec amendments summary (current truth)

- **FR-C6 → ** framework-dependent `dotnet tool` is the launch target; AOT is a later optimization (BD-3, AR-8-adjacent).
- **FR-F (enforcement) → ** four tiers remain, but T2/T4 are **Claude-scoped** with named per-host fallbacks (AR-3); T3 (Roslyn analyzer) and CI are the cross-host deterministic floor.
- **FR-A2/A3 → ** neutral artifact model (AR-4); opt-in resources (AR-5).
- **FR-H2 → ** license-light defaults; commercial packages opt-in (AR-1).
- **New: FR-I** host-capability matrix + smoke tests (AR-2); **FR-J–N** security model, user-file policy, schema versioning, release/rollback, Windows parity (AR-7).
- **Command count: 32** (D1–D32 in FR-D; the `fix` command is in).

---

## 5. Phased execution plan (the build order for the full scope)

Scope is "everything," but it is built in dependency order with a working, tested system at each phase boundary. Each phase has an acceptance gate tied to the success criteria in [25 §SC](25-v2-requirements.md).

| Phase | Build | Acceptance gate |
|---|---|---|
| **P0 Foundation** | rewrite branch · `dotnet-ai-kit.slnx` · 6 projects + `Analyzers` (netstandard2.0) + test projects · `Directory.Build.props`/`Directory.Packages.props` (central pkg mgmt) · `global.json` (pin 10.0.300) · `.editorconfig` · CI skeleton (build + test + `generate` git-diff gate) · `artifacts/` dir tree | empty solution builds; CI green on a clean checkout |
| **P1 Core domain** | `Skill`/`Agent`/`Rule`/`Profile`/`Command`/`Fragment`/`Manifest` types · value objects · `ArtifactGraph` · `DescriptionStandard` · `SubstitutionEngine` (AR-4 neutral model) | `Core.Tests` green; graph build fails on a broken edge (FR-A6) |
| **P2 Ports + Infrastructure** | ports (`IFileSystem`/`IGitClient`/`IProcessRunner`/`IArtifactSerializer`/`ITokenizer`/`IConsoleReporter`) + impls (`PhysicalFileSystem`, `YamlFrontmatterParser`, `JsonArtifactSerializer`, `TiktokenTokenizer`, `FileSystemArtifactRepository`) | frontmatter round-trips; `Application.Tests` with fakes green |
| **P3 Projection engine + Claude projector + `generate`** | `IHostAdapter`/`ProjectionEngine` · `ClaudeProjector` · `ClaudeManifestWriter` · `generate` use-case · CI git-diff gate | **SC-A** on a thin slice (≈5 artifacts); golden-output (Verify) tests |
| **P4 Remaining host projectors** | `Codex`/`Cursor`/`Copilot` projectors + manifest writers · **host-capability matrix (AR-2)** · per-host install smoke tests | all 4 hosts golden-tested; smoke tests pass where the host CLI is present |
| **P5 CLI verbs + contract suite** | `init`/`check`/`render`/`migrate`/`configure`/`detect`/`upgrade` · `SpectreConsoleReporter` · `Acceptance.Tests` (no-network, FR-031 exit codes, SC-001 footprint, schema validation) | **SC-B**, **SC-G**; NFR-1/5/7 |
| **P6 Corpus rebuild** | migrate all v1 artifacts into `artifacts/` (consolidate dups, fix `when_to_use` no-op + the `event-catalogue` sample) · author the 32 command-skills (AR-5 opt-in resources) | every artifact projects; budget within target (**SC-F**) |
| **P7 Enforcement** | `Dotnet.Ai.Kit.Analyzers` NuGet (T3) · PreToolUse/Stop hooks (T1/T2/T4, **Claude-scoped per AR-3**) + per-host fallbacks · `deterministic-enforcement` rule · forced-output-style channel (AR-10) | analyzer tests; **SC-C** (Stop-hook gate); rule delivery verified |
| **P8 Multi-repo** | `orchestrate` · `feature-brief` projection to every affected repo · cross-repo `analyze` · awareness **contract test** | **SC-E**; FR-G1/G2/G8 |
| **P9 Expansion** | ~30 new skills (Aspire/AI/MinimalAPI/Dapr/testing/Blazor/auth/GraphQL/Roslyn) · `aspire-architect` + `ai-engineer` agents · 5 new rules · license-light migration skills (AR-1) | new artifacts project + pass the triggering oracle (AR-6) |
| **P10 Selector oracle + distribution** | triggering eval harness (clusters→broad, AR-6) wired into CI · framework-dependent `dotnet tool` packaging · `marketplace.json` (project-scope, pinned) | **SC-D**; `dotnet tool install` smoke; **then** parity-removal of Python (BD-1) |

**Cross-cutting (every phase):** cross-platform discipline (NFR-3, Windows parity AR-7e), the user-owned-file policy (AR-7b), and the security model for bundled scripts (AR-7a) are honored as code is written, not bolted on.

---

## 6. Work-breakdown summary

- **New .NET code:** 6 src projects + 1 analyzer project + ~6 test projects (~per [22 §5–6](22-v2-project-structure.md)).
- **Artifacts to (re)author:** 32 command-skills · 15 agents · 21 rules · 12 profiles · ~130 rebuilt + ~30 new skills (per [23](23-v2-artifact-catalog.md)).
- **Host outputs:** Claude / Codex / Cursor / Copilot projections + 3 plugin manifests from one descriptor + `marketplace.json`.
- **Tests/gates:** golden-output per projected file · `Acceptance.Tests` (the cross-host invariant gate) · analyzer tests · triggering oracle · CI `generate` git-diff gate.

## 7. Definition of done (v2.0)

All success criteria in [25 §SC](25-v2-requirements.md) pass (SC-A…SC-G), the host-capability matrix is published with smoke tests, generated code is license-light by default, the Python v1 is removed, and `dotnet tool install` produces a working CLI on Windows/macOS/Linux.

---

*Nothing in this plan is built yet. Next action after approval: P0 (branch + solution skeleton).*
