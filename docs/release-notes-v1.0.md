# Release Notes — dotnet-ai-kit v1.0 (Plugin-Native Architecture)

**Feature**: 019-plugin-native-arch
**Branch**: `019-plugin-native-arch`
**Spec**: [specs/019-plugin-native-arch/spec.md](../specs/019-plugin-native-arch/spec.md)
**Date**: 2026-05-18

## TL;DR

v1.0 moves dotnet-ai-kit to a **plugin-native architecture**. The per-solution
file footprint drops from ~180 files to a small fixed set (config.yml,
project.yml, manifest.json, settings.json). The same plugin source serves
multiple solutions: update once, all solutions see the new behavior on next
AI session.

Four hosts are now first-class:
- **Claude Code** — plugin-native (full feature parity)
- **Codex CLI** — plugin-native (skills + MCP + hooks; native agents
  deferred to v1.1)
- **Cursor** — plugin-native (rules + skills + MCP + hooks; sub-agents
  conditional on the A-005 spike fixture)
- **GitHub Copilot** — render-only via `.github/*.md` files

## Highlights

### `dotnet-ai check` validation command (FR-017)

Single command verifies plugin install per host, `csharp-ls` binary on PATH,
`project.yml` schema, detected paths, `manifest.json` integrity, and Copilot
render freshness. Exit codes uniquely identify the failing check class
(10/11/12/13/14/15/16/99). Runs in under 10 seconds.

### `dotnet-ai migrate` for safe upgrades (US4)

Classifies each managed file by SHA-256 hash against `manifest.json`:
- **clean** files MOVE to `.dotnet-ai-kit/backups/migrate/<timestamp>/`
- **user-modified** files PRESERVE in place (`--include-modified` to opt in)
- 3-keep backup rotation; `--dry-run` for preview; `--host <host>` for scoping

### `dotnet-ai render` for runtime inspectability (US6)

`dotnet-ai render skill <name>` or `dotnet-ai render rule <name>` prints the
runtime-resolved content with current `project.yml` metadata substituted.
v1 produces Claude-host-shaped output only; other hosts deferred to v1.1.

### C# language-server migration (FR-028)

`csharp-ls` is removed from `.mcp.json`. C# diagnostics now flow through the
`csharp-lsp` plugin dependency declared in the Claude plugin manifest. **Pre-
flight: run `dotnet-ai check` to verify `csharp-ls` is on your PATH before
upgrading.** Install from
<https://github.com/razzmatazz/csharp-language-server> if missing.

### Compact SessionStart bootstrap (SC-013)

Replaced the legacy ~5000-token bootstrap with a ≤500-token index pointing
to project.yml + `dotnet-ai check`. Skill and rule bodies load on-demand
via the plugin namespace, not at session start.

### Runtime architecture-profile selection (FR-034)

New `pretooluse-arch-profile.sh` hook reads `project.yml` at every PreToolUse
fire (no caching). Mid-session profile changes are observed by the next tool
use without requiring session restart.

### Rules: 5 universal + 11 path-scoped (FR-011)

Constitution amended to v1.0.8. The universal whitelist is now 5 rules:
`async-concurrency`, `coding-style`, `existing-projects`, `security`,
`tool-calls`. The 11 domain rules (`api-design`, `architecture`,
`configuration`, `data-access`, `error-handling`, `localization`, `multi-repo`,
`naming`, `observability`, `performance`, `testing`) load just-in-time per
their declared `paths:` scope.

## Plugin-update-mid-session recovery (R15)

If you update the plugin while an AI session is running, each host has its
own reload mechanism:

| Host | Reload action |
|--|--|
| Claude Code | `/reload-plugins` slash command |
| Codex CLI | Restart the Codex session |
| Cursor | "Reload Window" command palette action |
| GitHub Copilot | `dotnet-ai upgrade --copilot` re-renders `.github/` files |

## Out of scope for v1.0

Recorded so reviewers know these are intentional v1.1+ items:

- **`bin/` launcher**: deferred to v1.1 (OOS-003). The spike result is
  recorded in the planning folder.
- **Native Codex CLI plugin agents**: deferred to v1.1 (OOS-004). The
  Codex plugin manifest does NOT declare `agents`; `generate_codex_agent()`
  raises NotImplementedError.
- **Multi-repository activity monitor**: not included in this release
  (OOS-006). Plugin-served-artifact drift across linked secondary
  repositories is solved by FR-033 (linked-secondary-repository footprint)
  plus US1 (single-host-action update propagation). Surveillance beyond
  that is deferred.

## Cursor sub-agent spike outcome (A-005)

<!--
T171 (commit 25, OOS-005 PASS branch) — release notes updated for the
PASS outcome. The A-005 spike fixture outcome JSON
(`specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json`)
flipped to `passed` under maintainer override (see commit message); the
PASS-branch artifacts (manifest `agents` field, 13 generated specialist
sub-agents, `rules/cursor/*.mdc`) ship with this release. The first
post-tag `workflow_dispatch` smoke run (T200) remains the authoritative
validator; a regression there reinstates T170b/T170c.
-->

**Cursor sub-agent generation shipped.** Per the A-005 spike fixture
PASS outcome (`cursor-subagent-outcome.json::outcome == "passed"`),
this release includes the full Cursor sub-agent set:

- **14 sub-agent files** under `agents/` (1 fixture + 13 specialists)
  generated by `generate_cursor_agent()` from `agents-source/*.md`.
- **`.cursor-plugin/plugin.json`** declares `"agents": "./agents/"`
  per `contracts/cursor-fixture-decision.contract.md:28`.
- **`rules/cursor/*.mdc`** — 16 Cursor-format rule files (5 universal
  with `alwaysApply: true`; 11 path-scoped with `globs:` from the
  source `paths:` list) regenerated by `render_cursor_rule_mdc()`.

Per `contracts/cursor-fixture-decision.contract.md:27-31`, the PASS
branch entails: (1) manifest `agents` field present, (2) all 13
specialists generated, (3) spec A-005 recorded "spike passed",
(4) this release-notes section states "shipped" (CHK062).

## Privacy + telemetry posture (A-011)

- **No outbound network calls** from any CLI command (statically verified
  by `tests/unit/test_no_network_no_telemetry.py`).
- **No analytics SDKs** in the import graph (parametrized AST scan rejects
  `requests`, `httpx`, `aiohttp`, `urllib3`, `grpc`, segment/mixpanel/
  amplitude/rudder_sdk/posthog).
- **No `socket.create_connection` calls.**

## Documentation

- Migration guide: `docs/migration-v1.md`
- A-008 non-exhaustive list of paths the tool will never write to:
  see `checklists/verification.md` CHK026 + spec A-008.

## Verification commands

After upgrading, run:

```
dotnet-ai check        # Verify plugin install + binary prerequisites
dotnet-ai status       # Tool status (legacy info display, renamed from check)
dotnet-ai render rule async-concurrency   # Inspect a runtime-resolved rule
```
