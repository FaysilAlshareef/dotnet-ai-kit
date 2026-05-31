# Implementation Plan: dotnet-ai-kit v2 — Planning-Fidelity Gaps

**Branch**: `022-v2-fidelity-gaps` | **Date**: 2026-05-31 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/022-v2-fidelity-gaps/spec.md`

## Summary

Close the specified-but-absent/stubbed gaps between `planning/20`–`26` (26 authoritative) and the codebase, on top of the green 020+021 engine: populate skill resources where they add value (FR-D33 set + `add-*` + cluster evals), make the enforcement hooks actually runnable (fix the `dotnet-ai` v1-shim shadowing), author `evals/cases.jsonl` + a confusion-matrix gate, add Verify golden baselines, implement the user-owned-file policy, add the remaining enforcement channels (T2 `prompt` hook, forced output styles), codify per-host install smoke tests, and verify Codex/Cursor loadability. Every change keeps the corpus graph-consistent, projects to four hosts, stays drift-clean, and keeps all gates green.

## Technical Context

**Language/Version**: C# 13 on .NET 10 (SDK 10.0.300); analyzers/codefixes netstandard2.0.
**Primary Dependencies**: System.CommandLine 2.0.8 · Spectre.Console (behind `IConsoleReporter`) · YamlDotNet · Microsoft.ML.Tokenizers · Microsoft.CodeAnalysis (+ Workspaces for codefixes) · xUnit + **Verify.Xunit** (already referenced, unused).
**Storage**: filesystem only (artifacts/ source → build/ projections), via `IFileSystem`.
**Testing**: xUnit; `Acceptance.Tests` (cross-host invariants) · `Hosts.Tests` (projector golden) · `Triggering.Evals` (selector) · analyzer tests; external `claude` CLI v2.1.154 available for plugin-validate smoke.
**Target Platform**: Windows/macOS/Linux (NFR-3); hooks invoked by host CLIs.
**Project Type**: CLI tool + shipped Roslyn analyzer/codefix NuGets + projected per-host plugin.
**Performance Goals**: `check` < 10 s; `render` < 2 s; `generate` deterministic/idempotent (NFR-5) — unchanged.
**Constraints**: no-network for init/check/migrate/render/generate (NFR-1); byte-stable deterministic projection; AOT-friendly (no reflection on the hot path); descriptions hard-gated.
**Scale/Scope**: 181 skills / 32 command-skills / 15 agents / 21 rules / 12 profiles; 4 hosts; ~834 generated files. This feature touches a *subset* of skills (resources), the projectors (resource copy + golden), the hook launcher + `init` write path, and the test projects.

## Constitution Check

`.specify/memory/constitution.md` (v1.1.0) principles preserved:
- **Clean architecture / Core purity**: resource-set population is corpus authoring + a Core value object that already exists; the user-file policy + hook-launcher logic live in Application/Hosts/Infrastructure, not Core. ✅
- **Single source → projection, CI-gated**: resources are authored under `artifacts/skills/<name>/<resource>/` and projected; `generate --check` remains the drift gate. ✅
- **Determinism**: resource copy is byte-stable; goldens are deterministic. ✅
- **No-network**: unaffected; the `claude plugin validate` smoke is a dev/CI tool check, gated on the CLI being present (skipped otherwise). ✅
- **Description standard / token budget**: unaffected (no description churn beyond eval-driven fixes, which the matrix gate guards). ✅

No violations → no Complexity Tracking entries.

## Project Structure

### Documentation (this feature)

```text
specs/022-v2-fidelity-gaps/
├── spec.md          # done
├── plan.md          # this file
├── tasks.md         # the actionable work list (next)
└── contracts/       # (optional) hook-launcher contract + user-file-policy contract
```

### Source Code (repository root) — touched by this feature

```text
artifacts/skills/commands/{constitution,checklist,fix,release}/scripts|examples/   # FR-022-01
artifacts/skills/commands/add-*/examples|assets/                                    # FR-022-02
artifacts/skills/<cluster>/evals/cases.jsonl                                         # FR-022-06
src/DotnetAiKit.Core/Artifacts/Skill.cs                 # SkillResourceSet already present; schema-version check (FR-022-19)
src/DotnetAiKit.Infrastructure/FileSystemArtifactRepository.cs  # load resource sets from disk
src/DotnetAiKit.Hosts/**/<Host>Projector.cs             # copy resource sets into build/<host>/skills (FR-022-04)
src/DotnetAiKit.Hosts/Claude/ClaudeHooksWriter.cs       # launcher resolution (FR-022-10)
src/DotnetAiKit.Hosts/Claude/ClaudeHostAdapter.cs       # user-file merge/backup/consent (FR-022-13/14)
src/DotnetAiKit.Cli/Commands/HookCommand.cs             # fail-safe resolution (FR-022-12)
tests/DotnetAiKit.Hosts.Tests/**                        # Verify golden baselines (FR-022-08)
tests/DotnetAiKit.Acceptance.Tests/**                   # resource-set assertions, install smoke (FR-022-11/17)
tests/DotnetAiKit.Triggering.Evals/**                   # cases.jsonl harness + matrix (FR-022-07)
```

**Structure Decision**: No new projects. Resources are corpus content under `artifacts/`; the engine already models them (`SkillResourceSet`) — the work is *populate + load + project + test*, plus the hook-launcher, user-file-policy, and remaining-channel additions within the existing layers. Verify golden tests land in the existing `Hosts.Tests`; install smoke in `Acceptance.Tests`.

## Phasing (maps spec user stories → build order)

| Phase | User story | Build | Gate |
|---|---|---|---|
| **F1** | US2 (P1) | Fix hook launcher resolution + fail-safe + smoke test (FR-022-10/11/12) — makes 021's wired hooks runnable | hook smoke runs v2 backend; no shim error |
| **F2** | US1 (P1) | Load + project `SkillResourceSet`; author FR-D33 + `add-*` resources + trust model (FR-022-01..05) | corpus-integrity asserts resources; drift-clean |
| **F3** | US4 (P2) | Verify golden baselines for every projection shape (FR-022-08/09) | goldens green; induced format change fails |
| **F4** | US3 (P2) | `evals/cases.jsonl` for clusters + confusion-matrix gate (FR-022-06/07) | SC-D matrix passes/fails-on-collision |
| **F5** | US5 (P2) | User-owned-file merge/backup/consent + `HostWriteResult` reporting (FR-022-13/14) | existing settings.json survives init |
| **F6** | US7 (P3) | Per-host install smoke (Claude validate codified) + Codex/Cursor loadability (FR-022-17/18) | validate --strict in CI; codex/cursor asserted-or-recorded |
| **F7** | US6 (P3) | T2 `prompt` hook + forced-output-style channel (FR-022-15/16) | judgment-deny works; output-style projects |
| **F8** | FR-022-19 | Schema-version compatibility/migration check | out-of-range version fails load with guidance |

**Cross-cutting (every phase)**: keep build `-warnaserror` 0/0, full test suite green, `dotnet format` clean, `generate --check` drift-clean (NFR), cross-platform discipline (NFR-3).

## Open clarifications (carry into tasks)

- **FR-022-10 launcher mechanism** (plugin-root launcher vs. required global `dotnet tool install` vs. `dotnet <dll>`) — resolve in F1; default lean = plugin-root-relative launcher so no global install is required, plus document removing the stale v1 shim.
- Resource depth per `add-*` skill (one canonical compilable example vs. a small set) — decide in F2 per skill value; AR-5 keeps it minimal-but-real.
