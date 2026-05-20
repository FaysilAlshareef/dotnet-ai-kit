DISAGREE-COUNTER-LIST

Round 3 final verification is not clean. Most conceded corrections landed, but the Cursor `agents/` correction is still inconsistent in the applied plan/data-model/contracts, and the plan has one stale contracts count.

## Blocking Issues

1. `plan.md` commit 2 still packages the deleted `agents-cursor/` directory and does not mention `agents-source/`. This contradicts the round-3 correction that source bodies move to `agents-source/` and Cursor build output is `agents/`. See `specs/019-plugin-native-arch/plan.md:375`.

2. `plan.md` commit 3 acceptance still says the Cursor manifest has `rules`/`subagents` references. The corrected manifest field is `agents` with `"./agents/"`, as reflected elsewhere in the data model. See `specs/019-plugin-native-arch/plan.md:389` versus `specs/019-plugin-native-arch/data-model.md:49` and `specs/019-plugin-native-arch/data-model.md:60`.

3. `plan.md` commit 6 still places the spike fixture in `agents-cursor/<one-fixture>.md`. It should be `agents/<one-fixture>.md`, matching the Cursor manifest's `./agents/` path and the new source/build split. See `specs/019-plugin-native-arch/plan.md:411`.

4. `data-model.md` section 7 still labels the source-of-truth agent definition as `agents/<name>.md`. Later in the same file the corrected map says `agents-source/<name>.md` is source-of-truth and `agents/<name>.md` is Cursor build output. See `specs/019-plugin-native-arch/data-model.md:135` versus `specs/019-plugin-native-arch/data-model.md:288` and `specs/019-plugin-native-arch/data-model.md:290`.

5. `cursor-fixture-decision.contract.md` fail-path step 7 still names legacy `agents-cursor/`. It should refer only to the corrected Cursor output directory behavior, not the deleted old path. See `specs/019-plugin-native-arch/contracts/cursor-fixture-decision.contract.md:48`.

6. `plan.md` says the contracts folder has 17 files after round-3 expansion, but the applied contracts folder has 18 files: 7 schemas and 11 markdown contracts. See stale count at `specs/019-plugin-native-arch/plan.md:101`.

## Verified Landed

- Hook event names are corrected to `SessionStart`, `PreToolUse`, and `PostToolUse` in the data model and schema. See `specs/019-plugin-native-arch/data-model.md:203` and `specs/019-plugin-native-arch/contracts/hooks-json.schema.json:14`.
- Quickstart install commands removed the noncanonical `codex plugin install` path and document Codex `/plugins`, Cursor `/add-plugin`, and Cursor local symlink. See `specs/019-plugin-native-arch/quickstart.md:32`, `specs/019-plugin-native-arch/quickstart.md:39`, `specs/019-plugin-native-arch/quickstart.md:52`, and `specs/019-plugin-native-arch/quickstart.md:58`.
- Commit 11/12 explicit tests landed for CHK011 and `.mcp.json` `csharp-ls` removal while retaining `codebase-memory-mcp`. See `specs/019-plugin-native-arch/plan.md:459` and `specs/019-plugin-native-arch/plan.md:468`.
- `agent-source.contract.md` correctly says frontmatter is structured fields and the markdown body is the document body after closing `---`. See `specs/019-plugin-native-arch/contracts/agent-source.contract.md:12` and `specs/019-plugin-native-arch/contracts/agent-source.contract.md:49`.
- Research R7/R8/R14/R15/R16 landed with corrected host paths, tighter `tiktoken>=0.13.0`, and per-host manifest field shapes. See `specs/019-plugin-native-arch/research.md:83`, `specs/019-plugin-native-arch/research.md:114`, `specs/019-plugin-native-arch/research.md:198`, `specs/019-plugin-native-arch/research.md:210`, and `specs/019-plugin-native-arch/research.md:227`.

Plan-phase debate should remain open until the six stale references above are corrected.
