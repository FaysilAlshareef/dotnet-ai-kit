# Quickstart — Fix Token Burn

**Feature**: `018-fix-token-burn` | **Date**: 2026-05-16
**Audience**: maintainer or contributor working on this feature branch, OR a plugin user migrating an existing install.

This is a Phase 1 artifact derived from [plan.md](./plan.md). It does not change behaviour; it documents how to use what each PR ships.

---

## 1. Migrate an existing installed project (after PR2b lands)

```bash
# Always preview first
dotnet-ai upgrade --dry-run

# Live migration (atomic — rolls back on any failure)
dotnet-ai upgrade

# Verify
cat .dotnet-ai-kit/manifest.json | jq '.files | length'  # number of managed files
git diff                                                  # see what changed
```

**Atomic guarantee** (FR-031, SC-013): if migration fails on any file (e.g. write error on file N of M), the upgrade restores every file from `.dotnet-ai-kit/backups/upgrade/<run_id>/` and exits non-zero. `git diff` after a failed upgrade shows zero changes.

**User-modified files**: if the manifest's SHA-256 doesn't match the current bytes, `/dai.upgrade` aborts on that file and asks for `--force`. Use `--force` only after diffing the file against the plugin's template version.

---

## 2. Install `codebase-memory-mcp` (after PR4 lands)

The plugin requires `codebase-memory-mcp >= 0.6.1` for full functionality. `/dai.init` detects it automatically; if missing, choose one of:

### Windows (PowerShell)

```powershell
# Option A — PyPI (simplest)
pip install "codebase-memory-mcp>=0.6.1"

# Option B — manual binary
$url = "https://github.com/DeusData/codebase-memory-mcp/releases/download/v0.6.1/codebase-memory-mcp-windows-amd64.zip"
Invoke-WebRequest $url -OutFile codebase-memory-mcp.zip
Expand-Archive codebase-memory-mcp.zip -DestinationPath $env:USERPROFILE\bin
$env:Path += ";$env:USERPROFILE\bin"
```

### macOS / Linux

```bash
pip install "codebase-memory-mcp>=0.6.1"
# verify
codebase-memory-mcp --version
```

After install:

```bash
dotnet-ai init   # detects MCP, indexes project, records state in .dotnet-ai-kit/mcp-state.yml
```

If the MCP is unavailable at runtime, operational commands (`/dai.analyze`, `/dai.review`, etc.) emit exactly one line and fall back:

```
MCP unavailable: codebase-memory-mcp is not connected or below >=0.6.1; falling back to csharp-ls + grep/read.
```

---

## 3. Run the regression test suite locally

After PR5 lands:

```bash
# Cross-platform (recommended)
python scripts/check.py

# OR — wrappers
make check                         # Linux/macOS
.\scripts\check.ps1                # Windows PowerShell
```

This runs the static + unit categories — every PR must pass these. Target time: ≤ 30s (SC-009).

**Smoke tests** (opt-in, separate run):

```bash
# Linux/macOS
CLAUDE_CODE_SMOKE=1 pytest -m smoke

# Windows PowerShell
$env:CLAUDE_CODE_SMOKE = "1"; pytest -m smoke
```

Smoke tests require `claude` on PATH. CI runs these nightly or on PRs labelled `smoke`.

---

## 4. Read the manifest

`.dotnet-ai-kit/manifest.json` is the source of truth for what the plugin deployed:

```bash
# Number of managed files
jq '.files | length' .dotnet-ai-kit/manifest.json

# Show files deployed by an old plugin version
jq '.files[] | select(.plugin_version != "1.0.0")' .dotnet-ai-kit/manifest.json

# Verify a specific file matches manifest checksum
file=".claude/skills/api/controllers/SKILL.md"
manifest_sha=$(jq -r ".files[] | select(.path == \"$file\") | .sha256" .dotnet-ai-kit/manifest.json)
actual_sha=$(sha256sum "$file" | cut -d' ' -f1)
[ "$manifest_sha" = "$actual_sha" ] && echo "match" || echo "USER-MODIFIED"
```

Schema: see [contracts/manifest.schema.json](./contracts/manifest.schema.json).

---

## 5. The 6-file memory split (after PR4)

`/dai.learn` now produces a compact index plus six on-demand topic files:

```
.dotnet-ai-kit/memory/
├── constitution.md       # index (≤100 lines) — loaded by commands that need a quick overview
├── architecture.md       # detail — read on demand by /dai.plan when architectural context needed
├── domain-model.md       # aggregates, entities, value objects, events
├── event-flow.md         # event publishers/handlers/projections
├── interfaces.md         # HTTP/gRPC/message contracts and route maps
├── dependencies.md       # NuGet packages, SDK versions, external services
└── conventions.md        # naming, DI, error handling, logging
```

**Do not** add `constitution.md` to your project's always-loaded rules. Commands read the topic files only when needed (FR-023).

---

## 6. Run baseline + post-fix measurements (PR0 + PR5)

```bash
# PR0 — baseline (before any fix lands)
python scripts/measure.py --label baseline >> specs/018-fix-token-burn/measurements.md

# After PR5 — post-fix
python scripts/measure.py --label post-fix >> specs/018-fix-token-burn/measurements.md

# Compare
python scripts/measure.py --report
```

Scenarios captured per run (3 reads each, median wins):
1. Fresh-session startup (SC-001)
2. `/dai.implement` 5-task fixture (SC-002)
3. `/dai.review` (SC-003)
4. Graph-shaped question (SC-007)

Pinned attributes per measurement: Claude Code version, model id, plugin commit SHA, Python version.

---

## 7. Contributor checklist (when adding a new skill / rule / command)

Before pushing:

```bash
python scripts/check.py     # blocks merge if any static/unit test fails
```

Common errors and fixes:

| Failing test | Cause | Fix |
|---|---|---|
| `test_no_skill_activation_fields_under_metadata` | New SKILL.md has `metadata.paths` | Move to top-level `paths:` |
| `test_no_alwaysApply_in_rules_profiles_skills` | New file carries `alwaysApply: true` | Delete the field; use `paths:` for scoping or omit for always-loaded |
| `test_commands_have_no_bulk_skill_load` | New command says "Load all skills listed" | Replace with MCP-first selection (≤2 skills per task) |
| `test_no_agent_skills_loaded_section` | New agent has `## Skills Loaded` body section | Delete the section |
| `test_command_line_budget` | Command > 200 physical lines | Trim or split the command |
| `test_hooks_blocking_uses_exit_2` | New blocking hook script uses `exit 1` | Change to `exit 2` |
| `test_hook_command_filters_use_if_not_matcher` | `matcher: "Bash(git commit*)"` | Move to handler-level `if: "Bash(git commit*)"`, set `matcher: "Bash"` |

---

## 8. Roll back the whole feature (emergency)

```bash
# Revert the merged PRs in reverse order
git revert <PR5-sha> <PR4-sha> <PR3-sha> <PR2b-sha> <PR2a-sha> <PR1-sha>
# Note: PR0 is baseline measurement, safe to keep.

# In an installed project, restore from a backup
ls .dotnet-ai-kit/backups/upgrade/
# pick a known-good run_id, then:
# (manual copy or write a restore helper — not part of the regular CLI)
```

---

## 9. Verifying coverage (T087-doc / SC-010)

After PR5, every static / unit check has a deliberate failure path planted by the violation harness:

```bash
# Run the full sweep — copies the repo to a tempdir, mutates one violation
# per class, runs scripts/check.py against the mutated copy, asserts the
# named test catches the regression. 17 classes, all 17 expected OK.
python scripts/violation_harness.py

# Filter a single class while debugging
python scripts/violation_harness.py --filter V05
```

If any class reports `MISS`, the corresponding regression is undetected. Either tighten the test (preferred) or add a new test row in `specs/018-fix-token-burn/traceability.md` and document the gap.

---

## See Also

- [spec.md](./spec.md) — the 38 functional requirements
- [plan.md](./plan.md) — 7-PR implementation map
- [research.md](./research.md) — Phase 0 findings
- [data-model.md](./data-model.md) — entity schemas
- [contracts/](./contracts/) — JSON Schema + YAML contracts
- [issues/token-burn-optimization/FINAL-REPORT.md](../../issues/token-burn-optimization/FINAL-REPORT.md) — the original 18-finding source
