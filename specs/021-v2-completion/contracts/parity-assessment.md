# Contract: Python v1 → .NET parity assessment (gates Python removal — FR-020)

Python (`src/dotnet_ai_kit/`) is removed **only** when every v1 CLI capability maps to a covered .NET capability AND the acceptance suite is green. **Filled in C9** from `src/dotnet_ai_kit/cli.py` (verbs: init, status, upgrade, configure, render, migrate, check, extension-add/remove/list, changelog).

| v1 CLI verb | .NET equivalent | Status |
|---|---|---|
| `init` | `InitService` / `init` verb | ✅ covered |
| `check` | `CheckService` / `check` verb (enumerated exit codes) | ✅ covered |
| `render` | `RenderService` / `render` verb | ✅ covered |
| `migrate` | `MigrateService` / `migrate` verb | ✅ covered |
| `configure` | `ConfigureService` / `configure` verb | ✅ covered |
| `upgrade` | `UpgradeService` / `upgrade` verb | ✅ covered |
| (new) | `generate` / `detect` verbs | ✅ added in v2 |
| `status` | v2 `status` **command-skill** (assistant-invoked), not a CLI verb | ⚠️ covered-by-redesign, **not a CLI verb** |
| `changelog` | v2 `release` / `docs` **command-skills** | ⚠️ covered-by-redesign, **not a CLI verb** |
| `extension-add/remove/list` | superseded by the plugin/marketplace model (v2 has no CLI extension manager) | ⚠️ superseded by design |
| no-network invariant | `Acceptance.Tests` network-deny | ✅ covered |
| exit-code contract | `Acceptance` + `Cli` exit-code tests | ✅ covered |
| footprint bound | `Acceptance` footprint test | ✅ covered |

## Decision (C9)

The .NET CLI fully covers the **six core engine verbs** + adds `generate`/`detect`, and the acceptance suite is green. However, **`status`, `changelog`, and `extension-*` are not 1:1 .NET CLI verbs** — they are redesigned as assistant-invoked command-skills (status/changelog) or superseded by the plugin/marketplace model (extension-*).

The maintainer's gate is explicit and conservative: remove Python **only when sure** .NET fully covers it. Because the CLI surface is not 1:1 (the three verbs above), **Python is RETAINED this session** as the reference. This is the honest, safe outcome.

**Path to removal** (a focused follow-on): either (a) add a `status` .NET CLI verb (read `.dotnet-ai-kit/features/` → progress) and a `changelog` path, and confirm `extension-*` is intentionally dropped; or (b) the maintainer accepts the command-skill/plugin redesign as full coverage. Then remove `src/dotnet_ai_kit/` + Python `tests/` + the Python-coupled dirs (`templates/ config/ schemas/ scripts/`) and confirm build/test/generate green.
