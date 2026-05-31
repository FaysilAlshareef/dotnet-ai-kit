# Implementation Plan: dotnet-ai-kit v2 — Completion

**Branch**: `021-v2-completion` | **Date**: 2026-05-31 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/021-v2-completion/spec.md`

## Summary

Complete the v2 rewrite on top of the feature-020 engine. The work is a **deterministic bulk migration** of the v1 corpus into `artifacts/` (verified by the engine's own `Load()` + drift gate), plus structural new artifacts, a project restructure that removes the dead v1 layout, completion of the deferred .NET features with a parametrized corpus-integrity test, rewritten docs + CI, and a parity-gated removal of the Python v1. Authoring is hand/subagent; the migration is a throwaway script. Scope is tiered: the **anchor** (migration + structural artifacts + restructure + plugin/docs/CI + integrity test + deferred features) is built green; the **~30 new-domain skills** are baseline-authored.

## Technical Context

**Language/Version**: C# 13 on .NET 10 (SDK 10.0.300); analyzer netstandard2.0 — unchanged from 020
**Primary Dependencies**: System.CommandLine 2.0.8, Spectre.Console, YamlDotNet, Microsoft.ML.Tokenizers, Microsoft.CodeAnalysis, xUnit + Verify — unchanged from 020. Migration script: Python (throwaway, dev-time only)
**Storage**: filesystem (`artifacts/` source, `build/` generated). No DB.
**Testing**: xUnit + Verify; a new parametrized **corpus-integrity** test over the full corpus; deferred-feature tests; the 020 suite. `dotnet test`.
**Target Platform**: cross-platform CLI (Windows/macOS/Linux)
**Project Type**: single multi-project .NET solution + authored corpus + generated outputs
**Performance Goals**: `generate` deterministic/idempotent at full-corpus scale; `check` < 10 s
**Constraints**: no-network for local verbs; `-warnaserror` clean; `dotnet format` clean; no package vulns; `generate --check` drift-clean; bulk migration verified by `Load()` after each batch
**Scale/Scope**: ≈240 artifacts (32 commands, 15 agents, 21 rules, 12 profiles, ≈160 skills, knowledge); remove ~10 v1 dirs + Python v1 (gated); rewrite docs + 4 CI workflows

## Constitution Check

The repo constitution is **v1.1.0** (amended in 020 to v2 facts). This feature brings reality into line with it:

| Principle | Gate | Status |
|---|---|---|
| I. Detect-First / Respect-Existing | migration preserves v1 content + conventions; no behavior invented | ✅ |
| II. Pattern Fidelity | migrated artifacts keep their bodies; new artifacts match the established v2 SKILL.md shape | ✅ |
| III. Architecture & Platform Agnostic | corpus covers all profiles; cross-platform engine unchanged | ✅ |
| IV. Best Practices & Quality | corpus-integrity test + deferred-feature tests; TDD where new logic is added; docs-first | ✅ |
| V. Safety & Token Discipline | command-skills off-budget; budget check; token-frugal descriptions; DescriptionStandard gate (new) + metric (migrated) | ✅ |

**Counts reconciled to the constitution after migration**: 21 rules (5 universal + 16 domain), 15 agents, 32 commands, 12 profiles, ~160 skills. **No violations.** The constitution's amendment procedure is satisfied (already at 1.1.0).

## Project Structure

### Documentation (this feature)
```text
specs/021-v2-completion/
├── plan.md  research.md  data-model.md  quickstart.md  tasks.md  analysis.md
├── checklists/requirements.md
└── contracts/{migration-mapping.md, parity-assessment.md}
```

### Target repository layout (per planning/22 §1 — after restructure)
```text
artifacts/                 # SINGLE SOURCE: skills/ agents/ rules/{conventions,domain}/ profiles/ fragments/ knowledge/ manifest.yml
src/                       # .NET: Core Application Hosts Infrastructure Cli Analyzers   (Python dotnet_ai_kit/ REMOVED once parity-proven)
tests/                     # .NET test projects (Python tests/ REMOVED with parity)  + tests/fixtures/ (the dotnet-ai-architect Cursor spike)
build/                     # GENERATED per-host outputs + manifests + marketplace.json (drift-gated)
docs/                      # rewritten v2 docs
planning/  issues/         # design record
.github/workflows/         # rewritten .NET CI
.specify/                  # SDD tooling (kept)
Directory.Build.props  Directory.Packages.props  global.json  dotnet-ai-kit.slnx  .editorconfig  .gitattributes  .gitignore  CLAUDE.md  README.md
```
**Removed (dead v1, after migration):** root `skills/ commands/ rules/ agents/ agents-source/ agents-claude/ agents-copilot-templates/ profiles/ knowledge/ config/ prompts/ schemas/` + root `.claude-plugin/` (v1) + (parity-gated) `src/dotnet_ai_kit/` + Python `tests/`. **Kept after a reference check:** `templates/` `bin/` `scripts/` `assets/` `hooks/` only if referenced by `.specify/`/`src/`/workflows/docs (else removed or migrated).

**Structure Decision**: planning/22 is authoritative — generated outputs (incl. the Claude plugin manifest) live under `build/`; the root carries no competing hand-authored plugin manifest. The bulk migration is a deterministic script; the engine's `Load()` + `generate --check` are the gate.

## Phases (execution order)

| Phase | Work | Gate |
|---|---|---|
| **C1 Migration** | throwaway script transforms v1 skills/commands/rules/agents/profiles/knowledge → `artifacts/`; do the 3 consolidations in-pass; drop `when_to_use`; set `metadata.kind/invocation/paths`; resolve agent `skills:` lists | `repo.Load()` Ok (0 broken edges), every name==dir |
| **C2 Generate baseline** | regenerate `build/` for the full corpus (orphan-cleanup drops the 8-artifact baseline); commit migrated `artifacts/` + `build/` (v1 dirs still present) | `generate` + `generate --check` no drift; 4 hosts populated |
| **C3 Structural new artifacts** | 5 new commands (constitution/checklist/orchestrate/release/fix), 2 new agents (aspire-architect/ai-engineer), 5 new rules (mediator-abstraction/messaging-bus-selection/testing-platform/ai-integration + deterministic-enforcement done) — hand-authored, DescriptionStandard hard-gated | Load + drift green; DescriptionStandard passes for new |
| **C4 Corpus-integrity test** | one parametrized test: every artifact loads, name==dir, graph consistent, projects to 4 hosts; + DescriptionStandard metric for migrated, hard gate for new | test green; migrated-compliance count reported |
| **C5 Deferred features** | analyzer code-fix (T060), `check` capability-dependency validation (T048), manifest sha256 integrity (T056), distribution `PackAsTool` + `marketplace.json` + install smoke (T080-82) | tests green |
| **C6 Restructure** | grep-before-delete the ambiguous dirs; remove v1 artifact dirs + root v1 `.claude-plugin/` (separate commit); reconcile one authoritative manifest | build/test/generate green; no orphan dirs |
| **C7 Docs + CI** | rewrite README/CLAUDE.md/docs to v2; rewrite GitHub Actions (.NET build/test/format/drift); remove Python-coupled workflows | CI reflects .NET; no Python refs |
| **C8 New-domain skills (baseline)** | ~30 catalog skills authored to description-standard baseline (hand/subagent); license-light migration skills | each projects + passes the standard |
| **C9 Parity + Python removal** | write the parity assessment (every v1 verb/behavior → .NET); if full, remove `src/dotnet_ai_kit/` + Python tests (same change as CI cutover); else document gaps + retain | parity doc complete; if removed, build/test/generate green with no Python |
| **C10 Final verify** | full `-warnaserror` + format + `generate --check` + test suite + vuln scan; tasks.md + summary state deep-vs-baseline | all green |

**Anchor (must reach green):** C1–C7 + C9 (parity assessment at least; removal if proven). **Baseline:** C8.

## Complexity Tracking

No constitution violations. The migration script is throwaway (not shipped). Restructure is guarded by reference checks (grep) and the separate-commit rule (v1 recoverable). Python removal is parity-gated.
