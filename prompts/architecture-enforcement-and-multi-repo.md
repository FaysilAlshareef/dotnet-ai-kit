# Feature: Architecture Profiles, Multi-Repo Deployment, and Enforcement Optimization

## Problem Statement

The dotnet-ai-kit has comprehensive architecture knowledge (rules, skills, agents) but fails to prevent design and implementation violations because:

1. **Rules are generic** — all 15 rules apply to all project types. A VSA project gets microservice rules, a command-side project gets gateway rules. No project-type-specific constraints exist.
2. **Enforcement is reactive** — violations are caught at review time (`/dai.review`), not prevented during spec, plan, tasks, or implement phases.
3. **Secondary repos have no tooling** — in multi-repo microservice mode, only the primary repo has rules/agents/skills. When `/dai.implement` executes tasks in secondary repos (query, processor, gateway, controlpanel), there are zero architectural guardrails.
4. **Auto-commits in secondary repos go to the current branch** — during spec/plan/tasks phases, feature briefs are committed directly to whatever branch the secondary repo is on, without creating a dedicated branch. This is dangerous if the branch has protection rules or is shared.
5. **Agent frontmatter is underutilized** — agents don't declare their expertise (preloaded knowledge), role constraints (advisory vs implementation), complexity level, or iteration limits, forcing commands to manually orchestrate what the agent system handles natively.
6. **Skills are passive** — skills are only loaded when commands explicitly reference them. They don't auto-activate based on file paths, don't register session hooks for enforcement, and don't declare `when-to-use` for model auto-invocation.
7. **No code-time enforcement for Claude Code** — Claude Code supports PreToolUse prompt hooks that can block writes/edits, but the tool doesn't use them. Profile constraints are text the AI reads (can ignore), not hooks that block execution.

### Real-World Impact

In the Competition-Points project, feature 001 had two critical failures:
- **Two aggregates committed in one handler** (`RequestPointsExchangeHandler` committed both `PointsExchange` and `AccountPoints` in separate transactions) — broke event sourcing rules. Required a full rewrite in feature 002.
- **Tests didn't follow project patterns** — only basic unit tests were written instead of the project's established integration test pattern (WebApplicationFactory, GrpcClientHelper, DbContextHelper, CustomConstructorFaker, assertion extensions).

Both failures would have been prevented if project-type-specific constraints existed during the spec and plan phases.

---

## Feature Description

### Part 1: Architecture Profiles

Create a new `profiles/` directory containing per-project-type constraint files. Each profile is a markdown file with `alwaysApply: true` frontmatter that gets deployed as a rule to the project's AI tool rules directory.

**Profile directory structure:**

```
profiles/
  microservice/
    command.md
    query-sql.md
    query-cosmos.md
    processor.md
    gateway.md
    controlpanel.md
    hybrid.md
  generic/
    vsa.md
    clean-arch.md
    ddd.md
    modular-monolith.md
    generic.md
```

**`hybrid` profile:** For projects detected as single-repo with both command and query sides. Combines the key constraints from command and query profiles — aggregate boundaries, event handler idempotency, and sequence checking. Must stay under 100 lines so it focuses on the highest-severity constraints from both sides.

**`generic` profile:** A minimal baseline profile for projects where detection couldn't determine a specific architecture. Contains only universal .NET constraints: layer dependency direction, no circular references, test coverage requirements. This is the fallback — if detection fails or confidence is too low, the generic profile is deployed.

**Fallback logic:** If `.dotnet-ai-kit/project.yml` has no `project_type` or detection confidence is `low`, deploy `generic/generic.md`. Never skip profile deployment — every project gets at least the generic baseline.

**Profile content requirements:**
- Each profile must be under 100 lines (rule token budget).
- Written as HARD CONSTRAINTS using NEVER/ALWAYS/MUST/MUST NOT language — not soft guidance.
- Include explicit anti-pattern examples showing what NOT to do and why.
- Cover: architecture boundaries, aggregate/entity design, event patterns, testing requirements, data access patterns, and error handling specific to that project type.
- Constraints must be derived from existing skills and rules — no new conventions, just project-type-specific enforcement of existing knowledge.

**Profile deployment:**
- During `configure` (after project type is detected), copy the matching profile to the AI tool's rules directory (e.g., `.claude/rules/architecture-profile.md` for Claude Code).
- During `upgrade`, re-deploy the profile to match the current version.
- Only ONE profile is deployed per project — the one matching the detected project type from `.dotnet-ai-kit/project.yml`.
- Profile deployment must work for all configured AI tools (claude, cursor, copilot, codex) — each tool gets the profile in its rules directory format.

**Token budget impact:**
- Current rules: 803 lines (15 rules).
- Profile adds: ~80-100 lines (1 rule file per project).
- New total: ~883-903 lines. Must fit within ~900-line budget.
- 12 profile files total (10 specific + hybrid + generic), but only ONE is deployed per project.

### Part 2: Multi-Repo Deployment (Option B)

When the user links repos during `configure` (step 3: repository paths), the tool must deploy the full tooling stack to each linked secondary repo.

**Prerequisite:** Each secondary repo must be independently initialized and detected BEFORE linking. The user runs `dotnet-ai init` and `/dai.detect` in each secondary repo first. This ensures each repo has its own `.dotnet-ai-kit/config.yml` and `.dotnet-ai-kit/project.yml` with a detected project type. Configure in the primary repo then deploys profiles/agents/skills based on the already-detected type — it does NOT run detection itself (detection requires AI context which the Python CLI doesn't have).

**Deployment flow during configure:**
1. User links repos (command, query, processor, gateway, controlpanel) with local paths or GitHub URLs.
2. For each linked repo with a local path:
   a. Check if the secondary repo is initialized (has `.dotnet-ai-kit/config.yml` and `.dotnet-ai-kit/project.yml`).
   b. If NOT initialized: warn the user — "Run `dotnet-ai init` and `/dai.detect` in {repo} first." Skip this repo.
   c. If initialized: read its `project.yml` to get the detected project type.
   d. **Version check:** Compare the secondary repo's `.dotnet-ai-kit/version.txt` with the primary repo's tool version.
      - If secondary is older: deploy updated commands, rules, skills, agents, and the matching architecture profile. Log "Upgrading {repo} from {old} to {new}."
      - If secondary is same version: deploy only the architecture profile (if not already deployed) and update config with back-link. Log "Adding profile to {repo}."
      - If secondary is newer: skip deployment, warn "Secondary repo {repo} has newer version {v}. Run upgrade from there instead."
   e. Write `linked_from` field to the secondary repo's `.dotnet-ai-kit/config.yml` pointing to the primary repo.
   f. Create a new branch `chore/dotnet-ai-kit-setup` in the secondary repo.
   g. Commit all deployed/updated files on that branch.
   h. Optionally create a PR via `gh pr create` (if user confirms).
3. For repos referenced as `github:org/repo` (not cloned locally): skip deployment, warn the user.
4. For null/unconfigured repos: skip silently.

**Upgrade flow:**
- `dotnet-ai upgrade` must re-deploy to all linked repos from the saved config.
- For each linked repo: version-check, deploy updated files if secondary is older or same version.
- Create branch `chore/dotnet-ai-kit-upgrade-{version}` in each secondary repo.
- Commit updated files on that branch.

**Config back-link:**
- Each secondary repo's `.dotnet-ai-kit/config.yml` must include a `linked_from` field pointing to the primary repo, so the secondary repo knows it's part of a multi-repo setup. This field is added to the `DotnetAiConfig` pydantic model in `models.py`.

### Part 3: Auto-Commit Branch Fix

Fix all secondary repo auto-commit operations to use dedicated branches instead of committing directly to the current branch.

**Operations that auto-commit to secondary repos:**

| Phase | Operation | Current Behavior | Fixed Behavior |
|-------|-----------|-----------------|----------------|
| configure | Deploy tooling | Doesn't exist yet | Branch: `chore/dotnet-ai-kit-setup` |
| specify | Project feature brief | Direct commit on current branch | Branch: `chore/brief-{NNN}-{name}` |
| plan | Update brief | Direct commit on current branch | Same branch as specify (reuse) |
| tasks | Update brief | Direct commit on current branch | Same branch as specify (reuse) |
| implement | Execute tasks | Creates feature branch (OK) | No change needed |
| upgrade | Re-deploy tooling | Doesn't exist for linked repos | Branch: `chore/dotnet-ai-kit-upgrade-{version}` |

**Branch reuse logic:**
- For brief projections (specify/plan/tasks): check if a `chore/brief-{NNN}-{name}` branch exists. If yes, reuse it. If no, create it.
- For tooling deployment: always create a new branch.
- After all commits on a branch, optionally offer to create a PR.

**Where branch creation logic lives:**
- For configure and upgrade (Python CLI commands): branch creation logic is in `cli.py` — these are Python-driven operations.
- For specify, plan, and tasks (AI slash commands): branch creation instructions must be added to the **command markdown files** (`dai.specify.md`, `dai.plan.md`, `dai.tasks.md`) — these are AI-driven operations where the AI executes git commands based on the command instructions. The Python CLI is not involved in these phases.

**Safety:**
- Never commit to main/master/develop branches directly.
- If the secondary repo has uncommitted changes, warn and skip (existing behavior — keep this).
- If the branch already exists with unpushed commits, reuse it and add commits on top.

### Part 4: Claude Code Prompt Hooks (CC-Only Enhancement)

Add a PreToolUse prompt hook for Claude Code that validates Write/Edit operations against the architecture profile constraints using haiku.

**Why prompt hooks, not shell/regex hooks:**
- Architecture violations are **behavioral**, not textual. "This handler touches two aggregates" can be written infinite ways — no regex catches all of them.
- An LLM (haiku) understands behavior: it can read code and determine if it violates a constraint regardless of naming, patterns, or style.
- One generic hook works for ALL project types because it reads the profile — no per-project-type hook scripts.

**Hook structure:**
- One hook configuration deployed when `claude` is in `config.ai_tools`.
- The hook is a `type: "prompt"` PreToolUse hook on `Write|Edit` matcher.
- The prompt is a **static string** embedded in `.claude/settings.json` at deployment time — not a dynamic file reference. Prompt hooks cannot read the filesystem at runtime.
- Model: `claude-haiku-4-5-20251001` (fast, cheap — ~2-5 seconds, ~$0.001 per check).
- Timeout: 15 seconds.
- The hook returns `{"ok": true}` or `{"ok": false, "reason": "specific violation"}`.

**File scope — .NET files only:**
- The hook must only validate .NET-relevant files to avoid wasted latency on non-architecture files.
- The hook prompt must instruct haiku to immediately return `{"ok": true}` for files that are NOT one of: `.cs`, `.csproj`, `.sln`, `.slnx`, `.razor`, `.proto`, `.cshtml`. This avoids running architecture checks on `.md`, `.json`, `.yml`, `.xml`, and other non-.NET files.

**Profile as single source of truth:**
- During deployment, `copier.py` reads the profile's HARD CONSTRAINTS section, extracts the constraint text, and embeds it directly into the hook prompt string in `settings.json`. The prompt hook does NOT read the profile file at runtime — the constraints are baked into the prompt at deployment time.
- Adding a new constraint to the profile means re-running `configure` or `upgrade` to regenerate the hook prompt with the updated constraints.
- The profile drives both layers: AI reads the file (design-time), hook prompt contains the same constraints as a static string (code-time).

**Cross-tool note:**
- Hooks are Claude Code only. Cursor, Copilot, and Codex do not support hooks.
- The profile must be strong enough to work alone for non-CC tools.
- Hooks are a bonus safety net for Claude Code users, not a requirement for correctness.

**Deployment:**
- During `configure`, if `claude` is in `ai_tools`:
  1. Read the deployed profile's HARD CONSTRAINTS section.
  2. Build the hook prompt string by embedding the constraint text into a prompt template.
  3. Write the PreToolUse hook entry (with the static prompt string) into `.claude/settings.json` under the hooks key.
- During `upgrade`, if the profile version changed, regenerate the hook prompt string and update `.claude/settings.json`.

### Part 5: Agent Frontmatter Optimization (Universal Schema)

Update all 13 agent definition files to use a **universal frontmatter schema** that maps to tool-specific formats during deployment. This ensures adding support for Cursor, Copilot, and Codex in future versions does not require rewriting agent files.

**Problem with tool-specific frontmatter:**
Fields like `disallowedTools`, `skills` (preloading), and `maxTurns` are Claude Code-specific. If we lock these into agent files now, supporting Cursor/Copilot/Codex later requires either maintaining separate agent files per tool or stripping incompatible fields during deployment. Both approaches are fragile and create maintenance burden.

**Solution: Universal frontmatter with tool-specific mapping in copier.py.**

Agent files use tool-agnostic fields. `copier.py` transforms them into the correct format for each AI tool during deployment.

**Universal frontmatter schema:**

```yaml
---
name: command-architect
role: advisory | implementation | testing | review
  # advisory → CC: disallowedTools: [Write, Edit] | Cursor: read-only context
  # implementation → CC: all tools | Cursor: full access
  # testing → CC: all tools | Cursor: full access
  # review → CC: disallowedTools: [Write, Edit] | Cursor: read-only context
expertise:
  # CC → maps to skills: [...] (preloaded)
  # Cursor → maps to @docs references or context includes
  # Copilot → maps to included context files
  # Codex → maps to context loading instructions
  - aggregate-design
  - event-design
  - outbox
  - command-handler
  - event-versioning
complexity: high | medium | low
  # CC → maps to effort: high/medium/low AND model selection (opus/sonnet/haiku)
  # Cursor → maps to model selection
  # Others → ignored or tool-specific
max_iterations: 20
  # CC → maps to maxTurns: 20
  # Others → ignored or tool-specific limit
---
```

**Agent-specific updates (using universal schema):**

- **command-architect**: `role: advisory`, `expertise: [aggregate-design, event-design, event-store, outbox, command-handler, event-versioning, aggregate-testing]`, `complexity: high`, `max_iterations: 20`
- **query-architect**: `role: advisory`, `expertise: [query-entity, event-handler, listener-pattern, query-handler, sequence-checking, event-versioning]`, `complexity: high`, `max_iterations: 20`
- **cosmos-architect**: `role: advisory`, `expertise: [cosmos-entity, cosmos-repository, transactional-batch, partition-strategy, event-handler]`, `complexity: high`, `max_iterations: 20`
- **processor-architect**: `role: advisory`, `expertise: [hosted-service, event-routing, grpc-client, batch-processing, event-versioning]`, `complexity: high`, `max_iterations: 20`
- **gateway-architect**: `role: advisory`, `expertise: [gateway-endpoint, endpoint-registration, gateway-security, scalar-docs, versioning, authorization]`, `complexity: high`, `max_iterations: 20`
- **test-engineer**: `role: testing`, `expertise: [aggregate-testing, unit-testing, integration-testing, test-fixtures]`, `complexity: high`, `max_iterations: 25`
- **reviewer**: `role: review`, `expertise: [review-checklist, architectural-fitness]`, `complexity: medium`, `max_iterations: 15`
- **ef-specialist**: `role: advisory`, `expertise: [ef-core-basics, repository-patterns, specification-pattern, audit-trail, ef-migrations]`, `complexity: medium`, `max_iterations: 15`
- **api-designer**: `role: advisory`, `expertise: [minimal-api, controllers, versioning, openapi-scalar, rate-limiting]`, `complexity: medium`, `max_iterations: 15`
- **dotnet-architect**: `role: advisory`, `expertise: [clean-architecture, vertical-slice, ddd-patterns, modular-monolith]`, `complexity: high`, `max_iterations: 20`

**Transformation architecture:**

The transformation mapping lives in `agents.py` alongside the existing `AGENT_CONFIG` dict, following the same per-tool pattern:

```python
# agents.py — existing
AGENT_CONFIG = {
    "claude": {
        "commands_dir": ".claude/commands",
        "rules_dir": ".claude/rules",
        "agents_dir": ".claude/agents",
        ...
    },
    # v1.0.1: "cursor": { ... }
}

# agents.py — new
AGENT_FRONTMATTER_MAP = {
    "claude": {
        "role": {
            "advisory": {"disallowedTools": ["Write", "Edit"]},
            "implementation": {},
            "testing": {},
            "review": {"disallowedTools": ["Write", "Edit"]},
        },
        "expertise": lambda skills: {"skills": skills},
        "complexity": {
            "high": {"effort": "high", "model": "opus"},
            "medium": {"effort": "medium", "model": "sonnet"},
            "low": {"effort": "low", "model": "haiku"},
        },
        "max_iterations": lambda n: {"maxTurns": n},
    },
    # v1.0.1: "cursor": { ... }
    # v1.0.1: "copilot": { ... }
}
```

**How `copy_agents()` uses the mapping:**

`copy_agents()` receives the tool name and applies the correct transformation:

```
copy_agents(source_dir, target_dir, tool_name):
    mapping = AGENT_FRONTMATTER_MAP[tool_name]
    for each agent_file in source_dir:
        universal_fm = parse_yaml_frontmatter(agent_file)
        tool_fm = transform(universal_fm, mapping)
        body = extract_markdown_body(agent_file)
        write(target_dir / agent_file.name, tool_fm + body)
```

For each configured AI tool in `config.ai_tools`, the same agent source file is deployed with different frontmatter:

```
Agent source: agents/command-architect.md
  │  (role: advisory, expertise: [...], complexity: high, max_iterations: 20)
  │
  ├─→ .claude/agents/command-architect.md
  │   (disallowedTools: [Write, Edit], skills: [...], effort: high, model: opus, maxTurns: 20)
  │
  └─→ .cursor/agents/command-architect.md  (v1.0.1)
      (tool-specific frontmatter per Cursor's schema)
```

**Integration with configure flow:**

```
dotnet-ai configure
  └─ deployment (for each tool in config.ai_tools):
      ├─ copy_commands(source, target, tool)    ← existing, already per-tool
      ├─ copy_rules(source, target, tool)       ← existing, already per-tool
      ├─ copy_agents(source, target, tool)      ← UPDATED: universal → tool-specific transform
      ├─ copy_skills(source, target, tool)      ← UPDATED: resolve paths + per-tool adjustments
      ├─ copy_profile(target, tool, project)    ← NEW: deploy matching profile
      └─ copy_hook(target, tool, profile)       ← NEW: CC only, embed constraints in hook prompt
```

When v1.0.1 adds a new tool:
1. Add tool entry to `AGENT_CONFIG` in `agents.py` (directory paths, file format)
2. Add tool entry to `AGENT_FRONTMATTER_MAP` in `agents.py` (frontmatter transformation)
3. Zero changes to agent source files, copier logic, or CLI commands

For v1.0, only the `claude` mapping is implemented. If `ai_tools` contains an unsupported tool, `copy_agents()` logs a warning: "Agent transformation for {tool} not yet supported — skipping agent deployment for this tool."

**Note:** Expertise field values must match skill names as registered in each skill's SKILL.md frontmatter. Verify each skill name matches before updating agents.

**Plugin restriction awareness:** Agents deployed via the plugin (`agents/` in plugin root) CANNOT use `permissionMode`, `hooks`, or `mcpServers` in frontmatter. Agents deployed to `.claude/agents/` (via init/configure) CAN use all fields. The tool deploys to `.claude/agents/`, so all fields are available. The universal schema avoids tool-specific restricted fields entirely.

### Part 6: Skill Optimization (Detected Paths + Behavioral Activation)

Update skill SKILL.md files to use Claude Code skill features that are currently unused.

**Problem with hard-coded paths:**
Hard-coding `paths` like `**/Domain/Aggregates/**/*.cs` is fragile. Different projects organize differently:
- Some use `Domain/Aggregates/`, others `Domain/Core/`
- VSA projects use `Features/OrderFeature/` with flat structure
- Clean arch projects use `src/Company.Domain/Aggregates/`
- Naming conventions vary across companies and teams

Hard-coded paths miss most real projects and create false matches on others.

**Solution: Detected paths (Option A) + behavioral activation (Option B) combined.**

**Option A — Detected paths from project structure:**

During `init`/`detect`, the tool already scans the project structure. After detection, store the actual discovered paths in `.dotnet-ai-kit/project.yml`:

```yaml
# .dotnet-ai-kit/project.yml (extended after detection)
detected_paths:
  aggregates: "Anis.Competition.Points.Command.Domain/Core"
  events: "Anis.Competition.Points.Command.Domain/Events"
  commands: "Anis.Competition.Points.Command.Application/Features"
  handlers: "Anis.Competition.Points.Command.Application/Features"
  entities: "Anis.Competition.Points.Command.Domain/Entities"
  tests: "Anis.Competition.Points.Command.Test/Tests"
  test_live: "Anis.Competition.Points.Command.Test.Live/Tests"
  persistence: "Anis.Competition.Points.Command.Infra/Persistence"
  controllers: "Anis.Competition.Points.Command.Grpc/Services"
```

During `copy_skills()`, the copier reads `detected_paths` from `project.yml` and injects them into the skill's `paths` frontmatter. Skills in the source use placeholder tokens:

```yaml
# Source skill (in tool's skills/ directory)
---
name: aggregate-design
paths: "${detected_paths.aggregates}/**/*.cs"
---
```

`copy_skills()` resolves `${detected_paths.aggregates}` → `Anis.Competition.Points.Command.Domain/Core` during deployment. If the path is not detected, the `paths` field is omitted (skill remains globally available).

**Option B — Behavioral activation via `when-to-use`:**

Add `when-to-use` field to all skills for model auto-invocation. This works as a fallback when paths are not detected, and for generic/unscanned projects:

```yaml
# Example for aggregate-design skill
when-to-use: |
  When creating or modifying an event-sourced aggregate.
  When adding domain methods, factory methods, or Apply methods.
  When the user mentions aggregate, aggregate root, or event sourcing patterns.
```

The model decides when to load the skill based on behavioral context, not file paths. Works regardless of folder structure.

**Combined approach — both layers:**
- `paths` (from detection): activates skill when the AI touches specific detected files. Fast, precise, no model judgment needed.
- `when-to-use` (behavioral): activates skill when the AI recognizes relevant context. Resilient to any folder structure, works even without detection.
- If both are present, either can trigger the skill. Detected paths provide precision; `when-to-use` provides coverage.

**Cross-tool note:**
`paths` and `when-to-use` are **Claude Code skill frontmatter features**. Cursor, Copilot, and Codex do not support these activation mechanisms. For non-CC tools:
- `paths` is ignored (skill remains available but not auto-scoped).
- `when-to-use` text is preserved in the skill body as a context hint that other tools' AI can read, but there's no native auto-invocation trigger.
- The skill content (instructions, patterns, examples) works for all tools — only the activation mechanism is CC-specific.
- Skill optimization is primarily a CC enhancement. For other tools, skills remain manually loaded via commands (existing behavior).

**Skills to update with `when-to-use`:**

| Skill | when-to-use |
|-------|-------------|
| aggregate-design | When creating/modifying event-sourced aggregates, factory methods, Apply methods |
| event-design | When creating/modifying domain events, event data records, EventType enums |
| command-handler | When creating/modifying command handlers using MediatR IRequestHandler |
| event-handler | When creating/modifying event handlers on query side, sequence checking |
| query-entity | When creating/modifying read-model entities with private setters |
| gateway-endpoint | When creating/modifying REST controllers or gRPC service endpoints |
| cosmos-entity | When creating/modifying Cosmos DB entities, partition keys, discriminators |
| ef-core-basics | When configuring EF Core DbContext, entity configurations, migrations |
| unit-testing | When writing unit tests, creating fakers, assertion extensions |
| integration-testing | When writing integration tests with WebApplicationFactory |
| aggregate-testing | When writing tests for event-sourced aggregates |

**Detection enhancement for `project.yml`:**
- The `/dai.detect` command (and the smart-detect skill) must be updated to populate the `detected_paths` section.
- Detection scans for known patterns: classes inheriting `Aggregate<T>`, files in directories containing "Event", "Handler", "Test", etc.
- Paths are stored as relative paths from the project root.
- If a path category is not found (e.g., no Cosmos entities in a SQL project), omit it.

**Skill hooks — NOT implemented (overlap with Part 4):**

Part 4 already deploys an always-active PreToolUse prompt hook that checks ALL writes against the full profile constraints. Adding per-skill session hooks would cause **double haiku calls** on the same Write/Edit — double latency, double cost, with potentially conflicting responses.

Since Part 4's hook already covers all constraints from the profile (including aggregate boundaries, event immutability, sequence checking), per-skill hooks are redundant. If Part 4 proves insufficient in practice (e.g., skill-specific context makes haiku more accurate), skill hooks can be added in a future version. For now, Part 4 is the single code-time enforcement layer.

### Part 7: Command Context Optimization

Update select commands to use `context: 'fork'` to run in subagent context, preventing main context pollution:

| Command | Current | Change To | Reason |
|---------|---------|-----------|--------|
| `/dai.review` | inline | `context: 'fork'` | Review analysis is large, pollutes main context |
| `/dai.verify` | inline | `context: 'fork'` | Build/test output is verbose |
| `/dai.detect` | inline | inline (no change) | Small output, updates config that main context needs |
| `/dai.do` | inline | inline (no change) | Orchestrator, needs main context throughout |
| `/dai.check` | inline | `context: 'fork'` | Analysis output is large |

For forked commands, add `agent` field to specify which agent type handles the forked execution:
- `/dai.review`: `agent: reviewer`
- `/dai.verify`: `agent: general-purpose`
- `/dai.check`: `agent: general-purpose`

---

## Implementation Scope

### New Files
- 12 profile files in `profiles/` (10 specific + hybrid + generic fallback)
- 1 hook prompt template file for Claude Code prompt hook generation (used by `copy_hook()` to build the static prompt string)

### Modified Files
- `src/dotnet_ai_kit/agents.py` — add `AGENT_FRONTMATTER_MAP` dict with per-tool transformation mappings alongside existing `AGENT_CONFIG`
- `src/dotnet_ai_kit/copier.py` — add `copy_profile()`, `copy_hook()`, `deploy_to_linked_repos()` functions; update `copy_agents()` to read universal frontmatter and transform via `AGENT_FRONTMATTER_MAP[tool]`; update `copy_skills()` to resolve `${detected_paths.*}` tokens from `project.yml`
- `src/dotnet_ai_kit/cli.py` — **extend the `configure` CLI function** to call `copy_profile()`, `copy_hook()`, and `deploy_to_linked_repos()` (currently `configure` only re-copies commands — it does NOT call `copy_rules()`, `copy_agents()`, or `copy_skills()`; profile and hook deployment are new capabilities for this function). Add branch creation logic for CLI-driven secondary repo operations (configure, upgrade only — specify/plan/tasks branch logic lives in command markdown files)
- `src/dotnet_ai_kit/models.py` — add `detected_paths` field to `DetectedProject` model; add `linked_from` field to `DotnetAiConfig` model
- `commands/dai.configure.md` — add step for linked repo deployment
- `commands/dai.detect.md` — add path detection step that populates `detected_paths` in `project.yml`
- `commands/dai.specify.md` — fix auto-commit to use branches
- `commands/dai.plan.md` — fix auto-commit to use branches
- `commands/dai.tasks.md` — fix auto-commit to use branches
- `commands/dai.review.md` — add `context: 'fork'` and `agent` frontmatter
- `commands/dai.verify.md` — add `context: 'fork'` and `agent` frontmatter
- `commands/dai.analyze.md` — add `context: 'fork'` and `agent` frontmatter
- 13 agent files in `agents/` — replace tool-specific frontmatter with universal schema (`role`, `expertise`, `complexity`, `max_iterations`)
- ~10 skill SKILL.md files — add `when-to-use` for behavioral activation, add `paths` using `${detected_paths.*}` tokens, and optionally `hooks` frontmatter (CC only)

### New Test Files
- `tests/test_copier_profiles.py` — test `copy_profile()`: correct profile selection per project type, token budget validation, cross-tool deployment
- `tests/test_copier_agents.py` — test `copy_agents()` universal→CC transformation: role mapping, expertise→skills, complexity→effort/model
- `tests/test_copier_skills.py` — test `copy_skills()` token resolution: `${detected_paths.*}` substitution, fallback when path missing
- `tests/test_copier_hooks.py` — test `copy_hook()`: constraint extraction from profile, prompt embedding, file scope filtering
- `tests/test_multi_repo_deploy.py` — test `deploy_to_linked_repos()`: version checking, branch creation, skip logic for uninitialized/remote repos
- `tests/test_models_new_fields.py` — test `detected_paths` on `DetectedProject` and `linked_from` on `DotnetAiConfig` pydantic validation

### Files NOT Modified
- Existing 15 rule files — no changes
- Plugin manifest (`plugin.json`) — no changes
- Other command files not listed above — no changes

---

## Implementation Order

Parts have dependencies and must be implemented in this order:

```
Phase 1 (Foundation — no dependencies):
  ├─ Part 1: Architecture Profiles (create profile files)
  ├─ Part 5: Agent Universal Schema (update agent frontmatter + copier transformation)
  └─ Part 3: Auto-Commit Branch Fix (update command files + cli.py)

Phase 2 (Depends on Phase 1):
  ├─ Part 6: Skill Optimization (depends on Part 1 for profile existence, needs detected_paths model)
  │   └─ Includes: detection enhancement, models.py detected_paths, copier token resolution
  └─ Part 4: Claude Code Prompt Hooks (depends on Part 1 — extracts constraints from profiles)

Phase 3 (Depends on Phase 1 + 2):
  ├─ Part 2: Multi-Repo Deployment (depends on Part 1 profiles, Part 5 agents, Part 3 branch fix)
  │   └─ Includes: models.py linked_from, version checking, deploy_to_linked_repos()
  └─ Part 7: Command Context Optimization (independent but lower priority, do last)
```

Within each phase, parts can be implemented in parallel. Phases must be sequential.

---

## Constraints

1. Rule token budget: each profile must be under 100 lines. Total rules (15 existing + 1 profile) must stay under ~900 lines.
2. Command token budget: each command must stay under 200 lines.
3. Skill token budget: each skill must stay under 400 lines.
4. Cross-platform: all Python code must work on Windows, macOS, and Linux. Use `pathlib.Path`, never `os.path.join()`.
5. Cross-tool: profiles must work for all AI tools (claude, cursor, copilot, codex). Hooks are Claude Code only. Agent frontmatter must use the universal schema — `copier.py` handles tool-specific transformation during deployment.
6. No breaking changes: existing projects must continue working. New features activate only when `configure` or `upgrade` is re-run.
7. Branch safety: never auto-commit to main/master/develop in secondary repos. Always create a dedicated branch.
8. Profile content must be derived from existing skills and rules — no new architectural conventions, just project-type-specific enforcement of existing knowledge.
9. Skill `paths` must never be hard-coded in source files. Use `${detected_paths.*}` tokens resolved from `project.yml` during deployment. If a path is not detected, omit the `paths` field (skill remains globally available with `when-to-use` as fallback).
10. Agent files must remain tool-agnostic. No Claude Code-specific fields (`disallowedTools`, `skills`, `maxTurns`, `effort`, `model`) in agent source files. Universal fields (`role`, `expertise`, `complexity`, `max_iterations`) are transformed by `copier.py` per target tool.
