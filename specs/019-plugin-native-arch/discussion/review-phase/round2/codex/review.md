# Round-2 Codex Cross-Review - Feature 019 Plugin-Native Architecture

**Branch/commit reviewed**: `019-plugin-native-arch` at `93dcfee`.

**Review stance**: independent pass first, then comparison against Claude's
round-2 review. Claude's review was for `cd71d95`; this review treats the
user-requested `93dcfee` checkout as binding.

**Severity rubric**:

- **B / Blocker**: violates a binding FR/contract or likely prevents a host path
  from working correctly in v1.0.
- **H / High**: real defect or cross-platform/spec risk that should be fixed
  before tag unless explicitly accepted.
- **M / Medium**: drift, test gap, or maintainability issue that should be
  tracked but does not block the current runtime path by itself.
- **L / Low**: hygiene only.

**Verification note**: I attempted the requested Python audit commands, but this
workspace does not expose `python` on PATH. Each command failed before entering
repo code with `python : The term 'python' is not recognized`. Commands
attempted: `python scripts/check.py --cov=dotnet_ai_kit --cov-fail-under=83 -q`,
`python scripts/doc_lint.py`, `python scripts/quality_scan.py`, and
`python scripts/quality_scan2.py`. I therefore relied on static audits,
PowerShell inventory checks, and primary-source web verification for this pass.

---

## 1. Independent Findings

### B-CX-1 - `dotnet-ai check` can report an empty host plugin directory as installed

`FR-017` says the validation command must confirm "the plugin manifest is
present at the expected path" via filesystem inspection
(`specs/019-plugin-native-arch/spec.md:174`). The clarification is equally
explicit: `dotnet-ai check` confirms the host plugin manifest is present
(`specs/019-plugin-native-arch/spec.md:28`).

The three plugin hosts do not check for any manifest file:

- Claude marks the marketplace install present when a
  `<marketplace>/dotnet-ai-kit` directory exists, and marks the local install
  present when the local directory exists (`src/dotnet_ai_kit/hosts/claude.py:50-67`).
- Codex does the same directory-only test (`src/dotnet_ai_kit/hosts/codex.py:40-52`).
- Cursor does the same directory-only test (`src/dotnet_ai_kit/hosts/cursor.py:42-54`).

That creates a false positive: an empty `~/.claude/plugins/local/dotnet-ai-kit/`
or cache directory passes `verify_install()` even when `.claude-plugin/plugin.json`
is missing. The base class wording also describes "expected paths" only, not
manifest files (`src/dotnet_ai_kit/hosts/base.py:24-31`), which appears to be
the implementation model that caused the miss.

Existing tests verify read-only/no-shell-out behavior, not manifest presence.
`test_check_does_not_shell_out_for_plugin_install` only asserts no host CLI
subprocesses were invoked (`tests/unit/test_check_filesystem_inspection.py:40-62`).
The manifest-path contract test validates declared repo paths point to disk, but
does not exercise installed host-cache layouts
(`tests/contract/test_plugin_manifest_paths.py:35-80`).

**Required fix**: for each plugin host, treat installed as true only if the
host-specific plugin manifest exists at the installed plugin root:

- Claude: `.claude-plugin/plugin.json`
- Codex: `.codex-plugin/plugin.json`
- Cursor: `.cursor-plugin/plugin.json`

Add negative tests for empty local/cache directories and positive tests for the
manifest file at the expected location.

### B-CX-2 - `dotnet-ai check --host codex|cursor|copilot` still fails on `csharp-ls`

The check contract says `--host <host>` scopes validation to a single host
(`specs/019-plugin-native-arch/contracts/check-cli.contract.md:16-20`). The same
contract says external binary failure applies when "a configured host depends on
it" (`specs/019-plugin-native-arch/contracts/check-cli.contract.md:24-29`).

The implementation computes the host scope correctly
(`src/dotnet_ai_kit/cli.py:3094-3110`), then unconditionally checks `csharp-ls`
after the per-host loop (`src/dotnet_ai_kit/cli.py:3145-3154`). That means a
Codex-only, Cursor-only, or Copilot-only check can exit 11 because a Claude LSP
dependency is absent. This contradicts the scoped CLI contract and blocks
non-Claude users from getting a clean validation result.

The current host-scope test only asserts Codex/Cursor plugin-install checks are
absent under `--host claude`; it does not assert irrelevant binary checks are
suppressed (`tests/unit/test_check_cli_flags.py:36-45`).

**Required fix**: gate `csharp_ls_binary` on the selected/configured hosts that
actually depend on the Claude `csharp-lsp` plugin. At minimum, only run it when
`"claude"` is in `host_names`; if LSP dependencies become host-configurable,
derive this from the manifest/dependency model instead of hard-coding the host.
Add tests for `--host codex`, `--host cursor`, and `--host copilot` with
`shutil.which("csharp-ls") -> None`.

### B-CX-3 - `init` silently selects hosts in non-TTY/JSON mode despite FR-014's no-silent-default rule

`FR-014` requires `init` to launch the interactive host-selection prompt when
there is no explicit host selection and says it "MUST NOT default to writing
files for all supported hosts silently" (`specs/019-plugin-native-arch/spec.md:171`).
The clarification says absence of a host flag triggers the interactive prompt,
not a silent default (`specs/019-plugin-native-arch/spec.md:29`).

The implementation only prompts when stdin is a TTY. In JSON mode or any
non-TTY context, it silently picks auto-detected tools or falls back to Claude
(`src/dotnet_ai_kit/cli.py:873-891`). The tests encode that contradictory
behavior as expected: the test module says JSON/non-TTY "MUST skip the prompt"
(`tests/unit/test_init_interactive_prompt.py:1-7`) and asserts exit 0 for both
cases (`tests/unit/test_init_interactive_prompt.py:81-107`).

This is not only a wording mismatch. In CI/scripts, `dotnet-ai init . --json`
without `--ai` can write Claude-specific configuration without explicit user
selection. That is exactly the silent host-write class FR-014 tried to remove.

**Required fix**: in non-interactive mode with no explicit host selection, fail
with an actionable error that requires `--ai <host>`/host selection. Keep JSON
machine-readable, but do not pick Claude by default. Update the contradictory
tests.

### B-CX-4 - Claude `lspServers.csharp-lsp` is not a valid LSP server config

The manifest currently declares a `lspServers` object whose `csharp-lsp` entry
only contains `_note` (`.claude-plugin/plugin.json:181-184`). The repo schema
permits that by allowing `csharp-lsp` to be any object with no required
properties (`schemas/claude-plugin.schema.json:46-55`). The contract test only
checks that the field exists (`tests/contract/test_claude_plugin_schema.py:61-63`)
and that the dependency name exists (`tests/contract/test_mcp_csharp_removed.py:50-72`).

Claude's current plugin docs contradict this shape. Inline LSP config examples
contain a server object with `command` and `extensionToLanguage`, and the docs
list those two fields as required. The repo's `_note` object supplies neither.

This is stronger than Claude's H-5 uncertainty. The primary docs make the
current manifest shape invalid or at least non-functional. If `csharp-lsp` is
intended to be an external Claude marketplace dependency, then the repo should
not also declare an inline `lspServers.csharp-lsp` object. If the repo intends
to configure the LSP inline, it needs the required fields.

**Required fix**: choose one of two valid models:

1. Remove the inline `lspServers.csharp-lsp` block and rely on
   `dependencies: ["csharp-lsp"]` if Claude's marketplace dependency is the
   intended integration.
2. Replace `_note` with a real server config, for example `command:
   "csharp-ls"` and an extension map for `.cs`, if this plugin owns the LSP
   config directly.

Either way, tighten `schemas/claude-plugin.schema.json` and add a contract test
that rejects `_note`-only LSP configs.

### H-CX-5 - MCP minimum version has two sources of truth

`.mcp.json` declares `dotnet_ai_kit_min_version: "0.6.1"`
(`.mcp.json:3-7`). `mcp_check.py` says that field is documentation-only
(`src/dotnet_ai_kit/mcp_check.py:1-8`) and enforces a separate constant
(`src/dotnet_ai_kit/mcp_check.py:18`), parsed through `_min_tuple()`
(`src/dotnet_ai_kit/mcp_check.py:39-42`).

That is a real drift vector. `tests/contract/test_mcp_csharp_removed.py` pins
the JSON field to `"0.6.1"` (`tests/contract/test_mcp_csharp_removed.py:42-47`),
but no test proves the runtime constant and JSON field remain equal. If one
changes, the host-facing config and actual check disagree.

**Recommended fix**: either remove the JSON field from the runtime host config
and document the minimum in repo docs only, or read the minimum version from
`.mcp.json` in `mcp_check.py` and test that path.

### M-CX-6 - Copilot `verify_install()` checks the process cwd, not the target project

`dotnet-ai check` accepts a `target` path and passes that target through the
main validation flow (`src/dotnet_ai_kit/cli.py:3098-3105`). `CopilotHost`
cannot use it because `Host.verify_install()` accepts no project root
(`src/dotnet_ai_kit/hosts/base.py:73-79`), so Copilot checks
`Path.cwd() / ".github"` (`src/dotnet_ai_kit/hosts/copilot.py:73-87`).

The test locks in cwd-based behavior by changing the process cwd before calling
`CopilotHost().verify_install()` (`tests/contract/test_copilot_instructions.py:93-110`).
For `dotnet-ai check C:\some\project --host copilot` invoked from a different
directory, the install-status line can describe the wrong repository. Later
freshness checks may use the target path, but this install status remains
misleading.

**Recommended fix**: change `verify_install()` to accept `project_root` or add a
separate Copilot project-status method used by `check`.

### M-CX-7 - Manifest path tests are one-way and miss orphan generated artifacts

`tests/contract/test_plugin_manifest_paths.py` validates that manifest entries
resolve to existing files/directories (`tests/contract/test_plugin_manifest_paths.py:35-80`).
It never checks the reverse: every generated/plugin-served artifact on disk is
declared by the appropriate manifest, or explicitly exempted.

The current tree demonstrates the gap. `.claude-plugin/plugin.json` lists 13
Claude agents (`.claude-plugin/plugin.json:5-18`), while `agents-claude/` has 14
Markdown files; `dotnet-ai-architect.md` is present on disk but not listed in
the Claude manifest. `agents-source/dotnet-ai-architect.md` describes itself as
the Cursor spike fixture (`agents-source/dotnet-ai-architect.md:14-19`), and the
Cursor output contains it (`agents/dotnet-ai-architect.md:1-15`).

This is not a runtime blocker by itself because the Claude manifest will load
only the 13 declared files, but it is an audit drift class and should be tested.

**Recommended fix**: add reverse inventory tests for:

- manifest-declared agents vs `agents-claude/*.md`
- source-agent names vs generated Cursor/Claude outputs, with an explicit
  allow-list for source-only or host-only fixtures
- `rules/conventions|domain/*.md` vs generated `rules/cursor/*.mdc`

### L-CX-8 - Stale placeholder files remain in populated plugin directories

The repo still contains `.gitkeep` placeholders in populated directories such
as `agents-claude/`, `agents-source/`, `agents-copilot-templates/`,
`rules/conventions/`, `rules/domain/`, `schemas/`, `.codex-plugin/`, and
`.cursor-plugin/`. The packaging config force-includes those directories
(`pyproject.toml:81-86`), so the placeholders are likely shipped.

This is hygiene, not a blocker. It only becomes functional if a host rejects
extra files in a special directory. Codex's docs do say "Only plugin.json
belongs in .codex-plugin/", which makes `.codex-plugin/.gitkeep` more relevant
than the `agents-claude/.gitkeep` singled out by Claude, but I did not observe a
testable runtime failure here.

**Recommended fix**: remove stale placeholders in populated plugin-control
directories, especially `.codex-plugin/.gitkeep`.

---

## 2. Agreements With Claude's B/H Findings

### Confirmed fact, downgraded severity: Claude B-1 orphan agent

I confirm the underlying inventory: `.claude-plugin/plugin.json` lists 13
Claude agents (`.claude-plugin/plugin.json:5-18`), while `agents-claude/` has a
14th `dotnet-ai-architect.md` generated artifact. The source file says it is
the Cursor spike fixture (`agents-source/dotnet-ai-architect.md:14-19`).

I do not agree it is a v1 blocker. The Claude manifest is explicit and excludes
the fixture, so Claude's runtime surface is still 13 declared agents. This is a
reverse-inventory test gap, not a broken host path.

### Confirmed and strengthened: Claude H-5 LSP `_note`

I confirm `lspServers.csharp-lsp` is `_note`-only
(`.claude-plugin/plugin.json:181-184`) and the repo schema permits that
(`schemas/claude-plugin.schema.json:46-55`). Primary Claude docs show LSP server
configs require `command` and `extensionToLanguage`. I therefore raise this
from High to Blocker as B-CX-4.

### Confirmed: Claude H-6 MCP minimum version drift

I confirm `.mcp.json` contains `dotnet_ai_kit_min_version`
(`.mcp.json:3-7`) and runtime enforcement comes from the independent constant in
`mcp_check.py` (`src/dotnet_ai_kit/mcp_check.py:18`). This is a real drift risk.

### Confirmed in narrow form: Claude H-2 missing skill-agent enforcement

The data model intentionally allows `metadata.agent` to be omitted for
cross-cutting skills (`specs/019-plugin-native-arch/data-model.md:321-331`).
The high-value issue is not that six skills omit `metadata.agent`; it is that
there is no contract test for the documented exemption list. I agree with the
test recommendation, not with treating the omissions themselves as defects.

### Confirmed: Claude H-11 Bash-only hook portability risk

`hooks/hooks.json` invokes only `.sh` scripts (`hooks/hooks.json:7-9`,
`hooks/hooks.json:18-20`, `hooks/hooks.json:27-29`,
`hooks/hooks.json:37-39`, `hooks/hooks.json:48-55`,
`hooks/hooks.json:63-65`). Tests acknowledge Windows needs Git Bash or WSL
(`tests/unit/test_pretooluse_arch_profile.py:23-40`,
`tests/unit/test_pretooluse_arch_profile.py:74`). Since A-010 makes Windows,
macOS, and Linux binding (`specs/019-plugin-native-arch/spec.md:253`), this is
a legitimate High unless top-level docs make the Git Bash prerequisite explicit.

---

## 3. Disagreements With Claude's B/H Findings

### Disagree with B-2 as a blocker

`agents-claude/.gitkeep` is stale, but stale placeholders also exist in
`.codex-plugin/`, `.cursor-plugin/`, `agents-source/`,
`agents-copilot-templates/`, `rules/conventions/`, `rules/domain/`, and
`schemas/`. Singling out `agents-claude/.gitkeep` as a blocker is inconsistent.

The only placeholder with a plausible host-spec angle is `.codex-plugin/.gitkeep`,
because Codex docs say only `plugin.json` belongs in `.codex-plugin/`. Even
there, I would call it Low/Medium without a loader failure. B-2 should not block
v1.0.

### Disagree with B-3 for Claude; only Cursor copy is stale

Claude says `.claude-plugin/plugin.json::description` claiming "13 specialist
agents" is a blocker. That description is accurate for the Claude manifest,
which declares 13 agents (`.claude-plugin/plugin.json:4-18`). The extra
`dotnet-ai-architect.md` is not loaded by Claude because it is not in the
manifest.

The Cursor description is stale: `.cursor-plugin/plugin.json` says "13
sub-agents" while its manifest points at `./agents/`
(`.cursor-plugin/plugin.json:4-7`), and that directory contains 14 generated
agent files. That is copy drift, not a release blocker.

### Disagree with B-4 as phrased

Claude labels `cli.py` size as a Blocker, then recommends deferring it to v1.1.
That is internally inconsistent. A blocker cannot be "ship as-is, refactor
later."

I agree `cli.py` is too large and makes bugs easier to hide. I found two actual
blockers inside it: unconditional `csharp-ls` checks
(`src/dotnet_ai_kit/cli.py:3145-3154`) and silent init defaults
(`src/dotnet_ai_kit/cli.py:873-891`). Those should be fixed surgically for
v1.0. The file split is v1.1 engineering debt.

### Disagree with H-1

Claude treats missing Cursor `model`/`readonly` fields on 13 specialists as
High. The generator explicitly documents that sources without
`host_overrides.cursor` emit only `{name, description}` and says Cursor
`model`/`readonly` are optional (`src/dotnet_ai_kit/agent_generators.py:210-225`).
The unit test asserts the same minimal output is valid
(`tests/unit/test_agent_generators.py:253-265`).

This may be a policy decision, but it is not a defect against the local
contract. If the team wants explicit Cursor routing, add it deliberately and
test the exact model values. Do not call inherited defaults a High bug while
the generator and tests declare them intentional.

### Disagree with H-7

Profiles and rules are different axes. Profiles are architecture/runtime
classifications (`generic` vs `microservice`) preserved by clarification
(`specs/019-plugin-native-arch/spec.md:26`). Rules are activation-policy
classifications (`conventions` always-loaded vs `domain` path-scoped), and the
Cursor renderer maps those to `alwaysApply`/`globs`
(`src/dotnet_ai_kit/render.py:266-315`).

Forcing profiles into the rules taxonomy would reduce clarity. The fix is a
short documentation note connecting the axes, not reclassification and not High
severity.

### Disagree with H-10

`render_cursor_rule_mdc()` is a build-time renderer for generating Cursor `.mdc`
files (`src/dotnet_ai_kit/render.py:266-291`). The user-facing `dotnet-ai render`
contract explicitly says v1 supports Claude-shaped output only and rejects
Cursor/Codex/Copilot with exit 20
(`specs/019-plugin-native-arch/contracts/render-cli.contract.md:20-39`). The CLI
implementation matches that (`src/dotnet_ai_kit/cli.py:2691-2733`), and
`render.py` encodes the same v1 host set (`src/dotnet_ai_kit/render.py:47-60`).

This is not an H-level UX gap. Exposing Cursor rule rendering would be a new
maintenance command, not a contract correction.

---

## 4. Misses Caught

Claude's pass spent blocker budget on audit hygiene, but missed three functional
contract violations:

1. **B-CX-1**: plugin install verification does not verify manifests despite
   FR-017 requiring manifest presence (`specs/019-plugin-native-arch/spec.md:174`;
   `src/dotnet_ai_kit/hosts/claude.py:50-67`;
   `src/dotnet_ai_kit/hosts/codex.py:40-52`;
   `src/dotnet_ai_kit/hosts/cursor.py:42-54`).
2. **B-CX-2**: `check --host` still runs the Claude-only `csharp-ls` prerequisite
   for non-Claude host scopes (`specs/019-plugin-native-arch/contracts/check-cli.contract.md:20-29`;
   `src/dotnet_ai_kit/cli.py:3094-3154`).
3. **B-CX-3**: non-interactive `init` silently defaults to detected/Claude
   despite FR-014's host-selection requirement (`specs/019-plugin-native-arch/spec.md:171`;
   `src/dotnet_ai_kit/cli.py:873-891`;
   `tests/unit/test_init_interactive_prompt.py:81-107`).

I also caught **M-CX-6**, the Copilot cwd/target mismatch
(`src/dotnet_ai_kit/hosts/copilot.py:73-87`), which Claude did not identify.

Finally, Claude marked `lspServers._note` as unresolved uncertainty. Primary
Claude docs resolve it: this is not merely "documentation-only"; it is the wrong
shape for an inline LSP server config.

---

## 5. Answers to Claude Appendix C Open Questions

1. **B-1 - Cursor-only or dual-purpose spike fixture?**

   Binding v1 behavior is Cursor-only for the fixture. Evidence: the source
   body says Cursor spike fixture (`agents-source/dotnet-ai-architect.md:14-19`)
   and the Claude manifest intentionally lists 13 agents, not this file
   (`.claude-plugin/plugin.json:5-18`). Do not add it to the Claude manifest
   unless the body is rewritten as a real Claude agent. Better v1 fix: prevent
   the Claude generator/build output from emitting this one file, or add an
   explicit manifest-orphan allow-list for this fixture.

2. **B-4 - `cli.py` refactor: v1.1 or v1.0 blocker?**

   v1.1. The file size is risk, not a blocker. The blocker work is fixing the
   concrete behavioral defects in `cli.py`: non-scoped `csharp-ls` checks
   (`src/dotnet_ai_kit/cli.py:3145-3154`) and silent non-interactive init
   defaults (`src/dotnet_ai_kit/cli.py:873-891`).

3. **H-1 - What Cursor model defaults should the 13 specialists use?**

   Do not mass-set `claude-sonnet-4`. The verified Cursor fixture in the Cursor
   plugin repo uses `model: fast`, and public docs/forum examples show
   `model: inherit` as a valid style. If explicit fields are required, use
   `model: inherit` as the conservative baseline, then override only agents with
   clear cost/quality needs. `readonly` should be per-agent behavior, not a
   blanket value.

4. **H-5/H-6 - Policy for documentation-only fields?**

   Runtime host manifests/configs should not contain documentation-only fields
   unless the host spec explicitly supports extension metadata. `_note` belongs
   in docs or tests, not in `.claude-plugin/plugin.json`. For `.mcp.json`, either
   make `dotnet_ai_kit_min_version` the actual runtime source of truth or remove
   it from host-facing config and document the minimum elsewhere.

5. **H-7 - Should profiles use the conventions/domain split?**

   No. Profiles model architecture (`generic`/`microservice`); rules model
   activation policy (`conventions`/`domain`). The axes are fundamentally
   different. Add a mapping note if needed.

6. **H-10 - Expose `render_cursor_rule_mdc` via CLI?**

   Not in v1. The render contract explicitly says Claude output only and exit 20
   for Cursor (`specs/019-plugin-native-arch/contracts/render-cli.contract.md:20-39`).
   Keep `render_cursor_rule_mdc` as a build-time helper unless v1.1 adds
   host-shaped render support.

7. **M-2/M-4/11.1 - Unified drift test or split tests?**

   Use one contract-test file for inventory drift, but split test cases by
   artifact class. A single file can share helpers and still produce clear
   failures:

   - `test_no_orphan_manifest_artifacts`
   - `test_generated_agents_match_sources`
   - `test_cursor_rules_match_renderer`

   Avoid one mega-assertion that reports "drift" without telling maintainers
   which generation path broke.

---

## 6. Internet Research Summary

### Cursor sub-agent specs

URL: https://cursor.com/changelog/2-4

Snippet verified: Cursor says subagents are "independent agents" and can be
configured with "custom prompts, tool access, and models" (lines 216-223).

URL: https://github.com/cursor/plugins/blob/main/agent-compatibility/agents/startup-review.md

Snippet verified: the official Cursor plugin fixture shows frontmatter fields
`name`, `description`, `model`, and `readonly` (lines 235-238).

Impact on codebase: confirms the repo's Cursor allow-list
`{name, description, model, readonly}` (`src/dotnet_ai_kit/agent_generators.py:102`).
It does not prove every agent must set `model` and `readonly`; the repo's
minimal-output test remains defensible (`tests/unit/test_agent_generators.py:253-265`).

### Claude Code plugin manifest schema and LSP

URL: https://code.claude.com/docs/en/plugins-reference

Snippet verified: Claude lists `lspServers` as a component path/config field
(lines 422-430), and its LSP section lists `command` and `extensionToLanguage`
as required fields (lines 270-273).

Impact on codebase: contradicts `.claude-plugin/plugin.json:181-184`, whose
`csharp-lsp` object contains only `_note`. The repo schema is too loose
(`schemas/claude-plugin.schema.json:46-55`).

### Codex CLI plugin manifest

URL: https://developers.openai.com/codex/plugins/build

Snippet verified: Codex says every plugin has `.codex-plugin/plugin.json` and
"Only plugin.json belongs in .codex-plugin/" (lines 811-836). It also says
manifest paths should start with `./` (lines 896-899).

Impact on codebase: supports `.codex-plugin/plugin.json` using scalar
`"./skills/"`, `"./.mcp.json"`, and `"./hooks/hooks.json"`
(`.codex-plugin/plugin.json:5-7`; `schemas/codex-plugin.schema.json:17-33`).
It also makes `.codex-plugin/.gitkeep` a real hygiene issue when that directory
is packaged (`pyproject.toml:81-82`).

### MCP server transport spec

URL: https://modelcontextprotocol.io/specification/2025-06-18/basic/transports

Snippet verified: MCP defines two standard transports, `stdio` and Streamable
HTTP (lines 79-83). In stdio, the client launches the server as a subprocess
and JSON-RPC flows over stdin/stdout (lines 88-95).

Impact on codebase: supports `.mcp.json` using `"transport": "stdio"`
(`.mcp.json:3-7`) as a host/client config hint. It does not support adding
arbitrary documentation fields unless the consuming host tolerates them, which
is why `dotnet_ai_kit_min_version` remains a drift/policy issue.

### csharp-ls canonical repo

URL: https://github.com/razzmatazz/csharp-language-server

Snippet verified: csharp-ls brings C# language features to editors (lines
280-284), and the install command is `dotnet tool install --global csharp-ls`
(lines 296-304).

Impact on codebase: confirms the binary name and remediation URL used by
`dotnet-ai check` (`src/dotnet_ai_kit/cli.py:3145-3154`). It does not justify
running that prerequisite for non-Claude host scopes.

### GitHub Actions `workflow_dispatch` and matrix `if` semantics

URL: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

Snippet verified: `workflow_dispatch` can pass inputs and runs only when the
workflow file is on the default branch (lines 805-817). GitHub also says
`jobs.<job_id>.if` is evaluated before the matrix is applied (lines 1233-1239).

Impact on codebase: `.github/workflows/smoke.yml` uses a job-level `if` that
does not reference `matrix` (`.github/workflows/smoke.yml:41-53`), so the
pre-matrix evaluation is not itself a bug. The per-matrix strictness logic is
implemented as step-level env/continue-on-error expressions
(`.github/workflows/smoke.yml:113-148`), which are evaluated inside each matrix
entry. Claude's concern is directionally useful but not a blocker.

---

## Bottom Line

I would not block v1.0 on Claude's `.gitkeep`, manifest-description, or
single-file-CLI findings. I would block on the functional contract violations:

1. Host install checks must verify plugin manifests, not just directories.
2. `check --host` must not require Claude's `csharp-ls` dependency for
   non-Claude host scopes.
3. Non-interactive `init` must not silently select Claude/detected hosts without
   explicit user selection.
4. Claude LSP manifest shape must be made valid or removed in favor of the
   declared dependency.

Fix those four, then handle the orphan/generated-artifact tests and hygiene
items as release hardening rather than blocker theater.
