# dotnet-ai-kit - Optimization Roadmap

**Status**: Decision record &middot; **Date**: 2026-05-09 &middot; **Owner**: Faysil Alshareef

Captures all decisions from the May 2026 optimization analysis covering two concerns: (1) multi-repo feature setup gaps observed in the live `Anis.MeterCharger` deployment, and (2) token-burn reduction across the plugin surface. Every recommendation here is anchored to either a verified codebase observation or a cited industry source.

Companion files:
- `planning/token-reduction-report.html` &mdash; visualized version of the token reduction plan with charts.
- `~/.claude/projects/.../memory/project_multi_repo_linked_specs_gap.md` &mdash; updated memory record (original gap closed, new gaps logged).

---

## Executive Summary

| Concern | Current state | Target state | Effort |
|---|---|---|---|
| `/dai.do` token cost | ~200K per run | ~22K per run (-89%) | 5 dev-days |
| `/dai.implement` token cost | ~80-100K | ~9-12K (-89%) | 4 dev-days |
| Cursor session always-loaded | ~9K (alwaysApply on 16 rules) | ~1K (rule scoping) | 2 hours |
| Cost per dev/month (heavy use) | $200-300 | $35-55 | included in above |
| Multi-repo brief projection | Working (verified live) | Add bidirectional repos sync | 1-2 dev-days |
| Multi-repo Python sync CLI | None | `dotnet-ai feature sync` | 1 dev-day |

**Recommended sequence**: Multi-repo Fix #1 (bidirectional repos) &rarr; Token Phase 1 (Changes 1-4) &rarr; Multi-repo Fixes #2-#4 &rarr; Token Phase 2 &rarr; Token Phase 3 &rarr; MCP catalog. Roughly 3 working weeks total to ship everything.

---

## Part A: Multi-Repo Feature Setup Decisions

### A.1 Verified state (Anis.MeterCharger trio)

Confirmed live at `C:\Users\libya\source\repos\Ecom-LTD\Khales\`:

| Repo | dotnet-ai-kit installed | project_type | dotnet | linked_from |
|---|---|---|---|---|
| Anis.MeterCharger.Commands | Yes (primary) | command | net10.0 | n/a |
| Anis.MeterCharger.Queries | Yes (secondary) | query-sql | unknown (stub) | path to Commands |
| Anis.MeterCharger.Processor | Yes (secondary) | processor | unknown (stub) | path to Commands |
| anis.meter-charger | No (unrelated) | n/a | n/a | n/a |

**Brief projection feature works.** Feature `001-infrastructure-setup` has projected briefs at:
- `Anis.MeterCharger.Queries/.dotnet-ai-kit/briefs/Anis.MeterCharger.Commands/001-infrastructure-setup/feature-brief.md`
- `Anis.MeterCharger.Processor/.dotnet-ai-kit/briefs/Anis.MeterCharger.Commands/001-infrastructure-setup/feature-brief.md`

This closes the original "linked-specs" gap recorded in user memory 37 days ago.

### A.2 Remaining gaps

| # | Gap | Source location | Reproducer |
|---|---|---|---|
| 1 | Asymmetric `repos:` map | `src/dotnet_ai_kit/copier.py:772-799` `_update_sibling_config` | From Queries: `/dai.spec "add UserBalance"` projects zero briefs &mdash; secondaries' `repos:` are all `null` |
| 2 | Branch base divergence | per-repo git default detection | Commands on `master`, Queries/Processor detected `main`; coordinated PRs need manual rebase |
| 3 | Bare secondary `project.yml` | sibling auto-init logic | Only 4 lines; missing `layers`, `solution_name`, `dotnet_version`, `namespace_format` &rarr; codegen falls back to defaults in secondaries |
| 4 | No reverse status feedback | `commands/status.md` | Primary's `/dai.status` cannot see brief phase in siblings |
| 5 | No Python `feature sync` CLI | `src/dotnet_ai_kit/cli.py` | CI/non-Claude users cannot regenerate stale briefs after `git pull` |

### A.3 Prioritized fixes

1. **Bidirectional `repos:` propagation** &mdash; smallest diff (~15 LOC in `_update_sibling_config`), unlocks Gap #4. Write reciprocal repos map into each secondary's `config.yml` during sibling deploy. **(1 day)**
2. **`dotnet-ai feature sync` CLI verb** &mdash; new file `src/dotnet_ai_kit/feature_sync.py`, registered in `cli.py`. Iterates `repos:`, scans each sibling's `briefs/{primary-name}/` for stale or missing briefs against primary's `features/`, re-projects. CI-callable, non-LLM path. **(1-2 days)**
3. **`feature_status.json` artifact** &mdash; emit next to each `feature-brief.md` with `{phase, completed_tasks, branch, last_updated}`. `/dai.implement` writes in secondary; primary's `/dai.status` aggregates. **(1 day)**
4. **Full re-detection on sibling init** &mdash; run same detection skill against each sibling's source tree during `_update_sibling_config`. Captures `layers/solution_name/dotnet_version`. **(1 day &mdash; depends on detection skill refactor)**
5. **`coordinated_branch_base` config field** &mdash; primary defines shared base (e.g., `develop`), all sibling brief branches cut from it. **(2 hours)**

---

## Part B: Token Reduction Decisions

### B.1 Diagnosis

The premise that "rules + skills + commands all auto-load" was partially incorrect under Claude Code:

| Layer | Real per-session cost | Why |
|---|---|---|
| Rules (`rules/*.md`) | ~0 tokens (Claude) / ~9K (Cursor with `alwaysApply: true`) | Cursor frontmatter convention, not Claude Code semantics |
| Skill descriptions (frontmatter only) | ~600 tokens (~100 per skill &times; advertised count) | Pre-loaded by Claude Code |
| SessionStart hook stdout | ~80 tokens | Injected each session |
| Skill bodies | 0 tokens (Claude auto-discovers) | UNLESS commands prescribe `Read skills/...` &mdash; this is the actual leak |
| Agent files | 0 tokens unless commands load them | Same |
| Command body | 2.5K-6K when invoked | Per-invocation |
| Skills/agents loaded by command's eager Reads | **20K-100K per command** | The real cost |

**Real burn**: per-command eager `Read skills/...` and `Read agents/...` cascades. Worst offenders: `commands/implement.md` (235 lines, 17 skill refs, 7 agent refs), `commands/do.md` (chains 7 phases), `commands/specify.md`, `commands/tasks.md`. A `/dai.do` run injects 150-250K tokens before any code is written.

### B.2 The 10 changes

| # | Change | Phase | Saved /implement | Saved /do | Effort | Risk |
|---|---|---|---|---|---|---|
| 1 | Description hygiene pass on 124 skills | P1 | enabler | enabler | 1d | Low |
| 2 | Strip eager Reads from 27 commands | P1 | 40K | 100K | 1d | Low |
| 3 | Delete `Skills Loaded` lists in 13 agents | P1 | 15K | 25K | 3h | Low |
| 4 | Demote `alwaysApply`, add `globs:` scoping | P1 | ~0 (Claude) / 9K (Cursor) | same | 2h | Low |
| 5 | Verify all SKILL.md &le; 500 lines | P2 | 3K | 5K | 0.5-1d | Low |
| 6 | Trim shipped CLAUDE.md template | P2 | 1K | 2K | 2h | Low |
| 7 | Add `dotnet-ai audit --tokens` CLI | P2 | regression prevention | same | 1d | Low |
| 8 | Cache-friendly prompt ordering | P3 | 6K | 13K | 4h | Low |
| 9 | Subagent stubs for `/do`, `/implement`, `/review` | P3 | 7K | 25K | 1-2d | **Medium** |
| 10 | Token-savior MCP integration | MCP | 9K | 8K | 2d | Low |

### B.3 Detailed per-change specifications

#### Change 1 &mdash; Description hygiene pass on 124 skills
- **What**: Rewrite every SKILL.md `description:` frontmatter field.
- **Rules**: third-person only (`Generates X` not `I help with X`); trigger keywords first (Claude truncates to 1,536 chars when many skills present); include both *what* and *when*; &le; 1024 chars (Anthropic hard limit).
- **Files**: 124 SKILL.md files in `skills/**/`, frontmatter only.
- **Effort**: 4-6 hours bulk-edit pass with validation script.
- **Why this matters**: Anthropic's Mar 2026 skill-creator A/B testing showed 5/6 of their own skills got better trigger accuracy after this exact pass. Vercel data: skills miss in 56% of cases when descriptions are weak.
- **Risk**: Very low. Pure additive quality fix.

#### Change 2 &mdash; Strip eager `Read skills/...` and `Read agents/...` from 27 commands
- **What**: Remove instructions like *"Read skills/workflow/sdd-lifecycle/SKILL.md. Read agents/dotnet-architect.md and load all 18 skills it lists."* Replace with: *"Use the Skill tool &mdash; Claude will auto-load matching skills from descriptions."*
- **Files**: 27 files in `commands/`. Worst offenders: `implement.md` (235 lines), `do.md`, `specify.md` lines 26-40, `tasks.md`, `analyze.md`, `review.md`, `verify.md`.
- **Effort**: 6-8 hours.
- **Risk**: Low if Change 1 done first. Mitigation: add safety-net lines for must-load workflows, e.g., *"If implementing event-sourced aggregates, ensure aggregate-builder and ddd-patterns skills load."*
- **Depends on**: Change 1.

#### Change 3 &mdash; Delete `Skills Loaded` enumerations from 13 agent files
- **What**: Remove `## Skills Loaded` sections; replace with `## When to invoke this agent` paragraph that names relevant skills in prose for description-based matching.
- **Files**: 13 files in `agents/`. `agents/dotnet-architect.md:21-38` lists 18 skills; `agents/command-architect.md` lists 12; etc.
- **Effort**: 2-3 hours.
- **Risk**: Low.

#### Change 4 &mdash; Demote `alwaysApply: true` on rules; add `globs:` scoping
- **What**: Currently all 16 `rules/*.md` carry `alwaysApply: true`. Cursor community guidance: 2-3 always-on max, sweet spot 5-8 total. Rewrite frontmatter so 2 rules stay always-on (`coding-conventions`, `architecture`); 14 get scoped via globs.
- **Examples**:
  - `rules/testing.md` &rarr; `globs: tests/**/*.cs,**/*Tests.cs`
  - `rules/api-design.md` &rarr; `globs: **/Controllers/**/*.cs,**/Endpoints/**/*.cs`
  - `rules/data-access.md` &rarr; `globs: **/Repositories/**/*.cs,**/Persistence/**/*.cs`
- **Files**: 16 files in `rules/`, frontmatter only.
- **Effort**: 2 hours.
- **Why this matters**: For Cursor users in v1.1 this saves ~9K tokens per request. No-op for Claude Code (which doesn't use `alwaysApply` semantics) but makes rules portable.
- **Risk**: Very low.

#### Change 5 &mdash; Verify all SKILL.md &le; 500 lines
- **What**: Anthropic's hard limit. Currently 14 skills are at 340-398 lines (close); none confirmed over 500 yet. For any over: split using Pattern 1 &mdash; keep SKILL.md as overview, move details to `references/advanced.md`, `references/examples.md`.
- **Constraint**: References must be **one level deep** from SKILL.md. Deeper nesting causes Claude to use `head -100` previews and miss content.
- **Files**: ~14 large SKILL.md files; create sibling `references/` dirs.
- **Effort**: 4-6 hours per offending skill.
- **Risk**: Medium if executed badly (fragmentation). Mitigation: split on domain boundaries, not arbitrary line counts.

#### Change 6 &mdash; Trim shipped CLAUDE.md template; index-then-detail pattern
- **What**: CLAUDE.md template that drops into user projects via `dotnet-ai init`. Cut to &le; 50 lines. Add activation phrase *"IMPORTANT: Read relevant docs below before starting any task"* before a `## Further Reading` links list. Also cut the 27-row commands table from project's own `CLAUDE.md` &mdash; Claude Code already discovers slash commands.
- **Files**: `templates/` (the CLAUDE.md template), project root `CLAUDE.md`.
- **Effort**: 1-2 hours.
- **Why this matters**: Vercel data &mdash; explicit `## Further Reading` references outperformed auto-skill-trigger (skills missed 56% of cases). Same pattern applies to Cursor's `.cursorrules`, Copilot's `.github/instructions/`, Codex's `AGENTS.md`.
- **Risk**: Very low.

#### Change 7 &mdash; Add `dotnet-ai audit --tokens` CLI command
- **What**: New CLI verb that walks all commands/skills/rules/agents and reports:
  - Token budget violations (SKILL.md > 500 lines, descriptions > 1024 chars, &gt; 3 always-on rules)
  - Eager Read patterns in commands that bypass progressive disclosure
  - Description quality issues (first/second person, missing trigger keywords)
  - Estimated per-command token cost
- **Files**: New `src/dotnet_ai_kit/audit.py`; registration in `cli.py`; tests in `tests/test_audit.py`.
- **Effort**: 1 day.
- **Why this matters**: Without measurement, regressions return. GitHub Spec-Kit ships exactly this pattern. Catches violations from contributors before merge.
- **Risk**: Very low.

#### Change 8 &mdash; Cache-friendly prompt ordering
- **What**: When commands assemble their prompt to Claude, put **stable static content first** (skill manifest, tool definitions, rules) and **dynamic input last** (user feature description, current task state). Tag last static block with `cache_control` to leverage Anthropic's 5-min prompt cache TTL.
- **Files**: Wherever commands assemble prompts; mostly affects longer commands and any prompt-building helpers.
- **Effort**: 4 hours.
- **Why this matters**: 5-min cache hits on iterative loops like `/dai.implement --resume` mean cached prefix tokens cost ~10% of normal. Compounds with Change 2 &mdash; small stable prefix = high cache hit rate.
- **Risk**: Low.
- **Depends on**: Phase 1 (prefix must be stable for caching to matter).

#### Change 9 &mdash; Subagent stubs for `/dai.do`, `/dai.implement`, `/dai.review`
- **What**: 3 longest commands become ~30-line router stubs that spawn a Task subagent with the verbose body as the subagent's system prompt. Subagent's verbose Reads stay isolated; only summary returns to main thread.
- **Files**: `commands/do.md`, `commands/implement.md`, `commands/review.md`, possibly `commands/analyze.md`, `commands/verify.md`.
- **Effort**: 1-2 days plus testing.
- **HARD GUARDRAILS** (the [887K tokens/min crisis](https://www.aicosts.ai/blog/claude-code-subagent-cost-explosion-887k-tokens-minute-crisis) &mdash; $47K bill in 3 days):
  - No upfront mass spawn &mdash; sequential per phase only
  - Never use subagents for `/dai.add-event`, `/dai.entity`, `/dai.spec` (small tasks &mdash; overhead exceeds savings)
  - Pass minimal context to subagent, not entire conversation
  - Idle termination after 15 minutes
- **Risk**: **Medium**. After Changes 1-6 land, may not be needed &mdash; measure first.
- **Multi-tool note**: Claude-Code-only (Task tool absent in Cursor/Copilot/Codex). Non-Claude projection of these commands stays unchanged.

#### Change 10 &mdash; Token-savior MCP integration
- See Part C below.

### B.4 Token cost progression

| Workload | Current | After P1 | After P2 | After P3 | + MCP |
|---|---|---|---|---|---|
| `/dai.add-event` (small) | 25K | 14K | 12K | 10K | 7K |
| `/dai.implement` (medium) | 90K | 35K | 31K | 18K | 9K |
| `/dai.do` (full lifecycle) | 200K | 75K | 68K | 30K | 22K |
| Cursor session always-loaded | 9K | 1K | 1K | 1K | 1K |
| $/dev/month (heavy use) | $250 | $105 | $80 | $55 | $40 |

### B.5 Performance dimensions per change

Score 1-5 (1 = regression, 3 = neutral, 5 = strong improvement):

| # | Change | Cost | Latency | Accuracy | Completeness | Cache |
|---|---|---|---|---|---|---|
| 1 | Descriptions | 4 | 4 | **5** | 3 | 4 |
| 2 | Strip Reads | **5** | **5** | 4 | 3 | **5** |
| 3 | Delete agent lists | 4 | 4 | 4 | 3 | 4 |
| 4 | Rule scoping | 4 | 3 | 3 | 3 | 3 |
| 5 | Skill &le; 500 | 3 | 3 | 4 | 3 | 3 |
| 6 | CLAUDE.md trim | 3 | 3 | 4 | 3 | 4 |
| 7 | Audit CLI | 3 | 3 | 3 | **5** | 3 |
| 8 | Caching | **5** | **5** | 3 | 3 | **5** |
| 9 | Subagents | 3 | **2** | 3 | **2** | 2 |
| 10 | Token-savior MCP | **5** | **5** | 4 | **5** | 3 |

**Eight of ten changes improve quality alongside cost. Only Change 9 carries genuine trade-offs.**

---

## Part C: MCP Integration Strategy

### C.1 The MCP overhead trap

Each connected MCP server can add up to 18,000 tokens per turn for tool definitions. Stacking MCPs naively makes things worse. Token-savior alone exposes 90 tools. Mitigation exists via selective tool-advertising profiles, but must be configured.

### C.2 Tool evaluation

| Tool | Verdict | Reasoning |
|---|---|---|
| **token-savior** ([mibayy/token-savior](https://github.com/mibayy/token-savior)) | **Strong fit** | MIT, MCP standard, multi-tool (Claude/Cursor/Cline/Continue/Aider/Zed/Windsurf). Symbol nav + persistent memory engine with 3-layer progressive disclosure (memory_index 15 tokens &rarr; memory_search 60 &rarr; memory_get 200). Benchmark: -77% tokens, -76% wall time. Per-type TTLs and content-hash invalidation match SDD lifecycle needs. |
| **Mem0** | Alternative | Easier setup (managed cloud) but adds vendor cost on top of Anthropic billing. Recommend as alternative for users who want managed solution. |
| **claude-mem** | Alternative | Zero-config UX. Auto-compresses sessions but adds Claude API cost for compression. Claude-Code-only. |
| **Serena** | Skip | Direct overlap with `csharp-ls` already in `.mcp.json`. Multi-language is unused value (tool is .NET-specific). [Active regression on Opus 4.7](https://github.com/oraios/serena/issues/802). |
| **token-optimizer-mcp** | Skip for now | New project; 95% claim unverified at scale; revisit when proven. |
| **MemCP, Memory Keeper, WhenMoon, doobidoo memory-service** | Skip | Lighter memory MCPs; token-savior dominates this category on benchmarks and feature scope. |

### C.3 Integration pattern

**Selected: Pattern 1 + Pattern 2** (opt-in CLI catalog plus conditional skill usage).

**Pattern 1: New CLI verb `dotnet-ai install-mcp <name>`**
- Add to `src/dotnet_ai_kit/cli.py` alongside existing `extension-add/remove/list`.
- Curated catalog: `token-savior` (recommended), `mem0` (managed alternative), `claude-mem` (zero-config alternative).
- Each install:
  1. Adds entry to user's `.mcp.json`
  2. Runs the `pip install` / setup command
  3. Drops a tuned profile config (selective tool advertising)
  4. Updates `.dotnet-ai-kit/mcps.json` tracking what's installed
- New file: `src/dotnet_ai_kit/mcp_catalog.py`
- Effort: 2 days.

**Pattern 2: Skills use these MCPs conditionally when available**
- Update workflow skills (e.g., `skills/workflow/sdd-lifecycle/SKILL.md`) to check tool availability:
  ```markdown
  If token-savior or mem0 MCP is available:
    - Save phase decisions: memory_save({type: "spec", feature: "001", content: ...})
    - Next phase loads via: memory_search({feature: "001"})
  Else:
    - Fall back to filesystem-only (current behavior)
  ```
- Existing users without MCPs see no change; opted-in users get savings.
- Effort: 1 day.

**Rejected: Pattern 3 (bundle by default in `dotnet-ai init`)**
- Adds Python pip dependency for users on .NET-only stacks
- Setup friction (venv, paths, env vars)
- One-off failure during init breaks tool's reputation
- Revisit when token-savior ships a binary distribution and profiles are battle-tested.

### C.4 MCP impact estimate

After token-savior added on top of Phase 1+2+3 changes:

| Workload | Without MCP | With token-savior memory | + symbol nav |
|---|---|---|---|
| `/dai.implement` (resuming feature) | 18K | 12K | 9K |
| `/dai.plan` (after spec) | 15K | 10K | 8K |
| Multi-repo brief lookup | 5K | 1K | same |
| `/dai.do` full lifecycle | 30K | 22K | 22K |

---

## Part D: Multi-Tool Portability Requirements

### D.1 Tool ecosystem

| Tool | Format | Auto-load mechanism | Constraint |
|---|---|---|---|
| Claude Code | SKILL.md | Description matching | &le; 500 line body |
| Cursor 2.0 | `.mdc` | `alwaysApply: true` OR `globs:` patterns OR agent-requested | Max 2-3 always-on, sweet spot 5-8 total |
| GitHub Copilot | `.github/instructions/*.md` | Path-scoped via `applyTo:` frontmatter | Brief instructions |
| Codex CLI | Single `AGENTS.md` | Always loaded | Must be small |
| Gemini CLI | Adopting SKILL.md | Description matching | Same as Claude |

### D.2 Per-change multi-tool impact

| Change | Claude Code | Cursor | Copilot | Codex | Gemini |
|---|---|---|---|---|---|
| 1. Descriptions | Yes | Yes | Yes | Yes | Yes |
| 2. Strip eager Reads | Yes | Yes | Yes | Yes | Yes |
| 3. Delete agent skill lists | Yes | N/A | N/A | N/A | N/A |
| 4. Rule scoping (globs) | Neutral | **Critical** | Yes | Yes | Yes |
| 5. Skill &le; 500 lines | Yes | Yes | Yes | Yes | Yes |
| 6. CLAUDE.md trim | Yes | Yes | Yes | Yes | Yes |
| 7. Audit CLI | Yes | Yes | Yes | Yes | Yes |
| 8. Caching ordering | Yes | No | No | No | No |
| 9. Subagent stubs | Yes | No | No | No | No |
| 10. Token-savior MCP | Yes | Yes | Yes | No | Yes |

### D.3 Architecture decision

**SKILL.md is canonical.** Skills are authored once in SKILL.md format. `src/dotnet_ai_kit/copier.py` projects to each tool's native format:
- **Claude**: copy as-is to `.claude/skills/`
- **Cursor**: convert to `.mdc`, add `globs:` from frontmatter, drop `alwaysApply` for non-essential rules
- **Copilot**: flatten to `.github/instructions/{name}.md` with `applyTo`
- **Codex**: bundle into single `AGENTS.md` with section headers
- **Gemini**: copy as-is (adopting SKILL.md standard)

Existing `AGENT_FRONTMATTER_MAP` at `src/dotnet_ai_kit/agents.py:63-81` covers agent frontmatter. Needs extension to handle skill-frontmatter projection rules per tool.

---

## Part E: Implementation Roadmap

### Week 1 &mdash; Foundation (3 days)

| Day | Tasks | Outcome |
|---|---|---|
| 1 | Multi-repo Fix #1 (bidirectional `repos:` propagation) + Token Change 4 (rule scoping) in parallel | Multi-repo: cross-feature origination unlocked. Cursor: 9K tokens saved per request. |
| 2 | Token Change 1 (description hygiene on 124 skills) | Dispatcher accuracy improved; Anthropic-style discovery enabled. |
| 3 | Token Change 2 (strip eager Reads from 27 commands) + Token Change 3 (delete agent skill lists) | 60-70% token reduction on heavy commands. |

**Phase 1 result**: ~70% reduction; Cursor v1.1-ready; cross-repo features work bidirectionally.

### Week 2 &mdash; Hygiene + tooling (3-4 days)

| Day | Tasks | Outcome |
|---|---|---|
| 4 | Token Change 7 (`dotnet-ai audit --tokens` CLI) | Regression baseline established. |
| 5 | Token Change 5 (verify SKILL.md &le; 500) + Token Change 6 (trim CLAUDE.md template) | Hygiene + portable templates. |
| 6 | Multi-repo Fix #2 (`dotnet-ai feature sync` CLI verb) | CI-callable brief regeneration. |
| 7 | Multi-repo Fix #3 (`feature_status.json` artifact) | Reverse status feedback. |

**Phase 2 result**: ~75% reduction; CI-friendly multi-repo; regression-proofed.

### Week 3 &mdash; Advanced (4-5 days)

| Day | Tasks | Outcome |
|---|---|---|
| 8 | Multi-repo Fix #4 (full re-detection on sibling init) + Multi-repo Fix #5 (`coordinated_branch_base`) | Multi-repo feature complete. |
| 9-10 | Token Change 10 (MCP catalog: install-mcp CLI + token-savior profile) | Opt-in MCP integration. |
| 11 | Token Change 8 (cache-friendly ordering) | Cache hit rate optimized. |
| 12-13 | Token Change 9 (subagent stubs) + measurement | 85-90% reduction matched against industry best (ClaudeFast 82%, Token Savior 77%). |

**Phase 3 result**: 85-90% reduction; full multi-repo; MCP-amplified.

---

## Part F: Decision Log

| ID | Decision | Rationale | Date |
|---|---|---|---|
| OPT-001 | Adopt SKILL.md as canonical format with per-tool projection | Industry standard (Anthropic + agensi.io); future-proofs v1.1 multi-tool support | 2026-05-09 |
| OPT-002 | Strip eager `Read skills/...` from commands; rely on Anthropic-native dispatcher | Anthropic best practices doc + Vercel data show description-based auto-load outperforms hand-prescribed loads | 2026-05-09 |
| OPT-003 | Defer Change 9 (subagents) to last | Medium risk; 887K tokens/min crisis precedent; may not be needed after P1+P2 | 2026-05-09 |
| OPT-004 | Add token-savior via opt-in CLI catalog, not bundled | Pip dependency friction; profile tuning needed; reputation risk on init failures | 2026-05-09 |
| OPT-005 | Skip Serena MCP | Redundant with `csharp-ls`; active Opus 4.7 regression | 2026-05-09 |
| OPT-006 | Build `dotnet-ai audit --tokens` CLI in Phase 2 | Regression prevention; matches Spec-Kit pattern; without measurement future skills will silently re-bloat | 2026-05-09 |
| OPT-007 | Cursor rules: 2 always-on max, 14 scoped via `globs:` | Cursor community guidance (2-3 always-on max, 5-8 sweet spot); v1.1 readiness | 2026-05-09 |
| OPT-008 | Multi-repo Fix #1 (bidirectional repos) is highest-priority gap | Smallest diff, biggest unlock; prerequisite for Fixes #2 and #4 | 2026-05-09 |
| OPT-009 | Original "linked-specs" gap memory file is stale; brief projection now works | Verified live at Anis.MeterCharger trio; feature 001 has projected briefs | 2026-05-09 |
| OPT-010 | Description hygiene (Change 1) is prerequisite for stripping eager Reads (Change 2) | Without good descriptions, dispatcher cannot auto-load; risk of missed-skill failures | 2026-05-09 |

---

## Part G: Risk Register

| Risk | Detection | Mitigation |
|---|---|---|
| Description rewrite breaks skill auto-trigger | Smoke test: ask Claude "add an event" and verify it picks `add-event` skill | Keep an A/B branch; revert frontmatter if accuracy drops |
| Stripped Reads cause missed-skill failures | After P1, sample 10 real `/dai.*` runs and check skill-load coverage | Add safety-net "If doing X, ensure Y skill is loaded" lines for critical paths |
| Subagent stubs (Change 9) explode costs | Set per-command token budget in `audit --tokens` | Don't ship Change 9 until Phase 1+2 measured |
| Cursor users hit `alwaysApply` regressions in v1.1 | Monitor v1.1 user reports | Tested via projection layer in `copier.py` before v1.1 GA |
| SKILL.md splits fragment workflows | Author review per skill before merging | Split on domain not size; one-level-deep references only |
| Multi-repo Fix #1 breaks existing primary configs | Existing primary `repos:` are read-only; only sibling configs are written | Idempotent write; only emits if reciprocal entry missing |
| MCP profile too aggressive removes needed tools | Per-MCP smoke test in `tests/test_mcp_catalog.py` | Profiles versioned alongside catalog; users can override |

---

## Part H: References

### Anthropic primary sources
- [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) &mdash; 500-line limit, description rules, progressive disclosure patterns
- [Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) &mdash; how skill discovery works
- [Prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) &mdash; cache_control, 5-min TTL, ordering rules
- [Subagents docs](https://code.claude.com/docs/en/sub-agents) &mdash; isolation semantics
- [Equipping agents with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

### Industry analysis
- [Stop Bloating CLAUDE.md - alexop.dev](https://alexop.dev/posts/stop-bloating-your-claude-md-progressive-disclosure-ai-coding-tools/) &mdash; Vercel data on skill miss rates
- [Subagent Cost Explosion - AICosts.ai](https://www.aicosts.ai/blog/claude-code-subagent-cost-explosion-887k-tokens-minute-crisis) &mdash; 887K/min crisis post-mortem
- [Claude Code Token: 10 Repos - Pasquale Pillitteri](https://pasqualepillitteri.it/en/news/1181/claude-code-token-10-github-repos-savings) &mdash; 30-92% benchmark range
- [5 Skills That Cut Token Costs 70% - MindStudio](https://www.mindstudio.ai/blog/5-claude-code-skills-cut-token-costs-70-percent-benchmarked)
- [MCP Server Token Overhead - MindStudio](https://www.mindstudio.ai/blog/claude-code-mcp-server-token-overhead) &mdash; 18K/turn definition cost
- [Claude Code Skills 2.0 A/B testing - Pasquale Pillitteri](https://pasqualepillitteri.it/en/news/341/claude-code-skills-2-0-evals-benchmarks-guide) &mdash; Anthropic's 5/6 trigger improvement
- [Claude Code Skills vs Cursor Rules vs Codex Skills - Agensi](https://www.agensi.io/learn/claude-code-skills-vs-cursor-rules-vs-codex-skills) &mdash; SKILL.md as cross-tool standard
- [Cursor alwaysApply forum thread](https://forum.cursor.com/t/q-rules-what-is-implication-of-alwaysapply/57826)

### Codebase audit (verified observations)
- `src/dotnet_ai_kit/copier.py:772-799` &mdash; `_update_sibling_config` (Multi-repo Gap #1)
- `src/dotnet_ai_kit/agents.py:63-81` &mdash; `AGENT_FRONTMATTER_MAP` (extension point for projection)
- `commands/implement.md` (235 lines, 17 skill refs, 7 agent refs &mdash; worst Change-2 offender)
- `commands/do.md`, `commands/specify.md:26-40`, `commands/tasks.md:191-197` &mdash; brief projection logic (verified working)
- `agents/dotnet-architect.md:21-38` &mdash; 18-skill `Skills Loaded` list (Change 3 target)
- `rules/*.md` &mdash; 16 files, all `alwaysApply: true` (Change 4 target)
- `.mcp.json` &mdash; csharp-ls only; integration point for MCP catalog
- Verified live: `Anis.MeterCharger.{Commands,Queries,Processor}` brief projection working for feature 001

### MCP candidate tools
- [mibayy/token-savior](https://github.com/mibayy/token-savior) &mdash; selected
- [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) &mdash; alternative
- [Mem0 Claude Code memory](https://mem0.ai/blog/claude-code-memory) &mdash; alternative (managed)
- [oraios/serena](https://github.com/oraios/serena) &mdash; rejected (redundant + Opus 4.7 regression)
- [ooples/token-optimizer-mcp](https://github.com/ooples/token-optimizer-mcp) &mdash; rejected (unproven)
- [github/spec-kit](https://github.com/github/spec-kit) &mdash; pattern source for audit CLI

### Reference plugins (comparable scope)
- [Aaronontheweb/dotnet-skills](https://github.com/Aaronontheweb/dotnet-skills) &mdash; 30 skills, 5 agents (smaller surface than dotnet-ai-kit's 124)
- [dotnet/skills](https://github.com/dotnet/skills) &mdash; official Microsoft, SKILL.md format
- [NeoLabHQ/context-engineering-kit](https://github.com/NeoLabHQ/context-engineering-kit) &mdash; multi-tool reference architecture (OpenCode/Cursor/Antigravity/Gemini)

---

## Appendix: Open Questions

1. **Skill consolidation**: Is 124 skills the right number? Aaronontheweb's plugin has 30; dotnet/skills similar. Discussed but deferred &mdash; product call, not token-burn call.
2. **Anthropic Issue [#14882](https://github.com/anthropics/claude-code/issues/14882)** (open, Dec 2025): `/context` shows skill bodies counting toward startup tokens, contradicting progressive disclosure spec. Watch for fix; until resolved, lean SKILL.md bodies are defense.
3. **Subagent decision**: Skip Change 9 if P1+P2 measurement shows acceptable burn? Decide after Phase 2 audit.
4. **Mem0 inclusion in catalog**: Adds vendor lock-in. Include only as documented alternative? Decide before shipping `install-mcp` catalog.
5. **`dotnet-ai feature sync` failure modes**: What happens when a sibling has uncommitted changes on the brief branch? Decide before Phase 2.
