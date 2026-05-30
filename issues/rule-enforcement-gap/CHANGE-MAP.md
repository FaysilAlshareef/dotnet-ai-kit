# Change-map — what the two reports translate to in *this* codebase

**Date:** 2026-05-30
**Inputs:** [`REPORT.md`](REPORT.md) (Tiers 1–4 + workaround) and [`RESEARCH-2-workflows-and-tooling.md`](RESEARCH-2-workflows-and-tooling.md) (Workflows, Codex, Cursor, `force-for-plugin`, orchestration).
**Method:** every file below was opened and its *current* state verified against the recommendation. Format is an **inventory, not an implementation** — `file → current state → change → what it breaks`. Code sketches already live in REPORT.md Part 5; this doc references them, it does not reproduce them.

> **Scope honesty:** this maps the reports onto files. It does **not** re-litigate the diagnosis. Where a recommendation is a *decision* (not a mechanical edit), it's flagged **⚖️ DECISION** — those are yours to make before any code is written.

---

## ⚖️ Three decisions that change the blast radius

1. **Tier-1 delivery channel.** `force-for-plugin: true` output style (cap-free, system-prompt, plugin-native — RESEARCH-2 §F) **vs.** expanding the SessionStart heredoc (REPORT.md's original Tier-1).
   - **If force-for-plugin** (recommended): `hooks/session-start-bootstrap.sh` stays the ≤500-token banner **unchanged**, and `tests/unit/test_session_start_budget.py` + `contracts/session-start-bootstrap.contract.md` + **FR-013 survive untouched**. The digest rides the output style.
   - **If heredoc expansion:** the ≤500-token budget test must be deleted/rewritten and FR-013 + the contract amended. This is the *only* reason to touch FR-013 — surface it as a deliberate amendment, not a silent edit.
2. **The already-existing `copy_hook()`** (`copier.py:601`) writes a `prompt`-type PreToolUse hook into per-solution `.claude/settings.json`, but is **dead-branched for plugin-native hosts** (`copier.py:1127`, `tool_name not in PLUGIN_NATIVE_HOSTS` is always false for claude). **Supersede, don't revive:** the always-on path is the plugin-install `hooks/hooks.json` arch-profile hook (Tier 2), not per-solution settings injection.
3. **NetArchTest package.** Swap `NetArchTest.Rules` (unmaintained, last release 2021) → **`NetArchTest.eNhancedEdition`** (RESEARCH-2 §C), or adopt **ArchUnitNET** for declarative member-level "no public setter" without the reflection loop.

---

## Bucket 1 — Plugin-install-path (ships to *every* user on plugin upgrade; no per-solution write)

| File | Current state | Change | Report |
|---|---|---|---|
| `output-styles/conventions.md` | **does not exist** (no `output-styles/` dir) | **NEW.** `force-for-plugin: true` + `keep-coding-instructions: true`; carries the *condensed* 5-universal-conventions digest into the system prompt. Cap-free, always-on. | REPORT Tier 1 (corrected) · RESEARCH-2 §F.1 |
| `.claude-plugin/plugin.json` | 25 lines; `skills`/`commands`/`agents` only — **no `outputStyles` field** | **MODIFY.** Add `"outputStyles": "./output-styles/"`. | RESEARCH-2 §F.1 |
| `rules/conventions/_digest.md` | **does not exist** (5 full rule bodies = 10,787 chars) | **NEW.** Trimmed DO/DON'T digest (drop frontmatter, "Related Skills", long fences). Single source feeding the output style **and** the Codex hook. | REPORT Tier 1 / §5 |
| `hooks/pretooluse-arch-profile.sh` | injects profile body + a **pointer** ("Always-on conventions: rules/conventions/{…}.md", line 26); `project.yml` lookup is **CWD-relative & shallow** (line 9, `[ -f "$PYM" ]`) | **MODIFY.** (Tier 2) inline the **body** of the domain rule matching the touched path; (Tier 4.2) **walk up** to nearest `.dotnet-ai-kit/project.yml` so launching at solution root isn't a no-op. | REPORT Tier 2 + Tier 4.2 · RESEARCH-2 §F.2 (Read-not-Write → hook still required on Write) |
| `hooks/session-start-bootstrap.sh` | ≤500-token banner, "NO bulk rule bodies", fires on all SessionStart | **MODIFY (Tier 4.2 walk-up only)** if force-for-plugin carries the digest. **Larger rewrite only if** you pick the heredoc-expansion channel (see DECISION 1). Register `compact` matcher in `hooks.json` either way. | REPORT Tier 1 / Tier 4.2 |
| `hooks/hooks.json` | SessionStart (1) · PreToolUse (bash-guard, commit-lint, arch-profile) · PostToolUse (edit-format, scaffold-restore). **No UserPromptSubmit, no content-gate** | **MODIFY (optional).** Add SessionStart `compact` matcher; optionally a `PostToolUse Edit\|Write` fitness/format content-gate (`decision:"block"`) for in-loop self-correction (Tier 3.5). | REPORT §3.3, Tier 3.5 |
| `hooks/posttooluse-fitness-gate.sh` | **does not exist** | **NEW (optional, Tier 3.5).** Runs the fitness check / `dotnet format --verify-no-changes` on the written file; blocks on violation. Prefer PostToolUse (sees whole file) over PreToolUse (fragment only). | REPORT Tier 3.5 |
| `agents-claude/review/*.md` | 13 flat agents; **no `review/` subfolder** | **NEW (Part G).** Read-only dimension reviewers (`tools: Read, Grep, Glob`) mapped 1:1 onto `rules/domain/` (security, architecture, data-access, api-design, testing, naming) + a `verifier` + `synthesizer`. Each preloads its rule via `skills:` frontmatter. | RESEARCH-2 §G.4 |
| `skills/quality/architectural-fitness/SKILL.md` | uses **`NetArchTest.Rules`** (line 26, old pkg); already contains `Entities_ShouldHave_PrivateSetters()` (lines 121-137) | **MODIFY.** Swap package → `NetArchTest.eNhancedEdition`; keep the private-setter test as the canonical gate; add the sequence-guard expectation. (Promotion to a *generated* artifact is Bucket 2/3.) | RESEARCH-2 §C |
| `.codex-plugin/plugin.json` | `skills` only — **no `hooks` field** | **MODIFY (Part D).** Add `"hooks": "./hooks/hooks.json"`; the same digest + gate logic ports to Codex hooks 1:1. | RESEARCH-2 §D.3 |
| `.claude/workflows/*.js` | **not in the kit repo** (dynamic workflows can't be plugin-bundled) | **NEW (optional, Part A).** Ship `.js` audit/migration-sweep scripts in the repo; `dotnet-ai init` *optionally* copies into project `.claude/workflows/`. **Label experimental, pin v2.1.154+, do NOT add a `workflows` key to any manifest** (silently dropped). | RESEARCH-2 §A.5–A.6 |

---

## Bucket 2 — Per-solution init-written (governed by the ≤18-files cap, A-008 unmanaged-paths, **manifest tracking**)

> **Hard constraint discovered:** every file `init` writes **must be tracked in `.dotnet-ai-kit/manifest.json`** or `dotnet-ai check` trips **exit 14 ("unexpected paths")** and `upgrade`/`migrate` can't manage it. `manifest.py`'s `host_owner` already allows `claude/codex/cursor` — **no manifest *schema* change needed**, but the writer must register each new file.

| File | Current state | Change | Report |
|---|---|---|---|
| `.editorconfig` (per solution) | **kit ships none anywhere** (verified: no `.editorconfig` in repo) | **NEW.** `severity = error` subset (`dotnet_diagnostic.CA1051.severity = error`, chosen IDExxxx as `…:error`). Set severity **explicitly** — `.editorconfig` overrides `TreatWarningsAsErrors` (roslyn#43051). Must be manifest-tracked. | REPORT Tier 3.2 · RESEARCH-2 §C |
| Fitness test project (e.g. `*.Architecture.Tests`) | **no test-project template exists** (verified: `templates/**/*test*` empty) | **NEW.** Generated for command/query/processor; references `NetArchTest.eNhancedEdition`; carries the promoted `architectural-fitness` tests. Run by `implement` 1b / `verify`. Multiple files → all manifest-tracked → **raises the ≤18 cap**. | REPORT Tier 3.1 |
| `.cursor/hooks.json` | **not emitted** (only `.cursor/rules/*.mdc` are — `copier.py:246` `copy_commands_cursor`) | **NEW (Part E).** `afterFileEdit → dotnet format` (can't block); `beforeShellExecution → bash-guard` (`"permission":"deny"`); `beforeReadFile → deny secret reads`. Mirrors the Claude hooks. | RESEARCH-2 §E.3 |
| secondary-repo `.dotnet-ai-kit/project.yml` | **not written for secondaries** — `implement` 5b drops only `briefs/` (the Circle root cause) | **NEW write during `implement` 5b** (detect + write profile *before* writing code). This is the Layer-1 fix. | REPORT Layer 1 / Tier 4.1 |

*Unchanged but adjacent:* `.cursor/rules/*.mdc` already emitted — **only `.cursor/hooks.json` is net-new for Cursor.** Root `AGENTS.md` stays **user-owned** (FR-008 / T049 deleted the emitter) — for Codex cloud, write a kit-managed *section* or `@`-imported file, never clobber.

---

## Bucket 3 — Python engine

| File | Current state | Change |
|---|---|---|
| `src/dotnet_ai_kit/copier.py` | `copy_commands_cursor` emits `.mdc`; `copy_hook` dead-branched for plugin-native; `scaffold_project` renders templates | **MODIFY.** New emitters: `.editorconfig`, fitness test project, `.cursor/hooks.json` — each **registered in the manifest**. Decide copy_hook fate (DECISION 2). |
| `src/dotnet_ai_kit/cli.py` | `init` writes ≤18 per-solution files; `check` = 6 classes / 8 exit codes | **MODIFY.** `init` writes the new per-solution files; raise the file-count expectation; ensure `check`'s host smoke-fixture (exit 16) accepts `outputStyles` and the manifest tracks the new paths (exit 14). **Keep the Tier-3 build gate OUT of `check`** — `check` is read-only/no-shell-out/no-network (A-011). |
| `src/dotnet_ai_kit/hosts/{claude,codex,cursor}.py` | per-host `write_per_solution_files()` / `verify_install()` adapters | **MODIFY.** claude: emit `.editorconfig` + fitness project + (no output-style write — that's plugin-path). codex: nothing per-solution (hooks ship via plugin). cursor: emit `.cursor/hooks.json`. |
| `commands/implement.md` | 5b `cd`s into secondaries, writes only briefs; 1b quality check is advisory ("check against `rules/`") | **MODIFY.** 5b: write secondary `project.yml` (Tier 4.1). 1b: add "run the fitness test project" to the per-task gate. |
| `commands/verify.md` | runs build/test/`dotnet format`; Check 6 uses `.editorconfig` "if present"; reads the fitness SKILL but **runs no fitness project** | **MODIFY (Tier 3).** Add an explicit architecture-fitness check (`dotnet test` on the generated project); `.editorconfig` now always present. This is where determinism lives. |
| `commands/review.md` | 9 advisory prompt checks; loads `reviewer.md` + skills; single-threaded | **MODIFY (Part G).** Rebuild as a **main-thread orchestrator** fanning out to the Bucket-1 dimension reviewers (find → verify → synthesize). Subagents can't nest, so the orchestrator must be `/review` itself, not a Workflow. |
| `templates/*/Directory.Build.props` | has `TreatWarningsAsErrors` but **no `EnforceCodeStyleInBuild`** | **MODIFY.** Add `<EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>` (required for IDExxxx rules to break the CLI build). |

---

## Bucket 4 — Tests & contracts (the real blast radius)

| Pin | What it asserts today | Effect of the change |
|---|---|---|
| `tests/unit/test_session_start_budget.py` · `contracts/session-start-bootstrap.contract.md` · **FR-013** | SessionStart output ≤500 tokens, "NO bulk rule bodies" | **Survives unchanged** under force-for-plugin (DECISION 1). **Breaks / must be amended** only if you expand the heredoc. |
| `contracts/pretooluse-arch-profile.contract.md` | profile body + convention *pointer*; advisory exit 0 | **Amend** for Tier-2 domain-rule **body** injection + Tier-4.2 walk-up resolution. |
| `contracts/check-cli.contract.md` · `tests/unit/test_check_raw_schema_validation.py` · `test_check_filesystem_inspection.py` · `test_sc010_check_runtime.py` | 6 check classes; exit 14 = manifest integrity/unexpected paths; exit 16 = host loader/manifest schema | **Update.** New init-written files must be manifest-tracked (else exit 14); host fixture must still load with `outputStyles` present (exit 16); keep runtime <10s (SC-010). |
| "≤18 per-solution files" invariant (CLAUDE.md + any counting test) | per-solution write budget | **Raise.** `.editorconfig` + fitness project (multiple files) + `.cursor/hooks.json` increase the count. |
| `tests/unit/test_no_network_invariant.py` (**A-011**) | `init/check/migrate/render` make no network calls | **Must stay green.** The Tier-3 gate runs via `/verify` (model-driven `dotnet test`) and CI — **never** inside `init`/`check`/`render`. |
| `manifest.py` (`host_owner ∈ {claude,codex,cursor,copilot}`) | per-file host ownership | **No schema change** — new files just get tracked with the right `host_owner`. |
| **New tests needed** | — | output-style present + `force-for-plugin:true`; `.editorconfig` severity content; fitness project generates + fails on a public setter; `.cursor/hooks.json` shape; `.codex-plugin` `hooks` field; arch-profile body-injection + walk-up. |

---

## One-paragraph synthesis

The **smallest correct change** is: (1) add an `output-styles/conventions.md` with `force-for-plugin:true` + register it in `.claude-plugin/plugin.json` — this alone fixes the *delivery* gap that caused Circle, and leaves FR-013/the budget test untouched; (2) upgrade `hooks/pretooluse-arch-profile.sh` to inject the matched domain-rule **body** and **walk up** for `project.yml`; (3) write a secondary `project.yml` in `implement.md` step 5b so the hook fires at all in linked repos. The **durable** change is **Tier 3** — promote the already-written NetArchTest (swapped to `eNhancedEdition`) into a *generated* fitness project plus a `severity=error` `.editorconfig`, wired into `/verify`, so a public setter **fails the build** regardless of what the model remembered. Everything Codex/Cursor is the same digest + same gate ported through their (now near-identical) hook systems; **the build gate is host-agnostic and is the kit's defensible differentiator.** Workflows are an optional, experimental scale tool — ship `.js` + `init`-copy, never a manifest dependency.
