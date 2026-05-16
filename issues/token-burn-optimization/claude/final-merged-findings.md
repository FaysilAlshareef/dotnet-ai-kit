# Final Merged Findings — Claude Version

Status: final merged findings, agreed by Claude and Codex
Date: 2026-05-16
Reviewers: Claude (Opus 4.7, 1M context) and Codex (gpt-5.5 xhigh)
Scope: token burn, lazy-loading correctness, hook correctness, and MCP workflow for `dotnet-ai-kit`

This file is the Claude-side mirror of `issues/codex/final-merged-findings.md`. The 18 findings and their fixes are byte-identical in substance; only the voice and ordering of the supporting prose differ. Read whichever you opened first. The executive-facing summary is at `issues/FINAL-REPORT.md`.

## Methodology

1. **Codex original scan** (`issues/codex/token-burn-optimization-report.md`) — produced 10 issues with file-level evidence.
2. **Claude verification + additions** (`issues/claude/token-burn-verification-and-additions.md`) — re-ran every Codex claim against the working tree, added Issues A–J.
3. **Round 1 cross-review** (`issues/discussion/round1-*`) — Codex audited Claude's additions, added four new findings (blocking-exit safety bug, matcher misuse, linked-repo nested read, profile `alwaysApply`), corrected Claude's stale line counts.
4. **Round 2 reconciliation** (`issues/discussion/round2-claude-reply.md`) — Claude accepted all four Codex corrections and additions, added Issue K (`Availability: Always` body text), and proposed this three-file structure.
5. **Codex round-2 reply** verified Issue K (only 2 of 13 agents, not all 13) and committed to this structure.

All file:line citations below were verified by at least one of us during this discussion.

## Verified Counts

| Area | Count | Confidence |
|---|---:|---|
| Skill files total | 124 | both verified |
| Skills with `metadata:` block | 124 | both verified |
| Skills with top-level `paths:`, `when_to_use:`, `disable-model-invocation:` | 0 | both verified |
| Skills with nested `metadata.paths` | 9 | Codex |
| Skills with nested `metadata.when-to-use` | 115 | Codex |
| Skills with nested `metadata.alwaysApply` | 9 | Codex |
| Rule files | 16 | both verified |
| Rules with `alwaysApply: true` | 16 | Claude verified |
| Rules with top-level `paths:` | 0 | both verified |
| Rules total physical lines | 880 | Codex (corrected from Claude's 705 non-blank count) |
| Profile files | 12 | both verified |
| Profiles with `alwaysApply: true` | 12 | Codex |
| Commands containing `"Load all skills listed"` | 16 of 27 | both verified |
| Agents with `expertise:` frontmatter | 13 of 13 | Codex |
| Agents with `## Skills Loaded` body section | 13 of 13 | both verified |
| Agents with `**Availability**: Always (loaded for every interaction)` | **2 of 13** (not 13) | Codex verified |
| Commands currently over 200 physical lines | 3 (`implement.md` 235, `tasks.md` 203, `clarify.md` 202) | both verified |

**Line-count correction:** Claude's earlier "under 200" claim was wrong. PowerShell `Measure-Object -Line` counts non-blank lines; `wc -l` / `File.ReadAllLines().Count` counts physical lines. Token cost tracks physical lines (blanks still occupy tokens). Codex's original numbers stand.

## Severity Table (18 findings)

| ID | Severity | Title | Source |
|---|---|---|---|
| F01 | 🔴 HIGH | SessionStart hook explicitly fights lazy loading | Claude A |
| F02 | 🔴 HIGH | Blocking hooks `exit 1` — Claude Code needs `exit 2` to block | Codex N1 |
| F03 | 🔴 HIGH | Hook registration duplicated; matchers misuse permission syntax | Claude D ∪ Codex N2 |
| F04 | 🔴 HIGH | Detected paths saved nested, read top-level (CLI + linked repos) | Codex 5 ∪ Codex N3 |
| F05 | 🟠 MED | Skill activation fields buried under `metadata:` block | Codex 1 (joins C) |
| F06 | 🟠 MED | Skill trigger text in `metadata.when-to-use`, invisible to router | Claude E |
| F07 | 🟠 MED | All 16 rules unconditional + carry Cursor-style `alwaysApply` | Codex 2 ∪ Claude B |
| F08 | 🟠 MED | 16 commands say "Load all skills listed in agent's section" | Codex 3 |
| F09 | 🟠 MED | `expertise → skills` subagent preload mapping (`agents.py:71`) | Codex 4 |
| F10 | 🟠 MED | 13 agent bodies carry `## Skills Loaded` lists (~18 skills each) | Claude F |
| F11 | 🟡 LOW-MED | 2 agents say `**Availability**: Always (loaded for every interaction)` | Claude K |
| F12 | 🟡 LOW-MED | Profile + agent architecture duplication; profiles also `alwaysApply` | Claude G ∪ Codex N4 |
| F13 | 🟠 MED | `/dai.learn` recommends always-loaded constitution | Codex 6 |
| F14 | 🟠 MED | Commands don't prefer MCP-first discovery | Codex 7 |
| F15 | 🟢 LOW | MCP roadmap sequencing — `csharp-ls` alone insufficient | Codex 8 ∪ 9 |
| F16 | 🟠 MED | No token-budget tests; 3 commands over budget | Codex 10 |
| F17 | 🟢 LOW | Post-edit format hook process spawns on every Edit/Write | Claude H |
| F18 | 🟢 LOW | Rule and skill pattern guidance overlaps | Claude J |

Distribution: **4 HIGH / 8 MED / 4 LOW-MED-LOW** (collapsing LOW-MED to LOW).

---

## F01 — SessionStart Hook Fights Lazy Loading 🔴 HIGH

**Evidence**
- [hooks/hooks.json:3-12](hooks/hooks.json:3) registers `SessionStart`.
- [hooks/session-start-bootstrap.sh:6](hooks/session-start-bootstrap.sh:6) "Before any action, check if a skill applies"
- [hooks/session-start-bootstrap.sh:13](hooks/session-start-bootstrap.sh:13) "If a skill MIGHT apply, load it BEFORE acting. Even a small chance = load it."

**Why it matters:** This text is injected as a system-reminder at every session start. It is the loudest instruction the agent receives, and it directly contradicts the lazy-loading model that every other fix in this report depends on. Fixing other items without fixing this one yields no measurable token reduction.

**Agreed fix:** Replace the hook output with a lazy-default, MCP-first reminder. Remove the "MIGHT apply / load before acting / even a small chance" phrasing. Sample replacement:

```text
[dotnet-ai-kit] Skills available on demand. Defaults:
1. Use MCP tools (csharp-ls) to locate exact code before reading files.
2. Load at most 1 skill body per task before editing.
3. Treat skills and rules as just-in-time references, not preloads.
```

---

## F02 — Blocking Hooks Exit 1 (May Not Block) 🔴 HIGH

**Evidence**
- [hooks/pre-bash-guard.sh:78](hooks/pre-bash-guard.sh:78) prints "BLOCKED by dotnet-ai-kit bash-guard"
- [hooks/pre-bash-guard.sh:81](hooks/pre-bash-guard.sh:81) `exit 1`
- [hooks/pre-commit-lint.sh:45](hooks/pre-commit-lint.sh:45) prints "BLOCKED by dotnet-ai-kit pre-commit-lint"
- [hooks/pre-commit-lint.sh:48](hooks/pre-commit-lint.sh:48) `exit 1`

**Why it matters:** Claude Code hooks docs specify exit code `2` blocks the tool call (or feeds stderr back to the model). Other non-zero exit codes are non-blocking errors shown to the user only. These hooks **claim** to block dangerous commands and unformatted commits but in fact don't. This is a **safety bug**, not just token burn.

**Agreed fix:** Change `exit 1` to `exit 2` on the blocking branches, or emit the supported JSON denial response. Add tests that feed a dangerous bash payload and a formatting-failure scenario and assert the tool call was blocked.

---

## F03 — Hook Registration Duplicated; Matchers Wrong 🔴 HIGH

**Evidence**
- [hooks/hooks.json:15](hooks/hooks.json:15) — `pre-bash-guard.sh` on `matcher: "Bash"`
- [hooks/hooks.json:24](hooks/hooks.json:24) — `pre-commit-lint.sh` on `matcher: "Bash"` (no glob → runs on **every** Bash call)
- [.claude/settings.json:124](.claude/settings.json:124) — `matcher: "Bash(git commit*)"` (permission-rule syntax, not docs-valid for `matcher`)
- [.claude/settings.json:148](.claude/settings.json:148) — `matcher: "Bash(dotnet new*)"` (same problem)
- Both files duplicate the PostToolUse `Edit|Write` registration.

**Why it matters:** Per Claude Code hooks docs, `matcher` filters `tool_name` only. Command-pattern matching belongs in a handler-level `if` field. Both the plugin manifest and the project settings have the wrong shape — the plugin manifest under-filters (runs on every Bash); the project settings use a `matcher` syntax that may match nothing or may behave unpredictably depending on parser quirks.

**Agreed fix:** Pick one source of truth (plugin manifest preferred). Convert command-pattern hooks to:

```json
{
  "matcher": "Bash",
  "hooks": [{
    "type": "command",
    "command": "bash hooks/pre-commit-lint.sh",
    "if": "Bash(git commit*)"
  }]
}
```

Same shape for `Bash(dotnet new*)` and `Edit(*.cs)`/`Write(*.cs)` filters.

---

## F04 — Detected Paths Saved Nested, Read Top-Level 🔴 HIGH

**Evidence**
- [src/dotnet_ai_kit/config.py:122-124](src/dotnet_ai_kit/config.py:122) — `load_project()` correctly unwraps nested `detected` key
- [src/dotnet_ai_kit/config.py:144](src/dotnet_ai_kit/config.py:144) — `save_project()` writes `{"detected": ...}` nested

Six call sites bypass `load_project()`:
- [src/dotnet_ai_kit/cli.py:477-478](src/dotnet_ai_kit/cli.py:477) — init: raw YAML + top-level `detected_paths`
- [src/dotnet_ai_kit/cli.py:1067-1068](src/dotnet_ai_kit/cli.py:1067) — upgrade: same
- [src/dotnet_ai_kit/cli.py:1149-1151](src/dotnet_ai_kit/cli.py:1149) — profile deploy: top-level `project_type`, `confidence`
- [src/dotnet_ai_kit/cli.py:1671-1672](src/dotnet_ai_kit/cli.py:1671) — configure: same as init
- [src/dotnet_ai_kit/cli.py:1711-1713](src/dotnet_ai_kit/cli.py:1711) — profile deploy duplicate
- [src/dotnet_ai_kit/copier.py:982, 985-986, 1003](src/dotnet_ai_kit/copier.py:982) — linked-repo deployment: same bug for secondary repos

**Why it matters:** After init/upgrade/configure, `detected_paths` is `None`. Skill `${detected_paths.aggregates}/**/*.cs` tokens never resolve. Profile deployment falls back to `"generic"`/`"low"`. Combined with F05 this makes the skill scoping system inert end-to-end. The linked-repo bug means the workaround "run init in the secondary repo" doesn't work either.

**Agreed fix:** Migrate all six sites to `load_project()`. Add a regression test that calls `save_project()` then `load_project()` and asserts `detected_paths` round-trips. Add a second test that simulates a legacy top-level YAML file and asserts it still loads.

---

## F05 — Skill Activation Fields Buried Under `metadata:` 🟠 MED

**Evidence**
- [skills/microservice/command/aggregate-design/SKILL.md:5-9](skills/microservice/command/aggregate-design/SKILL.md:5) — `paths`, `when-to-use`, `agent` under `metadata`
- [skills/testing/unit-testing/SKILL.md:5-9](skills/testing/unit-testing/SKILL.md:5) — same pattern
- 124 of 124 skill files use this nested pattern.

**Why it matters:** Claude Code skill discovery reads top-level frontmatter only (`description`, `when_to_use`, `paths`, `disable-model-invocation`, `user-invocable`). Anything under `metadata:` is invisible to the skill router. Skills cannot be path-scoped or filtered by `when_to_use` in the current shape.

**Agreed fix:** Move activation fields to top-level frontmatter. Keep `metadata:` only for non-Claude consumers (Cursor `category`, internal `agent` routing) — those fields don't pollute Claude.

```yaml
---
name: aggregate-design
description: Use when designing or implementing event-sourced aggregate roots.
when_to_use: When creating or modifying aggregates, factory methods, or Apply methods.
paths:
  - "${detected_paths.aggregates}/**/*.cs"
metadata:
  category: microservice/command
  agent: command-architect
---
```

---

## F06 — Skill Trigger Text Hidden From Router 🟠 MED

**Evidence**
- [skills/testing/unit-testing/SKILL.md:3](skills/testing/unit-testing/SKILL.md:3) top-level `description` is short doc
- [skills/testing/unit-testing/SKILL.md:8](skills/testing/unit-testing/SKILL.md:8) the actual trigger is in `metadata.when-to-use`
- Same pattern across all 115 skills with `metadata.when-to-use`.

**Why it matters:** After F05 is fixed, the router needs trigger text. Today the stronger trigger lives in metadata. If the F05 fix lifts `when-to-use` to top-level `when_to_use`, this resolves automatically. Listed separately because **the rewrite needs to think about what makes a good trigger phrase**, not just renaming.

**Agreed fix:** Rewrite each `description` as a concrete trigger sentence ("Use when …") and add top-level `when_to_use` where the existing `metadata.when-to-use` adds context beyond the description. **Do not** add a brittle minimum-character test for description.

---

## F07 — Rules Are Unconditional + Carry Cursor-Style `alwaysApply` 🟠 MED

**Evidence**
- All 16 rule files have `alwaysApply: true` in frontmatter
- All 16 have no top-level `paths:`
- Total physical lines: 880 (~ 9k tokens loaded every session)

**Why it matters:** Claude Code rules are always-loaded by **absence** of `paths`, not by presence of `alwaysApply`. The `alwaysApply` field is a Cursor convention with no effect in Claude. Removing it is correctness hygiene; the token savings come from **adding `paths:`** to all but a small universal set.

**Agreed fix:**
- Delete `alwaysApply` from every rule (and profile and skill that has it).
- Keep universal rules unscoped: `existing-projects.md`, `tool-calls.md`, trimmed `coding-style.md`, trimmed `security.md`.
- Path-scope the rest, e.g. `rules/api-design.md` → `paths: ["**/Controllers/**/*.cs", "**/Endpoints/**/*.cs", "**/Program.cs"]`.

---

## F08 — Commands Bulk-Load Agent Skill Lists 🟠 MED

**Evidence**
- [commands/implement.md:93](commands/implement.md:93) — "Load all skills listed in the secondary agent's Skills Loaded section."
- [commands/tasks.md:38](commands/tasks.md:38), [commands/clarify.md:40](commands/clarify.md:40), [commands/review.md:27](commands/review.md:27), [commands/add-tests.md:75](commands/add-tests.md:75) — same instruction.
- Pattern appears in 16 of 27 commands.

**Why it matters:** Even with perfect skill metadata, commands explicitly ask the model to read 18 skill bodies per architect. That is ~3,600-5,400 lines of preload per command invocation.

**Agreed fix:** Replace with bounded selection:

```markdown
Select the minimum context needed:
1. Read one primary architect agent for the project type.
2. Read at most 2 task-specific skills before editing.
3. Read more only when the current task proves it needs more.
4. Prefer MCP symbol/graph queries before reading full files.
```

---

## F09 — `expertise → skills` Subagent Preload 🟠 MED

**Evidence**
- [src/dotnet_ai_kit/agents.py:71](src/dotnet_ai_kit/agents.py:71) — `"expertise": lambda skills: {"skills": skills}`
- All 13 agents have `expertise:` frontmatter feeding this transformation.

**Why it matters:** Claude Code subagent docs state that the `skills:` field injects the full skill body into subagent context at startup. The current mapping turns descriptive `expertise` metadata into ~18 preloaded skill bodies per architect.

**Agreed fix:** Drop the `expertise` → `skills` lambda. Keep `expertise` as descriptive metadata (visible to humans, used by command routing logic) — do not emit it as Claude `skills:`.

---

## F10 — Agent Body `## Skills Loaded` Lists 🟠 MED

**Evidence**
- [agents/dotnet-architect.md:20-38](agents/dotnet-architect.md:20) — 18 skills listed
- [agents/api-designer.md:19-37](agents/api-designer.md:19) — 18 skills listed
- All 13 agents have this section.

**Why it matters:** The body list is the source the commands point at when they say "Load all skills listed." Even if F08 is fixed, the lists themselves still arrive in context when the agent body is read.

**Agreed fix:** Delete the `## Skills Loaded` section in every agent. Optionally replace with a one-line "Primary skill: X" pointer.

---

## F11 — `Availability: Always` in 2 Agent Bodies 🟡 LOW-MED

**Evidence (Codex re-verified — only 2, not 13)**
- [agents/dotnet-architect.md:16](agents/dotnet-architect.md:16) — `**Availability**: Always (loaded for every interaction)`
- [agents/reviewer.md:14](agents/reviewer.md:14) — same

**Why it matters:** Survives YAML fixes because it's prose, not frontmatter. Reinforces the wrong always-loaded model.

**Agreed fix:** Remove the two lines.

---

## F12 — Profile + Agent Architecture Duplication 🟡 LOW-MED

**Evidence**
- [src/dotnet_ai_kit/copier.py:24-41](src/dotnet_ai_kit/copier.py:24) — `PROFILE_MAP` deploys one of 12 profiles per project
- [src/dotnet_ai_kit/copier.py:609](src/dotnet_ai_kit/copier.py:609) — profile copied as `.claude/rules/architecture-profile.md`
- [profiles/microservice/command.md:2](profiles/microservice/command.md:2) — `alwaysApply: true` (and same in 11 others)
- [commands/implement.md:74-81](commands/implement.md:74) — commands separately route by architecture to agents.

**Why it matters:** Profiles and agents both describe the same architecture from different angles. Profiles also carry the Cursor-style `alwaysApply`. **But** profiles also feed the Haiku edit-check hook prompt ([src/dotnet_ai_kit/copier.py:616-677](src/dotnet_ai_kit/copier.py:616)) — they cannot simply be deleted.

**Agreed fix:** Keep compact profiles as the single architecture-constraint source AND hook input. Path-scope them where possible. Remove `alwaysApply`. Strip duplicate architecture narrative from agents/commands so the profile is the single source.

---

## F13 — `/dai.learn` Recommends Always-Loaded Constitution 🟠 MED

**Evidence**
- [commands/learn.md:107](commands/learn.md:107) — "Add this file as an always-loaded rule in your AI tool configuration"
- [commands/learn.md:29-89](commands/learn.md:29) — constitution structure captures aggregates, entities, events, packages, conventions, patterns (potentially large)
- [skills/workflow/plan-templates/SKILL.md:26, 73](skills/workflow/plan-templates/SKILL.md:26) — downstream references

**Agreed fix:** Constitution becomes a compact index (under 100 lines). Detailed architecture/domain/event/package notes move to on-demand files:

```text
.dotnet-ai-kit/memory/
  constitution.md       # index, < 100 lines
  architecture.md       # on-demand
  domain-model.md       # on-demand
  event-flow.md         # on-demand
  conventions.md        # on-demand
```

Remove the "always-loaded rule" recommendation.

---

## F14 — Commands Don't Prefer MCP-First Discovery 🟠 MED

**Evidence**
- [.mcp.json](mcp.json) configures only `csharp-ls`.
- [commands/implement.md:74-93](commands/implement.md:74) routes through agents and skill lists, no MCP guidance.
- [commands/review.md:27](commands/review.md:27) loads reviewer + all listed skills, no MCP step.
- Operational commands have zero references to `csharp-ls`, `symbol`, `references`, or `MCP`.

**Why it matters:** Adding MCP servers without changing command authoring saves nothing — Claude still follows the broad-read instructions in the command body.

**Agreed fix:** Add bounded MCP-first guidance to `detect`, `learn`, `analyze`, `plan`, `implement`, `review`, `add-tests`:

```markdown
Before reading full files:
1. Use MCP symbol/reference/route tools where available.
2. Read only the smallest relevant files.
3. Fall back to grep/file-reads when MCP is unavailable.
```

Frame as **this plugin's authoring convention**, not as an official Claude Code mandate (no docs page states this).

---

## F15 — MCP Roadmap Sequencing 🟢 LOW

**Evidence**
- [.mcp.json:3-6](mcp.json:3) — `csharp-ls` only
- F14 demonstrates commands haven't been rewritten to exploit MCP.

**Agreed fix:** Sequence:
1. Keep `csharp-ls`.
2. After Phases 0-2 land and are measured, add a graph MCP (e.g. `codebase-memory-mcp`).
3. Defer a custom Roslyn MCP until the remaining gaps are specifically CQRS/event-flow shaped.

Building a custom MCP before the local eager-loading fixes solves the wrong problem first.

---

## F16 — No Token Budget Tests; 3 Commands Over Budget 🟠 MED

**Evidence (physical line counts)**
- `commands/implement.md` — 235 lines (budget 200)
- `commands/tasks.md` — 203 lines (budget 200)
- `commands/clarify.md` — 202 lines (budget 200)

**Agreed fix:** Add pytest checks. Concrete list in the "Regression Tests" section below.

---

## F17 — Post-Edit Hook Spawns On Every Edit/Write 🟢 LOW

**Evidence**
- [hooks/hooks.json:35-41](hooks/hooks.json:35) — `matcher: "Edit|Write"`
- [.claude/settings.json:137-145](.claude/settings.json:137) — duplicate registration
- [hooks/post-edit-format.sh:26-29](hooks/post-edit-format.sh:26) — self-filters non-`.cs` after launch

**Agreed fix:** Add handler-level `if: "Edit(*.cs)"` / `if: "Write(*.cs)"`. Keep script self-filter as fallback.

---

## F18 — Rule/Skill Pattern Guidance Overlap 🟢 LOW

**Evidence**
- [rules/api-design.md:12-13](rules/api-design.md:12) duplicates [skills/api/controller-patterns/SKILL.md:139-202](skills/api/controller-patterns/SKILL.md:139) on ProblemDetails.
- [rules/testing.md:21](rules/testing.md:21) duplicates [skills/testing/unit-testing/SKILL.md:16-20](skills/testing/unit-testing/SKILL.md:16) on AAA.

**Agreed fix:** After F07 lands, prune each rule to compact hard policy only. Pattern examples, tables, and code recipes belong in skills.

---

## Phased Fix Plan

### Phase 0 — Safety + startup pressure (under 1 hour)

- F01: rewrite SessionStart hook
- F02: change `exit 1` → `exit 2` in both blocking hooks (and add tests)
- F03: choose hook source-of-truth and convert command filters to `matcher: "Bash" + if:`

### Phase 1 — Frontmatter & data-flow correctness

- F05: lift skill activation fields to top-level
- F06: rewrite descriptions; promote `when-to-use` to `when_to_use`
- F07 (part 1): remove `alwaysApply` from rules, skills, profiles
- F04: migrate all 6+ `cli.py`/`copier.py` raw-read sites to `load_project()`

### Phase 2 — Lazy-loading enforcement

- F07 (part 2): path-scope all non-universal rules and profiles
- F08: remove "Load all skills listed" from 16 commands
- F09: drop `expertise → skills` lambda in `agents.py`
- F10: delete `## Skills Loaded` sections from 13 agents
- F11: delete `Availability: Always` lines from 2 agents
- F12: strip duplicate architecture narrative from agents/commands

### Phase 3 — Memory + MCP workflow

- F13: redesign `/dai.learn` output (index + on-demand files)
- F14: add MCP-first guidance to 7 operational commands
- F15: keep `csharp-ls`; add graph MCP only after measuring local fixes

### Phase 4 — Regression tests + measurement

- F16: add the test suite below
- F17: tighten post-edit-format matcher
- F18: prune rule duplication after F07 path-scoping
- Measure representative `/dai.do`, `/dai.implement`, `/dai.review` token usage before/after

---

## Regression Tests (pytest)

Each test described as a one-liner; intent should be obvious to a future maintainer.

1. `test_no_skill_activation_fields_under_metadata` — assert no SKILL.md has `paths`/`when-to-use`/`when_to_use`/`disable-model-invocation`/`user-invocable`/`alwaysApply` nested in `metadata:`.
2. `test_no_alwaysApply_in_rules_profiles_skills` — assert `alwaysApply` does not appear in `rules/*.md`, `profiles/**/*.md`, or `skills/**/SKILL.md` frontmatter.
3. `test_non_universal_rules_are_path_scoped` — assert every rule except a whitelist (`existing-projects`, `tool-calls`, `coding-style`, `security`) has top-level `paths:`.
4. `test_commands_have_no_bulk_skill_load` — grep `Load all skills listed` in `commands/*.md` returns zero.
5. `test_no_expertise_to_skills_mapping` — assert `AGENT_FRONTMATTER_MAP["claude"]` has no `expertise` lambda producing `{"skills": ...}`.
6. `test_no_agent_skills_loaded_section` — assert `## Skills Loaded` absent in every `agents/*.md`.
7. `test_no_availability_always_text` — assert `**Availability**: Always` absent in every `agents/*.md`.
8. `test_hooks_blocking_uses_exit_2` — assert `pre-bash-guard.sh` and `pre-commit-lint.sh` exit `2` on blocking branches.
9. `test_hook_command_filters_use_if_not_matcher` — assert no `.claude/settings.json` or `hooks/hooks.json` matcher contains a permission rule like `Bash(... *)` or `Edit(*.cs)`.
10. `test_post_edit_format_filtered_at_config` — assert post-edit-format hook has `if: "Edit(*.cs)"`/`if: "Write(*.cs)"`.
11. `test_cli_uses_load_project_for_project_yml` — assert `cli.py` and `copier.py` have no raw `yaml.safe_load(project_yml...)` outside the `load_project()` body.
12. `test_command_line_budget` — every `commands/*.md` ≤ 200 physical lines.
13. `test_rule_line_budget` — every `rules/*.md` ≤ 100 physical lines.
14. `test_skill_line_budget` — every `skills/**/SKILL.md` ≤ 400 physical lines.
15. `test_learn_does_not_say_always_loaded_rule` — assert `commands/learn.md` does not contain "always-loaded rule".
16. `test_operational_commands_have_mcp_guidance` — assert `detect`, `learn`, `analyze`, `plan`, `implement`, `review`, `add-tests` mention MCP/symbol/reference tools at least once.
17. `test_skill_descriptions_are_top_level` — assert every SKILL.md has top-level `description:`, optionally `when_to_use:`.
18. `test_save_project_load_project_roundtrip` — write a `DetectedProject` via `save_project()`, read back via `load_project()`, assert `detected_paths` round-trips.
19. `test_legacy_top_level_project_yml_still_loads` — write a legacy top-level YAML, assert `load_project()` returns the same `DetectedProject`.

---

## Measurement Plan

Capture before/after with Claude Code `/cost` on:

- `/dai.do "Add hello world feature"` — small surface, mostly startup
- `/dai.implement` on a 5-task feature — agent + skill load mid-flight
- `/dai.review` — review-time skill load

Track:
- Total tokens, broken down: system + skills + rules + tool results
- Tool calls per command (count + bytes)
- Wall time

Report regression if any of the three runs exceed pre-fix totals.

---

## Sign-off

| Reviewer | Role | Verified |
|---|---|---|
| Codex (gpt-5.5 xhigh) | Original scan, round-1 critique, structure agreement | ✅ |
| Claude (Opus 4.7) | Verification, additions A–K, round-2 reconciliation | ✅ |

Discussion trail preserved at `issues/discussion/round{1,2}-*`. Either folder (`issues/claude` or `issues/codex`) is a valid entry point; the executive summary is at `issues/FINAL-REPORT.md`.
