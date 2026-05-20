# Contract: `dotnet-ai check` CLI

**Spec source**: FR-017, FR-031, FR-032, SC-010, SC-011, US5
**Implementation**: `src/dotnet_ai_kit/cli.py` `check` command + `hosts/<host>.verify_install()` modules

## Purpose

Single validation entry point. Verifies plugin install per configured host, external binary prerequisites, project metadata schema + detected-path correctness, managed-file manifest integrity, and Copilot render freshness.

## CLI shape

```
dotnet-ai check [--verbose] [--json] [--host <host>]
```

| Flag | Behavior |
|--|--|
| `--verbose` | Per-check breakdown (one line per check; status, path, details) |
| `--json` | Machine-readable JSON output (overrides `--verbose` formatting; structured per check class) |
| `--host <host>` | Scope to a single host's checks. Default: all hosts in `enabled_hosts`. |

## Exit codes (unique check-class identification per FR-031)

| Code | Check class | Failure description |
|--|--|--|
| 0 | All checks pass | Healthy state |
| 10 | Plugin install missing | One or more configured hosts lack the plugin in their plugin-cache path (per R7 paths) |
| 11 | External binary missing | `csharp-ls` (or other) not on PATH when a configured host depends on it |
| 12 | Project metadata schema | `.dotnet-ai-kit/project.yml` fails JSON schema validation |
| 13 | Detected-path inconsistency | One or more paths in `project.yml.detected_paths` no longer exist on disk |
| 14 | Manifest integrity | `.dotnet-ai-kit/manifest.json` missing, unreadable, content-hash mismatch, or unexpected paths |
| 15 | Copilot render stale | Rendered files in `.github/` differ from current plugin source + project metadata |
| 16 | Host symmetric / loader failure | Smoke fixture for a configured host fails to load (e.g., manifest schema invalid for the host) |
| 99 | Unknown error | Internal exception; not user-actionable |

Each failure class MUST be distinguishable by exit code. Multiple failures: lowest code wins (e.g., manifest missing + Copilot stale → exit 14).

## Output

### Default (no flags)

```
✅ Claude Code plugin: installed at ~/.claude/plugins/cache/dotnet-ai-kit/1.0.0/
✅ Codex CLI plugin: installed at ~/.codex/plugins/cache/dotnet-ai-kit/1.0.0/
✅ csharp-ls binary: /usr/local/bin/csharp-ls
✅ project.yml: valid (company=Contoso, project_type=command, branch=microservice)
✅ Detected paths: all 6 paths exist on disk
✅ manifest.json: 7 files tracked, all hashes match
✅ Copilot renders: 14 files fresh

dotnet-ai check passed in 1.2s
```

### On failure

```
❌ csharp-ls binary: NOT FOUND on PATH
   The csharp-lsp plugin dependency requires csharp-ls to be installed.
   Install: https://github.com/razzmatazz/csharp-language-server
   
dotnet-ai check failed (exit 11) in 0.8s
```

### `--json` output

```json
{
  "version": "1.0.0",
  "duration_ms": 1234,
  "exit_code": 0,
  "checks": [
    { "name": "claude_plugin_install", "status": "pass", "details": "~/.claude/plugins/cache/dotnet-ai-kit/1.0.0/" },
    { "name": "csharp_ls_binary", "status": "pass", "details": "/usr/local/bin/csharp-ls" },
    { "name": "project_yml_schema", "status": "pass" },
    { "name": "detected_paths", "status": "pass", "details": "6/6 paths exist" },
    { "name": "manifest_integrity", "status": "pass", "details": "7 files, all hashes match" },
    { "name": "copilot_freshness", "status": "skip", "details": "Copilot not enabled" }
  ]
}
```

## Performance budget (SC-010)

Total runtime under 10 seconds on a developer's typical workstation. Tested in `tests/unit/test_sc010_check_runtime.py` with a representative project metadata fixture.

## What `check` MUST NOT do

- MUST NOT make outbound network calls (A-011)
- MUST NOT shell out to host CLIs in v1 (clarify Q3 — filesystem inspection only)
- MUST NOT mutate any file (read-only)
- MUST NOT emit telemetry (A-011)
