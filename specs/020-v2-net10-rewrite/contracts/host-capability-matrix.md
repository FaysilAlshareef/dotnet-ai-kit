# Contract: Host capability matrix (FR-012 / AR-2)

A machine-readable table (authored in `manifest.yml`, validated by `check`, surfaced in docs). Every projected artifact names the capability it depends on; the matrix must cover it. Maturity tags: **GA** / **Preview** / **Experimental** / **Unsupported**.

| Capability | Claude | Codex | Cursor | Copilot |
|---|---|---|---|---|
| Skills (Agent Skills standard) | GA | GA | GA | GA |
| Slash commands | GA (merged into skills) | GA (skills) | GA | GA (prompts) |
| Agents | GA | GA (`.toml`) | GA | Preview (`.agent.md`) |
| Path-scoped rules/instructions | GA (`paths:`) | Unsupported (AGENTS.md global) | GA (`globs`) | GA (`applyTo`) |
| Always-on rules | GA | GA (AGENTS.md) | GA (`alwaysApply`) | GA (copilot-instructions) |
| Hooks (PreToolUse inject) | GA | Unsupported | Unsupported | Unsupported |
| Pre-edit **deny** (T2) | GA | Unsupported → analyzer/CI fallback | Unsupported → analyzer/CI fallback | Unsupported → analyzer/CI fallback |
| Completion **block** (Stop hook, T4) | GA | Unsupported → generated `verify` + CI | Unsupported → generated `verify` + CI | Unsupported → generated `verify` + CI |
| Bundled resources (scripts/examples) | GA | GA (`.agents/skills/`) | GA | GA |
| Plugin manifest | GA (`.claude-plugin`) | GA (`.codex-plugin`) | GA (`.cursor-plugin`) | GA (auto-detects `.claude-plugin`) |
| Packaging / marketplace | GA | Preview | Preview | Preview |

## Rules
- **No false claims (FR-024)**: where a host is `Unsupported` for an enforcement capability, the projected artifacts must use the named fallback (analyzer + CI, generated `verify`, static rule projection, host-native rules) and MUST NOT assert the capability.
- **Claude is the verified enforcement host for v2.0**; the others rely on the deterministic floor (Roslyn analyzer + CI).
- **Per-host install smoke tests** run where the host CLI is present; they are skipped (not failed) where absent.

## Acceptance
`check` validates that every artifact's declared `requires-capability` exists in the matrix and is not `Unsupported` for that host without a declared fallback. Covered by Hosts.Tests + Acceptance.Tests.
