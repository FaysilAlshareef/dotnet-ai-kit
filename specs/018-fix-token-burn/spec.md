# Feature Specification: Fix Token Burn in dotnet-ai-kit Plugin

**Feature Branch**: `018-fix-token-burn`
**Created**: 2026-05-16
**Status**: Approved by both reviewers. Spec + Plan + Tasks phases all complete (Codex `READY` markers in `discussion/{spec,plan,tasks}-phase/codex-ready.txt`). Ready for `/speckit.analyze` consistency check before implementation.
**Input**: User description: "Fix token burn issues across dotnet-ai-kit Claude Code plugin: skill metadata, rule scoping, command bulk-loading, hook safety bugs, SessionStart eager-loading instruction, and make codebase-memory-mcp a required MCP server"

**Source findings**: `issues/token-burn-optimization/FINAL-REPORT.md` (18 findings agreed by Codex and Claude after 2 rounds of cross-review)

**Reviewers**: Claude (Opus 4.7, 1M context) + Codex (gpt-5.5 xhigh)

---

## Clarifications

### Session 2026-05-16

- Q: How should the generated-file manifest (FR-032) be stored? → A: Single JSON file at `.dotnet-ai-kit/manifest.json`
- Q: How should the `codebase-memory-mcp` version requirement be expressed? → A: Pin minimum (`>= x.y.z`); plan phase verifies and records the concrete minimum version. **Resolved by plan-phase R1 (2026-05-16)**: `>= 0.6.1` — see `research.md` for the verification protocol and re-verification requirement before PR4.
- Q: What should `/dai.upgrade` do on partial migration failure? → A: Stop & roll back atomically using manifest + backups; restore previous state and exit with error

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Plugin user experiences fast, low-token startup (Priority: P1)

A .NET developer installs `dotnet-ai-kit` in their solution and starts a new Claude Code session. The agent boots quickly. Background context loaded at startup is small and proportional to the developer's current file location — rules, skills, and tool surfaces unrelated to what they're touching do not occupy context space. When the developer asks for help with a controller, only API-related guidance loads. When they switch to a Cosmos repository, that context shifts automatically.

**Why this priority**: Every plugin invocation is gated by startup cost. If startup is heavy, every `/dai.*` command pays the tax. This is the single largest token-saving change available and unblocks measurement of subsequent improvements.

**Independent Test**: Run `/cost` immediately after a fresh `claude` session in a fixture project, taking the **median of 3 sessions**. Compare totals before and after fixes. A passing test shows ≥ 50% reduction in baseline session-start token usage AND the combined universal (unscoped) rule set is ≤ 300 physical lines (down from 880).

**Acceptance Scenarios**:

1. **Given** a fresh Claude Code session in a plugin-installed project, **When** the session starts, **Then** no system-reminder instructs the agent to "load skills on weak signals" or equivalent eager-loading text.
2. **Given** a fresh session, **When** the user opens a `*.cs` file under a controllers directory, **Then** API rules become available and Cosmos / queries / gateway rules do not load.
3. **Given** a fresh session, **When** the user edits a non-`.cs` file, **Then** the post-edit-format hook process does not spawn `dotnet format`.

---

### User Story 2 — Plugin's safety hooks actually block dangerous actions (Priority: P1)

A developer attempts `rm -rf` or commits without running `dotnet format`. The plugin's pre-bash-guard and pre-commit-lint hooks block the tool call at the Claude Code level — the model sees a denial and adjusts. Today these "blocking" hooks merely emit a message and exit `1`, which Claude Code treats as a non-blocking error: the dangerous command runs anyway.

**Why this priority**: This is a **safety bug**, not a token issue. It must ship in the same fix because the hook config is being rewritten anyway, and shipping the cleanup without fixing the exit code would leave the safety claim broken in production.

**Independent Test**: A test in `tests/` invokes both blocking hook scripts with a known-dangerous input and asserts they exit with code `2`. A second test parses `hooks/hooks.json` and asserts every blocking script uses blocking semantics. A smoke test (separate from CI default) drives a real Claude Code session and confirms the tool call is denied.

**Acceptance Scenarios**:

1. **Given** a developer's session, **When** the model proposes `Bash(rm -rf /)`, **Then** Claude Code blocks the call before execution and feeds the block reason back to the model.
2. **Given** a `git commit` attempt with unformatted code, **When** the pre-commit-lint hook runs, **Then** the commit is blocked and the developer sees the formatting failure.

---

### User Story 3 — Plugin author maintains lazy-loading correctness automatically (Priority: P1)

A plugin contributor opens a PR that adds a new skill. CI runs a regression test suite that catches: nested `metadata.paths`, `alwaysApply` in frontmatter, body-level `## Skills Loaded` sections in agents, "Load all skills listed" in commands, blocking hooks that exit `1`, and raw `yaml.safe_load(project_yml)` outside `load_project()`. The PR fails fast with a clear test name pointing at the offending file. The author fixes the issue and the PR goes green.

**Why this priority**: Without automated enforcement, every fix in this spec rots within weeks as new skills/rules/commands are added. The regression suite is the durability layer.

**Independent Test**: Tests split into **static checks** (pytest grep + frontmatter parse, runs on every PR), **unit tests** (Python module behaviour, runs on every PR), and **smoke tests** (Claude Code transcript fixtures, run nightly or on-demand). Land the test suites first. Force-add a violation (e.g., a new SKILL.md with `metadata.paths`); CI must fail with a name like `test_no_skill_activation_fields_under_metadata`. Revert. CI passes.

**Acceptance Scenarios**:

1. **Given** a PR that introduces a SKILL.md with `metadata.paths`, **When** CI runs, **Then** `pytest` static-check fails with a test name referencing the violation.
2. **Given** a PR that adds `exit 1` in a new blocking hook, **When** CI runs, **Then** the hook-exit-code static check fails.
3. **Given** a PR that adds "Load all skills listed" to a command body, **When** CI runs, **Then** the bulk-load static check fails.

---

### User Story 4 — Plugin uses `codebase-memory-mcp` to navigate code without reading whole files (Priority: P2)

A developer asks the agent "where is `AggregateBase` used?" The agent queries the `codebase-memory-mcp` graph for callers, gets back exact file:line locations, and reads only the relevant snippets. It does not grep the repo nor read whole files to map structure. The plugin's command templates (`detect`, `learn`, `analyze`, `plan`, `implement`, `review`, `add-tests`) instruct MCP-first discovery as a non-optional convention; `codebase-memory-mcp` is **required for full plugin functionality, and commands degrade explicitly when unavailable**. It is registered in `.mcp.json` and documented as a hard dependency in `README.md` and `commands/configure.md`.

**Why this priority**: P2 because this depends on P1 first (the eager-loading commands must stop dictating bulk reads before MCP-first behaviour can take effect). The MCP itself is straightforward to register; the lift is rewriting the seven operational commands.

**Independent Test**: With `codebase-memory-mcp` registered and indexed, ask the agent a graph-shaped question ("who calls X", "what events does Y publish to"). The agent's tool-call log shows MCP queries before any `Grep` / `Read` of full files. Without the MCP, the same question falls back gracefully with a clear "MCP unavailable — falling back to grep" message (verified via Claude Code transcript smoke test).

**Acceptance Scenarios**:

1. **Given** `.mcp.json` has `codebase-memory-mcp` registered with a pinned minimum version, **When** the plugin is freshly installed in a .NET project, **Then** `/dai.init` detects via `codebase-memory-mcp --version` and offers audited install choices; the user's response (`accepted` / `declined` / `unavailable`) is recorded in `.dotnet-ai-kit/mcp-state.yml` (sibling of `config.yml`; written outside the pydantic-validated schema to keep the config model narrow — round-3 implementation refinement).
2. **Given** the `codebase-memory-mcp` server is available, **When** the user runs `/dai.analyze`, **Then** the command body instructs the agent to query `codebase-memory-mcp` for graph/impact/architecture, use `csharp-ls` for C# symbol precision, then read only the smallest relevant snippets.
3. **Given** `codebase-memory-mcp` is unavailable (server down or not installed), **When** the user runs any operational command, **Then** the agent emits a single-line "MCP unavailable, falling back" notice and continues using `csharp-ls` + grep.
4. **Given** the plugin's `README.md`, **When** a new user reads installation steps, **Then** `codebase-memory-mcp` is listed as a required dependency with Windows PowerShell, manual zip, and PyPI install paths.

---

### User Story 5 — `project.yml` round-trips and skill `${detected_paths.*}` tokens resolve (Priority: P2)

A developer runs `/dai.init` in a CQRS microservice. Detection writes `project.yml`. The plugin then deploys skills with paths like `${detected_paths.aggregates}/**/*.cs` and rewrites these to the developer's actual aggregate directory (e.g., `src/Orders.Commands/Domain/Aggregates/**/*.cs`). Path-scoping then works — the aggregate-design skill loads only when the developer touches a file in that directory. **If a required `detected_paths.*` key is missing, deployment fails loudly rather than substituting empty strings or root-level globs.**

**Why this priority**: P2 because Stories 1 + 4 deliver value standalone, but this story is needed for skill scoping (Story 1's mechanism) to work in microservice repos with non-default directory layouts.

**Independent Test**: pytest creates a temp `DetectedProject` via `save_project()`, reads it back via `load_project()`, asserts `detected_paths` round-trips. A second pytest writes a legacy top-level YAML and asserts `load_project()` still parses it. A third pytest installs the plugin in a fixture project, asserts the deployed skill files have `paths` rewritten to concrete directories with zero `${detected_paths.` substrings remaining. A fourth pytest asserts that a fixture with a missing key causes deployment to error out (no silent broad-glob fallback).

**Acceptance Scenarios**:

1. **Given** a microservice repo with detected aggregate path `src/MyDomain.Commands/Aggregates`, **When** `/dai.init` runs, **Then** the deployed aggregate-design skill has `paths: ["src/MyDomain.Commands/Aggregates/**/*.cs"]` at top-level frontmatter (no unresolved tokens).
2. **Given** a legacy `project.yml` with top-level `detected_paths`, **When** the plugin reads it, **Then** `load_project()` returns identical data as if it were nested.
3. **Given** linked secondary repos configured in `config.yml`, **When** `/dai.implement` deploys to them, **Then** the same path resolution succeeds in each repo.
4. **Given** a `project.yml` with `detected_paths.aggregates = null`, **When** the plugin deploys aggregate-related skills, **Then** deployment fails with a clear error pointing at the missing key — it does NOT rewrite to `""` or `"**/*.cs"`.

---

### User Story 6 — Memory (`constitution.md`) does not balloon as a permanent rule (Priority: P3)

A developer runs `/dai.learn` to capture project knowledge. The output is a compact index (under 100 lines) at `.dotnet-ai-kit/memory/constitution.md` and detailed knowledge across six on-demand files: `architecture.md`, `domain-model.md`, `event-flow.md`, `interfaces.md`, `dependencies.md`, `conventions.md`. All on-demand files are loaded only when `/dai.plan` or `/dai.review` need them. The constitution is NOT registered as an always-loaded rule. No documentation tells users to make it one.

**Why this priority**: P3 because individual project constitutions vary in size and the impact is per-user. Stories 1-5 dominate the savings; this protects against re-introducing the eager-loading anti-pattern at the memory layer.

**Independent Test**: Run `/dai.learn` on a representative project. Assert `constitution.md` ≤ 100 lines, the six on-demand topic files exist, and `commands/learn.md` contains no text recommending "always-loaded rule" status. Assert `/dai.plan` reading the constitution loads only the topic file it needs, not the full set.

**Acceptance Scenarios**:

1. **Given** a developer running `/dai.learn`, **When** the command completes, **Then** the output is split into one index file (≤ 100 lines) and six on-demand topic files.
2. **Given** `commands/learn.md`, **When** read, **Then** it does not contain the phrase "always-loaded rule" or equivalent.
3. **Given** `/dai.plan` execution, **When** plan generation needs domain context, **Then** it reads only the relevant topic file (e.g., `domain-model.md`), not the full constitution.

---

### Edge Cases

- **First-time user without `codebase-memory-mcp` installed**: `/dai.init` prompts to install via a documented command (Windows PowerShell, manual zip, or PyPI). If the user declines, the plugin records `declined` in `.dotnet-ai-kit/mcp-state.yml` and operational commands fall back to grep/read without prompting again per session.
- **`codebase-memory-mcp` index stale or missing**: Plugin commands detect this (MCP returns empty graph or error) and prompt to run the MCP's reindex command; do not silently degrade.
- **Migration of existing installed projects**: A user who installed an earlier plugin version has `metadata.paths` skills and `alwaysApply` rules in their `.claude/`. `/dai.upgrade` rewrites these in place using a checksummed manifest of generated files; user-modified files are detected and backed up with warning; idempotent re-runs do nothing. **Migration is atomic** — any per-file failure triggers full rollback (FR-031).
- **Skill author writes new SKILL.md the old way**: CI catches it (Story 3). Local pre-commit hook in the plugin repo also catches it before push (FR-038).
- **Hook scripts run on a system without bash**: Existing scripts already check; no regression. PowerShell-only environments fall back to no-hook behaviour with a one-time notice during `/dai.init`.
- **Linked-repo `project.yml` missing**: Linked-repo deployment uses default `"generic"` project_type and logs a clear warning rather than silently failing skill path substitution. **Path-token substitution still fails closed (FR-033) for missing keys — token-bearing skills are skipped with a `WARNING` log, never deployed with literal `${detected_paths.` substrings.**
- **`/dai.learn` run on the same project twice**: Update mode merges; never replaces with an empty constitution.
- **User has hand-edited `.claude/settings.json`**: `/dai.upgrade` preserves unrelated user hook entries and only removes/updates dotnet-ai-kit-managed entries identified by the manifest (FR-032).
- **Claude Code older than v2.1.85**: Handler-level `if:` filter support requires v2.1.85+. Plan-phase decision: **runtime detect** via `src/dotnet_ai_kit/version_check.py` (`.claude-plugin/plugin.json` schema lacks a `minimumClaudeCodeVersion` field per `code.claude.com/docs/en/plugins-reference`). README documents v2.1.85+ recommended. When older Claude Code is detected, hooks deploy with command-pattern matchers and accept over-firing as documented degradation rather than failing install.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Group A — Hooks and startup (Phase 0 → PR 1)

- **FR-001**: The SessionStart hook script (`hooks/session-start-bootstrap.sh`) MUST emit lazy-default, MCP-first guidance and MUST NOT contain phrases like "MIGHT apply", "load it BEFORE acting", "even a small chance", or any equivalent eager-loading instruction. The replacement MUST positively assert lazy-default behaviour.
- **FR-002**: The pre-bash-guard hook script MUST exit `2` (not `1`) on its blocking branch so Claude Code actually blocks the dangerous tool call.
- **FR-003**: The pre-commit-lint hook script MUST exit `2` (not `1`) on its blocking branch.
- **FR-004**: Plugin-owned **static** hook definitions MUST live in exactly one location (the plugin manifest `hooks/hooks.json`). `.claude/settings.json` MUST NOT duplicate them. Unrelated user-authored hooks in `.claude/settings.json` MUST be preserved. **Documented exception**: dynamic per-project hooks injected by `copier.py` and identified by the `_source: dotnet-ai-kit-arch` marker MAY live in `.claude/settings.json` because they encode project-specific architecture constraints, not plugin-global behaviour. At most one such hook per project; `/dai.upgrade` rewrites its filter to use handler-level `if:` when Claude Code v2.1.85+ is detected.
- **FR-005**: Command-pattern hook filtering (`Bash(git commit*)`, `Bash(dotnet new*)`, `Edit(*.cs)`, `Write(*.cs)`) MUST be expressed in handler-level `if:` fields. The `matcher:` field MUST contain only tool names (`Bash`, `Edit|Write`, etc.). This requires Claude Code v2.1.85+ for `if:` support. **Plan-phase decision (ratified)**: runtime detect via `version_check.py`; README documents v2.1.85+ recommended; degrade gracefully (command-pattern matchers) on older versions.

#### Group B — Frontmatter correctness (Phase 1 → PR 2)

- **FR-006**: Every SKILL.md MUST place activation fields at top level of YAML frontmatter — NOT under a nested `metadata:` block. Schema constraints: `paths` is a top-level list; `when-to-use` normalises to `when_to_use`; no activation field (`paths`, `when_to_use`, `disable-model-invocation`, `user-invocable`, `alwaysApply`) remains under `metadata`.
- **FR-007**: Every SKILL.md `description` field MUST be a concrete trigger sentence ("Use when …") readable by the Claude Code skill router; descriptions that read as pure documentation MUST be rewritten. No brittle minimum-character test.
- **FR-008**: No rule file under `rules/`, no profile file under `profiles/`, and no SKILL.md MUST contain `alwaysApply:` in its frontmatter.
- **FR-009**: All raw `yaml.safe_load(project_yml...)` calls in `src/dotnet_ai_kit/cli.py` and `src/dotnet_ai_kit/copier.py` MUST be replaced with `load_project()` calls. `load_project()` MUST continue to support both nested (`detected:` key) and legacy top-level YAML formats.
- **FR-010**: After `/dai.init`, `/dai.upgrade`, or `/dai.configure` runs on a project where detection succeeded, every deployed skill file with a `paths:` token MUST have `${detected_paths.*}` substrings substituted with concrete paths. No deployed skill file MUST contain literal `${detected_paths.` substrings. **See FR-033 for the fail-closed contract on missing keys.**

#### Group C — Lazy-loading enforcement (Phase 2 → PR 3)

- **FR-011**: A whitelist of universal rules MAY remain unscoped (no `paths:`): `existing-projects.md`, `tool-calls.md`, a trimmed `coding-style.md`, a trimmed `security.md`. Every other rule MUST have a top-level `paths:` list. The four universal files combined MUST be ≤ 300 physical lines.
- **FR-012**: No file under `commands/` MUST contain the phrase "Load all skills listed" or semantically equivalent bulk-load instructions (case-insensitive, wording-tolerant matcher).
- **FR-013**: The `AGENT_FRONTMATTER_MAP` in `src/dotnet_ai_kit/agents.py` MUST NOT emit a `skills:` field derived from source agent `expertise`. `expertise` MUST remain as descriptive metadata only.
- **FR-014**: No file under `agents/` MUST contain a `## Skills Loaded` body section.
- **FR-015**: No file under `agents/` MUST contain the text "**Availability**: Always" or equivalent phrasing implying always-loaded behaviour.
- **FR-016**: Normative architecture guidance MUST live only in `architecture-profile.md`. Commands and agents MAY contain short routing pointers (e.g., "see profile for Cosmos query layer") but MUST NOT duplicate the profile's normative content.
- **FR-017**: The deployed `architecture-profile.md` MUST have a top-level `paths:` scope matching the architecture's primary code directories. It MUST NOT carry `alwaysApply:`.

#### Group D — MCP-first workflow (Phase 3 → PR 4)

- **FR-018**: `.mcp.json` MUST register `codebase-memory-mcp` alongside `csharp-ls`, using a stable server name `codebase-memory-mcp` and a **minimum-version constraint of `>= 0.6.1`** (verified against PyPI + GitHub `v0.6.1` on 2026-05-16; recorded in `research.md` R1 with a re-verification protocol before PR4 author date). Both servers are required for full plugin functionality.
- **FR-019**: `/dai.init` MUST detect whether `codebase-memory-mcp` is installed by invoking `codebase-memory-mcp --version` and comparing against the FR-018 minimum-version constraint. If absent OR below minimum, it MUST offer audited install choices (Windows PowerShell, manual zip, PyPI). It MUST record the result (`accepted` / `declined` / `unavailable` / `below-minimum`) in `.dotnet-ai-kit/mcp-state.yml` (sibling of `config.yml`; written outside the pydantic-validated schema to keep the config model narrow — round-3 implementation refinement) so the prompt is not repeated per session.
- **FR-020**: `README.md` and `commands/configure.md` MUST list `codebase-memory-mcp` as a required dependency with Windows PowerShell, manual zip, and PyPI install instructions.
- **FR-021**: The operational commands `detect`, `learn`, `analyze`, `plan`, `implement`, `review`, `add-tests` MUST contain a bounded MCP-first instruction block defining division of labor: (1) use `codebase-memory-mcp` for graph/impact/architecture; (2) use `csharp-ls` for C# symbol precision; (3) read only the smallest relevant snippets; (4) fall back to grep/file-reads when MCP is unavailable.
- **FR-022**: The operational command templates MUST instruct the agent to emit a single-line "MCP unavailable, falling back" notice when MCP is unavailable. This is verified BOTH by a static pytest (the markdown contains the instruction) AND by a Claude Code transcript smoke test (the agent actually emits it at runtime).
- **FR-023**: `commands/learn.md` MUST NOT contain the phrase "always-loaded rule" or equivalent guidance.
- **FR-024**: `/dai.learn` MUST produce a compact `constitution.md` (≤ 100 lines) plus six on-demand files: `architecture.md`, `domain-model.md`, `event-flow.md`, `interfaces.md`, `dependencies.md`, `conventions.md`. `interfaces.md` covers HTTP/gRPC/message contracts and route maps. `dependencies.md` covers NuGet packages, SDK versions, external services, infrastructure bindings. Downstream references to the monolithic constitution MUST be updated in: `skills/workflow/plan-templates/SKILL.md`, `README.md` (memory section), `commands/plan.md`, and `commands/review.md`.

#### Group E — Budgets, tests, and measurement (Phase 4 → PR 5)

- **FR-025**: Every file in `commands/` MUST be ≤ 200 physical lines.
- **FR-026**: Every file in `rules/` MUST be ≤ 100 physical lines.
- **FR-027**: Every `SKILL.md` MUST be ≤ 400 physical lines.
- **FR-028**: A pytest regression test suite MUST exist, split into three categories:
  - **Static checks** (every PR): grep / frontmatter validation for FR-001, FR-004–FR-008, FR-011–FR-017, FR-021, FR-023–FR-027, FR-033 (config validation), FR-034 (config invariants), FR-036.
  - **Unit tests** (every PR): Python module behaviour for FR-002–FR-003 (script exit codes), FR-009, FR-010 (substitution on fixture), FR-031, FR-032 (manifest round-trip), FR-033 (substitution failure modes), FR-037 (budget enforcement).
  - **Smoke / transcript tests** (nightly or on-demand): runtime behaviour for FR-018–FR-022 (MCP runtime), FR-030 (measurements), US2 hook-block-runtime, US6 selective topic-file reads.
  - Every FR MUST map to ≥ 1 test in a traceability matrix at `specs/018-fix-token-burn/traceability.md`, including FR-028 (the test framework itself, verified by CI-config schema), FR-029 (CI block-on-failure, verified by GitHub Actions config check), FR-035 (`codebase-memory-mcp` integration), and FR-038 (local pre-commit entry point).
- **FR-029**: Static + unit tests MUST run in CI on every PR and MUST block merge on failure. Smoke tests run on a designated stage (nightly or PR label), not every PR.
- **FR-030**: Before-and-after `/cost` measurements MUST be captured for: fresh-session startup (SC-001), `/dai.implement` on a 5-task feature (SC-002), `/dai.review` (SC-003), `/dai.analyze` graph-question (SC-007). Stored in `specs/018-fix-token-burn/measurements.md` with sample size, model version, and fixture description.
- **FR-031**: `/dai.upgrade` MUST migrate existing dotnet-ai-kit-deployed rules, profiles, agents, skills, commands, and hook config from the legacy loading model to the new one. It MUST be **atomic**: on any failure during migration, all changes from the current run MUST be rolled back using the manifest (FR-032) and per-file backups, the project MUST be restored to its pre-run state, and the command MUST exit with a non-zero status reporting the failing file and reason. It MUST be idempotent, preserve non-Claude metadata, avoid rewriting user-authored files outside known managed paths, and support `--dry-run` reporting.
- **FR-032**: Deployed files MUST be version-stamped and tracked in a single JSON manifest at `.dotnet-ai-kit/manifest.json`. The manifest MUST contain, at minimum: deployed file path (relative to project root), SHA-256 checksum of the deployed file, plugin version that deployed it, and a timestamp. Upgrade MUST use the manifest to distinguish generated files from user-modified files; ambiguous files require backup-plus-warning or explicit `--force`.
- **FR-033**: Path-token resolution MUST fail closed at the SKILL.md level. Missing `${detected_paths.*}` keys MUST produce a clear warning/error and MUST NOT rewrite to empty strings, repository-root globs (`**/*.cs`), or broader-than-intended paths. **Implementation refinement (round-3 codex review, 2026-05-16)**: "fail closed" is enforced *per skill*, not per deploy. `copy_skills` MUST skip any SKILL.md whose tokens cannot resolve (either because `detected_paths` is empty or because a key is missing) and emit a `WARNING` log naming the skipped file and missing key(s); it MUST NOT deploy that file with a literal `${detected_paths.` substring. The directly-callable `_resolve_detected_path_tokens` still raises `DeploymentError`. This balances the fail-closed contract against the legitimate case of a command service that doesn't populate `cosmos_entities`.
- **FR-034**: Hook correctness invariants MUST be asserted: blocking PreToolUse hooks use `exit 2` with stderr or valid JSON deny on exit 0; no blocking hook exits `1`; handler-level `if` filters are present for command/file patterns; PostToolUse format hooks do not spawn for non-C# Edit/Write calls; generated hook config preserves unrelated user hooks.
- **FR-035**: `codebase-memory-mcp` integration MUST enforce a minimum-version constraint (per FR-018), register the server with a stable name (`codebase-memory-mcp`), document Windows PowerShell / manual zip / PyPI install paths, and avoid clobbering existing MCP servers or dotnet-ai-kit-managed hooks/instructions.
- **FR-036**: Rules MUST be pruned to compact hard policy after path scoping. Detailed examples, tables, and recipes that duplicate skills MUST move to skills or be removed from rules. Covers F18.
- **FR-037**: Agent and profile budgets ratified by plan phase R4 (current largest agent ~51 lines, largest profile ~73 lines — both well below the ratified ceiling): **agents ≤ 120 physical lines, profiles ≤ 100 physical lines**. The regression test (`test_budgets.py`) enforces these.
- **FR-038**: The plugin repo MUST include a local pre-commit/static check entry point (e.g., `make check` or a pre-commit hook config) that runs the same token-burn anti-pattern checks as CI, so contributors catch violations before pushing.

### Key Entities

- **DetectedProject** (existing): The pydantic model in `src/dotnet_ai_kit/models.py` holding `project_type`, `confidence`, `detected_paths`. Round-trips through `save_project()`/`load_project()` after this fix.
- **Skill frontmatter (revised)**: Top-level keys `name`, `description`, `when_to_use`, `paths`, `disable-model-invocation`, `user-invocable`. Nested `metadata:` may persist for non-Claude tool consumers (Cursor `category`, internal routing) but contains no Claude-visible activation fields.
- **Rule frontmatter (revised)**: Top-level `description` and optional `paths:`. No `alwaysApply` field.
- **Hook registration (revised)**: `matcher` contains tool names only; `if` contains permission-rule-style filters; blocking branches exit `2`.
- **MCP registry (`.mcp.json`)**: Two required servers — `csharp-ls` (existing, symbol precision) and `codebase-memory-mcp` (new, graph/impact/architecture).
- **Memory layout (revised)**: `.dotnet-ai-kit/memory/constitution.md` is an index; six on-demand files (`architecture.md`, `domain-model.md`, `event-flow.md`, `interfaces.md`, `dependencies.md`, `conventions.md`) hold detail.
- **Generated-file manifest (new)**: Single JSON file at `.dotnet-ai-kit/manifest.json` listing every file dotnet-ai-kit deploys, with fields: relative path, SHA-256 checksum, plugin version, deployment timestamp. Drives idempotent upgrade detection (FR-031, FR-032).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

**Token-reduction targets (SC-001 / SC-002 / SC-003)** are recorded as **measured targets**. **Plan-phase ratification**: hard release gates are the binary safety/correctness SCs (SC-004, SC-005, SC-006, SC-013, SC-014, SC-015, SC-016); SC-001/002/003 remain measured targets ratified against actual baseline (PR0) — soft regressions flagged as PR-blocking warnings, not auto-fails. All measurements are medians of ≥ 3 runs on the same fixture, model, and project.

- **SC-001**: Baseline session-start token usage on a representative installed fixture drops by **at least 50%** vs. pre-fix baseline (median of 3 fresh `/cost` reads, no commands issued). Universal (unscoped) rules combined ≤ 300 physical lines.
- **SC-002**: `/dai.implement` on a 5-task feature consumes **at least 35% fewer tokens** vs. pre-fix baseline (median of 3 runs, identical fixture and outcomes).
- **SC-003**: `/dai.review` on the same feature consumes **at least 30% fewer tokens** vs. pre-fix baseline.
- **SC-004**: Pre-bash-guard blocks `rm -rf /` in a smoke test — the model receives a denial, not just stderr output.
- **SC-005**: Pre-commit-lint blocks a `git commit` with unformatted code. CI uses a minimal mocked-formatter fixture for speed; full `dotnet format` reserved for opt-in smoke tests.
- **SC-006**: After `/dai.init` on a fixture microservice repo with non-default directory layout, **100% of deployed skills** have `${detected_paths.*}` tokens substituted with concrete paths. Grep for literal `${detected_paths.` returns zero matches.
- **SC-007**: For a representative graph-shaped question ("who calls `AggregateBase.ApplyChange`"), `/dai.analyze` consumes **≤ 30% the tokens** of the pre-fix baseline when `codebase-memory-mcp` is available. **Answer-quality parity is required** (same correct answer). Measurement excludes MCP indexing time/tokens.
- **SC-008**: When `codebase-memory-mcp` is unavailable, the same question still completes successfully via fallback and emits the documented one-line fallback notice exactly once.
- **SC-009**: Static + unit pytest runs in **≤ 30 seconds** end-to-end. Smoke/transcript tests are opt-in or nightly, not part of this budget.
- **SC-010**: Each of the 17 testable findings (F01–F14, F16, F17, F18 — F15 excluded as roadmap-only sequencing recommendation) maps to ≥ 1 test in `specs/018-fix-token-burn/traceability.md`. Force-introducing each violation class causes a named pytest to fail with an unambiguous file pointer.
- **SC-011**: After this feature ships, every file in `commands/`, `rules/`, `agents/`, `skills/`, `profiles/` passes the budget checks (FR-025, FR-026, FR-027, FR-037).
- **SC-012**: `/dai.learn` on a fixture project produces `constitution.md` ≤ 100 physical lines, plus the six on-demand files. `/dai.plan` and `/dai.review` read only the topic file they need, not the full set.
- **SC-013**: `/dai.upgrade` is idempotent AND atomic. (a) A second run on a freshly-upgraded project produces zero file changes (verified by `git diff` post-run). (b) A simulated mid-run failure (e.g., write error on file N/M) causes a complete rollback to the pre-run state — verified by comparing SHA-256 of all managed files before run vs. after failed run.
- **SC-014**: `codebase-memory-mcp --version` detection succeeds on a Windows fixture; the result is recorded in `.dotnet-ai-kit/mcp-state.yml` (sibling of `config.yml`; written outside the pydantic-validated schema to keep the config model narrow — round-3 implementation refinement) and reproducible across re-runs.
- **SC-015**: Post-edit format hook does not spawn `dotnet format` on a non-`.cs` Edit/Write (verified by hook-invocation log on a fixture with `.md` and `.cs` edits).
- **SC-016**: Path-token substitution fails closed — a fixture with `detected_paths.aggregates = null` causes deployment to abort with a clear error pointing at the missing key. Deployment does NOT produce skill files with empty or root-level globs.

---

## Out of Scope

- Building a custom Roslyn MCP server. Deferred until after Phases 0–3 are measured and remaining gaps are specifically CQRS/event-flow shaped (F15).
- Migrating dotnet-ai-kit to support Cursor or GitHub Copilot. `metadata:` survives for that future use; no new behaviour added.
- Rewriting individual SKILL.md to be shorter than 400 lines beyond fixing budget violations. Content quality is a separate effort.
- Changing `/dai.do`'s overall lifecycle. Only the skill/agent loading inside it changes.
- Replacing `csharp-ls` with another C# MCP. It stays.

---

## Assumptions

- `codebase-memory-mcp` is a real, installable MCP server with Windows amd64 binary, PyPI package, and stdio MCP registry presence. Verified via web research in round 1 (see `discussion/spec-phase/round1-codex-reply.md` web research section).
- Plugin maintainers accept a CI-time addition of ≤ 30s for static + unit tests; smoke/transcript tests run nightly.
- Token-reduction targets (50% / 35% / 30%) are plausible based on the agreed findings; PR0 baseline + PR5 post-fix measurement confirms or revises (soft warning, not auto-fail).
- `csharp-ls` stays as the symbol-navigation MCP; `codebase-memory-mcp` covers graph/architecture.
- Existing installed projects can be migrated via `/dai.upgrade` with manifest + checksums (FR-031, FR-032).
- "User lacks `codebase-memory-mcp`" is tolerable as fallback-with-notice, not a hard plugin block.
- Claude Code v2.1.85+ provides handler-level `if:` field support; **plan-phase chose runtime detect** (no manifest pin field exists).

---

## Dependencies

- `codebase-memory-mcp` (external, GitHub `DeusData/codebase-memory-mcp`).
- `csharp-ls` (already configured).
- Claude Code v2.1.85+ for handler-level `if:` hook filters.
- pydantic v2, pyyaml, typer, jinja2, rich (already in `pyproject.toml`).
- pytest, pytest-cov, ruff (already in `[dev]` extras).

---

## Phased Delivery

Single feature branch `018-fix-token-burn` with **7 PRs** (refined during plan-phase round 2; PR2 sub-split to keep mechanical frontmatter rewrite reviewable separately from atomic upgrade logic):

- **PR 0** — Baseline measurement only. Adds fixture project + `measurements.md` baseline section. No plugin behaviour changes. Captures `/cost` baselines for SC-001, SC-002, SC-003, SC-007.
- **PR 1** (Phase 0): hooks/startup safety — FR-001 through FR-005, FR-034. Includes 5 hook scripts (`pre-bash-guard`, `pre-commit-lint`, `post-edit-format`, `post-scaffold-restore`, `session-start-bootstrap`) and `pyproject.toml` force-include update. US1 + US2 acceptance, SC-004, SC-005, SC-015.
- **PR 2a** (Phase 1, part 1): mechanical frontmatter rewrite — FR-006, FR-007, FR-008, FR-014, FR-015, FR-017. 124 SKILL.md + 16 rules + 12 profiles + 13 agents.
- **PR 2b** (Phase 1, part 2): data-flow + atomic upgrade — FR-009, FR-010, FR-031, FR-032, FR-033. New `manifest.py` + `upgrade.py`; US5; SC-006, SC-013, SC-016.
- **PR 3** (Phase 2): rule/profile/agent/command lazy-loading cleanup + constitution v1.0.7 amendment — FR-011, FR-012, FR-013, FR-016, FR-025, FR-036, FR-037; SC-011.
- **PR 4** (Phase 3): MCP/memory docs + command guidance — FR-018 through FR-024, FR-035; US4 + US6; SC-007, SC-008, SC-012, SC-014.
- **PR 5** (Phase 4): measurements + final CI gates + local-check entry point — FR-025 through FR-030, FR-038; US3; SC-001, SC-002, SC-003, SC-009, SC-010.

See `plan.md` "PR-by-PR Implementation Map" for the canonical sequencing, file touch lists, and acceptance criteria.

---

## Round Tracking

### Spec phase
- [x] Round 1 Claude draft → Codex critique (8 new FRs accepted)
- [x] Round 2 Claude reconciliation → Codex `READY` 2026-05-16

### Clarify phase
- [x] 3 questions answered (manifest format, MCP version constraint shape, upgrade partial-failure semantics) — encoded in `## Clarifications` above

### Plan phase
- [x] Round 1 Claude draft → Codex critique (8 new FRs, PR sub-split, hook inventory fix, packaging gap)
- [x] Round 2 Claude reconciliation → Codex round 3 (2 narrow gaps) → Claude fixes → Codex `READY` 2026-05-16

### Tasks phase
- [x] Round 1 Claude draft (93 tasks) → Codex critique (17 missing, 4 [P] conflicts, T047 mis-phased, T022 brittle)
- [x] Round 2 Claude reconciliation (~110 tasks) → Codex round 3 (3 mechanical) → fixes → Codex round 4 (3 bookkeeping) → fixes → Codex `READY` 2026-05-16

### Auto-clarify pass (this session)
- [x] Stale plan-deferral language in FR-005, FR-018, FR-024, FR-037, SC intro, Edge cases, Assumptions auto-fixed to reflect ratified plan-phase decisions

## Reviewer Sign-off

- ✅ Codex (gpt-5.5 xhigh) — `READY` on spec, plan, and tasks phases
- ✅ Claude (Opus 4.7, 1M context) — all phase reconciliations complete
