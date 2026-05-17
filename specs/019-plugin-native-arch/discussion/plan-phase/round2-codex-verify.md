# Plan Round 2 - Codex verification

## Verdict

Counter-list, not clean sign-off.

Claude's round 2 accepts the core corrections and most proposed edits are concrete enough to apply. Four blockers remain before `/speckit.tasks`: the hooks contract rewrite contains stale event names, the Cursor agent output directory is still unsupported by evidence, the quickstart install-command finding has no edit response, and the commit 11/12 LSP/MCP test gaps are still missing from the inventory.

## Commit Headings - AGREED

Restore FINAL's byte-identical headings. Claude's proposed headings now match `FINAL-REPORT.md:91-105`, including "frozenset", "manifest", "New", and the original commit-6 "subagent" title (`issues/plugin-native-architecture/FINAL-REPORT.md:91-105`, `specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:28-43`).

## P1 Commit-6 Title - AGREED

Keeping "subagent" in the commit title is acceptable because FINAL uses that wording (`issues/plugin-native-architecture/FINAL-REPORT.md:96`). The contract/manifests must still use Cursor's actual `agents` field, which Claude accepts (`specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:34`, `specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:227-231`).

## Constitution / Complexity - AGREED

The contradiction is resolved if the constitution row is removed from Complexity Tracking while commit 14's first acceptance check gates the v1.0.8 amendment. Current plan contradicts itself by saying the amendment is not complexity and then listing it (`specs/019-plugin-native-arch/plan.md:79-84`, `specs/019-plugin-native-arch/plan.md:242-249`); Claude's fix removes that row and adds `test_constitution_amendment.py` as a precondition (`specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:168-173`).

## Contract Schema Rewrites - DISAGREE, NARROW

Codex schema: AGREED. The current schema wrongly models `skills` as arrays and MCP/hooks as object wrappers (`specs/019-plugin-native-arch/contracts/codex-plugin.schema.json:13-33`). Claude's scalar `./` path rewrite matches Codex docs showing `skills`, `mcpServers`, `apps`, and `hooks` as relative path strings plus `interface` metadata (`specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:51-62`, `specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:141`, `https://developers.openai.com/codex/plugins/build:843-899`).

Cursor schema: AGREED on `agents` field, DISAGREE on `./agents-cursor/`. The current contract's `subagents` field is wrong (`specs/019-plugin-native-arch/contracts/cursor-plugin.schema.json:40-43`), and Claude correctly switches to `agents` (`specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:64-78`, `specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:140`). But the only verified working official fixture uses `"agents": "./agents/"` and an `agents/` folder, not `agents-cursor/` (`https://raw.githubusercontent.com/cursor/plugins/main/agent-compatibility/.cursor-plugin/plugin.json:0`, `https://github.com/cursor/plugins/tree/main/agent-compatibility:233-239`). Use `./agents/` for the Cursor plugin output, or produce fresh evidence that Cursor honors arbitrary `agents` paths before keeping `./agents-cursor/`.

Hooks schema: DISAGREE. Event-keyed object is the right correction, but Claude's explicit example lists `PreCommit`/`PostEdit` (`specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:142`). Current `hooks/hooks.json` is event-keyed under `SessionStart`, `PreToolUse`, and `PostToolUse`, with hook handlers nested under each event (`hooks/hooks.json:2-60`), and Codex docs show the same event-keyed `hooks` object shape (`https://developers.openai.com/codex/plugins/build:930-955`). The rewrite must model the current event names/handler shape, including `PostToolUse`, not carry stale `PreCommit`/`PostEdit` names.

Manifest schema: AGREED. Current schema rejects current manifests because it omits `schema_version` while `cli.py` writes it (`specs/019-plugin-native-arch/contracts/manifest-json.schema.json:7-8`, `src/dotnet_ai_kit/cli.py:433-438`), and it requires `host_owner` on every file (`specs/019-plugin-native-arch/contracts/manifest-json.schema.json:24-27`). Claude's v1-read/v2-write plan with path-based host inference is sufficient if encoded as distinct read/write validation modes (`specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:93-117`, `specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:143`).

Copilot agent contract: AGREED. Current contract only shows `name` and `description` (`specs/019-plugin-native-arch/contracts/copilot-agent.contract.md:16-25`). Claude's allow-list matches current GitHub fields and excludes retired `infer` (`specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:80`, `specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:144`, `https://docs.github.com/en/copilot/reference/custom-agents-configuration:536-550`).

Claude/config/Copilot instruction/session contracts: AGREED. The accepted edits address the loose Claude `lspServers.additionalProperties: true`, `ai_tools` legacy alias, FR-008 force-render opt-in, detected-path-only Copilot instruction files, Cursor plugin-root uncertainty, and hard 2000-character fallback (`specs/019-plugin-native-arch/contracts/claude-plugin.schema.json:46-50`, `specs/019-plugin-native-arch/contracts/config-yml.schema.json:7-15`, `specs/019-plugin-native-arch/contracts/copilot-instructions.contract.md:33-35`, `specs/019-plugin-native-arch/contracts/copilot-instructions-path.contract.md:13-16`, `specs/019-plugin-native-arch/contracts/pretooluse-arch-profile.contract.md:36-41`, `specs/019-plugin-native-arch/contracts/session-start-bootstrap.contract.md:23-28`, `specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:145-150`).

## Research R7 / Paths - AGREED WITH ONE LIMIT

R7 now matches the PQ1/PQ2 evidence for Codex and Cursor local testing: Codex installed marketplace path is `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/`, and Cursor local testing path is `~/.cursor/plugins/local/<name>/` (`specs/019-plugin-native-arch/research.md:83-99`, `specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:82-89`, `https://developers.openai.com/codex/plugins/build:801-809`, `https://github.com/cursor/plugins/tree/main/agent-compatibility:325-329`). Keep the removal of `.cursor/extensions`. Do not treat Cursor marketplace cache inspection as fully resolved until the first real install path is verified; round 2 still phrases that part as "verify path on first install" (`specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:87`).

## R11 / R16 Legacy Manifest Compatibility - AGREED

The v1/v2 read strategy is robust enough: current manifests have `schema_version="1"` (`src/dotnet_ai_kit/cli.py:433-438`), current draft contracts lack that field and require new `host_owner` (`specs/019-plugin-native-arch/contracts/manifest-json.schema.json:7-8`, `specs/019-plugin-native-arch/contracts/manifest-json.schema.json:24-27`), and Claude now requires v1 legacy inference plus v2 writes (`specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:18`, `specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:93-117`).

## New Contracts - AGREED WITH TWO FIXES

The six new contracts close the major round-1 gaps: source agent format, `check` exit classes, `migrate` reporting/legacy reads, `render` CLI shape, linked-secondary footprint, and Cursor fixture decision (`specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:152-159`). Two fixes are required while writing them:

1. `agent-source.contract.md` should not put `body` in YAML frontmatter. Existing agent files use frontmatter plus Markdown body (`agents/dotnet-architect.md:1-20`); the contract should say `name`, `description`, and `host_overrides` are frontmatter, while the Markdown body is the document body (`specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:154`).
2. `cursor-fixture-decision.contract.md` must encode P2's resolved output path after the Cursor directory decision; otherwise the fixture may validate a noncanonical shape (`specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:212-223`, `https://raw.githubusercontent.com/cursor/plugins/main/agent-compatibility/.cursor-plugin/plugin.json:0`).

## Traceability / Measurements - AGREED

These are concrete enough. Mapping every FR/SC/A/CHK to a test or manual gate closes the traceability gap, and baseline/post sections for file count, token budgets, `check`, `render`, and SessionStart are the right measurement artifact (`specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:161-164`). This also addresses the current plan's SC-001/SC-004/SC-010/SC-012/SC-013 targets without baseline capture (`specs/019-plugin-native-arch/plan.md:30-35`).

## Test Inventory / CI - DISAGREE, INCOMPLETE

The accepted inventory covers the named FR/SC gaps from the CP4 list (`specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:177-196`) and the cross-platform expansion is correct (`specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:198-208`, `specs/019-plugin-native-arch/spec.md:253`).

Two round-1 findings still need concrete tests:

1. Commit 11 still needs an explicit CHK011 fixture transcript or test artifact, not only "extend `test_smoke_claude.py`" (`specs/019-plugin-native-arch/discussion/plan-phase/round1-codex-reply.md:25`, `specs/019-plugin-native-arch/checklists/verification.md:34-37`, `specs/019-plugin-native-arch/plan.md:418-425`).
2. Commit 12 still needs an explicit contract test that `.mcp.json` removes only `csharp-ls` and retains `codebase-memory-mcp`; current `.mcp.json` contains both (`specs/019-plugin-native-arch/discussion/plan-phase/round1-codex-reply.md:27`, `.mcp.json:2-14`, `issues/plugin-native-architecture/codex/final-merged-findings.md:195`, `specs/019-plugin-native-arch/plan.md:427-434`).

## Cursor Fixture Decision - AGREED

CP6 is enforceable enough if implemented exactly: fixture pass ships `agents`; fixture fail fails CI unless the same PR removes manifest support and updates spec, schema, checklist, and release notes (`specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:16`, `specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:210-223`). This directly strengthens current A-005/SC-008/OOS-005 language (`specs/019-plugin-native-arch/spec.md:234`, `specs/019-plugin-native-arch/spec.md:248`, `specs/019-plugin-native-arch/spec.md:264`).

## P2 Cursor Directory Name - DISAGREE

The `agents-cursor/` rationale is understandable, but it adds an unverified loader variable. The evidence we have is not "any arbitrary path"; it is manifest field `agents` pointing to `./agents/` and a real `agents/` directory (`specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:233-237`, `https://raw.githubusercontent.com/cursor/plugins/main/agent-compatibility/.cursor-plugin/plugin.json:0`, `https://github.com/cursor/plugins/tree/main/agent-compatibility/agents:235-247`). Resolve by either generating Cursor-compatible files under plugin-root `agents/` and moving source-of-truth definitions elsewhere, or by producing evidence that Cursor honors `agents: "./agents-cursor/"`.

## Quickstart / Docs - DISAGREE, OMITTED EDIT

Round 1 flagged quickstart's likely-noncanonical Codex/Cursor install commands (`specs/019-plugin-native-arch/discussion/plan-phase/round1-codex-reply.md:33`, `specs/019-plugin-native-arch/quickstart.md:30-45`). Claude's 22-file edit list does not include `quickstart.md` (`specs/019-plugin-native-arch/discussion/plan-phase/round2-claude-reply.md:239-265`). Add a quickstart edit: Codex should route through `codex` then `/plugins` / plugin browser install, matching current Codex docs (`https://developers.openai.com/codex/plugins:640-657`), and Cursor instructions should cite the verified local/marketplace path used by the fixture.

## Required Round 3 Counter-List

1. Fix `hooks-json.schema.json` rewrite to model the actual event-keyed object and `PostToolUse` handler shape.
2. Resolve Cursor output directory: prefer `agents/` for plugin-loaded Cursor files unless new evidence proves `agents-cursor/`.
3. Add `quickstart.md` to the concrete edit list and correct host install instructions.
4. Add explicit tests/artifacts for CHK011 LSP edit-time diagnostics and commit-12 MCP retention/removal.
5. While writing `agent-source.contract.md`, make Markdown body a document body, not a frontmatter field.

After those five corrections, I would sign off on applying the 22+ edits and proceeding to `/speckit.tasks`.
