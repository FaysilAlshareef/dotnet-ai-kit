# Research: dotnet-ai-kit v2 - Corpus Correctness and Delivery Foundation

## R1: Feature Boundary

**Decision**: Treat this feature as the first repair slice, not the entire planning 28/29/30 backlog.

**Rationale**: The planning backlog includes profile delivery, MCP/LSP projection, script porting, progressive disclosure, analyzer growth, W7 expansion, and the kit MCP server. Combining those with artifact correctness would create a large feature with many shared generated-output conflicts. The foundation slice fixes shipped correctness and delivery problems first.

**Alternatives considered**: Implement all phases from planning 29 in one spec. Rejected because it would mix repair, projection architecture, corpus expansion, and runtime server work.

## R2: Defect Selection

**Decision**: Include the 8 broken samples from `planning/30`, localized serious correctness/security defects from section 3 where they can be fixed directly, and Tier-A MediatR policy drift. Defer broad architecture/profile/eval/enrichment work.

**Rationale**: Broken samples and serious localized defects are user-facing correctness risks. Tier-A MediatR drift contradicts an existing always-on rule and is policy-critical. Broad progressive-disclosure and analyzer work should be handled by later feature specs.

**Alternatives considered**: Fix only engine delivery bugs. Rejected because shipped corpus correctness is the highest product risk.

## R3: Cursor Plugin Delivery

**Decision**: Emit Cursor agents and realign the Cursor plugin manifest under the Cursor plugin root, then add a manifest-reference resolution test.

**Rationale**: Current generated output is drift-clean but structurally broken: the manifest references agents that are not emitted. A drift gate cannot catch missing referenced files if the projector itself intentionally emits the bad shape.

**Alternatives considered**: Drop the `agents` array from the manifest. Rejected for this feature because planning 29 selected "emit + realign" as the higher-fidelity path.

## R4: Manifest Integrity

**Decision**: Implement actual manifest integrity verification in `CheckService` using the existing `ManifestIntegrityService`, unless implementation discovers that the persisted manifest format lacks sufficient data; in that case, rename the check honestly and record full integrity as deferred.

**Rationale**: The current check says "manifest-integrity" but only checks file presence. That is a misleading guarantee. A tamper-detection test must define the real contract.

**Alternatives considered**: Leave the presence check unchanged. Rejected because it keeps a known false guarantee in the product.

## R5: Review Phase

**Decision**: Add an explicit `Review & Verification` phase to `tasks.md`.

**Rationale**: `.claude/commands` has `speckit.analyze`, but that command is a pre-implementation consistency analysis, not a post-implementation review. There is no `speckit.review` command, so review must be represented as executable tasks.

**Alternatives considered**: Rely on `speckit.analyze`. Rejected because it is read-only and runs before implementation.

## Deferred Defect Ledger

The following planning/30 themes are intentionally deferred because they require
separate feature boundaries rather than localized repairs:

- Profile deduplication and always-on profile delivery -> `024-v2-profile-rule-and-dynamic-delivery`.
- C# script porting and event-catalogue/changelog script cleanup -> `025-v2-dotnet-script-and-tooling-cleanup`.
- Progressive disclosure for references, examples, evals, and descriptions -> `026-v2-progressive-disclosure-and-triggering`.
- New analyzer expansion beyond existing repair guards -> `027-v2-analyzers-and-deterministic-enforcement`.
- W7 expansion skills and agents -> `028-v2-expansion-skills-and-agents`.
- Kit MCP server runtime and LSP/MCP projection -> `029-v2-kit-mcp-server`.
