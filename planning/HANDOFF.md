# Session Handoff — dotnet-ai-kit v2 rewrite (planning)

**Date:** 2026-05-31
**Focus this session:** Deep-scanned v1, researched the rewrite, and produced the complete v2 plan (full .NET 10 rewrite + re-authored artifacts). **No code written** — planning is complete and we are holding at the build boundary awaiting go-ahead.

---

## TL;DR — where we are
- The full v2 plan is written: **`planning/20`–`planning/26`**. **Start at [26](26-v2-build-plan-and-decisions.md) — it is authoritative** (overrides 20–25 where they differ).
- All major decisions are **locked**. Codex independently reviewed the plan (verdict: *proceed with changes*) and its accepted refinements are folded into 26.
- **Nothing built or branched.** Repo is on `fix/plugin-manifest-scalar-paths`; the only uncommitted items are untracked `planning/20–26` + `planning/HANDOFF.md` + `issues/`.
- **Next action = P0** (branch + .NET solution skeleton). The maintainer said "don't start directly," so this is **pending explicit go-ahead.**

## What this session produced
| Artifact | What it is |
|---|---|
| `planning/20-rewrite-strategy-net10.md` | keep-vs-rebuild strategy + the verified rule-enforcement bug (**superseded** by the full-rewrite decision) |
| `planning/21-v2-architecture-blueprint.md` | v2 architecture (.NET 10 clean/hexagonal, single-source → per-host projection, the stack) |
| `planning/22-v2-project-structure.md` | repo/solution layout + per-class responsibilities |
| `planning/23-v2-artifact-catalog.md` | every artifact: 32 commands, 15 agents, 21 rules, 12 profiles, ~160 skills (with previews) |
| `planning/24-v2-selector-gates-lifecycle-multirepo.md` | selector brain · enforcement gates · token economy · SDD completeness · multi-repo (amended by 26) |
| `planning/25-v2-requirements.md` | testable FR/NFR/SC baseline (amended by 26) |
| **`planning/26-v2-build-plan-and-decisions.md`** | **AUTHORITATIVE: locked decisions + adopted refinements + 11-phase execution plan** |
| `issues/v2-design-review/CODEX-REVIEW-PROMPT.md` | the adversarial review prompt given to Codex |
| `issues/v2-design-review/CODEX-FINDINGS.md` | Codex's review (PROCEED WITH CHANGES; confirmed all factual claims) |

## Locked decisions (see 26 §2–§3 for detail)
- **Full rewrite now** — v1 was never released, so there's no migration/hotfix concern (this moots Codex's main objection).
- **BD-1** new branch off current HEAD; keep Python `src/dotnet_ai_kit/` + `tests/` as the runnable reference until the .NET passes the contract suite, then remove.
- **BD-2** scope = everything (engine + all 4 hosts + full rebuild + ~30 new artifacts), built in dependency order.
- **BD-3** distribution: framework-dependent `dotnet tool` first; Native AOT deferred until trim-clean.
- **Codex refinements AR-1…10 adopted:** license-light generated code by default · host-capability matrix + per-host smoke tests · hard enforcement tiers (PreToolUse-deny, Stop-hook) Claude-scoped with per-host fallbacks · neutral artifact model · opt-in per-skill resources · selector oracle on ambiguous clusters first · new FR areas (script trust/security, user-file merge policy, schema versioning, release/rollback, Windows parity) · no over-abstraction.

## Verified facts (don't re-litigate; re-confirm exact versions at implementation time)
- **Rule-delivery bug CONFIRMED** (by me and Codex): `copy_rules` only in the dead `else` branch (`src/dotnet_ai_kit/cli.py` ~1281–1334) + `ClaudeHost.write_per_solution_files` writes only `.claude/settings.json` (`src/dotnet_ai_kit/hosts/claude.py:110-130`) → plugin-native Claude never receives domain rules. This is the central thing v2's enforcement layer fixes; corroborated by `issues/rule-enforcement-gap/`.
- **.NET stack:** System.CommandLine **2.0.8** stable (`SetAction`; `System.CommandLine.Hosting` deprecated) · **Spectre.Console** for output (never `Spectre.Console.Cli` — AOT-hostile) · **YamlDotNet + static generator** for AOT YAML (spike whether needed) · **Microsoft.Extensions.AI GA 10.6.0** · **Verify** for golden-output tests.
- **Claude Code:** commands merged into skills (official); hooks can **deny** (PreToolUse) and **block completion** (Stop/SubagentStop) + inject `additionalContext`; `disable-model-invocation` makes a skill a slash-only command off the budget.
- **Cross-tool:** one `.claude-plugin/plugin.json` serves Claude Code + Copilot CLI + VS Code Copilot (Copilot *cloud* agent stays render-only). `.agents/skills/` is read by Cursor/Codex/Copilot but treat as a non-load-bearing optimization.
- **Licensing:** MediatR / AutoMapper / MassTransit are now commercial → license-light defaults + dispatch/mapping behind ports.

## Environment / gotchas
- Windows; PowerShell is primary (Bash also available). **.NET 10 SDK 10.0.300 installed** (also a 5.0.408).
- No `.sln`/`.slnx`, no root `Directory.Build.props`/`Directory.Packages.props`/`global.json` yet.
- Persistent memory: `project-v2-dotnet10-rewrite.md` (auto-loaded) + `project_multi_repo_linked_specs_gap.md` (the multi-repo awareness gap v2 §FR-G closes).

## Next action — P0 (on maintainer go-ahead)
Create the rewrite branch + `dotnet-ai-kit.slnx` + 6 projects (`DotnetAiKit.Core/Application/Hosts/Infrastructure/Cli` + `DotnetAiKit.Analyzers`) + test projects + `Directory.Build.props`/`Directory.Packages.props` + `global.json` (pin 10.0.300) + `.editorconfig` + CI skeleton + the `artifacts/` directory tree. **Acceptance:** the empty solution builds and CI is green. Then **P1 (Core domain)** per [26 §5](26-v2-build-plan-and-decisions.md).

## Pending maintainer input
- **Approval to start P0** (currently holding per "don't start directly").
- (Minor, defaultable) naming: namespace root `DotnetAiKit`, tool command `dotnet-ai`, analyzer package `Dotnet.Ai.Kit.Analyzers`, target `net10.0`, solution `dotnet-ai-kit.slnx` — confirm or override.

## Learnings worth carrying
- The v1 mess is **artifact drift + unenforced rules**, not the CLI language — the single-source→projection + deterministic enforcement is the real fix.
- Skills ≠ tools: the selector is description-engineering + a graph + a thin disambiguator, **not** a runtime router.
- "Quality is cheapest when deterministic" — push verification to hooks/analyzers/build-test (zero model tokens), keep the model's context to model-work.
