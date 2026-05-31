# Phase 1 Data Model — v2 Planning-Fidelity Gaps

Entities this feature introduces or activates. Most extend existing Core/Application types rather than add new aggregates (AR-8). Core stays pure; I/O lives in Infrastructure/Hosts.

## SkillResourceSet (exists in Core — activate)

A skill's bundled resources. **Already defined** (`src/DotnetAiKit.Core/Artifacts/Skill.cs` → `Resources : SkillResourceSet = Empty`); this feature **populates** it from disk and **projects** it.

| Field | Type | Notes |
|---|---|---|
| `Scripts` | list of resource files | `.py` default + optional `.ps1`/`.sh` siblings; executable → governed by `ScriptTrust` |
| `Examples` | list of files/dirs | compilable C# (one canonical project per `add-*`) |
| `References` | list of `.md` | long-form reference loaded on demand |
| `Assets` | list of files | `.json`/templates/diagrams |
| `Evals` | `EvalCase[]` (from `cases.jsonl`) | triggering cases for cluster skills |

**Validation**: a declared resource subdir that is empty or references a missing file → corpus load FAILS with a broken-resource error (mirrors the broken-edge gate). Required-set assertion per skill-kind: FR-D33 command-skills MUST have `Scripts`; `add-*` MUST have `Examples`.

## ScriptTrust (new — Application/Core value)

Provenance + trust metadata for an executable bundled script (FR-022-05 / FR-J).

| Field | Type | Notes |
|---|---|---|
| `Path` | string | the script's projected path |
| `Interpreter` | enum {Python, Pwsh, Sh} | from extension |
| `AutoRun` | bool = **false** | scripts are NEVER auto-run without explicit consent |
| `Origin` | enum {Bundled} | authored-in-corpus provenance |

**Rule**: projection records trust; nothing executes a bundled script without consent. Cross-platform: prefer `.py`; ship `.ps1`/`.sh` siblings (NFR-3).

## EvalCase (new — Triggering.Evals)

One line of `evals/cases.jsonl`.

| Field | Type | Notes |
|---|---|---|
| `Query` | string | natural-language trigger phrase |
| `Expect` | string | the skill name that MUST rank #1 |
| `TopK` | int = 1 | acceptable rank window |

**Confusion matrix**: for each case, the deterministic lexical scorer over all sibling-cluster skills MUST rank `Expect` within `TopK` and no sibling above it.

## GoldenBaseline (new — Hosts.Tests, Verify)

A pinned `*.verified.*` projection shape. Not a runtime entity — a test artifact.

| Dimension | Values |
|---|---|
| Artifact-type | skill · agent · rule · command-skill |
| Host | claude · codex · cursor · copilot |
| Singletons | plugin.json (×3 hosts) · marketplace.json · hooks.json · AGENTS.md · copilot-instructions.md |

## UserFilePolicy + outcome (new — Application; activates HostWriteResult fields)

Classifies a host write and records the outcome.

| Field | Type | Notes |
|---|---|---|
| `Classification` | enum {Managed, UserOwned} | UserOwned = `.claude/settings.json`, `AGENTS.md`, `.cursor/rules`, `.github/*` |
| `Action` | enum {Written, Refreshed, Merged, Preserved, PendingConsent} | the resolved action |
| `BackupPath` | string? | set when backed up (3-keep rotation, NFR-7) |

**Maps to** the existing `HostWriteResult.{Written, Preserved, ForceRendered, PendingConsent}` (currently never populated → this feature populates them). State transitions: absent→Written · present-unchanged→Refreshed · present-user-edited+mergeable→Merged · present-user-edited+unmergeable→PendingConsent(+Backup) · invalid-JSON→PendingConsent(+Backup)+warn.

## HookLauncher (resolution policy — Hosts/Application)

How the generated `hooks.json` command resolves the backend (FR-022-10).

| Field | Type | Notes |
|---|---|---|
| `Command` | string | `dotnet-ai hook {event}` (global tool) |
| `ShadowDetected` | bool | `init`/`check` flag: a `dotnet-ai` on PATH that is not the v2 tool |
| `FailSafe` | bool = true | unresolved backend → no spurious block, clear message (FR-022-12) |

## SchemaVersionRange (new — Core constant + check)

| Field | Type | Notes |
|---|---|---|
| `Supported` | SemVer range | e.g. `>=1.0.0 <2.0.0` |
| on-load check | — | out-of-range `SchemaVersion` fails load with migration guidance (FR-022-19) |

## Relationships

- `Skill` 1—1 `SkillResourceSet`; `SkillResourceSet` 0—* `EvalCase` (via `evals/cases.jsonl`); executable `Scripts` 1—1 `ScriptTrust`.
- `IHostProjector` reads `SkillResourceSet` → emits resources under `build/<host>/skills/<name>/` (+ `GoldenBaseline` pins each shape).
- `IHostAdapter.WritePerSolution` consults `UserFilePolicy` → populates `HostWriteResult`.
- `HookLauncher` is emitted by `ClaudeHooksWriter`; `Init/CheckService` set `ShadowDetected`.
