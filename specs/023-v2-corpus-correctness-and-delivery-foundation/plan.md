# Implementation Plan: dotnet-ai-kit v2 - Corpus Correctness and Delivery Foundation

**Branch**: `023-v2-corpus-correctness-and-delivery-foundation` | **Date**: 2026-06-02 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/023-v2-corpus-correctness-and-delivery-foundation/spec.md`

## Summary

Repair the highest-risk v2 corpus and delivery defects before expansion work. The implementation fixes broken shipped artifact samples, localized serious correctness/security guidance defects, MediatR Tier-A policy drift, obvious v1/Python residue in touched guidance, Cursor plugin manifest/agent delivery, and real manifest integrity verification. The work remains a focused foundation slice; profile delivery, MCP/LSP projection, .NET script porting, progressive-disclosure enrichment, analyzer expansion, W7 expansion, and the kit MCP server are intentionally deferred to later specs.

## Technical Context

**Language/Version**: C# on .NET 10 SDK 10.0.300; analyzer projects remain `netstandard2.0`  
**Primary Dependencies**: System.CommandLine, Spectre.Console, YamlDotNet, Microsoft.CodeAnalysis, xUnit, Verify.Xunit  
**Storage**: Filesystem only; authored source in `artifacts/`, generated output in `build/`, per-solution footprint under `.dotnet-ai-kit/`  
**Testing**: xUnit suites in `tests/`; existing gates are build, test, format, and generate drift check  
**Target Platform**: Windows, macOS, Linux  
**Project Type**: .NET CLI tool, Roslyn analyzer package, and multi-host AI plugin projection  
**Performance Goals**: Preserve existing `generate` determinism and `check` speed; no broad full-corpus semantic compilation requirement  
**Constraints**: No network in local verbs; generated `build/` files are not hand-edited; fix authored artifacts/projectors then regenerate; preserve hexagonal dependencies  
**Scale/Scope**: 182 skills, 15 agents, 21 rules, 12 profiles, 16 knowledge docs; this feature touches only targeted defects plus Cursor delivery and manifest integrity

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Detect-First / Respect-Existing**: The feature repairs existing corpus/projector behavior and adds regression checks; it does not change target project detection behavior. PASS.
- **Pattern Fidelity**: Artifact repairs must match local guidance style and the existing single-source projection model. PASS.
- **Architecture & Platform Agnostic**: Use `Path` APIs and deterministic projection; no OS-specific shell logic in product code. PASS.
- **Best Practices & Quality**: Tests and review gates are first-class; broken security/data-integrity guidance is explicitly repaired. PASS.
- **Safety & Token Discipline**: Scope is bounded; no blanket resource expansion; generated output remains derived. PASS.

No constitution violations require Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/023-v2-corpus-correctness-and-delivery-foundation/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- artifact-repair.md
|   |-- cursor-plugin-delivery.md
|   `-- manifest-integrity.md
|-- tasks.md
`-- checklists/
    `-- requirements.md
```

### Source Code (repository root)

```text
artifacts/
|-- skills/          # targeted broken samples, MediatR drift, v1 residue
|-- agents/          # targeted MediatR/default guidance drift if present
|-- rules/           # targeted v1 residue or MediatR drift if in scope
`-- knowledge/       # targeted broken samples and policy drift

src/
|-- DotnetAiKit.Application/UseCases/CheckService.cs
|-- DotnetAiKit.Hosts/Cursor/CursorProjector.cs
|-- DotnetAiKit.Hosts/FrontmatterWriter.cs
`-- DotnetAiKit.Infrastructure/ManifestIntegrityService.cs

tests/
|-- DotnetAiKit.Acceptance.Tests/
|-- DotnetAiKit.Application.Tests/
`-- DotnetAiKit.Hosts.Tests/

build/               # regenerated only; no hand edits
```

**Structure Decision**: No new production project is needed. Cursor delivery changes stay in `DotnetAiKit.Hosts`; manifest integrity check behavior stays in Application/Infrastructure; artifact repairs stay in `artifacts/`; tests are added to the existing xUnit projects.

## Phase Mapping

| Phase | Work | Gate |
|---|---|---|
| Phase 0 | Research decisions and defect selection | `research.md` records included/deferred defect policy |
| Phase 1 | Design contracts and testable entities | contracts, data model, quickstart complete |
| Phase 2 | Task generation | `tasks.md` includes Review & Verification phase |
| Phase 3 | Implement artifact correctness repairs | targeted guards pass, generated output drift-clean |
| Phase 4 | Implement Cursor delivery repair | manifest-reference resolution test passes |
| Phase 5 | Implement manifest integrity repair | tamper test fails `check` as expected |
| Phase 6 | Review & Verification | changed artifacts/source/build output reviewed; all gates pass |
| Phase 7 | Polish | docs/status cleanup only |

## Complexity Tracking

No constitution violations.

## Standing Gates

Every implementation increment must keep or restore:

```powershell
dotnet build dotnet-ai-kit.slnx -warnaserror
dotnet test dotnet-ai-kit.slnx
dotnet format dotnet-ai-kit.slnx --verify-no-changes
dotnet run --project src/DotnetAiKit.Cli -- generate --check
```

Additional gates for this feature:

- Cursor manifest references resolve.
- Manifest tampering fails the manifest-integrity check.
- Repaired broken samples have feasible regression guards.
- Touched generated output changes only through regeneration.
