# Phase 0 Research: dotnet-ai-kit v2 stack & key decisions

**Date**: 2026-05-31 · **Feature**: 020-v2-net10-rewrite
**Method**: Decisions inherited from the verified planning research (planning/21 §5.2 + planning/26 "Verified facts", confirmed against primary sources 2026-05-30). Per the build-time discipline, fast-moving package APIs are **reconfirmed by compile-spike** against the restored package version during P0/P5 before CLI code is written — web/doc lookups are necessary but not authoritative; the throwaway build is.

## Decisions

### D1 — CLI runtime & language
- **Decision**: C# 13 on **.NET 10** (SDK 10.0.300, already installed) for all `src/*` and test projects; **`netstandard2.0`** for `DotnetAiKit.Analyzers` (Roslyn analyzers must target netstandard2.0 to load in the compiler).
- **Rationale**: Maintainer-locked (BD); .NET 10 is GA; netstandard2.0 is mandatory for analyzer assemblies.
- **Alternatives**: .NET 9 (rejected — 10 is installed/locked); single TFM for the analyzer (rejected — would not load in Roslyn).

### D2 — CLI parsing
- **Decision**: **System.CommandLine 2.0.8** (stable). Build a `RootCommand` tree; use **`SetAction`** (not `SetHandler`); `rootCommand.Parse(args)` then `await parseResult.InvokeAsync(...)`; async actions forward `CancellationToken`.
- **Rationale**: In-box-adjacent, AOT-friendly, the current stable surface. `System.CommandLine.Hosting` is **deprecated** → manual DI.
- **Alternatives**: Spectre.Console.Cli (rejected — `RequiresDynamicCode`, AOT-hostile); Cocona/McMaster (rejected — heavier, less AOT-clean).
- **Spike before use (P5)**: confirm `SetAction` overloads + `InvokeAsync` signature against the restored 2.0.8 package (the 2.0.x line churned across betas).

### D3 — Dependency injection
- **Decision**: **manual `ServiceCollection` → `BuildServiceProvider`**; resolve services inside each command's `SetAction`. Select the host adapter via a `HostRegistry` dictionary keyed by `HostName` (no keyed DI).
- **Rationale**: keyed DI + Generic Host are AOT-risky; a plain dictionary is trivially AOT-clean and testable.
- **Alternatives**: `System.CommandLine.Hosting` (deprecated); keyed DI (AOT-risk).

### D4 — Terminal output
- **Decision**: **Spectre.Console** (rendering only) behind an `IConsoleReporter` port. Use-cases never reference Spectre.
- **Rationale**: rich tables/panels/progress; the port keeps Application UI-free and testable.
- **Alternatives**: `Spectre.Console.Cli` (rejected — AOT-hostile); raw `Console` (rejected — poor UX).

### D5 — Serialization (tool config vs artifact frontmatter)
- **Decision**: tool's own config = **JSON via System.Text.Json source-gen** (`JsonSerializerContext`). Artifact YAML frontmatter = **YamlDotNet + `Vecc.YamlDotNet.Analyzers.StaticGenerator`** (static context, reflection-free).
- **Rationale**: STJ source-gen is in-box and AOT-clean; YAML can't be dropped (frontmatter is YAML) so it needs a static generator to stay AOT-clean.
- **Alternatives**: reflection-based (rejected — IL2026/AOT-breaking); JSON for frontmatter (rejected — frontmatter is conventionally YAML across all four hosts).
- **Spike before use (P2)**: confirm the static-generator package id/attribute names; if the AOT static path is awkward at this stage, parse frontmatter with a thin hand-rolled scanner (frontmatter is a constrained subset) and defer full YamlDotNet — AOT is deferred anyway (BD-3), so reflection-based YAML is acceptable in the FD build as long as the seam (`IArtifactSerializer`) is clean.

### D6 — Config binding & validation
- **Decision**: `EnableConfigurationBindingGenerator=true` + `[OptionsValidator]` + DataAnnotations (reflection-free). Domain validation lives in Core value objects (parse-don't-validate).
- **Rationale**: the pydantic-equivalent that stays AOT-clean; most validation is actually in Core VOs.
- **Alternatives**: FluentValidation (heavier, reflection); manual everywhere (more code).

### D7 — Token counting (new capability)
- **Decision**: **Microsoft.ML.Tokenizers** `TiktokenTokenizer` behind `ITokenizer`, used by `check` to measure the always-loaded listing against the budget.
- **Rationale**: real token counts replace v1's line-count proxy; CI gate on budget regression.
- **Alternatives**: line-count proxy (v1 — imprecise); SharpToken (less maintained).

### D8 — Testing
- **Decision**: **xUnit** + **Verify** for golden-output snapshots of every projected/generated file; `Microsoft.CodeAnalysis.CSharp.Analyzer.Testing` for analyzer tests.
- **Rationale**: Verify snapshots are the regression contract a full rewrite needs; they are red on first authoring (emit `*.received.*`) until baselines are accepted as `*.verified.*` and committed — this is expected, not a failure.
- **Alternatives**: TUnit (pre-1.0 maturity risk); hand-written string asserts (brittle for large outputs).

### D9 — Distribution
- **Decision**: **framework-dependent `dotnet tool`** first (BD-3); per-RID Native AOT deferred until trim-warning-clean. Project-scope, pinned `marketplace.json`.
- **Rationale**: AOT is an optimization, not a launch blocker; keep the AOT path open by construction (reflection-free) without paying its cost now.
- **Alternatives**: AOT-first (rejected — premature; trim warnings unresolved).

### D10 — CQRS dispatch / mapping licensing (act-on regardless of rewrite)
- **Decision**: generated code is **license-light by default** — manual mapping + an `ISender`-style dispatch port; MediatR/AutoMapper/MassTransit are **opt-in** with version + license notes; free alternatives offered: **Mediator** (source-gen, MIT) and **Wolverine** (MIT).
- **Rationale**: MediatR (commercial license-key, <13.0.0 free), AutoMapper (commercial), MassTransit v9 (commercial) — verified 2026-05-30. Default must not introduce a commercial dependency.
- **Alternatives**: pin MediatR <13 (offered as one opt-in path); ignore (rejected — license risk for users).
- **Re-check at implementation**: the *commercial shift* is verified; the exact version cutoffs are the authors' secondary sources — re-read vendor pages before they become load-bearing in generated READMEs.

### D11 — Enforcement portability
- **Decision**: hard tiers (PreToolUse-deny, Stop-hook completion gate) are **Claude-scoped** (the verified host); Codex/Cursor/Copilot get documented fallbacks (Roslyn analyzer + CI gates, a generated `verify` command, static rule projection, host-native rule systems). The Roslyn analyzer + CI are the cross-host deterministic floor.
- **Rationale**: hook deny/block semantics are verified only on Claude; claiming them elsewhere would be false.
- **Alternatives**: claim parity everywhere (rejected — unverifiable/false).

### D12 — Skill selection mechanism
- **Decision**: **not a runtime router.** Selection = strict per-artifact descriptions (the description standard) + the artifact graph's confusion-pair edges + a thin `do` disambiguator (guidance, not a gate). Triggering eval harness gates description changes in CI, starting on the ambiguous clusters.
- **Rationale**: skills ≠ tools — the "30-50 tool degradation" figures are about MCP tools that load full schemas; skills use progressive disclosure (~100 tokens each). The problem is selection precision, not token bloat.
- **Alternatives**: heavyweight RAG/MCP router over the 124+ skills (rejected — anti-pattern here; single point of failure).

## Resolved unknowns (were NEEDS CLARIFICATION)
- Generated-output directory name → `build/` (planning/22); `.gitignore` excludes `bin/`/`obj/` only.
- Solution file format → `.slnx` (planning/26 over planning/22's `.sln`).
- Config format → JSON for tool config (frictionless AOT); YAML stays only for artifact frontmatter.
- Python removal timing → after the .NET binary passes the acceptance suite (P10), not before (BD-1).

## Items to reconfirm by compile-spike before they become load-bearing
1. System.CommandLine 2.0.8 `SetAction`/`InvokeAsync` exact signatures (P5).
2. YamlDotNet static-generator package id + attributes; fallback to a thin frontmatter scanner if the AOT static path is awkward (P2).
3. Verify package wiring on .NET 10 + xUnit (P3).
4. Microsoft.ML.Tokenizers `TiktokenTokenizer` factory API + model name (P5).
5. Microsoft.CodeAnalysis version compatible with netstandard2.0 analyzer + the test harness (P7).

All five are confined behind ports/seams, so a surprise in any one is a localized fix, not a redesign.
