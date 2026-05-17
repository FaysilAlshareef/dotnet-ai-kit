# Spec Round 1 — Codex reply

## Spec critique

User stories:

- **US1: REVISE.** The goal is right, but the independent test mixes a percentage goal with an always-loaded rule ceiling that is too loose: `spec.md:20` says "<= 9k tokens" even though the final report says current rules are already about 9k tokens (`issues/token-burn-optimization/FINAL-REPORT.md:52`). Tighten this to a physical-line or token ceiling for the trimmed universal rule set, and measure startup as a median of repeated fresh sessions.
- **US2: AGREE.** This is a real safety bug and belongs in the same feature. The story correctly treats `exit 1` vs `exit 2` as behavioral correctness, not just token burn (`spec.md:30-41`, `issues/token-burn-optimization/codex/final-merged-findings.md:82-95`).
- **US3: REVISE.** The regression durability story is necessary, but it should separate static repo checks from smoke/integration checks. The checklist says every FR is testable (`checklists/requirements.md:17`), but FR-022 and several runtime MCP behaviors cannot be proven by plain pytest without a harness.
- **US4: REVISE.** `codebase-memory-mcp` is real, installable on Windows, and viable enough to standardize on, but the wording "required" plus "fallback gracefully" is contradictory. Phrase it as "required for full plugin functionality; commands degrade explicitly when unavailable." Also, do not let its installer own `.claude` config if dotnet-ai-kit also manages hooks and instructions.
- **US5: AGREE.** This story directly addresses F04/F05 and should stay. Add a failure rule: missing `${detected_paths.*}` keys must not rewrite to empty or broad globs, because current token replacement can otherwise hide a bad detection result.
- **US6: REVISE.** The memory split is the right direction, but the four-file list is incomplete for .NET microservices. Add `dependencies.md` and `interfaces.md` or make explicit where packages, external services, HTTP/gRPC routes, and public contracts live. Also update downstream references in `skills/workflow/plan-templates/SKILL.md` noted in F13 (`issues/token-burn-optimization/codex/final-merged-findings.md:260-273`).

Functional requirements:

- **FR-001: AGREE.** Covers F01 and should explicitly test both forbidden phrases and the positive lazy/MCP default (`spec.md:128`, `issues/token-burn-optimization/codex/final-merged-findings.md:66-80`).
- **FR-002: AGREE.** Correct for `pre-bash-guard`.
- **FR-003: AGREE.** Correct for `pre-commit-lint`.
- **FR-004: REVISE.** "Exactly one location" is right for plugin-owned hook definitions, but clarify that generated `.claude/settings.json` must preserve unrelated user hooks and only remove dotnet-ai-kit duplicates.
- **FR-005: REVISE.** Correct shape, but add a Claude Code minimum version if relying on handler-level `if:`. Official docs say `if` requires Claude Code v2.1.85 or later.
- **FR-006: REVISE.** Add schema-level constraints: `paths` must be a top-level list, `when-to-use` must normalize to `when_to_use`, and no activation field may remain under `metadata`.
- **FR-007: AGREE.** Good requirement; avoid brittle tests like minimum description length.
- **FR-008: AGREE.** Covers rules, profiles, and skills.
- **FR-009: AGREE.** Correct data-flow fix for F04.
- **FR-010: REVISE.** This covers token substitution but not the on-disk legacy skill frontmatter rewrite during `/dai.upgrade`. Add a separate upgrade-migration FR.
- **FR-011: REVISE.** The universal whitelist is reasonable only if the four files are actually trimmed. Add a line/size sub-budget for unscoped rules.
- **FR-012: AGREE.** Keep "semantically equivalent" so casing or wording changes do not bypass the test.
- **FR-013: AGREE.** Covers F09.
- **FR-014: AGREE.** Covers F10.
- **FR-015: AGREE.** Covers F11.
- **FR-016: REVISE.** "Exactly one place" is too strict if commands contain short routing hints. Say normative architecture guidance lives only in `architecture-profile.md`; commands/agents may contain short pointers.
- **FR-017: AGREE.** Necessary for profiles after removing `alwaysApply`.
- **FR-018: REVISE.** Make `codebase-memory-mcp` required for full functionality, but allow degraded command execution. Also require a minimum verified version and a stable server name in `.mcp.json`.
- **FR-019: REVISE.** Do not auto-run a remote install silently. Detect `codebase-memory-mcp --version`, offer audited install choices, and record `accepted`, `declined`, or `unavailable` in config.
- **FR-020: AGREE.** Documentation must include Windows PowerShell/manual zip/PyPI paths.
- **FR-021: REVISE.** The block should define division of labor: use `codebase-memory-mcp` for graph/impact/architecture; use `csharp-ls` for C# symbol precision; then read smallest snippets.
- **FR-022: REVISE.** Command markdown can instruct the agent to emit a fallback notice, but pytest cannot guarantee runtime behavior. Either make this a command-template assertion or define a Claude Code transcript smoke test.
- **FR-023: AGREE.** Covers F13 prose.
- **FR-024: REVISE.** Add `dependencies.md` and `interfaces.md`, or explicitly fold those topics into the four files.
- **FR-025: AGREE.** Matches repo convention (`AGENTS.md:66`).
- **FR-026: AGREE.** Matches repo convention.
- **FR-027: AGREE.** Matches repo convention.
- **FR-028: REVISE.** "FR-001 through FR-027" is too broad for one pytest suite. Split static checks, unit tests, and manual/smoke measurements, and require a traceability matrix.
- **FR-029: AGREE.** CI must block static regressions.
- **FR-030: REVISE.** Add fresh-session startup and `/dai.analyze` graph-question measurements; `spec.md:169` currently omits SC-001 and SC-007 measurement artifacts.
- **MISSING:** upgrade migration of existing installed files, Windows MCP install verification, no empty-glob token substitution, explicit rule/skill duplication pruning (F18), agent/profile budget definitions, and local pre-commit enforcement promised by the edge case at `spec.md:115`.

Success criteria:

- **SC-001: REVISE.** Keep 50%, but measure median of 3+ fresh sessions on the same fixture and tighten the universal-rule ceiling below today's 880 physical lines.
- **SC-002: REVISE.** 35% is plausible as a target, but make it a measured success target with same model/project/task and same acceptance output. Do not make it the only release gate until baseline variance is known.
- **SC-003: AGREE.** 30% review reduction is realistic because reviewer agent/skill bulk-loading is a large part of current cost.
- **SC-004: AGREE.** Must prove the tool call is denied, not just that the script prints "blocked".
- **SC-005: REVISE.** Good, but use a small fixture or mocked formatter path so CI is stable and fast; reserve full `dotnet format` for smoke tests.
- **SC-006: AGREE.** Strong and testable.
- **SC-007: REVISE.** The 70% reduction is plausible for graph-shaped questions, but require answer-quality parity and define whether MCP indexing tokens/time are excluded from the query measurement.
- **SC-008: AGREE.** Required because "required MCP" still has runtime failure modes.
- **SC-009: REVISE.** Limit the <=30s target to static/unit pytest. MCP install/index smoke tests should be opt-in or nightly.
- **SC-010: REVISE.** "Each of the 18 findings" is too broad unless every finding has a mapped violation class. F15 is roadmap sequencing; F18 is duplication quality. Add an explicit finding-to-test matrix.
- **SC-011: REVISE.** It mentions agents and profiles but FR-025/026/027 define budgets only for commands/rules/skills. Either define agent/profile budgets or remove them here.
- **SC-012: REVISE.** Expand if FR-024 expands, and require `/dai.plan`/`/dai.review` to read only the topic file they need.
- **MISSING:** success criteria for `/dai.upgrade` idempotent migration, Windows `codebase-memory-mcp` install verification, no unresolved or empty path globs after deployment, and post-edit hook non-C# no-spawn behavior.

The checklist is mostly fair, but I would change "requirements are testable and unambiguous" from checked to partial (`checklists/requirements.md:17`) until FR-022, FR-028, SC-010, and SC-011 are tightened.

## Answers to the 5 open questions

1. **codebase-memory-mcp required vs optional:** Agree with "required for full functionality," not "hard block all commands." Web research verifies it is real, has a GitHub repo, a current release, Windows amd64 artifacts, PyPI packaging, and stdio MCP registry presence. The spec should keep fallback because MCP servers are local tools that can be missing, blocked by policy, stale, or temporarily broken. Implementation guidance: dotnet-ai-kit should own the `.mcp.json` entry and its own hooks; use `codebase-memory-mcp` binary-only/manual install paths or `--skip-config` so its installer does not inject competing Claude hooks/instructions.

2. **Token-reduction targets (50% / 35% / 30%):** Keep them for Round 2, but make the measurement protocol precise. 50% startup is realistic if SessionStart eager-loading and unscoped rules are fixed. 35% implement is plausible but depends on how much of the 5-task fixture is exploration vs editing/build output. 30% review is realistic because current review eagerly loads reviewer skills (`issues/token-burn-optimization/codex/final-merged-findings.md:181-197`, `issues/token-burn-optimization/codex/final-merged-findings.md:213-228`). For graph-only questions, the codebase-memory evidence supports larger reductions, but whole-command workflows should be measured before making 35% a hard ship gate.

3. **Memory file split -- complete list?** Not complete. Use six on-demand files: `architecture.md`, `domain-model.md`, `event-flow.md`, `interfaces.md`, `dependencies.md`, and `conventions.md`. `interfaces.md` covers HTTP/gRPC/message contracts and route maps; `dependencies.md` covers NuGet packages, SDK versions, external services, and infrastructure bindings. Do not add `patterns.md`; that overlaps `conventions.md` and skills.

4. **One-shot vs phased PR delivery:** Use phased PRs under one feature branch/spec. PR 1: hooks/startup safety. PR 2: frontmatter, `load_project()`, upgrade migration. PR 3: rule/profile/agent/command lazy-loading cleanup. PR 4: MCP/memory docs and command guidance. PR 5: measurement hardening and final CI gates if not already included per PR. A single mega-PR would mix safety fixes, 124 skill rewrites, command rewrites, and MCP installation semantics in one review.

5. **/dai.upgrade migration safety:** In-place rewrite is safe only for files known to be generated by dotnet-ai-kit. Add version stamping plus a generated-file manifest with paths and checksums going forward. For legacy installs without checksums, migrate known dotnet-ai-kit paths conservatively, preserve non-Claude `metadata`, write a backup or dry-run diff when a file appears user-modified, and make repeated `/dai.upgrade` runs no-op. Do not rewrite arbitrary user-authored `.claude/skills` unless the user opts in.

## New requirements (if any)

- **FR-031:** `/dai.upgrade` MUST migrate existing dotnet-ai-kit-deployed rules, profiles, agents, skills, commands, and hook config from the legacy loading model to the new one. It MUST be idempotent, preserve non-Claude metadata, avoid rewriting user-authored files outside known managed paths, and support `--dry-run` reporting.
- **FR-032:** Deployed files MUST be version-stamped and tracked in a generated-file manifest with checksums where possible. Upgrade MUST use the manifest to distinguish generated files from user-modified files; ambiguous files require backup-plus-warning or explicit `--force`.
- **FR-033:** Path-token resolution MUST fail closed. Missing `${detected_paths.*}` keys MUST produce a clear warning/error and MUST NOT rewrite to empty strings, repository-root globs, or broader-than-intended paths.
- **FR-034:** Hook correctness tests MUST assert these invariants: blocking PreToolUse hooks use `exit 2` with stderr or valid JSON deny on exit 0; no blocking hook exits `1`; handler-level `if` filters are present for command/file patterns; PostToolUse format hooks do not spawn for non-C# Edit/Write calls; generated hook config preserves unrelated user hooks.
- **FR-035:** `codebase-memory-mcp` integration MUST verify a minimum supported version, register the server with a stable name, document Windows PowerShell/manual zip/PyPI install paths, and avoid clobbering existing MCP servers or dotnet-ai-kit-managed hooks/instructions.
- **FR-036:** Rules MUST be pruned to compact hard policy after path scoping. Detailed examples, tables, and recipes that duplicate skills MUST move to skills or be removed from rules. This explicitly covers F18.
- **FR-037:** Agent and profile budgets MUST be defined if SC-011 keeps agents/profiles in scope. Suggested starting point: agents <= 120 physical lines and profiles <= 100 physical lines unless plan-phase counts justify different numbers.
- **FR-038:** The plugin repo SHOULD include a local pre-commit/static check entry point that runs the same token-burn anti-pattern checks as CI, because the edge case at `spec.md:115` promises local catch-before-push behavior.

## Web research findings

- https://github.com/DeusData/codebase-memory-mcp -- quoted line: "single static binary for macOS, Linux, and Windows" -- relevance: confirms the project exists and claims cross-platform binary distribution.
- https://github.com/DeusData/codebase-memory-mcp/releases -- quoted line: "`codebase-memory-mcp-windows-amd64.exe`" -- relevance: confirms a Windows amd64 release artifact exists in the release page.
- https://pypi.org/project/codebase-memory-mcp/ -- quoted line: "`pip install codebase-memory-mcp`" -- relevance: confirms a Python install path useful for dotnet-ai-kit users already using Python tooling.
- https://pypi.org/project/codebase-memory-mcp/ -- quoted line: "Windows amd64" -- relevance: confirms PyPI metadata lists Windows amd64 as a supported platform.
- https://mcpbench.ai/servers/io.github.DeusData/codebase-memory-mcp -- quoted line: "Transport stdio" -- relevance: confirms the server is represented as a stdio MCP package in a registry-derived catalog.
- https://ar5iv.labs.arxiv.org/html/2603.27277v1 -- quoted line: "ten times fewer tokens" -- relevance: supports the plausibility of large reductions for graph-shaped exploration, with the caveat that this is a preprint tied to the project.
- https://code.claude.com/docs/en/hooks -- quoted line: "only exit code 2 blocks" -- relevance: validates the hook-exit-code safety requirement.
- https://code.claude.com/docs/en/hooks-guide -- quoted line: "`if` field requires Claude Code v2.1.85" -- relevance: the spec should add a minimum Claude Code version or fallback for handler-level `if:` filters.
- https://marketplace.visualstudio.com/items?itemName=tunakite03.codebase-memory-mcp -- quoted line: "pre-built binary for Windows x64" -- relevance: independent ecosystem signal that Windows packaging is practical, though not necessary for Claude Code.

## Open disputes for round 2

- Required MCP wording: "required for full functionality" vs "required and command-blocking."
- Whether dotnet-ai-kit should invoke `codebase-memory-mcp install` or only install/register the binary itself to avoid config/hook ownership conflicts.
- Whether token targets are release gates or success targets that can be revised after baseline measurement.
- Final memory topic filenames, especially `interfaces.md` and `dependencies.md`.
- Agent/profile budget numbers.
- Minimum Claude Code version for hook `if:` support.
- Exact `/dai.upgrade` migration policy for legacy files that users have edited after install.
