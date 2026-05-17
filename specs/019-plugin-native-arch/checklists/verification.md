# Verification Checklist: Plugin-Native Architecture

**Purpose**: Pre-merge verification gates for the v1.0 plugin-native architecture release
**Created**: 2026-05-17 (initial); revised after spec-phase round 2 (2026-05-17)
**Feature**: [spec.md](../spec.md)
**Source**: `issues/plugin-native-architecture/FINAL-REPORT.md` "Verification gates before merge" + the converged commit order (originally 15 commits; updated to 16 commits `1..14, 14b, 15` during tasks-phase round 1 to add a dedicated `render` commit per Codex's BLOCKER (c) verdict — see `discussion/tasks-phase/round1-codex-reply.md`) + `specs/019-plugin-native-arch/discussion/spec-phase/round2-codex-verify.md` expansion items 1-8

This checklist enumerates every gate the release MUST pass before the single PR is merged. Items are derived from the converged design and the spec-phase debate; nothing here is new policy.

FR/SC references match the revised spec (US3 removed, US6/US7 split → US5/US6, FR-034-FR-037 renumbered to FR-032-FR-035 inside spec while keeping their original conceptual identities, SC-013/SC-014 added). **FR-030 (packaging test) IS present in the current spec at `spec.md:198-199`** — earlier preamble drafts incorrectly stated FR-030 was removed; the canonical post-spec-phase numbering retains FR-030 as the packaging-test requirement (CHK005-CHK008 below map to FR-030 per spec). The mapping below corresponds to the spec at `../spec.md` after spec-phase round-2 edits.

## Host smoke fixtures (spec FR-029, SC-008)

Each host with a plugin model must demonstrably load an asset from the packaged plugin source. The fixtures are minimal artifacts whose only purpose is to prove the loader pathway works end-to-end on a freshly installed plugin.

- [ ] CHK001 Claude Code smoke fixture: a Claude-native custom agent is committed to the source repository and listed in the Claude Code plugin manifest. After installing the plugin, Claude Code's `/agents` listing includes the fixture under the plugin namespace.
- [ ] CHK002 Codex CLI smoke fixture: a Codex-format skill is committed to the source repository inside the Codex plugin source directory. After installing the plugin in Codex CLI, the skill is visible to Codex CLI's skill enumeration.
- [ ] CHK003 Cursor smoke fixture: a Cursor sub-agent definition is committed to the source repository per Cursor's packaging format. After installing the plugin in Cursor, Cursor lists the sub-agent.
- [ ] CHK004 Cursor sub-agent spike decision recorded: the outcome of CHK003 is captured in `issues/plugin-native-architecture/FINAL-REPORT.md`. Per A-005 / SC-008 / OOS-005, the fixture itself is mandatory; if it fails, full Cursor sub-agent generation is removed from this release's scope and the release is revised to reflect that scope reduction.

## Packaging tests (spec FR-030, SC-009)

The distribution package must include every host-specific plugin manifest such that a package-based install yields a working plugin install for every supported plugin host.

- [ ] CHK005 Distribution package build succeeds without errors.
- [ ] CHK006 A freshly built distribution package, installed into an isolated environment, contains all three host-specific plugin manifest directories at the installed location (one per supported plugin host).
- [ ] CHK007 The plugin manifest files inside the installed package are byte-identical to the source-repository versions.
- [ ] CHK008 An automated test exercises CHK005–CHK007 in continuous integration on a clean environment.

## C# language-intelligence migration gate (spec FR-028, SC-011)

The migration of C# diagnostics and navigation from a model-context-protocol entry to a language-server primitive is staged. The MCP removal is the LAST step and is explicitly gated.

- [ ] CHK009 The validation command's language-server binary check is implemented and exits non-zero when the C# language-server binary is absent from the developer's search path.
- [ ] CHK010 The C# language-server primitive is declared as a plugin dependency in the Claude Code plugin manifest.
- [ ] CHK011 An end-to-end check confirms the plugin host loads the language-server dependency and exposes C# diagnostics at edit time (not only via explicit AI tool invocation).
- [ ] CHK012 The old C# model-context-protocol entry is removed from the plugin's MCP configuration ONLY after CHK009, CHK010, and CHK011 have passed in CI. If any of those gate checks fail or are skipped, this step is not performed and the release does not ship the removal in this PR.

## Project metadata schema validation (spec FR-017, SC-010)

- [ ] CHK013 A schema for the per-solution project metadata file exists in the plugin source.
- [ ] CHK014 The validation command runs the schema check against the project metadata file and exits non-zero on schema violations.
- [ ] CHK015 The validation command reports detected-path discrepancies (i.e., paths declared in project metadata that no longer exist on disk).

## Copilot render freshness (US2, spec FR-017, SC-006)

- [ ] CHK016 The validation command identifies rendered Copilot files whose content was generated from an older plugin source version than the currently installed plugin.
- [ ] CHK017 The Copilot-targeted upgrade variant re-renders all Copilot files using the current plugin source and current project metadata.
- [ ] CHK018 A test confirms that after a project metadata change followed by the Copilot-targeted upgrade variant, the rendered files contain the updated values.
- [ ] CHK019 Copilot output structurally contains the three logical content classes (repository-wide instructions, path-scoped instructions, per-agent custom-agent files) at the Copilot-native paths.

## Migration safety (US4, spec FR-020 to FR-025, SC-007)

- [ ] CHK020 The migration command classifies every previously-managed file by content hash (against the managed-file manifest) as clean or user-modified before any move or delete.
- [ ] CHK021 The migration command moves clean files to a timestamped backup folder at the project-local path `.dotnet-ai-kit/backups/migrate/<timestamp>/` and does NOT delete clean files outright.
- [ ] CHK022 The migration command preserves user-modified files in place by default and reports them as preserved.
- [ ] CHK023 The migration command's backup folders are subject to the same 3-keep retention as existing backup retention.
- [ ] CHK024 The migration command does NOT re-render Copilot files (re-render belongs to the Copilot-targeted upgrade variant; per spec FR-024).
- [ ] CHK025 The init command with the force option detects shadowed legacy artifacts, does NOT auto-delete them, and prints the exact migration invocation for the user.
- [ ] CHK026 Paths outside the formally-managed manifest are not classified as managed, not moved to backup, and not modified by any release-introduced command. The repository-root `AGENTS.md` file is a concrete example, but the rule applies generally to every path not declared in the managed-file manifest (other common .NET examples include `.editorconfig`, `Directory.Build.props`, `Directory.Packages.props`, `global.json`, `nuget.config`, `.gitignore`, `.gitattributes`, `Dockerfile`, CI workflow files).

## Agent generation (spec FR-026, FR-027)

- [ ] CHK027 The legacy generic agent-frontmatter map is deleted from the codebase.
- [ ] CHK028 Each supported host has a per-host generation path that produces that host's agent files from the single source-of-truth agent definitions (implementation pattern of named generator functions is a plan-phase detail, not a spec contract).
- [ ] CHK029 For every supported host, a test asserts that no unsupported frontmatter field appears in that host's generated agent file.
- [ ] CHK030 A regression test asserts that the Claude Code agent generation does not introduce a skill-preload field that would cause performance regression at session start.

## Convention vs domain rule classification (spec FR-011, FR-012, FR-013, SC-004, SC-013)

- [ ] CHK031 Exactly five rules are classified as always-on conventions per spec FR-011: `async-concurrency`, `coding-style`, `existing-projects`, `security`, `tool-calls`.
- [ ] CHK032 Exactly eleven rules are classified as just-in-time domain per spec FR-011: `api-design`, `architecture`, `configuration`, `data-access`, `error-handling`, `localization`, `multi-repo`, `naming`, `observability`, `performance`, `testing`.
- [ ] CHK033 No rule with architecture-specific branches (`error-handling`) is in the always-on set.
- [ ] CHK034 No rule that requires runtime substitution of project-metadata values (`naming`) is in the always-on set.
- [ ] CHK035 The session-start orientation output is ≤500 tokens of stdout under typical project metadata, is an index (not a concatenation of rule bodies), and contains no full rule bodies. Verified by tokenizer count with character-length fallback.
- [ ] CHK036 Every always-on convention rule is referenced from the skill bodies that depend on it, using the host's plugin-root substitution variable so the path resolves at load time.

## Multi-host configure (spec FR-016)

- [ ] CHK037 The configure command's interactive flow lists all four supported AI hosts as individually selectable.
- [ ] CHK038 Selecting a subset of hosts at init writes only the files required by the selected hosts; no files appear for unselected hosts.

## Validation command coverage (US5, spec FR-017, FR-031, FR-032, SC-010, SC-011)

- [ ] CHK039 The validation command emits a single command-line invocation that produces all of the following in one run: plugin install status per configured host, external binary prerequisite status, project metadata schema status, detected-path correctness, Copilot render freshness, AND managed-file manifest integrity.
- [ ] CHK040 The validation command exits with status zero in a healthy state and with a non-zero status that uniquely identifies the failing check class in a broken state.
- [ ] CHK041 The validation command completes within 10 seconds on a developer workstation under typical conditions.
- [ ] CHK042 The managed-file manifest integrity check (per spec FR-032) verifies: manifest file readability, all expected managed paths exist, content hashes match for rendered/managed files, and the failure output is actionable (names the inconsistent file, the expected hash, the observed state, and the remediation command). Exits with a non-zero status that uniquely identifies the manifest-integrity check class.

## Render command (US6, spec FR-019, SC-012)

- [ ] CHK043 The `render` command (spec FR-019) accepts a skill name or rule name and prints the runtime-resolved content using current project metadata.
- [ ] CHK044 The `render` command's output for a parameterized skill shows substituted project-metadata values, not the unresolved tokens.
- [ ] CHK045 The `render` command's output is identified as Claude-host-shaped (v1 scope); a test confirms the output is the expected Claude-host render and that v1 does not silently produce a different host's shape.

## Runtime architecture-profile resolution (spec FR-034, US3)

- [ ] CHK046 The pre-tool-use runtime architecture-profile hook reads project metadata at fire-time, not from a frozen init-time snapshot.
- [ ] CHK047 A test confirms that a mid-session change to the architecture-profile value in project metadata is observed by the next pre-tool-use hook invocation without requiring session restart.
- [ ] CHK048 If project metadata is missing or corrupt at hook fire-time, the hook produces a clear corrective error message (naming the file and the corrective command) rather than silently degrading to a default or broad behavior.

## Linked-secondary-repository footprint (spec FR-033, SC-014)

- [ ] CHK049 The linked-secondary-repository writer code path is updated to honor plugin-native footprint, host selection, and managed-manifest ownership rules.
- [ ] CHK050 A test confirms that a primary-repository initialization with one linked secondary repository does not create legacy copied commands, rules, skills, or agents in the secondary repository for plugin-supporting hosts.
- [ ] CHK051 A test confirms that the migration command applied to a primary repository with linked secondaries also cleans up legacy copies in the secondaries (subject to the same user-modified preservation rules per spec FR-022).

## New host admission gate (spec FR-035)

- [ ] CHK052 No host can be added to the supported-host list or the configure UI unless it has all of: a documented host-native install/update path, documented artifact primitives for the assets being exposed, a passing host-specific smoke fixture, and a passing packaging test. The admission gate is enforced as a code review checklist for any PR that expands the supported-host set.

## Test contract changes

- [ ] CHK053 Tests previously asserting Claude-only multi-tool support are updated to assert the new multi-host contract.
- [ ] CHK054 The expanded supported-tools set is reflected in tests and in any host-validation logic the configure and check commands rely on.

## Documentation and migration guide

- [ ] CHK055 The migration guide explains: when to run the migration command, what it does and does not do, how it interacts with the Copilot-targeted upgrade variant, and how to reverse a migration from the project-local backup folder.
- [ ] CHK056 The release notes call out the plugin-update-mid-session edge case and the recommended reload action for each host (Claude Code's `/reload-plugins` plus the Codex CLI and Cursor host-equivalents), not only the Claude Code action.
- [ ] CHK057 The release notes call out the C# language-server binary prerequisite (per A-007) and the validation command as the recommended pre-flight.
- [ ] CHK058 The README reflects the new file footprint (only the per-solution files defined by spec FR-005, plus Copilot renders if Copilot is enabled) rather than the previous ~180-file footprint.
- [ ] CHK059 The user-facing documentation publishes the non-exhaustive list of .NET solution-root developer-owned paths that the tool will not write to (per A-008), making the FR-008 generic rule concrete for users.

## Items explicitly recorded as out-of-this-release (OOS-001 to OOS-007)

These items are NOT gates for this release. They are recorded here so reviewers do not raise them as missing.

- [ ] CHK060 The release notes explicitly state that a `bin/` launcher is deferred to v1.1 (OOS-003), with the spike result recorded in the planning folder.
- [ ] CHK061 The release notes explicitly state that native Codex CLI plugin agents are deferred to v1.1 pending Codex documentation (OOS-004).
- [ ] CHK062 If the Cursor sub-agent fixture passes (CHK003), the release notes explicitly state that full Cursor sub-agent generation is shipped. If the fixture fails, the release notes explicitly state that full Cursor sub-agent generation is deferred to v1.1 and the release was scope-revised per OOS-005 and A-005.
- [ ] CHK063 The release notes explicitly state that a multi-repository activity monitor is not included in this release (OOS-006), and clarify that plugin-served-artifact drift is solved by spec FR-033 (linked-secondary-repository footprint) plus US1 (single-host-action update propagation) — sibling-repository activity surveillance beyond that is deferred.

## Notes

- Check items off as completed: `[x]`
- Add comments or findings inline
- Link to relevant test files, CI runs, or PR review threads
- Items are numbered sequentially across categories for cross-reference
- CHK012 remains the highest-risk gate: language-server MCP removal MUST NOT ship if CHK009, CHK010, or CHK011 are unchecked. If shipping the language-server migration in this release is blocked, defer the corresponding commit to a follow-up PR rather than shipping it ungated.
- CHK046–CHK048 (runtime arch-profile), CHK049–CHK051 (linked-secondary-repository), and CHK042 (manifest integrity) are the gates that close the gaps Codex flagged in spec-phase round 1 (`discussion/spec-phase/round1-codex-reply.md` lines 87-93 and 121-123). Without these, the spec's FR-032, FR-033, FR-034, SC-013, SC-014 would be untestable.
