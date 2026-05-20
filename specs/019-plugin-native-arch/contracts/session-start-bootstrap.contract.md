# Contract: `hooks/session-start-bootstrap.sh`

**Spec source**: FR-013, SC-013, US3 (acceptance scenario 3 — runtime resolution at session start)
**Event**: `SessionStart` (Claude Code / Codex CLI / Cursor where supported)
**Output budget**: ≤500 tokens of stdout under typical project metadata

## Purpose

The compact bootstrap. Provides the AI host with an index of where to find current state (project.yml pointer, validation command name, active architecture-profile **name**) without preloading rule bodies. Replaces the v0 hook that concatenated ~5000+ tokens of rule bodies into SessionStart stdout (the token-burn precedent in feature 018).

## Required stdout content

In order:

1. One short line identifying the tool and version: `dotnet-ai-kit v<version> active`
2. Pointer to project metadata: `Project metadata: .dotnet-ai-kit/project.yml`
3. Active architecture profile name (NOT body): `Architecture profile: <profile_name>` where `<profile_name>` is the value of `ProjectMetadata.architecture_profile_name` or derived from `ProjectMetadata.project_type`
4. Reminder to use the validation command: `Run \`dotnet-ai check\` to verify state`
5. Lazy-loading instruction: `Skills and rules load on-demand via plugin namespace`
6. Persistent-memory pointer (preserved from feature 018 to avoid regressing the existing `tests/test_session_start_hook.py:26-29` assertion, and aligned with the post-commit-12 `.mcp.json` shape which retains `codebase-memory-mcp` per CHK012): `Persistent memory: codebase-memory-mcp (call on demand for cross-session context)`

That's it. No rule bodies. No skill listings. No architectural narrative. The total output MUST be ≤500 tokens under typical project metadata (and SHOULD be ≤300 to give margin) even with line 6 included.

## Token-count verification

Per SC-013: verified by tokenizer (`tiktoken>=0.13.0` per research R8). The verification test `tests/unit/test_session_start_budget.py` MUST assert:

1. **Primary** — token count ≤500 using `tiktoken`. When `tiktoken` is available (Windows-x64 / macOS / Linux per PyPI binary wheels), this is the binding check.
2. **Fallback** — character count ≤2000 (hard ceiling). When `tiktoken` is unavailable (e.g., ARM Windows where no binary wheel exists), the hard 2000-char ceiling stands in. **Note**: this fallback is a SAFETY NET, not a proof of the 500-token budget. The `chars × 0.25 ≈ tokens` heuristic is NOT used as proof; the 2000-char ceiling is conservative enough that any input under it MUST be safe regardless of tokenization.

The test logs which path it took (tiktoken vs fallback) so a CI reviewer can spot which method was used. CI uses `--only-binary=:all:` when installing `tiktoken` to guarantee the binary-wheel install path on Windows-x64.

## Cross-host behavior

The bootstrap runs under whichever host invoked it (`SessionStart` event handler). The output is host-agnostic plain text. The "Run `dotnet-ai check`" suggestion is interpreted by the user, not by the host.

## Failure mode

If `.dotnet-ai-kit/project.yml` is missing or unreadable:
- Stdout MUST emit: `Project metadata not initialized; run \`dotnet-ai init\``
- Exit code: 0 (advisory; do not block session start)

If `.dotnet-ai-kit/project.yml` is corrupt (fails schema):
- Stdout MUST emit: `Project metadata corrupt; run \`dotnet-ai check\` for details`
- Exit code: 0

## What this hook MUST NOT do

- MUST NOT inline rule bodies
- MUST NOT inline skill listings (the host's plugin namespace handles that)
- MUST NOT make outbound network calls (per A-011)
- MUST NOT mutate any file
- MUST NOT depend on `tiktoken` being installed at hook fire time (the budget is a build-time / test-time check, not a runtime gate)
