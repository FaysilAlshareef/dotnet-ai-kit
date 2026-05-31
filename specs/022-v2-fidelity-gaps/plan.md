# Implementation Plan: dotnet-ai-kit v2 — Planning-Fidelity Gaps

**Branch**: `022-v2-fidelity-gaps` | **Date**: 2026-05-31 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/022-v2-fidelity-gaps/spec.md`

## Summary

Close the specified-but-absent/stubbed gaps between `planning/20`–`26` (26 authoritative) and the codebase, on the green 020+021 engine: make the wired enforcement hooks actually runnable (fix the `dotnet-ai` v1-shim shadowing), populate skill resources where they add value (FR-D33 set + `add-*` + cluster evals) with a script-trust model, author `evals/cases.jsonl` + a confusion-matrix gate, add Verify golden baselines (NFR-6), implement the user-owned-file merge/backup/consent policy, add the remaining enforcement channels (T2 `prompt` hook, forced output styles), codify per-host install smoke tests, verify Codex/Cursor loadability, enforce a `SchemaVersion` migration check, and close the `blazor-hybrid` name-parity gap. Every change keeps the corpus graph-consistent, projects to four hosts, stays drift-clean, and keeps all gates green.

## Technical Context

**Language/Version**: C# 13 on .NET 10 (SDK 10.0.300); analyzers/codefixes netstandard2.0.
**Primary Dependencies**: System.CommandLine 2.0.8 · Spectre.Console (behind `IConsoleReporter`) · YamlDotNet · Microsoft.ML.Tokenizers · Microsoft.CodeAnalysis (+ Workspaces for codefixes) · xUnit + **Verify.Xunit** (referenced, currently unused).
**Storage**: filesystem only (`artifacts/` source → `build/` projections), via `IFileSystem`.
**Testing**: xUnit; `Acceptance.Tests` (cross-host invariants + smoke) · `Hosts.Tests` (projector golden) · `Triggering.Evals` (selector) · analyzer tests. External `claude` CLI v2.1.154 present for plugin-validate smoke.
**Target Platform**: Windows/macOS/Linux (NFR-3); hooks invoked by host CLIs.
**Project Type**: CLI tool + shipped Roslyn analyzer/codefix NuGets + projected per-host plugin (single solution, hexagonal).
**Performance Goals**: `check` < 10 s; `render` < 2 s; `generate` deterministic/idempotent (NFR-5) — unchanged.
**Constraints**: no-network for init/check/migrate/render/generate (NFR-1); byte-stable deterministic projection; AOT-friendly (no reflection on the hot path); descriptions hard-gated.
**Scale/Scope**: 181 skills / 32 command-skills / 15 agents / 21 rules / 12 profiles; 4 hosts; ~834 generated files. This feature touches a *subset* of skills (resources), the projectors (resource copy + golden), the hook launcher + `init` write path, and the test projects — not a corpus rewrite.

## Constitution Check

`.specify/memory/constitution.md` (v1.1.0) — gates evaluated; **no violations**:
- **Clean architecture / Core purity**: `SkillResourceSet`/`SchemaVersion` already exist in Core; resource population is corpus authoring + repository loading. The user-file policy, hook-launcher resolution, and `prompt`-hook logic live in Application/Hosts/Infrastructure/Cli — never in Core. ✅
- **Single source → projection, CI-gated**: resources authored under `artifacts/skills/<name>/<resource>/` and projected; `generate --check` stays the drift gate; goldens add intent-level coverage. ✅
- **Determinism / byte-stability**: resource copy + goldens are deterministic; eval scoring is deterministic lexical (no live LLM in CI). ✅
- **No-network**: unaffected; `claude plugin validate` smoke is a dev/CI tool check, skipped when the CLI is absent. ✅
- **Token budget / description standard**: unaffected; the confusion-matrix gate guards any eval-driven description edits. ✅

→ No Complexity Tracking entries.

## Project Structure

### Documentation (this feature)

```text
specs/022-v2-fidelity-gaps/
├── spec.md            # done (clarified)
├── plan.md            # this file
├── research.md        # Phase 0 — decisions (launcher, resource depth, eval, golden, user-file)
├── data-model.md      # Phase 1 — entities (resource set, eval case, golden, policy record, launcher)
├── quickstart.md      # Phase 1 — how to validate the feature end-to-end
├── contracts/         # Phase 1 — hook-launcher, user-file-policy, eval-cases schema, resource-set
│   ├── hook-launcher.md
│   ├── user-file-policy.md
│   ├── eval-cases.schema.md
│   └── skill-resource-set.md
├── tasks.md           # Phase 2 (/speckit.tasks)
└── checklists/        # /speckit.checklist — requirements-quality unit tests
```

### Source Code (repository root) — files touched

```text
artifacts/skills/commands/{constitution,checklist,fix,release}/scripts|examples/   # FR-022-01
artifacts/skills/commands/add-*/examples|assets/                                   # FR-022-02
artifacts/skills/<cluster>/evals/cases.jsonl                                        # FR-022-06
artifacts/skills/microservice/controlpanel/blazor-hybrid/SKILL.md                  # FR-022-20 (or de-scope note in planning/23)
src/DotnetAiKit.Core/Artifacts/Skill.cs                       # SchemaVersion compat check (FR-022-19)
src/DotnetAiKit.Infrastructure/FileSystemArtifactRepository.cs # load resource sets + broken-resource error
src/DotnetAiKit.Hosts/**/<Host>Projector.cs                   # copy resource sets into build/<host>/skills (FR-022-04)
src/DotnetAiKit.Hosts/Claude/ClaudeHooksWriter.cs             # launcher command (FR-022-10)
src/DotnetAiKit.Hosts/Claude/ClaudeHostAdapter.cs            # user-file merge/backup/consent (FR-022-13/14)
src/DotnetAiKit.Application/UseCases/{Init,Check}Service.cs   # shim-shadow detection (FR-022-10)
src/DotnetAiKit.Cli/Commands/HookCommand.cs                  # fail-safe resolution (FR-022-12)
tests/DotnetAiKit.Hosts.Tests/**                             # Verify goldens (FR-022-08/09)
tests/DotnetAiKit.Acceptance.Tests/**                        # resource assertions, hook + install smoke (FR-022-11/17)
tests/DotnetAiKit.Triggering.Evals/**                        # cases.jsonl harness + matrix (FR-022-07)
```

**Structure Decision**: No new projects. The engine already models resources (`SkillResourceSet`) and schema versions (`SchemaVersion`); the work is *populate + load + project + test*, plus the hook-launcher, user-file policy, and remaining-channel additions within existing layers. Goldens land in `Hosts.Tests`; hook/install smoke in `Acceptance.Tests`; eval cases in `Triggering.Evals`. This honors AR-8 (no new abstraction without proven need).

## Phase mapping (spec user stories → build order)

| Phase | Story | Build | Gate |
|---|---|---|---|
| **F1** | US2 (P1) | Hook launcher resolution + shim detection + fail-safe + smoke (FR-022-10/11/12) | hook smoke runs v2 backend; no shim error |
| **F2** | US1 (P1) | Load + project `SkillResourceSet`; author FR-D33 + `add-*` resources + script-trust (FR-022-01..05) | corpus-integrity asserts resources; drift-clean |
| **F3** | US4 (P2) | Verify goldens per projection shape (FR-022-08/09) | goldens green; induced format change fails |
| **F4** | US3 (P2) | `evals/cases.jsonl` + confusion-matrix gate (FR-022-06/07) | SC-D matrix passes/fails-on-collision |
| **F5** | US5 (P2) | User-owned-file merge/backup/consent + `HostWriteResult` (FR-022-13/14) | existing settings.json survives init |
| **F6** | US7 (P3) | Per-host install smoke + Codex/Cursor loadability (FR-022-17/18) | validate --strict in CI; codex/cursor asserted-or-recorded |
| **F7** | US6 (P3) | T2 `prompt` hook + forced-output-style channel (FR-022-15/16) | judgment-deny works; output-style projects |
| **F8** | FR-022-19/20 | SchemaVersion migration check + `blazor-hybrid` parity | out-of-range fails w/ guidance; corpus==catalog |

**Cross-cutting (every phase)**: build `-warnaserror` 0/0 · full test suite · `dotnet format` · `generate --check` drift-clean · cross-platform (NFR-3). MVP = F1 (hooks runnable) + F2 (resources).

## Complexity Tracking

No constitution violations → not applicable.
