# Research II — Claude Code "Workflows", new enforcement features, and cross-tool landscape

**Date:** 2026-05-30
**Companion to:** [`REPORT.md`](REPORT.md) (the rule-enforcement-gap diagnosis).
**Method:** multi-agent web research with recency-first adversarial verification. Where a claim is marked **[verified]** it survived an independent fact-check against the official source; the run confirmed **15/16** load-bearing claims (1 "uncertain" = a release-date nitpick that *strengthens* the conclusion).
**Freshness caveat:** several items below are **days old** (Claude Opus 4.8 + dynamic workflows shipped 2026-05-28). Treat fast-moving previews as moving targets.

---

## Part A — Claude Code "Dynamic Workflows" (the feature you asked about)

### A.1 What it actually is

The feature is officially called **"dynamic workflows"** (not "Workflows"). Official docs page title: *"Orchestrate subagents at scale with dynamic workflows."* **[verified]**

> *"A dynamic workflow is a JavaScript script that orchestrates subagents at scale. Claude writes the script for the task you describe, and a runtime executes it in the background while your session stays responsive."*

The runtime runs the script in an **isolated environment**; intermediate results stay in **script variables instead of Claude's context window**, and only a **final consolidated report** comes back. That is exactly what you watched happen with `/deep-research` in this session — it *is* a dynamic workflow.

### A.2 Release & availability **[verified]**

- Shipped in **Claude Code v2.1.154**, released **2026-05-28** alongside **Claude Opus 4.8**. (Changelog had advanced to v2.1.158 at research time.)
- **Research preview.** Requires **v2.1.154+**. Available on **all paid plans**, the **Anthropic API**, **Amazon Bedrock**, **Google Cloud Vertex AI**, and **Microsoft Foundry**. On **Pro** you must turn it on from the *Dynamic workflows* row in `/config`.
- This is **~2 days old** as of this report — far too new to take a hard dependency on.

### A.3 How it works **[verified]**

- It's the **4th parallelization primitive** in Claude Code, alongside **subagents**, **agent view**, and **agent teams**. The workers a workflow spawns **are subagents** (the `Task` tool was renamed **`Agent`** in v2.1.63; `Task(...)` still works as an alias).
- Scale limits: **up to 16 concurrent agents**, **1,000 agents total per run**.
- Spawned subagents always run in **`acceptEdits`** mode and inherit the session's tool allowlist regardless of the session's permission mode. In headless `claude -p` and the **Agent SDK** there's **no approval prompt** — the run starts immediately.
- `/workflows` lists running/completed runs (per-phase agent counts, token totals, elapsed). Keys: arrows select · Enter/→ drill in · Esc back · j/k scroll · **p** pause/resume · **x** stop · **r** restart agent · **s** save.
- **Resume is session-scoped only** — completed agents return cached results and the rest run live, but **only within the same Claude Code session**; exiting restarts from scratch. There is no durable cross-session run ID.

### A.4 How to author & "add to your project" **[verified]**

Three ways to get a workflow:
1. Put the literal word **"workflow"** anywhere in a prompt → Claude writes a script (highlighted; `alt+w` ignores it for one prompt; the "Workflow keyword trigger" can be disabled in `/config`).
2. **`/effort ultracode`** — combines `xhigh` reasoning effort with **automatic workflow orchestration** for each substantive task (session-scoped, resets on new session, only on models that support `xhigh`).
3. Run an existing **saved or bundled** workflow command.

To **persist/share one**: run `/workflows` → select the run → press **`s`** → **Tab** toggles between:
- **`.claude/workflows/`** in your project — **shared with everyone who clones the repo**, and
- **`~/.claude/workflows/`** in your home dir — personal.

It then runs as **`/<name>`** and appears in `/` autocomplete. If a project and personal workflow share a name, **the project one wins**.

The kit ships **one bundled workflow today: `/deep-research`.** Disable controls: `/config` toggle, `"disableWorkflows": true` in `settings.json`, env `CLAUDE_CODE_DISABLE_WORKFLOWS=1`, or org-wide via **managed settings**.

> ⚠️ The JavaScript authoring API (`agent()`, `parallel()`, `pipeline()`, the `schema:` field, `export const meta {…}`, the `.js` extension) is **NOT documented by Anthropic**. The signatures circulating come from third-party reverse-engineering (e.g. alexop.dev). Hand-authored workflow scripts therefore ride an **undocumented, unstable contract**. **[verified]**

### A.5 The key answer: can dotnet-ai-kit ship a workflow as a plugin? **No.** **[verified]**

- `plugin.json` has **no `workflows` field** and there is **no `workflows/` component directory**. The complete component set is: skills, commands, agents, hooks, mcpServers, outputStyles, lspServers, experimental.themes, experimental.monitors (+ userConfig, channels, dependencies).
- Claude Code **"ignores top-level fields it does not recognize"**, so a `workflows` key in the manifest would be silently dropped.
- Dynamic workflows live **only** in `.claude/workflows/` (project) or `~/.claude/workflows/` (user) — neither is a plugin-distributable path.

**What the plugin CAN ship** are the **worker primitives** a workflow orchestrates: **subagents** (`agents/*.md`, namespaced `dotnet-ai-kit:<agent>`) and **commands/skills** (`/dotnet-ai-kit:<cmd>`). The kit already bundles 13 agents + 27 commands — fully supported.

### A.6 So how would the kit "use Workflows"? (practical options)

1. **Ship `.js` workflow files in the kit repo + docs**, and have `dotnet-ai init` *optionally copy them* into the project's `.claude/workflows/` (so they're repo-shared as `/<name>`). Good candidates for .NET: a **solution-wide convention audit**, a **multi-repo migration sweep**, or a **review/verify fan-out**. **Label experimental, version-pin to v2.1.154+, and treat the JS API as unstable.**
2. **Make the kit's subagents workflow-ready** — crisp `description`/`whenToUse` so Claude's auto-written workflows (or `/effort ultracode`) can leverage them. *Caveat:* targeting a **named custom/plugin subagent** from a workflow script is **not officially documented** (examples only show `agentType: "general-purpose"`) — verify before relying on it.
3. **Don't hard-depend yet.** It's a research-preview, toggleable off by users/orgs, with an undocumented authoring API. Keep `dotnet-ai check`'s manifest validation aligned to the *official* component fields (there is no `workflows` field to validate).
4. **The robust, available-today path for the rule-enforcement problem is still hooks + deterministic gates** (REPORT Tiers 1–3) — *not* workflows. Workflows are a thoroughness/scale tool (audits, reviews), not a rule-delivery mechanism.

---

## Part B — Cross-tool standards (AGENTS.md, GitHub Spec Kit)

### B.1 AGENTS.md is now a real cross-tool standard — but Claude Code doesn't auto-load it **[verified]**

- **AGENTS.md** is an open, tool-agnostic Markdown convention adopted by **20+ coding agents** (Codex, Jules + Gemini CLI, Cursor, Windsurf + Devin, GitHub Copilot coding agent, JetBrains Junie, Zed, Warp, VS Code, Aider, goose, opencode, Factory, RooCode, Kilo Code, Amp, Augment, Semgrep, UiPath…) and **60k+ projects**. It standardizes the **filename/location, not a schema**.
- **Claude Code reads `CLAUDE.md`, NOT `AGENTS.md`** (confirmed verbatim in the memory docs; native-support feature requests like anthropics/claude-code#6235 remain **open**). Bridges: `@AGENTS.md` import inside `CLAUDE.md`, or a `CLAUDE.md → AGENTS.md` symlink (on Windows prefer the import — symlinks need admin/Developer Mode).
- **Implication for the kit:** emitting/maintaining **AGENTS.md closes the "rules not resident" gap for Codex/Cursor/Copilot/Gemini**, but **Claude Code still needs the hook-injection path** from REPORT Tier 1/2. Respect the kit's existing decision that **root `AGENTS.md` is user-owned** (the legacy emitter was removed in T049) — write a kit-managed *section* or a separate file the user's `AGENTS.md` `@`-imports; never clobber it.

### B.2 GitHub Spec Kit — the kit is built on it; the differentiator is determinism **[verified]**

- **GitHub Spec Kit** (official `github/spec-kit`, MIT) is the spec-driven-dev toolkit whose command set — `/speckit.{specify, clarify, plan, tasks, analyze, implement, constitution, checklist, taskstoissues}` — **matches dotnet-ai-kit's SDD lifecycle**. The kit repo carries `.specify/` scaffolding and `speckit.*` skills, i.e. **dotnet-ai-kit is built on Spec Kit**, not parallel to it.
- Spec Kit is **language-agnostic**; its **constitution** (`memory/constitution.md`) and **"Phase -1 Gates"** enforce conventions **only at prompt/template level** (LLM-evaluated checkbox gates) and it ships **zero analyzers or build gates**. `/speckit.review` is an **unmerged proposal** (issue #1323), not shipped.
- **Positioning:** frame the kit's `constitution v1.0.8` as *"Spec Kit's constitution, made deterministic for .NET."* The defensible edges over both Spec Kit and the four comparator kits are **(a) .NET opinionation** and **(b) the deterministic build gate** from REPORT Tier 3.

---

## Part C — .NET deterministic enforcement: 2026 specifics (refines REPORT Tier 3)

These update the REPORT's Tier-3 recommendations with current package/version reality:

- **Do NOT use the original `NetArchTest` (BenMorris)** — it is effectively **unmaintained** (last release v1.3.2; no releases for years). **[verified — the only "uncertain" verdict was that its last release is actually 2021, not 2023, i.e. *more* stale, strengthening this.]**
- **Use `NetArchTest.eNhancedEdition` (NeVeSpl)** instead: **v1.4.5 (2025-06-04)**, .NET Standard 2.0, compatible **net5.0–net10.0**, ~643k downloads. It's based on v1.3.2 with fixes + added dependency-analysis rules, and **matches the reflection-loop pattern already written in** `skills/quality/architectural-fitness/SKILL.md`. **[verified]**
- **Or `ArchUnitNET` (TngTech)**: **v0.13.3 (2026-03-05)**, supports **.NET 10**, and uniquely offers **declarative member-level visibility rules** (`PropertyMembers()`) — so "no public setter" is expressible without a reflection loop. Heavier (Mono.Cecil); adapters for xUnit/xUnitV3/NUnit/MSTestV2. **[verified]**
- **The platform did NOT close the gap.** **.NET 10** (GA Nov 2025, LTS) added only **CA2023** and **CA2266** as new default rules — **neither about encapsulation**. **CA1051** still targets *fields* (and is off by default in .NET 10). **No built-in CA/IDE analyzer flags a public property setter or public aggregate constructor** → a **custom Roslyn analyzer** or a **NetArchTest/ArchUnitNET** test remains the *only* deterministic enforcement. **[verified]**
- **Wiring the `.editorconfig` correctly** (verified mechanics):
  - **Code-style (IDExxxx) analysis is DISABLED by default on command-line builds** → you **must** set MSBuild **`EnforceCodeStyleInBuild=true`** AND set each rule's severity in `.editorconfig`.
  - **.NET 9+** lets the **option format** carry a build-respected severity, e.g. `dotnet_style_require_accessibility_modifiers = always:error`.
  - Set `dotnet_diagnostic.<id>.severity = error` **explicitly** (don't trust `TreatWarningsAsErrors`, which `.editorconfig` overrides — REPORT §3.3). CA-side knob: `CodeAnalysisTreatWarningsAsErrors`. Lock the set with `AnalysisLevel` (default `latest`; e.g. `latest-Recommended`) and `AnalysisMode` (None/Default/Minimum/Recommended/All).
- **Headroom confirmed:** no shipping AI-coding kit bundles **analyzer-as-error + architecture tests that run on the user's solution**. README differentiator stands: **"violations fail the build, not just the review."** **[verified — medium; absence-of-evidence, re-check before using as a marketing claim]**

---

## Part D — OpenAI Codex (rule enforcement + orchestration)

**Headline:** Codex's rule/enforcement/orchestration surface is now a **near-1:1 structural mirror of Claude Code** — same hook events, same `deny`/`exit 2`/`additionalContext` semantics, plus skills, subagents, and a plugin manifest. **Your REPORT.md fix plan ports to Codex almost verbatim.** (Subagent passes also reported the kit's existing `.codex` adapter looks mechanically correct against these docs — verify against your own `src/.../hosts/codex.py` and `.codex-plugin/plugin.json` before relying on it.)

### D.1 Rule delivery & enforcement
- **AGENTS.md is Codex's primary always-on instruction channel** — discovered hierarchically (global `~/.codex/AGENTS.md` → repo-root → nested subdir), **at most one file per directory**, concatenated root→cwd with **closer files overriding farther** ones. An `AGENTS.override.md` is checked **before** `AGENTS.md` at each level. **[verified]**
- It is loaded as **instructions, not enforced configuration** — the same advisory gap REPORT.md identified for `CLAUDE.md`. Hard budget: **`project_doc_max_bytes` ≈ 32 KiB** (Codex stops adding files past the limit), plus `project_doc_fallback_filenames`. **[verified]**
- **Codex has a full HOOKS system that is a near-clone of Claude Code's** — events `SessionStart, SubagentStart, PreToolUse, PermissionRequest, PostToolUse, PreCompact, PostCompact, UserPromptSubmit, SubagentStop, Stop`; blocking via `permissionDecision: "deny"` / `exit 2`; `PostToolUse` `decision: "block"`; `additionalContext` injection. Discovery: `~/.codex/hooks.json`, inline `[hooks]` in `config.toml`, `<repo>/.codex/hooks.json`. **Stabilized ~May 2026, with plugin-bundled hooks default-enabled** (changelog 2026-05-18). **[verified]** This is the deterministic primitive the kit needs on Codex.
- **Deterministic guardrails = sandbox + approval modes, OS-enforced** (macOS Seatbelt/`sandbox-exec`, Linux `bwrap`+`seccomp`): `sandbox_mode` ∈ `read-only|workspace-write|danger-full-access`; `approval_policy` ∈ `untrusted|on-request|never|granular` (+ a **deprecated** `on-failure`). **They block file/network/command actions but do NOT gate on test/lint/CI failure.** **[verified]**
- **Codex Skills** (`SKILL.md`) use the **same progressive-disclosure/description-matching model as Claude Code** (~2% / 8K-char list budget; full body on selection) — so skills are **not** a reliable always-on rule channel (same trap). Path: `.agents/skills` (repo) / `$HOME/.agents/skills` (user), **not** `~/.codex/skills`. Launched Dec 2025. **[verified]**
- **Codex plugins** (`.codex-plugin/plugin.json`) bundle `skills, mcpServers, apps, hooks` — **no `agents` field** (kit's adapter comment is correct). **Codex subagents** are TOML files in `.codex/agents/*.toml` (`name`, `description`, `developer_instructions`; built-ins `default`/`worker`/`explorer`). Plugin marketplace shipped 2026-05-18/21. **[verified]**

### D.2 Orchestration
- **Codex cloud tier** runs background + **parallel** tasks, each in its own sandbox (launched 2025-05-16; CLI 2025-04-16). **Subagent fan-out** — "spawn specialized agents in parallel and collect their results." **`@codex` GitHub** integration proposes PRs — but delivery is **not gated by check results**. **Automations** (cloud triggers) + `codex remote-control` daemon (2026-05-18) push toward continuous operation. **GA at DevDay Oct 6, 2025 with GPT-5-Codex.** **[verified]**
- Even cloud has **no test/lint gate** — commands are discovered from AGENTS.md, so gating must come from **your repo's CI/build**.

### D.3 Applicability to dotnet-ai-kit
1. **Port the REPORT.md fix to Codex via a plugin hook.** Add `"hooks": "./hooks/hooks.json"` to `.codex-plugin/plugin.json`; ship a `SessionStart`/`UserPromptSubmit` hook emitting the same condensed conventions digest as `additionalContext` (the **single digest file feeds Claude + Codex**). Port the deterministic gate as a Codex `PreToolUse`/`PostToolUse` hook (identical semantics).
2. **The NetArchTest + `severity=error` `.editorconfig` gate is host-agnostic** — neither Codex local nor cloud gates on tests, so the build-time gate covers Codex for free (the agent's AGENTS.md-driven `dotnet test` / your CI run it).
3. **Use AGENTS.md for the cloud surface** (where plugin hooks may not run): emit a kit-managed **section** (or a `project_doc_fallback_filenames` entry) carrying the exact `dotnet test` / `dotnet format` / fitness-test commands + hard constraints — without clobbering the user-owned root AGENTS.md (FR-008).
4. **Minor accuracy fixes from verification:** `on-failure` is a *deprecated* approval mode (not absent); DevDay is firmly **Oct 6, 2025** (GA + GPT-5-Codex confirmed); a couple changelog sub-dates were off by days. Core thesis fully supported.

## Part E — Cursor (rule enforcement + orchestration)

**Headline:** Cursor shipped the **deterministic-enforcement layer the kit needs — Hooks — in v1.7 (2025-09-29)**. The kit already emits `.cursor/rules` `.mdc` files; it should now also emit `.cursor/hooks.json`.

### E.1 Rule delivery & enforcement
- `.cursor/rules/*.mdc` files (plain `.md` is ignored) with **four activation types** via `alwaysApply`/`globs`/`description`: **Always** (`alwaysApply:true`), **Auto-Attached** (`globs` + `alwaysApply:false`), **Agent-Requested** (`description` only), **Manual** (`@`-mention). Four scopes: Project / User / Team (dashboard) / `AGENTS.md`. **Nested per-directory `.cursor/rules` AND nested `AGENTS.md` are supported.** **[verified]**
- Rules are **advisory** ("persistent, reusable context at the prompt level") — no block-on-violation in the rules system itself. **[verified]**
- **Cursor HOOKS shipped in v1.7 (2025-09-29), as beta** — "observe, control, and extend the Agent loop." Config = `.cursor/hooks.json` (`version:1`, `hooks` map → `{command}` arrays). **Blocking via `"permission":"deny"` or `exit code 2`.** Precedence Enterprise→Team→Project→User. **[verified]**
- Hook events: core six (`beforeSubmitPrompt`, **`beforeShellExecution`** [can block], **`beforeMCPExecution`** [block], **`beforeReadFile`** [block], `afterFileEdit` [informational], `stop`) — plus an extended set now confirmed real in Cursor docs/forums: `sessionStart/sessionEnd`, `afterShellExecution`, `afterMCPExecution`, `preCompact`, `beforeTabFileRead/afterTabFileEdit`, and the Claude-style `preToolUse/postToolUse/postToolUseFailure/subagentStart/subagentStop/afterAgentResponse/afterAgentThought`. (`workspaceOpen` remains unverified.) **[verified — the verifier upgraded these from the launch-era "6 events" to the current ~21-event set]**
- Key behavior: **`afterFileEdit` is informational (cannot block)** → use it to auto-fix (run `dotnet format`); **`beforeShellExecution` can block** → the real "deny dangerous command" point.

### E.2 Orchestration
- **Background Agent** GA in **1.0 (2025-06-04)** (preview in 0.50, May 2025). **Composer** frontier model + **multi-agent parallel** (git worktrees / remote machines) in **2.0 (2025-10-29)**. **Plan Mode** in 1.7, improved in 2.1 (2025-11-21). **Bugbot** PR review (out of beta Jul 2025; agentic rebuild Jan 2026; "over 70%" resolution; ~2M PRs/month). **[verified]**
- **There is NO Cursor feature literally named "Workflow."** The scheduling/orchestration primitive is **Automations (2026-03-05)** — agents run on schedules or event triggers (Slack / Linear / GitHub PR / PagerDuty / webhooks), spinning up a cloud sandbox. Latest: Composer 2.5 (2026-05-18), 3.5 (2026-05-20, adds a `/loop` skill), 3.6 (2026-05-29, "Auto-review" run mode). **[verified]**

### E.3 Applicability to dotnet-ai-kit
1. **Emit `.cursor/hooks.json` alongside the `.mdc` rules (highest leverage).** Mirror the kit's Claude hooks: `afterFileEdit` → `dotnet format` (auto-fix; can't block); **`beforeShellExecution` → port `bash-guard` (`"permission":"deny"`)**; `stop` → `commit-lint`/wrap-up; `beforeReadFile` → deny secret-file reads. Generate it in `dotnet-ai init` like `.claude/settings.json`. Note hooks were **beta at launch** — gate on the user's Cursor version in `dotnet-ai check`, and re-verify the full event list against `cursor.com/docs/hooks` at build time.
2. **Keep `.mdc` rules but map the conventions/domain split to Cursor's loader:** universal → `alwaysApply:true`; path-scoped domain → `globs:` Auto-Attached (e.g. `globs:"**/*Controller.cs"` for api-design). Native path-scoping instead of relying on the agent reading a description.
3. **AGENTS.md** for the human-readable brief (nested support + cross-tool lingua franca).
4. Orchestration mapping (lower priority): SDD lifecycle ≈ **Plan Mode**; recurring chores ≈ **Automations** (cloud-hosted — document as optional, not a core dependency).

## Part F — Newest Claude Code rule-delivery & enforcement features

> **⚠️ This section materially CORRECTS [`REPORT.md`](REPORT.md) Layer 2 / Tier 1.** REPORT.md said *"plugins have no always-on rules primitive; the only plugin-native way to force rule bodies into context is a hook."* As of the current docs (v2.1.158), that is **outdated** — there are now **three** plugin-native always-on channels, the best of which sidesteps the 10k-char cap.

### F.1 A plugin can now ship always-on rule BODIES three ways (was: one)
1. **`force-for-plugin: true` output style — the new best answer.** A plugin ships `output-styles/<name>.md` with `force-for-plugin: true`; it **auto-applies to the system prompt for every session the plugin is enabled in, without the user selecting it**, and overrides the user's `outputStyle`. Output styles "directly modify Claude Code's system prompt." Set `keep-coding-instructions: true` to retain built-in SWE behavior while adding your rules. **Crucially, system-prompt text sidesteps the 10,000-char hook-output cap** that made REPORT.md's "10,787-char SessionStart digest" infeasible in one shot. **[verified — existence/behavior; introduction version unpinned]**
2. **Bundled `settings.json` `agent` key** (heavier): runs the main thread as a named subagent, applying *its* system prompt/tools/model. Strongest delivery, but it **commandeers the entire main-thread persona** — only if the kit wants to own the default agent. **[verified]**
3. **`SessionStart` `additionalContext` hook** (the REPORT.md path): still valid, register on `startup`/`resume`/**`compact`**, but **capped at 10,000 chars** — best for the project-metadata banner + a short pointer, with `force-for-plugin` carrying the rule bodies. **[verified]**

> Note: a plugin manifest **still has no `rules` field**, a plugin-root `CLAUDE.md` is **still not loaded**, and `.claude/rules/*.md` (now officially GA/documented, with `paths:` scoping and load order Managed→User→Project→Local) is **still project/user-scoped, not plugin-shippable**. So the *manifest* gap REPORT.md described is real — but `force-for-plugin` routes around it. **[verified]**

### F.2 The path-scoped "Read-not-Write" gap — directly relevant to the Circle case **[verified]**
- Path-scoping uses **`paths:` frontmatter** (globs). But **path-scoped rules/skills load only when Claude *reads* a matching file (or edits an existing one via the pre-edit Read) — NOT when Claude *creates a new file* via Write.** Confirmed by issue **#38487** (opened 2026-03-25, **closed not-planned**).
- **Implication:** the Circle Query violations happened on **new-file generation** — exactly what a `paths:`-scoped rule would miss. So a **`PreToolUse Write|Edit` hook that inspects `tool_input.file_path`** and re-asserts the matched domain-rule body is **still required** (REPORT.md Tier 2 stands, sharpened).

### F.3 Enforcement primitives confirmed & expanded **[verified]**
- **PreToolUse blocks** via `exit 2` or `permissionDecision: "deny"` (+ a new `defer` value). **PostToolUse** can't un-run a tool but `decision:"block"` forces a fix and **can now replace tool output** (v2.1.121) — the reliable full-file validation layer.
- **Many new hook events** (2.1.x): `Setup`, `UserPromptExpansion`, `PermissionRequest/Denied`, `PostToolUseFailure`, `PostToolBatch`, `MessageDisplay`, `SubagentStart/Stop`, `FileChanged`, `InstructionsLoaded`, … and **new hook *types*: `command`, `http`, `mcp_tool`, `prompt` (LLM-evaluated), `agent` (agentic verifier)** — so a convention check can be an LLM/agent gate, not just a script.
- **`InstructionsLoaded`** hook = **observability only** (can't inject/block); use it to *verify* which rule files actually load (REPORT.md Part 6).
- **Managed/enterprise settings** are highest precedence and **cannot be overridden**: `claudeMd` injects org-managed rules, `permissions.deny`, `sandbox.enabled`, `allowManagedPermissionRulesOnly`, `disableSkillShellExecution`. A *plugin's* own hooks can be disabled in a user's `settings.json`; **managed settings cannot** — the path to non-bypassable org enforcement.
- **Permission modes**: `dontAsk` (pre-approved tools only, fully non-interactive) is the right CI-gate mode; `auto` (v2.1.83+) boundaries are explicitly *not* a hard guarantee (lost on compaction) — "for a hard guarantee, add a deny rule."
- **Skills** gained `paths:`, `user-invocable:false` (model-only "background knowledge"), `allowed-tools`/`disallowed-tools`, `model`/`effort` — a `paths:`+`user-invocable:false` skill is a clean **Tier-2 conditional** rule vehicle (but inherits the #38487 Read-not-Write gap).

### F.4 Net correction & recommendation
- **Update REPORT.md Tier 1** to lead with a **`force-for-plugin` output style** carrying the condensed 5-universal-conventions digest (cap-free, plugin-native, always-on) — *better* than expanding the SessionStart heredoc.
- Keep **Tier 2** (PreToolUse `Write|Edit` hook re-asserting the matched domain rule) — confirmed still necessary because of the Read-not-Write gap.
- Keep **Tier 3** (NetArchTest + `severity=error` `.editorconfig`) as the adherence-independent gate; optionally use the new `agent`/`prompt` hook types or managed settings for org-level non-bypassability.

## Part G — Wiring orchestration/subagents into the kit (quality gates, Agent SDK/CI)

### G.1 Multi-agent review patterns (Anthropic's own) **[verified]**
- Anthropic's production **multi-agent research system** is **orchestrator-worker**: an Opus lead spawns 3–5 (up to 10+) parallel Sonnet subagents with effort-scaled counts, then a separate **CitationAgent** synthesizes — and **beat single-agent Opus by 90.2%**. Lesson: subagent prompts must be **highly specific** (objective, output format, boundaries) or they duplicate work. Evaluation uses an **LLM-as-judge rubric** + human review.
- Anthropic ships a managed **GitHub Code Review** product whose architecture is exactly **find → verify → synthesize**: parallel dimension-specialized agents → a **verification step that filters false positives against actual code** → dedup + severity ranking. Tunable via repo `CLAUDE.md` + a `REVIEW.md` injected highest-priority into every review agent. **It is non-blocking by design** (neutral check run) — to gate merges you **parse its severity JSON yourself**. Research preview, Team/Enterprise, ~$15–25/review. Local analog: the `/code-review` command (renamed from `/simplify` at v2.1.147).

### G.2 Agent SDK / headless for CI **[verified]**
- `claude -p` (headless) supports `--output-format json`, **`--json-schema`** (forces `structured_output`), **`--permission-mode dontAsk`** (CI-safe), `--max-turns`, `--append-system-prompt`. **`--bare`** skips auto-discovery (recommended for SDK/CI; will become the `-p` default) — opt back in with `--plugin-dir`/`--agents`/`--mcp-config`.
- **`anthropics/claude-code-action@v1`** (GA 2025-08-26; latest v1.0.133, 2026-05-23) runs on PR events with **no `@claude` mention**, and can **install a plugin marketplace + invoke that plugin's skill as the prompt** — the cleanest CI path. The `system/init` stream event reports `plugin_errors` → **fail CI if the plugin didn't load**.
- **Critical constraint:** user-invoked slash-commands/skills (e.g. `/code-review`, and thus `/dotnet-ai-kit:review`) **do NOT resolve under bare `claude -p`** — only in interactive mode or **via the GitHub Action**. So the portable CI path is the Action (`plugins:` + `prompt: /dotnet-ai-kit:review`), **not** `claude -p "/dotnet-ai.review"`.

### G.3 Subagents — the hard constraints **[verified]**
- Each subagent runs in an **isolated fresh context** (own system prompt/tools/model/permissions); it does **not** see the parent's history. **Subagents CANNOT spawn subagents** → the orchestrator must be the **main thread** (or a workflow).
- **Plugin-bundled subagents silently ignore `hooks`, `mcpServers`, and `permissionMode`** frontmatter (security). Enforce read-only via the **`tools` allowlist** (which *is* honored). Subfolders namespace them (`agents/review/security.md` → `dotnet-ai-kit:review:security`).
- A **named** subagent is targetable via the `Agent`/`Task` tool `subagent_type`, an `@agent-…` mention, or `--agent` — **but NOT as a parameter of the `Workflow` tool**. **Targeting a named/bundled subagent from a dynamic-workflow script is undocumented** (the `agent()` signature isn't published) — so assume workflow agents are defined **inline in the script**.
- Subagent results **return to and consume the parent's context** → many-result fan-outs can overflow; return **structured summaries only**, use cheaper models per dimension, or escalate to a **Workflow** (results live in script variables) for repo-wide sweeps.

### G.4 Applicability to dotnet-ai-kit
1. **Build `/dotnet-ai.review` as a main-thread orchestrator** (not a Workflow for v1, because subagents can't nest) that **fans out to read-only dimension-reviewer subagents mapped 1:1 onto the `rules/domain/` split** (`dai-review-{security,architecture,data-access,api-design,testing,naming}`). Each reviewer: `tools: Read, Grep, Glob` (read-only via allowlist), `model: sonnet`/`haiku`, **preloads its matching rule via the `skills:` frontmatter** so the rule body is *in* its context, and returns a strict `severity | file:line | rule-id | fix` summary. Then a **find → verify → synthesize** pass (a `dai-verifier` re-checks each finding against `file:line` evidence; a synthesizer dedups + ranks).
2. **Respect the plugin-subagent restrictions:** keep enforcement in the plugin's *session hooks* (not agent frontmatter); achieve read-only via `tools`, not `permissionMode`.
3. **`/dotnet-ai.verify` = the deterministic language gate** (`dotnet build` / `dotnet test` / `dotnet format --verify-no-changes` + the NetArchTest fitness project). `/review` owns judgment; `/verify` owns determinism.
4. **Ship a CI gate as a first-class artifact** via `claude-code-action@v1` (`plugins: dotnet-ai-kit` + `prompt: /dotnet-ai-kit:review`), emit `--json-schema` findings, parse `blocking_count`, `exit 1` to block (the managed review is neutral by design). Assert `system/init.plugin_errors` is empty. This is the **only** place network/model calls happen — keeping the A-011 no-network invariant on `init/check/render` intact.
5. **Reserve the `Workflow` tool for scale-out audits** (repo-wide endpoint/auth sweeps), with **inline** agent definitions (paste rule bodies into the inline prompts), gated behind the v2.1.154+/paid-plan/`disableWorkflows` reality.

---

## Sources (Part A–C; all primary/official, fetched 2026-05-30)

- Dynamic workflows: https://code.claude.com/docs/en/workflows
- Parallelism primitives / subagents: https://code.claude.com/docs/en/agents · https://code.claude.com/docs/en/sub-agents
- Plugins (no `workflows` component): https://code.claude.com/docs/en/plugins-reference · https://code.claude.com/docs/en/plugins
- Claude Code CHANGELOG (v2.1.154 introduces dynamic workflows): https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md
- Opus 4.8 announcement (2026-05-28): https://www.anthropic.com/news/claude-opus-4-8
- Memory / CLAUDE.md vs AGENTS.md: https://code.claude.com/docs/en/memory
- AGENTS.md standard: https://agents.md
- GitHub Spec Kit: https://github.com/github/spec-kit · https://github.com/github/spec-kit/blob/main/spec-driven.md
- NetArchTest.eNhancedEdition: https://www.nuget.org/packages/NetArchTest.eNhancedEdition
- ArchUnitNET: https://www.nuget.org/packages/TngTech.ArchUnitNET/ · https://github.com/TNG/ArchUnitNET/releases
- .NET code analysis (enabled rules, EnforceCodeStyleInBuild, option format): https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/overview
- Third-party (workflow JS API, unofficial): https://alexop.dev/posts/claude-code-workflows-deterministic-orchestration/

**Part D–F (Codex / Cursor / new CC features):**
- Codex: https://developers.openai.com/codex/guides/agents-md · /codex/hooks · /codex/config-reference · /codex/skills · /codex/plugins/build · /codex/subagents · /codex/cloud · /codex/agent-approvals-security · /codex/changelog
- Cursor: https://cursor.com/docs/rules · https://cursor.com/docs/hooks · https://cursor.com/changelog/1-7 · /changelog/1-0 · https://cursor.com/blog/2-0 · https://cursor.com/blog/automations · https://cursor.com/changelog
- New CC features: https://code.claude.com/docs/en/output-styles (force-for-plugin) · /settings (managed, agent key) · /permission-modes · /skills · /cli-reference · GitHub issue #38487 (path-scoped Read-not-Write, closed not-planned 2026-03-25)

**Part G (orchestration / Agent SDK / CI):**
- https://www.anthropic.com/engineering/built-multi-agent-research-system (2025-06-13) · https://code.claude.com/docs/en/code-review · /headless · /github-actions · /sub-agents · /agent-sdk/typescript · https://claude.com/blog/how-anthropic-teams-use-claude-code (2025-07-24)

---

## Cross-cutting takeaway: the three tools have converged

Claude Code, OpenAI Codex, and Cursor have all landed on the **same three-layer architecture**, which is exactly the shape of the REPORT.md fix:

| Layer | Claude Code | Codex | Cursor |
|---|---|---|---|
| **Advisory rules** | `CLAUDE.md`, `.claude/rules/`, **`force-for-plugin` output style** | `AGENTS.md` (hierarchical) | `.cursor/rules` `.mdc`, `AGENTS.md` |
| **Deterministic hooks** | PreToolUse/PostToolUse (`deny`/`exit 2`/`block`) | **Hooks** (May 2026, 1:1 clone) | **Hooks** (v1.7, Sept 2025) |
| **Orchestration** | dynamic workflows + subagents + agent teams | cloud parallel tasks + subagent fan-out | Background Agents + Composer multi-agent + Automations |

**So the kit's fix is portable:** one condensed conventions digest feeds Claude (`force-for-plugin`/SessionStart) **and** Codex (`SessionStart`/`UserPromptSubmit` hook); the same `bash-guard`/`edit-format`/content-gate logic ports to Codex hooks **and** Cursor `.cursor/hooks.json`; and the **NetArchTest + `severity=error` `.editorconfig` build gate is host-agnostic** — it gates *every* tool because the agent's own `dotnet test`/your CI runs it. None of these tools gates on test/lint failure by itself, which is precisely why the build-time gate ("violations fail the build, not just the review") remains the kit's defensible, cross-tool differentiator.
