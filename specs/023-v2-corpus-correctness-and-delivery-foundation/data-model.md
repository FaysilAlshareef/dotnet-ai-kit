# Data Model: dotnet-ai-kit v2 - Corpus Correctness and Delivery Foundation

## Entities

### ArtifactRepairItem

| Field | Type | Description |
|---|---|---|
| `ArtifactPath` | string | Authored artifact path under `artifacts/` |
| `PlanningSource` | string | Planning document and section that reported the issue |
| `DefectClass` | enum | BrokenSample, SeriousCorrectness, Security, PolicyDrift, V1Residue |
| `RepairAction` | enum | Fix, Remove, Replace, Defer |
| `RegressionGuard` | string | Test, search assertion, syntax parse, or documented manual guard |

### CursorPluginReference

| Field | Type | Description |
|---|---|---|
| `ManifestPath` | string | Generated Cursor manifest path |
| `PluginRoot` | string | Directory from which relative references resolve |
| `RelativeReference` | string | Manifest-declared path such as `./agents/name.md` |
| `ResolvedPath` | string | Expected generated file path |
| `Exists` | bool | Whether generation produced the referenced file |

### ManifestIntegrityState

| Field | Type | Description |
|---|---|---|
| `ManifestPath` | string | `.dotnet-ai-kit/manifest.json` path |
| `ExpectedHash` | string | SHA-256 hash expected by the integrity contract |
| `ActualHash` | string | SHA-256 hash computed from current contents |
| `Status` | enum | Missing, Valid, Tampered, Unsupported |
| `ExitCode` | int | Check result code |

### PolicyDriftItem

| Field | Type | Description |
|---|---|---|
| `ArtifactPath` | string | File containing policy drift |
| `PolicyArea` | enum | MediatorAbstraction, V2DotnetOnly, CommercialLibrary |
| `CurrentGuidance` | string | Problematic guidance summary |
| `TargetGuidance` | string | Replacement or redirect summary |
| `Guard` | string | Search/test/review guard |

## Relationships

- `ArtifactRepairItem` may produce one or more `PolicyDriftItem` records when the defect is policy-related.
- `CursorPluginReference` records are derived from the generated Cursor manifest and must all resolve after generation.
- `ManifestIntegrityState` is evaluated by `CheckService`; a Tampered or Missing state maps to manifest-integrity failure.
- Regression guards attach to each repair item so the same defect class does not silently return.

## Validation Rules

- Every included broken sample must have `RepairAction != Defer`.
- Every deferred serious defect must state the target follow-on feature.
- Every Cursor manifest reference must resolve to an emitted generated file.
- Manifest tampering must not pass as Valid.
- Generated `build/` files are derived output and cannot be listed as the source of truth for a repair.
