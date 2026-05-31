# Feature Specification: dotnet-ai-kit v2 — Planning-Fidelity Gaps (resources, evals, golden tests, hook execution, user-file policy)

**Feature Branch**: `022-v2-fidelity-gaps`
**Created**: 2026-05-31
**Status**: Draft
**Input**: User description: "Scan planning/20–26 + HANDOFF against the codebase, find features specified in planning that don't exist (or are stubs) in the code — e.g. skills are still just `SKILL.md` with no bundled resources — collect them all, and open a new spec to work on them."

## Overview

Features 020 (engine) and 021 (completion) delivered the .NET 10 engine, the full 245-artifact corpus, the four host projectors, the 8 CLI verbs + `hook` verb, all four planning/24 enforcement tiers (wired + the Claude plugin verified loadable via `claude plugin validate`), Python removal, and green gates (build `-warnaserror` 0/0, 112 tests, drift-clean).

This feature closes the **remaining fidelity gaps** between the planning baseline (`planning/20`–`26`; **26 authoritative**) and the codebase — capabilities that are *specified but absent or stubbed*. A fresh planning-vs-code scan (2026-05-31) found the corpus is **structurally complete but resource-empty**, several gates are **stubs**, and a few wired features **cannot actually run**:

- **0 of 181 skills** and **0 of 32 command-skills** carry any bundled resource (`scripts/`, `examples/`, `references/`, `assets/`, `evals/`) — every skill is a bare `SKILL.md`. The Core `Skill` model already has `SkillResourceSet Resources` and a `SchemaVersion`; the corpus simply never populates them. (FR-A2, FR-D33, planning/23 §368.)
- **0 `evals/cases.jsonl`** exist and the triggering oracle is 3 hard-coded lexical `InlineData` cases — far below the FR-E6 design (cluster-curated queries + a confusion matrix). (FR-E6, AR-6.)
- **0 Verify golden-output files** (`*.verified.*`) exist, though `Verify.Xunit` is referenced — NFR-6 ("golden-output for every projected/generated file") is unmet.
- The enforcement hooks call `dotnet-ai hook …`, but bare `dotnet-ai` resolves to a **stale v1 Python shim**, not the (un-installed) v2 .NET tool — so the hooks load and validate but **error on fire**. *(Verified firsthand: `Get-Command dotnet-ai` → `…\Python312\Scripts\dotnet-ai.exe` (v1 pip launcher, v0.0.0.0); `dotnet tool list -g` shows the v2 tool is not installed.)*
- One named artifact is **absent**: `blazor-hybrid` (planning/23 §5.2, marked "low priority") is the only one of the 29 named NEW skills not in the corpus — count parity (181 ≥ 160) masked it. (The 12 profiles, the other 28 NEW skills, and the 🔀 merges `controllers→controller-patterns`/`scalar→openapi-scalar`/`cqrs-basics` are all correct.)
- `init` **overwrites** `.claude/settings.json` with a bare schema; the `HostWriteResult.Preserved/PendingConsent/ForceRendered` policy fields are **never populated** — the FR-K user-owned-file policy is unimplemented.
- T2's **`prompt` (Haiku) judgment hook** (FR-F2) and the **forced-output-style** rule-delivery channel (AR-10) are not implemented; **per-host install smoke tests** (FR-I/AR-2) do not exist; **Codex/Cursor plugin loadability** is unverified (only Claude was validated in 021).

The engine, the full corpus's *presence*, and the enforcement *wiring* are the constraints that keep this honest: every change must keep the corpus graph-consistent, project to all four hosts, stay drift-clean, and keep all gates green.

## Clarifications

### Session 2026-05-31

- Q: planning/23 §368 says "every skill ships the resource model," but 26/AR-5 says resources are **opt-in** (only where the skill needs them). Which governs? → A: **26/AR-5 wins (authoritative).** Author resources where they add value — **firmly** the FR-D33 set (the 4 new command-skills bundle workflow `scripts/`+`examples/`), the code-gen command-skills (`add-*` bundle compilable `examples/` / template `assets/`), and the ambiguous-cluster skills that need `evals/` — **not** blanket boilerplate on all 181. The bare-MD default is acceptable for a skill whose `SKILL.md` body is self-sufficient.
- Q: How far does the triggering eval go this feature? → A: **AR-6 scope** — author `evals/cases.jsonl` (curated queries + expected top-k) for the ambiguous clusters (mediator, CQRS, eventing, testing, architecture, gateway/control-panel) and wire a confusion-matrix gate into CI; full ≥20-queries/skill coverage stays a later follow-on. The lexical oracle is replaced/augmented by the authored cases.
- Q: How is the `dotnet-ai` hook-execution gap fixed — change the hook command, or fix install? → A: **Require the v2 `dotnet-ai` global tool (it IS the backend; a plugin cannot portably carry the .NET binary), and harden resolution: (1) `init`/`check` detect a shadowing stale shim and warn with the fix, (2) the hook fails *safe* if the backend is unresolved (no spurious block), (3) the install docs make the dependency explicit and the smoke test enforces it.** The plugin-root-relative-launcher alternative is rejected in `research.md` (it would have to bundle the runtime/binary). Recorded below as a clarify decision.

### Session 2026-05-31 (clarify)

- Q: Hook-launcher mechanism (resolves the FR-022-10 `[NEEDS CLARIFICATION]`)? → A: **Require the global v2 `dotnet-ai` tool + shadow-detection in `init`/`check` + fail-safe hook + smoke-test enforcement** (not a bundled plugin-root launcher; rationale + alternatives in `research.md`). FR-022-10 updated accordingly.
- Q: Resource depth for `add-*` code-gen skills — one canonical example or a set? → A: **One canonical, compilable C# `examples/` per `add-*` skill** (minimal-but-real per AR-5), plus template `assets/` only where the generator fills a template. Breadth is a later follow-on.
- Q: How is the confusion-matrix gate scored when eval cases are lexical (no live LLM here)? → A: **Deterministic top-k lexical scoring over authored `cases.jsonl`** (the existing oracle approach, scaled to the cluster cases); a live-LLM eval stays a follow-on (AR-6). The gate asserts correct-fires + siblings-silent on the authored cases.
- Q: Verify golden scope confirmed? → A: **One golden per artifact-type × host + each manifest/marketplace/hooks/AGENTS/copilot-instructions** (shape coverage), not 834 per-file baselines (already in Session 2026-05-31).
- Q: Does this feature include the *live in-session* hook-firing test that 021 named as the headless ceiling? → A: **No.** That still requires an interactive Claude instance; this feature makes the hooks *runnable* (correct tool resolution + smoke validation), and a live trigger remains an interactive manual check.
- Q: Scope of golden-output (Verify) tests — every one of 834 generated files, or representative? → A: **Representative-but-complete by shape**: at least one golden per artifact-type × host (skill/agent/rule/command/manifest/hooks/AGENTS.md/copilot-instructions), plus the marketplace + plugin manifests, so any projection-shape regression is caught; not 834 individual baselines.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Skills carry the bundled resources their value requires (Priority: P1)

A skill author opens a code-gen or workflow skill and finds it ships more than prose: the `add-*` command-skills bundle compilable C# `examples/` (and template `assets/`), the 4 new SDD command-skills (`constitution`, `checklist`, `fix`, `release`) bundle their workflow `scripts/`, and ambiguous-cluster skills carry `evals/`. The projector copies each skill's resource set into every host's skill directory, and the trust model governs the executable ones.

**Why this priority**: This is the headline gap the maintainer named ("skills still just md file"). Resources are the substance that makes skills more than documentation; the engine already models them (`SkillResourceSet`) but the corpus is empty.

**Independent Test**: Pick the FR-D33 set + the `add-*` skills; verify each has the required resource subdirs with real content; run `generate` and confirm the resources appear under `build/<host>/skills/<name>/`; confirm a corpus-integrity test asserts the required resource set per skill-kind.

**Acceptance Scenarios**:

1. **Given** the `constitution`/`checklist`/`fix`/`release` command-skills, **When** the corpus loads, **Then** each exposes a non-empty `scripts/` (and `examples/` where applicable) in its `SkillResourceSet` (FR-D33).
2. **Given** an `add-*` code-gen command-skill, **When** projected, **Then** its compilable `examples/` (and/or template `assets/`) are copied into each host's skill dir byte-identically and `generate --check` stays drift-clean.
3. **Given** a skill with an executable `scripts/` resource, **When** it is projected/installed, **Then** the script is marked per the trust model (never auto-run without consent) (FR-J).

---

### User Story 2 - The enforcement hooks actually run when fired (Priority: P1)

With the plugin installed, a Write/Edit triggers the PreToolUse hook and a Stop triggers the gate, and the `dotnet-ai hook …` command **resolves to the v2 tool and runs** — not to a stale v1 Python shim that errors.

**Why this priority**: 021 wired all four tiers and proved the plugin/hooks.json load via `claude plugin validate`, but a separate scan found bare `dotnet-ai` on PATH resolves to a broken v1 shim, so the hooks would fail at fire time. A wired-but-unrunnable hook is not delivered enforcement.

**Independent Test**: From a clean environment, install/enable the plugin, invoke the exact `command` string the generated `hooks.json` uses, and confirm it executes the v2 hook backend (emits valid hook protocol) rather than erroring on the shim.

**Acceptance Scenarios**:

1. **Given** the generated `hooks.json` command string, **When** it is executed with a PreToolUse payload on stdin, **Then** the v2 backend runs and emits valid protocol (no "command not found" / Python shim error).
2. **Given** a host without the v2 tool globally installed, **When** the hook fires, **Then** it still resolves the backend via the documented mechanism (plugin-root-relative launcher or equivalent) — or the install guide makes the dependency explicit and the smoke test enforces it.

---

### User Story 3 - Triggering selection is gated by authored eval cases, not a 3-line stub (Priority: P2)

A maintainer changing a skill description runs the triggering harness; it loads authored `evals/cases.jsonl` for the ambiguous clusters and a confusion matrix confirms the correct skill fires and its siblings stay silent, failing CI on a regression.

**Why this priority**: FR-E6/SC-D is the guarantee that the token-frugal selector actually selects. Today it is a 3-case lexical placeholder; description edits can silently regress selection.

**Independent Test**: Add `evals/cases.jsonl` to the cluster skills; run the harness over them; confirm the matrix passes and that flipping a description to collide with a sibling makes it fail.

**Acceptance Scenarios**:

1. **Given** cluster skills with `evals/cases.jsonl`, **When** the harness runs, **Then** every should-trigger query selects its skill and no sibling (SC-D).
2. **Given** a description edited to collide with a sibling, **When** CI runs the matrix, **Then** it fails.

---

### User Story 4 - Every projection shape has a golden-output baseline (Priority: P2)

A change to any projector is caught by a Verify golden test: the emitted shape for each artifact-type × host (plus manifests, marketplace, hooks.json, AGENTS.md, copilot-instructions) is pinned, so an unintended format change turns a test red, not just the drift gate.

**Why this priority**: NFR-6 mandates golden-output for generated files; today there are zero `*.verified.*` baselines, so projection-shape regressions rely solely on the drift gate (which only catches changes against the committed `build/`, not intent).

**Independent Test**: Add Verify baselines for each shape; alter a projector's frontmatter ordering and confirm the golden test fails independently of the drift gate.

**Acceptance Scenarios**:

1. **Given** the projectors, **When** the Verify suite runs, **Then** each artifact-type × host shape (+ manifests/marketplace/hooks/AGENTS/copilot-instructions) has a passing `*.verified.*` baseline.
2. **Given** a deliberate projector format change, **When** the suite runs, **Then** the corresponding golden test fails.

---

### User Story 5 - User-owned files are merged/backed-up/consented, never silently overwritten (Priority: P2)

When `init`/`upgrade` touches a user-owned file (`.claude/settings.json`, `AGENTS.md`, `.cursor/rules`, `.github/*`), the tool merges or backs up + diff-previews + asks consent rather than clobbering it; the `HostWriteResult` reports `Preserved`/`ForceRendered`/`PendingConsent` accurately.

**Why this priority**: FR-K/AR-7b is a named requirement; today `ClaudeHostAdapter` overwrites `.claude/settings.json` with a bare schema and the policy fields are never populated — a real risk to a user's existing settings.

**Independent Test**: Pre-create a `.claude/settings.json` with user content, run `init`, and confirm the content is preserved/merged (or backed up with a diff-preview) and reported in `HostWriteResult`.

**Acceptance Scenarios**:

1. **Given** an existing user-edited `.claude/settings.json`, **When** `init` runs, **Then** the user content is preserved/merged (not clobbered) and the action is reported as `Preserved`/`PendingConsent`.
2. **Given** a managed file with no user edits, **When** `init` runs, **Then** it is written/refreshed and reported as written.

---

### User Story 6 - The remaining enforcement channels are implemented (Priority: P3)

The T2 PreToolUse `prompt` (Haiku) hook handles judgment-call violations the analyzer can't (FR-F2), and a forced-output-style channel provides an additional Claude-native rule-delivery path (AR-10), complementing the wired command-deny + Stop gate.

**Why this priority**: The deterministic floor (analyzer + command-deny + Stop) is delivered; these add the judgment layer and an extra delivery channel called out in planning, but the core enforcement already functions without them.

**Independent Test**: Configure the `prompt` hook and confirm a judgment-class violation is denied with a reason; generate the output-style artifact and confirm it projects.

**Acceptance Scenarios**:

1. **Given** a judgment-class change the analyzer cannot catch, **When** the `prompt` hook evaluates it, **Then** it can return a deny with a reason.
2. **Given** the forced-output-style channel, **When** the corpus projects, **Then** the output-style artifact is emitted for Claude.

---

### User Story 7 - Per-host install + loadability is smoke-tested in CI (Priority: P3)

The host-capability matrix (already in Core) is backed by per-host install smoke tests: Claude plugin + marketplace validate under `claude plugin validate --strict` (codified from 021's manual run), and Codex/Cursor loadability is verified or honestly marked per their own discovery model.

**Why this priority**: FR-I/AR-2 calls for install smoke tests; 021 validated the Claude plugin manually but nothing codifies it, and Codex/Cursor loadability (different mechanism — planning/21: Codex `.agents/skills/`, Cursor own path) is unverified.

**Independent Test**: A smoke test runs `claude plugin validate build/claude --strict` + `build --strict`; Codex/Cursor have a structural check or a documented, tracked limitation.

**Acceptance Scenarios**:

1. **Given** generated `build/`, **When** the smoke test runs, **Then** the Claude plugin + marketplace pass `claude plugin validate --strict`.
2. **Given** the Codex/Cursor outputs, **When** the smoke test runs, **Then** their loadability is asserted against each host's documented discovery (or the gap is recorded with the `build/codex/skills` vs `.agents/skills` tension named).

### Edge Cases

- A skill declares a resource subdir that is empty or references a missing file → corpus load fails with a clear broken-resource error (mirrors the broken-edge gate).
- A bundled script lacks `.ps1`/`.sh` siblings on the host OS → the trust model / launcher degrades gracefully (FR-J, NFR-3 Windows parity AR-7e).
- `init` encounters a `.claude/settings.json` that is invalid JSON → back up + warn, never crash or silently discard.
- The v2 tool is genuinely absent and no plugin-root launcher exists → the hook fails *safe* (no block / clear message), never wedging the session.
- A golden baseline drifts because of an intentional format change → the failing Verify test is the signal to re-accept the baseline in the same PR.

## Requirements *(mandatory)*

### Functional Requirements

**Resources (FR-A2 / FR-D33 / AR-5 / planning/23 §368)**
- **FR-022-01**: The 4 new command-skills (`constitution`, `checklist`, `fix`, `release`) MUST each bundle their workflow `scripts/` (and `examples/` where the workflow produces artifacts), populated into `SkillResourceSet`.
- **FR-022-02**: The `add-*` code-gen command-skills MUST bundle compilable C# `examples/` and/or template `assets/` representing what they generate.
- **FR-022-03**: Resource authoring is opt-in per AR-5; a skill whose `SKILL.md` is self-sufficient MAY remain resource-free, but the corpus-integrity test MUST assert the required resource set for the FR-022-01/02 skill kinds.
- **FR-022-04**: The projectors MUST copy each skill's resource set into every host's skill directory, byte-stable, and `generate --check` MUST stay drift-clean.
- **FR-022-05 (FR-J)**: A trust/security model MUST govern bundled executable scripts — declared, never auto-run without consent, with provenance recorded; cross-platform (`.py` default + `.ps1`/`.sh` siblings, NFR-3).

**Eval harness (FR-E6 / AR-6)**
- **FR-022-06**: Ambiguous-cluster skills MUST carry `evals/cases.jsonl` (curated queries + expected top-k).
- **FR-022-07**: The triggering harness MUST run those cases as a confusion matrix gate in CI (correct skill fires; siblings silent; SC-D), replacing/augmenting the lexical stub.

**Golden output (NFR-6)**
- **FR-022-08**: A Verify golden-output baseline MUST exist for each artifact-type × host shape, plus the plugin manifests, `marketplace.json`, `hooks.json`, `AGENTS.md`, and `copilot-instructions.md`.
- **FR-022-09**: A deliberate projector format change MUST fail its golden test independently of the drift gate.

**Hook execution (memory: dotnet-ai shim; FR-F)**
- **FR-022-10**: The generated `hooks.json` command MUST resolve to the v2 hook backend (the global `dotnet-ai` tool) at fire time, NOT to a stale v1 `dotnet-ai` Python shim. `init`/`check` MUST detect a shadowing shim (a `dotnet-ai` on PATH that is not the v2 tool) and warn with the remediation; the install docs MUST make the v2-tool dependency explicit.
- **FR-022-11**: A smoke test MUST execute the generated hook command with a sample payload and assert valid hook-protocol output (proving runnability, not just discovery).
- **FR-022-12**: When the backend cannot be resolved, the hook MUST fail safe (no spurious block, clear message), never wedging the session.

**User-owned-file policy (FR-K / AR-7b)**
- **FR-022-13**: `init`/`upgrade` MUST merge or back-up-with-diff-preview user-owned files (`.claude/settings.json`, `AGENTS.md`, `.cursor/rules`, `.github/*`) and obtain consent before overwriting; user content MUST NOT be silently clobbered.
- **FR-022-14**: `HostWriteResult` MUST report `Preserved`/`ForceRendered`/`PendingConsent` accurately for each affected file.

**Remaining enforcement channels (FR-F2 / AR-10)**
- **FR-022-15**: A T2 PreToolUse `prompt` (Haiku) hook MUST handle judgment-class violations the analyzer cannot, returning a deny + reason (Claude-scoped per AR-3).
- **FR-022-16**: A forced-output-style channel MUST be evaluated/implemented as an additional Claude-native rule-delivery path (AR-10).

**Install / loadability (FR-I / AR-2)**
- **FR-022-17**: Per-host install smoke tests MUST codify Claude `claude plugin validate … --strict` (plugin + marketplace) in CI/acceptance.
- **FR-022-18**: Codex and Cursor plugin loadability MUST be verified against their documented discovery, or the limitation recorded with the `build/codex/skills` vs planning/21 `.agents/skills/` tension named and resolved.

**Schema versioning / migration (FR-L)**
- **FR-022-19**: The existing `SchemaVersion` field MUST have an enforced compatibility/migration check (the field exists; the migration path does not) — out-of-range schema versions fail load with guidance.

**Corpus name-parity (planning/23 §5.2)**
- **FR-022-20**: The named-but-absent skill `blazor-hybrid` (planning/23 §5.2, "low priority": reuse control-panel components in MAUI Blazor Hybrid) MUST either be authored to the description standard or explicitly recorded as a deliberate de-scope in the catalog (so name-parity with planning/23 is closed, not silently divergent).

### Key Entities

- **SkillResourceSet** (exists, empty in corpus): `scripts/` / `examples/` / `references/` / `assets/` / `evals/` for a skill; this feature populates it where required and the projectors emit it.
- **Eval case** (`evals/cases.jsonl`): a query + expected top-k skill selection; consumed by the triggering harness.
- **Golden baseline** (`*.verified.*`): the pinned expected projection shape per artifact-type × host.
- **User-owned file**: a host file a user may edit (`settings.json`, `AGENTS.md`, …) governed by the merge/backup/consent policy.
- **Hook launcher**: the resolved command the generated `hooks.json` invokes (the fix for the v1-shim shadowing).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-022-1**: The FR-D33 command-skills and the `add-*` skills each carry their required resources; the corpus-integrity test asserts it; `generate --check` is drift-clean with resources present in every host's skill dir.
- **SC-022-2**: Executing the generated `hooks.json` command with a sample payload runs the v2 backend and emits valid protocol (no shim error) — proven by a smoke test.
- **SC-022-3**: Ambiguous-cluster `evals/cases.jsonl` exist and the confusion-matrix gate passes (and fails on an induced collision).
- **SC-022-4**: A Verify golden baseline exists for every artifact-type × host shape + manifests/marketplace/hooks/AGENTS/copilot-instructions; an induced format change fails its golden test.
- **SC-022-5**: An existing user-edited `.claude/settings.json` survives `init` (preserved/merged/backed-up) and is reported in `HostWriteResult`.
- **SC-022-6**: `claude plugin validate --strict` passes for the plugin + marketplace in CI; Codex/Cursor loadability is asserted or its gap recorded.
- **SC-022-7**: All existing gates stay green throughout: build `-warnaserror` 0/0, full test suite, `dotnet format --verify-no-changes`, `generate --check` drift-clean.

## Out of scope (this feature)

- A **live in-session** PreToolUse/Stop firing test inside a running Claude instance (interactive-only; 021's named headless ceiling). This feature proves *runnability*, not live firing.
- Full **≥20-queries/skill** eval coverage across all 181 skills (AR-6 keeps that a later follow-on; clusters first).
- **Native-AOT** packaging (BD-3 defers it) and the per-RID release/rollback matrix beyond what NFR-7 already preserves.
- Re-litigating locked decisions in `planning/26`.

## Gap-trace (planning → current status)

| Planning ref | Specified | Codebase status | Addressed by |
|---|---|---|---|
| FR-A2 / FR-D33 / 23 §368 | skills bundle resources | **0/181, 0/32 command-skills** (bare MD) | US1 / FR-022-01..05 |
| memory: dotnet-ai shim | hooks fire | wired + validate-load, but **error on fire** — verified: `dotnet-ai`→`Python312\Scripts\dotnet-ai.exe`, v2 tool not installed | US2 / FR-022-10..12 |
| 23 §5.2 | `blazor-hybrid` skill | **absent** (only named NEW skill missing; "low priority") | FR-022-20 |
| FR-E6 / AR-6 | eval harness + matrix | **3-case lexical stub; 0 cases.jsonl** | US3 / FR-022-06..07 |
| NFR-6 | golden output | **0 `*.verified.*`** | US4 / FR-022-08..09 |
| FR-K / AR-7b | user-file policy | **overwrites; policy fields unused** | US5 / FR-022-13..14 |
| FR-F2 | T2 Haiku `prompt` hook | **command-deny only** | US6 / FR-022-15 |
| AR-10 | forced output styles | **absent** | US6 / FR-022-16 |
| FR-I / AR-2 | install smoke tests | **absent** (Claude validated manually in 021) | US7 / FR-022-17 |
| 021 follow-on | Codex/Cursor loadable | **unverified** (Claude verified) | US7 / FR-022-18 |
| FR-L | schema versioning | **field exists; no migration check** | FR-022-19 |
| FR-G2 / FR-G8 | feature-brief + awareness test | **present** (`OrchestrateService`, `MultiRepoAwarenessTests`) | — (no gap) |
| FR-H4 / FR-H5 | new agents + rules | **present** (aspire-architect, ai-engineer; 5 rules) | — (no gap) |
| FR-D (32 cmds) | command-skills present | **present** (32) | — (resources only, US1) |
| FR-B1 | Copilot `.instructions.md`/`.prompt.md`/`.agent.md` | **present** (`CopilotProjector` emits all three + copilot-instructions) | — (no gap; verified) |
| 23 §5.2 (28 skills) / profiles / merges | named NEW skills, 12 profiles, 🔀 merges | **present/correct** (28/29 NEW; 12 profiles; merges done) | — (no gap; verified) |
