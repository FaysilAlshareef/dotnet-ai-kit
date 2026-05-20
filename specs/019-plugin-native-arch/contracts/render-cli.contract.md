# Contract: `dotnet-ai render` CLI

**Spec source**: FR-019, SC-012, US6
**Implementation**: `src/dotnet_ai_kit/render.py` + `src/dotnet_ai_kit/cli.py` `render` command

## Purpose

Inspectability mitigation. Prints what a skill or rule resolves to right now, with current `project.yml` metadata substituted in. Restores the property that pre-rendered files had on disk under the old layout (visible, inspectable) without restoring those files.

## CLI shape

```
dotnet-ai render <kind> <name> [--host <host>]
```

| Argument | Behavior |
|--|--|
| `<kind>` | One of: `skill`, `rule`. Required positional. |
| `<name>` | Name of the skill or rule (without `.md` extension). Required positional. |
| `--host <host>` | Output shape. Default: `claude`. v1 supports `claude` only; other values reject with non-zero exit + v1.1 deferral message. |

## v1 host scope (per SC-012 / CP9)

In v1, `render` produces Claude-host-shaped output only. The CLI explicitly handles other hosts:

```
$ dotnet-ai render skill add-aggregate --host codex
Error: --host codex is not supported in v1 of dotnet-ai render.

The render command produces Claude Code-shaped output in v1. Support for
other hosts (Codex CLI, Cursor, GitHub Copilot) is deferred to v1.1.

Run without --host to get Claude-shaped output:
  dotnet-ai render skill add-aggregate

Exit code: 20
```

The test `tests/unit/test_fr019_render_cases.py` MUST assert this rejection happens for `--host codex`, `--host cursor`, `--host copilot` and that exit code 20 is unique to "unsupported host shape in v1."

## Exit codes

| Code | Meaning |
|--|--|
| 0 | Render succeeded; output printed |
| 20 | Unsupported `--host` shape in v1 |
| 21 | Skill or rule not found |
| 22 | `.dotnet-ai-kit/project.yml` missing or corrupt |
| 23 | Substitution failure (e.g., metadata key referenced by skill but absent in project.yml) |

## Output

### Success

```
$ dotnet-ai render skill add-aggregate
---
name: add-aggregate
description: Use when adding a new command-side domain entity.
metadata:
  paths:
    - "**/Domain/**"
  when_to_use: |
    User is adding a new aggregate to a command-side microservice.
---

# Add Aggregate Skill

(content with ${Company} → Contoso, ${Domain} → Sales, ${detected_paths.command_path} → src/Contoso.Sales.Command resolved against current project metadata...)
```

### Skill not found

```
$ dotnet-ai render skill nonexistent
Error: Skill 'nonexistent' not found.

Searched in: ${CLAUDE_PLUGIN_ROOT}/skills/
Available skills: add-aggregate, add-entity, add-event, ... (124 total)

Exit code: 21
```

## Performance budget (SC-012)

Render completes in under 2 seconds for a parameterized skill on a developer's typical workstation. Tested in `tests/unit/test_sc012_render_runtime.py` with a representative skill + project metadata fixture.

## What `render` MUST NOT do

- MUST NOT mutate any file (read-only)
- MUST NOT write a "pre-rendered" file to disk (the whole point of the new architecture is no on-disk pre-renders)
- MUST NOT make outbound network calls (A-011)
- MUST NOT emit telemetry (A-011)
- MUST NOT silently emit a non-Claude shape when `--host` is unsupported (CHK045 explicit guard)
