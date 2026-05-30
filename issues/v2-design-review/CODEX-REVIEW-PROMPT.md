# v2 Design Review — Codex Review Request

## For the maintainer (context — read first)

Over several sessions, Claude produced a complete **v2 rewrite plan** for `dotnet-ai-kit`: a full re-platform of the CLI from **Python → .NET 10** plus a re-authoring of every artifact (skills, agents, rules, profiles, commands). The plan lives in six planning docs:

| Doc | What it claims |
|---|---|
| `planning/20-rewrite-strategy-net10.md` | keep-vs-rebuild strategy + evidence (now *superseded* by the full-rewrite decision) |
| `planning/21-v2-architecture-blueprint.md` | the architecture: skill-as-atomic-unit, single-source→per-host projection, .NET 10 stack |
| `planning/22-v2-project-structure.md` | concrete repo/solution layout + per-class responsibilities |
| `planning/23-v2-artifact-catalog.md` | every artifact (32 commands, 15 agents, 21 rules, 12 profiles, ~160 skills) |
| `planning/24-v2-selector-gates-lifecycle-multirepo.md` | the skill-selector model, 4-tier enforcement + verification gates, token economy, SDD additions, multi-repo |
| `planning/25-v2-requirements.md` | the testable FR/NFR requirements baseline |

**How to use this file:** from the repo root, launch OpenAI Codex CLI and give it the prompt in the next section — e.g. paste it, or say *"Read `issues/v2-design-review/CODEX-REVIEW-PROMPT.md` and carry out the review it describes."* Codex needs repo read access and, ideally, web access to verify external claims.

**Why a second reviewer:** the plan was written by Claude and labels many claims "verified." The highest-value review **re-verifies those claims independently** and hunts for flaws, gaps, and over-engineering — not a rubber stamp.

---

## === PROMPT FOR CODEX (give this to Codex) ===

You are a **senior .NET architect and adversarial design reviewer**. Your job is to critically review a v2 rewrite plan for an open-source tool called `dotnet-ai-kit` and find what is **wrong, weak, stale, contradictory, over-engineered, or missing**. Do **not** be agreeable or summarize approvingly — assume the plan has flaws and find them. Be specific and cite evidence.

### Background
`dotnet-ai-kit` is currently a **Python** CLI (`src/dotnet_ai_kit/`) that ships AI-assistant artifacts (skills/agents/rules/commands) to four AI coding tools: **Claude Code, OpenAI Codex CLI, Cursor, and GitHub Copilot**. The maintainer has decided on a **full rewrite to .NET 10** plus re-authoring all artifacts. The rewrite plan is in `planning/20`–`planning/25` (see the table at the top of this file). Today's date is **2026-05-30**. The repo on disk is still the Python v1 — the plan treats v1 + its ~717 tests as the *reference spec*, not the starting code.

### What to do

**1. Independently verify the load-bearing claims** — do NOT trust the plan's "verified" labels. For each, read the actual code and/or check primary sources (official docs, NuGet), and mark **CONFIRMED / REFUTED / UNCERTAIN** with the evidence you found:
   - **The rule-delivery bug** (the linchpin of `planning/20` §4.4 and the `planning/24`/`25` enforcement fix): open `src/dotnet_ai_kit/cli.py` around lines 1280–1350 and `src/dotnet_ai_kit/hosts/claude.py`. Is it true that for a *plugin-native Claude* install, `copy_rules(...)` only runs in a dead `else` branch (so domain rules are never written to `.claude/rules/`), and that `ClaudeHost.write_per_solution_files` writes only `settings.json`? Cross-check `issues/rule-enforcement-gap/` (the maintainer's own field report).
   - **The command-duplication / agent-drift claims**: `grep -r "Bounded skill selection (FR-012)" commands/` (plan says 17/27); compare `agents-source/`, `agents-claude/`, and `.claude-plugin/plugin.json` agent counts (plan says 14/13/13).
   - **The .NET 10 stack currency** (`planning/21` §5.2, `planning/25` FR-C): is **System.CommandLine 2.0.8** really the current *stable* (vs a 3.0 preview)? Is `Spectre.Console.Cli` actually AOT-hostile (`RequiresDynamicCode`)? Is the YamlDotNet-needs-a-static-generator-for-AOT claim correct? Is **Microsoft.Extensions.AI** GA? Verify versions against nuget.org / learn.microsoft.com.
   - **Licensing claims** (`planning/23`/`24`/`25` FR-H2): are **MediatR**, **AutoMapper**, and **MassTransit v9** really now commercial, and are the "free" escape hatches (MediatR <13, Mediator by Martin Othamar, Wolverine) accurate?
   - **Cross-tool platform claims**: is "**custom commands have been merged into skills**" official Claude Code behavior? Does **GitHub Copilot / VS Code really auto-detect `.claude-plugin/plugin.json`** (one repo serving three tools)? Is `.agents/skills/` really read by Cursor + Codex + Copilot? Are the **hook capabilities** (PreToolUse `deny`, Stop-hook `decision: block`, `additionalContext`) accurate? Check code.claude.com/docs, developers.openai.com/codex, cursor docs, code.visualstudio.com.

**2. Critique the architecture** (`planning/21`, `22`): Is clean/hexagonal layering (`Core/Application/Hosts/Infrastructure/Cli/Analyzers`) appropriate and not over-engineered for a CLI of this size? Is the **single-source → per-host projection** engine sound, and does the `IHostAdapter` model actually fit each tool's real capabilities? Is **"skill = the only resource-bearing unit; agents/commands reference skills"** correct for all four tools, or does it break somewhere? Is the AOT/distribution plan realistic (per-RID Native AOT, cross-OS build constraints)?

**3. Critique the intelligence / selector model** (`planning/24` §1): Is "**no runtime router — description engineering + the artifact graph + a thin `/dai.do` disambiguator**" the right call at ~160 skills, or will selection degrade? Is the ~1% always-on listing budget reasoning correct? What are the failure modes?

**4. Critique enforcement + token economy** (`planning/24` §2–3): Are the **4 enforcement tiers** (advisory context → PreToolUse `deny` → Roslyn analyzer build-error → **Stop-hook completion gate**) sound and safe? Is the Stop-hook gate practical (performance, false blocks, portability — do Codex/Cursor/Copilot even have an equivalent)? Is **"quality is cheapest when deterministic"** actually achievable, or hand-wavy? Where could it backfire?

**5. Critique SDD completeness + multi-repo** (`planning/24` §4–5, `planning/25` FR-D/FR-G): Are the **32 commands** the right set — any redundant, missing, or mis-scoped? Is splitting `learn`→`constitution` worth it? Does the multi-repo design (`orchestrate`: init every repo + project `feature-brief.md` to every repo + dependency-order + cross-repo `analyze` + a contract test) actually close the two stated gaps (secondary-repo enforcement no-op; cross-repo feature awareness)? Find holes in cross-repo event-contract consistency.

**6. Cross-document consistency**: Find contradictions, stale numbers, or claims in one doc undercut by another across `planning/20`–`25`.

**7. Risks & sequencing**: Is the phased roadmap (`planning/21` §10) realistic? What are the top risks to this rewrite succeeding, and what would you do differently? Is anything a likely waste of effort?

### Output format
Produce a Markdown review with:
- **Verdict**: one of `PROCEED` / `PROCEED WITH CHANGES` / `RECONSIDER`, with a 3–5 sentence rationale.
- **Claim verification table**: each load-bearing claim → CONFIRMED / REFUTED / UNCERTAIN → evidence (file:line, doc, or dated source URL).
- **Findings by severity** (Critical / High / Medium / Low): each with a `planning/NN §X` or `file:line` reference and a concrete recommended fix.
- **Gaps / missing requirements**.
- **Over-engineering / things to cut**.
- **Top 5 risks** + mitigations.

### Rules of engagement
- Be adversarial and **evidence-based**; prefer primary, dated sources. If you can't verify a claim, mark it **UNCERTAIN** — never assert.
- Cite `planning/NN` (and section) or `path:line` for every finding.
- Distinguish "the plan is wrong" from "I couldn't confirm it."
- It is more useful to surface 5 real problems than to praise 20 good decisions. If the plan is genuinely sound in an area, say so briefly and move on.
- Write the review to `issues/v2-design-review/CODEX-FINDINGS.md`.

## === END PROMPT ===
