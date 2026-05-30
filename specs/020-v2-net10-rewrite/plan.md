# Implementation Plan: dotnet-ai-kit v2 — Single-Source Artifact Engine

**Branch**: `020-v2-net10-rewrite` | **Date**: 2026-05-31 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/020-v2-net10-rewrite/spec.md`

## Summary

Rewrite dotnet-ai-kit as a **.NET 10 clean/hexagonal CLI** that authors every artifact **once** in a tool-agnostic `artifacts/` source tree and **projects** it to Claude Code, Codex CLI, Cursor, and GitHub Copilot. A single `generate` pass (re)produces every per-host output + all manifests, CI-gated by `git diff --exit-code` so drift cannot merge. The rewrite fixes the v1 defect where plugin-native Claude never received domain rules (`init` now writes `.claude/rules/*.md` with `paths:`), adds a deterministic enforcement layer (a shipped Roslyn analyzer + PreToolUse/Stop hooks, Claude-scoped with documented fallbacks), keeps invocation token-frugal (description standard + artifact graph + a thin disambiguator), and preserves the v1 behavioral contract (no-network, exit codes, footprint) as a language-neutral acceptance suite.

**Technical approach**: clean architecture with dependencies pointing inward (`Cli → {Hosts, Infrastructure, Application} → Core`; `Core` is pure). Reflection-free serialization (System.Text.Json source-gen for tool config; YamlDotNet static generator for artifact frontmatter) to keep the AOT path open (AOT itself deferred per BD-3). The MVP/convergence anchor is **US1 + US2**: the engine + Claude projection + the rule-delivery fix + green build/tests, proven on a thin ~5-artifact slice, then broadened.

## Technical Context

**Language/Version**: C# 13 on .NET 10 (SDK 10.0.300) for the CLI; `netstandard2.0` for the Roslyn analyzer package
**Primary Dependencies**: System.CommandLine 2.0.8 (CLI parsing, `SetAction`), Spectre.Console (terminal output, never `Spectre.Console.Cli`), System.Text.Json source-gen (tool config), YamlDotNet + Vecc.YamlDotNet.Analyzers.StaticGenerator (artifact frontmatter), Microsoft.ML.Tokenizers `TiktokenTokenizer` (token budget), Microsoft.CodeAnalysis (analyzer), Verify (golden-output tests), xUnit (test framework)
**Storage**: Filesystem only — `artifacts/` (authored source), `build/` (generated per-host outputs, committed), per-solution `.dotnet-ai-kit/*` + `.claude/*`. No database. Tool config is JSON; artifact frontmatter is YAML.
**Testing**: xUnit + Verify (golden snapshots of every projected file); `Acceptance.Tests` for the cross-language invariants (no-network, exit codes, footprint); `Analyzers.Tests` via Microsoft.CodeAnalysis.Testing; `Triggering.Evals` for selection precision. Tests run with `dotnet test`.
**Target Platform**: Cross-platform CLI — Windows, macOS, Linux (identical behavior; FS abstraction; list-arg subprocess, never shell)
**Project Type**: Single multi-project .NET solution (CLI tool + shipped analyzer NuGet), authored corpus, generated outputs
**Performance Goals**: `check` < 10 s; single-artifact `render` < 2 s; `generate` deterministic, idempotent, byte-stable
**Constraints**: No-network invariant for `init`/`check`/`migrate`/`render`/`generate` (process-level network-deny test); reflection-free on the serialization/validation path (AOT-clean by construction); per-solution footprint within a fixed bound; token budget on the always-loaded listing enforced by `check` + CI
**Scale/Scope**: ~160 skills + 15 agents + 21 rules + 12 profiles + 32 command-skills authored once and projected to 4 hosts; 6 src projects + 1 analyzer + ~7 test projects; the v1 Python (`src/dotnet_ai_kit/` + `tests/`) coexists as the runnable reference until parity, then removed

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The repo governance constitution (`.specify/memory/constitution.md`) was amended **1.0.8 → 1.1.0** alongside this plan: the five core **principles are unchanged**; only descriptive technology/corpus/workflow facts were updated to v2 reality (CLI now .NET 10; counts 21 rules/15 agents/~160 skills/32 commands/12 profiles; lifecycle adds constitution/checklist/fix/orchestrate/release). With that amendment, all gates pass:

| Principle | Gate | Status |
|---|---|---|
| **I. Detect-First, Respect-Existing** | `DetectService`/`IDetectionProvider` reads `<TargetFramework>`, architecture, naming, packages before generating; never changes a project's .NET version or refactors existing code | ✅ PASS — design includes detection + token substitution; generated code matches detected conventions |
| **II. Pattern Fidelity** | Generated code uses version-appropriate C#; matches detected DI/error/naming patterns | ✅ PASS — substitution + profiles drive pattern-fidelity; analyzer enforces naming/layering |
| **III. Architecture & Platform Agnostic** | Cross-platform (FS port, list-arg subprocess, no hardcoded company/`~`/`/tmp`); supports all listed architectures via profiles | ✅ PASS — NFR cross-platform + SC-012; profiles for VSA/Clean/DDD/Modular/CQRS-ES |
| **IV. Best Practices & Quality** | TDD (golden tests red-first by design; analyzer tests), SOLID (clean layering), docs-first (research.md confirms APIs), structured errors (Result-style + exit codes) | ✅ PASS — see research.md; Verify baselines accepted after first red run |
| **V. Safety & Token Discipline** | No deploy; `--dry-run` on mutating verbs; reversible via `undo`; skill ≤500 / command ≤200 / rule ≤100 / agent ≤120 / profile ≤100; budget measured by `check` (`TiktokenTokenizer`) | ✅ PASS — `TokenBudgetPolicy` + `check` budget gate; commands off the always-loaded listing |

**Complexity note (AR-8)**: ports are introduced only for genuinely volatile concerns (filesystem, git, process, serialization, host rendering, tokenization, detection, manifest writing, backup). Simple manifest records and projection functions are NOT wrapped in extra service layers. No constitution violations to track.

## Project Structure

### Documentation (this feature)

```text
specs/020-v2-net10-rewrite/
├── plan.md              # This file
├── research.md          # Phase 0 — stack decisions + version reconfirmation plan
├── data-model.md        # Phase 1 — Core domain types, value objects, graph, manifest
├── quickstart.md        # Phase 1 — author→generate→init→check walkthrough
├── contracts/           # Phase 1 — CLI verb contracts, exit codes, projection & host-capability contracts
│   ├── cli-verbs.md
│   ├── exit-codes.md
│   ├── projection-contract.md
│   └── host-capability-matrix.md
├── checklists/
│   └── requirements.md  # spec quality checklist (from /speckit.specify)
└── tasks.md             # Phase 2 — created by /speckit.tasks
```

### Source Code (repository root, transition layout per BD-1)

```text
artifacts/                        # ◀ SINGLE SOURCE OF TRUTH (tool-agnostic, authored once)
├── skills/<category>/<name>/SKILL.md (+ optional scripts/ examples/ references/ assets/ evals/)
├── skills/commands/<name>/SKILL.md   # lifecycle/code-gen commands authored as command-skills
├── agents/<name>.md                  # reference skills; no bundled resources
├── rules/conventions/<name>.md       # universal (always-on)
├── rules/domain/<name>.md            # path-scoped (paths: globs)
├── profiles/<arch>.md                # architecture hard-constraints
├── fragments/<name>.md               # reusable stanzas
├── knowledge/<topic>.md              # long-form references
└── manifest.yml                      # ONE descriptor → all per-host manifests

src/
├── dotnet_ai_kit/                # v1 Python — KEPT as runnable reference until parity, then removed
├── DotnetAiKit.Core/             # domain; no I/O, no third-party deps
├── DotnetAiKit.Application/      # use-cases + ports; → Core only
├── DotnetAiKit.Hosts/            # per-tool IHostAdapter + projectors; → Application, Core
├── DotnetAiKit.Infrastructure/   # adapter impls (FS, git, serializers, tokenizer, detector); → Application, Core
├── DotnetAiKit.Cli/              # composition root + System.CommandLine tree; → all
└── DotnetAiKit.Analyzers/        # Roslyn analyzers (netstandard2.0) shipped as Dotnet.Ai.Kit.Analyzers NuGet

tests/                            # v1 Python tests KEPT as reference; new .NET test projects added alongside
├── DotnetAiKit.Core.Tests/
├── DotnetAiKit.Application.Tests/
├── DotnetAiKit.Hosts.Tests/
├── DotnetAiKit.Cli.Tests/
├── DotnetAiKit.Analyzers.Tests/
├── DotnetAiKit.Acceptance.Tests/ # cross-language invariants — the portable spec
└── DotnetAiKit.Triggering.Evals/ # selection precision harness + confusion matrix

build/                            # GENERATED per-host outputs (committed; CI git diff --exit-code)
├── .claude-plugin/  .codex-plugin/  .cursor-plugin/
├── claude/  codex/  cursor/  copilot/
└── marketplace.json

dotnet-ai-kit.slnx                # .NET solution (slnx per planning/26)
Directory.Build.props  Directory.Packages.props  global.json   # central build/pkg/version mgmt
.editorconfig  .gitignore
.github/workflows/                # CI: build + test + generate git-diff gate (+ later: pack matrix)
```

**Structure Decision**: Clean/hexagonal multi-project .NET solution with one `IHostAdapter`/projector per tool (the backbone, descended from v1 `hosts/base.py`). The authored `artifacts/` tree is the single source; `build/` holds committed generated outputs as the drift baseline. The Python v1 (`src/dotnet_ai_kit/`, `tests/`) coexists during the rewrite (BD-1) and is removed only after the .NET binary passes the acceptance suite (P10). Solution file is `.slnx` (planning/26). Generated output dir is `build/` (planning/22) — `.gitignore` excludes `bin/`/`obj/` but explicitly NOT `build/`.

## Phases (build order — maps to planning/26 §5)

Each phase ends green (build + tests) and is committed.

| Phase | Story | Build | Acceptance gate |
|---|---|---|---|
| **P0 Foundation** | — | `dotnet-ai-kit.slnx`, 6 src + analyzer + 7 test projects, central pkg mgmt, `global.json` (pin 10.0.300), `.editorconfig`, `.gitignore`, CI skeleton, `artifacts/` tree | empty solution builds; CI green |
| **P1 Core domain** | US1 found. | `Skill/Agent/Rule/Profile/Command/Fragment/Manifest` + value objects + `ArtifactGraph` + `DescriptionStandard` + `SubstitutionEngine` | `Core.Tests` green; graph build fails on a broken edge (FR-006) |
| **P2 Ports + Infra** | US1 found. | ports + `PhysicalFileSystem`, `YamlFrontmatterParser`, `JsonArtifactSerializer`, `FileSystemArtifactRepository`, `TiktokenTokenizer` | frontmatter round-trips; `Application.Tests` (fakes) green |
| **P3 Engine + Claude + generate** | US1 | `IProjectionEngine`/`ProjectionEngine`, `ClaudeProjector`, `ClaudeManifestWriter`, `GenerateService`, ~5-artifact corpus, golden tests, drift gate | **SC-001** on the slice; Verify baselines committed |
| **P4 Remaining projectors** | US3 | `Codex`/`Cursor`/`Copilot` projectors + manifest writers; **host-capability matrix**; golden tests | **SC-008**; all 4 hosts golden-tested |
| **P5 CLI verbs + acceptance + rule delivery** | US2, US4 | `init`/`check`/`render`/`migrate`/`generate`/`configure`/`detect`/`upgrade`; `SpectreConsoleReporter`; `Acceptance.Tests` (no-network, exit codes, footprint); **`init` writes `.claude/rules/*.md` with `paths:`** | **SC-002 (the bug fix)**, **SC-007**, SC-010/011 |
| **P7 Enforcement** | US5 | `Dotnet.Ai.Kit.Analyzers` (layering + naming + banned-API), `Analyzers.Tests`, PreToolUse + Stop hooks (Claude-scoped), `deterministic-enforcement` rule | analyzer tests; **SC-004** |
| **P6 Corpus** | US7 | migrate/consolidate a representative corpus into `artifacts/` (fix `when_to_use` no-op + broken sample); author command-skills; license-light defaults | every artifact projects; budget within target (**SC-006**) |
| **P8 Multi-repo** | US8 | feature-brief projection + awareness **contract test**; cross-repo analyze (sequential default, `--parallel` opt-in) | **SC-009**; FR-035 |
| **P6e Selector oracle** | US6 | triggering eval harness over ambiguous clusters wired to CI | **SC-005** |
| **P9 Expansion** | US7 | new-domain skills/agents/rules (Aspire/AI/MinimalAPI/testing/…), license-light migration skills | new artifacts project + pass the oracle |
| **P10 Distribution** | US9 | framework-dependent `dotnet tool` packaging + `marketplace.json`; **then** Python parity-removal (BD-1) | `dotnet tool install` smoke |

**Convergence anchor (must reach green this session)**: P0 → P5 + P7-core. That delivers SC-001, SC-002, SC-003, SC-007 (and SC-004 with P7). P6/P8/P9/P10 are built to a representative/contract level and the remainder tracked in tasks.md for follow-on, per incremental-delivery (each story independently testable).

## Complexity Tracking

No constitution violations. Ports are limited to volatile concerns (AR-8); no speculative abstraction over plain records/projection functions.
