# Data Model: Profile, Rule, and Dynamic Delivery

Conceptual model for the delivery feature. No persistent database; "entities" are the authored-artifact and projection concepts the engine manipulates. Existing types are referenced by their source location; new/derived concepts are marked **(new)**.

## Profile (existing — `src/DotnetAiKit.Core/Artifacts/Profile.cs`)

| Field | Meaning | This feature |
|---|---|---|
| `Name` | profile slug (e.g., `clean-arch`, `command`) | drives tier derivation (R3) and the architecture→profile mapping |
| `Description` | selector description | unchanged |
| `ConstraintBody` | the profile guidance | **deduplicated** against universal rules (R4); kept ≤100 lines |
| `TargetPaths` | `Glob[]` scope | drives role-tier path-scoped delivery (Cursor `globs`, Copilot `applyTo`); narrowed for over-broad profiles |
| `AnalyzerBackedConstraints` | constraint names also enforced by analyzers | may be *referenced* by `deterministic-enforcement` framing; populating new diagnostics is `027` |

No new authored field is added (M2 — tier derives from name).

## ProfileTier **(new, derived)**

A pure, name-based classification (a known-set lookup, no I/O):

- **Architecture-tier** (single-select, always-on on Claude): `clean-arch`, `ddd`, `modular-monolith`, `vsa`, `hybrid`, `generic`.
- **Role/band-tier** (additive, path-scoped): `command`, `query-cosmos`, `query-sql`, `gateway`, `processor`, `controlpanel`.

Invariant: every authored profile name maps to exactly one tier; an unknown name is a corpus-integrity failure (caught by a test). Lives in `Core` (or `Hosts`) as a small helper used by the projectors and the adapter.

## DeliveryChannel **(new, conceptual)** — per (host × tier)

The matrix the projectors implement (see research R2):

| Host | Architecture-tier channel | Role-tier channel |
|---|---|---|
| Claude | per-solution `.claude/profiles/<arch>.md` at `init` + PreToolUse always-on injection | `paths:`-scoped, hook glob-matched (JIT) |
| Codex | static section in `codex/AGENTS.md` | static section in `codex/AGENTS.md` |
| Cursor | `cursor/rules/<arch>.mdc`, `alwaysApply: false` (selectable) | `cursor/rules/<role>.mdc` with `globs` |
| Copilot | `copilot/.github/instructions/<arch>.instructions.md` (narrow/empty `applyTo`) | `…instructions.md` with role `applyTo` |

Each channel carries a `supported` flag; unsupported capabilities (e.g., Codex dynamic gating, Cursor/Copilot arch auto-select) are emitted as an explicit marker (FR-008), never silently dropped.

## ArchitectureSelector (existing — `ProjectMetadata.Architecture` → `.dotnet-ai-kit/project.yml`)

The project's declared architecture, defaulting to `generic` (already implemented in `ClaudeHostAdapter.RenderProject`). Selects the single architecture-tier profile delivered always-on on Claude. Unknown/absent → `generic` (R8).

## Per-project profile footprint file **(new)**

`.claude/profiles/<arch>.md` — written by `ClaudeHostAdapter.WritePerSolution` at `init`, outside the `build/` drift baseline (like `.claude/rules/*.md`). Its bytes are folded into the footprint SHA-256 (`ManifestIntegrityService.ComputeFootprintSha256`) so tamper/determinism is covered (R7).

## MCP descriptor (existing — root `.mcp.json`)

`mcpServers: { <name>: { command, args, transport, dotnet_ai_kit_min_version } }`. Single source projected per-host into the native shape (Claude `.mcp.json`, Codex `[mcp_servers]`, Cursor `mcpServers`, Copilot config). Byte-stable (R7).

## LSP descriptor (existing — root `.lsp.json`)

`{ <language>: { command, extensionToLanguage } }` (e.g., `csharp` → `csharp-ls`). Projected to Claude (GA) and Copilot (Preview); Codex/Cursor get an explicit unsupported marker.

## DuplicationItem **(new, transient — drives R4)**

A `(profile, universalRule, restatedConstraint)` finding: a generic constraint stated by both a universal rule and a profile. Resolution = remove from the profile (keep the rule authoritative) and reference the rule. The dedup acceptance check asserts the set is empty after implementation.

## Rule scope (existing — `Rule.Scope` / `Rule.Paths`)

Unchanged type; this feature edits the `Paths` of three domain rules (narrow) and converts `deterministic-enforcement` to universal scope (no globs) — see R5. `error-handling`/`performance` keep broad globs.
