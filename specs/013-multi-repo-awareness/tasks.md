# Tasks: Multi-Repo Awareness

**Input**: Design documents from `/specs/013-multi-repo-awareness/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Foundation Models)

**Purpose**: Python model changes that enable all subsequent work
**Note**: Setup tasks carry [Story] labels for traceability since each model change directly serves a specific user story.

- [x] T001 [US1] Update `validate_repo_path` in `ReposConfig` to normalize GitHub HTTPS URLs (`https://github.com/org/repo`) and git SSH URLs (`git@github.com:org/repo.git`) to `github:org/repo` format in `src/dotnet_ai_kit/models.py`
- [x] T002 [P] [US2] Add `FeatureBrief` pydantic model with phase enum validation (specified, planned, tasks-generated, implementing, implemented, blocked) in `src/dotnet_ai_kit/models.py`
- [x] T003 [P] Add unit tests for URL normalization (HTTPS, SSH, .git suffix, already-normalized, local paths unchanged) in `tests/test_models.py`
- [x] T004 [P] Add unit tests for `FeatureBrief` model validation (valid phases, invalid phase rejection, required fields) in `tests/test_models.py`

**Checkpoint**: Models and validators ready. Run `pytest tests/test_models.py` to verify.

---

## Phase 2: User Story 1 — Smart Repo Configuration (Priority: P1)

**Goal**: `/dai.configure` auto-detects sibling repos, accepts GitHub URLs, validates paths, and saves to config.

**Independent Test**: Run `/dai.configure` in a directory with sibling repos and verify `config.yml` repos section is populated with validated paths.

### Slash Command (configure.md)

- [x] T005 [US1] Rewrite Step 3 in `commands/configure.md`: Add Step 3a (auto-detect sibling repos by scanning `../` for `.git/` + `.sln`/`.slnx`/`.csproj`, classify type), Step 3b (prompt per role with 3 input options), Step 3c (validate local paths and normalize GitHub URLs), Step 3d (save to config.yml)
- [x] T006 [US1] Update Step 3 skip logic: add condition "If detected mode is NOT microservice, skip Step 3 entirely" in `commands/configure.md`

### CLI Python Code

- [x] T007 [US1] Add repo configuration prompts to `configure()` interactive flow (after company settings, before command style) with sibling repo auto-detection using `pathlib.Path("..").iterdir()`, questionary prompts, and path validation in `src/dotnet_ai_kit/cli.py`
- [x] T008 [US1] Add `--repos` CLI flag support for non-interactive mode (`--no-input --repos command=../cmd,query=../qry`) in `src/dotnet_ai_kit/cli.py`
- [x] T008b [P] [US1] Add tests for repo configuration prompts in configure() (sibling scan, URL input, path validation, --repos flag) in `tests/test_cli.py`

**Checkpoint**: Configure command detects repos, accepts URLs, validates paths.

---

## Phase 3: User Story 3 — Briefs Directory Isolation (Priority: P1)

**Goal**: `briefs/` is completely separate from `features/`, init never touches it, numbering is independent.

**Independent Test**: Place briefs from two source repos (both with feature 002) in `briefs/`, run `/dai.specify`, verify new local feature gets 001.

- [x] T009 [US3] Update `commands/init.md`: After Step 1, add detection of `.dotnet-ai-kit/briefs/` directory. If exists with content, warn user. Init/reinit must never delete or modify `briefs/`. in `commands/init.md`
- [x] T010 [US3] Update `commands/specify.md`: Add explicit instruction that feature numbering scans ONLY `.dotnet-ai-kit/features/` for next number, never `briefs/` in `commands/specify.md`

**Checkpoint**: Init preserves briefs, numbering ignores briefs.

---

## Phase 4: User Story 2 — Feature Brief Projection (Priority: P1)

**Goal**: Each SDD lifecycle phase projects/updates a self-contained `feature-brief.md` to each affected secondary repo under `briefs/{source-repo-name}/{NNN}-{name}/`.

**Independent Test**: Run `/dai.specify` for a cross-repo feature, verify `feature-brief.md` exists in the query repo's `briefs/` directory with correct role, events, and phase "Specified".

### Core Projection (specify + tasks)

- [x] T011 [US2] Add Step 4b to `commands/specify.md`: After generating `service-map.md`, project initial `feature-brief.md` to each affected secondary repo. Include: feature ID, date, phase "Specified", source repo info, role, required changes, events. Auto-commit in secondary repo with `chore: project feature brief` message. Skip auto-commit if secondary repo has uncommitted changes (warn instead). Skip projection entirely if not cloned or not configured.
- [x] T012 [US2] Replace "Cross-Repo Feature Tracking" section (lines 187-189) in `commands/tasks.md` with full brief projection logic: update briefs with "Tasks (This Repo Only)" filtered to `[Repo:this-repo]`, "Dependencies" section, phase "Tasks Generated"

### Progressive Enrichment (clarify + plan + implement)

- [x] T013 [P] [US2] Add brief re-projection to `commands/clarify.md`: After Step 5, if clarification answers affect secondary repos (changed events/entities/boundaries), re-project updated briefs
- [x] T014 [P] [US2] Add Step 7b to `commands/plan.md`: Update existing briefs with "Implementation Approach" section and phase "Planned". Create brief if missing (repo cloned after specify)
- [x] T015 [US2] Update Step 5a in `commands/implement.md`: After resolving/cloning each repo, check for briefs, load for context. If missing (just cloned), project now. After cloning, update `config.yml` with local path
- [x] T016 [US2] Update Step 5b in `commands/implement.md`: After completing tasks in secondary repo, update brief — mark tasks `[x]`, phase "Implementing"/"Implemented". On failure: phase "Blocked"

**Checkpoint**: Full brief lifecycle works: specify creates, plan/tasks/clarify update, implement tracks progress.

---

## Phase 5: User Story 4 — Status Visibility for Linked Features (Priority: P2)

**Goal**: `/dai.status` displays linked features from `briefs/` separately from local features.

**Independent Test**: Place sample `feature-brief.md` files in `briefs/` and run `/dai.status` to verify display.

- [x] T017 [US4] Add Step 2b to `commands/status.md`: Scan `.dotnet-ai-kit/briefs/` for all source repo subdirectories and their feature briefs. Display separately as "Linked Features (from other repos):" with source repo, feature name, phase, task progress. Support `--verbose` (full brief) and `--all` (include completed)

**Checkpoint**: Status shows both local and linked features.

---

## Phase 6: User Story 5 — Cross-Repo PR and Review Awareness (Priority: P2)

**Goal**: PRs and reviews in secondary repos use the feature brief for context and compliance checking.

**Independent Test**: Run `/dai.pr` in a secondary repo with a brief, verify PR body includes cross-repo references.

- [x] T018 [US5] Update Step 3 in `commands/pr.md`: For secondary repos, include "Part of cross-repo feature: {NNN}-{name} (from {source-repo})" header, reference primary repo PR URL, source changes from `feature-brief.md` task list, include merge-order dependencies
- [x] T019 [P] [US5] Add Check 9 (Brief Compliance) to Step 3 in `commands/review.md`: Load feature brief when entering a secondary repo, compare actual changes (git diff) against brief's "Required Changes" and "Tasks", flag scope creep and incomplete items

**Checkpoint**: PRs reference cross-repo context, reviews check brief compliance.

---

## Phase 7: User Story 6 — Sibling Repo Detection in Detect (Priority: P3)

**Goal**: `/dai.detect` reports sibling repos found in `../`.

**Independent Test**: Run `/dai.detect` with sibling repos in `../` and verify "Sibling repos found:" output.

- [x] T020 [US6] Add Step 6b to `commands/detect.md`: After saving detection results, scan `../` for sibling directories that are git repos with `.sln`/`.slnx`/`.csproj`. Report as "Sibling repos found:" with detected type if classifiable

**Checkpoint**: Detect reports sibling repos.

---

## Phase 8: User Story 7 — Brief Consistency Analysis (Priority: P3)

**Goal**: `/dai.analyze` includes Pass 11 checking brief consistency with current spec/plan/tasks.

**Independent Test**: Modify spec after projecting briefs, run `/dai.analyze`, verify HIGH-severity stale brief finding.

- [x] T021 [US7] Add Pass 11 (Brief Consistency) to `commands/analyze.md`: For each secondary repo reachable via config.yml, verify briefs match current spec/plan/tasks. Flag stale briefs (HIGH), minor drift (MEDIUM)

**Checkpoint**: Analysis catches stale briefs.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Session commands, skill docs, and .slnx audit

### Session Commands

- [x] T022 [P] Update `commands/wrap-up.md`: Add "Projected Briefs Status" section to handoff, listing each secondary repo brief status (current/stale/missing)
- [x] T023 [P] Update `commands/checkpoint.md`: Same as wrap-up — include brief status in checkpoint handoff

### Skill Documentation

- [x] T024 Add "Feature Brief Projection" section to `skills/workflow/multi-repo-workflow/SKILL.md`: Document briefs/ directory structure, lifecycle phases, format, init interaction, independent numbering

### .slnx Audit

- [x] T025 Audit all command files, skill files, and detection code for `.sln` references that don't also include `.slnx`. Update any that are missing. Files to check: `commands/configure.md`, `commands/detect.md`, `commands/init.md`, `commands/verify.md`, `src/dotnet_ai_kit/detection.py`, `skills/workflow/multi-repo-workflow/SKILL.md`

### Documentation Updates

- [x] T026 Update planning docs and constitution if needed: verify `planning/12-version-roadmap.md` reflects multi-repo awareness feature, verify `.specify/memory/constitution.md` mentions `briefs/` directory in relevant sections

### Post-Implementation Fixes (from review)

- [x] T027 Standardize auto-commit message format across `commands/tasks.md`, `commands/plan.md`, `commands/clarify.md`, `commands/implement.md` to use `chore: update feature brief {NNN}-{name} — {phase}` for updates (matching specify.md's initial projection format)
- [x] T028 [P] Add explicit test for `--repos` CLI flag with URL normalization in `tests/test_cli.py`
- [x] T029 [P] Fix review.md check numbering: rename "Check 8b" to "Check 9" and rename "Check 8: Performance" to "Check 10" in `commands/review.md`
- [x] T030 [P] Add brief awareness note to Safety Rules in `commands/undo.md`: document that projected briefs in secondary repos are NOT automatically reverted
- [x] T031 [P] Optimize `_scan_sibling_repos()` in `src/dotnet_ai_kit/cli.py`: replace redundant glob pairs (`*.cs` + `**/*.cs`) with only recursive patterns (`**/*.cs`, `**/*.csproj`)
- [x] T032 [P] Update `templates/config-template.yml` repos section comment to document the three accepted formats: local path, GitHub HTTPS URL (`https://github.com/org/repo`), git SSH URL (`git@github.com:org/repo.git`)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (US1 — Configure)**: Depends on T001 (URL normalizer)
- **Phase 3 (US3 — Isolation)**: No dependency on Phase 2 — can run in parallel
- **Phase 4 (US2 — Brief Projection)**: Depends on T002 (FeatureBrief model) and T009-T010 (isolation rules)
- **Phase 5 (US4 — Status)**: Depends on Phase 4 (briefs must exist to display)
- **Phase 6 (US5 — PR/Review)**: Depends on Phase 4 (briefs must exist to reference)
- **Phase 7 (US6 — Detect)**: Independent — can run any time after Phase 1
- **Phase 8 (US7 — Analyze)**: Depends on Phase 4 (briefs must exist to analyze)
- **Phase 9 (Polish)**: Depends on all previous phases

### User Story Dependencies

- **US1 (Configure)**: Independent after Phase 1 models
- **US2 (Brief Projection)**: Depends on US3 (isolation rules must be in place first)
- **US3 (Isolation)**: Independent after Phase 1 models
- **US4 (Status)**: Depends on US2 (needs briefs to display)
- **US5 (PR/Review)**: Depends on US2 (needs briefs to reference)
- **US6 (Detect)**: Fully independent
- **US7 (Analyze)**: Depends on US2 (needs briefs to analyze)

### Parallel Opportunities

- T001, T002, T003, T004 can all run in parallel (different sections of models.py / test_models.py)
- T005/T006 (configure.md) can run parallel with T009/T010 (init.md + specify.md)
- T013 and T014 can run in parallel (clarify.md and plan.md are separate files)
- T018 and T019 can run in parallel (pr.md and review.md are separate files)
- T022 and T023 can run in parallel (wrap-up.md and checkpoint.md are separate files)

---

## Parallel Example: Phase 1

```
# All Phase 1 tasks can run in parallel (different files/sections):
Task T001: URL normalizer in models.py (ReposConfig section)
Task T002: FeatureBrief model in models.py (new section at bottom)
Task T003: URL tests in test_models.py
Task T004: FeatureBrief tests in test_models.py
```

---

## Implementation Strategy

### MVP First (US1 + US3 + US2 core)

1. Complete Phase 1: Models + validators (T001-T004)
2. Complete Phase 2: Configure command (T005-T008)
3. Complete Phase 3: Isolation rules (T009-T010)
4. Complete Phase 4: Brief projection core (T011-T012)
5. **STOP and VALIDATE**: Test configure detects repos, specify projects briefs, numbering is independent
6. Continue with T013-T016 (progressive enrichment)

### Incremental Delivery

1. Models → Configure works with URLs → Test
2. Init + Specify isolation → Briefs project correctly → Test
3. Full lifecycle enrichment (clarify/plan/tasks/implement update briefs) → Test
4. Status + PR/Review → Team visibility → Test
5. Detect + Analyze + Polish → Quality/safety net → Test

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All command file edits must stay within the 200-line budget (constitution V)
- For files near 200 lines (specify, tasks, implement, review, analyze): replace existing placeholder content rather than append
- Brief projection auto-commits in secondary repos (FR-035); skip commit if dirty working tree (FR-036)
- All `.sln` references must also include `.slnx` (FR-033)
