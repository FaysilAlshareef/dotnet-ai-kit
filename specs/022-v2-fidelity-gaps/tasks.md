# Tasks: dotnet-ai-kit v2 — Planning-Fidelity Gaps

**Input**: Design documents from `specs/022-v2-fidelity-gaps/` (spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md)
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Tests**: INCLUDED — this feature's success criteria are test/gate-defined (corpus-integrity, hook smoke, golden output, confusion matrix, install validate), so test tasks are first-class.

**Organization**: by user story (spec.md priorities). Format: `- [ ] T### [P?] [US?] Description with file path`. `[P]` = parallelizable (different files). Each phase ends green: build `-warnaserror` 0/0 · `dotnet test` · `dotnet format` · `generate --check` drift-clean.

> Baseline (start state, 2026-05-31): 020+021 complete; 112 tests green; four enforcement tiers wired; Claude plugin + marketplace pass `claude plugin validate --strict`.

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Confirm baseline gates green on `022-v2-fidelity-gaps` (build -warnaserror, test, format, `generate --check`) before changes.
- [ ] T002 [P] Wire Verify into `tests/DotnetAiKit.Hosts.Tests/` (a `ModuleInitializer` / `VerifyXunit.Verifier` settings file; `Verify.Xunit` is already referenced) so golden tests can land in Phase US4.
- [ ] T003 [P] Add a `tests/DotnetAiKit.Acceptance.Tests/` skip-if-absent helper for the external `claude` CLI (used by US7 smoke).

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ Blocks US1 (resources) + US4 (goldens). No resource projection until done.**

- [ ] T004 Load `SkillResourceSet` from disk in `src/DotnetAiKit.Infrastructure/FileSystemArtifactRepository.cs` (scripts/examples/references/assets/evals → `Skill.Resources`); empty-declared/missing-file → broken-resource load error (per contracts/skill-resource-set.md).
- [ ] T005 [P] Add executable-script `ScriptTrust` (AutoRun=false, interpreter from extension) in `src/DotnetAiKit.Core/Artifacts/` (or Application) per data-model.md (FR-022-05).
- [ ] T006 Project a skill's resource set into `build/<host>/skills/<name>/` byte-stable in each `src/DotnetAiKit.Hosts/**/<Host>Projector.cs` (FR-022-04); extend `tests/DotnetAiKit.Hosts.Tests/GenerationDriftTests` (or add) to cover a resourced skill.
- [ ] T007 [P] Enforce `SchemaVersion` compatibility on load in `src/DotnetAiKit.Core/Artifacts/Skill.cs` + `FileSystemArtifactRepository` (out-of-range → clear "unsupported schema version" load error) (FR-022-19).

**Checkpoint**: corpus still loads + projects + drift-clean with the resource pipeline in place.

## Phase 3: User Story 2 — Hooks actually run when fired (Priority: P1) 🎯 MVP

**Goal**: the wired hooks resolve the v2 backend at fire time, not the v1 shim. **Independent test**: execute the generated `hooks.json` command with a payload → valid protocol.

- [ ] T008 [US2] Confirm/adjust the launcher command in `src/DotnetAiKit.Hosts/Claude/ClaudeHooksWriter.cs` per contracts/hook-launcher.md; regenerate `build/`.
- [ ] T009 [P] [US2] Shadow-detection: `src/DotnetAiKit.Application/UseCases/CheckService.cs` (+ `InitService`) warn when a `dotnet-ai` on PATH is not the v2 tool (e.g. `…/Python*/Scripts/dotnet-ai*`) (FR-022-10), via `IProcessRunner`/PATH probe.
- [ ] T010 [US2] Keep `HookCommand` fail-safe on unresolved backend (no spurious block, clear stderr) in `src/DotnetAiKit.Cli/Commands/HookCommand.cs` (FR-022-12); add a unit test.
- [ ] T011 [US2] Acceptance smoke in `tests/DotnetAiKit.Acceptance.Tests/HookExecutionSmokeTests.cs`: run the *generated* command string with PreToolUse + Stop payloads; assert protocol (FR-022-11, SC-022-2).
- [ ] T012 [US2] Update `docs/setup-claude-code.md` (explicit v2-tool prereq + shim removal) + the `dotnet-ai-path-shim` memory.

**Checkpoint**: hooks run end-to-end against the v2 backend; smoke green.

## Phase 4: User Story 1 — Skills carry bundled resources (Priority: P1)

**Goal**: FR-D33 + `add-*` skills ship resources; projector copies them. **Independent test**: the resourced skills assert + project + drift-clean.

- [ ] T013 [P] [US1] Author `scripts/` (+`examples/`) for `artifacts/skills/commands/constitution/` (FR-022-01).
- [ ] T014 [P] [US1] Author `scripts/` (+`examples/`) for `artifacts/skills/commands/checklist/`.
- [ ] T015 [P] [US1] Author `scripts/` (+`examples/`) for `artifacts/skills/commands/fix/` (failing-test→fix→verify workflow).
- [ ] T016 [P] [US1] Author `scripts/` (+`examples/`) for `artifacts/skills/commands/release/` (version bump + changelog).
- [ ] T017 [P] [US1] Author one compilable C# `examples/` for each `artifacts/skills/commands/add-*/` (add-aggregate/entity/event/endpoint/page/crud/tests) (+ template `assets/` where the generator fills a template) (FR-022-02).
- [ ] T018 [US1] Corpus-integrity test in `tests/DotnetAiKit.Acceptance.Tests/CorpusIntegrityTests.cs` asserts the required resource set per skill-kind (FR-022-03); regenerate + `generate --check` drift-clean (SC-022-1).

**Checkpoint**: resourced skills load, project to all four hosts, drift-clean.

## Phase 5: User Story 4 — Golden-output baselines (Priority: P2)

**Goal**: every projection shape pinned. **Independent test**: an induced format change fails a golden.

- [ ] T019 [P] [US4] Golden per artifact-type × host (skill/agent/rule/command) in `tests/DotnetAiKit.Hosts.Tests/` via Verify; accept initial `*.verified.*` (FR-022-08).
- [ ] T020 [P] [US4] Golden for each manifest (`build/.../plugin.json` ×3), `marketplace.json`, `claude/hooks/hooks.json`, `codex/AGENTS.md`, `copilot/.github/copilot-instructions.md`.
- [ ] T021 [US4] Negative test: a deliberate frontmatter-order change fails its golden independently of the drift gate (FR-022-09); revert (SC-022-4).

## Phase 6: User Story 3 — Eval cases + confusion matrix (Priority: P2)

**Goal**: selection gated by authored cases. **Independent test**: matrix passes; induced collision fails.

- [ ] T022 [P] [US3] Author `evals/cases.jsonl` for the cluster skills (mediator, CQRS, eventing, testing, architecture, gateway/control-panel) per contracts/eval-cases.schema.md (FR-022-06).
- [ ] T023 [US3] Generalize `tests/DotnetAiKit.Triggering.Evals/TriggeringOracleTests.cs` to load cluster `cases.jsonl` + run a confusion matrix (correct fires, siblings silent); validate `expect` names exist (FR-022-07, SC-022-3).
- [ ] T024 [US3] Negative test: an induced description collision flips a case to fail.

## Phase 7: User Story 5 — User-owned-file policy (Priority: P2)

**Goal**: never clobber user files. **Independent test**: a pre-existing user `settings.json` survives `init`.

- [ ] T025 [US5] `UserFilePolicy` (Application) classifying Managed vs UserOwned + the decision table in contracts/user-file-policy.md (merge/preserve/consent/backup); invalid-JSON → back up + warn (FR-022-13).
- [ ] T026 [US5] `ClaudeHostAdapter` routes user-owned writes (`.claude/settings.json`, `AGENTS.md`, …) through `UserFilePolicy`; populate `HostWriteResult.{Preserved,ForceRendered,PendingConsent}`; surface in the `init` reporter (FR-022-14).
- [ ] T027 [US5] Tests in `tests/DotnetAiKit.Application.Tests/`: pre-existing user `settings.json` is merged/preserved + reported; managed-no-edit refreshes (SC-022-5).

## Phase 8: User Story 7 — Install smoke + cross-host loadability (Priority: P3)

**Goal**: loadability is gated. **Independent test**: `claude plugin validate --strict` in CI; codex/cursor asserted-or-recorded.

- [ ] T028 [US7] `tests/DotnetAiKit.Acceptance.Tests/PluginInstallSmokeTests.cs`: run `claude plugin validate build/claude --strict` + `build --strict` (skip-if-CLI-absent, via T003) (FR-022-17, SC-022-6).
- [ ] T029 [P] [US7] Assert Codex/Cursor projected layout against their documented discovery; resolve or record the `build/codex/skills/` vs `.agents/skills/` tension (FR-022-18) in `research.md`/`docs/`.

## Phase 9: User Story 6 — Remaining enforcement channels (Priority: P3)

**Goal**: judgment hook + output-style channel. **Independent test**: judgment-deny works; output-style projects.

- [ ] T030 [US6] Add a T2 PreToolUse `prompt`-type entry (Haiku, Claude-scoped) in `ClaudeHooksWriter` for judgment-class checks → deny+reason (FR-022-15); golden + smoke.
- [ ] T031 [P] [US6] Author + project a forced-output-style artifact for Claude (`build/claude/output-styles/…`) (FR-022-16, AR-10); drift-clean.

## Phase 10: Polish & Cross-Cutting

- [ ] T032 [P] Close `blazor-hybrid` name-parity (FR-022-20): author `artifacts/skills/microservice/controlpanel/blazor-hybrid/SKILL.md` to the description standard, OR record a de-scope note in `planning/23` §5.2 (corpus == catalog).
- [ ] T033 [P] Update docs (`README.md` enforcement section, `docs/setup-*.md`) + memory for the delivered gaps.
- [ ] T034 Run `/speckit.analyze` (re-check) + the full gate: build -warnaserror 0/0 · `dotnet test` · `dotnet format --verify-no-changes` · `generate --check` drift-clean · `claude plugin validate --strict` (SC-022-7).
- [ ] T035 Update `spec.md` Status → done; record any item still a tracked follow-on (live in-session hook firing; full ≥20/skill evals; Native-AOT).

## Dependencies & Execution Order

- **Setup (P1)** → **Foundational (P2, blocks US1/US4)** → user stories.
- **US2 (Phase 3)** is independent of Foundational (hook launcher) — can run in parallel with Phase 2; it is the highest-value MVP slice (makes wired hooks runnable).
- **US1 (Phase 4)** depends on Foundational (T004/T006). **US4 (Phase 5)** depends on Foundational + US1 (goldens cover resourced skills). **US3/US5/US6/US7** are mutually independent (different files) once Foundational is done.
- **Polish (Phase 10)** last.

### Parallel opportunities
- T002/T003 (setup); T005/T007 (foundational, different files); T013–T017 (different skill dirs); T019/T020 (different golden files); T022 (eval files); T029/T031/T032/T033 (independent).

## Implementation Strategy

- **MVP** = Phase 1 + Phase 2 + **Phase 3 (US2, hooks runnable)** + **Phase 4 (US1, resources)** — the two P1 stories; stop & validate (`quickstart.md` F1/F2).
- **Incremental**: add US4 → US3 → US5 → US7 → US6 → Polish, each an independently testable green increment.
- Commit per green phase (no push / no PR unless asked). Honor AR-5 (resources only where required), NFR-1 (no-network), NFR-3 (cross-platform).

## Notes / scope guards

- **Out of scope** (spec §Out of scope): live in-session hook firing (interactive-only), full ≥20-queries/skill evals, Native-AOT packaging, the per-RID release/rollback matrix.
- Do NOT add resource dirs to all 181 skills — only the FR-D33 set, `add-*`, and eval-bearing clusters (AR-5).

---

## Implementation status — COMPLETE (all phases green)

Implemented across 7 commits on `022-v2-fidelity-gaps`:
- **Foundational [T001-T007]**: `SkillResourceSet`→`ResourceFile{RelativePath,Content}` (content-in-model so pure projectors emit resources); `ScanResources` loads skill-dir-relative + sorted + LF; all 4 projectors emit resources; `ArtifactSchema` load guard (FR-022-19).
- **US2 hooks runnable [T008-T012]**: `HookToolDiagnostics` (shim shadow-detection in `check`) + hook-execution smoke; launcher stays `dotnet-ai hook`.
- **US1 resources [T013-T018]**: workflow scripts for constitution/checklist/fix/release + one C# example per `add-*` (subagent-authored); corpus-integrity required-set + Roslyn parse-check.
- **US5 user-file policy [T025-T027]**: `UserFilePolicy` (JSON deep-merge/preserve/consent/backup) wired into `ClaudeHostAdapter`; `HostWriteResult` buckets populated.
- **US3 eval cases [T022-T024]**: cluster `evals/cases.jsonl` + discriminating confusion-matrix gate (strict outrank).
- **US4 goldens [T019-T021]**: Verify baseline over the full projection (manifests/marketplace/hooks/AGENTS/copilot-instructions).
- **US7 install smoke [T028-T029]**: `claude plugin validate --strict` (skip-if-absent) + codex/cursor structure.
- **US6 channels [T030-T031]**: T2 `prompt` judgment hook + forced output-style; validate passes with both.
- **Polish [T032-T035]**: `blazor-hybrid` authored (name-parity with 23 §5.2 closed — 182 skills); docs/memory; final gate.

**Final gate**: build -warnaserror 0/0 · 142 tests green · `dotnet format` clean · `generate --check` drift-clean (885 files, 4 hosts) · `claude plugin validate build/claude --strict` + `build --strict` pass.

**Remaining (out of scope / follow-on)**: a *live* in-session PreToolUse/Stop firing test (interactive-only); full ≥20-queries/skill LLM eval (AR-6); Codex/Cursor plugin-load parity (different discovery model); Native-AOT packaging.
