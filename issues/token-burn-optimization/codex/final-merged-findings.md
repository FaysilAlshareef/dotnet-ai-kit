# Final Merged Findings - Codex Version

Status: final merged findings, agreed by Codex and Claude
Date: 2026-05-16
Scope: token burn, lazy-loading correctness, hook correctness, and MCP workflow for dotnet-ai-kit

## Structure Decision

I accept Claude's proposed final structure:

- `issues/FINAL-REPORT.md`: executive-facing final report.
- `issues/claude/final-merged-findings.md`: Claude's mirrored findings.
- `issues/codex/final-merged-findings.md`: this Codex version.

No round 3 structural change is requested.

## Verified Counts

| Area | Count |
| --- | ---: |
| Skill files | 124 |
| Skill files with `metadata:` frontmatter | 124 |
| Top-level skill `paths:` fields | 0 |
| Nested skill `metadata.paths` files | 9 |
| Nested skill `metadata.when-to-use` files | 115 |
| Nested skill `metadata.alwaysApply` files | 9 |
| Rule files | 16 |
| Rule files with `alwaysApply: true` | 16 |
| Rule files with top-level `paths:` | 0 |
| Profile files | 12 |
| Profile files with `alwaysApply: true` | 12 |
| Commands containing "Load all skills listed" | 16 of 27 |
| Agents with `expertise:` frontmatter | 13 of 13 |
| Agents with `## Skills Loaded` body sections | 13 of 13 |
| Agents with body `Availability: Always (loaded for every interaction)` | 2 of 13 |
| Current over-budget commands using physical lines | 3 |

Issue K verification: grep found 2 occurrences across `agents/*.md`:

- `agents/dotnet-architect.md:16`
- `agents/reviewer.md:14`

## Severity Table

| ID | Severity | Finding | Source |
| --- | --- | --- | --- |
| F01 | HIGH | SessionStart hook explicitly pushes eager skill loading | Claude A |
| F02 | HIGH | Blocking hooks exit 1, which may not block tool calls | Codex N1 |
| F03 | HIGH | Hook registration is duplicated and command filters misuse matcher syntax | Claude D, Codex N2 |
| F04 | HIGH | Detected paths are saved nested but read as top-level, including linked repos | Codex 5, Codex N3 |
| F05 | MED | Skill activation fields are nested under `metadata`, breaking lazy routing/scoping | Codex 1, Claude C |
| F06 | MED | Skill trigger text lives in `metadata.when-to-use`, not router-visible fields | Claude E |
| F07 | MED | All rules are unconditional, and `alwaysApply` is Cursor-style noise in Claude | Codex 2, Claude B |
| F08 | MED | Commands explicitly bulk-load every skill listed by selected agents | Codex 3 |
| F09 | MED | Subagent conversion preloads skills through `expertise -> skills` | Codex 4 |
| F10 | MED | Agent body `## Skills Loaded` lists multiply eager context | Claude F |
| F11 | LOW-MED | Two agent bodies also say `Availability: Always` | Claude K |
| F12 | LOW-MED | Profiles and agents duplicate architecture context; profiles also use `alwaysApply` | Claude G, Codex N4 |
| F13 | MED | `/dai.learn` recommends an always-loaded constitution | Codex 6 |
| F14 | MED | MCP exists, but command workflows do not prefer MCP-first discovery | Codex 7 |
| F15 | LOW | MCP roadmap needs sequencing: `csharp-ls` is useful but insufficient; custom Roslyn MCP is later | Codex 8, Codex 9 |
| F16 | MED | Token budget regression tests are missing and current commands exceed the command budget | Codex 10 |
| F17 | LOW | Post-edit hook process launches for every Edit/Write before self-filtering | Claude H |
| F18 | LOW | Rules and skills duplicate pattern guidance | Claude J |

## F01 - SessionStart Hook Fights Lazy Loading

Severity: HIGH

Evidence:

- `hooks/hooks.json:3` registers `SessionStart`.
- `hooks/hooks.json:8` runs `session-start-bootstrap.sh`.
- `hooks/session-start-bootstrap.sh:6` says to check whether a skill applies before any action.
- `hooks/session-start-bootstrap.sh:11` advertises the full `skills/` directory.
- `hooks/session-start-bootstrap.sh:13` says that if a skill might apply, load it before acting.

Impact: Every session receives a strong eager-loading instruction, directly opposing lazy loading.

Agreed fix: Replace the hook text with a lazy-default, MCP-first reminder. Remove "MIGHT apply", "load it BEFORE acting", and equivalent weak-signal loading language.

## F02 - Blocking Hooks May Not Block

Severity: HIGH

Evidence:

- `hooks/pre-bash-guard.sh:78` prints a blocking message.
- `hooks/pre-bash-guard.sh:81` exits with `exit 1`.
- `hooks/pre-commit-lint.sh:45` prints a blocking message.
- `hooks/pre-commit-lint.sh:48` exits with `exit 1`.

Impact: The scripts claim to block dangerous commands and bad commits, but agreed hook behavior requires blocking exit semantics, not ordinary non-zero error behavior.

Agreed fix: Use `exit 2` or the supported JSON denial shape for blocking branches. Add tests for dangerous bash input and formatting failures.

## F03 - Hook Registration And Matchers Are Wrong

Severity: HIGH

Evidence:

- `hooks/hooks.json:15` registers `pre-bash-guard.sh` on `matcher: "Bash"`.
- `hooks/hooks.json:24` registers `pre-commit-lint.sh` on `matcher: "Bash"`, so the process starts for every Bash call.
- `.claude/settings.json:124` uses `matcher: "Bash(git commit*)"`.
- `.claude/settings.json:148` uses `matcher: "Bash(dotnet new*)"`.
- `hooks/hooks.json:35` and `.claude/settings.json:137` both register PostToolUse `Edit|Write`.
- `src/dotnet_ai_kit/copier.py:672` also emits a `Write|Edit` architecture hook.

Impact: Hook definitions are duplicated, and command-sensitive filters are expressed as matcher strings instead of handler-level filters.

Agreed fix: Pick one hook source of truth. Use tool-name matchers such as `Bash`, `Edit|Write`, and move command/file filters into handler-level `if` expressions.

## F04 - Detected Paths Are Saved Nested But Read Top-Level

Severity: HIGH

Evidence:

- `src/dotnet_ai_kit/config.py:122` unwraps nested `detected` data in `load_project()`.
- `src/dotnet_ai_kit/config.py:144` writes project data under `detected`.
- `src/dotnet_ai_kit/cli.py:477` raw-loads YAML during init.
- `src/dotnet_ai_kit/cli.py:478` reads top-level `detected_paths`.
- `src/dotnet_ai_kit/cli.py:1067` and `src/dotnet_ai_kit/cli.py:1068` repeat this during upgrade.
- `src/dotnet_ai_kit/cli.py:1149` to `src/dotnet_ai_kit/cli.py:1151` raw-read top-level profile fields.
- `src/dotnet_ai_kit/cli.py:1671` and `src/dotnet_ai_kit/cli.py:1672` repeat this during configure.
- `src/dotnet_ai_kit/cli.py:1711` to `src/dotnet_ai_kit/cli.py:1713` raw-read top-level profile fields again.
- `src/dotnet_ai_kit/copier.py:982`, `src/dotnet_ai_kit/copier.py:985`, `src/dotnet_ai_kit/copier.py:986`, and `src/dotnet_ai_kit/copier.py:1003` repeat the same bug for linked repos.

Impact: `${detected_paths.*}` token substitution can receive `None`, and profile deployment can fall back to generic/low-confidence data.

Agreed fix: Use `load_project()` for all project reads in CLI and linked-repo deployment. Preserve legacy top-level support inside `load_project()`.

## F05 - Skill Activation Fields Are Nested Under Metadata

Severity: MED

Evidence:

- `skills/microservice/command/aggregate-design/SKILL.md:5` starts `metadata:`.
- `skills/microservice/command/aggregate-design/SKILL.md:8` stores `when-to-use` under metadata.
- `skills/microservice/command/aggregate-design/SKILL.md:9` stores `paths` under metadata.
- `skills/testing/unit-testing/SKILL.md:8` and `skills/testing/unit-testing/SKILL.md:9` show the same pattern.
- `skills/core/async-patterns/SKILL.md:8` stores `alwaysApply: true` under metadata.

Impact: Claude-visible activation/scoping fields are not in the agreed top-level location. Combined with F04, skill path scoping is dead end-to-end.

Agreed fix: Move activation fields to top-level frontmatter: `description`, `when_to_use`, `paths`, `disable-model-invocation`, and `user-invocable` where applicable. Keep `metadata:` only for internal package data.

## F06 - Skill Trigger Text Is Hidden From The Router

Severity: MED

Evidence:

- `skills/testing/unit-testing/SKILL.md:3` has a short top-level description.
- `skills/testing/unit-testing/SKILL.md:8` stores the stronger trigger under `metadata.when-to-use`.
- `skills/microservice/command/aggregate-design/SKILL.md:3` has a short top-level description.
- `skills/microservice/command/aggregate-design/SKILL.md:8` stores the stronger trigger under `metadata.when-to-use`.

Impact: Once bulk-loading is removed, skill discovery needs top-level trigger text. Today the best trigger text is hidden.

Agreed fix: Keep top-level `description`, add top-level `when_to_use` where useful, and do not use a brittle description-length minimum.

## F07 - Rules Are Unconditional And Use Cursor-Style AlwaysApply

Severity: MED

Evidence:

- `rules/api-design.md:2` has `alwaysApply: true`.
- `rules/testing.md:2` has `alwaysApply: true`.
- `rules/security.md:2` has `alwaysApply: true`.
- `rules/multi-repo.md:3` has `alwaysApply: true`.
- Verified count: 16 of 16 rule files have `alwaysApply`, 0 have top-level `paths:`, totaling 880 physical lines.

Impact: All rules are loaded unconditionally by absence of `paths`, while `alwaysApply` is Claude-irrelevant format noise.

Agreed fix: Remove `alwaysApply`. Keep only a small universal rule set unscoped. Add top-level `paths:` to file-type-specific rules.

## F08 - Commands Bulk-Load Agent Skill Lists

Severity: MED

Evidence:

- `commands/implement.md:74` to `commands/implement.md:91` route to many agents.
- `commands/implement.md:93` says to load all skills listed in the secondary agent.
- `commands/tasks.md:38` says to load all skills listed in the agent.
- `commands/clarify.md:40` says to load all skills listed in the agent.
- `commands/review.md:27` says to read the reviewer and load all listed skills.
- `commands/add-tests.md:75` says to load all skills listed in each loaded agent.

Impact: Commands defeat lazy loading by forcing agent reads and then full skill-list reads before the task proves the need.

Agreed fix: Replace bulk-loading text with bounded selection: one primary agent and at most one or two task-specific skills initially.

## F09 - Subagent Conversion Preloads Skills

Severity: MED

Evidence:

- `src/dotnet_ai_kit/agents.py:71` maps source `expertise` to Claude `skills`.
- `agents/dotnet-architect.md:5` defines `expertise:`.
- `agents/api-designer.md:5` defines `expertise:`.
- Verified count: 13 of 13 agent files contain `expertise:`.

Impact: Universal agent metadata becomes Claude subagent skill preloads, which injects full skill bodies into subagent startup context.

Agreed fix: Stop transforming `expertise` into Claude `skills`. Keep expertise as descriptive routing metadata only.

## F10 - Agent Body `Skills Loaded` Lists Multiply Context

Severity: MED

Evidence:

- `agents/dotnet-architect.md:20` starts `## Skills Loaded`.
- `agents/dotnet-architect.md:21` to `agents/dotnet-architect.md:38` list 18 skills.
- `agents/api-designer.md:19` starts `## Skills Loaded`.
- `agents/api-designer.md:20` to `agents/api-designer.md:37` list 18 skills.
- `agents/reviewer.md:18` starts `## Skills Loaded`.
- Verified count: 13 of 13 agents contain this section.

Impact: Agent bodies provide the list that commands then ask the model to bulk-load.

Agreed fix: Delete body-level `## Skills Loaded` sections. Replace with short routing hints only where needed.

## F11 - Agent Bodies Say `Availability: Always`

Severity: LOW-MED

Evidence:

- `agents/dotnet-architect.md:16` says `**Availability**: Always (loaded for every interaction)`.
- `agents/reviewer.md:14` says the same.
- Verified grep count: 2 occurrences across `agents/*.md`.

Impact: This body text survives frontmatter fixes and reinforces the wrong always-loaded model.

Agreed fix: Remove these lines and avoid replacement text that implies always-loaded behavior.

## F12 - Profiles And Agents Duplicate Architecture Context

Severity: LOW-MED

Evidence:

- `src/dotnet_ai_kit/copier.py:24` describes `PROFILE_MAP`.
- `src/dotnet_ai_kit/copier.py:26` starts the project-type profile map.
- `src/dotnet_ai_kit/copier.py:609` deploys the selected profile as `architecture-profile.md`.
- `profiles/microservice/command.md:2` and `profiles/generic/vsa.md:2` use `alwaysApply: true`.
- `commands/implement.md:74` to `commands/implement.md:81` separately route by architecture to agents.

Impact: Profiles are useful as compact architecture constraints and hook input, but commands and agents repeat architecture narrative. Profiles also carry Cursor-style frontmatter.

Agreed fix: Keep compact profiles, path-scope them where possible, remove `alwaysApply`, and strip duplicate architecture narrative from agents/commands.

## F13 - `/dai.learn` Recommends Always-Loaded Constitution

Severity: MED

Evidence:

- `commands/learn.md:29` says the constitution captures architecture, domain model, naming conventions, packages, .NET version, and patterns.
- `commands/learn.md:55` writes `.dotnet-ai-kit/memory/constitution.md`.
- `commands/learn.md:107` tells users to add it as an always-loaded rule.
- `skills/workflow/plan-templates/SKILL.md:26` and `skills/workflow/plan-templates/SKILL.md:73` reference that constitution.

Impact: A potentially large memory file is recommended as permanent startup context.

Agreed fix: Make `constitution.md` a compact index and put detailed architecture/domain/event/package notes in on-demand files. Remove always-loaded guidance.

## F14 - Commands Do Not Prefer MCP-First Discovery

Severity: MED

Evidence:

- `.mcp.json:2` configures MCP servers.
- `.mcp.json:3` to `.mcp.json:6` configure only `csharp-ls`.
- `commands/configure.md:107` mentions MCP permissions, but operational commands do not contain MCP/symbol guidance.
- `commands/implement.md:74` to `commands/implement.md:93` route through agents and skill lists instead.
- `commands/review.md:27` loads the reviewer and all listed skills instead of starting with MCP discovery.

Impact: MCP cannot reduce token use if command templates still ask for broad agent and skill reads.

Agreed fix: Add bounded MCP-first discovery guidance to detect, learn, analyze, plan, implement, review, and add-tests, with fallback when MCP is unavailable.

## F15 - MCP Roadmap Needs Sequencing

Severity: LOW

Evidence:

- `.mcp.json:3` registers `csharp-ls`.
- `.mcp.json:5` passes `--solution .`.
- `.mcp.json:6` uses stdio transport.
- F14 shows command workflows do not yet exploit MCP-first behavior.

Impact: `csharp-ls` is useful for symbols/navigation, but not enough for architecture summaries, event-flow graphs, route maps, or impact analysis. A custom Roslyn MCP before local eager-loading fixes would solve the wrong problem first.

Agreed fix: Keep `csharp-ls`. Add a graph/codebase MCP after Phases 0-2 are measured. Defer custom Roslyn MCP until remaining gaps are specifically CQRS/event-flow shaped.

## F16 - Token Budget Tests Are Missing And Current Commands Exceed Budget

Severity: MED

Evidence:

- `commands/implement.md:235` exists; physical line count is 235.
- `commands/tasks.md:203` exists; physical line count is 203.
- `commands/clarify.md:202` exists; physical line count is 202.
- Repo convention sets commands at <= 200 lines, rules at <= 100 lines, and skills at <= 400 lines.

Impact: Budget conventions are not enforced, and three commands currently exceed the agreed physical-line budget.

Agreed fix: Add pytest checks for artifact budgets and token-burn anti-patterns: nested activation fields, `alwaysApply`, bulk skill-load text, agent `## Skills Loaded`, bad hook filters, bad hook blocking exits, and bad project reads.

## F17 - Post-Edit Hook Process Spawns Too Broadly

Severity: LOW

Evidence:

- `hooks/hooks.json:35` registers `matcher: "Edit|Write"`.
- `hooks/hooks.json:39` runs `post-edit-format.sh`.
- `.claude/settings.json:137` and `.claude/settings.json:141` duplicate that registration.
- `hooks/post-edit-format.sh:26` says it only processes `.cs` files.
- `hooks/post-edit-format.sh:27` and `hooks/post-edit-format.sh:28` self-filter non-C# files after launch.

Impact: The script avoids formatting non-C# files, but the process still starts for every Edit/Write.

Agreed fix: Add handler-level C# file filters and keep script self-filtering as a fallback.

## F18 - Rules And Skills Duplicate Pattern Guidance

Severity: LOW

Evidence:

- `rules/api-design.md:12` lists detailed HTTP status-code rules.
- `rules/api-design.md:13` requires `ProblemDetails`.
- `skills/api/controller-patterns/SKILL.md:139` starts a `ProblemDetails Configuration` section.
- `skills/api/controller-patterns/SKILL.md:201` repeats ProblemDetails guidance.
- `rules/testing.md:21` requires Arrange-Act-Assert.
- `skills/testing/unit-testing/SKILL.md:16` also requires Arrange-Act-Assert.

Impact: Once a matching skill loads, the model can see both rule policy and full skill pattern text for the same topic.

Agreed fix: Keep rules as compact hard policy. Move examples, tables, and recipes into skills.

## Phased Fix Plan

Phase 0:

- Replace eager SessionStart text.
- Fix blocking hook exit semantics.
- Pick one hook registration source.
- Move command/file filters into handler-level `if`.

Phase 1:

- Move skill activation fields to top-level frontmatter.
- Remove `alwaysApply` from skills, rules, and profiles.
- Fix project reads to use `load_project()`.
- Verify detected path token substitution for init, upgrade, configure, and linked repos.

Phase 2:

- Path-scope non-universal rules and profiles.
- Remove "Load all skills listed" from commands.
- Stop mapping agent `expertise` to Claude `skills`.
- Delete agent `## Skills Loaded` sections and `Availability: Always` lines.

Phase 3:

- Change `/dai.learn` to produce an index plus on-demand memory files.
- Add MCP-first guidance to operational commands.
- Keep `csharp-ls`; add graph MCP only after measuring local fixes.
- Defer custom Roslyn MCP until remaining gaps justify it.

Phase 4:

- Add artifact budget tests.
- Add token-burn anti-pattern tests.
- Add hook syntax/blocking tests.
- Add nested `project.yml` compatibility tests.
- Measure representative `/dai.do`, `/dai.implement`, and `/dai.review` runs before and after.

## Regression Test Checklist

- No skill activation fields under `metadata`.
- No rule/profile `alwaysApply`.
- Non-universal rules and profiles have `paths`.
- No command contains "Load all skills listed".
- No generated Claude agent gets broad `skills:` from `expertise`.
- No agent body contains `## Skills Loaded` or `Availability: Always`.
- Blocking hooks use blocking semantics.
- Bash command filters use `matcher: "Bash"` plus handler `if`.
- Edit/Write format hooks are filtered to C# files at configuration level.
- CLI and linked-repo deployment use `load_project()`.
- Commands are <= 200 physical lines, rules <= 100, skills <= 400.
- `/dai.learn` does not recommend an always-loaded constitution.
- Target operational commands contain bounded MCP-first guidance.

## Pending Claude Review

None. This file adds no new findings beyond the agreed round-2 merge, except the requested Issue K count verification, which found 2 occurrences rather than all 13 agents.
