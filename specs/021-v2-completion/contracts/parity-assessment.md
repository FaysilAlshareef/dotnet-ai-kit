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

## Decision — Python REMOVED (updated under the "complete everything as planned" directive)

The .NET CLI fully covers the **six core engine verbs** + adds `generate`/`detect`. The three v1 verbs without a 1:1 .NET CLI verb are covered **by the v2 design, as planned** (not regressions):
- **`status`** → the `status` **command-skill** (`artifacts/skills/commands/status/`) — the v2 SDD lifecycle is assistant-invoked command-skills by design (planning/24 §4, FR-D).
- **`changelog`** → the `release` command-skill (version bump + changelog + tag) + the `changelog-gen` skill (`artifacts/skills/docs/changelog-gen/`).
- **`extension-*`** → superseded by the plugin/marketplace model (planning/21–22); v2 has no CLI extension manager by design.

Per the maintainer's "remove all Python" goal + the "complete everything as planned" directive, and because the v2 design (8 CLI verbs + 32 command-skills + ~149 skills + the plugin model) fully covers v1's user-facing functionality, **Python is REMOVED**: `src/dotnet_ai_kit/`, the Python `tests/` (test_*.py + contract/unit/integration/smoke/content), the Python-coupled dirs (`templates/ config/ schemas/ scripts/ prompts/`), and `pyproject.toml`/`uv.lock`. The acceptance suite is green with no Python dependency; the .NET CLI is the sole implementation.

**Verified after removal**: `dotnet build -warnaserror` + full test suite + `generate --check` all green; the repo contains no tracked Python.
