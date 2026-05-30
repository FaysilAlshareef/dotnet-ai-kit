# Contract: CLI verbs (FR-013)

Each verb is a thin `*Command` (System.CommandLine) delegating to an Application use-case. All local verbs honor the no-network invariant (FR-015) and `--dry-run` where they mutate.

| Verb | Use-case | Inputs (key options) | Output / effect | No-network |
|---|---|---|---|---|
| `init` | `InitService` | `[path]`, `--host`, `--include-linked`, `--dry-run` | Writes the bounded per-solution footprint: `.dotnet-ai-kit/{config.yml,project.yml,manifest.json,version.txt}` + `.claude/settings.json` + **`.claude/rules/*.md` with `paths:`** (FR-019). | ✅ |
| `check` | `CheckService` | `[path]`, `--host`, `--json`, `--verbose` | Read-only validation → enumerated exit code (see exit-codes.md); JSON report optional. < 10 s. | ✅ |
| `render` | `RenderService` | `skill\|rule <name>`, `[path]` | Resolves the artifact + substitutes project metadata → prints the rendered body. < 2 s. No unresolved tokens remain. | ✅ |
| `migrate` | `MigrateService` | `[path]`, `--include-linked`, `--dry-run` | Cleans v1 layout artifacts with 3-keep rotated backups; accepts `ai_tools`→`enabled_hosts` alias on read. | ✅ |
| `generate` | `GenerateService` | `--out build/`, `--check` | Build-time: load `artifacts/` → project every artifact to every host → render all manifests → write `build/`. `--check` asserts no drift (CI gate). Deterministic/idempotent. | ✅ |
| `configure` | `ConfigureService` | interactive / `--set k=v` | Edits `config.yml` (enabled_hosts, permission profile, repos). | ✅ |
| `detect` | `DetectService` | `[path]`, `--json` | Drives detection → prints `ProjectMetadata` + `DetectedPaths`. | ✅ |
| `upgrade` | `UpgradeService` | `[path]`, `--copilot` | Plugin-native = no-op; `--copilot` re-renders Copilot files only. | ✅ |

**Global**: `--dry-run` previews mutations; mutating actions are reversible (constitution V). Exit `0` on success unless a verb defines otherwise (only `check` has the rich exit-code contract). Errors are structured (message + non-zero exit).

**Acceptance**: `generate --check` on a clean checkout exits 0 with no diff (SC-001). `init` then asserting `.claude/rules/*.md` exist with `paths:` (SC-002). All verbs run under a process-level network-deny harness (FR-015 / SC-007).
