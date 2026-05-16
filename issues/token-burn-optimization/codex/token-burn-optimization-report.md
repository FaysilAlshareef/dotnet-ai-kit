# Token Burn Optimization Report

Status: discovered, not implemented
Source: Codex codebase scan and Claude Code/MCP documentation review
Date: 2026-05-16

## Goal

Reduce token burn and improve Claude Code plugin performance without weakening the architecture safety model. The edit hook can stay because it uses a cheap/faster Haiku prompt hook; the main token cost is in the primary Claude Code context, not that hook.

## Executive Summary

The current plugin has the right idea: commands, skills, agents, rules, profiles, and MCP. The token problem is that too many parts independently tell Claude to load more context. MCP helps, but it will not fix the issue by itself unless commands and skills are changed to prefer MCP and lazy loading.

Highest impact fixes:

1. Move skill activation fields from nested `metadata` to top-level frontmatter.
2. Path-scope most `.claude/rules` files.
3. Remove "Load all skills listed..." instructions from commands.
4. Stop bulk preloading skills into subagents.
5. Fix nested `project.yml` reads so detected paths actually resolve.
6. Add MCP-first behavior to detect/analyze/implement/review workflows.

## Issue 1: Skill Path Scoping Is Probably Not Working

### Evidence

Claude Code expects skill activation fields such as `paths`, `when_to_use`, `disable-model-invocation`, and `user-invocable` at the top level of `SKILL.md` frontmatter.

Current skills place these fields under `metadata`, for example:

- `skills/microservice/command/aggregate-design/SKILL.md`
- `skills/testing/unit-testing/SKILL.md`
- `skills/microservice/query/event-handler/SKILL.md`

Scan result:

- 124 skill files
- 0 top-level `paths`
- 9 nested `metadata.paths`
- 0 top-level `when_to_use`
- 115 nested `metadata.when-to-use`
- 9 nested `metadata.alwaysApply`

### Impact

Claude may ignore those nested activation hints. This means skills intended to be path-scoped can remain broadly visible or trigger too often, which increases context use.

### Solution

Move activation fields to top-level frontmatter:

```yaml
---
name: aggregate-design
description: Use when designing or implementing event-sourced aggregate roots.
when_to_use: When creating or modifying event-sourced aggregates, factory methods, or Apply methods.
paths:
  - "${detected_paths.aggregates}/**/*.cs"
---
```

Keep custom metadata only for internal CLI use:

```yaml
metadata:
  category: microservice/command
  agent: command-architect
```

## Issue 2: All Rules Are Unconditional

### Evidence

All 16 rule files under `rules/` have no `paths` frontmatter. Claude Code rules without `paths` load at launch.

Measured surface:

- 16 rule files
- 896 lines
- 36,631 chars
- Roughly 9k tokens
- 0 path-scoped rules

Examples:

- `rules/api-design.md`
- `rules/data-access.md`
- `rules/localization.md`
- `rules/multi-repo.md`
- `rules/observability.md`

### Impact

Every session pays for rules that may not apply to the current task or file type.

### Solution

Keep only small universal rules always loaded:

- `existing-projects.md`
- `tool-calls.md`
- a trimmed `coding-style.md`
- a trimmed `security.md`

Path-scope the rest:

```yaml
---
paths:
  - "**/*.cs"
---
```

Use narrower scopes where possible:

```yaml
---
paths:
  - "**/Controllers/**/*.cs"
  - "**/Endpoints/**/*.cs"
  - "**/Program.cs"
---
```

For cross-repo rules, make them conditional through command logic instead of always loaded.

## Issue 3: Commands Tell Claude To Load Too Much

### Evidence

There are 16 occurrences of "Load all skills listed..." across commands. Examples:

- `commands/implement.md`
- `commands/analyze.md`
- `commands/plan.md`
- `commands/tasks.md`
- `commands/add-tests.md`
- `commands/add-crud.md`

The `commands/implement.md` command alone references:

- 17 skill paths
- 15 agent paths
- 1 "Load all skills listed..." instruction

### Impact

This defeats lazy skill loading. Even if skills are well structured, commands explicitly ask the model to read many of them.

### Solution

Replace bulk loading instructions with bounded selection:

```markdown
Select the minimum context needed:
- Read one primary architect agent for project type.
- Read at most 2 task-specific skills before editing.
- Read more only when the current task proves it needs more context.
- Prefer MCP symbol/graph queries before reading full files.
```

For commands like `/dai.implement`, make the command a router:

1. Determine current task type.
2. Load only one architect agent.
3. Load one primary skill.
4. Use MCP to locate exact code.
5. Read only the target files.

## Issue 4: Subagents Preload Too Many Skills

### Evidence

`src/dotnet_ai_kit/agents.py` maps source agent `expertise` into Claude Code `skills`.

Claude Code docs say a subagent `skills` field injects the full skill content into the subagent context at startup.

Measured agent surface:

- 13 agent files
- 63 `expertise` items mapped into preloaded skills
- 131 body-level "Skills Loaded" references
- `agents/dotnet-architect.md` lists 18 skills
- `agents/api-designer.md` lists 18 skills

### Impact

Invoking a subagent can pull in large skill bodies up front. This can cost more than keeping the main conversation lean.

### Solution

Do not map `expertise` directly to Claude `skills`.

Preferred alternatives:

1. Keep `expertise` as descriptive metadata only.
2. Create one compact profile skill per agent, under 100 lines.
3. Let subagents discover and invoke specific skills during work.
4. Remove or shorten the body-level "Skills Loaded" lists.

Example transformed Claude frontmatter:

```yaml
---
name: command-architect
description: Use for event-sourced command-side CQRS design.
model: sonnet
effort: medium
---
```

## Issue 5: Detected Paths Are Saved Nested But Read As Top-Level

### Evidence

`save_project()` writes project data under a `detected:` key:

- `src/dotnet_ai_kit/config.py`

But multiple call sites read top-level keys directly:

- `src/dotnet_ai_kit/cli.py`
- init path reads `_init_proj.get("detected_paths")`
- upgrade path reads `_upg_proj.get("detected_paths")`
- profile deployment reads `project_data.get("project_type")`

### Impact

Detected paths may be `None`, so skill path token resolution can silently fail. Profile deployment can also fall back to generic or low-confidence behavior.

### Solution

Use `load_project()` everywhere project data is needed. It already supports both nested and top-level formats.

Replace direct YAML reads like:

```python
project_data = yaml.safe_load(project_yml.read_text(encoding="utf-8")) or {}
project_type = project_data.get("project_type", "generic")
```

With:

```python
detected = load_project(project_yml)
project_type = detected.project_type
detected_paths = detected.detected_paths
```

Add regression tests for:

- nested `detected.detected_paths`
- top-level legacy `detected_paths`
- profile deployment from nested `detected.project_type`
- skill path token resolution during init, upgrade, and configure

## Issue 6: `/dai.learn` Can Create Permanent Token Bloat

### Evidence

`commands/learn.md` tells users:

> Add this file as an always-loaded rule in your AI tool configuration

The generated constitution is intended to capture architecture, domain model, events, conventions, packages, and patterns.

### Impact

The constitution can become a large always-loaded memory/rule. This is the opposite of token reduction.

### Solution

Change `/dai.learn` output guidance:

- Do not add constitution as always-loaded rule.
- Keep a small index file.
- Put detailed architecture/domain/event notes in supporting files.
- Have `/dai.plan` and `/dai.review` read only needed sections.

Suggested structure:

```text
.dotnet-ai-kit/memory/
  constitution.md        # compact index, under 100 lines
  architecture.md        # detailed, on demand
  domain-model.md        # detailed, on demand
  event-flow.md          # detailed, on demand
  conventions.md         # detailed, on demand
```

## Issue 7: MCP Exists But Commands Do Not Prefer It

### Evidence

Current `.mcp.json` only configures `csharp-ls`.

Current commands still instruct broad scanning and file reading. The command templates do not consistently say to query MCP first.

### Impact

Adding MCP alone may not reduce token burn. Claude may still use grep/read workflows because commands ask for broad scans.

### Solution

Update command templates with MCP-first guidance:

```markdown
Before reading full files:
1. Use MCP symbol, reference, route, or graph tools when available.
2. Ask for exact snippets or paths from MCP.
3. Read only the smallest relevant files.
4. Fall back to `rg` and file reads only when MCP is unavailable or incomplete.
```

Apply first to:

- `commands/detect.md`
- `commands/learn.md`
- `commands/analyze.md`
- `commands/plan.md`
- `commands/implement.md`
- `commands/review.md`
- `commands/add-tests.md`

## Issue 8: `csharp-ls` Is Useful But Not Enough

### Evidence

Current MCP:

```json
{
  "mcpServers": {
    "csharp-ls": {
      "command": "csharp-ls",
      "args": ["--solution", "."],
      "transport": "stdio"
    }
  }
}
```

`csharp-ls` is good for:

- find symbol
- find references
- diagnostics
- go to definition style navigation

It is not enough for:

- architecture summaries
- call graph traversal
- impact analysis
- route maps
- dead code discovery
- event flow graphs
- command-to-event-to-projection maps

### Solution

Keep `csharp-ls`, and add a code graph MCP.

Recommended next MCP:

- `codebase-memory-mcp`

Use it for:

- indexing repositories
- `search_graph`
- `trace_call_path`
- `get_architecture`
- route discovery
- impact analysis
- dead code checks

Do not set MCP `alwaysLoad: true` unless the server is tiny. Claude Code has MCP Tool Search that defers tools to keep startup context low.

## Issue 9: Custom Roslyn MCP Is Not First Move

### Evidence

The external MCP proposal file recommends:

- existing graph MCP first
- NDepend for deep static quality analysis if licensed
- custom Roslyn MCP only for domain-specific CQRS/event-sourcing intelligence

### Impact

Building a custom MCP too early adds maintenance cost before the plugin's own token loading issues are fixed.

### Solution

Build custom Roslyn MCP only after these are true:

1. Rules and skills are properly scoped.
2. Commands are MCP-first.
3. `csharp-ls` and a graph MCP are installed and measured.
4. Remaining missing answers are specifically semantic .NET/CQRS questions.

Custom MCP tools worth building later:

- `command_handler_map`
- `event_handler_map`
- `aggregate_callers`
- `projection_graph`
- `saga_dependencies`
- `dead_events`
- `service_boundary_map`

## Issue 10: Need Token Budget Tests

### Evidence

The repo has stated budgets:

- Commands <= 200 lines
- Rules <= 100 lines
- Skills <= 400 lines

But current command files exceed the command budget:

- `commands/implement.md`: 236 lines
- `commands/tasks.md`: 204 lines
- `commands/clarify.md`: 203 lines

### Solution

Add tests that fail on token-burn regressions:

- no command over 200 lines
- no command contains "Load all skills listed"
- no skill activation fields under `metadata`
- no unresolved `${detected_paths.*}` after init/upgrade/configure when paths exist
- always-loaded rules total under a fixed char/token budget
- no subagent has more than 1-2 preloaded skills
- constitution guidance must not say "always-loaded rule"

## Implementation Order

### Phase 1: Metadata and loading fixes

1. Move skill activation fields to top-level.
2. Fix `project.yml` nested reads.
3. Add regression tests for detected path resolution.
4. Remove nested `alwaysApply` or convert to valid top-level behavior only where truly needed.

### Phase 2: Command and agent slimming

1. Remove "Load all skills listed..." from commands.
2. Shorten over-budget commands.
3. Stop mapping agent `expertise` to preloaded Claude `skills`.
4. Replace long body skill lists with compact routing hints.

### Phase 3: Rule scoping

1. Trim universal rules to a small base.
2. Add `paths` to file-type and architecture-specific rules.
3. Move rare guidance into skills, not rules.

### Phase 4: MCP-first workflow

1. Keep `csharp-ls`.
2. Add `codebase-memory-mcp` as optional/recommended graph MCP.
3. Add command instructions to use MCP before broad file reads.
4. Document fallback when MCP is unavailable.

### Phase 5: Measure before custom MCP

1. Measure token usage before/after with Claude Code `/cost`.
2. Track tool calls per command.
3. Only build custom Roslyn MCP if existing MCPs cannot answer domain-specific CQRS/event flow questions.

## Resources Used

### Official Claude Code docs

- Skills and custom commands: https://code.claude.com/docs/en/slash-commands
  - Skill body loads only when used.
  - Skill descriptions are in context.
  - Top-level fields include `description`, `when_to_use`, `paths`, `disable-model-invocation`, `context`, `agent`, `allowed-tools`.
  - Supporting files keep large references out of context until needed.

- Memory and rules: https://code.claude.com/docs/en/memory
  - `CLAUDE.md` loads at startup.
  - Imports load at startup too, so imports do not reduce token use.
  - `.claude/rules` files without `paths` load unconditionally.
  - Path-scoped rules trigger only when matching files are used.

- Subagents: https://code.claude.com/docs/en/sub-agents
  - Subagents have their own context.
  - A subagent `skills` field preloads full skill content at startup.
  - MCP servers can be scoped to subagents to avoid polluting parent context.

- MCP: https://code.claude.com/docs/en/mcp
  - MCP connects external tools and data sources.
  - MCP Tool Search defers tool definitions to keep context low.
  - Avoid `alwaysLoad: true` unless tools are needed every turn.
  - MCP prompts can become commands.

- Hooks: https://code.claude.com/docs/en/hooks
  - Prompt hooks are supported.
  - Prompt hooks can use Claude models for single-turn evaluation.
  - Keeping the Haiku edit hook is acceptable if latency/cost is acceptable.

### MCP/code intelligence resources

- Existing local MCP proposal: `C:/Users/libya/source/repos/AI/dotnet-code-intelligence-mcp.md`
- codebase-memory-mcp: https://github.com/DeusData/codebase-memory-mcp
  - Persistent code graph MCP.
  - Supports C#.
  - Claims lower token usage for structural code exploration.
  - Useful for call graphs, routes, architecture summaries, dead code, and impact analysis.

### Local repo files reviewed

- `.mcp.json`
- `.claude/settings.json`
- `.claude-plugin/plugin.json`
- `src/dotnet_ai_kit/agents.py`
- `src/dotnet_ai_kit/cli.py`
- `src/dotnet_ai_kit/config.py`
- `src/dotnet_ai_kit/copier.py`
- `commands/implement.md`
- `commands/analyze.md`
- `commands/add-tests.md`
- `commands/learn.md`
- `agents/dotnet-architect.md`
- `agents/command-architect.md`
- `skills/microservice/command/aggregate-design/SKILL.md`
- `skills/testing/unit-testing/SKILL.md`
- `rules/*.md`

