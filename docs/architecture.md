# Architecture (v2)

dotnet-ai-kit v2 is a **.NET 10 clean/hexagonal** application that authors every artifact once and **projects** it to four AI assistants.

## The one idea

```
            ┌─────────── artifacts/ — ONE authored source, tool-agnostic ───────────┐
            │  skills/  agents/  rules/{conventions,domain}/  profiles/              │
            │  skills/commands/  knowledge/  manifest.yml                            │
            └───────────────────────────────┬───────────────────────────────────────┘
                                             │  PROJECTION ENGINE (CI-gated: git diff --exit-code)
        ┌────────────────────┬───────────────┼───────────────┬────────────────────┐
        ▼                    ▼               ▼               ▼                     ▼
   Claude Code           Codex CLI         Cursor       GitHub Copilot      Dotnet.Ai.Kit.Analyzers
   build/claude + manifest  build/codex    build/cursor   build/copilot       (Roslyn NuGet, build errors)
```

Author once, project per host, gate drift. The same move keeps the four assistants consistent and makes quality deterministic.

## Solution layering (dependencies point inward)

```
Cli ──▶ Hosts ──▶ Application ──▶ Core ◀── Infrastructure ◀── Cli
                          ▲                     │
                          └──── ports ◀─────────┘     Core is pure (no I/O, no third-party deps)
```

| Project | Responsibility |
|---|---|
| `Core` | domain: `Skill/Agent/Rule/Profile/Fragment/KnowledgeDoc/ArtifactCorpus`, value objects, `ArtifactGraph` (broken-edge gate), `DescriptionStandard`, `SubstitutionEngine`, `PluginManifest`, `HostCapabilityMatrix` |
| `Application` | use-cases (`Generate/Init/Check/Render/Detect/Migrate/Configure/Upgrade/Orchestrate/Budget/VerificationGate`) + ports (`IFileSystem`, `IGitClient`, `IProcessRunner`, `IArtifactRepository`, `IArtifactSerializer`, `IHostProjector`, `IHostAdapter`, `IConsoleReporter`, `ITokenizer`, `IDetectionProvider`, `IBackupService`) |
| `Hosts` | one `IHostProjector` per assistant + `HostRegistry` + `ProjectionEngine`; `ClaudeHostAdapter` (per-solution init) |
| `Infrastructure` | adapter impls: `PhysicalFileSystem` (atomic, LF), `GitCliClient`, `ProcessRunner` (list-args), `YamlFrontmatterParser`, `FileSystemArtifactRepository`, `TiktokenTokenizer`, `DotnetProjectDetector`, `BackupRotationService` |
| `Cli` | composition root + System.CommandLine verb tree + `SpectreConsoleReporter` |
| `Analyzers` | Roslyn `DiagnosticAnalyzer`s (DAK0001 async-void, DAK0004 aggregate setters) + code-fix, shipped as a NuGet |

## Enforcement (four tiers; Claude-scoped hard tiers + cross-host floor)

1. **Advisory** — `init` writes domain rules to `.claude/rules/*.md` with `paths:`; a PreToolUse hook injects the active rule body. *(fixes the v1 rule-delivery defect)*
2. **Interceptive** — PreToolUse `deny` for hard violations (Claude).
3. **Deterministic** — `Dotnet.Ai.Kit.Analyzers` → build errors (cross-host floor; `.editorconfig` severity).
4. **Completion gate** — a Stop/SubagentStop hook runs build + tests and blocks "done" until green.

## Selection (no runtime router)

Distributed + compile-time: sharp per-artifact descriptions (the description standard) + the `ArtifactGraph` confusion edges + path-scoping + a thin `do` disambiguator. A triggering eval (confusion matrix) gates description changes; commands are off the always-loaded listing.

## Invariants (the Acceptance.Tests contract)

No-network for local verbs · enumerated `check` exit codes · bounded per-solution config footprint (corpus not copied per project) · deterministic/idempotent generation · corpus-integrity (every artifact loads, name==dir, graph-consistent, projects to 4 hosts) · cross-platform LF output.

See `planning/21` (blueprint), `planning/22` (structure), `planning/26` (locked decisions, authoritative).
