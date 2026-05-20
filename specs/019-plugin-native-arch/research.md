# Phase 0 Research: Plugin-Native Architecture

**Branch**: `019-plugin-native-arch` | **Date**: 2026-05-17 | **Plan**: [plan.md](./plan.md)

This file consolidates research findings for the plugin-native architecture refactor. Items R1–R6 were resolved during the architecture-phase debate (`issues/plugin-native-architecture/`) and are restated here for completeness. Items R7–R13 are plan-phase research that this document closes before commits 4–14 ship.

## R1 — Claude Code plugin manifest schema (resolved during architecture-phase)

**Decision**: Use the documented manifest fields: `name`, `version`, `description`, `agents`, `skills`, `commands`, `hooks`, `mcpServers`, `lspServers`, `outputStyles`, `dependencies`, `userConfig`, `channels`.

**Rationale**: These are the fields Claude Code's loader recognizes. Other fields are silently ignored. The `agents` field is the one our existing manifest is missing today (`issues/plugin-native-architecture/codex/final-merged-findings.md:104` confirms `.claude-plugin/plugin.json` has no `agents` field).

**Alternatives considered**: A generic cross-host manifest format — rejected because each host loads only its documented fields and silent ignores create confusion.

**Source**: `https://code.claude.com/docs/en/plugins-reference` lines 365-485.

## R2 — Codex CLI plugin schema (resolved during architecture-phase)

**Decision**: Codex plugin = `.codex-plugin/plugin.json` + `skills/` + `.mcp.json` + `hooks/hooks.json` + `.app.json` + `assets/`. No `agents/`, no LSP, no monitors, no settings, no bin.

**Rationale**: Codex CLI docs explicitly document only those primitives. Native agents for Codex remain OOS-004 until docs catch up.

**Alternatives considered**: Treating Codex as a Claude-Code-compatible plugin host — rejected per architecture-phase round 1 reply (Codex pushback: Codex compatibility is narrower than Claude's).

**Source**: `https://developers.openai.com/codex/plugins/build` lines 811-836.

## R3 — Cursor plugin packaging (resolved during architecture-phase)

**Decision**: Cursor plugins package skills, subagents, MCP servers, hooks, and rules. Rules use `.mdc` format.

**Rationale**: Cursor 2.5 changelog and marketplace announcement both confirm subagents as a packaging primitive.

**Alternatives considered**: Skip Cursor plugins entirely — rejected per Codex's evidence-based pushback in architecture-phase round 1.

**Sources**:
- `https://cursor.com/blog/marketplace/` lines 268-273
- `https://cursor.com/changelog/2-5` lines 37-45
- `https://github.com/cursor/plugins` lines 286-300
- `https://cursor.com/docs/context/rules` (rules `.mdc` format)

## R4 — Cursor sub-agent loader behaviour (plan-phase re-verify needed before commit 6)

**Decision (current best knowledge)**: Cursor marketplace announces sub-agents as a primitive. The live marketplace page `https://cursor.com/marketplace/cursor/agent-compatibility` lines 45-55 lists 4 Subagents in the Agent Compatibility plugin. The cursor/plugins repository README does **not** explicitly document a `subagents/` or `agents/` directory layout; it lists manifests, skills, rules, and MCP. This means the precise file-layout spec for sub-agent discovery is not documented in static docs.

**Plan-phase action**: Before commit 6 ships, re-fetch the Cursor docs site and the `cursor/plugins` repository structure. If a loader layout spec is published, use it. Otherwise, use the file shape observed in the live `agent-compatibility` plugin as the reference.

**Spike outcome handling**: A-005 + SC-008 + OOS-005 bind the release. The single fixture in commit 6 must load cleanly under Cursor. If it does not, full Cursor sub-agent generation is removed from this release.

**Rationale**: Treating documentation symmetry as loader symmetry was an architecture-phase failure mode that Codex flagged. The spike is the gate.

**Alternatives considered**:
- Ship without a fixture: violates SC-008 (release MUST NOT merge with any host-specific smoke fixture failing or absent).
- Ship multiple fixtures: increases failure surface without proportionate value for v1.

**Sources**:
- `https://cursor.com/marketplace/cursor/agent-compatibility` lines 45-55 (live primitive listing)
- `https://github.com/cursor/plugins` repository structure (documented primitives)

## R5 — GitHub Copilot customization paths (resolved during architecture-phase)

**Decision**: Copilot custom agents = `.github/agents/*.agent.md` (per-agent custom agent files). Repo-wide instructions = `.github/copilot-instructions.md`. Path-scoped instructions = `.github/instructions/*.instructions.md`.

**Rationale**: Three logical content classes published by GitHub Copilot for repo-level customization. The architecture-phase round 1 reply from Codex corrected the initial misconception that root `AGENTS.md` was the Copilot agent target.

**Alternatives considered**: Root `AGENTS.md` for Copilot — rejected (collides with developer-authored repo guidance; root `AGENTS.md` is user-owned per A-008).

**Sources**:
- `https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli` lines 542-550 (custom agents)
- `https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot` lines 714-735 (repo-wide + path-scoped instructions)

## R6 — `csharp-lsp` plugin dependency (resolved during architecture-phase)

**Decision**: Use the official `csharp-lsp` plugin as a `dependencies` entry in `.claude-plugin/plugin.json`. The plugin still requires the `csharp-ls` binary to be on PATH on the developer's machine.

**Rationale**: LSP is the correct primitive for edit-time diagnostics and navigation. MCP requires explicit AI tool invocation.

**Alternatives considered**:
- Keep `csharp-ls` in `.mcp.json` only: rejected because MCP defers diagnostics to AI invocation rather than surfacing them at edit time.
- Drop C# language intelligence from the plugin: rejected because the existing user value would regress.

**Source**: `https://code.claude.com/docs/en/discover-plugins` lines 131-155.

## R7 — Per-OS plugin-cache directories per host (RESOLVED per plan-phase round-3 corrections)

**Decision**: For each host, `dotnet-ai check` inspects the following filesystem locations (filesystem-only per clarify Q3). All paths derived from `Path.home()` plus platform-specific subpath.

| Host | Linux/macOS path | Windows path |
|--|--|--|
| Claude Code | `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` | `%USERPROFILE%\.claude\plugins\cache\<marketplace>\<plugin>\<version>\` |
| Codex CLI | `~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/` | `%USERPROFILE%\.codex\plugins\cache\<marketplace>\<plugin>\<version>\` |
| Cursor (local) | `~/.cursor/plugins/local/<name>/` | `%USERPROFILE%\.cursor\plugins\local\<name>\` |
| Cursor (marketplace) | `~/.cursor/plugins/<...>` (path verified before commit 9 — first marketplace install ground-truths the path) | `%USERPROFILE%\.cursor\plugins\<...>` |

**Rationale**: Filesystem inspection is fast, deterministic, no shell-out dependency (per clarify Q3).

- Claude Code path: live disk inspection at architecture-phase confirmed `~/.claude/plugins/cache/claude-plugins-official/coderabbit/1.1.1/`.
- Codex CLI path: confirmed via `https://developers.openai.com/codex/plugins/build:801-809` — installed marketplace plugins under `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/`.
- Cursor local testing path: confirmed via `https://github.com/cursor/plugins/tree/main/agent-compatibility:325-329` and `https://forum.cursor.com/t/local-plugin-is-not-being-picked-up-by-cursor/156549/3:9-12` — symlink into `~/.cursor/plugins/local/<plugin-name>/`.

**Rejected paths**: `.cursor/extensions/` — no evidence Cursor uses this for plugins; was an early guess in plan-phase draft.

**Plan-phase action remaining**: First marketplace install during commit 6/9 testing ground-truths the Cursor marketplace cache path. If it differs from `~/.cursor/plugins/<cache>`, update `hosts/cursor.py` and document.

**Limitations**: A host-considers-plugin-disabled-but-file-on-disk scenario will pass the filesystem check but the user will see the plugin as unavailable. Documented as an acceptable v1 trade-off per clarify Q3. Future v1.1 may add optional host-CLI shell-out as a deeper check.

**Sources**:
- `https://developers.openai.com/codex/plugins/build:801-809` (Codex installed cache)
- `https://github.com/cursor/plugins/tree/main/agent-compatibility:325-329` (Cursor local symlink)
- `https://forum.cursor.com/t/local-plugin-is-not-being-picked-up-by-cursor/156549/3:9-12` (Cursor local path Windows confirmation)
- Live disk inspection of `~/.claude/plugins/cache/`

## R8 — Token-counting library for SC-013 verification (RESOLVED per plan-phase round-3)

**Decision**: Primary = `tiktoken>=0.13.0` (Python wrapper for OpenAI tokenizer). Fallback = **hard 2000-char ceiling** (NOT `chars × 0.25` as proof). CI install: `pip install --only-binary=:all: tiktoken` to force the binary-wheel install path on Windows-x64.

**Pin justification**: Codex PQ4 evidence confirms `tiktoken==0.13.0` (May 15, 2026 release) publishes `win_amd64` wheels for CPython 3.10-3.14 per `https://pypi.org/project/tiktoken/:397-450`. Earlier pin `>=0.5.0` was too loose for modern Python/Windows assurance.

**Rationale**: SC-013 (SessionStart bootstrap ≤500 tokens) and SC-004 (always-on context ≥65% reduction, target band 2500-3000 tokens) both need a token unit. `tiktoken` is the de facto Python token-counting library for OpenAI/Anthropic-style models. The character-length fallback ensures the assertion still runs even if `tiktoken` fails to install on a CI agent (e.g., missing Rust toolchain on a fresh Windows agent).

**Alternatives considered**:
- `transformers` library: too heavy for a CLI dependency.
- `anthropic` SDK's `count_tokens`: requires API key for some methods.
- Pure character count without ratio: too inaccurate for the 500-token budget assertion.

**Implementation note**: `tests/unit/test_session_start_budget.py` MUST try `tiktoken` first and fall back to character count with a clearly-logged fallback warning so a reviewer can spot which method was used in any given CI run.

**Plan-phase action**: Confirm `tiktoken` installs cleanly on Windows + macOS + Linux CI agents during commit 13 build. If Windows install consistently fails, escalate to the character-length fallback as the primary method.

**Sources**:
- `https://github.com/openai/tiktoken` (cross-platform install matrix)
- OpenAI/Anthropic published guidance that 1 token ≈ 4 characters for English text

## R9 — JSON schema validation library (plan-phase resolution)

**Decision**: `jsonschema>=4.0`. Add to `pyproject.toml` dependencies (currently absent).

**Rationale**: Mature, cross-platform, no compiled deps. Used by many CLI tools for config validation. Provides clear error messages with JSON Pointer paths to the failing field.

**Alternatives considered**:
- `pydantic` alone for validation (already a dependency): adequate for runtime validation but lacks the "publish a schema for external consumption" property that `schemas/*.schema.json` files give us. The plan keeps both — `pydantic` for runtime, `jsonschema` for the published schema artifact.
- `fastjsonschema`: faster but less informative error messages.

**Plan-phase action**: Add `jsonschema>=4.0` to `pyproject.toml [project.dependencies]` as part of commit 8.

**Source**: `https://python-jsonschema.readthedocs.io/`

## R10 — Cross-platform binary-on-PATH detection (plan-phase resolution)

**Decision**: `shutil.which("csharp-ls")` from stdlib. Returns the absolute path if found, `None` if not.

**Rationale**: Cross-platform out of the box. Honors `PATH` on all OSes. Used by the existing `mcp_check.py` pattern from feature 018.

**Alternatives considered**:
- Subprocess `csharp-ls --version`: fails opaquely if binary missing; requires error handling.
- Manual `PATH` parsing: reinventing `shutil.which`.

**Implementation note**: `hosts/claude.py` exposes `check_csharp_ls_binary()` that returns a typed result (`Found(path) | NotFound()`). Used by commit 9's `check` command.

**Source**: Python stdlib `shutil.which` documentation.

## R11 — Manifest hash algorithm (plan-phase resolution)

**Decision**: SHA-256 per file (existing format from feature 018's `.dotnet-ai-kit/manifest.json`). No new algorithm.

**Rationale**: Feature 018 already established SHA-256 as the per-file hash in `manifest.json`. Re-using the existing format eliminates a migration concern and keeps `migrate` simple — it reads the existing `manifest.json`, matches paths to deployed files, compares hashes.

**Schema extension for this feature**: Add `host_owner` field to each `DeployedFile` entry — values: `"claude"`, `"codex"`, `"cursor"`, `"copilot"`, or `null` (for non-host-specific files like `project.yml` and `config.yml`). Used by `migrate` to scope cleanup per host.

**Alternatives considered**:
- BLAKE3 (faster): no reason to break compatibility.
- SHA-1 (smaller): cryptographically weaker; SHA-256 is the industry default for non-crypto integrity.

**Source**: Feature 018 `manifest.py` data model.

## R12 — Cursor existing one-blob `.cursor/rules/dotnet-ai-kit.mdc` migration (plan-phase resolution)

**Decision**: Drop the one-blob output. Replace with per-rule `.cursor/rules/<name>.mdc` files. Existing one-blob file is treated as a managed legacy artifact by the migration command — if its hash matches what `copier.py:231-272` would have produced, it gets backed up; if user-modified, preserved in place per FR-022.

**Rationale**: Cursor's documented rule format supports multiple `.mdc` files in `.cursor/rules/`. The one-blob output was a v0 expedient that loses the per-rule scoping Cursor's `.mdc` format provides.

**Implementation note**: Commit 6 is where this migration happens. The `migrate` command added in commit 10 inherits the cleanup logic.

**Source**: Architecture-phase merged-findings line 94 documents the existing one-blob behavior.

## R13 — Codex CLI stub root-`AGENTS.md` removal (plan-phase resolution)

**Decision**: Remove the code path entirely. Root `AGENTS.md` becomes user-owned per FR-008 / A-008.

**Code locations to delete or refactor**:
- `src/dotnet_ai_kit/agents.py:51` — `AGENT_CONFIG["codex"]["agents_file"] = "AGENTS.md"` mapping.
- `src/dotnet_ai_kit/copier.py:276-317` — `copy_commands_codex` function that emits root `AGENTS.md`.
- Any test fixture that asserts root `AGENTS.md` is written.

**Rationale**: Architecture-phase merged-findings line 95 documented this collision risk. Spec FR-008 (clarify-extended) binds the generalization: paths outside the formally-managed manifest MUST NOT be written, modified, migrated, or deleted by any tool command unless the user explicitly opts in. The root `AGENTS.md` is the concrete example.

**Source**: `src/dotnet_ai_kit/agents.py:51`, `src/dotnet_ai_kit/copier.py:276-317`.

## R14 — Host manifest field-shape resolution (NEW per plan-phase round-2/3)

**Decision**: Each host's plugin manifest uses a different schema. The contracts MUST reflect each host's actual published shape, not a generalized abstraction.

- **Claude Code**: array/object fields per `https://code.claude.com/docs/en/plugins-reference:365-485`. `agents` is an array of file paths; `skills` is an array of glob patterns; `hooks` is an object with `configFile`; etc.
- **Codex CLI**: scalar relative paths with `./` prefix per `https://developers.openai.com/codex/plugins/build:843-860`. `skills: "./skills/"`, `mcpServers: "./.mcp.json"`, `hooks: "./hooks/hooks.json"`.
- **Cursor**: scalar relative paths with `./` prefix per `https://raw.githubusercontent.com/cursor/plugins/main/agent-compatibility/.cursor-plugin/plugin.json:0`. Manifest field `agents` (NOT `subagents`) → `"./agents/"`.

**Rationale**: Treating documentation symmetry as loader symmetry was a v1 architecture-phase failure mode (per architecture-phase merged-findings). Per-host schema is the safe move.

**Closure**: Contract schemas at `contracts/{claude,codex,cursor}-plugin.schema.json` reflect each host's shape exactly.

## R15 — Host reload mechanisms (NEW per plan-phase round-2/3)

**Decision**: For CHK056 release-notes documentation, the host-equivalent reload action per host is:

| Host | Reload mechanism |
|--|--|
| Claude Code | `/reload-plugins` slash command (verified) |
| Codex CLI | Restart Codex CLI process (Codex docs don't document a hot-reload; verified before commit 15 ships, otherwise documented as "restart Codex") |
| Cursor | Workspace reload (Cmd/Ctrl+Shift+P → "Reload Window"; verified before commit 15 ships) |
| GitHub Copilot | N/A — no plugin host; re-render via `dotnet-ai upgrade --copilot` |

**Rationale**: The spec edge case "Plugin updated mid-session" requires each host's reload to be documented. Without this, users update the plugin and see no change until session restart.

**Plan-phase action remaining**: Re-fetch Codex CLI and Cursor docs before commit 15 to confirm the exact reload commands.

**Sources**: Claude Code docs `/reload-plugins`; Codex CLI docs (to be re-fetched); Cursor docs (to be re-fetched).

## R16 — Legacy manifest backward compatibility (NEW per plan-phase round-2/3)

**Decision**: The new `manifest.json` schema is versioned. Reader accepts v1 (legacy from feature 018) and v2 (new). Writer always emits v2.

**Schema versions**:

- **v1** (feature 018; current `cli.py:433-438` writes this): `schema_version: "1"`, no `host_owner` per file
- **v2** (feature 019, this release): `schema_version: "2"`, `host_owner` per file (one of `claude`, `codex`, `cursor`, `copilot`, or `null`)

**Migration behavior**:

1. Reader detects `schema_version`
2. For v1, infer `host_owner` per file from path patterns at read time:
   - `.claude/*` → `claude`
   - `.codex/*` → `codex` (rare; codex never wrote here per FR-008, but defensive)
   - `.cursor/*` → `cursor`
   - `.github/agents/*.agent.md`, `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md` → `copilot`
   - Otherwise (`.dotnet-ai-kit/config.yml`, `.dotnet-ai-kit/project.yml`) → `null`
3. After any successful operation that writes the manifest (`init`, `upgrade --copilot`, `migrate`), the manifest is upgraded to v2 (writer always emits v2)
4. `migrate` is the natural upgrade point; running `migrate --dry-run` does NOT upgrade the manifest (only the apply path writes)

**Rationale**: Feature 018 manifests exist in dogfood repos. Strict-write/new-schema-only forces a separate pre-migration step or breaks dogfood workflows.

**Contract**: `contracts/manifest-json.schema.json` uses `oneOf` to accept v1 or v2 read; writer is documented as always v2.

**Tests**: `tests/contract/test_manifest_schema.py` asserts both v1 and v2 readable; `tests/unit/test_fr020_host_owner_all_values.py` asserts v1 inference matches expected host_owner per path pattern.

## Summary

| Item | Status | Closure |
|--|--|--|
| R1 Claude manifest schema | RESOLVED | Architecture-phase debate |
| R2 Codex plugin schema | RESOLVED (scalar paths per round-3) | Plan-phase round 3 |
| R3 Cursor plugin packaging | RESOLVED (`agents` key, not `subagents`) | Plan-phase round 3 |
| R4 Cursor sub-agent loader | RESOLVED (per `cursor/plugins/agent-compatibility` evidence) | Plan-phase round 2-3 |
| R5 Copilot customization paths | RESOLVED (expanded frontmatter allow-list) | Plan-phase round 3 |
| R6 csharp-lsp dependency | RESOLVED | Architecture-phase debate |
| R7 Per-OS plugin-cache paths | RESOLVED (corrected paths per Codex evidence; Cursor marketplace path verified at commit 6/9 ground-truth) | Plan-phase round 3 |
| R8 Token-counting library | RESOLVED (`tiktoken>=0.13.0`, `--only-binary`, 2000-char hard fallback) | Plan-phase round 3 |
| R9 JSON schema library | RESOLVED | `jsonschema>=4.0` |
| R10 Binary-on-PATH detection | RESOLVED | `shutil.which()` |
| R11 Manifest hash algorithm | RESOLVED (SHA-256 + v1/v2 schema versioning) | Plan-phase round 3 |
| R12 Cursor one-blob migration | RESOLVED | Drop blob; emit per-rule `.mdc`; migrate inherits cleanup |
| R13 Codex root AGENTS.md removal | RESOLVED | Delete code path; root file user-owned |
| R14 Host manifest field-shape | RESOLVED | Plan-phase round 3 |
| R15 Host reload mechanisms | PARTIAL — re-verify Codex CLI / Cursor docs before commit 15 ships | Plan-phase round 3 |
| R16 Legacy manifest compat | RESOLVED | Plan-phase round 3 |

One item (R15) remains as "verify before commit 15 ships" because the answer affects release-notes documentation, not implementation correctness. R4 and R7 are now fully closed using Codex's PQ1/PQ2/PQ3 evidence.
