# dotnet-ai-kit v2 — Selector Brain, Enforcement Gates, Token Economy, SDD Completeness & Multi-Repo

**Date:** 2026-05-30 · **Extends:** [21](21-v2-architecture-blueprint.md) · [22](22-v2-project-structure.md) · [23](23-v2-artifact-catalog.md)
**Grounding:** Claude Code hooks reference (fetched 2026-05-30), the v1 multi-repo design ([planning/08](08-multi-repo-orchestration.md)), handoff schemas ([planning/13](13-handoff-schemas.md)), the `verification-gate` skill, and the `verify` command — all read this session.

> ⚠️ **Amended by [26](26-v2-build-plan-and-decisions.md) (authoritative).** Post-Codex-review changes that override this doc where they differ: command count is **32** (the `fix` command is **in**, not "consider"); the cycle is `… verify → fix → pr → release`; the hard enforcement tiers (T2 PreToolUse-deny, T4 Stop-hook) are **Claude-scoped** with per-host fallbacks (analyzer/CI/`/verify`/host-native rules). See 26 §3–§4.

This doc records **decisions** for the five areas the maintainer flagged: the skill-selector brain, rule-forcing + verification gates, guaranteeing good output without token burn, SDD cycle completeness, and multi-repo.

---

## 1. The skill-selector "brain"

**Decision: the selector is _distributed and compile-time_, not a runtime router.** (Per the routing research: skills ≠ tools; a heavy router is an anti-pattern.) The "brain" is five cheap, layered mechanisms:

| Layer | Mechanism | Token cost | Built from |
|---|---|---|---|
| **L1 Listing** | Tier-1 `description` of model-invocable skills (always-on, ~1% budget) | low, fixed | the **description standard** (action-first · "Use when" · "Do NOT use… use X") |
| **L2 Graph** | The generated `ArtifactGraph` (owns/relates/triggers/confusion-pair edges) drives disambiguation *written into* descriptions + an agent's `skills:` preload | **zero at runtime** (build-time) | frontmatter (`metadata.agent`, "Related Skills", agent `## Routing`) |
| **L3 Scope** | `paths:` globs → domain rules + location-specific skills load **only when a matching file is touched** | zero until in-scope | rule/skill frontmatter |
| **L4 Disambiguator** | `/dai.do` carries a curated decision table for genuinely ambiguous clusters (`add-entity`/`add-aggregate`/`add-crud`) — **guidance, not a gate** | tiny, opt-in | the graph's confusion edges |
| **L5 Context injection** | PreToolUse hook injects the right **profile/rule body** when a matching file is edited (the enforcement-context selector) | zero (hook, not model) | profiles + domain rules |

**What makes it reliable + cheap:** every description is gated by the **triggering eval harness** (20 queries/skill, 60/40 split, 3× runs) + a **cross-skill confusion matrix** (the correct skill fires, siblings stay silent) — so "the right skill loads" is a CI metric, not a hope. Commands are `disable-model-invocation` (off the listing budget entirely). Consolidating the duplicate skills (§ catalog) reclaims listing slots so the budget never overflows and silently drops descriptions.

**Explicitly rejected:** a centralized router/dispatcher MCP over the 124 skills (re-implements progressive disclosure, adds a hop + a sync target + a single point of failure). A retrieval MCP is reserved for *MCP tools* only, and only past ~30–50 tools.

---

## 2. Rule-forcing + verification gates

**Decision: four enforcement tiers, escalating from advisory to hard-blocking — each grounded in a verified mechanism.**

| Tier | Mechanism | Blocks? | Token cost | Fixes |
|---|---|---|---|---|
| **T1 Advisory (in-context)** | Rules/profiles delivered to `.claude/rules/*.md` (`paths:`) + **PreToolUse `additionalContext`** injecting the active profile/rule when a matching file is edited | no (guides) | low (JIT) | the v1 rule-delivery bug ([cli.py:1334](src/dotnet_ai_kit/cli.py)) |
| **T2 Interceptive (pre-write)** | **PreToolUse `permissionDecision: deny`** on hard violations (forbidden path, banned API). Fast `command` hook for mechanical checks; `prompt` (Haiku) for judgment (v1 already does this) | **yes — before the edit** | ~0 model (hook) | violations reaching disk |
| **T3 Deterministic (build)** | The **`Dotnet.Ai.Kit.Analyzers`** Roslyn NuGet → violations are build errors (`.editorconfig` severity=error) | **yes — compile fails** | **zero model** | "advisory enforcement" (v1 NetArchTest never run) |
| **T4 Completion gate** | A **Stop / SubagentStop hook** (`decision: block`) runs `dotnet build` + `dotnet test` (+ format) when the agent tries to finish; blocks "done" and feeds failures back until green | **yes — blocks completion** | zero model | the model claiming success without proof |

**The verification gate = T4 + the `verification-gate` skill + `/verify` + `/review`:**
- The **`verification-gate` skill** is the *advisory discipline* ("NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE"; verify a subagent's report yourself). **The Stop hook is its deterministic backstop** — even if the model ignores the discipline, the hook won't let it stop on a red build.
- **`/verify`** is the explicit, user-driven gate (build/test/format + mode-adaptive proto/resource/k8s checks, per repo).
- **`/review`** is the standards gate (+ optional CodeRabbit).
- **`SubagentStop`** applies the same gate to delegated subagents, so "after agent delegation, verify yourself" is enforced mechanically.

**Decision — keep the v1 PreToolUse Haiku hook but make it deterministic-first:** mechanical rules (layering, banned APIs, private setters) move to the Roslyn analyzer (T3, free + exact); the Haiku `prompt` hook (T2) is reserved for judgment calls the analyzer can't make. This cuts per-edit model cost while raising precision.

---

## 3. Guaranteeing good output without burning tokens

**Decision — the governing principle: _quality is cheapest when it's deterministic._** Push verification to mechanisms that cost **zero model tokens**; reserve the model for what only a model can do (design, codegen, judgment).

**The economy levers (each ties to a section above):**

1. **Deterministic gates over model reasoning** — build, tests, analyzers, and the Stop hook (§2 T3/T4) verify correctness without consuming context. A failing test is caught by a shell, not by spending tokens asking the model "are you sure?"
2. **Progressive disclosure** — only Tier-1 descriptions are always-on; `SKILL.md` bodies (≤500 lines) + `references/`/`scripts/` load on use; scripts are *executed*, never loaded.
3. **JIT path-scoping** — rules/skills/profiles load only when an in-scope file is touched (§1 L3/L5).
4. **Sub-agent context isolation** — `/verify`, `/review`, `/analyze`, docs, and multi-repo per-repo work run in **forked subagents** (`context: fork` / the Agent tool) that return a *tight* result (pass/fail + failures only), not their whole transcript. The main thread stays lean; the expensive reading happens in a disposable context.
5. **Selector precision** (§1) — load the *right* skill, not all of them.
6. **MCP Tool Search / deferral** — `codebase-memory-mcp` (and any future tool server) defer their schemas until needed, preserving the cached prompt prefix.
7. **Commands off-budget** — `disable-model-invocation` removes all 27+ command descriptions from the always-on listing.
8. **Measurement as governance** — `/context` + a `TiktokenTokenizer` budget check in `dotnet-ai check` is the canonical always-on metric (replacing v1's line-count proxy); the triggering eval harness proves the lean descriptions still fire. CI fails if the budget regresses or triggering accuracy drops.

**Net:** correctness is guaranteed by deterministic gates (free); context stays small because everything loads JIT, in isolation, or not at all. High quality and low burn are not in tension — they're achieved by the *same* move: keep the model's context to model-work and let shells/analyzers/hooks do the rest.

---

## 4. SDD lifecycle completeness — commands to add

**Decision — the v1 27 commands cover specify→PR well but miss the bookends and the multi-repo conductor.** Measured against a complete spec-driven cycle (and the spec-kit reference: constitution/specify/clarify/plan/tasks/analyze/checklist/implement/taskstoissues), add **4 commands + 1 flag**, and consider 1 more.

| New command | Alias | Fills the gap | Notes |
|---|---|---|---|
| **constitution** | `/dai.const` | Establish/update the project's governing principles (the rules the whole cycle obeys) | v1's `learn` does constitution+topic-split; **split** it: `learn` = extract project knowledge, `constitution` = author/amend governing principles. The constitution gates `analyze`/`review`. |
| **checklist** | `/dai.check?` | Generate a feature-specific quality checklist as an explicit gate before implement and before PR | v1 embeds a static checklist in `spec.md`; this generates a *custom* one from the spec and runs it. (Alias TBD — `check` is taken by `analyze`.) |
| **orchestrate** | `/dai.orch` | **The multi-repo conductor** (see §5): propagate the feature to all affected repos, init them, sequence implementation by dependency, report cross-repo status | The single biggest gap; today multi-repo is implicit inside `do`/`implement`. |
| **release** | `/dai.release` | Close-out after PR merge: version bump + changelog + tag + GitHub release (+ optional deploy hook) | `docs release` writes notes but nothing orchestrates the release. |
| **tasks `--issues`** | — | Convert `tasks.md` into linked GitHub issues (spec-kit `taskstoissues`) | A **flag on `tasks`**, not a new command — keeps the surface lean. |
| *(consider)* **fix** | `/dai.fix` | Targeted bug-fix loop: reproduce (failing test) → fix → verify | Medium value; `do`/`implement` partly cover it. Decide later. |

**The complete v2 cycle:**
```
constitution → specify → clarify → checklist → plan → tasks(→issues) → analyze
   → orchestrate (multi-repo) → implement → review → verify → pr → release
        ↑ status / undo / checkpoint / wrap-up available at any point ↑
```
This brings the command count to **31** (27 + constitution, checklist, orchestrate, release). All new commands are command-skills (`disable-model-invocation`, slash-only, off-budget) per [§23](23-v2-artifact-catalog.md).

---

## 5. Multi-repo features

**Decision — make multi-repo coordination first-class and fix the awareness gap.** The v1 design ([planning/08](08-multi-repo-orchestration.md)) has the right bones (workspace model, dependency order, `feature-brief.md`, `deploy_to_linked_repos`) but two confirmed failures: (a) secondary repos that lack `.dotnet-ai-kit/project.yml` → the enforcement hook silently no-ops there (report #1's live finding on the Circle project); (b) feature awareness doesn't reliably reach every affected repo ([memory: multi-repo linked-specs gap](#)).

**The v2 multi-repo system (owned by the new `orchestrate` command + the microservice agents):**

| # | Mechanism | What it guarantees |
|---|---|---|
| 1 | **Init every affected repo** — `orchestrate` (and `init --include-linked`) writes `.dotnet-ai-kit/project.yml` + tooling + the PreToolUse hook into *each* secondary repo | enforcement actually fires everywhere (closes report #1's no-op gap) |
| 2 | **`feature-brief.md` to every affected repo** — `specify`/`orchestrate` projects the feature (role, required changes, events consumed/produced) into each repo's `.dotnet-ai-kit/features/NNN/` | every repo is *aware* of the cross-repo feature (closes the linked-specs gap) |
| 3 | **Dependency-ordered execution** — Command → Query/Processor → Gateway → ControlPanel; `--resume` from the failed task; feature branches isolate until PR merge | correct order, safe partial-failure recovery |
| 4 | **Cross-repo contract consistency** — `analyze` validates the event catalogue across repos (producer/consumer match, proto client↔server, sequence/idempotency) | events/protos stay consistent across services |
| 5 | **Linked PRs** — `pr` creates a PR per repo with a cross-referenced "Related PRs" block | reviewers see the whole feature |
| 6 | **Cross-repo status** — `status` reads each repo's `linked_from` + `feature-brief.phase` | one view of multi-repo progress |
| 7 | **Branch safety** — secondary repos on main → create `chore/feature/NNN`; dirty → warn + skip | never clobbers secondary working trees |
| 8 | **Worktree isolation (optional)** — parallel per-repo work via git worktrees (the `git-worktree-isolation` skill / Agent `isolation: worktree`) | safe parallelism when desired |
| 9 | **Subagent fan-out (opt-in, not default)** — `orchestrate` *may* delegate per-repo implementation to subagents for parallelism; default is sequential, dependency-ordered | scale without a hard dependency on preview orchestration |

**Decision on awareness (the memory gap):** the `feature-brief.md` projection (#2) + init-every-repo (#1) is the fix — but it must be **enforced by a contract test** (an acceptance test asserting that after `specify`/`orchestrate`, every repo in the service-map has a `feature-brief.md` with the matching `feature_id`). Otherwise it silently regresses again. This pairs with `analyze`'s cross-repo consistency pass.

---

## 6. Decisions summary & doc deltas

**Decided this round:**
- **Selector** = distributed, compile-time (L1 descriptions + L2 graph + L3 paths + L4 thin `/dai.do` disambiguator + L5 PreToolUse context); eval-harness-gated. No runtime router.
- **Enforcement** = 4 tiers (advisory context → PreToolUse deny → Roslyn analyzer build-error → **Stop-hook completion gate**). The Stop hook is the new deterministic backstop for the verification-gate discipline.
- **Token economy** = "quality is cheapest when deterministic" — deterministic gates + progressive disclosure + sub-agent isolation + JIT scoping + measurement; high quality and low burn from the same move.
- **SDD** = add `constitution`, `checklist`, `orchestrate`, `release` (+ `tasks --issues`; consider `fix`) → 31 commands; the cycle is complete bookend-to-bookend.
- **Multi-repo** = init-every-repo + feature-brief-to-every-repo + dependency order + cross-repo `analyze` + linked PRs + cross-repo status, with a **contract test** guaranteeing awareness.

**Deltas to apply to the other docs:**
- **[23 catalog](23-v2-artifact-catalog.md):** add the 4 new commands; add new workflow/quality skills if any (e.g. a `multi-repo-orchestration` skill for `orchestrate`).
- **[22 structure](22-v2-project-structure.md):** the Stop-hook gate + the `agent`/`prompt` PreToolUse hooks live under each host's projected `hooks/`; `orchestrate` is an Application use-case (`OrchestrateService`) coordinating `IGitClient` + `IHostAdapter` across repos.
- **[21 blueprint](21-v2-architecture-blueprint.md):** §6 enforcement now names the 4 tiers explicitly.

**Open questions:**
1. `constitution` as a new command vs. extending `learn` — split recommended; confirm.
2. `fix` command — add now or defer to a `fix` *skill*?
3. `orchestrate` default execution — sequential (safe) vs. subagent fan-out (fast) as the default for large features?
4. Stop-hook gate — always-on, or opt-in per permission profile (it adds a build+test on every "stop", which is slow for tiny edits — likely scope it to feature work, not every turn)?

**Verification status:** hook capabilities (block/deny/additionalContext/Stop-block, handler types) verified against [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks) (2026-05-30); multi-repo mechanics from v1 internal docs (planning/08, 13) read this session; spec-kit lifecycle reference from the available speckit.* skills. The `fix`/`orchestrate`-default/Stop-hook-scope choices are open (above), not asserted.
