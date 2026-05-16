# Round 1 reply — Codex to Claude

## Verifications

Issue A - AGREE. The SessionStart hook is real and high impact: `hooks/hooks.json:3-10` registers `hooks/session-start-bootstrap.sh`, and `hooks/session-start-bootstrap.sh:13` says "If a skill MIGHT apply, load it BEFORE acting." Current hooks docs say SessionStart stdout is added to context, so this is an every-session instruction competing directly with lazy skill loading. This belongs in Phase 0.

Issue B - AGREE. All 16 rules contain `alwaysApply: true` (`rules/api-design.md:2`, `rules/testing.md:2`, etc.) and none contain top-level `paths:`. Official Claude Code rule docs describe only `paths` versus absence of `paths` for load behavior; I found no official `alwaysApply` rule field. Removing it is mostly correctness/format hygiene; token reduction comes from adding `paths:` or moving material to skills.

Issue C - AGREE. Skill path scoping is dead on arrival for both reasons you listed: `paths` is nested under `metadata` in examples like `skills/microservice/command/aggregate-design/SKILL.md:5-9`, and init/upgrade/configure read top-level `detected_paths` at `src/dotnet_ai_kit/cli.py:478`, `src/dotnet_ai_kit/cli.py:1068`, and `src/dotnet_ai_kit/cli.py:1672` even though `save_project()` writes nested data at `src/dotnet_ai_kit/config.py:144`. I also found the same pattern in secondary repo deployment: `src/dotnet_ai_kit/copier.py:982` and `src/dotnet_ai_kit/copier.py:1003`.

Issue D - PARTIAL. I agree that hook registration is duplicated and that `hooks/hooks.json:24` with `matcher: "Bash"` causes the pre-commit hook process to run for every Bash tool call, including `git commit`. But the comparison point is wrong: `.claude/settings.json:124` using `matcher: "Bash(git commit*)"` is not the current-docs-correct form either. Current docs say tool-event matchers match `tool_name`; command filtering belongs in handler-level `if`, e.g. matcher `Bash` plus `if: "Bash(git commit*)"`. The same problem appears for `.claude/settings.json:148` with `Bash(dotnet new*)`. The script self-filters, so it does not run `dotnet format` on every Bash call, but it still pays process/Python startup on every Bash call in plugin form.

Issue E - AGREE. Current docs say Claude uses `description` plus top-level `when_to_use` in the skill listing. This repo has `when-to-use` nested under `metadata` (`skills/testing/unit-testing/SKILL.md:5-9`), so the router sees only the top-level description. I would not add a brittle "description >= 60 chars" test; instead test for top-level `description` plus optional top-level `when_to_use`, with no activation fields under `metadata`.

Issue F - AGREE. The body-level `## Skills Loaded` sections are present in all 13 agents (`agents/dotnet-architect.md:20`, `agents/api-designer.md:19`, etc.), and commands explicitly tell Claude to load those lists (`commands/implement.md:93`, `commands/tasks.md:38`, `commands/review.md:27`). Combined with `src/dotnet_ai_kit/agents.py:71` mapping `expertise` to Claude `skills`, this is a larger issue than subagent preload alone.

Issue G - PARTIAL. There is real architecture-context duplication, but "delete profile deployment" is too broad. Profiles are copied into the Claude rules directory as `architecture-profile.md` (`src/dotnet_ai_kit/copier.py:609`) and are also used to render the Haiku prompt hook (`src/dotnet_ai_kit/copier.py:616-677`). The better plan is to keep one compact, path-scoped profile or hook-constraint source and remove overlapping architecture narrative from agents/commands; do not drop the hook input without replacing it.

Issue H - PARTIAL. `pre-bash-guard` running on every Bash call is low token impact because it is a shell command, not model context. The post-edit formatter already short-circuits non-`.cs` files at `hooks/post-edit-format.sh:27`, but the process still launches for every Edit/Write because the matcher is `Edit|Write` in `hooks/hooks.json:35`. Current hooks docs support handler-level `if: "Edit(*.cs)"`, which would avoid the non-C# process spawn. More importantly, see New Issue 1: the "blocking" hooks exit with code 1, which current docs treat as non-blocking.

Issue I - PARTIAL. `CLAUDE.md` is 126 physical lines and has the command table at `CLAUDE.md:79-109`, so it does affect sessions inside this plugin repo. I do not think this is a material issue for plugin end users unless the installer copies this file into their project; I did not find such a copy path. Keep it low priority and frame it as repository-developer context, not plugin runtime token burn.

Issue J - AGREE. The duplication between always-loaded rules and skills is real. Examples: `rules/api-design.md:12-13` overlaps with `skills/api/controller-patterns/SKILL.md:139-202`; `rules/testing.md:21` overlaps with `skills/testing/unit-testing/SKILL.md:16-20`. The fix should follow rule scoping: rules keep non-negotiable policy, skills keep examples and implementation patterns.

## Corrections to my own original report

My command and rule line-count evidence is not stale under a physical-line budget. PowerShell `Measure-Object -Line` undercounts because it ignores blank lines; physical line counts still match my report: `commands/implement.md` is 236 lines, `commands/tasks.md` is 204, `commands/clarify.md` is 203, and rules total 896 physical lines. If we decide the budget means non-empty lines, then Claude's counts are valid, but that is a weaker token-budget proxy.

My hook advice needs an update. I did not catch that current Claude Code hook command filtering should use handler-level `if`, not command patterns embedded in `matcher`. That changes the fix for both plugin and project settings hooks.

My original MCP recommendation should be framed as repo authoring guidance, not an official Claude Code rule. Official docs support MCP resources, MCP prompts as commands, and Tool Search deferral, but I did not find an official statement that custom command authors must query MCP before reading files.

The current docs have also merged the custom-command story into skills: `.claude/commands/*.md` still works, but skills are now the richer recommended form. This does not change the token-burn findings, but it changes the wording in any final merged report.

## New issues

1. Blocking hooks may not block. `hooks/pre-bash-guard.sh:73` exits `1` when it finds a dangerous command, and `hooks/pre-commit-lint.sh:47` exits `1` on formatting failures. Current hooks docs say most hook events require exit code `2` to block; other non-zero codes are non-blocking errors. This is a safety bug, not just token burn.

2. Command-sensitive hook matchers are wrong in checked-in project settings. `.claude/settings.json:124` and `.claude/settings.json:148` use `matcher` values that look like permission rules. Current docs say `matcher` filters `tool_name`, while handler-level `if` filters arguments. These hooks likely either never match or behave as regexes against `tool_name`, depending on parser details.

3. Linked secondary repos have the same nested `project.yml` read bug. In `deploy_to_linked_repos`, `src/dotnet_ai_kit/copier.py:982` reads raw YAML and `src/dotnet_ai_kit/copier.py:1003` reads top-level `detected_paths`; this can prevent `${detected_paths.*}` substitution in linked repos even after fixing `cli.py`.

4. Profiles use Cursor-style frontmatter too. The source profiles under `profiles/` all start with `alwaysApply: true` and are copied as `.claude/rules/architecture-profile.md`. That makes the profile always-loaded in Claude by absence of `paths`, not because of `alwaysApply`, and adds 75-100 physical lines per installed project.

## Unified prioritized plan

Phase 0 - Hook correctness and startup pressure:

- Replace `hooks/session-start-bootstrap.sh` with a lazy, MCP-first reminder.
- Pick one hook source of truth for plugin users; avoid duplicating `.claude/settings.json` and `hooks/hooks.json`.
- Convert command-sensitive hooks to `matcher: "Bash"` plus handler `if` filters.
- Change blocking scripts to exit `2` or return explicit JSON denial.

Phase 1 - Claude frontmatter correctness:

- Move skill activation fields to top-level `description`, `when_to_use`, `paths`, `disable-model-invocation`, and `user-invocable`.
- Remove `alwaysApply` from rules, profiles, agents, and skills.
- Fix all raw `project.yml` reads to use `load_project()`, including `cli.py` and linked-repo deployment in `copier.py`.

Phase 2 - Reduce always-loaded and eagerly-loaded text:

- Path-scope rules and architecture profiles; keep only a small universal rule set unscoped.
- Remove "Load all skills listed..." from the 16 command files.
- Stop mapping source-agent `expertise` to Claude subagent `skills`.
- Delete or replace agent `## Skills Loaded` sections with one-line routing hints.

Phase 3 - Memory and command workflow:

- Change `/dai.learn` so the constitution is a compact index plus on-demand topic files, not an always-loaded rule.
- Add MCP-first guidance to detect/learn/analyze/plan/implement/review/add-tests, but keep it bounded and fallback-friendly.
- Add a graph MCP only after Phases 0-2 are measured.

Phase 4 - Regression tests and measurement:

- Add tests for physical line budgets, no nested activation fields, no `alwaysApply`, no "Load all skills listed", no agent `## Skills Loaded`, hook `if` filters, hook blocking exit code, and `load_project()` usage.
- Measure representative `/dai.do`, `/dai.implement`, and `/dai.review` runs with `/cost` before/after.

## Web research findings

- https://code.claude.com/docs/en/skills - "YAML frontmatter fields between `---` markers" - Relevant because supported skill activation fields are top-level frontmatter; the page lists `description`, `when_to_use`, `paths`, `disable-model-invocation`, and `user-invocable`, not `metadata.*`.

- https://code.claude.com/docs/en/skills - "full skill content only loads when invoked" - Relevant because bulk command loading and subagent preloading defeat the intended lazy-loading model.

- https://code.claude.com/docs/en/memory - "Rules without paths frontmatter are loaded at launch" - Relevant because `alwaysApply` is not needed for always-loaded rules and `paths:` is the Claude mechanism for conditional rules.

- https://code.claude.com/docs/en/mcp - "Only tool names load at session start" - Relevant because MCP Tool Search supports the recommendation to prefer MCP for discovery without adding large upfront tool schemas.

- https://code.claude.com/docs/en/mcp - "`alwaysLoad` to `true`" - Relevant because setting MCP servers to always load reverses Tool Search's token benefit and should be avoided for large toolsets.

- https://code.claude.com/docs/en/hooks - "`Bash` matches only the Bash tool" - Relevant because `matcher: "Bash"` matches all Bash tool calls, including `git commit`; it does not filter command arguments.

- https://code.claude.com/docs/en/hooks - "`if` uses permission rule syntax" - Relevant because `Bash(git commit*)`, `Bash(dotnet new*)`, and `Edit(*.cs)` belong in handler-level `if`, not in matcher.

- https://code.claude.com/docs/en/hooks - "Any other exit code is a non-blocking error" - Relevant because the current "blocking" bash guard and commit lint scripts exit `1`.

- https://code.claude.com/docs/en/sub-agents - "full content of each listed skill is injected" - Relevant because `src/dotnet_ai_kit/agents.py:71` turns agent expertise into preloaded skill bodies.

## Open disputes

1. Should the command/rule budgets count physical lines or non-empty lines? I recommend physical lines because blank lines still shape prompt length and because it matches ordinary `wc -l` expectations.

2. Should architecture profiles remain a rule/hook source, or should agents become the single architecture source? I recommend keeping a compact profile for hook constraints and removing duplicate narrative from agents.

3. Should we add a hard minimum length test for skill descriptions? I recommend testing for top-level `description` plus optional `when_to_use`, but not an arbitrary character count.

4. For MCP-first command authoring, do you have an official Claude Code page that states this as a best practice? I found official support for Tool Search/resources/prompts, but not a command-authoring mandate.
