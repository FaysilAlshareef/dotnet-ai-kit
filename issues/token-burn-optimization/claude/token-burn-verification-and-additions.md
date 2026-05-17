# Token Burn — Claude Verification & Additional Findings

Status: discovered, not implemented
Source: Independent codebase scan to verify `issues/codex/token-burn-optimization-report.md` and look for issues Codex missed
Date: 2026-05-16
Author: Claude Code

## Executive Summary

Codex's report is largely correct. Of its 10 issues, **8 are verified as real**, **1 has stale evidence but the underlying need still applies**, and **2 are architectural recommendations rather than concrete defects**. This document records the verification, corrects the stale numbers, and adds **10 additional issues** Codex missed that compound the token-burn problem.

The most consequential additions:

- A SessionStart hook actively instructs the agent to load skills aggressively, working against every lazy-loading fix.
- Rule frontmatter uses Cursor-style `alwaysApply: true` that Claude Code does not recognise.
- Hook configuration is duplicated between `.claude/settings.json` and `hooks/hooks.json`, with one path running the commit lint on every Bash call rather than git commits.
- Skill `description` fields are short but `when-to-use` is buried in `metadata` — Claude's skill-discovery layer never sees the trigger.

---

## Part 1: Verification of Codex's 10 Issues

### Issue 1 — Skill activation fields under `metadata` ✅ VERIFIED

Counted across all 124 `SKILL.md` files:

- 124 files contain a top-level `metadata:` block
- 0 files contain top-level `paths:`, `when_to_use:`, `when-to-use:`, `disable-model-invocation:`, or `user-invocable:`
- All activation hints (`paths`, `when-to-use`, `agent`, `category`) are nested under `metadata`

Example confirmed: `skills/microservice/command/aggregate-design/SKILL.md:5-9` — `paths`, `when-to-use`, `agent` are all under `metadata:`.

**Impact:** Claude Code ignores nested activation hints; skills cannot be path-scoped and `when_to_use` is invisible to the skill router.

### Issue 2 — Rules are unconditional ✅ VERIFIED (+ correction)

- 16 rule files, **0** with `paths:` frontmatter
- Total ~36,849 chars across all rule files (close to Codex's 36,631)
- Per-file ranges: 31–65 lines, 1,856–3,469 chars

Largest: `rules/testing.md` (65 lines, 3,469 chars). Smallest: `rules/error-handling.md` (35 lines, 1,856 chars).

**Correction:** Codex listed 896 lines; actual is 705 lines across the 16 files. The chars/tokens estimate stands.

### Issue 3 — Commands bulk-load skills ✅ VERIFIED

Found "Load all skills listed" in **16 of 27** command files. Verified files:

```
add-aggregate, add-crud, add-endpoint, add-entity, add-event, add-page,
add-tests, analyze, clarify, docs, implement, plan, review, specify,
tasks, verify
```

Confirmed at [commands/implement.md:93](commands/implement.md:93): "Load all skills listed in the secondary agent's Skills Loaded section."

### Issue 4 — Subagents preload skills ✅ VERIFIED

[src/dotnet_ai_kit/agents.py:71](src/dotnet_ai_kit/agents.py:71) maps source `expertise` directly into Claude `skills`:

```python
"expertise": lambda skills: {"skills": skills},
```

Verified `agents/dotnet-architect.md:20-38` lists 18 skills under "Skills Loaded". Every agent has a body-level "Skills Loaded" list (13/13 agents). All 13 contain this section.

### Issue 5 — Detected paths saved nested, read top-level ✅ VERIFIED

`save_project()` at [src/dotnet_ai_kit/config.py:144](src/dotnet_ai_kit/config.py:144) writes `{"detected": project.model_dump(...)}` — nested format.

`cli.py` reads top-level at **6 call sites**:

- Line 478: `_init_proj.get("detected_paths")` (init path)
- Line 1068: `_upg_proj.get("detected_paths")` (upgrade path)
- Line 1150: `project_data.get("project_type", "generic")` (profile deploy A)
- Line 1672: `_cfg_proj.get("detected_paths")` (configure path)
- Line 1712: `project_data.get("project_type", "generic")` (profile deploy B)
- Line 1713: `project_data.get("confidence", "low")`

All 6 sites bypass `load_project()`, which itself unwraps `detected` correctly. After init/upgrade/configure, `detected_paths` is `None` and profile selection falls back to `"generic"`.

### Issue 6 — `/dai.learn` recommends always-loaded constitution ✅ VERIFIED

[commands/learn.md:107](commands/learn.md:107):
> "Note: Add this file as an always-loaded rule in your AI tool configuration"

Confirmed. The constitution captures aggregates, entities, events, conventions, packages, and patterns — it can grow large.

### Issue 7 — MCP exists but commands do not prefer it ✅ VERIFIED

`.mcp.json` configures only `csharp-ls`. None of the 27 commands contain the strings "MCP", "csharp-ls", "symbol", or "find_references" in their instruction body (spot-checked `analyze.md`, `implement.md`, `learn.md`, `review.md`). All instruct broad reads.

### Issue 8 — `csharp-ls` is not enough 🟡 RECOMMENDATION (not a defect)

Verified `.mcp.json` content. The recommendation to add a code-graph MCP is sound but is a design choice, not a defect. Move forward only after Issues 1–5 are fixed; otherwise the new MCP runs alongside broad reads and saves nothing.

### Issue 9 — Custom Roslyn MCP not first move 🟡 RECOMMENDATION

Same category as Issue 8. Sound sequencing advice.

### Issue 10 — Token budget tests ⚠️ STALE EVIDENCE, valid intent

Codex listed three over-budget commands. **Actual current line counts:**

| File | Codex said | Now | Status |
|------|------------|-----|--------|
| `commands/implement.md` | 236 | **179** | under 200 |
| `commands/tasks.md` | 204 | **153** | under 200 |
| `commands/clarify.md` | 203 | **151** | under 200 |

All 27 commands are currently under 200 lines (max is `implement.md` at 179). The files were trimmed after Codex's scan. The proposed regression tests are still valuable to prevent re-growth, but the "current violations" claim is no longer accurate.

---

## Part 2: Additional Issues Codex Missed

### Issue A — SessionStart hook fights lazy loading 🔴 HIGH

[hooks/session-start-bootstrap.sh:5-14](hooks/session-start-bootstrap.sh:5):

```
[dotnet-ai-kit] Skills active. Before any action, check if a skill applies:
  - Building/fixing? → skills/workflow/systematic-debugging
  - Completing work? → skills/workflow/verification-gate
  ...
Rule: If a skill MIGHT apply, load it BEFORE acting. Even a small chance = load it.
```

This system-reminder is injected at **every session start** (registered in `hooks/hooks.json:3-12`). The final rule explicitly tells the agent to load skills on weak signals — directly opposite to the lazy-loading direction Codex recommends.

**Impact:** Every other fix in this report is undermined while this hook fires. It is the loudest instruction the agent sees at startup.

**Fix:** Replace with an MCP-first, lazy-by-default reminder, e.g.:

```
[dotnet-ai-kit] Skills available on demand. Before reading bodies:
1. Use MCP tools (csharp-ls) to locate exact code.
2. Read at most 1 skill per task before editing; add more only if needed.
3. Treat skill paths and rule paths as just-in-time references, not preloads.
```

### Issue B — Cursor-style `alwaysApply` in rules has no effect in Claude 🟠 MEDIUM

All 16 rules contain `alwaysApply: true` in frontmatter. Claude Code does not recognise this field — rules without `paths:` are already always-loaded by default. The field is decorative and signals format confusion (Cursor uses `alwaysApply`; Claude uses `paths`/absence-of-paths).

Same pattern in skills: 9 nested `metadata.alwaysApply` entries (per Codex's count) — also a no-op for Claude.

**Fix:** Remove `alwaysApply: true` everywhere. Replace with the correct Claude semantics: omit `paths:` for always-loaded, add `paths:` for scoped.

### Issue C — Skill `paths` tokens are dead on arrival 🟠 MEDIUM

Skills use `paths: "${detected_paths.aggregates}/**/*.cs"` under `metadata`. Two compounding failures:

1. Claude Code does not read `metadata.paths` (Issue 1).
2. Even if it did, `detected_paths` is `None` at every call site (Issue 5), so the token would not resolve.

The skill scoping system has **never worked end-to-end** in the current code.

**Fix:** Together with Issues 1 and 5 — move `paths` to top-level frontmatter AND fix `load_project()` use so token substitution receives real data before the skills are written to disk.

### Issue D — Duplicate hook registration with broken matcher 🔴 HIGH

Hooks are registered in two places:

- [.claude/settings.json:110-159](.claude/settings.json:110) — project settings
- [hooks/hooks.json:2-53](hooks/hooks.json:2) — plugin manifest

Both register PreToolUse for `Bash` and PostToolUse for `Edit|Write`. **The plugin manifest's commit-lint matcher is `Bash` (no glob), not `Bash(git commit*)` as in settings.json.** This means in plugin distribution form, `hooks/pre-commit-lint.sh` runs on **every Bash invocation**, not only on commits.

Verified:

```json
// hooks/hooks.json
{ "matcher": "Bash",
  "hooks": [{ "command": "${CLAUDE_PLUGIN_ROOT}/hooks/pre-commit-lint.sh" }] }

// .claude/settings.json
{ "matcher": "Bash(git commit*)",
  "hooks": [{ "command": "bash hooks/pre-commit-lint.sh" }] }
```

**Impact:** Latency tax on every shell call for plugin users; possible duplicate post-edit-format runs for projects using both.

**Fix:** Pick one source of truth. Plugin distribution should rely on `hooks/hooks.json`; fix its matcher to `Bash(git commit*)`. Project-level settings should not re-declare plugin hooks.

### Issue E — Skill router can't see `when_to_use` 🟠 MEDIUM

Spot-checked all skill descriptions: they are short (1-2 lines, ~80-150 chars) and read like documentation, not triggers. The actual trigger phrase lives at `metadata.when-to-use`, which is invisible to Claude's skill index.

**Impact:** Claude's automatic skill selection (when commands don't explicitly load) is uninformed, leading commands to over-compensate with "Load all skills listed..." instructions (Issue 3). Fixing Issue 1 alone helps; also rewrite each `description` to be a concrete trigger sentence.

### Issue F — Body-level "Skills Loaded" lists multiply context 🟠 MEDIUM

Every agent (13/13) contains a `## Skills Loaded` section. Examples:

- `agents/dotnet-architect.md:20-38` — 18 skill paths
- `agents/api-designer.md` — 18 skill paths (per Codex)

Commands instruct: "Load all skills listed in the agent's Skills Loaded section." So:

1. Command tells Claude to read agent body. (~ 60-100 lines of agent)
2. Agent body contains 18-skill list with `*(alwaysApply)*` markers.
3. Command instructs loading them all.
4. Claude loads 18 skill bodies (~200-300 lines each).

That is 3,600-5,400 lines of skill content per architect chosen — for a single command invocation.

**Fix:** Delete the "Skills Loaded" body sections. Move skill discovery into the command's task-typed router (Codex Issue 3 fix). Add at most a 1-2 line "Primary skill: X" pointer in the agent body.

### Issue G — Profiles + agents = double architecture context 🟡 LOW-MEDIUM

`copier.py:26-41` (`PROFILE_MAP`) deploys one architecture profile (~60-73 lines) per project. Commands separately instruct loading `agents/{matching-architect}.md` for the same project type. Both files describe the same architecture from different angles.

**Fix:** Either let the agent be the architecture guide (delete profile deployment) or let the profile be the architecture guide (don't auto-load the architect agent for the same project type). Pick one source.

### Issue H — `bash hooks/pre-bash-guard.sh` runs on every Bash call 🟡 LOW

Even when configured correctly, the pre-bash-guard fires on every Bash call. Per the project's own note, it uses a Haiku prompt so it is cheap — Codex acknowledged this. Listing as a low item for completeness: the **post**-edit-format hook (30s timeout, runs `dotnet format`) is the more expensive one and runs after every Edit/Write. For non-`.cs` files this is wasted work. The hook may already short-circuit by extension — verify and tighten matcher to `Edit|Write` only for `*.cs` if it doesn't.

### Issue I — CLAUDE.md table of commands is loaded every session 🟡 LOW

[CLAUDE.md](CLAUDE.md) (~145 lines) loads at every session start and contains the full 27-command table. Useful for plugin developers; redundant for end-users whose only interaction is `/dai.*` discovery via Claude's command list.

**Fix:** Move the per-command table into a `docs/commands.md` referenced by CLAUDE.md, keep CLAUDE.md to architecture + conventions only.

### Issue J — No deduplication between rules and skills 🟡 LOW

Spot-checked:

- `rules/api-design.md` (40 lines) + `skills/api/controller-patterns/SKILL.md` + `skills/api/minimal-api/SKILL.md`
- `rules/data-access.md` + `skills/data/ef-core-basics/SKILL.md` + `skills/data/ef-queries/SKILL.md`
- `rules/testing.md` + `skills/testing/unit-testing/SKILL.md`

Rules establish conventions; skills give patterns. The overlap is real (HTTP status codes, ProblemDetails, AAA test pattern appear in both). With rules always-loaded and skills sometimes-loaded, the agent pays twice for the same content the moment a relevant skill loads.

**Fix:** After Issue 2 (path-scope rules), prune each rule to non-pattern policy only (e.g. "Always use ProblemDetails for errors"; never code examples). Move pattern examples to skills.

---

## Part 3: What Must Happen — Prioritised Plan

The order matters. Doing Phase 1 before Phase 2 makes Phase 2 measurable; reversing the order makes everything noisier.

### Phase 0 — Stop the bleeding (under 1 hour)

1. **Replace `hooks/session-start-bootstrap.sh`** with an MCP-first, lazy-default message. Issue A is the highest-leverage single change because it shapes every subsequent decision the agent makes.
2. **Fix the matcher in `hooks/hooks.json:24`** — change `"matcher": "Bash"` to `"matcher": "Bash(git commit*)"` for the pre-commit-lint entry.

### Phase 1 — Metadata correctness

3. Move skill frontmatter fields to top-level: `name`, `description`, `when_to_use`, `paths`. Keep `metadata:` only for non-Claude consumers (Cursor/Copilot if/when implemented). Rewrite each `description` to be a concrete trigger sentence (Issue E).
4. Remove `alwaysApply:` from every rule and every skill (Issue B). Replace with `paths:` where scoping applies.
5. Path-scope rules. Universal stays: `existing-projects.md`, `tool-calls.md`, a trimmed `coding-style.md`, a trimmed `security.md`. Everything else gets `paths:` (Codex Issue 2).
6. Fix `cli.py` to use `load_project()` at all 6 call sites and resolve `detected_paths` before token substitution (Codex Issue 5).

### Phase 2 — Command and agent slimming

7. Remove "Load all skills listed..." from all 16 commands (Codex Issue 3).
8. Delete agent body "Skills Loaded" sections (Issue F). Keep agent frontmatter clean: no `skills:` injected from `expertise` (Codex Issue 4).
9. Decide profile vs agent overlap (Issue G) and pick one.

### Phase 3 — Memory & MCP

10. Change `/dai.learn` guidance to never recommend always-loaded constitution (Codex Issue 6). Split into index + on-demand files.
11. Add MCP-first instructions to detect/learn/analyze/plan/implement/review/add-tests commands (Codex Issue 7).
12. Add a graph MCP (e.g. `codebase-memory-mcp`) after Phase 1-2 are landed and measured (Codex Issue 8).

### Phase 4 — Regression tests

13. Add the tests Codex proposed (Codex Issue 10) plus:
    - No rule contains `alwaysApply:` in frontmatter
    - No agent body contains `## Skills Loaded`
    - `hooks/hooks.json` matcher for `pre-commit-lint.sh` is `Bash(git commit*)`
    - Skill `description` length ≥ 60 chars and contains a trigger word
    - `cli.py` does not use `yaml.safe_load(project_yml...)` outside `load_project()`

### Phase 5 — Measure, then maybe build Roslyn MCP

14. Use `/cost` to capture before/after token usage on a representative `/dai.do` run.
15. Only build a custom Roslyn MCP if the gap is specifically CQRS/event-flow shaped (Codex Issue 9).

---

## Resources Used

### Files actually read (this scan)

- `.mcp.json`
- `.claude/settings.json`
- `.claude-plugin/plugin.json`
- `hooks/hooks.json`
- `hooks/session-start-bootstrap.sh`
- `CLAUDE.md` (loaded via context)
- `commands/analyze.md`, `commands/do.md`, `commands/implement.md`, `commands/learn.md`
- `agents/dotnet-architect.md`
- `skills/microservice/command/aggregate-design/SKILL.md`, `skills/testing/unit-testing/SKILL.md`, `skills/microservice/query/event-handler/SKILL.md`
- `rules/api-design.md`
- `src/dotnet_ai_kit/agents.py`, `src/dotnet_ai_kit/config.py`, `src/dotnet_ai_kit/copier.py` (head), `src/dotnet_ai_kit/cli.py` (greps)

### Aggregated counts (this scan)

- Skills: 124 SKILL.md files; 0 top-level path scoping; 133 nested `metadata:` blocks (some skills have two `metadata:` references inside body)
- Rules: 16 files, 705 lines, 36,849 chars, 0 path-scoped, **all 16 with `alwaysApply: true`**
- Commands: 27 files, all under 200 lines, max 179 (`implement.md`); **16 of 27 contain "Load all skills listed"**
- Agents: 13 files, **13 of 13 contain `## Skills Loaded` body section**
- Hooks: 4 hook scripts; registered in **two** places with one matcher mismatch
- Profiles: 12 files, 60-73 lines each, one deployed per project
- Total skill body: ~23,378 lines across 124 files (average ~188 lines)

### External docs not re-fetched

Trusted Codex's accurate citations of Claude Code official docs (`code.claude.com/docs/en/*`) for skill/memory/subagent/MCP/hooks semantics. Those passages match the behaviour observed in this codebase.
