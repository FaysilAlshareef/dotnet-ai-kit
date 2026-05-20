# Contract: `hooks/pretooluse-arch-profile.sh`

**Spec source**: FR-034, US3 (acceptance scenario 3 — mid-session profile change observed)
**Event**: `PreToolUse` (Claude Code; verified support per architecture-phase research)
**Output budget**: Soft target ≤500 tokens; hard ceiling ≤1500 tokens

## Purpose

Resolve the active architecture profile body at tool-use fire-time. This is what makes runtime resolution of architecture profile work per FR-034: a mid-session change to `ProjectMetadata.architecture_profile_name` (or to `ProjectMetadata.project_type`) is observed by the next tool-use without requiring session restart.

## Trigger condition

This hook fires on `PreToolUse` for the subset of tools where architecture-profile-specific context is useful. The current matcher targets:
- Code-generation tool calls (Edit, Write where targeting source files)
- Architecture-related queries (the hook reads tool input briefly and decides to emit profile context only when relevant)

The exact matcher is registered in `hooks/hooks.json` under the `PreToolUse` entry's `matcher` and `if` fields. Per feature 018 R2, the handler-level `if:` filter is available in Claude Code 2.1.85+; if the user's Claude Code is older, the matcher uses the older command-pattern matcher with the same effective scope.

## Required stdout content

When the hook decides to emit (profile-relevant tool use):

1. One header line: `Active architecture profile: <profile_name>` (with derived branch — `microservice` or `generic`)
2. The full body of `profiles/<branch>/<profile_name>.md` (≤100 lines per Constitution V)
3. Pointer to convention rules: `Always-on conventions: rules/conventions/{async-concurrency,coding-style,existing-projects,security,tool-calls}.md`

When the hook decides NOT to emit (non-profile-relevant tool use):

- Stdout is empty
- Exit code 0

## Project metadata reading

The hook MUST read `.dotnet-ai-kit/project.yml` at every fire (no caching). This is what makes FR-034 work — frozen-at-init snapshots are explicitly forbidden by the spec.

Read sequence:
1. Locate `.dotnet-ai-kit/project.yml` (search current directory up to repo root)
2. Parse YAML; if parse fails, exit 0 with the failure message documented under Failure mode
3. Read `architecture_profile_name` (if absent, derive from `project_type` per the data-model mapping)
4. Locate `profiles/<architecture_branch>/<profile_name>.md` under `${CLAUDE_PLUGIN_ROOT}` (substitution variable provided by Claude Code). Codex CLI exposes `${PLUGIN_ROOT}` per `https://developers.openai.com/codex/plugins/build:954-955`. Cursor's plugin-root substitution variable is NOT verified at plan-phase; if the v1 Cursor smoke fixture (A-005) reveals Cursor exposes a substitution variable, document it; otherwise the PreToolUse hook on Cursor is deferred to v1.1.
5. Emit the body

## Failure mode

- `.dotnet-ai-kit/project.yml` missing: stdout emits `Project metadata not initialized; run \`dotnet-ai init\``, exit 0
- `.dotnet-ai-kit/project.yml` corrupt: stdout emits `Project metadata corrupt; run \`dotnet-ai check\` for details`, exit 0
- `architecture_profile_name` references a profile that does not exist: stdout emits `Unknown architecture profile: <name>; run \`dotnet-ai check\` for valid values`, exit 0
- Any other error: stdout emits a single-line description, exit 0 (advisory — never block tool use)

## What this hook MUST NOT do

- MUST NOT mutate any file
- MUST NOT make outbound network calls (per A-011)
- MUST NOT exit non-zero (advisory hook)
- MUST NOT cache the profile body across invocations (per FR-034 runtime resolution requirement)
- MUST NOT emit when `project.yml` says the project type doesn't have a relevant profile body
