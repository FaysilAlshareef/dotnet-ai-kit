# dotnet-ai-kit v2 — Post-022 Fidelity & Defect Audit

**Date:** 2026-05-31 · **Status:** AUDIT — findings only, **nothing executed** (maintainer chose report-only).
**Branch at audit:** `022-v2-fidelity-gaps` @ `7419c7e` (tree clean). **Build:** `dotnet build dotnet-ai-kit.slnx -warnaserror` → **exit 0**.
**Method:** audited the codebase against the **specs' own definition-of-done** ([020](../specs/020-v2-net10-rewrite/) engine · [021](../specs/021-v2-completion/) completion · [022](../specs/022-v2-fidelity-gaps/spec.md) fidelity-gaps — all implemented), **not** the pre-code aspirational plan in [20](20-rewrite-strategy-net10.md)–[26](26-v2-build-plan-and-decisions.md). Produced by direct probes + two independent deep sweeps (artifact content-quality; `src/` refactoring/stubs). Every finding carries `file:line` evidence.

> **Why a fresh audit when 022 already closed the planning-vs-code gaps?** 022 *was* a planning-vs-code scan and it shipped. This audit looks for what remains **past** that done-line: (a) content/code **defects** inside artifacts the count-parity gates can't see, and (b) `src/` defects/refactors. The headline result: the engine and corpus are **structurally complete and green** — the real work is a small, concentrated defect + refactor set, and one planning **overclaim** worth recording.

---

## 1. Executive summary

- **Structurally complete, green, no dangling references.** 32 commands · 15 agents · 21 rules · 12 profiles · 182 skills · 16 knowledge docs · 4 host projectors; build `-warnaserror` 0/0; the ArtifactGraph broken-edge gate holds (zero dangling `(use X)`/`metadata.agent`/related-skill pointers found across the corpus).
- **One genuine BROKEN sample still ships** — and **planning claimed it was fixed.** `event-catalogue` calls `Activator.CreateInstance` on positional records → `MissingMethodException`. [25 FR-H1](25-v2-requirements.md) and [26 AR-9](26-v2-build-plan-and-decisions.md) assert "the broken `event-catalogue` sample is fixed." It is not (see §6 — process note).
- **The sharpest `src/` defect is a *misleading guarantee*:** `ManifestIntegrityService` (SHA-256, the NFR-7 preserved-contract) is implemented + unit-tested but **never wired into production**; `CheckService`'s exit-code-14 check is *named* "manifest-integrity" yet only does `FileExists`.
- **The kit under-dogfoods its own conventions:** ~15/21 rules and ~6/15 agents predate the description standard; 3 domain rules use JIT-defeating `**/*.cs` globs; the CQRS cluster still pushes MediatR-as-default against the kit's own `mediator-abstraction` rule.
- **Most "plan" items not in the repo are deferred *by decision*, not missing** (Native-AOT/BD-3, ≥20-queries eval/AR-6, Codex-Cursor plugin-load parity, live in-session hook firing, opt-in resources/AR-5, empty `fragments/`). Listed in §5 so none reads as a silent gap.

---

## 2. Scorecard (plan target → actual)

| Artifact | Target (23/26) | Actual | |
|---|---|---|---|
| Commands | 32 | 32 | ✅ |
| Agents | 15 | 15 | ✅ |
| Rules | 21 (5 univ + 16 dom) | 21 | ✅ |
| Profiles | 12 | 12 | ✅ |
| Skills | ~160 | 182 | ✅ |
| Knowledge | — | 16 | ✅ |
| `src/` projects | 6 | 7 (analyzer/code-fix split for RS1038) | ✅ |
| Test projects | 7 | 7 | ✅ |
| Build hosts | 4 | 4 (claude/codex/cursor/copilot) | ✅ |

Count parity is **not** the question; §3–§4 are. (Count parity once masked the missing `blazor-hybrid` — 022 closed that.)

---

## 3. Bucket A — Defects to fix (wrong/broken/misleading regardless of any plan)

### 3.1 Artifacts (content/code correctness)

| # | `file:line` | Finding | Severity | One-line fix |
|---|---|---|---|---|
| A1 | [event-catalogue/SKILL.md:187](../artifacts/skills/microservice/event-catalogue/SKILL.md) | `Activator.CreateInstance(type, nonPublic: true)` on **positional records** (no parameterless ctor) → `MissingMethodException`. Breaks the worked example **and** the test the skill tells readers to add. *(directly verified)* | **BROKEN** | `RuntimeHelpers.GetUninitializedObject(type)` to read the constant `Type` without a ctor. |
| A2 | [aggregate-design/SKILL.md:45,90](../artifacts/skills/microservice/command/aggregate-design/SKILL.md) · [event-sourcing-flow.md:188](../artifacts/knowledge/event-sourcing-flow.md) | Prose says it invokes "the private parameterless constructor," but the aggregate declares none → implicit **public** ctor, contradicting the skill's own "no public constructors / private setters" rule (`:204`, `:17`). *(sweep-reported)* | MISLEADING | Add `private Order() { }` to the concrete aggregate. |
| A3 | [cqrs/mediatr-handlers/SKILL.md:219](../artifacts/skills/cqrs/mediatr-handlers/SKILL.md) · [command-generator/SKILL.md:173](../artifacts/skills/cqrs/command-generator/SKILL.md) (+ pipeline-behaviors/notification-handlers/request-response, weaker) | MediatR presented as the default dispatch with no commercial-license caveat and no pointer to `mediator-abstraction`/`mediator-migration` — contradicts the kit's own always-on rule. *(sweep-reported)* | MISLEADING | Add a one-line license note + "abstract behind `ISender`; see `mediator-migration`." |
| A4 | [mapping-strategies/SKILL.md:3](../artifacts/skills/core/mapping-strategies/SKILL.md) | Description lists AutoMapper as a co-equal option though the body correctly warns it's now commercial. *(sweep-reported)* | MINOR | Drop/qualify AutoMapper in the description. |
| A5 | `mediator-abstraction`, `messaging-bus-selection`, `ai-integration` (all `paths: "**/*.cs"`) | JIT-defeating globs: each applies to a narrow slice (dispatch / messaging / AI) but loads into **every** C# edit → always-on token bloat + a false "JIT" story. `error-handling`/`performance` are correctly broad; `deterministic-enforcement` is a meta-registry (semantically mis-scoped but token-cheap). *(globs directly verified; verdicts from sweep)* | MISLEADING | Narrow the 3 globs to handler/messaging/AI-feature paths. |
| A6 | [rules/domain/testing.md:3,18,44](../artifacts/rules/domain/testing.md) · [performance-testing/SKILL.md:27](../artifacts/skills/testing/performance-testing/SKILL.md) · [testing-patterns.md:493](../artifacts/knowledge/testing-patterns.md) | Staleness: `testing.md` still carries v1-era "Python test patterns"; `RuntimeMoniker.Net90` in a .NET-10-pinned kit. *(sweep-reported)* | MINOR | Drop the Python section (or justify polyglot); bump moniker when available. |

### 3.2 CLI / `src/`

| # | `file:line` | Finding | Severity | Recommendation |
|---|---|---|---|---|
| A7 | `ManifestIntegrityService` (Infrastructure) + [CheckService] exit-code-14 | SHA-256 integrity service is implemented + unit-tested but **called nowhere in production**; the exit-14 check is *named* "manifest-integrity" but only does `FileExists`. **NFR-7 (preserved v1 contract) is unrealized and the check name misleads.** *(sweep-reported, strong evidence)* | **DEFECT/GAP** | Wire it into `check` (compute+store+verify a hash on the per-solution `manifest.json`), or rename the check to "manifest-present" and record NFR-7 as deferred. |
| A8 | no fitness test anywhere | The kit's **headline clean-arch invariant has no automated guard** — nothing fails the build if Core gains a dep or Application references a host. (Refs are correct by hand today.) *(verified: no NetArchTest / reflection check in tests/)* | GAP | Add one `Acceptance.Tests` fitness test: Core references no `DotnetAiKit.*`-but-Core and no third-party; Application references no Hosts/Infrastructure/Cli/Spectre. |
| A9 | [CompositionRoot.cs:55](../src/DotnetAiKit.Cli/CompositionRoot.cs) | `NotSupportedException("init for host '{host}' is not implemented yet.")` — the **throw is correct** (only Claude has a per-solution footprint; Codex/Cursor are plugin-native, Copilot render-only) but "not implemented yet" mislabels intentional non-applicability. *(directly verified)* | DEFECT (wording) | Reword: "init has no per-solution footprint for plugin-native/render-only host '{host}' (Claude only)." |

---

## 4. Bucket B — Genuine, but a small decision first

| # | `file:line` | Finding | Decision needed |
|---|---|---|---|
| B1 | [GitCliClient.cs](../src/DotnetAiKit.Infrastructure/GitCliClient.cs) + `IGitClient` | **Dead code** — referenced nowhere (not Cli, not a use-case, not tests). Meanwhile `OrchestrateService`'s **FR-G7 dirty-tree skip is only a missing-dir check, not a git-dirty check** — so FR-G7 branch-safety is partially unimplemented. *(sweep-reported, strong)* | Delete `IGitClient`/`GitCliClient`, **or** wire it into Orchestrate's dirty-tree skip to actually deliver FR-G7. |
| B2 | `OrchestrateService` + `Program.cs`/`CompositionRoot` | FR-G multi-repo conductor is implemented + tested (`MultiRepoAwarenessTests`) but exposed **only** as a command-skill, not a CLI verb. Plausibly by-design (the documented verbs are `init·check·render·generate·detect·migrate·configure·upgrade`). | Confirm no user-reachable `orchestrate` binary surface is required by FR-G/SC-E. |
| B3 | ~15/21 rules, ~6/15 agents, ~20 skills | Grandfathered descriptions predate the kit's own standard (no "Use when…/Do NOT use… (use X)"); ~20 skills have self-referential triggers. CI gates only *new* artifacts, so allowed — but the kit isn't dogfooding its standard. *(sweep estimate)* | Bring legacy descriptions up to standard (and consider gating *all* artifacts, not just new). |
| B4 | `CLAUDE.md` stack claim | "System.Text.Json **source-gen**" is unrealized — no `JsonSerializerContext` exists (JSON goes through AOT-safe `JsonNode` DOM). Not a runtime defect, but inaccurate and relevant to the deferred AOT goal (NFR-4). *(verified: zero `[JsonSerializable]` in src)* | Add a (near-empty) `JsonSerializerContext`, or correct the stack description. |

**Low-risk refactors (byte-stable, no behavior change), top of list:**
- **R1** [ClaudeProjector.cs:73-119](../src/DotnetAiKit.Hosts/Claude/ClaudeProjector.cs) — private nested `FrontmatterBuilder` duplicates the shared [FrontmatterWriter.cs](../src/DotnetAiKit.Hosts/FrontmatterWriter.cs) the other 3 projectors use (~45 dead lines). Delete and reuse.
- **R2** The identical YAML-quote escaper (`v.Replace("\\","\\\\").Replace("\"","\\\"")`) is copy-pasted ~6× across projectors/adapters/serializer/OrchestrateService. Extract one shared `YamlScalar.Quote`.
- **R3** No shared `PluginNativeHostBase` across the 4 projectors despite a clearly shared skill+resource-emission skeleton — the structural dedup win [22 §5.3](22-v2-project-structure.md) anticipated.
- **R4** [FileSystemArtifactRepository.cs:20,248](../src/DotnetAiKit.Infrastructure/FileSystemArtifactRepository.cs) news up its own `IDeserializer` for `manifest.yml` while also injecting `IArtifactSerializer` — two YamlDotNet code paths; route both through the port.
- **R5** Minor: `OrchestrateService`/`ConfigureService`/`MigrateService` always return `Ok=true, Errors=[]` (failure channel structurally present, never populated) — populate on real failures or drop the unused field.

---

## 5. Bucket C — Deferred *by decision*, not missing (recorded so nothing reads as a silent gap)

| Item | Authority |
|---|---|
| Live in-session PreToolUse/Stop firing test | 021 named headless ceiling; [022 spec §Out of scope](../specs/022-v2-fidelity-gaps/spec.md) — interactive-only |
| Full ≥20-queries/skill triggering eval (clusters-first only today) | AR-6 |
| Codex / Cursor plugin-**load** parity (different discovery model; structure-only check today) | 022 follow-on / FR-022-18 |
| Native-AOT packaging + per-RID release/rollback matrix | BD-3 |
| Sparse bundled resources; `references/` = 0 | AR-5 (opt-in; only FR-D33 + `add-*` + eval clusters required) |
| `fragments/` empty (`.gitkeep` only) | **Confirmed not needed** — command-skill `## Dry-Run Behavior` sections are command-specific prose, not copy-paste boilerplate; no FR-012-style duplication to extract |

---

## 6. Process note — a planning overclaim to retire

[25 FR-H1](25-v2-requirements.md) and [26 §3 AR-9](26-v2-build-plan-and-decisions.md) state the broken `event-catalogue` reflection sample **is fixed**. It is not (finding A1, directly verified at `event-catalogue/SKILL.md:187`). Count-parity gates and the drift gate can't catch a logically-broken-but-syntactically-valid sample. **Recommendation:** when A1 is fixed, add a regression guard (the Roslyn-parse check from FR-022-02 won't catch it — it's a *semantic* runtime bug; a targeted unit test or a doc-sample compile-and-run check is needed), and correct the "fixed" assertions in 25/26.

---

## 7. Suggested sequencing (when execution is authorized)

Each lands as an independently-testable green increment (build `-warnaserror` 0/0 · `dotnet test` · `dotnet format` · `generate --check` drift-clean):

1. **A1, A2** — correctness bugs in shipped samples (regenerate `build/`; re-accept goldens). Add the A1 regression guard (§6).
2. **A7** — wire `ManifestIntegrityService` into `check` (or rename + mark NFR-7 deferred). Closes the only misleading *guarantee*.
3. **A8** — layering fitness test. Cheap insurance for the headline invariant.
4. **A5, A3, A4, A9** — narrow the 3 globs; add MediatR caveats; description/wording fixes. (Globs change projected `.mdc`/rule output → re-accept goldens + drift.)
5. **B1, R1–R4** — resolve `IGitClient`; the byte-stable refactors.
6. **B3, A6, B4** — dogfood descriptions; staleness; doc-claim accuracy.

**Acceptance for the whole set:** all gates above stay green; `claude plugin validate build/claude --strict` + `build --strict` still pass; planning 25/26 "fixed" claims reconciled.

---

*Audit complete; no source changed. The corpus + engine are healthy — this is targeted cleanup, not a rescue.*
