# Plan Round 1 — Codex reply

## Plan critique
- Summary: REVISE. The direction is right, but the delivery summary should become PR0 + PR1 + PR2a + PR2b + PR3 + PR4 + PR5, or at least explicitly split PR2 internally. The current PR2 combines a mechanical 150+ file rewrite, deployment semantics, manifest design, and atomic rollback; that is too much review surface for one atomic PR.
- Technical Context: REVISE. `codebase-memory-mcp` should be pinned now as `>=0.6.1`, with Phase 0 re-verifying latest before PR4 opens. Also update the hook count: `hooks/post-scaffold-restore.sh` exists and is registered, so the plan's "4 hook scripts" inventory is wrong. Current line-count inventory also disagrees with the plan: commands are already under 200 lines in this checkout (`implement.md` 179, `tasks.md` 153, `clarify.md` 151), agents max at 51 lines, profiles max at 73, skills max at 330. R3/R4 should verify these numbers but not assume three over-budget commands.
- Constitution Check: REVISE, Gate V. I agree this is not a Complexity Tracking item, but it is more than a casual clarification. The constitution currently says "16 rules (always loaded)" in Technology Constraints, while PR3 intentionally changes behavior to 4 universal + 12 path-scoped. Mark the check PASS-CONDITIONAL: PR3 must include the v1.0.7 amendment in the same PR as rule scoping, and the PR should not merge before that amendment is reviewed. If PR3 lands without the amendment, it becomes a constitution violation.
- Project Structure: REVISE. Keep manifest logic in `src/dotnet_ai_kit/manifest.py`; do not also put "manifest helpers" in `config.py`. Add `src/dotnet_ai_kit/upgrade.py` as orchestrator and keep `config.py` focused on YAML config/project models. Add `tests/smoke/` plus a pytest marker for transcript/runtime tests. Add `pyproject.toml` to the touched files because the wheel `force-include` list currently does not include `.claude-plugin/`, `hooks/`, or `.mcp.json`, all of which matter for plugin packaging.
- Complexity Tracking: ADD one entry only if we adopt a real Claude Code transcript harness in PR5. The three existing entries are justified. The constitution amendment is governance, not implementation complexity. PR2 splitting reduces complexity and should not need a new table entry.
- PR1 sequencing: REVISE. Include `hooks/post-scaffold-restore.sh` in PR1 and assert it has handler-level `if:` filtering for `Bash(dotnet new *)`. Also make the `.claude/settings.json` language precise: remove duplicated static plugin safety hooks from generated/project settings, but preserve unrelated user hooks and separately classify the dynamic architecture-enforcement hook (`_source: dotnet-ai-kit-arch`) as generated project-specific state.
- PR2 sequencing: DISAGREE with one PR. Split into PR2a and PR2b. PR2a should be the frontmatter/source-template rewrite plus static tests. PR2b should be `load_project()` migration, fail-closed path substitution, manifest, and atomic `/dai.upgrade`. This keeps the mechanical diff reviewable and lets rollback logic be tested without being buried under 150 markdown changes.
- PR3 sequencing: REVISE. Include the constitution v1.0.7 amendment in PR3 and add an acceptance check that the four universal rules are the only unscoped rules and total <= 300 lines. Since current agents/profiles are already far below proposed FR-037 budgets, ratify agents <= 120 and profiles <= 100 unless Phase 0 discovers generated/deployed variants are larger than source.
- PR4 sequencing: REVISE. Pin `codebase-memory-mcp >=0.6.1` in `.mcp.json`/docs and add exact install options: Windows setup script, manual `codebase-memory-mcp-windows-amd64.zip`, and PyPI `codebase-memory-mcp==0.6.1` or `>=0.6.1`. Add explicit "do not let the upstream installer overwrite dotnet-ai-kit-managed Claude config" language.
- PR5 sequencing: REVISE. Add PR0 for baseline capture before PR1 changes. PR5 should verify deltas and CI gates, not be the first place the baseline appears.
- Rollout & Compat: REVISE. Backup location should align with existing `.dotnet-ai-kit/backups/`, not introduce `.dotnet-ai-kit/.backups/`. Also add a generated `.dotnet-ai-kit/.gitignore` or explicit docs so `backups/upgrade/` is not committed accidentally while `manifest.json`, `config.yml`, and feature files may still be project state.

## Answers to 7 open questions
Q1 MCP version research timing: Fetch now and pin now. The spec says plan phase verifies and records the concrete minimum. Use `codebase-memory-mcp >=0.6.1` as the candidate minimum because PyPI currently publishes `0.6.1`, GitHub latest is `v0.6.1`, and the release/README include Windows amd64 packaging. Phase 0 should still re-check latest before PR4 opens and record "verified on 2026-05-16" so a later security release can be considered deliberately rather than silently drifting the plan.

Q2 PR2 atomicity (sub-split or keep): Sub-split. PR2a: source frontmatter rewrite script + static frontmatter/budget tests. PR2b: `load_project()`, path-token fail-closed behavior, manifest model, and atomic upgrade. These write sets are separable enough to review independently, and PR2b is the actual risky behavior change.

Q3 Constitution amendment placement: Include it in PR3 and block PR3 until reviewed. Rule scoping and constitution semantics are the same change; a follow-up doc PR would leave the merged behavior temporarily contrary to the governing document.

Q4 Smoke test infrastructure: There is no existing Claude Code transcript/smoke pattern in this repo. Design it from scratch, but keep it opt-in: `tests/smoke/`, `pytest.mark.smoke`, skip unless `CLAUDE_CODE_SMOKE=1` and `claude` is on PATH. Include parser tests over checked-in transcript fixtures in normal CI only if they are deterministic and do not launch Claude Code.

Q5 Measurement baseline timing: Add PR0 "baseline capture only." It should add the measurement fixture, `measurements.md` baseline section, and exact command/version metadata without changing plugin behavior. That makes the baseline reviewable and prevents accidental "baseline after first fix" contamination.

Q6 Backup directory location: Use `.dotnet-ai-kit/backups/upgrade/<run_id>/`, not `.git/...`. `.git` may not exist, worktrees complicate it, and non-git projects still need rollback. The existing code/docs already use `.dotnet-ai-kit/backups/` for settings backups, so extending that namespace is cleaner. Add ignore protection for backup payloads.

Q7 MCP fallback notice format: Use a deterministic one-line notice, not a `## MCP Status` block on every command. Proposed exact line when fallback happens: `MCP unavailable: codebase-memory-mcp is not connected or below >=0.6.1; falling back to csharp-ls + grep/read.` Static tests can assert the template instructs this line; smoke tests can assert it appears exactly once only on fallback.

## Missing items
- Add `PR0 — Baseline measurement` before hook changes. Touch `measurements.md`, the measurement fixture, and optional smoke runner docs only.
- Add `hooks/post-scaffold-restore.sh` to PR1 touched files and tests. It is currently registered in `hooks/hooks.json` but omitted from the plan's hook-script inventory.
- Add `pyproject.toml` to the implementation map. The wheel `force-include` currently lists commands/rules/agents/skills/knowledge/templates/config/profiles/prompts, but not `.claude-plugin/`, `hooks/`, or `.mcp.json`.
- Add `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` checks. Official plugin docs do not show a `minimumClaudeCodeVersion` field in the current complete schema, so the plan should assume README/install-time/runtime detection rather than an unsupported manifest field unless Phase 0 finds a newer schema.
- Add tests for preserving/removing hook ownership boundaries: static plugin hooks should live in `hooks/hooks.json`; dynamic architecture-enforcement hooks in `.claude/settings.json` need an explicit exception or migration path.
- Add `copy_hook()` / architecture hook tests for handler-level `if:` or another spawn-avoidance strategy for non-.NET files. Current tests expect `matcher == "Write|Edit"` only.
- Add tests that fail if path-token substitution removes a `paths:` line on missing key. Current code removes broad/empty path lines; FR-033 requires aborting deployment.
- Add `tests/test_packaging.py` or equivalent to assert packaged assets exist under `_get_package_dir()` in wheel/dev layouts.
- Add `tests/test_mcp_config.py` for `.mcp.json` shape: preserves `csharp-ls`, adds stable `codebase-memory-mcp`, includes minimum constraint metadata if the chosen schema supports it, and does not clobber other servers.
- Add `tests/test_local_check_entrypoint.py` for `scripts/check.py` or wrapper commands. Prefer a Python `scripts/check.py` as the cross-platform source of truth, with optional `Makefile` and `scripts/check.ps1` wrappers.
- Update `tests/test_copier_skills.py`; current expectations around unresolved tokens will need to invert from "leave unchanged/remove paths" to "raise clear deployment error."
- Update `README.md` lines that say Claude Code v1.0 is fully supported; FR-005 means the lazy hook filtering behavior requires Claude Code v2.1.85+ or degrades.

## Phase 0 research findings (preview)
- https://github.com/DeusData/codebase-memory-mcp/releases — quote: "v0.6.1" / "Latest"; relevance: current GitHub latest release for the minimum pin candidate.
- https://github.com/DeusData/codebase-memory-mcp — quote: "Windows (x86_64) `codebase-memory-mcp-windows-amd64.zip`"; relevance: concrete Windows manual binary asset for docs and `/dai.init` prompt.
- https://github.com/DeusData/codebase-memory-mcp/releases/download/v0.6.1/codebase-memory-mcp-windows-amd64.zip — relevance: concrete Windows standard binary URL derived from the release assets API; use with `checksums.txt` verification in docs.
- https://pypi.org/project/codebase-memory-mcp/ — quote: "codebase-memory-mcp 0.6.1" and "pip install codebase-memory-mcp"; relevance: PyPI version pin candidate and install command.
- https://pypi.org/project/codebase-memory-mcp/ — quote: "Supported platforms ... Windows amd64"; relevance: PyPI package advertises Windows amd64 support.
- https://code.claude.com/docs/en/hooks-guide — quote: "The `if` field requires Claude Code v2.1.85 or later"; relevance: validates FR-005 minimum-version requirement.
- https://code.claude.com/docs/en/hooks-guide — quote: "the hook process only spawns when the tool call matches"; relevance: validates using handler-level `if:` for token/process savings.
- https://code.claude.com/docs/en/hooks — quote: "For most hook events, only exit code 2 blocks the action"; relevance: validates PR1 hook safety fix.
- https://code.claude.com/docs/en/plugins-reference — quote: "Complete schema" lists `name`, `version`, component paths, `dependencies`; relevance: no current documented `minimumClaudeCodeVersion` field found, so prefer docs/runtime detection.

## Open disputes for round 2
- Whether PR2 is formally split into two PR numbers (`PR2a`/`PR2b`) or kept as one named phase with two separately reviewable commits. My recommendation is formal split.
- Whether the dynamic architecture-enforcement hook in `.claude/settings.json` is an allowed exception to FR-004 or should move into plugin hook infrastructure. The plan needs one explicit answer.
- Whether `.mcp.json` can express a minimum-version constraint natively. If not, store the minimum in dotnet-ai-kit config/docs and enforce with `mcp_check.py`.
- Whether the hook scripts should stay Bash-only or move JSON parsing to a small Python entrypoint for Windows reliability. Current docs say shell form uses Git Bash on Windows or PowerShell fallback, but these scripts assume Bash syntax and `python3`.
