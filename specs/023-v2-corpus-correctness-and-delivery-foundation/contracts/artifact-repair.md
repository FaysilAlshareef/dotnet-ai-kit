# Contract: Artifact Repair

## Purpose

Define how this feature records and verifies repairs to shipped artifact defects.

## Inputs

- Defect inventory from:
  - `planning/30-artifacts-content-review.md`
  - `planning/30-appendix-all-artifacts.md`
  - Relevant sequencing from `planning/29-v2-execution-plan-fidelity-and-enhancement.md`
- Authored artifacts under `artifacts/`.

## Required Behavior

- Each selected broken sample is fixed, removed, or replaced in authored source.
- Each selected serious localized defect is repaired in authored source.
- Each Tier-A MediatR drift item is aligned with `mediator-abstraction`.
- Each touched v1/Python residue item is removed or reframed as external tooling only where appropriate.
- Generated output changes only through `dotnet-ai generate`.

## Verification

- Search or tests prove the repaired text/pattern is absent.
- Syntax parsing or focused fixture tests are added where feasible.
- `generate --check` passes after regeneration.
- Review phase confirms no hand edits to `build/`.
