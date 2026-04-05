# Feature Specification: Architecture Profiles, Multi-Repo Deployment, and Enforcement Optimization

**Feature Branch**: `015-arch-enforcement-multi-repo`  
**Created**: 2026-04-02  
**Status**: Draft  
**Input**: User description: "Architecture Profiles, Multi-Repo Deployment, and Enforcement Optimization — 7-part feature covering project-type-specific constraint profiles, multi-repo tooling deployment, auto-commit branch safety, Claude Code prompt hooks, universal agent frontmatter, skill auto-activation, and command context optimization."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Project-Type-Specific Architecture Enforcement (Priority: P1)

A developer initializes dotnet-ai-kit in a command-side CQRS microservice project and runs `/dai.configure`. The tool detects the project type as "command" and deploys a command-specific architecture profile as an always-loaded rule. When the developer later runs `/dai.specify` or `/dai.plan`, the AI reads the profile's hard constraints (e.g., "NEVER commit more than one aggregate per handler", "ALWAYS use the project's integration test patterns") and refuses to produce specs or plans that violate them. This prevents architectural mistakes at the design phase, before any code is written.

**Why this priority**: This is the core problem. Feature 001 failures (dual-aggregate handler, wrong test patterns) happened because no project-type-specific constraints existed. Profiles are the foundation all other parts build on.

**Independent Test**: Can be fully tested by deploying a command profile to a test project and verifying the AI tool's rules directory contains the profile with correct constraints. Delivers value immediately — even without hooks or multi-repo, profiles improve AI output quality.

**Acceptance Scenarios**:

1. **Given** a project with `project_type: command` in `project.yml`, **When** user runs `dotnet-ai configure`, **Then** the file `architecture-profile.md` appears in the AI tool's rules directory containing command-specific hard constraints, and no other profile is deployed.
2. **Given** a project with `project_type: vsa` in `project.yml`, **When** user runs `dotnet-ai configure`, **Then** a VSA-specific profile is deployed instead of the command profile.
3. **Given** a project with no `project_type` or `confidence: low`, **When** user runs `dotnet-ai configure`, **Then** the generic fallback profile is deployed.
4. **Given** a deployed command profile, **When** a spec/plan attempts to use two aggregates in one handler, **Then** the AI rejects the approach citing the profile constraint.

---

### User Story 2 - Multi-Repo Tooling Deployment (Priority: P2)

A developer has a primary command repo (fully initialized with dotnet-ai-kit) linked to a query repo and a processor repo. During `configure`, after linking the repos, the tool deploys the correct architecture profiles, agents, skills, and rules to each secondary repo based on its detected project type. Each secondary repo gets its own profile (query profile for query, processor profile for processor). The developer no longer needs to manually initialize each secondary repo's AI tooling.

**Why this priority**: Secondary repos currently have zero architectural guardrails. When the AI implements tasks in linked repos, there is no guidance. This is the second most impactful gap after profiles themselves.

**Independent Test**: Can be tested by initializing two repos, linking them via configure, and verifying the secondary repo receives the correct profile, agents, and rules on a dedicated branch.

**Acceptance Scenarios**:

1. **Given** a primary repo linked to an initialized secondary repo, **When** user runs `dotnet-ai configure` and links the secondary, **Then** the secondary repo receives its matching profile, rules, agents, skills, and a `linked_from` back-reference in its config.
2. **Given** a secondary repo that is NOT initialized (no `.dotnet-ai-kit/` directory), **When** configure tries to deploy, **Then** a warning is shown: "Run `dotnet-ai init` and `/dai.detect` in {repo} first." The repo is skipped.
3. **Given** a secondary repo with a newer tool version than the primary, **When** configure tries to deploy, **Then** deployment is skipped with a warning about the version mismatch.
4. **Given** a secondary repo with an older tool version, **When** configure deploys, **Then** the secondary is upgraded and receives the full tooling stack.

---

### User Story 3 - Auto-Commit Branch Safety (Priority: P2)

A developer runs `/dai.specify` which projects a feature brief to linked secondary repos. Instead of committing the brief directly to whatever branch the secondary repo is on (potentially main/master/develop), the tool creates a dedicated `chore/brief-{NNN}-{name}` branch, commits there, and optionally offers to create a PR.

**Why this priority**: Direct commits to protected or shared branches is dangerous. This safety fix is critical for multi-repo workflows and pairs directly with Story 2.

**Independent Test**: Can be tested by running specify with a linked repo and verifying the commit lands on a dedicated chore branch, not the current branch.

**Acceptance Scenarios**:

1. **Given** a linked secondary repo on `main` branch, **When** `/dai.specify` projects a brief, **Then** a `chore/brief-{NNN}-{name}` branch is created and the brief is committed there, not on `main`.
2. **Given** an existing `chore/brief-015-arch-enforcement` branch in a secondary repo, **When** `/dai.plan` updates the brief, **Then** the update is committed on the existing branch (reused, not recreated).
3. **Given** a secondary repo with uncommitted changes, **When** auto-commit is attempted, **Then** the operation is skipped with a warning about dirty working directory.
4. **Given** `dotnet-ai configure` deploying to a secondary repo, **When** deployment completes, **Then** all changes are committed on `chore/dotnet-ai-kit-setup` branch.

---

### User Story 4 - Code-Time Enforcement via Claude Code Hooks (Priority: P3)

A developer using Claude Code writes code that violates a profile constraint (e.g., a handler that modifies two aggregates). Before the Write/Edit tool executes, a PreToolUse prompt hook intercepts the operation, sends the code and constraints to a fast model (haiku) for behavioral validation, and blocks the write with a specific violation message. The developer is told exactly which constraint was violated and why.

**Why this priority**: Profiles are design-time guidance the AI reads but could theoretically ignore. Hooks add a second enforcement layer that actively blocks violations at code-write time. Important but only for Claude Code users — profiles must work alone for other tools.

**Independent Test**: Can be tested by configuring a hook, then attempting to write a .cs file that violates a constraint, and verifying the hook blocks it with a reason.

**Acceptance Scenarios**:

1. **Given** a deployed command profile with hooks enabled, **When** the AI attempts to write a `.cs` file that violates "one aggregate per handler", **Then** the hook returns `{"ok": false, "reason": "..."}` and blocks the write.
2. **Given** a deployed profile with hooks, **When** the AI writes a `.md` or `.json` file, **Then** the hook immediately returns `{"ok": true}` without running constraint checks.
3. **Given** a project configured with `cursor` (not `claude`), **When** configure runs, **Then** no hooks are deployed (hooks are Claude Code only).
4. **Given** an updated profile after re-running configure, **When** the hook prompt is regenerated, **Then** the new constraints are embedded in the hook and enforced immediately.

---

### User Story 5 - Universal Agent Frontmatter (Priority: P3)

A developer using the tool has 13 agent definitions that use tool-agnostic fields (role, expertise, complexity, max_iterations). When `configure` deploys agents for Claude Code, the copier transforms these universal fields into Claude Code-specific frontmatter (disallowedTools, skills, effort, model, maxTurns). The same agent source files will work for Cursor, Copilot, or Codex in future versions without any changes to agent files.

**Why this priority**: Agent frontmatter optimization improves agent behavior quality and future-proofs the tool for multi-AI-tool support. Lower priority than enforcement features but foundational for tool scalability.

**Independent Test**: Can be tested by deploying an agent with `role: advisory` to Claude Code and verifying the output contains `disallowedTools: [Write, Edit]`.

**Acceptance Scenarios**:

1. **Given** an agent file with `role: advisory`, **When** deployed for Claude Code, **Then** the output file contains `disallowedTools: [Write, Edit]` in frontmatter.
2. **Given** an agent file with `complexity: high`, **When** deployed for Claude Code, **Then** the output contains `effort: high` and `model: opus`.
3. **Given** an agent file with `expertise: [aggregate-design, event-design]`, **When** deployed for Claude Code, **Then** the output contains `skills: [aggregate-design, event-design]`.
4. **Given** `ai_tools: [cursor]` in config, **When** agents are deployed, **Then** a warning is logged: "Agent transformation for cursor not yet supported" and agent deployment is skipped for that tool.

---

### User Story 6 - Skill Auto-Activation (Priority: P3)

A developer is working on an aggregate file. The AI tool (Claude Code) automatically loads the `aggregate-design` skill because the file path matches the detected path from `project.yml`. Alternatively, when the user says "create a new aggregate", the skill is loaded via the `when-to-use` behavioral trigger even if paths are not configured.

**Why this priority**: Skills are currently passive — loaded only when commands explicitly reference them. Auto-activation makes skills context-aware, improving AI output without manual invocation. Lower priority because it's a quality improvement, not a critical gap.

**Independent Test**: Can be tested by configuring detected paths, deploying a skill with path tokens resolved, and verifying the skill frontmatter contains the correct resolved path.

**Acceptance Scenarios**:

1. **Given** `detected_paths.aggregates: "Company.Domain/Core"` in `project.yml` and a skill with `paths: "${detected_paths.aggregates}/**/*.cs"`, **When** skills are deployed, **Then** the deployed skill has `paths: "Company.Domain/Core/**/*.cs"`.
2. **Given** a skill with an unresolved `${detected_paths.cosmos}` token and no `cosmos` path in `project.yml`, **When** skills are deployed, **Then** the `paths` field is omitted and the skill relies on `when-to-use` for activation.
3. **Given** a deployed skill with `when-to-use: "When creating or modifying event-sourced aggregates"`, **When** the user asks to "create a new aggregate", **Then** the AI auto-loads the skill.

---

### User Story 7 - Command Context Optimization (Priority: P4)

A developer runs `/dai.review` which produces large analysis output. Instead of polluting the main conversation context, the command runs in a forked subagent context. The developer's main context stays clean for continued work. The review results are still visible but don't consume main context tokens.

**Why this priority**: Context optimization is a quality-of-life improvement. Important for long sessions but doesn't prevent architectural violations. Lowest priority.

**Independent Test**: Can be tested by verifying the command file contains `context: 'fork'` and `agent` fields in frontmatter.

**Acceptance Scenarios**:

1. **Given** the updated `/dai.review` command with `context: 'fork'`, **When** user runs the command, **Then** it executes in a subagent context, not inline.
2. **Given** the `/dai.detect` command (unchanged), **When** user runs it, **Then** it executes inline because its output is needed in main context.
3. **Given** `/dai.review` with `agent: reviewer`, **When** forked, **Then** the reviewer agent handles the execution.

---

### Edge Cases

- What happens when a project type changes after initial detection (e.g., a generic project is later re-detected as a command project)? The old profile is overwritten with the new one during re-configure.
- What happens when two linked repos have conflicting versions? Each repo is handled independently — version check is per-repo, not global.
- What happens when the hook prompt exceeds Claude Code's settings size limits? The profile is capped at 100 lines, and only the HARD CONSTRAINTS section is extracted, keeping the prompt compact.
- What happens when a skill has both `paths` and `when-to-use`, and neither matches? The skill is not auto-loaded but remains available for explicit command invocation.
- What happens when `dotnet-ai upgrade` runs but linked repos are on different branches? Each repo's branch state is independent — upgrade creates its own branch regardless.
- What happens when a secondary repo's local path no longer exists (moved/deleted)? Configure warns "Cannot access {path}" and skips the repo.
- What happens when deployment to one of several linked repos fails (git error, permissions)? The failure is logged, remaining repos continue deploying, and a summary of successes/failures is shown at the end.
- What happens when a secondary repo is un-linked from the primary? Deployed tooling (profiles, agents, skills, rules) is left in place — no cleanup. The `linked_from` field remains in the secondary repo's config until manually removed.

## Requirements *(mandatory)*

### Functional Requirements

**Architecture Profiles (Part 1)**

- **FR-001**: Tool MUST maintain 12 architecture profile files (7 microservice + 5 generic) covering all supported project types.
- **FR-002**: Each profile MUST be under 100 lines and use NEVER/ALWAYS/MUST/MUST NOT constraint language.
- **FR-003**: During `configure`, tool MUST deploy exactly ONE profile matching the detected project type to the AI tool's rules directory.
- **FR-004**: If no project type is detected or confidence is low, tool MUST deploy the generic fallback profile.
- **FR-005**: Profile deployment MUST work for all configured AI tools (claude, cursor, copilot, codex) by placing the profile in each tool's rules directory.
- **FR-006**: During `upgrade`, tool MUST re-deploy the profile to match the current tool version.
- **FR-007**: Total rules (existing 15 + 1 profile) MUST stay within the ~900-line budget.

**Multi-Repo Deployment (Part 2)**

- **FR-008**: During `configure`, when repos are linked, tool MUST deploy the full tooling stack (profiles, rules, agents, skills) to each initialized secondary repo with a local path.
- **FR-009**: Tool MUST check if each secondary repo is initialized before deployment. If not, warn and skip.
- **FR-010**: Tool MUST version-check secondary repos: upgrade if older, add profile if same version, skip if newer.
- **FR-011**: Tool MUST write a `linked_from` field to each secondary repo's config pointing to the primary repo.
- **FR-012**: During `upgrade`, tool MUST re-deploy to all linked repos with version-checking.
- **FR-013**: Tool MUST skip deployment for repos referenced as remote URLs (not cloned locally).
- **FR-013a**: If deployment to a secondary repo fails, tool MUST log the failure, continue deploying to remaining repos, and report a summary of successes and failures at the end.

**Auto-Commit Branch Safety (Part 3)**

- **FR-014**: All secondary repo auto-commit operations MUST use dedicated branches, never committing directly to main/master/develop.
- **FR-015**: Brief projections (specify/plan/tasks) MUST use `chore/brief-{NNN}-{name}` branches with reuse logic.
- **FR-016**: Tooling deployments (configure/upgrade) MUST use `chore/dotnet-ai-kit-setup` or `chore/dotnet-ai-kit-upgrade-{version}` branches.
- **FR-017**: If a secondary repo has uncommitted changes, auto-commit MUST be skipped with a warning.

**Claude Code Prompt Hooks (Part 4)**

- **FR-018**: When `claude` is in `ai_tools`, tool MUST deploy a PreToolUse prompt hook that validates Write/Edit operations against profile constraints.
- **FR-019**: The hook MUST only validate .NET files (.cs, .csproj, .sln, .slnx, .razor, .proto, .cshtml) and immediately approve all other file types.
- **FR-020**: The hook prompt MUST be a static string embedded at deployment time with constraints baked in from the profile.
- **FR-021**: Hook MUST NOT be deployed for non-Claude tools.

**Agent Universal Schema (Part 5)**

- **FR-022**: All agent source files MUST use universal frontmatter fields (role, expertise, complexity, max_iterations) with no tool-specific fields.
- **FR-023**: During deployment, tool MUST transform universal fields to tool-specific format using a mapping configuration.
- **FR-024**: For unsupported tools, agent deployment MUST be skipped with a warning log.
- **FR-025**: Expertise values MUST match registered skill names.

**Skill Optimization (Part 6)**

- **FR-026**: Skills MUST use `${detected_paths.*}` tokens for path-based activation, resolved during deployment from `project.yml`.
- **FR-027**: If a detected path is not available, the `paths` field MUST be omitted (skill remains globally available).
- **FR-028**: Skills MUST include a `when-to-use` field for behavioral activation as a fallback.
- **FR-029**: The `/dai.detect` command MUST populate a `detected_paths` section in `project.yml`.

**Command Context Optimization (Part 7)**

- **FR-030**: `/dai.review`, `/dai.verify`, and `/dai.check` commands MUST use `context: 'fork'` to run in subagent context.
- **FR-031**: Forked commands MUST specify an `agent` field for the handling agent type.

### Key Entities

- **Architecture Profile**: A per-project-type constraint file (markdown with frontmatter) containing hard constraints. Attributes: project type, constraint rules, anti-pattern examples. One profile is deployed per project.
- **Detected Paths**: A mapping of logical path categories (aggregates, events, handlers, tests, etc.) to actual filesystem paths discovered during project detection. Stored in `project.yml`.
- **Linked Repo**: A secondary repository in a multi-repo microservice setup, referenced from the primary repo's config. Attributes: local path, project type, tool version, linked_from back-reference.
- **Agent Frontmatter Map**: A per-tool configuration that transforms universal agent fields to tool-specific frontmatter during deployment.
- **Prompt Hook**: A Claude Code PreToolUse hook configuration containing a static constraint prompt, deployed to `.claude/settings.json`.

## Clarifications

### Session 2026-04-02

- Q: If deploying to multiple linked repos and one fails, what should the tool do? → A: Log failure, continue to next repo, report summary at end.
- Q: When a secondary repo is un-linked, should the tool clean up deployed tooling? → A: No — leave deployed tooling in place. User can manually delete if needed.
- Correction: gateway-architect expertise removes `authorization` (no matching skill exists). Actual list: [gateway-endpoint, endpoint-registration, gateway-security, scalar-docs, versioning].
- Correction: Agent-specific updates cover all 13 agents (original prompt listed 10; devops-engineer, docs-engineer, and controlpanel-architect were missing from the list but are included in implementation).

## Assumptions

- Each secondary repo must be independently initialized (`dotnet-ai init`) and detected (`/dai.detect`) before it can be linked. The primary repo's configure does not run detection in secondary repos.
- Only the `claude` tool mapping is implemented in v1.0. Other tool mappings (cursor, copilot, codex) are placeholder stubs for v1.0.1+.
- Profile constraints are derived exclusively from existing skills and rules. No new architectural conventions are introduced.
- The `gh` CLI is available for optional PR creation in secondary repos. If not available, PR creation is skipped silently.
- Skill `paths` and `when-to-use` are Claude Code features. For other AI tools, skills remain manually loaded via commands.
- The hook model (haiku) has a 15-second timeout. If the check exceeds this, the write proceeds (fail-open, not fail-close).
- Un-linking a secondary repo does not trigger cleanup of deployed tooling. Profiles/agents/skills remain in the secondary repo.
- Undo (`/dai.undo`) coverage for new operations (profile deployment, hook deployment, multi-repo deployment) is deferred to a follow-up. Reversal is handled via `upgrade` (re-deploys current version) or manual deletion. Adding undo support for these operations is out of scope for this feature.
- Profile deployment to tools with no `rules_dir` (e.g., codex) is a no-op — `copy_profile()` returns None and skips gracefully.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of supported project types (12 types) have a corresponding architecture profile that passes the under-100-lines budget check.
- **SC-002**: When a profile is deployed, the AI correctly rejects spec/plan proposals that violate the profile's top 3 hard constraints in at least 90% of test cases.
- **SC-003**: Multi-repo deployment successfully deploys the correct project-type-specific profile to linked secondary repos in under 30 seconds per repo.
- **SC-004**: Zero auto-commits land on main/master/develop branches in secondary repos across all tool operations (configure, specify, plan, tasks, upgrade).
- **SC-005**: Claude Code prompt hooks catch behavioral violations (e.g., multi-aggregate handler) with at least 80% accuracy when tested against known violation patterns.
- **SC-006**: Agent frontmatter transformation produces valid tool-specific output for all 13 agents with no manual fixups required.
- **SC-007**: Adding a new AI tool in a future version requires changes to only `agents.py` (adding a mapping entry) with zero changes to agent source files.
- **SC-008**: Skills with both `paths` and `when-to-use` auto-activate in at least 90% of relevant contexts during Claude Code sessions.
- **SC-009**: Existing initialized projects continue working without changes after tool upgrade (no breaking changes).
- **SC-010**: All 6 new test files pass with 100% of test cases green.
