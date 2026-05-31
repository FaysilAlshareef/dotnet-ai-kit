# Phase 1 Data Model: v2 Completion (delta)

**Feature**: 021-v2-completion. The Core domain is **unchanged from 020** ([../020-v2-net10-rewrite/data-model.md](../020-v2-net10-rewrite/data-model.md)): `Skill/Agent/Rule/Profile/Fragment/KnowledgeDoc/ArtifactCorpus`, value objects, `ArtifactGraph`, `PluginManifest`, policies. This feature populates that model at full scale and adds two **documents** (not Core types) + minor engine touch-points.

## Reused (no change)
- `ArtifactCorpus`, `ArtifactGraph` (broken-edge gate), `Skill.CountsAgainstListing`, `Rule.UniversalWhitelist`, `DescriptionStandard`, `HostCapabilityMatrix`, the projectors.

## New documents (authored, not code types)
- **Parity assessment** (`specs/021-v2-completion/contracts/parity-assessment.md`): table mapping each v1 CLI capability → its .NET equivalent + status (covered / gap). Gates Python removal (FR-020).
- **Migration mapping** (`contracts/migration-mapping.md`): the deterministic v1→v2 transform rules (the script's contract).

## Engine touch-points added this feature
- **`check` capability validation** (FR-014/T048): `CheckService` (or a budget/capability checker) validates that each artifact's declared `requires-capability` exists in `HostCapabilityMatrix` and is not `Unsupported` without a fallback. New check entry; no new exit code (folds into existing classes or a warning).
- **Manifest sha256 integrity** (T056): a `ManifestIntegrityService` computing/validating a sha256 over the manifest (ports v1 `manifest.py`).
- **Analyzer code-fix** (T060): `ConventionCodeFixProvider` offering the mechanical fix for DAK0004 (make setter private) / DAK0001 (Task return) where safe.
- **Distribution** (T080-82): `PackAsTool`/`ToolCommandName` on `DotnetAiKit.Cli`; `build/marketplace.json` generated; install smoke test.

## Invariants enforced at scale (the corpus-integrity test, FR-013/SC-002)
For **every** artifact in the loaded corpus:
1. loads without error; 2. `name == directory/file name`; 3. contributes to a graph that builds with zero broken edges; 4. projects to all four hosts (non-empty output per host where applicable).
Plus: migrated-artifact DescriptionStandard compliance is **counted** (metric); new/structural artifacts **must** pass (hard).
