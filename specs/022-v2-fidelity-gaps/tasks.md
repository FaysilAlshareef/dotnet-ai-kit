# Tasks: dotnet-ai-kit v2 — Planning-Fidelity Gaps

**Branch**: `022-v2-fidelity-gaps` · **Spec**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)
**Convention**: `[P]` = parallelizable (different files, no ordering dep). Each phase ends green (build `-warnaserror` 0/0 · full test suite · `dotnet format` · `generate --check` drift-clean).

> Baseline (start state, verified 2026-05-31): 020+021 complete; 112 tests green; all four enforcement tiers wired; Claude plugin + marketplace pass `claude plugin validate --strict`. Gaps below are what planning specifies that the code lacks.

## Phase F1 — Make the wired hooks runnable (US2, P1)

- [ ] T001 [US2] Decide the launcher mechanism for `hooks.json` (resolve FR-022-10 clarification): plugin-root-relative launcher vs. required global tool vs. `dotnet <dll>`. Record in `contracts/hook-launcher.md`.
- [ ] T002 [US2] Update `ClaudeHooksWriter` to emit the resolved launcher command (e.g. `${CLAUDE_PLUGIN_ROOT}`-relative) instead of bare `dotnet-ai`; regenerate `build/`.
- [ ] T003 [US2] `HookCommand` fail-safe: if the backend can't be resolved, exit without a spurious block + clear stderr (FR-022-12).
- [ ] T004 [US2] Acceptance smoke test: execute the *generated* hook command string with a sample PreToolUse + Stop payload; assert valid hook protocol (FR-022-11). Document/remove the stale v1 `dotnet-ai` PATH shim.
- [ ] T005 [US2] Re-run `claude plugin validate build/claude --strict` after the hooks.json change; update `docs/setup-claude-code.md` + the `dotnet-ai-path-shim` memory.

## Phase F2 — Populate + project skill resources (US1, P1)

- [ ] T006 [US1] Confirm `FileSystemArtifactRepository` loads `scripts/examples/references/assets/evals` into `SkillResourceSet` (add if missing) + a broken-resource load error (edge case).
- [ ] T007 [US1] Each host projector copies a skill's resource set into `build/<host>/skills/<name>/` byte-stable (FR-022-04); extend `GenerationDriftTests`.
- [ ] T008 [P] [US1] Author `scripts/` (+`examples/` where applicable) for `constitution`, `checklist`, `fix`, `release` command-skills (FR-022-01).
- [ ] T009 [P] [US1] Author compilable `examples/` (and/or template `assets/`) for the `add-*` code-gen command-skills (FR-022-02).
- [ ] T010 [US1] Trust/security model for executable scripts: declared + never auto-run + provenance; `.py` default + `.ps1`/`.sh` siblings (FR-022-05, NFR-3). Spec in `contracts/script-trust.md`.
- [ ] T011 [US1] Corpus-integrity test asserts the required resource set per skill-kind (FR-022-03); regenerate + drift-clean.

## Phase F3 — Golden-output baselines (US4, P2)

- [ ] T012 [P] [US4] Wire Verify (`Verifier.Verify`) into `Hosts.Tests`; add a golden per artifact-type × host (skill/agent/rule/command).
- [ ] T013 [P] [US4] Goldens for the manifests, `marketplace.json`, `hooks.json`, `AGENTS.md`, `copilot-instructions.md` (FR-022-08). Accept initial `*.verified.*`.
- [ ] T014 [US4] Prove independence: a deliberate frontmatter-order change fails its golden (FR-022-09); revert.

## Phase F4 — Eval cases + confusion matrix (US3, P2)

- [ ] T015 [P] [US3] Author `evals/cases.jsonl` (query + expected top-k) for the ambiguous clusters: mediator, CQRS, eventing, testing, architecture, gateway/control-panel (FR-022-06).
- [ ] T016 [US3] `Triggering.Evals` loads the cases + runs a confusion matrix (correct fires, siblings silent); wire into CI (FR-022-07, SC-D). Augment/replace the 3-case lexical stub.
- [ ] T017 [US3] Negative test: an induced description collision fails the matrix.

## Phase F5 — User-owned-file policy (US5, P2)

- [ ] T018 [US5] `ClaudeHostAdapter` (+ shared policy): for user-owned files (`.claude/settings.json`, `AGENTS.md`, `.cursor/rules`, `.github/*`) merge or back-up-with-diff-preview + consent; never clobber (FR-022-13). Invalid-JSON → back up + warn.
- [ ] T019 [US5] Populate `HostWriteResult.Preserved/ForceRendered/PendingConsent` accurately (FR-022-14); surface in the `init` reporter.
- [ ] T020 [US5] Tests: pre-existing user `settings.json` survives `init` (SC-022-5); managed-no-edit file refreshes.

## Phase F6 — Install smoke + cross-host loadability (US7, P3)

- [ ] T021 [US7] Codify `claude plugin validate build/claude --strict` + `build --strict` as an acceptance/CI smoke (skip-if-CLI-absent) (FR-022-17).
- [ ] T022 [US7] Verify Codex + Cursor loadability against their documented discovery; resolve the `build/codex/skills` vs planning/21 `.agents/skills/` tension, or record it (FR-022-18).

## Phase F7 — Remaining enforcement channels (US6, P3)

- [ ] T023 [US6] T2 PreToolUse `prompt` (Haiku) hook for judgment-class violations the analyzer can't catch → deny + reason (FR-022-15, Claude-scoped AR-3).
- [ ] T024 [US6] Forced-output-style channel: author + project the Claude output-style artifact (FR-022-16, AR-10).

## Phase F8 — Schema-version migration + corpus name-parity

- [ ] T025 [P] Enforce `SchemaVersion` compatibility on load; out-of-range fails with migration guidance (FR-022-19).
- [ ] T025b [P] Close the `blazor-hybrid` name-parity gap (FR-022-20): author the skill to the description standard, or record a deliberate de-scope note in planning/23 §5.2 so the corpus and catalog agree. (Only named NEW skill currently absent.)

## Phase F9 — Final verification

- [ ] T026 Full gate: build `-warnaserror` 0/0 · `dotnet test` · `dotnet format --verify-no-changes` · `generate --check` drift-clean · `claude plugin validate --strict`.
- [ ] T027 Update docs (setup guides, README enforcement section), memory, and the spec `Status` → done; record any item that remains a tracked follow-on.

## Dependencies & parallelism

- F1 (hooks runnable) is independent and highest-value — do first. F2 (resources) gates F3/F4 (goldens + evals reference projected resources). F5/F6/F7/F8 are independent of each other (different files) and can interleave.
- Parallel: T008/T009 (different skill dirs); T012/T013 (different golden files); T015 (independent eval files); T025 (Core, isolated).

## Notes / scope guards

- Per **AR-5**, resources are opt-in — do NOT add boilerplate dirs to all 181 skills; only the FR-D33 set, `add-*`, and eval-bearing clusters (the spec's firm subset).
- **Out of scope** (spec §Out of scope): live in-session hook firing (interactive-only), full ≥20-queries/skill eval coverage, Native-AOT packaging.
- Keep every phase green; commit per green phase (no push / no PR unless asked).
