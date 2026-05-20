# Plugin-Native Architecture — Final Report

Status: **CONFIRMED — converged by Claude (Opus 4.7, 1M context) and Codex (gpt-5.5 xhigh)**
Date: 2026-05-17
Release context: **pre-v1.0.0** — no public users, no backward-compat tax
Scope: v1.0 architecture for dotnet-ai-kit covering Claude Code, Codex CLI, Cursor, and GitHub Copilot
Predecessor: builds on token-burn-optimization (issue 018, merged in commit `63a532d`)

## How this report was produced

1. **Claude** produced initial analysis at [claude/REPORT.md](claude/REPORT.md) (703 lines, multi-source research)
2. **Codex** produced an independent position at [codex/REPORT.md](codex/REPORT.md) (703 lines) and a direct rebuttal at [discussion/round1-codex-reply.md](discussion/round1-codex-reply.md) (436 lines) with concrete file:line and URL+line citations
3. **Claude** responded at [discussion/round2-claude-reply.md](discussion/round2-claude-reply.md) accepting Codex's evidence-backed corrections and flagging 5 residual disputes
4. **Codex** signed off cleanly at [discussion/round2-codex-signoff.md](discussion/round2-codex-signoff.md) — AGREED on all 5 residuals
5. **Both AIs** produced mirrored final-merged-findings at `claude/final-merged-findings.md` and `codex/final-merged-findings.md`

This file is the executive-facing convergence. Detail lives in the two final-merged-findings files; they have identical substance and differ only in voice and ordering.

## What changed during the debate

| Topic | Claude's initial position | Codex's correction | Final converged position |
|--|--|--|--|
| Copilot custom agents | Root `AGENTS.md` | `.github/agents/*.agent.md` (verified) | `.github/agents/*.agent.md`; root `AGENTS.md` untouched (user-owned repo guidance) |
| Cursor agent support | Skip — not first-class | Cursor marketplace announces subagent packaging | Subagent spike with one fixture in v1; full generation if spike passes |
| Codex plugin compatibility | "Near-100% compatible" with Claude Code | Narrower: skills/MCP/hooks only; no native agents/LSP/monitors | v1: shared skills+MCP+hooks via `.codex-plugin/`; Codex agents excluded until docs catch up |
| Codex hooks feature flag | Required `[features].plugin_hooks = true` | Hooks now GA per May 2026 changelog | Drop the flag from v1 documentation |
| csharp-lsp migration | Add dependency, drop csharp-ls from MCP | csharp-lsp still requires csharp-ls binary on PATH | Add `dotnet-ai check` validation first; then dependency; then drop MCP entry |
| `AGENT_FRONTMATTER_MAP` | Keep universal abstraction for Copilot | Map has only Claude entries today; abstraction unjustified | Delete map; replace with explicit per-host generators backed by tests |
| Rule classification | 8 conventions / 8 domain | `performance.md`, `error-handling.md`, `naming.md` should be JIT | **5 conventions / 11 domain** (async-concurrency, coding-style, existing-projects, security, tool-calls always-on) |
| SessionStart hook transport | Concatenate 5k tokens of conventions | Defeats lazy loading; token-burn precedent | **≤500 token compact bootstrap**; convention rules referenced from skill bodies via `${CLAUDE_PLUGIN_ROOT}` paths |
| Copilot output | One large `copilot-instructions.md` + agents | Path-specific `.github/instructions/*.instructions.md` available | Split: repo-wide + path-scoped + per-agent files |
| `migrate` command design | Path-heuristic shadowed-file detection | Reuse existing manifest hash tracking | Manifest-driven via existing `cli.py:399-438` infrastructure |
| `bin/` launcher | Not addressed | Deserves spike | Spike researched; deferred to v1.1 |

## Final v1.0 architecture

### Plugin source repo layout (one repo, multi-host packaging)

```
.claude-plugin/plugin.json         # Claude Code manifest
.codex-plugin/plugin.json          # Codex manifest (skills+MCP+hooks; no agents/LSP/monitors)
.cursor-plugin/plugin.json         # Cursor manifest (skills+rules+subagent spike)

skills/                             # shared SKILL.md across Claude/Codex/Cursor
commands/                           # shared (bare names; namespaces handle resolution)
agents/                             # source-of-truth markdown bodies
agents-claude/                      # generated at build (Claude-native frontmatter)
agents-cursor/                      # generated at build (Cursor subagent format)
.github/agents-copilot-templates/   # templates for `.agent.md` generation
rules/
  conventions/                      # 5 always-on rules (referenced from skills)
  domain/                           # 11 JIT rules (referenced from relevant skills)
  profiles/                         # architecture profiles by project_type
  cursor/*.mdc                      # generated Cursor rule format
hooks/hooks.json                    # SessionStart compact bootstrap + arch-profile hook + existing 4
.mcp.json                           # codebase-memory-mcp only (after csharp-lsp lands)
plugin.json dependencies:           # csharp-lsp (paired with check binary validation)
pyproject.toml                      # updated to include .codex-plugin/ and .cursor-plugin/
```

### Per-solution files written by `init`

For Claude / Codex / Cursor users:
- `.dotnet-ai-kit/config.yml`
- `.dotnet-ai-kit/project.yml`
- `.claude/settings.json` (permissions merge only)

Additional for Copilot users:
- `.github/copilot-instructions.md` (repo-wide baseline rendered from conventions + project.yml)
- `.github/instructions/<scope>.instructions.md` (path-scoped from domain rules)
- `.github/agents/<name>.agent.md` (per-agent files)

Root `AGENTS.md` stays untouched as repo-developer guidance.

### CLI behavior changes

| Command | New behavior |
|--|--|
| `init` | Plugin tools: 3-file generator. Copilot adds `.github/*` renders. ~10 files max vs ~180 today. |
| `upgrade` | Plugin tools: near no-op (validates config schemas). `upgrade --copilot` re-renders GitHub-native files. |
| `configure` | Multi-host UI (was Claude-only). No copy step for plugin tools. |
| `check` | Validates: plugin install per configured host, `csharp-ls` binary, `project.yml` schema + detected paths, Copilot render freshness. |
| `migrate` (NEW) | Manifest-driven cleanup. Classifies clean vs user-modified. Moves clean managed files to `.dotnet-ai-kit/backups/migrate/<timestamp>/` with 3-keep rotation. Preserves user-modified files. |
| `render <skill\|rule>` (NEW) | Resolves runtime tokens against current `project.yml` and prints what Claude would see. Restores inspectability. |
| `extension-*` | Unchanged (extensions subsystem out of scope). |

### Single-PR commit order (revised from initial proposal)

Branch: `019-plugin-native-architecture` (or maintainer's choice).

1. Expand `SUPPORTED_AI_TOOLS` frozenset + multi-host config tests
2. Update `pyproject.toml` packaging to include `.codex-plugin/`, `.cursor-plugin/`
3. Add `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/` manifests
4. Claude plugin-native init (drop `.claude/commands/`, `.claude/skills/`, `.claude/agents/` copies)
5. Codex documented primitives (skills/MCP/hooks via `.codex-plugin/`)
6. Cursor rules + subagent spike (one agent fixture)
7. Copilot GitHub-native render (`.github/*.instructions.md`, `.github/agents/*.agent.md`)
8. `project.yml` JSON schema + validation
9. `check` host-specific validations including `csharp-ls` binary
10. Manifest-driven `migrate` command + backup rotation
11. `csharp-lsp` plugin dependency added (after step 9 lands)
12. Remove `csharp-ls` from `.mcp.json` (only if step 11 verified in CI)
13. New SessionStart compact bootstrap + PreToolUse runtime arch-profile hook
14. Rules reclassification (5 conventions / 11 domain) + skill body references
15. Docs, migration guide, README, planning/

## Quality impact (estimated)

| Quality lever | Direction | Magnitude |
|--|--|--|
| Skill selection accuracy in init'd Claude projects | + | 248 listed entries → 124 (namespaced only) |
| Command selection accuracy | + | 3 entries per command → 1 |
| Always-on context cost | + | ~9000 tokens → ~2500 tokens (5-rule conventions vs 16-rule) |
| Customization fidelity | + | Eliminates Jinja-staleness silent failure mode |
| Detected-paths accuracy | + | Read at invocation; survives layer renames |
| Plugin update propagation | + | `/plugin update` for Claude/Codex/Cursor; no per-repo upgrade needed |
| Inspectability | − | Mitigated by new `dotnet-ai render` command |
| Drift across team's repos | + | Eliminated for plugin tools |
| Copilot users | = | No regression; render-time staleness mitigated by `check` + `upgrade --copilot` |

## Items explicitly deferred to v1.1

- `bin/dotnet-ai` launcher (research result documented, spike pending)
- Codex native plugin agent support (revisit when Codex docs catch up)
- Cursor full subagent generation (gated on v1 spike result)
- Multi-repo activity monitor (spike justified but not bundled in v1)

## Items explicitly OUT of scope

- Extensions subsystem (maintainer direction)
- GitHub Copilot plugin support (Copilot has no plugin system; per-project render is the only path)

## Risks and mitigations

| Risk | Mitigation |
|--|--|
| Big-bang 15-commit PR is hard to review | Commit-by-commit organization; each commit independently reviewable; pre-v1.0 means no rollback drag |
| `project.yml` missing/corrupt at runtime | JSON schema validation in `check`; safe defaults in skills; clear error messages |
| `csharp-ls` binary missing after MCP removal | `check` validates binary BEFORE step 12; CI gate prevents shipping without verification |
| Cursor subagent spike fails | Documented as pending in FINAL; full generation deferred to v1.1 |
| Codex hooks feature still gated for some users | Hooks now GA per May 2026 changelog; document if any users report flag still required |
| Stale Copilot renders | `dotnet-ai check` reports freshness; `dotnet-ai upgrade --copilot` re-renders |
| Plugin update mid-session | Document `/reload-plugins` requirement; affects all hosts |

## Verification gates before merge

Three smoke tests, one per host:
1. **Claude**: drop a Claude-native agent in plugin `agents-claude/` with `agents` field in `.claude-plugin/plugin.json`. Verify `/agents` lists it as `dotnet-ai-kit:<name>`.
2. **Codex**: drop a SKILL.md in plugin `skills/`. Verify Codex CLI sees it after install.
3. **Cursor**: drop a subagent fixture in plugin per Cursor format. Verify Cursor lists it.

Plus per-host packaging tests: `pip install` from wheel must produce a working `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/` in the installed plugin directory.

## Cross-AI confirmation

| Signatory | Confirmation file |
|--|--|
| Claude (Opus 4.7, 1M context) | [claude/final-merged-findings.md](claude/final-merged-findings.md) |
| Codex (gpt-5.5 xhigh) | [codex/final-merged-findings.md](codex/final-merged-findings.md) + [discussion/round2-codex-signoff.md](discussion/round2-codex-signoff.md) |

Both files are byte-identical in substance (decisions, commit order, quality estimates, risks). They differ only in narrative voice and ordering of supporting prose. Read whichever you opened first.

## Where to find detail

- **Initial position papers**: [claude/REPORT.md](claude/REPORT.md), [codex/REPORT.md](codex/REPORT.md)
- **Round 1 challenge from Claude**: [discussion/round1-claude-to-codex.md](discussion/round1-claude-to-codex.md) (10 contestable claims C1-C10)
- **Round 1 evidence-based rebuttal from Codex**: [discussion/round1-codex-reply.md](discussion/round1-codex-reply.md) (corrections + 16 new findings)
- **Round 2 acceptance from Claude**: [discussion/round2-claude-reply.md](discussion/round2-claude-reply.md) (concessions + 5 residual disputes R1-R5)
- **Round 2 sign-off from Codex**: [discussion/round2-codex-signoff.md](discussion/round2-codex-signoff.md) (AGREED on all R1-R5)
- **This file**: executive summary for the maintainer

## Open items for the maintainer

1. Confirm scope and authorize implementation work on branch `019-plugin-native-architecture` (or chosen name).
2. Decide branch naming convention (matches existing pattern `0NN-<short-name>`).
3. Confirm `extensions` subsystem stays out of scope (already decided; flagging for re-confirmation).
4. Decide on dogfood test repos for verification gates (which sibling repos in `config.yml.repos` get used).
5. Schedule Cursor subagent spike outcome review (gates the full Cursor agent rollout vs deferral).
