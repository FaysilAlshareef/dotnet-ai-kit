# Contract: Profile Delivery

Covers FR-001..FR-008. Verifiable by `Acceptance.Tests` (and `Hosts.Tests` golden).

## C-PD-1 — Architecture profile reaches Claude as always-on content (Claude-only)

- **Given** a per-solution `init` against a project whose resolved `architecture:` is `X` (one of the six arch names; unknown/absent → `generic`),
- **Then** the footprint contains `.claude/profiles/X.md` with the (deduplicated) content of profile `X`, and **no other** architecture profile file is written.
- **And** the PreToolUse hook backend, when run in that solution, injects profile `X`'s body as `additionalContext` for any edit (always-on, like a universal rule) — verifiable via `PreToolUseHookService.Decide` returning the profile body regardless of file path.
- **And** `ClaudeOutputStyleWriter` output references the delivered profile path/content, not a profile that never ships.

## C-PD-2 — Role profiles are path-scoped, not always-on

- **Given** the six role/band profiles,
- **Then** on path-capable hosts they are delivered with their `TargetPaths` scope (Claude `paths:` / Cursor `globs` / Copilot `applyTo`) and are **absent** from any always-on channel.
- **And** editing a file outside a role profile's scope does not inject that profile.

## C-PD-3 — Per-host channel + explicit capability gaps

- **Then** each host emits profiles per the research R2 matrix, and every unsupported capability (Codex dynamic gating; Cursor/Copilot arch auto-select) is represented by an explicit marker in the generated output (FR-008) — assertable by a test that the marker text/field exists, never a silent omission.

## C-PD-4 — Default architecture

- **Given** `project.yml` with no/unknown `architecture:`, **Then** `.claude/profiles/generic.md` is delivered (never empty/omitted).

## Tests

- `ProfileDeliveryTests`: C-PD-1 (footprint file + single-select + hook injection + output-style reference), C-PD-2 (scope in/out), C-PD-4 (default).
- `Hosts.Tests` golden: role-profile `.mdc`/`.instructions.md` shapes + Codex `AGENTS.md` profile section + capability markers (re-accept on first authoring).
