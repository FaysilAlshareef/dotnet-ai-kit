# Contract: Projection (FR-008 / FR-009 / FR-010 / FR-011)

The projection engine renders the authored `artifacts/` tree into each host's native shape. One `IHostAdapter`/projector per host.

## Per-host output shapes

| Artifact | Claude | Codex | Cursor | Copilot (cloud render) |
|---|---|---|---|---|
| Skill | `build/claude/skills/<name>/SKILL.md` (+resources) | `build/codex/skills/<name>/SKILL.md` | `build/cursor/skills/<name>/SKILL.md` | (referenced from instructions) |
| Agent | `build/claude/agents/<name>.md` | `build/codex/agents/<name>.toml` (+`AGENTS.md`) | `build/cursor/...` (md) | `.github/agents/<name>.agent.md` |
| Rule (universal) | `build/claude/rules/<name>.md` | `AGENTS.md` (aggregated) | `build/cursor/rules/<name>.mdc` (`alwaysApply`) | `.github/copilot-instructions.md` |
| Rule (domain) | `build/claude/rules/<name>.md` + `paths:` | `AGENTS.md` | `build/cursor/rules/<name>.mdc` (`globs`) | `.github/instructions/<name>.instructions.md` (`applyTo`) |
| Command-skill | merged into skills (Claude commands→skills) | skill | `build/cursor/commands/<name>.md` | `.github/prompts/<name>.prompt.md` |
| Manifest | `build/.claude-plugin/plugin.json` | `build/.codex-plugin/plugin.json` (no `agents`) | `build/.cursor-plugin/plugin.json` (`agents`) | reuses `.claude-plugin/plugin.json` (auto-detect) |

## Invariants
1. **Frontmatter translation** — `x-<host>` blocks are stripped/translated so each emitted file carries only fields its host understands (FR-004). Claude-only fields (`disable-model-invocation`, `paths`, `user-invocable`) never leak to other hosts.
2. **Deterministic & idempotent** — stable key ordering, no timestamps, fixed newline; repeated runs are byte-identical (FR-011).
3. **One descriptor → all manifests** — every `plugin.json` is rendered from the single `manifest.yml`; auto-discovered keys (`hooks`/`mcpServers`/`lspServers`) are absent (FR-010).
4. **Drift gate** — `generate` writes every host output + manifests in one pass; `git diff --exit-code` is green on a clean checkout; deleting a generated file and regenerating restores it byte-identically (FR-009 / SC-001).
5. **Broken-edge fail-fast** — a reference to a non-existent artifact fails generation before any file is written (FR-006).

## Golden-output tests (Verify)
Each artifact × host projection is snapshotted (`*.verified.*`). First authoring is red (`*.received.*`) until baselines are accepted and committed — expected, not a failure. Drift fails CI (SC-008).
