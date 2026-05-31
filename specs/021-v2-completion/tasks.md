---
description: "Task list for 021-v2-completion"
---

# Tasks: dotnet-ai-kit v2 — Completion

**Input**: design docs in `specs/021-v2-completion/` · **Builds on**: 020 engine
**Gate after every migration batch**: `repo.Load()` Ok (0 broken edges) + `generate --check` drift-clean.
**Tiering**: anchor = C1–C7 + C9; baseline = C8 (new-domain skills).

## Phase C1: Bulk migration (US1) 🎯

- [x] T001 Write the throwaway migration script (Python, dev-time) per `contracts/migration-mapping.md`: skills, commands, agents, rules, profiles, knowledge → `artifacts/`; drop `when_to_use`; set `metadata.kind/invocation/paths`; build agent `skills:` reverse-index; do the 3 consolidations in-pass; assert name==dir + no dangling edges + conventions==whitelist
- [x] T002 Run the script; iterate until `repo.Load(artifacts/)` is Ok with 0 broken edges (use a tiny harness/test or the CLI)
- [x] T003 [US1] Fix the known v1 content defect (broken `event-catalogue` reflection sample) + any migration-surfaced validation failures
- [x] T004 [US1] Verify counts: ≈160 skills, 16 migrated rules (5 conventions + 11 domain), 12 profiles, agents, 27 migrated commands; record actual counts

## Phase C2: Generate full-corpus baseline (US1)

- [x] T005 [US1] `generate --out build/` for the full corpus (orphan-cleanup removes the 8-artifact baseline); confirm all 4 host trees populated
- [x] T006 [US1] `generate --check` → no drift; run the actual exit code once at full scale (advisor nit)
- [x] T007 [US1] Commit migrated `artifacts/` + regenerated `build/` (v1 dirs still present — v1 recoverable)

## Phase C3: Structural new artifacts (US1)

- [x] T008 [P] [US1] 5 new command-skills: constitution, checklist, orchestrate, release, fix (`artifacts/skills/commands/<n>/SKILL.md`, disable-model-invocation, DescriptionStandard-compliant)
- [x] T009 [P] [US1] 2 new agents: aspire-architect, ai-engineer (`artifacts/agents/`, with `skills:`)
- [x] T010 [P] [US1] 4 new rules: mediator-abstraction, messaging-bus-selection (domain), testing-platform, ai-integration (domain, with paths) — deterministic-enforcement already exists
- [x] T011 [US1] Regenerate + `generate --check`; re-commit baseline

## Phase C4: Corpus-integrity test (US4)

- [x] T012 [US4] `tests/DotnetAiKit.Acceptance.Tests/CorpusIntegrityTests.cs` — parametrized over the real `artifacts/`: every artifact loads, name==dir, graph consistent, projects to 4 hosts (SC-002)
- [x] T013 [US4] DescriptionStandard: hard-assert for new/structural artifacts; report migrated-compliance count (metric, non-failing) (FR-016)

## Phase C5: Deferred features (US4)

- [ ] T014 [P] [US4] `ConventionCodeFixProvider` (DAK0004 → private setter; DAK0001 → Task) + analyzer tests (T060)
- [ ] T015 [P] [US4] `check` capability-dependency validation against `HostCapabilityMatrix` + test (T048)
- [ ] T016 [P] [US4] `ManifestIntegrityService` (sha256 over manifest) + test (T056)
- [x] T017 [US4] Distribution: `PackAsTool`/`ToolCommandName` on Cli; generate `build/marketplace.json`; `dotnet pack` + install-smoke test (T080-82)

## Phase C6: Restructure (US3)

- [x] T018 [US3] grep-before-delete audit: for each ambiguous dir (templates, bin, scripts, schemas, assets, prompts, config, knowledge) record references in src/.specify/.github/docs
- [x] T019 [US3] Remove migrated v1 artifact dirs (skills, commands, rules, agents, agents-source, agents-claude, agents-copilot-templates, profiles, knowledge, config) + root v1 `.claude-plugin/` — **separate commit** from migration
- [x] T020 [US3] Reconcile to exactly one authoritative generated manifest per host; update `.gitignore`/`.gitattributes` as needed; confirm no orphan top-level dirs
- [x] T021 [US3] Verify build + test + `generate --check` still green after removal

## Phase C7: Docs + CI (US5, US6)

- [x] T022 [P] [US5] Rewrite `README.md` to the v2 .NET tool (commands, build/test/generate, architecture)
- [x] T023 [P] [US5] Rewrite `CLAUDE.md` (agent context) to v2 — .NET stack, structure, conventions; drop stale v1 Python-CLI claims
- [x] T024 [P] [US5] Rewrite/refresh `docs/` (architecture, contributor guide, ADR for the rewrite)
- [x] T025 [US6] Rewrite `.github/workflows/` for .NET (build -warnaserror + test + format + drift-gate); remove/retire Python-coupled workflows (ci.yml, ci-branch.yml, measure.yml, smoke.yml) or convert
- [x] T026 [US6] Confirm no workflow references removed Python tooling

## Phase C8: New-domain skills — baseline (US8)

- [x] T027 [P] [US8] Aspire (3) + AI integration (2) skills — baseline, description-standard
- [x] T028 [P] [US8] Minimal API/ASP.NET 10 (4) skills
- [x] T029 [P] [US8] Messaging/Dapr/Wolverine + mediator-migration (license-light) skills
- [x] T030 [P] [US8] Roslyn (3) + modern testing (3) skills
- [x] T031 [P] [US8] Blazor (2-3) + auth (3) + GraphQL (1) skills
- [x] T032 [US8] Regenerate + `generate --check`; each new skill projects + passes the standard; commit

## Phase C9: Parity + Python removal (US7)

- [x] T033 [US7] Survey `src/dotnet_ai_kit/cli.py` verbs; fill `contracts/parity-assessment.md` (every v1 verb → .NET status)
- [x] T034 [US7] Close any small gaps the assessment finds (or document + retain Python)
- [ ] T035 [US7] If full coverage + acceptance green: remove `src/dotnet_ai_kit/` + Python `tests/` (same change as CI cutover); else retain + document

## Phase C10: Final verification

- [x] T036 Full `dotnet build -warnaserror` (0/0) + `dotnet test` (all green) + `dotnet format --verify-no-changes` + `generate --check` + vuln scan
- [x] T037 Update tasks.md completion status + spec/summary stating deep-vs-baseline; update memory

## Dependencies
- C1 → C2 → (C3, C4) → C5 → C6 → C7; C8 after C2 (engine + corpus exist); C9 after C5 (features) + C7 (CI cutover paired); C10 last.
- Migration (C1/C2) before restructure (C6) — never delete v1 before its content is migrated + verified.

## Parallel opportunities
- C3 T008/T009/T010 parallel (different files). C5 T014/T015/T016 parallel. C7 T022/T023/T024 parallel. C8 T027–T031 parallel (subagent-friendly: independent skill batches).

---

## Completion status (this session) — 33/37 done

**Done & green:** full v1 corpus migrated (C1/C2); structural new artifacts → 32 commands/15 agents/21 rules
(C3); corpus-integrity test over all 245 artifacts (C4); distribution `PackAsTool` + `marketplace.json`
+ pack verified (C5/T017); restructure — 9 v1 artifact dirs + root v1 `.claude-plugin/` removed (C6);
README/CLAUDE.md/architecture/ADR rewritten + CI consolidated to one cross-platform .NET workflow (C7);
27 new-domain skills authored to the description-standard baseline by subagents (C8); parity assessment
written (C9/T033-34); final verify (C10): **245 artifacts, 89 tests green, build -warnaserror 0/0,
dotnet format clean, generate --check drift-clean, tool packs**.

## Deferred to follow-on (with rationale)

- **T035 — remove Python**: RETAINED per the maintainer's explicit gate. The .NET CLI fully covers the
  six core verbs but `status`/`changelog`/`extension-*` are redesigned as command-skills / superseded by
  the plugin model (not 1:1 CLI verbs) — so full CLI-surface parity is **not** proven. Python source kept
  as reference; its v1 tests are obsoleted by the migration (not run by .NET CI). Removal path + the
  Python-coupled dirs (`templates/ config/ schemas/ scripts/`) are documented in `contracts/parity-assessment.md`.
- **T014 (analyzer code-fix), T015 (`check` capability-dependency validation), T016 (manifest sha256)**:
  completeness refinements deferred. Enforcement is already proven (analyzers fire + Stop-gate, SC-004);
  T015 needs an artifact `requires-capability` field (model extension); T016 needs a consumer; T014 adds a
  Roslyn Workspaces dependency. None blocks the success criteria.
- **Per-host setup guides** (`docs/setup-*.md`): left as-is (install instructions, broadly valid); the
  primary docs (README, CLAUDE.md, architecture, ADR) are rewritten to v2.
- **Migrated-artifact DescriptionStandard**: ~5% comply (v1 descriptions lack negative scope); tracked as a
  metric (FR-016), improved incrementally. New/structural + the 27 C8 skills all comply (hard-gated/verified).
