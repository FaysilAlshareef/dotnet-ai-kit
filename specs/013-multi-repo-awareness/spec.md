# Feature Specification: Multi-Repo Awareness — Cross-Repo Feature Projection & Smart Repo Configuration

**Feature Branch**: `013-multi-repo-awareness`
**Created**: 2026-03-30
**Status**: Draft
**Input**: User description: "Fix two critical gaps in the multi-repo microservice workflow: (1) configure command doesn't auto-detect sibling repos, validate paths, or accept GitHub URLs, (2) secondary repos are blind to cross-repo features — all spec/plan/tasks artifacts only exist in the primary repo."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Smart Repo Configuration (Priority: P1)

A developer runs `/dai.configure` in their microservice project. The tool auto-detects sibling repos in the parent directory by scanning for git repos with `.sln`, `.slnx`, or `.csproj` files, classifies each repo by type (command, query, gateway, etc.), and presents them as suggestions. The developer confirms, adjusts, or provides GitHub URLs for repos not cloned locally. All paths are validated before saving.

**Why this priority**: Without correct repo paths in config, no cross-repo feature (brief projection, multi-repo implement, cross-repo PR) can function. This is the foundation everything else depends on.

**Independent Test**: Can be fully tested by running `/dai.configure` in a directory with sibling repos and verifying that `config.yml` repos section is populated with validated paths.

**Acceptance Scenarios**:

1. **Given** a microservice project with 3 sibling repos in `../`, **When** the developer runs `/dai.configure`, **Then** the tool detects all 3 repos, classifies their types, and presents them as suggestions with detected types.
2. **Given** the developer provides a GitHub URL `https://github.com/org/repo`, **When** the tool processes it, **Then** it normalizes to `github:org/repo` format and saves to config.yml.
3. **Given** the developer provides a local path `../my-query-repo`, **When** the tool validates it, **Then** it checks the directory exists, contains `.git/`, and contains `.sln`/`.slnx`/`.csproj`, warning if validation fails but allowing the user to proceed.
4. **Given** the developer provides a git SSH URL `git@github.com:org/repo.git`, **When** the tool processes it, **Then** it normalizes to `github:org/repo` format.
5. **Given** a non-microservice (generic) project, **When** the developer runs `/dai.configure`, **Then** Step 3 (repo paths) is skipped entirely.

---

### User Story 2 — Feature Brief Projection to Secondary Repos (Priority: P1)

A developer specifies a cross-repo feature in the command repo using `/dai.specify`. The tool generates `service-map.md` in the primary repo as before, then additionally projects a self-contained `feature-brief.md` into each affected secondary repo's `.dotnet-ai-kit/briefs/{source-repo-name}/{NNN}-{name}/` directory. Each brief contains only that repo's relevant information: its role, required changes, events, and later tasks and implementation approach. The brief is progressively enriched as the lifecycle advances (specify → clarify → plan → tasks → implement).

**Why this priority**: This is the core solution to the "secondary repos are blind" problem. Without briefs, developers working in secondary repos have no awareness of cross-repo features.

**Independent Test**: Can be fully tested by running `/dai.specify` for a feature that spans command and query repos, then verifying `feature-brief.md` exists in the query repo's `briefs/` directory with correct role and events sections.

**Acceptance Scenarios**:

1. **Given** a feature specified in the command repo that affects the query repo, **When** `/dai.specify` completes, **Then** `feature-brief.md` is created at `{query-repo}/.dotnet-ai-kit/briefs/{command-repo-name}/{NNN}-{name}/feature-brief.md` with phase "Specified", the query repo's role, and required changes.
2. **Given** a secondary repo is referenced as `github:org/repo` (not cloned locally), **When** brief projection runs, **Then** projection is skipped with a note "Brief not projected to {repo} — not cloned locally" in the report.
3. **Given** a secondary repo path is null (not configured), **When** brief projection runs, **Then** projection is skipped with a note "Brief not projected — repo not configured".
4. **Given** `/dai.plan` runs after specify, **When** the plan is generated, **Then** existing briefs are updated with "Implementation Approach" section and phase changes to "Planned".
5. **Given** `/dai.tasks` runs after plan, **When** tasks are generated, **Then** existing briefs are updated with "Tasks (This Repo Only)" section containing only tasks tagged for that repo, and phase changes to "Tasks Generated".
6. **Given** `/dai.implement` runs and completes tasks in a secondary repo, **When** each task completes, **Then** the brief's task list is updated with checkmarks and phase changes to "Implementing" then "Implemented".
7. **Given** `/dai.specify` is re-run (idempotent), **When** briefs already exist, **Then** they are overwritten with fresh content.

---

### User Story 3 — Briefs Directory Isolation from Local Features (Priority: P1)

Briefs from other repos live in `.dotnet-ai-kit/briefs/` which is completely separate from `.dotnet-ai-kit/features/`. This means: (a) local feature numbering only scans `features/` so numbers never collide with briefs, (b) `/dai.init` never touches the `briefs/` directory, (c) multiple source repos can project briefs without collision because they're namespaced by source repo name.

**Why this priority**: Without this separation, feature number collisions between local features and projected briefs would corrupt the workflow. This is an architectural constraint that must be correct from the start.

**Independent Test**: Can be fully tested by having briefs from two different source repos (both with feature `002`) in the `briefs/` directory, running `/dai.specify` locally, and verifying the new local feature gets `001` (not `003`).

**Acceptance Scenarios**:

1. **Given** a query repo has briefs `briefs/command-repo/001-orders/` and `briefs/command-repo/002-invoices/`, **When** the developer runs `/dai.specify` to create a local feature, **Then** the new feature is numbered `001` (scanning only `features/`, not `briefs/`).
2. **Given** two source repos both have feature `002`, **When** both project briefs to the same target repo, **Then** they coexist without collision at `briefs/command-repo/002-invoices/` and `briefs/gateway-repo/002-user-sync/`.
3. **Given** a repo has a `briefs/` directory with content, **When** `/dai.init` runs (fresh or `--force`), **Then** the `briefs/` directory is preserved untouched and a warning is shown: "This repo has linked features from other repos (in .dotnet-ai-kit/briefs/). They will be preserved."

---

### User Story 4 — Status Visibility for Linked Features (Priority: P2)

A developer opens a secondary repo and runs `/dai.status`. The status display shows both local features (from `features/`) and linked features (from `briefs/`), clearly separated. Linked features show: source repo name, feature name, current phase, and task progress.

**Why this priority**: Status visibility makes briefs actionable. Without it, developers would need to manually browse the `briefs/` directory to know what cross-repo work affects them.

**Independent Test**: Can be fully tested by placing sample `feature-brief.md` files in `briefs/` and running `/dai.status` to verify the display includes them.

**Acceptance Scenarios**:

1. **Given** a repo has 1 local feature and 2 linked briefs, **When** `/dai.status` runs, **Then** output shows "Local Features:" section with the local feature and "Linked Features (from other repos):" section with both briefs showing source repo, phase, and task count.
2. **Given** `--verbose` flag is used, **When** `/dai.status` runs, **Then** the full brief content is displayed for each linked feature.
3. **Given** `--all` flag is used, **When** `/dai.status` runs, **Then** both local and linked features are included regardless of completion state.

---

### User Story 5 — Cross-Repo PR and Review Awareness (Priority: P2)

When creating PRs and reviewing code in secondary repos, the tool uses the feature brief for context. PR bodies include "Part of cross-repo feature" headers with source repo references and merge-order dependencies. Reviews compare actual changes against the brief's expected changes.

**Why this priority**: PRs and reviews are the collaboration point where cross-repo awareness matters most for team members who weren't involved in the original planning.

**Independent Test**: Can be fully tested by running `/dai.pr` in a secondary repo that has a brief and verifying the PR body includes cross-repo references and dependency ordering.

**Acceptance Scenarios**:

1. **Given** a secondary repo has a feature brief with tasks and dependencies, **When** `/dai.pr` runs, **Then** the PR body includes "Part of cross-repo feature: {NNN}-{name} (from {source-repo})" and lists which other repo PRs must merge first.
2. **Given** `/dai.review` runs in a secondary repo, **When** checking changes against the brief, **Then** it flags changes not listed in the brief (scope creep) and brief items with no corresponding code changes (incomplete).

---

### User Story 6 — Sibling Repo Detection in Detect Command (Priority: P3)

When running `/dai.detect`, the tool optionally scans `../` for sibling directories that are git repos with `.sln`, `.slnx`, or `.csproj` files and reports them. This feeds useful context into `/dai.configure`.

**Why this priority**: This is a convenience enhancement that makes configure easier but isn't strictly required — configure has its own auto-detection in Step 3a.

**Independent Test**: Can be fully tested by running `/dai.detect` in a directory with sibling repos and verifying the "Sibling repos found:" output appears.

**Acceptance Scenarios**:

1. **Given** 4 sibling directories exist in `../`, 3 of which are git repos with `.sln`/`.slnx`/`.csproj`, **When** `/dai.detect` runs, **Then** a "Sibling repos found:" section lists the 3 repos with their detected type if classifiable.

---

### User Story 7 — Brief Consistency Analysis (Priority: P3)

When running `/dai.analyze`, a new Pass 11 checks that projected briefs in secondary repos match the current spec/plan/tasks in the primary repo. Stale briefs (where the spec changed after projection) are flagged as HIGH severity.

**Why this priority**: This is a safety net — ensures briefs don't drift from the source spec. Less critical because briefs are re-projected idempotently on each phase.

**Independent Test**: Can be fully tested by modifying a spec after briefs were projected, running `/dai.analyze`, and verifying a HIGH-severity finding about stale briefs appears.

**Acceptance Scenarios**:

1. **Given** a brief was projected during specify but the spec was later modified (events changed), **When** `/dai.analyze` runs, **Then** it reports a HIGH-severity "Brief Consistency" finding for the stale brief.
2. **Given** all briefs match current spec/plan/tasks, **When** `/dai.analyze` runs, **Then** Pass 11 reports no findings.

---

### Edge Cases

- What happens when a sibling repo directory in `../` exists but is not a git repo (no `.git/`)? — Skip silently during auto-detection.
- What happens when a configured repo path becomes invalid (directory deleted after configure)? — Warn at the point of use (implement, review, etc.) but don't block the overall workflow.
- What happens when the primary repo is renamed after briefs are projected? — Briefs become stale (source path invalid). The `analyze` command flags this. Re-running the lifecycle phase re-projects with the new name.
- What happens when a brief's source repo directory name contains special characters? — Use the directory name as-is; it's just a folder name within `briefs/`.
- What happens when `/dai.implement` clones a repo via `github:org/repo` that already has briefs from a previous projection? — Preserve existing briefs, update them with current info.
- What happens when two developers independently specify features in the same repo that affect the same secondary repo? — Each gets its own brief under `briefs/{source-repo}/{NNN}-{name}/` — no collision since feature names differ.
- What happens when `../` contains hundreds of directories? — Only check directories for `.git/` presence first (fast check), then only scan git repos for `.sln`/`.slnx`/`.csproj`. Limit to first 20 sibling repos found.
- What happens when the secondary repo has uncommitted changes during brief projection? — The brief file is written but the auto-commit is skipped with a warning, to avoid conflicting with in-progress work. The developer can commit manually later.
- What happens when a brief auto-commit is made on a feature branch in the secondary repo? — The commit is made on whatever branch is currently checked out. If the developer is on a feature branch, the brief commit goes there; if on main, it goes to main.

## Requirements *(mandatory)*

### Functional Requirements

**Configure — Smart Repo Detection (US1)**

- **FR-001**: The `/dai.configure` slash command MUST scan `../` for directories containing `.git/` and at least one `.sln`, `.slnx`, or `.csproj` file during Step 3 (microservice mode only).
- **FR-002**: For each detected sibling repo, the tool MUST attempt quick classification (command, query, processor, gateway, controlpanel) based on code patterns (AggregateRoot → command, EventHandler → query, gRPC clients → gateway, Blazor → controlpanel).
- **FR-003**: The tool MUST present detected repos as suggestions with their classified type and allow the user to accept, reject, or edit each one.
- **FR-004**: The tool MUST accept three input formats for repo paths: local filesystem path, GitHub HTTPS URL (`https://github.com/org/repo`), and git SSH URL (`git@github.com:org/repo.git`).
- **FR-005**: GitHub HTTPS URLs and git SSH URLs MUST be normalized to `github:org/repo` format before storing in config.yml. The `.git` suffix MUST be stripped.
- **FR-006**: For local paths, the tool MUST validate that the directory exists, contains `.git/`, and contains at least one `.sln`, `.slnx`, or `.csproj` file. If validation fails, warn but allow the user to proceed.
- **FR-007**: For GitHub URLs, the tool MAY optionally verify the repo exists using `gh repo view org/repo --json name`. Verification failure MUST warn but not block.
- **FR-008**: Step 3 MUST be skipped entirely for non-microservice (generic) projects.
- **FR-009**: The CLI Python code (`cli.py configure()`) MUST also include repo configuration prompts in the interactive flow, mirroring the slash command Step 3 logic.

**Feature Brief Projection (US2)**

- **FR-010**: During `/dai.specify` (microservice mode), after generating `service-map.md`, the tool MUST project a `feature-brief.md` to each affected secondary repo that has a resolved local path.
- **FR-011**: Briefs MUST be written to `{target-repo}/.dotnet-ai-kit/briefs/{source-repo-name}/{NNN}-{short-name}/feature-brief.md` where `{source-repo-name}` is the current (primary) repo's directory name.
- **FR-012**: Each brief MUST contain: Feature ID, Projected date, Phase, Source Repo name, Source Path, Source Feature path, This Repo's Role, Required Changes, Events (Produces/Consumes), Tasks (This Repo Only), Dependencies (Blocked by/Blocks), and Implementation Approach.
- **FR-013**: During `/dai.clarify`, if clarification answers affect secondary repos (changed events, entities, or service boundaries), affected briefs MUST be re-projected with updated information.
- **FR-014**: During `/dai.plan`, existing briefs MUST be updated with the "Implementation Approach" section and phase changed to "Planned".
- **FR-015**: During `/dai.tasks`, existing briefs MUST be updated with the "Tasks (This Repo Only)" section containing only tasks tagged `[Repo:this-repo]`, and phase changed to "Tasks Generated".
- **FR-016**: During `/dai.implement`, when tasks complete in a secondary repo, the brief MUST be updated: task checkmarks, phase to "Implementing" then "Implemented". On failure: phase to "Blocked".
- **FR-017**: Brief projection MUST be idempotent — re-running any lifecycle phase overwrites stale briefs with fresh content.
- **FR-018**: Brief projection MUST be best-effort — if a secondary repo is not cloned locally or not configured, skip with a note in the report. Never fail the primary workflow because of projection.
- **FR-035**: After projecting a brief to a secondary repo, the tool MUST auto-commit the brief in that repo. Commit message format: `chore: project feature brief {NNN}-{name} from {source-repo-name}` for initial projection, `chore: update feature brief {NNN}-{name} — {phase}` for subsequent updates. This format MUST be used consistently by all commands that project or update briefs (specify, clarify, plan, tasks, implement).
- **FR-036**: If the secondary repo has uncommitted changes that would conflict with the brief commit, the tool MUST warn and skip the auto-commit (leaving the brief as an uncommitted file) rather than risking data loss.

**Directory Isolation (US3)**

- **FR-019**: Briefs MUST live in `.dotnet-ai-kit/briefs/` which is separate from `.dotnet-ai-kit/features/`.
- **FR-020**: Feature numbering in `/dai.specify` MUST scan only `.dotnet-ai-kit/features/` for the next number. The `briefs/` directory MUST be ignored for numbering.
- **FR-021**: `/dai.init` (including `--force` reinit) MUST never delete, modify, or overwrite the `briefs/` directory or its contents.
- **FR-022**: If `briefs/` exists with content during init, the tool MUST warn: "This repo has linked features from other repos (in .dotnet-ai-kit/briefs/). They will be preserved."
- **FR-023**: Multiple source repos MUST be able to project briefs to the same target repo without collision, namespaced by source repo directory name under `briefs/`.

**Status and Lifecycle Integration (US4, US5, US6, US7)**

- **FR-024**: `/dai.status` MUST display linked features from `briefs/` separately from local features, showing source repo name, feature name, phase, and task progress.
- **FR-025**: `/dai.pr` in a secondary repo MUST include "Part of cross-repo feature: {NNN}-{name} (from {source-repo})" in the PR body and reference the primary repo PR URL.
- **FR-026**: `/dai.pr` in a secondary repo MUST include merge-order dependencies from the brief's "Dependencies" section.
- **FR-027**: `/dai.review` in a secondary repo MUST load the feature brief and compare actual changes against expected changes (Check 9 — Brief Compliance). The check MUST be numbered sequentially after the last existing check.
- **FR-028**: `/dai.detect` MUST optionally scan `../` for sibling repos and report them as "Sibling repos found:" with detected type.
- **FR-029**: `/dai.analyze` MUST include Pass 11 — Brief Consistency, flagging stale briefs (HIGH) and minor drift (MEDIUM).
- **FR-030**: `/dai.wrap-up` and `/dai.checkpoint` MUST include brief status in handoff notes.

**Model and Validation (cross-cutting)**

- **FR-031**: The `ReposConfig` validator in `models.py` MUST accept and normalize GitHub HTTPS URLs (`https://github.com/org/repo`, `https://github.com/org/repo.git`) and git SSH URLs (`git@github.com:org/repo.git`) to `github:org/repo` format.
- **FR-032**: A new `FeatureBrief` pydantic model MUST be added to `models.py` for programmatic validation of brief content.
- **FR-033**: All `.sln` references throughout the tool MUST also include `.slnx` (new .NET solution format).

**Undo and Config Template (cross-cutting)**

- **FR-037**: `/dai.undo` MUST document in its Safety Rules section that projected briefs in secondary repos are NOT automatically reverted. The user must manually delete briefs or revert the auto-commit in secondary repos.
- **FR-038**: The `config-template.yml` repos section comment MUST document the three accepted input formats: local path, GitHub HTTPS URL, and git SSH URL.
- **FR-039**: The `_scan_sibling_repos()` function in `cli.py` MUST use only recursive glob patterns (`**/*.cs`, `**/*.csproj`) to avoid redundant non-recursive+recursive pattern pairs.

**Skill Documentation (cross-cutting)**

- **FR-034**: The `multi-repo-workflow` skill MUST be updated with a "Feature Brief Projection" section documenting the briefs directory structure, lifecycle phases, format, and interaction with init.

### Key Entities

- **Feature Brief**: A self-contained markdown document projected to a secondary repo containing that repo's filtered view of a cross-repo feature. Attributes: feature ID, phase, source repo, role, required changes, events, tasks, dependencies, implementation approach.
- **Briefs Directory**: The `.dotnet-ai-kit/briefs/{source-repo-name}/{NNN}-{name}/` structure that isolates projected briefs from local features. Namespaced by source repo to prevent collisions.
- **Repo Reference**: A configured path to a microservice repo. Can be: local filesystem path, `github:org/repo` (normalized from GitHub URL or SSH URL), or null (not configured).

## Assumptions

- The primary repo (where `/dai.specify` runs) always keeps full artifacts (spec.md, plan.md, tasks.md, service-map.md) in `features/` — nothing changes there.
- The source repo name used in the briefs path is the directory name of the primary repo (e.g., if the primary repo is at `../company-domain-command/`, the source name is `company-domain-command`).
- Briefs do not require dotnet-ai-kit to be initialized in the secondary repo — projecting a brief only creates the `.dotnet-ai-kit/briefs/` directory structure.
- The `../` scan for sibling repos is limited to direct children of the parent directory (not recursive).
- Sibling repo auto-detection caps at 20 repos to avoid performance issues.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can configure all microservice repo paths in under 2 minutes using auto-detection suggestions, compared to the current manual-only approach.
- **SC-002**: After running `/dai.specify` for a cross-repo feature, 100% of affected secondary repos with local paths have a `feature-brief.md` containing their filtered role and changes.
- **SC-003**: A developer opening a secondary repo can see all linked cross-repo features within 5 seconds by running `/dai.status`.
- **SC-004**: Feature numbering in any repo is always correct — local features start at 001 regardless of how many briefs exist from other repos.
- **SC-005**: Running `/dai.init --force` in a repo with existing briefs preserves 100% of the briefs directory content.
- **SC-006**: All 15 affected commands across the SDD lifecycle correctly read, write, or respect feature briefs without manual intervention.
- **SC-007**: Two source repos projecting features with the same number to the same target repo results in zero collisions.

## Clarifications

### Session 2026-03-30

- Q: Should projected briefs be git-committed in the secondary repo? → A: Yes, auto-commit with descriptive message (`chore: project feature brief {NNN}-{name} from {source-repo-name}`). Skip auto-commit if secondary repo has uncommitted changes that would conflict.
