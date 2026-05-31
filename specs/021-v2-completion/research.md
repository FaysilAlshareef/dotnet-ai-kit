# Phase 0 Research: v2 Completion decisions

**Feature**: 021-v2-completion · **Builds on**: 020 (engine + stack already verified). Only the *new* decisions are recorded here.

## D1 — Bulk migration: deterministic script, not subagents
- **Decision**: a throwaway script (Python, dev-time) transforms v1 `skills/ commands/ rules/ agents/ profiles/ knowledge/` → `artifacts/`. Verified by `repo.Load()` Ok + `generate --check` after each batch.
- **Rationale**: consistency, zero token cost, no LLM-invented cross-references (a graph-breaking risk at 240 artifacts). The v1 frontmatter (`name`, `description`, `metadata.{category,agent}`) is already close to v2; the transform is mechanical.
- **Alternatives**: subagent fan-out (rejected for the bulk — inconsistency + graph-edge risk); hand authoring 240 (infeasible).

## D2 — v1→v2 transform rules (per artifact kind)
- **Skills**: `skills/<cat>/<name>/SKILL.md` → `artifacts/skills/<cat>/<name>/SKILL.md`; drop `when_to_use`; keep `metadata.{category,agent}`; preserve name==dir; carry `paths`/`kind`/`invocation` where applicable.
- **Commands**: `commands/<name>.md` → `artifacts/skills/commands/<name>/SKILL.md` with `metadata.kind: command` + `invocation: disable-model-invocation`.
- **Agents**: `agents/<name>.md` → `artifacts/agents/<name>.md` + `metadata.skills:` = the skills whose `metadata.agent == <name>` (reverse index); `dotnet-ai-architect` → `tests/fixtures/` (not shipped).
- **Rules**: `rules/conventions/*.md` (the 5 whitelist) → `artifacts/rules/conventions/`; `rules/domain/*.md` (11) → `artifacts/rules/domain/` with `metadata.paths`. (`rules/cursor/*.mdc` are v1 *generated projections* — ignored as source.)
- **Profiles/Knowledge**: copy bodies into `artifacts/profiles/` and `artifacts/knowledge/`.

## D3 — Consolidations done in-migration (avoid dangling edges)
- `controllers` → `controller-patterns`; `scalar` → `openapi-scalar`; `cqrs-basics` → a decision-guide. The script drops the merged source and rewrites any `agent.skills`/reference to the survivor, so the graph builds clean.

## D4 — DescriptionStandard scope
- **Decision**: hard gate for **new/structural** artifacts; **tracked metric** (count, non-failing) for **migrated** artifacts. Never weaken the standard to hide migrated gaps.
- **Rationale**: v1 descriptions have "Use when" but usually lack the "Do NOT use… use X" negative scope; failing 200 migrated artifacts at once is not actionable. New artifacts are held to the bar; migrated ones improve over time.

## D5 — Plugin ship-path
- **Decision**: `build/` is authoritative (planning/22). Generated host outputs + manifests + `marketplace.json` live under `build/`; remove the v1 root `.claude-plugin/`; one authoritative generated manifest per host. Finalize the internal `build/` layout to be a valid installable plugin.

## D6 — Python-removal parity gate
- **Decision**: remove `src/dotnet_ai_kit/` + Python tests **only** after a written parity assessment maps every v1 CLI verb/behavior to a covered .NET capability AND the acceptance suite is green. v1 verbs to map: `init`, `check`, `upgrade`, `configure`, `migrate`, `render`, `detect` (+ extension-* / learn). Gaps → retain Python + document.

## D7 — Restructure safety
- **Decision**: `grep -r` the .NET `src/`, `.specify/`, `.github/`, docs for each ambiguous dir (`templates/ bin/ scripts/ schemas/ assets/ prompts/ config/ knowledge/`) before deleting. `bin/` holds tracked source-tree wrappers (per `.gitignore`) — verify before touching. Removal of migrated v1 dirs is a **separate commit** from the migration (v1 recoverable one commit back).

## Items confirmed at implementation time
- The exact `build/` plugin layout that Claude/marketplace consume (manifest dir vs. host subdir).
- Microsoft.CodeAnalysis CodeFix testing harness vs. direct invocation (reuse 020's direct-compilation approach where possible).
