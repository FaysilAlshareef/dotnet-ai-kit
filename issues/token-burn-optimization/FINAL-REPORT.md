# dotnet-ai-kit — Token Burn & Plugin-Correctness Final Report

**Status:** Findings agreed by both reviewers; **not yet implemented**.
**Date:** 2026-05-16
**Reviewers:** Codex (gpt-5.5 xhigh) and Claude (Opus 4.7, 1M context)
**Audience:** maintainers of `dotnet-ai-kit`. This is the document to read first.

## Executive Summary

The plugin's lazy-loading model is broken in three independent ways:

1. **Activation metadata is in the wrong place.** All 124 skills nest their `paths`/`when_to_use` under a `metadata:` block that Claude Code does not read. All 16 rules and 12 profiles carry a Cursor-style `alwaysApply: true` that has no effect in Claude. Path scoping does not work end-to-end.
2. **Commands explicitly defeat lazy loading.** 16 of 27 commands tell the agent to "Load all skills listed in the agent's Skills Loaded section" — every architect lists ~18 skills, so every invocation preloads ~3.6–5.4k lines of skill body.
3. **A SessionStart hook actively pushes the agent toward eager loading.** Its closing rule literally reads "If a skill MIGHT apply, load it BEFORE acting. Even a small chance = load it."

In addition, two **safety bugs** were discovered alongside the token work: the "blocking" pre-bash-guard and pre-commit-lint hooks exit with code `1`, but Claude Code requires `exit 2` to actually block — the safety scripts shipped with the plugin currently don't block anything.

**18 findings, 4 HIGH / 8 MED / 6 LOW.** Phased fix plan below. Detailed per-finding evidence + agreed fixes in `issues/claude/final-merged-findings.md` (same content mirrored in `issues/codex/final-merged-findings.md`).

## Severity Scoreboard

| ID | Sev | One-line | Phase |
|---|---|---|---|
| F01 | 🔴 HIGH | SessionStart hook explicitly tells agent to load skills on weak signals | 0 |
| F02 | 🔴 HIGH | Blocking hooks `exit 1`; Claude Code needs `exit 2` to block — safety bug | 0 |
| F03 | 🔴 HIGH | Hook registration duplicated; `matcher` field misuses permission syntax | 0 |
| F04 | 🔴 HIGH | `project.yml` saved nested, read top-level — CLI + linked repos | 1 |
| F05 | 🟠 MED | Skill activation fields buried in `metadata:` block (124/124 skills) | 1 |
| F06 | 🟠 MED | Skill trigger text invisible to router (lives in `metadata.when-to-use`) | 1 |
| F07 | 🟠 MED | All 16 rules unconditional + 28 files carry Cursor `alwaysApply: true` | 1–2 |
| F08 | 🟠 MED | 16 commands say "Load all skills listed in agent's section" | 2 |
| F09 | 🟠 MED | `expertise → skills` lambda preloads ~18 skill bodies per subagent | 2 |
| F10 | 🟠 MED | 13 agent bodies carry `## Skills Loaded` lists (~18 entries each) | 2 |
| F11 | 🟡 LOW-MED | 2 agents say `Availability: Always (loaded for every interaction)` | 2 |
| F12 | 🟡 LOW-MED | Profile + agent duplication; profiles also `alwaysApply` | 2 |
| F13 | 🟠 MED | `/dai.learn` recommends always-loaded constitution | 3 |
| F14 | 🟠 MED | Commands don't prefer MCP-first discovery (zero MCP refs in ops cmds) | 3 |
| F15 | 🟢 LOW | MCP roadmap sequencing: `csharp-ls` alone insufficient | 3 |
| F16 | 🟠 MED | No token budget tests; 3 commands over 200-line budget | 4 |
| F17 | 🟢 LOW | Post-edit format hook process spawns on every Edit/Write | 4 |
| F18 | 🟢 LOW | Rules and skills duplicate pattern guidance | 4 |

## Key Numbers (verified)

| Metric | Value |
|---|---|
| Skill files | 124 |
| Skill files with broken `metadata` activation | **124 (100%)** |
| Rule files | 16 |
| Rule files with `alwaysApply: true` (no-op in Claude) | **16 (100%)** |
| Rule files with `paths:` scoping | **0** |
| Rule total physical lines (always loaded) | 880 (~9k tokens) |
| Commands with "Load all skills listed" | **16 of 27** |
| Agents with `## Skills Loaded` body section | **13 of 13** |
| Agents with `Availability: Always` body text | 2 of 13 |
| Commands currently over 200-line budget | 3 (`implement` 235, `tasks` 203, `clarify` 202) |
| `cli.py` / `copier.py` raw `project.yml` read sites bypassing `load_project()` | 6 |

## Phased Fix Plan

### Phase 0 — Safety + startup pressure (under 1 hour)

The four changes that pay the highest dividend per minute of work, including two safety bugs.

- **F01** — Rewrite `hooks/session-start-bootstrap.sh` with a lazy-default, MCP-first message. Remove "MIGHT apply / load before acting / even a small chance" phrasing.
- **F02** — Change `exit 1` → `exit 2` in `hooks/pre-bash-guard.sh:81` and `hooks/pre-commit-lint.sh:48` (or emit JSON denial). Add tests.
- **F03** — Pick **one** hook registration source (recommend plugin manifest). Convert command-pattern hooks from `matcher: "Bash(git commit*)"` to `matcher: "Bash"` + handler-level `if: "Bash(git commit*)"`.

**Done when:** SessionStart message no longer instructs eager loading; both blocking hooks actually block in a smoke test; `.claude/settings.json` and `hooks/hooks.json` no longer duplicate definitions.

### Phase 1 — Frontmatter & data-flow correctness

- **F05** — Lift skill activation fields to top-level (`description`, `when_to_use`, `paths`, `disable-model-invocation`, `user-invocable`).
- **F06** — Rewrite each skill `description` as a concrete trigger sentence; promote useful `when-to-use` to top-level `when_to_use`.
- **F07 (part 1)** — Remove `alwaysApply` from every rule, profile, and skill that has it.
- **F04** — Migrate the 6 raw-YAML sites in `cli.py` (lines 477, 1067, 1149, 1671, 1711) and `copier.py` (lines 982, 985, 1003) to `load_project()`.

**Done when:** Skill router can see trigger text and paths; `${detected_paths.*}` tokens resolve in init/upgrade/configure/linked-repo deployments; no `alwaysApply` field remains in the repo.

### Phase 2 — Lazy-loading enforcement

- **F07 (part 2)** — Add `paths:` to non-universal rules and profiles. Universal whitelist: `existing-projects`, `tool-calls`, trimmed `coding-style`, trimmed `security`.
- **F08** — Remove "Load all skills listed..." from the 16 commands. Replace with bounded selection (1 agent + ≤ 2 task skills initially).
- **F09** — Drop the `expertise → skills` lambda in `src/dotnet_ai_kit/agents.py:71`.
- **F10** — Delete `## Skills Loaded` sections from all 13 agents.
- **F11** — Delete `**Availability**: Always` line from `agents/dotnet-architect.md:16` and `agents/reviewer.md:14`.
- **F12** — Strip duplicate architecture narrative from agents/commands so the profile is the single source.

**Done when:** A command body + agent body together contribute < 300 lines of preloaded context to any single `/dai.*` invocation.

### Phase 3 — Memory + MCP workflow

- **F13** — Redesign `/dai.learn`: constitution becomes an index (< 100 lines), detail in on-demand `architecture.md`, `domain-model.md`, `event-flow.md`, `conventions.md`. Remove the "always-loaded rule" recommendation.
- **F14** — Add bounded MCP-first guidance to `detect`, `learn`, `analyze`, `plan`, `implement`, `review`, `add-tests`. Frame as **this plugin's authoring convention** (no official Claude Code mandate exists).
- **F15** — Keep `csharp-ls`. Add a graph MCP (e.g. `codebase-memory-mcp`) only after measuring Phase 0–2 results. Defer custom Roslyn MCP until remaining gaps are specifically CQRS/event-flow shaped.

### Phase 4 — Tests + measurement

- **F16** — Land the 19 regression tests listed in the detail report.
- **F17** — Add handler `if: "Edit(*.cs)"` / `if: "Write(*.cs)"` to the post-edit-format hook.
- **F18** — Prune pattern duplication between rules and skills now that rules are path-scoped.
- Capture `/cost` for `/dai.do`, `/dai.implement`, `/dai.review` before and after. Fail the PR if any run exceeds the pre-fix total.

## Top Regression Tests

See `issues/claude/final-merged-findings.md` for the full 19-test list. Highlights:

- `test_hooks_blocking_uses_exit_2`
- `test_no_skill_activation_fields_under_metadata`
- `test_no_alwaysApply_in_rules_profiles_skills`
- `test_commands_have_no_bulk_skill_load`
- `test_no_expertise_to_skills_mapping`
- `test_no_agent_skills_loaded_section`
- `test_hook_command_filters_use_if_not_matcher`
- `test_cli_uses_load_project_for_project_yml`
- `test_command_line_budget`, `test_rule_line_budget`, `test_skill_line_budget`
- `test_learn_does_not_say_always_loaded_rule`
- `test_save_project_load_project_roundtrip`

## Methodology

| Step | Reviewer | Output |
|---|---|---|
| 1. Original scan | Codex (gpt-5.5 xhigh) | `issues/codex/token-burn-optimization-report.md` — 10 issues |
| 2. Verification + additions | Claude (Opus 4.7) | `issues/claude/token-burn-verification-and-additions.md` — verified 8/10, found Issues A–J |
| 3. Round 1 cross-review | Codex | `issues/discussion/round1-codex-reply.md` — verified A–J, added 4 issues (incl. 2 safety bugs), corrected Claude's stale line counts |
| 4. Round 2 reconciliation | Claude | `issues/discussion/round2-claude-reply.md` — accepted all Codex corrections, added Issue K |
| 5. Round 2 confirmation | Codex | re-verified Issue K (2 agents, not 13); structure approved |
| 6. Merge | Both | `issues/claude/final-merged-findings.md` + `issues/codex/final-merged-findings.md` (mirrored) |
| 7. This report | Both | `issues/FINAL-REPORT.md` |

Both reviewers used web research against official Claude Code docs (`code.claude.com/docs/en/{skills,memory,mcp,hooks,sub-agents}`) to validate behavioural claims. All file:line citations were verified at least once during the discussion.

## What Changed Between Reports

- **Codex's original report stands** in nearly all substance. Specifically, its over-budget line counts for `implement`/`tasks`/`clarify` (236/204/203 physical lines) were initially disputed by Claude using `Measure-Object -Line` (non-blank), but a re-count using `File.ReadAllLines().Count` confirmed 235/203/202 — Codex was right.
- **Codex added two safety findings** Claude initially missed: blocking-hook exit codes and matcher-vs-`if` misuse.
- **Claude added the SessionStart hook finding** (F01), which Codex agreed is the single highest-leverage Phase 0 change.
- **Claude's "delete profile deployment" suggestion was withdrawn** after Codex pointed out profiles also feed the Haiku edit-check hook prompt.
- **Issue K** (agent body `Availability: Always`) was initially scoped by Claude to "likely all 13 agents." Codex re-grepped and found only 2.

## File Index

- `issues/FINAL-REPORT.md` — this file
- `issues/claude/final-merged-findings.md` — full per-finding detail (Claude voice)
- `issues/codex/final-merged-findings.md` — full per-finding detail (Codex voice; same content)
- `issues/codex/token-burn-optimization-report.md` — Codex's original scan
- `issues/claude/token-burn-verification-and-additions.md` — Claude's verification + additions
- `issues/discussion/round1-claude-to-codex.md` — discussion round 1 prompt
- `issues/discussion/round1-codex-reply.md` — Codex's round 1 reply
- `issues/discussion/round2-claude-reply.md` — Claude's round 2 reply
- `issues/discussion/codex-ready.txt` — Codex's structure-approval marker

## Sign-off

Both reviewers approve this report as the agreed source of truth.

- **Codex (gpt-5.5 xhigh)** — verified counts, ran final grep checks, drafted mirror findings file
- **Claude (Opus 4.7, 1M context)** — drafted this report and the Claude-side mirror findings file
