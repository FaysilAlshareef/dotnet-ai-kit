# Plan Round 1 — Codex reply

## Plan critique

Commit 1 — REVISE. The ordering is right, but the heading is not byte-identical to FINAL-REPORT: FINAL says "Expand `SUPPORTED_AI_TOOLS` frozenset + multi-host config tests" while plan drops "frozenset" (`issues/plugin-native-architecture/FINAL-REPORT.md:91`, `specs/019-plugin-native-arch/plan.md:328`). The test scope is also too narrow for FR-016: `tests/test_agents.py` and config schema tests do not prove `init` writes only selected-host files and skips unselected hosts, which CHK038 requires (`specs/019-plugin-native-arch/checklists/verification.md:80-81`).

Commit 2 — REVISE. The FINAL heading is "Update `pyproject.toml` packaging to include `.codex-plugin/`, `.cursor-plugin/`"; plan says "Update `pyproject.toml` packaging includes" and adds many more paths (`issues/plugin-native-architecture/FINAL-REPORT.md:92`, `specs/019-plugin-native-arch/plan.md:337-344`). The extra includes may be necessary, but this is not byte-identical and needs a packaging manifest inventory test that asserts no missing generated host assets, not just the three manifest dirs.

Commit 3 — REVISE. FINAL says "Add `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/` manifests"; plan says "Add three manifest twins" (`issues/plugin-native-architecture/FINAL-REPORT.md:93`, `specs/019-plugin-native-arch/plan.md:346-353`). More importantly, the Cursor and Codex contract schemas are currently wrong: current Codex docs use path-valued manifest entries such as `"skills": "./skills/"`, `"mcpServers": "./.mcp.json"`, and `"hooks": "./hooks/hooks.json"`, with path rules requiring `./` prefixes (`https://developers.openai.com/codex/plugins/build:843-860`, `https://developers.openai.com/codex/plugins/build:896-899`), while the draft Codex schema requires object wrappers (`specs/019-plugin-native-arch/contracts/codex-plugin.schema.json:18-33`).

Commit 4 — REVISE. The Claude native init cut is directionally right, but the test only names Claude (`specs/019-plugin-native-arch/plan.md:355-362`). FR-005 and FR-006 bind all plugin-supporting hosts, not just Claude (`specs/019-plugin-native-arch/spec.md:153-154`). Add a shared per-host footprint assertion for Claude/Codex/Cursor and an SC-001 file-count fixture; the plan currently mentions SC-001 acceptance without an explicit test (`specs/019-plugin-native-arch/plan.md:362`).

Commit 5 — REVISE. The root `AGENTS.md` removal is correct and grounded in the current collision (`src/dotnet_ai_kit/agents.py:51`, `src/dotnet_ai_kit/copier.py:276-317`), but `test_unmanaged_paths_untouched.py` as described only protects root `AGENTS.md` (`specs/019-plugin-native-arch/plan.md:364-371`). FR-008 generalizes to every non-manifest path and A-008 gives concrete .NET root examples including `.editorconfig`, `Directory.Build.props`, `global.json`, CI workflows, README, license, and solution/project files (`specs/019-plugin-native-arch/spec.md:156`, `specs/019-plugin-native-arch/spec.md:251`). This needs parameterized tests over the A-008 list and across every write command.

Commit 6 — DISAGREE until Cursor artifacts are corrected. The plan uses `.cursor-plugin/plugin.json` `sub-agent` / `subagents` language and `agents-cursor/<one-fixture>.md` (`specs/019-plugin-native-arch/plan.md:373-380`; `specs/019-plugin-native-arch/contracts/cursor-plugin.schema.json:40-43`). Current official Cursor plugin repo evidence points to `.cursor-plugin/plugin.json` with `"agents": "./agents/"` and an `agents/` directory, not a `subagents` manifest key (`https://raw.githubusercontent.com/cursor/plugins/main/agent-compatibility/.cursor-plugin/plugin.json:0`, `https://github.com/cursor/plugins/tree/main/agent-compatibility:233-239`). The fixture should follow that shape unless Cursor publishes a different loader spec before implementation.

Commit 7 — REVISE. Copilot render belongs here, but the Copilot agent contract is already stale: it only allows `name` and `description` (`specs/019-plugin-native-arch/contracts/copilot-agent.contract.md:16-25`), while current GitHub custom-agent frontmatter also documents `target`, `tools`, `model`, `disable-model-invocation`, `user-invocable`, `mcp-servers`, and `metadata` (`https://docs.github.com/en/copilot/reference/custom-agents-configuration:536-550`). The generator should be allow-list based, but the allow-list needs current docs.

Commit 8 — REVISE. Project schema validation is needed, but the schema alone does not test detected-path correctness, which FR-017 and CHK015 require (`specs/019-plugin-native-arch/spec.md:174`, `specs/019-plugin-native-arch/checklists/verification.md:41-43`). Also, `ProjectMetadata.linked_repos.hosts` must be validated as a subset of `UserConfig.enabled_hosts`; data-model states that invariant, but JSON schema cannot enforce cross-file consistency by itself (`specs/019-plugin-native-arch/data-model.md:191`, `specs/019-plugin-native-arch/data-model.md:264`).

Commit 9 — REVISE. This is under-specified because R7 is still partial and currently wrong for Codex. The plan says Codex check inspects `~/.codex/plugins/` (`specs/019-plugin-native-arch/research.md:89-95`), but current Codex docs say installed marketplace plugins live under `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/` (`https://developers.openai.com/codex/plugins/build:801-809`). Cursor likewise should not probe `.cursor/extensions` as a plugin path when official plugin material and forum guidance point to `.cursor/plugins/local` and internal cache (`https://github.com/cursor/plugins/tree/main/agent-compatibility:325-329`, `https://forum.cursor.com/t/local-plugin-is-not-being-picked-up-by-cursor/156549/3:9-12`).

Commit 10 — REVISE. The migrate command direction is correct, but the schema is not backward-tolerant enough for the migration it is supposed to perform. Current manifest writing includes `schema_version` (`src/dotnet_ai_kit/cli.py:433-438`), while the draft manifest schema forbids additional properties and does not define `schema_version` (`specs/019-plugin-native-arch/contracts/manifest-json.schema.json:7-8`). It also requires new `host_owner` on every file (`specs/019-plugin-native-arch/contracts/manifest-json.schema.json:24-27`), so old feature-018 manifests will fail strict parsing before they can be migrated.

Commit 11 — REVISE. Adding `csharp-lsp` dependency is right, but the plan's acceptance says CI verifies edit-time diagnostics surface (`specs/019-plugin-native-arch/plan.md:418-425`) without naming a concrete host fixture for CHK011. The checklist makes CHK011 part of the gate before MCP removal (`specs/019-plugin-native-arch/checklists/verification.md:34-37`); commit 11 needs an explicit fixture transcript or test artifact, not just an extension of `test_smoke_claude.py`.

Commit 12 — REVISE. The dependency ordering is correct, but "existing tests; CI gate enforces" is not a test inventory (`specs/019-plugin-native-arch/plan.md:427-434`). Add an explicit contract test that `.mcp.json` retains `codebase-memory-mcp` and removes only `csharp-ls`; current `.mcp.json` contains both (`.mcp.json:2-14`), and the merged findings call out that `codebase-memory-mcp` must remain (`issues/plugin-native-architecture/codex/final-merged-findings.md:195`).

Commit 13 — REVISE. The hook idea is right, but the hooks contract is structurally incompatible with both the current repo and Codex docs. Current `hooks/hooks.json` is an object keyed by hook event (`hooks/hooks.json:2-60`), and Codex docs show the same event-keyed object shape (`https://developers.openai.com/codex/plugins/build:930-946`); the draft schema instead requires `hooks` to be an array of six entries (`specs/019-plugin-native-arch/contracts/hooks-json.schema.json:10-15`). Fix the contract before implementation.

Commit 14 — REVISE. The 5/11 split matches FR-011 (`specs/019-plugin-native-arch/spec.md:165`), but the constitution handling is internally inconsistent: the Constitution Check says the amendment is "NOT a Complexity Tracking entry" (`specs/019-plugin-native-arch/plan.md:83`), while Complexity Tracking includes it (`specs/019-plugin-native-arch/plan.md:249`). I prefer a separate governance commit before the rule move, or at minimum a commit-14 precondition test that fails if the constitution version and whitelist are not updated before the rules are reclassified.

Commit 15 — REVISE. Docs are necessary, but the plan says "no FR maps directly" (`specs/019-plugin-native-arch/plan.md:454-459`) even though CHK055-CHK063 are explicit release documentation gates and A-008 user-facing path docs are binding (`specs/019-plugin-native-arch/checklists/verification.md:119-132`, `specs/019-plugin-native-arch/spec.md:251`). Quickstart also uses likely-noncanonical install commands (`specs/019-plugin-native-arch/quickstart.md:30-45`); Codex docs route CLI users through `/plugins` and marketplace install UI (`https://developers.openai.com/codex/plugins:640-657`), not `codex plugin install owner/repo`.

Research items:

- R1 — AGREE. Claude manifest fields are a valid research base, but the contract should distinguish auto-discovered plugin layout from manifest fields (`specs/019-plugin-native-arch/research.md:7-15`).
- R2 — REVISE. "No agents/LSP/monitors/settings/bin" is still right for Codex plugin primitives, but the manifest field shapes in the contracts are wrong per current Codex docs (`specs/019-plugin-native-arch/research.md:17-25`, `https://developers.openai.com/codex/plugins/build:843-860`).
- R3 — REVISE. Cursor packages agents, but current official repo material uses an `agents` key/path, not `subagents` (`specs/019-plugin-native-arch/research.md:27-38`, `https://raw.githubusercontent.com/cursor/plugins/main/agent-compatibility/.cursor-plugin/plugin.json:0`).
- R4 — DISAGREE. This is no longer acceptable as "verify before commit"; current plan artifacts already picked the wrong `subagents` shape (`specs/019-plugin-native-arch/research.md:41-57`, `specs/019-plugin-native-arch/contracts/cursor-plugin.schema.json:40-43`). Resolve now.
- R5 — REVISE. The paths are right, but Copilot custom-agent frontmatter has expanded beyond name/description (`specs/019-plugin-native-arch/research.md:59-69`, `https://docs.github.com/en/copilot/reference/custom-agents-configuration:536-550`).
- R6 — AGREE. `csharp-lsp` plus `csharp-ls` binary validation remains the right gate (`specs/019-plugin-native-arch/research.md:71-81`).
- R7 — DISAGREE. Codex path is wrong for installed plugins; Cursor path is unresolved and `.cursor/extensions` should not be in the plan without evidence (`specs/019-plugin-native-arch/research.md:83-99`, `https://developers.openai.com/codex/plugins/build:801-809`, `https://forum.cursor.com/t/local-plugin-is-not-being-picked-up-by-cursor/156549/3:9-12`).
- R8 — REVISE. `tiktoken` is acceptable on Windows x64 in 2026 because PyPI ships win_amd64 wheels for CPython 3.10-3.14 (`https://pypi.org/project/tiktoken/:397-450`), but `tiktoken>=0.5.0` is too loose and the fallback must be explicitly conservative (`specs/019-plugin-native-arch/research.md:101-118`).
- R9 — AGREE. `jsonschema` is a reasonable dependency, assuming schemas are fixed first (`specs/019-plugin-native-arch/research.md:120-132`).
- R10 — AGREE. `shutil.which()` is the right cross-platform binary check (`specs/019-plugin-native-arch/research.md:134-146`).
- R11 — REVISE. Reusing SHA-256 is right, but adding required `host_owner` must include legacy-manifest inference and a schema-version migration path (`specs/019-plugin-native-arch/research.md:148-160`, `src/dotnet_ai_kit/cli.py:433-438`).
- R12 — REVISE. Dropping Cursor one-blob output is right, but the new Cursor plugin schema must use current Cursor agent/rule field names and plugin root layout (`specs/019-plugin-native-arch/research.md:162-170`, `https://github.com/cursor/plugins:286-300`).
- R13 — AGREE. Root `AGENTS.md` is user-owned and the current Codex emitter must be deleted (`specs/019-plugin-native-arch/research.md:172-183`, `src/dotnet_ai_kit/copier.py:276-317`).
- MISSING R14. Resolve host plugin manifest field shape by host, including scalar-vs-array path values and `./` path-prefix rules for Codex and Cursor before contract tests are written.
- MISSING R15. Resolve host reload/update mechanisms for CHK056; spec says docs must call out each host reload mechanism, but plan only names Claude reload in prose (`specs/019-plugin-native-arch/spec.md:131`, `specs/019-plugin-native-arch/checklists/verification.md:119-120`).
- MISSING R16. Resolve legacy manifest compatibility: schema_version, missing host_owner, and path-to-host inference.

Entities:

- `ClaudePluginManifest` — REVISE. The entity requires `lspServers` and `dependencies` (`specs/019-plugin-native-arch/data-model.md:21-25`); confirm whether `csharp-lsp` belongs in `dependencies` only or also in `lspServers` before schema hardening.
- `CodexPluginManifest` — REVISE. Field names may be right, field shapes are wrong: docs show scalar relative paths, not arrays/objects (`specs/019-plugin-native-arch/data-model.md:29-42`, `https://developers.openai.com/codex/plugins/build:843-860`).
- `CursorPluginManifest` — DISAGREE. Replace `subagents` with current `agents` evidence and use `agents/` or a documented plugin-root path (`specs/019-plugin-native-arch/data-model.md:44-55`, `https://github.com/cursor/plugins/tree/main/agent-compatibility:233-248`).
- `ProjectMetadata` — REVISE. Good start, but cross-file invariants with `UserConfig.enabled_hosts` need a validation-layer contract, not only JSON schema (`specs/019-plugin-native-arch/data-model.md:57-71`, `specs/019-plugin-native-arch/data-model.md:264`).
- `UserConfig` — REVISE. Existing code currently uses `ai_tools`; plan introduces `enabled_hosts` (`specs/019-plugin-native-arch/data-model.md:73-82`). The migration/compat story between those field names must be explicit.
- `ManagedFile` — REVISE. `host_owner` is needed, but it must be optional-on-read/required-on-write during migration (`specs/019-plugin-native-arch/data-model.md:84-95`).
- `Manifest` — REVISE. Missing `schema_version` is a hard contract bug because current manifest writer emits it (`specs/019-plugin-native-arch/data-model.md:97-105`, `src/dotnet_ai_kit/cli.py:433-438`).
- `MigrationBackup` — REVISE. The entity lists backup entries but no restore/manifest snapshot metadata. FR-021 and SC-007 need enough metadata to audit moves and prove user-modified files stayed put (`specs/019-plugin-native-arch/data-model.md:107-125`, `specs/019-plugin-native-arch/spec.md:181-183`).
- `Agent` — REVISE. Needs a source-of-truth contract file. `host_overrides` is too vague unless each host's allowed frontmatter is enumerated (`specs/019-plugin-native-arch/data-model.md:127-136`).
- `Rule` — REVISE. The 5/11 names are right, but `loads_when` is underspecified and uncontracted; FR-011 says JIT rules load only when the skill/task applies (`specs/019-plugin-native-arch/spec.md:165`, `specs/019-plugin-native-arch/data-model.md:151-159`).
- `ArchitectureProfile` — AGREE. This is adequate if PreToolUse missing/corrupt metadata paths are tested (`specs/019-plugin-native-arch/data-model.md:161-170`, `specs/019-plugin-native-arch/checklists/verification.md:96-100`).
- `SmokeFixture` — REVISE. Add explicit fail-state semantics and required CI status names; current lifecycle says Cursor fail triggers A-005, but not what files/specs must change before merge (`specs/019-plugin-native-arch/data-model.md:172-181`, `specs/019-plugin-native-arch/data-model.md:244-260`).
- `LinkedSecondaryRepo` — REVISE. Needs ownership/manifest details for secondary manifests and migration; current writer copies commands/rules/skills/agents directly (`src/dotnet_ai_kit/copier.py:1090-1147`), which is exactly the FR-033 back door (`specs/019-plugin-native-arch/spec.md:205`).
- `HookConfig` — DISAGREE as modeled. Current hook config is event-keyed object, not six flat entries (`hooks/hooks.json:2-60`, `specs/019-plugin-native-arch/data-model.md:193-202`).

Contracts:

- `claude-plugin.schema.json` — REVISE. `lspServers.additionalProperties: true` is too loose for the most sensitive migration (`specs/019-plugin-native-arch/contracts/claude-plugin.schema.json:46-50`); CHK010 needs a precise declaration (`specs/019-plugin-native-arch/checklists/verification.md:34-36`).
- `codex-plugin.schema.json` — DISAGREE. The schema requires object wrappers and arrays where docs show relative path strings, and it omits documented metadata such as `interface` (`specs/019-plugin-native-arch/contracts/codex-plugin.schema.json:13-35`, `https://developers.openai.com/codex/plugins/build:884-899`).
- `config-yml.schema.json` — REVISE. `enabled_hosts` is clean, but existing code/config uses `ai_tools`; add explicit migration or alias handling (`specs/019-plugin-native-arch/contracts/config-yml.schema.json:7-15`, `src/dotnet_ai_kit/copier.py:1096-1100`).
- `cursor-plugin.schema.json` — DISAGREE. It uses `subagents`; current Cursor official plugin manifests use `agents` (`specs/019-plugin-native-arch/contracts/cursor-plugin.schema.json:40-43`, `https://raw.githubusercontent.com/cursor/plugins/main/agent-compatibility/.cursor-plugin/plugin.json:0`).
- `hooks-json.schema.json` — DISAGREE. It does not match current `hooks/hooks.json` or Codex plugin hook docs (`specs/019-plugin-native-arch/contracts/hooks-json.schema.json:10-25`, `hooks/hooks.json:2-60`, `https://developers.openai.com/codex/plugins/build:930-946`).
- `manifest-json.schema.json` — DISAGREE. It rejects current manifests because `schema_version` is missing from the schema and `additionalProperties` is false (`specs/019-plugin-native-arch/contracts/manifest-json.schema.json:7-8`, `src/dotnet_ai_kit/cli.py:433-438`).
- `project-yml.schema.json` — REVISE. Good basic schema, but it cannot enforce linked repo host subset, path existence, or profile existence; those need validation tests (`specs/019-plugin-native-arch/contracts/project-yml.schema.json:51-69`, `specs/019-plugin-native-arch/checklists/verification.md:41-43`).
- `copilot-agent.contract.md` — DISAGREE. It under-documents supported frontmatter; GitHub documents more than `name` and `description` (`specs/019-plugin-native-arch/contracts/copilot-agent.contract.md:16-25`, `https://docs.github.com/en/copilot/reference/custom-agents-configuration:536-550`).
- `copilot-instructions.contract.md` — REVISE. It says pre-existing `.github/copilot-instructions.md` exits non-zero (`specs/019-plugin-native-arch/contracts/copilot-instructions.contract.md:33-35`), but FR-008 allows explicit opt-in to exact paths; the contract needs the opt-in behavior, not only failure (`specs/019-plugin-native-arch/spec.md:156`).
- `copilot-instructions-path.contract.md` — REVISE. It requires 11 path-scoped instruction files (`specs/019-plugin-native-arch/contracts/copilot-instructions-path.contract.md:11-16`), but path scopes should be generated only where detected paths exist or the contract must say how generic projects map every domain rule.
- `pretooluse-arch-profile.contract.md` — REVISE. It claims equivalent plugin-root variables for other hosts (`specs/019-plugin-native-arch/contracts/pretooluse-arch-profile.contract.md:36-41`), but only Codex docs currently confirm `PLUGIN_ROOT` plus Claude compatibility env vars (`https://developers.openai.com/codex/plugins/build:954-955`). Cursor equivalent must be verified.
- `session-start-bootstrap.contract.md` — REVISE. Good budget intent, but the fallback "character-length x 0.25" is not conservative enough to prove a hard 500-token cap without tokenizer availability (`specs/019-plugin-native-arch/contracts/session-start-bootstrap.contract.md:23-27`).
- MISSING contract: `agents/<name>.md` source-of-truth format and allowed per-host override keys.
- MISSING contract: `dotnet-ai check` output and unique exit-code classes per FR-031.
- MISSING contract: `dotnet-ai migrate` classification/backup report, including legacy manifest read behavior.
- MISSING contract: `dotnet-ai render` CLI shape, error cases, and explicit Claude-only v1 output.
- MISSING contract: linked-secondary-repository writer behavior and manifest ownership.

Open items P1-P7:

- P1 — No. The order is semantically aligned but not byte-identical. Examples: commit 1 drops "frozenset", commit 2 changes the full title, commit 3 says "manifest twins", commit 13 drops "New", and commit 14 adds "constitution v1.0.8 amendment" (`issues/plugin-native-architecture/FINAL-REPORT.md:91-105`, `specs/019-plugin-native-arch/plan.md:328-456`).
- P2 — No as written. PASS-CONDITIONAL is reasonable only if governance is atomic and preconditioned, but the plan contradicts itself by saying the amendment is not a Complexity Tracking entry while listing it there (`specs/019-plugin-native-arch/plan.md:83`, `specs/019-plugin-native-arch/plan.md:249`).
- P3 — REVISE. `hosts/` is a good boundary for install/cache/check/init footprint, but the plan must make linked-secondary writers consume the same host adapters rather than leaving `copier.py` as a parallel copy path (`src/dotnet_ai_kit/copier.py:1090-1147`, `specs/019-plugin-native-arch/plan.md:125-145`).
- P4 — No. Test inventory is incomplete for FR-008, FR-011/012 JIT, FR-014/015, FR-019 error/shape, FR-020 all host_owner values, FR-029 fail path, FR-031 exit classes, FR-035 admission gate, SC-001, SC-002, SC-003, SC-004 baseline, SC-005, SC-010/012 perf, and SC-014 migration into secondaries (`specs/019-plugin-native-arch/plan.md:196-225`, `specs/019-plugin-native-arch/checklists/verification.md:12-132`).
- P5 — No. A-010 explicitly requires validation, smoke fixtures, packaging, and migration in CI on Windows/macOS/Linux, and says every FR is binding on each OS (`specs/019-plugin-native-arch/spec.md:253`). The plan scopes matrix language to only FR-017/FR-018/FR-029/FR-030 and misses cross-platform path/backup/unmanaged-path cases (`specs/019-plugin-native-arch/plan.md:27`, `specs/019-plugin-native-arch/plan.md:194`).
- P6 — No. "Spec/plan revised accordingly" has no enforcement. The PR should fail unless either Cursor agent fixture passes and full generation ships, or the spec/checklist/contracts/manifests/release notes are changed in the same PR to remove full Cursor agent support (`specs/019-plugin-native-arch/plan.md:380`, `specs/019-plugin-native-arch/spec.md:248`, `specs/019-plugin-native-arch/spec.md:264`).
- P7 — Missing R14-R16 above. R4 and R7 are not acceptable as late re-verifications because current plan artifacts already depend on their answers.

## Verdict on each contestable claim CP1-CP12

CP1 — DISAGREE. The 15-commit sequence is ordered the same, but it is not byte-for-byte. FINAL lines 91-105 are exact numbered titles; plan headings at lines 328-456 repeatedly reword them and add commit-14 constitution scope (`issues/plugin-native-architecture/FINAL-REPORT.md:91-105`, `specs/019-plugin-native-arch/plan.md:328-456`).

CP2 — REVISE. PASS-CONDITIONAL can work only if the constitution amendment is a first-class gate, but plan text is inconsistent: "NOT a Complexity Tracking entry" in the Constitution Check, then listed in Complexity Tracking (`specs/019-plugin-native-arch/plan.md:83`, `specs/019-plugin-native-arch/plan.md:249`). I would split a governance commit before commit 14 or make commit 14's first acceptance check the constitution version/whitelist update.

CP3 — REVISE. A `hosts/` package is the right direction for per-host cache paths, install verification, permissions merge, and plugin-native init, but it must be the only writer abstraction consumed by primary and linked-secondary paths. Otherwise `copier.py` remains a back door that writes commands/rules/skills/agents (`src/dotnet_ai_kit/copier.py:1090-1147`), violating FR-033 (`specs/019-plugin-native-arch/spec.md:205`).

CP4 — DISAGREE. The inventory is not complete. The plan lists about 28 tests (`specs/019-plugin-native-arch/plan.md:196-225`), but the verification checklist has CHK001-CHK063 with several gates that have no named test: SC-001 footprint, SC-002 two-solution propagation, SC-005 no duplicate Claude entries, CHK040 unique exit classes, CHK049-CHK051 linked-secondary init/migrate, and CHK052 host admission (`specs/019-plugin-native-arch/checklists/verification.md:16-132`).

CP5 — DISAGREE. The matrix scoping is too narrow. A-010 names FR-017, FR-018, FR-029, FR-030 as mandatory three-OS CI, but also says every FR is binding on each OS and calls out path handling/search-path semantics/file encoding (`specs/019-plugin-native-arch/spec.md:253`). At minimum, FR-008 unmanaged path tests, FR-021 backup path tests, FR-031/032 manifest path tests, FR-033 linked repo tests, and SC-013 hook line-ending/env tests need cross-platform coverage tiers.

CP6 — DISAGREE. Conditional Cursor scope handling is not explicit enough. The spec says the release must not quietly ship a failed capability as supported (`specs/019-plugin-native-arch/spec.md:135`, `specs/019-plugin-native-arch/spec.md:248`); plan says only "spec/plan revised accordingly" (`specs/019-plugin-native-arch/plan.md:380`). Define a blocking CI decision: fixture pass ships `agents`; fixture fail removes generated Cursor agents, updates spec/contracts/checklists/release notes, and leaves Cursor supported only for documented primitives that pass.

CP7 — DISAGREE. FR-033 is not sketched concretely. The existing linked writer explicitly deploys commands, rules, skills, and agents into secondaries (`src/dotnet_ai_kit/copier.py:1090-1147`); saying it is "constrained per FR-033" in a comment is not a plan (`specs/019-plugin-native-arch/plan.md:132`). It must be refactored to call the same host adapter footprint writer as primary init and must get separate init + migrate linked-repo tests.

CP8 — DISAGREE. The `host_owner` schema is not backward-compatible for migration. The draft schema requires `host_owner` and forbids unmodeled fields (`specs/019-plugin-native-arch/contracts/manifest-json.schema.json:7-8`, `specs/019-plugin-native-arch/contracts/manifest-json.schema.json:24-27`), but current manifests include `schema_version` (`src/dotnet_ai_kit/cli.py:433-438`) and older manifests will lack `host_owner`. Reader must accept legacy manifests and infer host ownership from paths before writing the new schema.

CP9 — REVISE. Claude-shaped render is acceptable because SC-012 explicitly scopes v1 that way (`specs/019-plugin-native-arch/spec.md:238`), but the CLI contract must make it explicit: `render` defaults to `--host claude`, rejects unsupported host shapes with a clear v1.1 deferral message, and tests CHK045 so it never silently emits the wrong shape (`specs/019-plugin-native-arch/checklists/verification.md:90-95`).

CP10 — DISAGREE. R4 and R7 cannot remain partial. Cursor current repo evidence contradicts the plan's `subagents` key (`https://raw.githubusercontent.com/cursor/plugins/main/agent-compatibility/.cursor-plugin/plugin.json:0`), and Codex docs contradict `~/.codex/plugins/` as the installed cache check path (`https://developers.openai.com/codex/plugins/build:801-809`). Plan-phase sign-off should block until these are resolved in research.md, contracts, and quickstart.

CP11 — DISAGREE. The 11 contracts are not the right surface yet. Some are wrong (`hooks-json`, `codex-plugin`, `cursor-plugin`, `manifest-json`), and several obvious contracts are missing: source agent format, check exit classes, migrate output/legacy read behavior, render CLI, linked-secondary footprint. FR-026/027, FR-031/032, FR-033, and FR-019 need those contracts (`specs/019-plugin-native-arch/spec.md:189-205`).

CP12 — REVISE. `tiktoken` is fine as primary on x64 CI; PyPI 0.13.0 has Windows x86-64 wheels for CPython 3.10-3.14 (`https://pypi.org/project/tiktoken/:397-450`). But pinning `>=0.5.0` is too weak for modern Python/Windows assurance, and the character fallback must be conservative. Use `tiktoken>=0.13.0` or install with `--only-binary=:all:` in CI, and make fallback use a hard character ceiling rather than treating `chars * 0.25` as proof.

## Answers to the 5 open questions PQ1-PQ5

Q1. Codex CLI plugin-cache path: current docs say Codex can read repo and personal marketplace files (`$REPO_ROOT/.agents/plugins/marketplace.json`, legacy `$REPO_ROOT/.claude-plugin/marketplace.json`, `~/.agents/plugins/marketplace.json`) and installs plugins into `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/` (`https://developers.openai.com/codex/plugins/build:801-809`). The Windows equivalent should be `Path.home() / ".codex/plugins/cache/..."`; docs use `~`, not a separate Windows table. Local manual plugin folders under `~/.codex/plugins/` are examples, not installed-cache truth (`https://developers.openai.com/codex/plugins/build:721-733`).

Q2. Cursor plugin-cache path: for local plugin testing, the official Cursor plugin repo says symlink into `~/.cursor/plugins/local/agent-compatibility` (`https://github.com/cursor/plugins/tree/main/agent-compatibility:325-329`). Cursor forum guidance says Windows local plugins belong at `C:\Users\<user>\.cursor\plugins\local\<plugin-name>\`, and `plugins/cache` is internal marketplace cache, not the local testing path (`https://forum.cursor.com/t/local-plugin-is-not-being-picked-up-by-cursor/156549/3:9-12`). I found no evidence for `.cursor/extensions` as the plugin path.

Q3. Cursor sub-agent file layout: current official plugin evidence uses `.cursor-plugin/plugin.json` with `"agents": "./agents/"` and files in an `agents/` directory (`https://raw.githubusercontent.com/cursor/plugins/main/agent-compatibility/.cursor-plugin/plugin.json:0`, `https://github.com/cursor/plugins/tree/main/agent-compatibility/agents:233-248`). A sample agent file has YAML-like frontmatter with `name`, `description`, `model`, and `readonly` (`https://raw.githubusercontent.com/cursor/plugins/main/agent-compatibility/agents/startup-review.md:0`). The plan's `subagents` key and `agents-cursor/` path should be replaced unless new Cursor docs contradict this.

Q4. tiktoken Windows status: `tiktoken` 0.13.0 was released May 15, 2026 (`https://pypi.org/project/tiktoken/:23-29`) and publishes `win_amd64` wheels for CPython 3.10, 3.11, 3.12, 3.13, and 3.14 (`https://pypi.org/project/tiktoken/:397-450`). Windows x64 CI should not need Rust if binary wheels are used. The platform list does not show Windows ARM64 (`https://pypi.org/project/tiktoken/:291-295`), so fallback remains useful for non-x64 Windows or future wheel gaps.

Q5. Copilot `.agent.md` frontmatter fields: GitHub documents more than `name` and `description`: `target`, `tools`, `model`, `disable-model-invocation`, `user-invocable`, retired `infer`, `mcp-servers`, and `metadata` are in the custom agents configuration table (`https://docs.github.com/en/copilot/reference/custom-agents-configuration:536-550`). The generator should use a documented-field allow-list, not the current two-field contract.

## New plan items (if any)

- Add `traceability.md` mapping every FR-001 through FR-035, SC-001 through SC-014, A-005/A-008/A-010/A-011, and CHK001-CHK063 to specific tests or documented manual gates.
- Add `measurements.md` for SC-001 file count, SC-004 token baseline/post-fix, SC-010 check runtime, SC-012 render runtime, and SC-013 SessionStart output. The plan currently names targets but no baseline capture artifact (`specs/019-plugin-native-arch/plan.md:30-35`).
- Add R14 host manifest field-shape resolution; current Codex/Cursor schemas conflict with current docs and official examples.
- Add R15 host reload/update mechanisms for CHK056 across Claude, Codex, Cursor (`specs/019-plugin-native-arch/checklists/verification.md:119-120`).
- Add R16 legacy manifest compatibility: `schema_version`, missing `host_owner`, host inference, and strict-write/new-schema behavior.
- Add a linked-secondary writer contract and tests for both init and migrate into secondaries; current writer still bulk-copies tooling (`src/dotnet_ai_kit/copier.py:1090-1147`).
- Add cross-platform path tests for unmanaged paths, backup rotation, manifest POSIX path normalization, and linked repo relative/absolute paths.
- Add host smoke decision artifact with blocking CI semantics: Cursor fixture pass ships Cursor agents; fail forces scoped docs/contracts/spec update before merge.

## Constitution Check pushback (if any)

Specific concern: Principle V rule classification. The plan says constitution v1.0.7 allows four universal rules and FR-011 requires five (`specs/019-plugin-native-arch/plan.md:79-84`, `specs/019-plugin-native-arch/spec.md:165`). That is a real governance change. Do not bury it as an implementation detail. Either create a pre-implementation governance commit or define commit 14 as constitution amendment first, rule move second, with `test_constitution_amendment.py` failing on any mismatch. Also resolve the contradiction between "not a Complexity Tracking entry" and the actual Complexity Tracking table (`specs/019-plugin-native-arch/plan.md:83`, `specs/019-plugin-native-arch/plan.md:249`).

## Complexity Tracking pushback (if any)

The entries are not all justified as written. Cross-platform CI is under-scoped: A-010 binds migration and path semantics on all OSes, not just the four named FR rows (`specs/019-plugin-native-arch/spec.md:253`, `specs/019-plugin-native-arch/plan.md:247`). Cursor conditional scope is justified, but it must be paired with a hard CI/spec-update rule, not prose (`specs/019-plugin-native-arch/plan.md:248`). The constitution row contradicts the Constitution Check and should either stay as governance complexity or be moved to a separate amendment commit (`specs/019-plugin-native-arch/plan.md:249`). Missing complexity entries: legacy manifest compatibility, host-doc volatility for plugin cache paths, and linked-secondary writer refactor from copy functions to host adapters.

## Test inventory pushback

Missing or under-specified tests:

- FR-008/A-008: parameterize the full non-exhaustive .NET root path list across `init`, `configure`, `upgrade`, `migrate`, and `render/check` no-mutation behavior (`specs/019-plugin-native-arch/spec.md:251`).
- FR-011/FR-012/SC-004: exact 5/11 split is not enough; test JIT load triggers and prove architecture-branching/runtime-substitution rules are not always-on (`specs/019-plugin-native-arch/spec.md:165-167`).
- FR-014/FR-016: init no-host interactive prompt and selected-host-only writes need end-to-end tests, not only config schema (`specs/019-plugin-native-arch/spec.md:171-173`).
- FR-015/FR-024: plugin-host upgrade no-op and Copilot-only re-render separation need explicit tests (`specs/019-plugin-native-arch/spec.md:172`, `specs/019-plugin-native-arch/spec.md:184`).
- FR-019/SC-012: render needs success, missing name, stale/missing metadata, Claude-shape assertion, and <2s timing tests (`specs/019-plugin-native-arch/checklists/verification.md:90-95`).
- FR-020: classify all four `host_owner` values plus `null`, missing `host_owner` legacy inference, and unknown paths.
- FR-029/SC-008/A-005: Cursor fixture fail path must be tested as a blocking scope-revision state, not only smoke success (`specs/019-plugin-native-arch/spec.md:234`, `specs/019-plugin-native-arch/spec.md:248`).
- FR-031/FR-032: unique exit class tests for each broken state and actionable manifest failure output (`specs/019-plugin-native-arch/spec.md:198-204`).
- FR-033/SC-014: linked secondary init and linked secondary migrate, including user-modified preservation in a secondary (`specs/019-plugin-native-arch/checklists/verification.md:102-106`).
- FR-035: add an automated guard or static test around supported-host registry/configure UI admission, not only a code-review checklist (`specs/019-plugin-native-arch/checklists/verification.md:108-110`).
- SC-001: fixture-based before/after file count assertion.
- SC-002: two initialized solutions sharing one host plugin install; plugin asset version update observed with zero per-solution upgrade.
- SC-003: metadata rename observed by a code-generation/rule/skill runtime resolution point, not just PreToolUse.
- SC-005: Claude command/skill listing duplicate prevention.
- SC-010/SC-012: performance budget tests.
- SC-013: tokenizer path and fallback path both tested, with fallback conservative.

## Open disputes for round 2

- Cursor plugin contract: `agents` vs `subagents`, `agents/` vs `agents-cursor/`, and exact fixture layout.
- Codex manifest schema: scalar path fields and `./` prefixes vs current object/array schemas.
- Hook schema: event-keyed object vs draft six-entry array.
- Manifest schema: `schema_version`, legacy read behavior, and `host_owner` migration.
- Constitution amendment sequencing and whether it is a complexity entry.
- Cross-platform CI scope beyond FR-017/018/029/030.
- Linked-secondary writer refactor through host adapters.
- Whether plan-phase sign-off is blocked until R4/R7 are fully resolved.
