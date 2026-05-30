# Phase 1 Data Model: dotnet-ai-kit v2 Core domain

**Date**: 2026-05-31 · **Feature**: 020-v2-net10-rewrite · **Layer**: `DotnetAiKit.Core` (pure; no I/O, no third-party deps)

The Core models are immutable records with validated value objects (parse-don't-validate). Entities derive from the spec's Key Entities; value objects enforce the invariants that the spec's FRs require.

## Artifact entities

### Skill
The atomic, resource-bearing unit.
- `Name` : `ArtifactName` — kebab, ≤64 chars, **== directory name** (invariant)
- `Description` : `Description` — conforms to the description standard; ≤1024 (portable) / ≤1536 (cap)
- `Frontmatter` : `Frontmatter` — portable core fields + `x-<host>` extension blocks
- `Body` : `string` — ≤500 lines (invariant; Agent Skills standard)
- `Kind` : `SkillKind` — `Knowledge` | `Command`
- `Invocation` : `InvocationPolicy` — default | `DisableModelInvocation` (command-skills) | `UserInvocableFalse` (background)
- `OwningAgent` : `ArtifactName?` — optional owned-by edge source
- `Paths` : `Glob[]` — JIT path-scoping (when location-specific)
- `Resources` : `SkillResourceSet` — optional `scripts/`, `examples/`, `references/`, `assets/`, `evals/` (opt-in; FR-003)
- `SchemaVersion` : `SemVer` — artifact schema version (FR-038)
- **Invariants**: name==dir; name kebab ≤64; body ≤500 lines; description passes `DescriptionStandard`; command-skills default to `DisableModelInvocation`.

### Agent
A specialist persona. **References** skills; carries no bundled resources (FR-003).
- `Name`, `Description`, `Body` (≤120 lines)
- `ReferencedSkills` : `ArtifactName[]` — the owned-by/preload edges
- `RoutingIntents` : `string[]` — phrases that feed the disambiguator
- `HostOverrides` : per-host extension blocks
- **Invariants**: every `ReferencedSkills` entry resolves to a real Skill (graph-checked; FR-006).

### Rule
A convention.
- `Name`, `Body` (≤100 lines)
- `Scope` : `RuleScope` — `Universal` (always-on) | `Domain` (path-scoped)
- `Paths` : `Glob[]` — required when `Scope == Domain` (FR-027)
- `AnalyzerBacked` : `bool` — paired with an analyzer diagnostic (FR-025)
- **Invariants**: `Domain` rules MUST have ≥1 path; `Universal` rules MUST be on the 5-name whitelist.

### Profile
Architecture hard-constraints (path-scoped). ≤100 lines.
- `Name`, `TargetPaths` : `Glob[]`, `ConstraintBody`
- `AnalyzerBackedConstraints` : `string[]` — which constraints are also analyzer diagnostics (spans advisory + deterministic layers; FR-022/025)

### Command (authored as a command-skill)
A user-invoked lifecycle/code-gen action — modeled as a `Skill` with `Kind == Command` and `Invocation == DisableModelInvocation` (kept off the always-loaded budget; FR-007). Not a separate type — this satisfies FR-002's "projection decides surface."

### Fragment
A reusable authored stanza included into skills/commands at projection time (kills duplication).
- `Name`, `Body`

### KnowledgeDoc
Long-form reference; graph-linked, loaded on demand. `Name`, `Body`, `RelatedArtifacts`.

## Graph

### ArtifactGraph / ArtifactNode / ArtifactEdge
Built (never hand-authored) from frontmatter.
- `Nodes` : `ArtifactNode[]` — one per artifact (`Id`, `Kind`)
- `Edges` : `ArtifactEdge[]` — `(From, To, EdgeKind)` where `EdgeKind` ∈ { `OwnedBy`, `RelatesTo`, `TriggeredBy`, `EnforcedBy` }
- **Behavior**: `Build(...)` returns either the graph or a list of broken edges (references to non-existent artifacts); the caller fails the build on any broken edge (FR-006, US1 scenario 3).

## Manifest

### PluginManifest / ComponentMap
The single descriptor → one per-host manifest each.
- `Name` (identical across hosts), `Version` : `SemVer`, `Description`, `Keywords`
- `Components` : `ComponentMap` — skills/agents/rules/commands references
- `HostCapabilities` : `HostCapabilityMatrix` — see contracts/host-capability-matrix.md
- **Invariant**: auto-discovered keys (`hooks`/`mcpServers`/`lspServers`) are **absent** from emitted manifests (FR-010).

## Project metadata (substitution source)

### ProjectMetadata / DetectedPaths / UserConfig
- `ProjectMetadata` : `Company`, `Domain`, `Architecture`, `DotnetVersion`, `DetectedPaths`
- `DetectedPaths` : key → path map (e.g. `entities`, `aggregates`, `endpoints`)
- `UserConfig` : `EnabledHosts` : `HostName[]`, `PermissionProfile`, `Retention`, `PluginVersion`; honors the `ai_tools` → `enabled_hosts` legacy alias on read (FR-018)

## Value objects (`Core/Values`, parse-don't-validate)

| VO | Validates |
|---|---|
| `ArtifactName` | lowercase-kebab, ≤64 chars, no leading/trailing hyphen |
| `Description` | non-empty, ≤1536 chars; (the standard's shape is checked by `DescriptionStandard`, not the VO, to keep VO construction cheap) |
| `Glob` | non-empty glob pattern; normalized to forward slashes |
| `SemVer` | `MAJOR.MINOR.PATCH` |
| `HostName` | one of `claude` \| `codex` \| `cursor` \| `copilot` |
| `TokenBudget` | non-negative count + limit; `IsWithin` |
| `InvocationPolicy` | enum: `Default` \| `DisableModelInvocation` \| `UserInvocableFalse` |
| `SkillKind` | enum: `Knowledge` \| `Command` |
| `RuleScope` | enum: `Universal` \| `Domain` |

## Policies (`Core/Policies`, pure)

- **`DescriptionStandard`** — validator: action-verb-first, third person, explicit "Use when…" trigger, explicit negative scope ("Do NOT use… use X"), concrete nouns. Returns structured violations (CI-gated; FR-026).
- **`TokenBudgetPolicy`** — budget math: which skills are model-invocable, the always-loaded listing fit, consolidation signals (FR-029).
- **`SubstitutionEngine`** — `${Company}`, `${Domain}`, `${detected_paths.<key>}` token replacement via regex over a metadata dictionary (NOT a template engine; FR-005). Detects unresolved tokens after rendering.

## State / lifecycle notes

- Artifacts are immutable once loaded; the repository rebuilds them from disk each run (deterministic; FR-011).
- `HostWriteResult { Written, Preserved, ForceRendered, PendingConsent }` carries per-solution write outcomes (supports the user-owned-file policy FR-037 and the script-trust model FR-036).
