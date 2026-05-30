# Why dotnet-ai-kit didn't enforce its rules in Circle feature 001 — diagnosis & fix

**Date:** 2026-05-29
**Scope:** `Ecom-LTD/Circle` feature `001-location-based-transfer-fees`, focused on `Anis.TheCircle.Command` and `Anis.TheCircle.Query`, used with **dotnet-ai-kit installed as a Claude Code plugin** (no agents/rules/skills copied into the project dir).
**Author of kit:** Faysil Alshareef (this report is written for the kit author — recommendations target *kit changes*, with an immediate per-repo workaround).

---

## TL;DR

The kit's rules were **never in the model's context** while it wrote the Query side. This is mechanical, not the model "ignoring" guidance:

1. **Claude Code plugins have no always-on "rules" primitive.** Per the official docs, a plugin-root `CLAUDE.md` is *not* loaded, and the plugin manifest has no `rules` field — "plugins contribute context through skills, agents, and hooks rather than CLAUDE.md." The only plugin-native way to force rule **bodies** into context is a **hook** that emits `hookSpecificOutput.additionalContext`. ([plugins-reference], [memory])
2. **The kit's only body-injecting hook is the PreToolUse arch-profile hook**, and it injects only the **architecture profile** — and only when `.dotnet-ai-kit/project.yml` exists *relative to the working directory*. The universal `rules/conventions/*` are passed as a **filename pointer**, not text. SessionStart injects **no** rule bodies (it's capped at ~500 tokens by design).
3. **Only the `Command` project had `project.yml`.** `Query` and `Processor` were never `dotnet-ai init`-ed — they received only `briefs/` from the multi-repo brief projection. So when the Query code was written, the arch-profile hook hit `Project metadata not initialized; exit 0` and injected **nothing**. The strongly-worded rules in `profiles/microservice/query-sql.md` (private setters, exact sequence guard, gap tests) were physically absent from context → your Q1–Q6 review findings.
4. **Even when rules *are* injected, they're advisory** (`exit 0`, never blocks) and prompt-time rules are non-deterministic. The kit ships the *perfect* deterministic gate — a NetArchTest named `Entities_ShouldHave_PrivateSetters()` in `skills/quality/architectural-fitness/SKILL.md` — but only as an **on-demand skill** that's never generated or run by default. Your human review (`/review` + `/verify`) was the only enforcement layer.

**The fix, in one line:** make the universal conventions *resident* (inject bodies via SessionStart/UserPromptSubmit hooks), close the per-project metadata gap so domain profiles actually fire, and add **deterministic gates** (ship + run the NetArchTest + a `severity=error` `.editorconfig`) so a public setter *fails the build* regardless of what the model remembered.

---

## Part 1 — What actually happened in Circle feature 001

### 1.1 The asymmetry (the key evidence)

| Project | `.dotnet-ai-kit/project.yml` | What the arch-profile hook injected | Outcome |
|---|---|---|---|
| `Anis.TheCircle.Command` | ✅ present (`mode: microservice`, `project_type: command`) | `profiles/microservice/command.md` — *"ALWAYS use private setters on aggregate state — NEVER expose public setters"* | command-side aggregates (`Transfer`, `Exchange`) came out **compliant** |
| `Anis.TheCircle.Query` | ❌ **missing** (dir contains only `briefs/`) | **nothing** — hook exits at `Project metadata not initialized` | `Region.cs` public setters, permissive `>=` sequence checks, weak tests |
| `anis.the-circle-processor` | ❌ **missing** (only `briefs/`) | **nothing** | same exposure |

> **Reading the table honestly:** the arch-profile hook injects `command.md` *only* when Claude is launched in that project dir with the plugin's hooks active — so the Command row shows the **designed** behavior given the project's metadata, not a forensic replay of the session. The **load-bearing, verified fact is the Query/Processor row**: no `project.yml` → nothing injected. Command-side compliance is *consistent with* the injected profile but equally attributable to the model's strong event-sourcing priors (its own `CLAUDE.md` doesn't state the rule either — see §1.4).

> Verified directly: `Circle/Anis.TheCircle.Query/.dotnet-ai-kit/` exists but contains only `briefs/` — no `project.yml`. `Circle/Anis.TheCircle.Command/.dotnet-ai-kit/project.yml` exists with `project_type: command`. The solution root `Circle/` has no `.dotnet-ai-kit/` at all, and `.claude/settings.local.json` is `{"enabledPlugins": {}}` (the plugin is enabled at the user level, not per-project).

### 1.2 The violations you fixed in review/verify were real

From the feature's own `review.md`, all of these were AI-generated then corrected by you:

- **Q1 (HIGH):** `Region` entity had **public setters** — violates the private-setter + behavior-method convention.
- **Q2 (HIGH):** Read-model handlers used permissive `entity.Sequence >= request.Sequence` instead of the strict guard `entity.Sequence == request.Sequence - 1` (gap-tolerant idempotency bug).
- **Q3 (MEDIUM):** Handler tests didn't assert sequence behavior / gap cases.
- **Q4–Q6 (HIGH):** pricing-precision, dimensional-consistency, and a dropped `LocationId` on the consumer endpoint.
- **C1/C2 (Command side):** duplicate-fee validation + weak assertions.

The command side was *mostly* clean; the query/processor side carried the encapsulation and idempotency violations — exactly the projects with **no injected rules**.

### 1.3 The rule existed and was strongly worded — it just wasn't loaded

`profiles/microservice/query-sql.md` already says, verbatim:

```
- ALWAYS use `{ get; private set; }` on every property — NEVER expose public setters
- MUST use private constructor with ALL parameters for EF Core materialization — NEVER parameterless
...
// THE ONLY CORRECT SEQUENCE GUARD — use this exact pattern:
if (entity.Sequence != @event.Sequence - 1)
    return entity.Sequence >= @event.Sequence;
```

This is precisely what was violated. The rule was never the problem; **rule delivery** was.

### 1.4 The discriminator: was the rule anywhere the model could see it?

To rule out "the model saw it and ignored it," I checked the one file Claude Code *does* auto-load natively — the project `CLAUDE.md`:

- `Anis.TheCircle.Query/CLAUDE.md` (211 lines): **zero** mention of private setters, encapsulation, or sequence guards (only two incidental "read model" references).
- `Anis.TheCircle.Command/CLAUDE.md` (508 lines): **also zero** matches for the private-setter/sequence rule.

So on the Query side the rule was **nowhere in the auto-loaded context** — not in the project `CLAUDE.md`, not injected by the hook (no `project.yml`), not in any plugin-resident text. **Primary cause: rule absent from context.** (The command-side compliance is *consistent with* the injected `command.md` profile, but since the command `CLAUDE.md` doesn't state the rule either, it's equally explained by the model's strong event-sourcing priors — so I don't claim the injection "proved" it. The query-side failure is the load-bearing evidence.)

---

## Part 2 — Root cause analysis (3 layers)

### Layer 1 — Mechanical (load-bearing): rules gated on per-project metadata that was missing

The `implement.md` Microservice flow (step 5b) `cd`s into each secondary repo to write code there, but only drops a `feature-brief.md` (`briefs/`). It never runs `dotnet-ai init` or writes a `project.yml` for the secondary repos. The PreToolUse arch-profile hook keys off `./.dotnet-ai-kit/project.yml` **relative to CWD**:

```bash
# hooks/pretooluse-arch-profile.sh
PYM=".dotnet-ai-kit/project.yml"
[ -f "$PYM" ] || { echo "Project metadata not initialized; run \`dotnet-ai init\`"; exit 0; }   # ← Query/Processor hit this
```

No `project.yml` → no profile → **no rule body injected**. This is the direct cause of Q1–Q6. (It's the same structural hole as your `project_multi_repo_linked_specs_gap` memory: secondary repos have no kit awareness.)

A secondary fragility: the lookup is **CWD-relative and shallow** — it checks only `./.dotnet-ai-kit/`, not parent or child dirs. In a single-root, multi-project layout, launching Claude at the solution root (`Circle/`) finds no `project.yml` and no-ops for *every* edit.

### Layer 2 — Design: even when it fires, delivery is pointer-based, partial, and advisory

Authoritatively confirmed against the Claude Code docs:

- **Plugins have no always-on rules primitive.** "A `CLAUDE.md` file at the plugin root is not loaded as project context. Plugins contribute context through skills, agents, and hooks rather than `CLAUDE.md`." The manifest has no `rules`/`memory` field. ([plugins-reference])
- **Plugin skills/agents/commands contribute only their *descriptions/names* to every session; their bodies load on-invoke.** So the kit's `rules/` directory (not even a plugin component) is invisible until a hook cats it or the model opens it. ([plugins-reference])
- The kit's **SessionStart** hook deliberately emits a ≤500-token *index* with **"NO bulk rule bodies"** (Feature 019/FR-013).
- The kit's **PreToolUse arch-profile** hook injects the **profile body** but passes the universal conventions as a **pointer**: `Always-on conventions: rules/conventions/{...}.md`. A pointer requires the model to choose to open the file — a step it can skip, defer, or read-then-forget.
- All injection is **advisory** (`exit 0`). Nothing *blocks* a non-compliant write. The docs are explicit: *"[CLAUDE.md/memory] are loaded… Claude treats them as context, not enforced configuration. To block an action regardless of what Claude decides, use a PreToolUse hook instead."* ([memory])

### Layer 3 — Fundamental: prompt-time rules are non-deterministic, and the kit ships no deterministic gate

The research (Part 3.3) shows in-context rule adherence degrades with context length, instruction count, and session drift — and Claude specifically exhibits a **recency bias** (later/edit-time instructions are followed more reliably). A rule stated once at session start decays as the agent's context grows. The only way to make adherence *not* depend on the model is a build/test-time gate. The kit ships none by default:

- No `.editorconfig` with `severity = error`, no analyzer, no architecture-test **as a generated artifact**.
- It *documents* the exact right test — `Entities_ShouldHave_PrivateSetters()` in `skills/quality/architectural-fitness/SKILL.md` — but as an **on-demand skill** that was never generated into the Query project and never run. So the human reviewer was the de-facto gate.

---

## Part 3 — How comparable kits handle this (web research, all claims source-verified)

I dissected `codewithmukesh/dotnet-claude-kit` (the one you named) plus three comparators, and the authoritative Claude Code / .NET docs. **All 14 verified claims came back confirmed against primary sources.**

### 3.1 Rule *delivery* across kits

| Kit | Delivery mechanism | Bodies or pointers? | Path-scoping | Multi-repo |
|---|---|---|---|---|
| **codewithmukesh/dotnet-claude-kit** | `.claude/rules/*.md` (10 files), all `alwaysApply: true`; Claude Code natively auto-loads every `.md` in `.claude/rules/` | **Full bodies, always-on** for Claude; Cursor gets one consolidated file; Codex gets pointers | ❌ none (all global) | ❌ none |
| **ardalis/CleanArchitecture** | `.github/copilot-instructions.md` (always-on) | Full body | ❌ (one global file) | layers = separate `.csproj` |
| **github/awesome-copilot** | `*.instructions.md` with `applyTo:` glob | Body, but **path-scoped** | ✅ glob `applyTo` | n/a |
| **Aaronontheweb/dotnet-cursor-rules** | `.cursor/rules/*.mdc`, `globs:` + `alwaysApply:false` | Body, **path-scoped** | ✅ glob | n/a |
| **dotnet-ai-kit (yours)** | hook-injected profile body + **pointer** to conventions | **Pointer** for conventions; body for profile *if `project.yml` present* | ✅ design (5 universal + 11 domain) | ✅ design (per-solution manifest) |

**Key insight #1 — codewithmukesh's "secret" is just `.claude/rules/*.md`.** Claude Code auto-loads those bodies at session start (confirmed via [anthropics/claude-code#16299] + the `InstructionsLoaded` hook event). But that is a **project/user-level** mechanism — files under the *user's* `.claude/`. It is **not** something a pure marketplace plugin auto-ships into a foreign project. codewithmukesh effectively assumes the rules live in the project tree (clone/copy install). Your kit is **plugin-native by design** (Feature 019 deliberately does *not* copy rules into the project), so you **cannot** rely on `.claude/rules/` auto-load — you must inject via hooks. This is the crux.

**Key insight #2 — your rule architecture is *better* than codewithmukesh's.** They make all 10 rules `alwaysApply: true` (every rule burns context every turn, no scoping). Your **5 universal + 11 path-scoped** split is exactly what the adherence research recommends (resident bodies for high-signal universal rules; lazy-load for conditional domain rules). Your *design* is sound; the *implementation* doesn't actually materialize the universal bodies.

### 3.2 Rule *enforcement* across kits — nobody ships the deterministic gate

| Kit | Deterministic enforcement | Notes |
|---|---|---|
| codewithmukesh | Bypassable git pre-commit **grep** hooks (not even auto-installed); Roslyn MCP `detect_antipatterns` is **on-demand**; CI gates the *kit's own* files, not user code | `.editorconfig` has **0** `severity=error` |
| ardalis | **Compiler-enforced** layer boundaries (separate `.csproj` → illegal refs don't compile) + `TreatWarningsAsErrors` + CI | 0 analyzer packages of 52; `.editorconfig` suggestion-level; **no** NetArchTest |
| awesome-copilot | None (prompt-only) | "MANDATORY" prose, no gate |
| dotnet-cursor-rules | None (prompt-only) | — |

**Key insight #3 — the headroom.** *None* of the four kits ships analyzer-as-error or a NetArchTest/ArchUnitNET architecture-test suite. The strongest enforcement observed (ardalis) is structural (project separation) and can't express *intra-project* rules like "no public setter on a domain entity." **A kit that ships a NetArchTest fitness project + a `severity=error` `.editorconfig` + CI that runs them on the *user's* solution would have enforcement none of the comparators have** — and you already have the NetArchTest written.

### 3.3 What the platform actually supports (authoritative)

**Getting rule bodies into context (Claude Code):** ([memory], [hooks], [plugins-reference])
- `CLAUDE.md` / `.claude/rules/*.md` load full bodies at launch — **but project/user-level, not plugin-shippable**.
- `@path` imports expand bodies at launch (max depth 4).
- **SessionStart hook → `hookSpecificOutput.additionalContext`**: injects once at conversation start, **persists in the transcript**, re-fires on the `compact` matcher (matchers: `startup`, `resume`, `clear`, `compact`). **This is the plugin-native equivalent of always-on rules.**
- **UserPromptSubmit hook → `additionalContext`**: injects on **every** prompt (hard every-turn guarantee) but pays the token cost each turn.
- Hook `additionalContext` is **capped at 10,000 characters**.
- `InstructionsLoaded` hook event lets you *verify* exactly which rule files load and when.

**Blocking deterministically (Claude Code hooks):** ([hooks], [hooks-guide])
- **PreToolUse exit code 2** → blocks the tool call; stderr is fed back to Claude as the reason.
- **PreToolUse exit 0 + JSON** `hookSpecificOutput.permissionDecision: "deny"` + `permissionDecisionReason` → blocks (forward-compatible form; exit-2 and JSON are mutually exclusive).
- PreToolUse receives `tool_input` on stdin (`file_path`+`content` for Write; `file_path`+`old_string`+`new_string` for Edit) — a content hook can regex these. **Limitation:** an Edit hook sees only the *fragment*, not the whole file, so it can't reliably tell whether the edited class is a domain entity.
- **PostToolUse** can't undo a write but `decision:"block"` + `reason` halts follow-on work and forces a fix — and it sees the **file as actually written** (the reliable content-validation layer).
- Honesty note: "deterministic" = not contingent on the model complying; it does **not** mean a user can't disable the hook in their own `settings.json`.

**Deterministic .NET enforcement of encapsulation:** ([netarchtest], [archunitnet], [editorconfig-severity], [roslyn-analyzer], [banned-api], [ca1051])
- **NetArchTest** has no built-in "no public setter" predicate — use a reflection loop (`type.GetProperties().Where(p => p.SetMethod?.IsPublic == true)`) inside an xUnit test → fails `dotnet test`/CI. MIT, netstandard2.0. **You already have this exact pattern.**
- **ArchUnitNET** supports member-level visibility rules declaratively (`PropertyMembers()`), but is a heavier dependency.
- **`.editorconfig` `dotnet_diagnostic.<id>.severity = error`** makes a rule a **build error**. *Gotcha:* `.editorconfig` severity **overrides** `TreatWarningsAsErrors` ([roslyn#43051]) — set `severity = error` explicitly.
- **No built-in `CAxxxx` analyzer flags public property setters** (CA1051 targets *fields*; its "good" example literally uses `{ get; set; }`). Catching public setters deterministically requires NetArchTest/ArchUnitNET (test-time) or a **custom Roslyn analyzer** (compile-time, flags setters *and* ctors).
- **BannedApiAnalyzers** can seal a *specific named* escape hatch (e.g. a public parameterless aggregate ctor `M:Ns.Aggregate.#ctor`) but can't express "any public setter."

**Why bodies beat pointers (adherence research):** ([lost-in-middle], [many-if], [lifbench], [position-bias], [context-eng], [gpt41-guide])
- "Lost in the middle": info in the middle of long context is recalled worst (U-shaped).
- Instruction-following degrades with the *number* of constraints and with context length/session drift.
- Claude shows a **recency bias** — constraints appearing later are followed more reliably → **re-assert critical rules at edit time**.
- Anthropic's own guidance: finite "attention budget," "context rot"; keep high-signal *behavioral rules* resident and put large *data* behind pointers. Your universal conventions are exactly the high-signal/low-token content that should be resident.

---

## Part 4 — The fix (prioritized, kit-oriented)

### 🚑 Immediate workaround (no kit change — do this in Circle today)

Initialize the secondary projects so the arch-profile hook starts injecting their profile bodies, then re-run review:

```powershell
cd C:\Users\libya\source\repos\Ecom-LTD\Circle\Anis.TheCircle.Query
dotnet-ai init            # detects query-sql, writes .dotnet-ai-kit/project.yml
cd ..\anis.the-circle-processor
dotnet-ai init            # detects processor profile
```

After this, editing files in those projects will inject `profiles/microservice/query-sql.md` / `processor.md` (private setters, exact sequence guard, gap tests) on every Edit/Write. Launch Claude **from the project directory**, not the solution root, until Tier 4 lands.

### Tier 1 — Make the universal conventions actually resident (highest leverage for *delivery*)

> **⚠️ Update 2026-05-30 (see [`RESEARCH-2-workflows-and-tooling.md`](RESEARCH-2-workflows-and-tooling.md) §F):** there's now a *better* mechanism than the SessionStart hook below. A plugin can ship an **`output-styles/*.md` with `force-for-plugin: true`**, which injects rule bodies **into the system prompt automatically** whenever the plugin is enabled — **and it sidesteps the 10,000-char hook cap**. Lead with that channel; keep the SessionStart hook as a complement. **But still ship the *condensed* digest, not the full ~10.8k-char corpus** — cap-free removes the *mechanical* limit, not the *leanness* rationale: the same attention-budget / "shorter files → better adherence" findings (Tier-3 rationale, §3.3) mean a trimmed imperative digest in *every* system prompt beats dumping all five rule bodies verbatim. Also note: path-scoped rules load on *Read, not Write/create* (issue #38487), so the Tier-2 `PreToolUse Write|Edit` hook is confirmed still necessary for new-file generation.

The kit's biggest delivery gap is that the 5 universal conventions are a **pointer**. Inject their **bodies** (via a `force-for-plugin` output style, or the SessionStart hook as a complement — the plugin-native always-on mechanisms):

- **Lowest-friction:** the SessionStart hook's **plain stdout already reaches context** — the startup banner you see (`dotnet-ai-kit active / Skills and rules load on-demand…`) *is* the existing `cat <<EOF` heredoc landing in context. So the minimal change is to **expand that heredoc** with a condensed digest of the 5 `rules/conventions/*`. You only need the JSON `hookSpecificOutput.additionalContext` form (Part 5) if you want the *discrete* (non-visible-in-transcript) placement.
- The five rules total **10,787 chars** today — *just* over the **10,000-char hook-output cap**, so you can't emit them verbatim in one injection. A light trim gets the imperative essence under the cap: drop YAML frontmatter, the "## Related Skills" footers, and the longer code fences (keep the DO/DON'T lines). Keep the full bodies available on-demand.
- Register SessionStart on `startup`, `resume`, **and `compact`** so it survives compaction.
- This **re-litigates the FR-013 ≤500-token budget** on purpose: that optimization is precisely what starved the rules. The adherence research says the universal set is high-signal/low-token content that *should* be resident — so spend the tokens here, keep domain rules lazy.

### Tier 2 — Re-assert the path-relevant domain rule **body** at edit time (exploit recency)

The PreToolUse arch-profile hook already fires on `Edit|Write`. Upgrade it from "profile body + pointer" to also **inline the body of the domain rule(s) matching the touched path** (e.g. editing a `*Repository*.cs` → inline `rules/domain/data-access.md`; editing an entity → the encapsulation rule). Claude's recency bias means a rule restated right before the edit is followed far more reliably than one stated only at session start. Keep it short (matched rule only) to respect the attention budget.

### Tier 3 — Ship + run the deterministic gate (the real fix — adherence-independent)

This is what makes a public setter **fail the build** no matter what the model remembered. You already have the test.

1. **Generate the NetArchTest fitness tests by default.** Promote `skills/quality/architectural-fitness/SKILL.md` (incl. `Entities_ShouldHave_PrivateSetters`, the layer-dependency tests, the sequence-guard expectations) from an on-demand skill into a **generated test project** that `dotnet-ai init` / `add-tests` / `implement` scaffolds for command, query, and processor. Because `implement.md` step 1b and `/verify` already run `dotnet test`, the violation would be caught **automatically, per task** — no human needed.
2. **Generate a `severity=error` `.editorconfig`** for the rules you care about. At minimum `dotnet_diagnostic.CA1051.severity = error` (ban public mutable fields on entities). Set `severity = error` *explicitly* (don't rely on `TreatWarningsAsErrors`, which `.editorconfig` overrides). Add `<EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>`.
3. **(Optional) BannedSymbols.txt** to seal specific escape hatches (e.g. a public parameterless aggregate ctor).
4. **(Optional, highest power) a kit-shipped custom Roslyn analyzer** that flags public setters *and* public constructors on types implementing your aggregate/entity marker interface — compile-time + IDE enforcement. Highest maintenance; do this only if Tier 3.1 isn't enough.
5. **(Optional) PostToolUse validation hook** that runs the fitness check (or `dotnet format --verify-no-changes`) on the written file and returns `decision:"block"` + reason on violation — forces an immediate self-correct *inside* the editing loop, before commit. Prefer PostToolUse over PreToolUse here (it sees the whole file; PreToolUse sees only a fragment).

> Position this in your README as the differentiator: **"violations fail the build, not just the review"** — none of codewithmukesh / ardalis / awesome-copilot / dotnet-cursor-rules ships this.

### Tier 4 — Close the multi-repo / metadata gap (so Tiers 1–3 actually reach secondary repos)

1. **Init secondary repos during `implement` step 5b.** When the flow `cd`s into a secondary repo to write code, detect + write a `project.yml` (the correct profile) *before* writing code — not just `briefs/`. Then the arch-profile hook fires there.
2. **Make the hooks resilient to CWD.** Have `session-start-bootstrap.sh` and `pretooluse-arch-profile.sh` **walk up** to the nearest `.dotnet-ai-kit/project.yml` (and, for single-root multi-project layouts, resolve the project owning the edited `file_path`). This fixes "launched at solution root → no-op."
3. **Carry rule context in the brief.** If a secondary repo genuinely can't be init-ed, have the projected `feature-brief.md` embed the target profile's hard-constraints so at least the brief (which the model reads) restates them.
4. **Have `dotnet-ai check` verify rule delivery.** Add a check that confirms each managed project has `project.yml`, that the SessionStart digest is under the 10k cap, and (optionally) wire the `InstructionsLoaded` hook to log what actually loaded.

---

## Part 5 — Concrete sketches

**SessionStart always-on digest** (`hooks/session-start-bootstrap.sh`, additionalContext form):

```bash
# Emit JSON so the digest is added as context (not just visible stdout).
# Keep DIGEST < 10000 chars (condensed DO/DON'T essence of rules/conventions/*).
DIGEST="$(cat "$ROOT/rules/conventions/_digest.md")"
cat <<JSON
{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":$(printf '%s' "$DIGEST" | jq -Rs .)}}
JSON
```
Register on `startup`, `resume`, `compact` in `hooks.json`.

**NetArchTest default (the gate you already wrote)** — generated into each test project:

```csharp
[Fact]
public void DomainEntities_MustHave_PrivateSetters()
{
    var offenders = Types.InAssembly(typeof(SomeEntity).Assembly)
        .That().ResideInNamespace($"{Company}.{Service}.Domain")
        .GetTypes()
        .SelectMany(t => t.GetProperties()
            .Where(p => p.SetMethod?.IsPublic == true && p.Name != "ETag")
            .Select(p => $"{t.Name}.{p.Name}"));
    offenders.Should().BeEmpty("domain entities must use private setters + behavior methods");
}
```

**`.editorconfig` (generated, severity=error subset):**

```ini
[*.cs]
dotnet_diagnostic.CA1051.severity = error   # no public mutable fields on entities
# add IDExxxx style rules you want build-breaking, explicitly as error
```
…with `<EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>` in `Directory.Build.props`.

---

## Part 6 — How to verify the fix works

1. **`InstructionsLoaded` / hook logging** — confirm the universal digest and the matched domain rule actually appear in context for a Query-side edit.
2. **Re-run the Circle case** after `dotnet-ai init` on Query/Processor: ask the model to add a read-model entity; confirm it emits private setters + the exact sequence guard *without* a human prompt.
3. **Break it on purpose** — add a `public set;` to a domain entity and run `dotnet test`; the NetArchTest must fail. That's the proof the gate is adherence-independent.

---

## Part 7 — Sources (all primary-verified)

- [plugins-reference] Claude Code — Plugins reference: https://code.claude.com/docs/en/plugins-reference
- [memory] Claude Code — How Claude remembers your project (CLAUDE.md, rules, @imports): https://code.claude.com/docs/en/memory
- [hooks] Claude Code — Hooks reference: https://code.claude.com/docs/en/hooks
- [hooks-guide] Claude Code — Automate workflows with hooks: https://code.claude.com/docs/en/hooks-guide
- [anthropics/claude-code#16299] `.claude/rules/` auto-load at session start: https://github.com/anthropics/claude-code/issues/16299
- [netarchtest] BenMorris/NetArchTest: https://github.com/BenMorris/NetArchTest
- [archunitnet] TNG/ArchUnitNET: https://github.com/TNG/ArchUnitNET
- [editorconfig-severity] Configure code analysis rules (.NET): https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/configuration-options
- [roslyn#43051] `.editorconfig` severity overrides `TreatWarningsAsErrors`: https://github.com/dotnet/roslyn/issues/43051
- [roslyn-analyzer] Write your first analyzer and code fix: https://learn.microsoft.com/en-us/dotnet/csharp/roslyn-sdk/tutorials/how-to-write-csharp-analyzer-code-fix
- [banned-api] Microsoft.CodeAnalysis.BannedApiAnalyzers: https://github.com/dotnet/roslyn-analyzers/blob/main/src/Microsoft.CodeAnalysis.BannedApiAnalyzers/BannedApiAnalyzers.Help.md
- [ca1051] CA1051 (targets fields, not setters): https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/quality-rules/ca1051
- [lost-in-middle] Liu et al., Lost in the Middle (TACL 2024): https://arxiv.org/abs/2307.03172
- [many-if] How Many Instructions Can LLMs Follow at Once?: https://arxiv.org/html/2507.11538v1
- [lifbench] LIFBench (long-context instruction following): https://arxiv.org/abs/2411.07037
- [position-bias] Granular instruction-compliance / position bias (Claude = recency): https://arxiv.org/html/2601.18554
- [context-eng] Anthropic — Effective context engineering for AI agents: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- [gpt41-guide] OpenAI — GPT-4.1 prompting guide (instructions at both ends): https://cookbook.openai.com/examples/gpt4-1_prompting_guide
- **Comparators:** codewithmukesh/dotnet-claude-kit (`.claude/rules/*.md`, `hooks/hooks.json`, `.editorconfig`, `skills/ddd/SKILL.md`), ardalis/CleanArchitecture (`.github/copilot-instructions.md`, `Directory.Build.props`, `Directory.Packages.props`), github/awesome-copilot (`instructions/dotnet-architecture-good-practices.instructions.md`), Aaronontheweb/dotnet-cursor-rules (`csharp/coding-style.mdc`).
- **Cursor/Copilot scoping:** https://docs.cursor.com/en/context/rules • https://code.visualstudio.com/docs/copilot/customization/custom-instructions
