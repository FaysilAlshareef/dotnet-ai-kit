# Implementation Plan: Profile, Rule, and Dynamic Delivery

**Branch**: `024-v2-profile-rule-and-dynamic-delivery` | **Date**: 2026-06-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/024-v2-profile-rule-and-dynamic-delivery/spec.md`

## Summary

Make the 12 authored profiles actually reach hosts in two tiers (architecture-tier always-on, role/band-tier path-scoped), fix the Claude output-style that names an architecture profile it never ships, deduplicate profiles against the 5 universal rules so always-on delivery does not double-inject, narrow the three over-broad rule globs (keeping `error-handling`/`performance` broad and turning `deterministic-enforcement` into a universal registry), and project MCP/LSP host configuration from single descriptors.

**Technical approach.** Architecture-tier always-on delivery is **Claude-only**, because only Claude has a per-solution `init` footprint where `architecture:` is known (`ClaudeHostAdapter` already writes `.dotnet-ai-kit/project.yml` from `metadata.Architecture`). Per the D2 decision (hook channel), at `init` the adapter writes the selected profile to `.claude/profiles/<arch>.md`, and the existing PreToolUse hook (`HookCommand.LoadRules` + `PreToolUseHookService`) injects it always-on exactly as it injects universal rules; the static output-style is fixed to reference the now-delivered profile; determinism rides the 023 footprint SHA-256 (the per-project file is outside the `build/` drift baseline, like `.claude/rules/*.md`). Codex/Cursor/Copilot are build-time/plugin-native (no per-project arch knowledge), so they receive role profiles path-scoped (Cursor `.mdc` globs, Copilot `.instructions.md applyTo`) and architecture profiles as static/selectable reference, with the arch-auto-select capability gap marked explicitly (FR-008). MCP/LSP project from the existing `.mcp.json`/`.lsp.json` descriptors into each host's native shape.

## Technical Context

**Language/Version**: C# 13 on .NET 10 (SDK 10.0.300); analyzer targets `netstandard2.0`
**Primary Dependencies**: System.CommandLine, Spectre.Console (behind `IConsoleReporter`), System.Text.Json (`JsonNode` DOM, no reflection), YamlDotNet, Microsoft.ML.Tokenizers
**Storage**: Filesystem via the `IFileSystem` port — authored `artifacts/`, generated `build/`, per-solution footprint
**Testing**: xUnit + Verify (golden output); `Acceptance.Tests` for cross-cutting contracts; `Hosts.Tests` for projection shape
**Target Platform**: Cross-platform CLI (Windows/macOS/Linux); no-network for local verbs
**Project Type**: Single .NET solution — CLI + projection engine, clean architecture
**Performance Goals**: Deterministic, byte-stable generation; no latency-sensitive path
**Constraints**: No-network (local verbs); LF + UTF-8; clean-architecture dependencies inward; token caps (profile ≤100 lines, rule ≤100); arch-tier single-select; no profile/rule double-injection
**Scale/Scope**: 12 profiles, 21 rules, 4 hosts, 2 descriptors; ~6 `src/` files + profile/rule/agent artifacts + tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Detect-First / II. Pattern Fidelity**: Honored — profiles describe constraints for the *detected* architecture; the arch profile is selected from the project's declared `architecture:`, never forced. ✓
- **III. Architecture & Platform Agnostic**: All 6 architectures keep a profile; per-host delivery adapts to each host's real capabilities (no OS-specific shell; FS port). ✓
- **IV. Best Practices & Quality (TDD)**: Tests-first per user story — profile-delivery test, rule/profile dedup check, glob-scope assertions, MCP/LSP determinism, per-host shape. ✓
- **V. Safety & Token Discipline**: The feature *reduces* tokens — dedup removes double-injected generic constraints, arch single-select prevents multi-inject, glob narrowing cuts idle-token bloat. Profile ≤100-line cap preserved. ✓
- **Clean architecture (dependencies inward)**: New delivery logic lives in `Hosts` (projectors + adapter) and the `Cli` hook backend, depending on `Application`/`Core`; any new tiering helper in `Core` is pure (no I/O). No `Core`→`Hosts` edge introduced. ✓
- **Single-source projection + determinism**: All delivery is single-source from `artifacts/` + projectors; `build/` stays drift-clean; the per-project init footprint is covered by the manifest SHA-256. ✓
- **No-network**: Profile/MCP/LSP projection is pure file generation; projecting an MCP descriptor writes host config, it does not contact a server. ✓

**Result**: No violations. Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/024-v2-profile-rule-and-dynamic-delivery/
├── plan.md              # This file
├── research.md          # Phase 0 — decisions (D2, per-host matrix, tiering, dedup, globs, MCP/LSP)
├── data-model.md        # Phase 1 — entities (ProfileTier, delivery channel, descriptors, duplication item)
├── quickstart.md        # Phase 1 — how to validate (gates + new acceptance checks)
├── contracts/           # Phase 1 — profile-delivery, rule-profile-coherence, mcp-lsp-projection
└── tasks.md             # Phase 2 — /speckit.tasks (NOT created here)
```

### Source Code (repository root)

```text
artifacts/
├── profiles/*.md                         # dedup: strip generic-rule restatement, reference rules (FR-009/010)
├── rules/domain/mediator-abstraction.md  # narrow glob → DI/composition (FR-011)
├── rules/domain/messaging-bus-selection.md   # narrow glob → DI/messaging (FR-011)
├── rules/domain/ai-integration.md        # narrow glob → AI features (FR-011)
├── rules/domain/deterministic-enforcement.md  # → universal registry/pointer (FR-013)
├── agents/{reviewer,dotnet-architect,ef-specialist}.md   # prefer symbol-precise nav when LSP available (FR-017)
└── (MCP/LSP descriptor source — reuse root .mcp.json/.lsp.json or an authored artifacts/ descriptor)

src/DotnetAiKit.Hosts/
├── Claude/ClaudeHostAdapter.cs           # write .claude/profiles/ per-solution: arch always-on + role path-scoped, hook glob-matches (FR-003/004/005)
├── Claude/ClaudeOutputStyleWriter.cs     # reference the delivered profile, not a name (FR-004)
├── Claude/ClaudeProjector.cs             # plugin-distribution copy of profiles + MCP/LSP projection (FR-015/016)
├── Codex/CodexProjector.cs               # static profile guidance in AGENTS.md + MCP (FR-007/015)
├── Cursor/CursorProjector.cs             # .mdc role profiles (globs) + arch selectable + MCP/LSP-unsupported marker
├── Copilot/CopilotProjector.cs           # .instructions.md applyTo role profiles + MCP + LSP (preview)
└── (new) ProfileProjection / ProfileTier helper   # tier-by-name, shared profile→host emit

src/DotnetAiKit.Cli/Commands/HookCommand.cs    # LoadRules also loads .claude/profiles/<arch>.md (always-on)
src/DotnetAiKit.Application/UseCases/PreToolUseHookService.cs   # inject the active profile always-on
src/DotnetAiKit.Infrastructure/ManifestIntegrityService.cs (+ ClaudeHostAdapter)  # footprint hash includes the profile file

tests/DotnetAiKit.Acceptance.Tests/    # ProfileDeliveryTests, RuleProfileCoherenceTests, McpLspProjectionTests
tests/DotnetAiKit.Hosts.Tests/         # re-accept GoldenProjection golden (new projected profile/MCP/LSP files)
```

**Structure Decision**: Single .NET solution, clean architecture. New delivery logic lives in the `Hosts` layer (the four projectors + `ClaudeHostAdapter`) and the `Cli` hook backend (`HookCommand`/`PreToolUseHookService`). Profile tiering is a pure, name-based derivation (no new authored frontmatter field per M2); it lives in `Core` or `Hosts` as a small helper. No new project is introduced.

## Complexity Tracking

> No Constitution Check violations — this table is intentionally empty.

## Phase outputs

- **Phase 0 → [research.md](research.md)**: D2 hook-channel decision (+ rejected alternatives), the per-host delivery matrix (arch always-on = Claude-only), tier-by-name, dedup strategy, glob-narrowing targets, the MCP/LSP descriptor + per-host shapes + support matrix, determinism handling.
- **Phase 1 → [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)**: profile/tier/channel/descriptor/duplication entities; the three delivery contracts; validation steps.
- **Phase 1 agent context**: ran `.specify/scripts/powershell/update-agent-context.ps1 -AgentType claude`.
