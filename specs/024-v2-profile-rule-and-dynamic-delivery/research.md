# Research: dotnet-ai-kit v2 - Profile, Rule, and Dynamic Delivery

Phase 0 decisions. Each is **Decision / Rationale / Alternatives considered**, grounded in the current source (read first-hand this session) and `planning/29` (authority) + `planning/28` (design context).

## R1: Claude always-on profile content-delivery mechanism (the D2 fork)

**Decision**: **Hook channel.** At `init`, `ClaudeHostAdapter.WritePerSolution` writes the selected architecture profile to `.claude/profiles/<arch>.md` (per-project; architecture is known there from `metadata.Architecture`). Extend the PreToolUse hook backend (`HookCommand.LoadRules` + `PreToolUseHookService.Decide`) to also load `.claude/profiles/*.md` and inject the active profile's body as `additionalContext` always-on, exactly as it already injects universal rules (empty globs ⇒ always apply). Fix `ClaudeOutputStyleWriter` so it references the now-delivered profile instead of naming a profile that never ships.

**Rationale**: First-hand code reading established that (a) `ClaudeOutputStyleWriter` emits a **static** plugin asset (`build/claude/output-styles/…`) that cannot carry per-project architecture content, and (b) the only proven always-on per-project channel is the PreToolUse hook injecting `.claude/rules/*.md` (universal rules) — `HookCommand.LoadRules` + `PreToolUseHookService`. The hook channel reuses that exact, working mechanism with the least new surface, and the per-project file rides the existing 023 footprint SHA-256 (it is outside the `build/` drift baseline, like `.claude/rules/*.md`).

**Alternatives considered**:
- *Per-project output-style generated at `init`, embedding profile content* — honors locked decision L3's literal "output-style" wording, but turns the output-style into an init-generated per-project artifact and would override the user's active output-style. Rejected: more new mechanism, weaker guarantee than the hook.
- *Static output-style references a per-project profile file (advisory)* — smallest change, but "soft" always-on (depends on the model following the reference, not a guaranteed injection). Rejected: doesn't reliably deliver the content.
- **L3 reconciliation**: L3 selected "always-on (output-style), avoid the hook." Code analysis showed that is not literally achievable (static output-style can't carry per-project arch content); the maintainer chose the hook channel for this feature on 2026-06-02 after seeing the finding. Universal-rule injection already *is* the hook, so "always-on" is preserved.

## R2: Per-host profile delivery matrix

**Decision**: Architecture-tier **always-on auto-selection is Claude-only**. Per-host:

| Host | Architecture-tier | Role/band-tier | Capability gap (FR-008) |
|---|---|---|---|
| Claude | always-on, single-select at `init` via the hook (R1) | path-scoped (profile `TargetPaths` → `.claude/rules`-style `paths:` loaded JIT by the hook) | none |
| Codex | static reference in `AGENTS.md` (no gating) | static reference in `AGENTS.md` (no path scope) | no dynamic gating; no per-project select — marked |
| Cursor | `.mdc` per arch profile, `alwaysApply: false` (selectable, **not** a broad glob — avoids 6-way multi-inject) | `.mdc` with role `globs` (path-scoped) | no per-project auto-select for arch — marked |
| Copilot | `.instructions.md` per arch profile, narrow/empty `applyTo` (selectable) | `.instructions.md` with `applyTo` role globs (path-scoped) | no per-project auto-select for arch — marked |

**Rationale**: Code reading established only `ClaudeHostAdapter` has a per-solution `init` footprint where `architecture:` is known; the other three projectors are build-time/plugin-native and architecture-agnostic. Shipping all six arch profiles with broad always-apply globs on Cursor/Copilot would inject six conflicting architectures into one C# edit (multi-inject) — so arch profiles are delivered *selectable*, not broad-glob-always-on, on those hosts. This matches `planning/28` W1.1 (the per-host channel table) and the capability matrix.

**Alternatives considered**: broad-glob arch profiles on Cursor/Copilot (rejected — multi-inject); omit arch profiles from non-Claude entirely (rejected — fails FR-001 "deliver to supported hosts"; selectable delivery closes the reach gap without injecting conflicts).

## R3: Profile tiering

**Decision**: Derive tier from profile name (no new authored frontmatter field). Architecture-tier = {`clean-arch`, `ddd`, `modular-monolith`, `vsa`, `hybrid`, `generic`}; role/band-tier = {`command`, `query-cosmos`, `query-sql`, `gateway`, `processor`, `controlpanel`}. Implemented as a small pure helper (a known-set lookup) in `Core` or `Hosts`.

**Rationale**: `planning/29` M2/M3 — map by name convention; "no new frontmatter field unless the architecture value-space diverges from profile names." The `Profile` entity (verified) carries only `Name`/`Description`/`ConstraintBody`/`TargetPaths`/`AnalyzerBackedConstraints`, no `Scope`; the 6/6 split aligns exactly with profile names, so a name-based set is sufficient and stable.

**Alternatives considered**: add a `tier:` frontmatter field (rejected — M2 says don't, unless names diverge; they don't).

## R4: Rule/profile deduplication (the always-on prerequisite, C2)

**Decision**: Strip generic-rule restatement from the profiles that duplicate the 5 universal rules (`async-concurrency`, `coding-style`, `existing-projects`, `security`, `tool-calls`) — worst offenders per `planning/30` T5: `generic` (≈ entire body), `vsa` (two `## Data Access` sections), `clean-arch`/`ddd`/`modular-monolith` (generic Testing/Data-Access tails). Profiles keep only architecture/role-specific constraints and *reference* the universal rules. Add a deterministic **duplication check** (acceptance test) that fails if a profile body restates a universal-rule constraint.

**Rationale**: `planning/29` C2 is a hard prerequisite for always-on profile delivery — "else always-on profiles double-inject the always-on rules." Doing dedup before wiring delivery (sequenced in tasks) prevents shipping the double-injection.

**Alternatives considered**: deliver first, dedup later (rejected — ships the very double-injection the feature must avoid). A purely manual review with no automated check (rejected — `planning/29` SC requires a dedup check).

## R5: Rule glob narrowing (M1)

**Decision**: Narrow exactly three globs; keep two broad; make one universal:
- `mediator-abstraction` → DI/composition: `**/Program.cs`, `**/*Extensions.cs`, `**/DependencyInjection/**`
- `messaging-bus-selection` → DI/messaging composition globs
- `ai-integration` → AI feature/namespace globs
- `error-handling`, `performance` → **stay broad** (`**/*.cs`) — coverage outweighs idle-token economy
- `deterministic-enforcement` → **universal** (always-apply, no path glob), carried as a concise registry/pointer to its analyzer-backed constraints

**Rationale**: `planning/29` M1 reconciles the 27↔28 conflict exactly this way (narrow the 3 both docs agree on; keep error-handling/performance broad; deterministic-enforcement is a false-JIT meta-registry). Confirmed by the clarify session.

**Alternatives considered**: narrow all six (28 W5.1) — rejected by M1 for error-handling/performance (under-triggering risk).

## R6: MCP/LSP descriptor projection (D3)

**Decision**: Project **LSP now** from the root `.lsp.json` (`csharp` → `csharp-ls`, target-relevant), and project **MCP from a new target-facing descriptor** (D-MCP resolved 2026-06-02 → option (a)). The root `.mcp.json` (`mcpServers.codebase-memory-mcp`) is the kit's OWN dev config and MUST NOT be projected into users' repos (it would wire `codebase-memory-mcp` into their Claude, pointed at their code); instead 024 authors a not-yet-available descriptor for the future `dotnet-ai mcp serve`. Per host:
- **LSP**: Claude `build/claude/.lsp.json` (GA); Copilot (Preview); **Codex/Cursor explicitly marked unsupported** (agent-facing LSP not available) rather than silently omitted.
- **MCP** (GA ×4): author a target-facing descriptor in `artifacts/` for the future `dotnet-ai mcp serve`, **marked not-yet-available** (never the kit's dev `codebase-memory-mcp`), and project it per host via the writer (Claude `.mcp.json`, Codex `[mcp_servers]`, Cursor `mcpServers`, Copilot form). `029` activates the descriptor when the kit's server exists. *(D-MCP resolved → option (a); rejected: (b) inert placeholder, (c) descope MCP to 029.)*
- **Agent wiring (FR-017)**: update `reviewer`, `dotnet-architect`, `ef-specialist` to prefer symbol-precise navigation (`goToDefinition`/`findReferences`) over text search when LSP is available.

The MCP track is the install mechanism `029` K4 depends on; 024 ships the mechanism plus a not-yet-available target-facing descriptor (option a), and `029` activates it. The kit's dev `.mcp.json` is never projected.

**Rationale**: `planning/29` D3 / `planning/28` W1.3 + the capability matrix (MCP GA ×4; LSP Claude GA, Copilot Preview, Codex/Cursor unsupported). The descriptors already exist at the repo root; projecting them from one source preserves single-source + determinism.

**Alternatives considered**: author a new descriptor format in `artifacts/` (deferred — reuse the existing root descriptors as the single source; revisit if `029` needs a richer shape). Build the MCP server now (out of scope — `029`).

## R7: Determinism & drift

**Decision**: Build-time projected files (`build/<host>/` MCP/LSP, role-profile `.mdc`/`.instructions.md`, the static output-style) stay in the `generate --check` drift baseline and must be byte-stable; re-accept the Verify golden when projection shape changes. The per-project `.claude/profiles/<arch>.md` (written at `init`, like `.claude/rules/*.md`) is **outside** the `build/` baseline; its determinism is covered by extending the footprint SHA-256 (`ManifestIntegrityService.ComputeFootprintSha256`) to include the profile file.

**Rationale**: Mirrors the existing split — `build/` is the static projection (drift-gated); the per-solution footprint is per-project (hash-gated, added in 023). No new drift surface is introduced for the per-project profile.

## R8: Default architecture (from clarify)

**Decision**: When `project.yml` declares no architecture or an unrecognized value, deliver the `generic` architecture profile (the catch-all). `ClaudeHostAdapter.RenderProject` already defaults `architecture:` to `generic`, so profile selection reuses that resolved value. A strict-mode error for unmatched values is out of scope.

**Rationale**: `generic` exists precisely as the catch-all; silently omitting profile delivery would be hostile. Reuses the existing default in `RenderProject`.

## Deferred / out-of-scope (recorded)

- Kit's own MCP **server runtime** → `029` (this feature only projects MCP *config*).
- Codex `AGENTS.md` size trim (952 lines) → `026` / `planning/29` I3.
- New analyzers / populating `AnalyzerBackedConstraints` with new diagnostics → `027` (this feature may *reference* the field for `deterministic-enforcement` but does not add analyzers).
- New W7 skills/agents, script porting, progressive-disclosure relocation → `025`/`026`/`028`.
