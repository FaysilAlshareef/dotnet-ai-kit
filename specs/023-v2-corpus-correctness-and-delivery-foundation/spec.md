# Feature Specification: dotnet-ai-kit v2 - Corpus Correctness and Delivery Foundation

**Feature Branch**: `023-v2-corpus-correctness-and-delivery-foundation`  
**Created**: 2026-06-02  
**Status**: Draft  
**Input**: User description: "Repair highest-risk shipped corpus and delivery defects before expansion work: broken artifact samples, localized serious correctness/security bugs, MediatR Tier-A policy drift, obvious v1/Python residue, Cursor plugin delivery, real manifest integrity in check, and regression gates. Keep profile delivery, MCP/LSP projection, C# script porting, progressive-disclosure relocation, W7 expansion, and kit MCP server out of scope. Generated output remains single-source from artifacts; tasks must include Review & Verification phase."

## Overview

The current v2 corpus and projection engine are green under the standing build, test, format, and generation gates, but the latest planning review identifies shipped correctness and delivery defects that those gates do not catch. This feature establishes a repair foundation before broader profile delivery, MCP/LSP projection, script conversion, progressive-disclosure enrichment, analyzer growth, or W7 expansion work begins.

The feature focuses on high-risk defects that are already documented in `planning/29-v2-execution-plan-fidelity-and-enhancement.md`, `planning/30-artifacts-content-review.md`, and `planning/30-appendix-all-artifacts.md`: broken artifact samples, localized serious correctness/security bugs, MediatR policy drift, v1/Python residue in shipped guidance, Cursor plugin manifest/agent delivery, and manifest integrity verification.

## Clarifications

### Session 2026-06-02

- Q: Should this feature include all work from planning 28, 29, and 30? -> A: No. This feature is the first repair slice only: artifact correctness, Cursor delivery, and manifest integrity. Profile delivery, MCP/LSP projection, script porting, progressive disclosure, analyzer expansion, W7 expansion, and the kit MCP server are separate follow-on features.
- Q: How should review be handled when there is no `/speckit.review` command? -> A: The generated `tasks.md` must include a dedicated `Review & Verification` phase after implementation phases and before final polish.
- Q: May generated host output be edited directly? -> A: No. Generated `build/` output remains single-source from authored `artifacts/` and host projectors; any build output changes must come from regeneration.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Broken Shipped Guidance Is Repaired (Priority: P1)

A maintainer reading or using shipped skills and knowledge docs can rely on the examples to be accurate enough to copy, adapt, or validate. The known broken samples and localized serious correctness/security bugs from the content review are fixed or explicitly removed from the shipped guidance.

**Why this priority**: Broken samples and security/data-integrity bugs are the highest product risk. They can teach users to write code that fails to compile, loses writes, leaks data, or handles security incorrectly.

**Independent Test**: Run targeted artifact checks for every fixed broken sample and localized serious defect, then regenerate all host outputs and confirm no drift remains.

**Acceptance Scenarios**:

1. **Given** the 8 broken artifact samples listed in `planning/30`, **When** the repaired corpus is reviewed, **Then** each sample is fixed, removed, or replaced with a correct pattern.
2. **Given** localized serious correctness/security defects from `planning/30` section 3, **When** the repaired artifacts are inspected, **Then** the shipped guidance no longer teaches the defective behavior.
3. **Given** repaired authored artifacts, **When** projection runs, **Then** all generated host outputs reflect the authored repairs and remain drift-clean.

---

### User Story 2 - License-Safe Mediator Guidance Is Consistent (Priority: P1)

A developer following CQRS, architecture, handler, and agent guidance receives one consistent policy: MediatR is not the default dependency, domain/application code does not depend directly on MediatR, and handler dispatch is abstracted behind the existing license-safe mediator policy.

**Why this priority**: The corpus currently contains a systemic contradiction: the always-on mediator-abstraction rule says MediatR is commercial and should be abstracted, while several artifacts still teach raw MediatR as the default.

**Independent Test**: Search the targeted Tier-A artifact set for domain-layer MediatR leaks and raw default installation guidance; verify each violation is removed or redirected to the license-safe abstraction policy.

**Acceptance Scenarios**:

1. **Given** architecture and CQRS artifacts that previously declared domain events as `INotification`, **When** the feature is complete, **Then** domain-level event contracts no longer depend on MediatR types.
2. **Given** artifacts that previously said to install or register MediatR as the default, **When** the feature is complete, **Then** they either use a project-owned dispatch port or explicitly frame MediatR as licensed opt-in.
3. **Given** agents or knowledge docs that named MediatR as the default, **When** they are inspected, **Then** they align with the mediator-abstraction rule.

---

### User Story 3 - Cursor Plugin Delivery Is Structurally Valid (Priority: P1)

A Cursor user installing the generated plugin receives a coherent plugin directory: the manifest is under the Cursor plugin root and every file referenced by the manifest exists in the generated output.

**Why this priority**: Current generation is drift-clean but structurally broken for Cursor. The manifest references `./agents/*.md` files that are not emitted, so the drift gate cannot prove loadability.

**Independent Test**: Generate the Cursor output and run a manifest-reference resolution test that fails if any path referenced by the Cursor plugin manifest is missing.

**Acceptance Scenarios**:

1. **Given** the generated Cursor plugin manifest, **When** each referenced relative path is resolved from the plugin root, **Then** every referenced agent file exists.
2. **Given** the generated Cursor output, **When** the plugin directory is inspected, **Then** manifest, skills, rules, commands, and agents are in one coherent Cursor plugin tree.
3. **Given** a future projector change that introduces a dangling manifest reference, **When** tests run, **Then** the manifest-reference test fails.

---

### User Story 4 - Manifest Integrity Detects Tampering (Priority: P2)

A maintainer running `check` gets a real manifest-integrity signal. A missing manifest and a tampered manifest are distinguishable, and the `manifest-integrity` check no longer passes merely because a file exists.

**Why this priority**: The current check name overpromises. A tested SHA-256 service exists, but the check path only verifies presence.

**Independent Test**: Initialize or fixture a project manifest, tamper with its contents, run `check`, and verify the manifest-integrity check fails with the documented exit code.

**Acceptance Scenarios**:

1. **Given** a valid initialized manifest, **When** `check` runs, **Then** manifest integrity passes.
2. **Given** a tampered manifest, **When** `check` runs, **Then** manifest integrity fails.
3. **Given** a missing manifest, **When** `check` runs, **Then** the user receives a clear missing-manifest failure distinct from a tamper failure.

---

### User Story 5 - v1/Python Residue Is Removed From Touched Shipped Guidance (Priority: P2)

A user reading touched command, workflow, rule, or setup guidance sees the v2 .NET CLI as the active implementation and is not told to install or call removed v1 Python tooling.

**Why this priority**: Stale Python instructions directly contradict the v2 rewrite and can send users to nonexistent or wrong tooling.

**Independent Test**: Search touched artifacts and generated outputs for known stale phrases such as `pip install dotnet-ai-kit`, nonexistent `mcp_check`, `.py`-only stack references in .NET rules, `pytest`, and `ruff` where they are not intentionally scoped.

**Acceptance Scenarios**:

1. **Given** touched setup or command guidance, **When** a user follows installation instructions, **Then** they are directed to the .NET global tool rather than the removed Python package.
2. **Given** touched .NET-only testing or verification guidance, **When** it is inspected, **Then** Python-only tools are absent unless explicitly marked as external MCP/tooling setup outside the kit implementation.
3. **Given** generated host output, **When** stale v1 residue checks run over touched projections, **Then** no repaired residue reappears through projection.

### Edge Cases

- A `planning/30` issue is broad, architectural, or better suited to a follow-on feature -> record it as deferred rather than partially fixing it in this feature.
- A broken artifact sample cannot be semantically compiled inside this repo because it references external framework types -> add the strongest feasible guard, such as syntax parsing, targeted text assertion, or focused regression fixture.
- A Cursor manifest references a glob-like or optional path -> the test must define whether that path is required or remove the reference.
- A generated build file appears broken -> fix the authored artifact or projector, then regenerate; do not hand-edit generated output.
- Manifest integrity metadata is absent from the existing manifest shape -> define a deterministic compatible representation or explicitly rename the check if full integrity is not implemented.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST repair the 8 broken shipped artifact samples identified in `planning/30-artifacts-content-review.md`.
- **FR-002**: The system MUST repair localized serious correctness/security defects from `planning/30` section 3 when they are scoped to specific artifacts and do not require a larger follow-on architecture feature.
- **FR-003**: The system MUST explicitly defer serious defects that are too broad for this foundation feature and identify the follow-on feature where they belong.
- **FR-004**: The corpus MUST remove Tier-A MediatR policy violations from targeted architecture, CQRS, agent, rule, and knowledge artifacts.
- **FR-005**: Domain-level event guidance MUST NOT require domain contracts to implement MediatR `INotification`.
- **FR-006**: Guidance that mentions MediatR as an implementation option MUST frame it as licensed opt-in or behind a project-owned dispatch abstraction.
- **FR-007**: Touched artifacts MUST remove stale v1/Python CLI residue that contradicts the v2 .NET CLI implementation.
- **FR-008**: The Cursor projector MUST emit a coherent plugin tree where the Cursor manifest lives under the Cursor plugin root.
- **FR-009**: Any agent path referenced by the Cursor manifest MUST be emitted by generation or removed from the manifest.
- **FR-010**: Tests MUST fail if any Cursor manifest reference points to a missing generated file.
- **FR-011**: The `check` manifest-integrity entry MUST verify actual manifest integrity rather than only file presence.
- **FR-012**: Manifest tampering MUST cause `check` to fail with the documented manifest-integrity result.
- **FR-013**: Missing-manifest failures MUST remain clear and actionable.
- **FR-014**: Generated `build/` files MUST remain single-source outputs from `artifacts/` and projectors; this feature MUST NOT rely on hand edits to generated files.
- **FR-015**: The test suite MUST include targeted regression coverage for repaired sample defects where feasible.
- **FR-016**: The generated `tasks.md` for this feature MUST include a `Review & Verification` phase after implementation phases and before final polish.
- **FR-017**: The `Review & Verification` phase MUST review changed source, changed artifacts, generated output, policy consistency, and the standing gates.

### Key Entities

- **Artifact repair item**: A broken sample or localized serious defect from the planning review, with a source artifact, defect summary, repair action, and regression guard.
- **Cursor plugin reference**: A relative path declared in the Cursor plugin manifest that must resolve from the plugin root to a generated file.
- **Manifest integrity record**: The data needed to verify whether `.dotnet-ai-kit/manifest.json` content matches the expected deterministic manifest state.
- **Policy drift item**: A guidance statement that contradicts the mediator-abstraction rule or the v2 .NET-only implementation posture.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All standing gates pass: `dotnet build dotnet-ai-kit.slnx -warnaserror`, `dotnet test dotnet-ai-kit.slnx`, `dotnet format dotnet-ai-kit.slnx --verify-no-changes`, and `dotnet run --project src/DotnetAiKit.Cli -- generate --check`.
- **SC-002**: Cursor manifest-reference resolution is tested and passes for the generated output.
- **SC-003**: A tampered manifest causes `check` to fail manifest integrity in an automated test.
- **SC-004**: Every broken artifact sample selected from `planning/30` has a recorded repair and feasible regression guard.
- **SC-005**: Tier-A MediatR policy drift is removed from the targeted artifact set or redirected to the license-safe abstraction policy.
- **SC-006**: Touched artifacts and their generated outputs contain no contradictory v1/Python CLI residue.
- **SC-007**: The feature's `tasks.md` contains an explicit `Review & Verification` phase before final polish.
