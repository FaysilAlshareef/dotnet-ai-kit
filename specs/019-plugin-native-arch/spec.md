# Feature Specification: Plugin-Native Architecture

**Feature Branch**: `019-plugin-native-arch`
**Created**: 2026-05-17
**Status**: v1.0.0 — Phase 10 (post-review corrections) IN PROGRESS. Phases 1-9 landed; cross-AI review-phase debate (rounds 1-4 at `discussion/review-phase/`) found **8 release-gating defects (B-1 through B-8: 4 P0 + 4 P1)** + 8 round-3 plan corrections + 12 content findings; tasks T131-T200 in `tasks.md` Phase 10 close them. Spec language unchanged — defects are implementation gaps against existing FRs. Canonical fix plan: [`discussion/review-phase/claude/final-consolidated-review.md`](./discussion/review-phase/claude/final-consolidated-review.md); round-4 verification refinements: [`discussion/review-phase/round4-codex-reply.md`](./discussion/review-phase/round4-codex-reply.md).
**Input**: User description: "now read @plugin-native-architecture issue very well and read the final reports, make your researches and write spec.md and checklist files that needed for this feature"

## Background

dotnet-ai-kit ships AI development assistance (commands, rules, skills, agents, project templates) for four AI coding tools: Claude Code, Codex CLI, Cursor, and GitHub Copilot. Three of those four hosts now expose a first-class plugin model; GitHub Copilot does not and uses repository-native instruction files instead.

The current architecture installs assistance per-solution by copying all assets (commands, rules, skills, agents) into the user's repository on `init`. This produces three structural problems users observe directly:

1. Each initialized solution holds roughly 180 generated files; the same assets are then loaded twice in Claude Code (once via the plugin host, once from the project copy), creating duplicate entries in the available-skill and available-command lists.
2. Bug fixes and improvements in the plugin source do not reach an initialized solution until the user runs an upgrade in that specific repository, producing drift across a team's sibling repositories.
3. Customization values that depend on the project (company name, domain, architecture profile, detected layer paths) are frozen at initialization and silently fall out of sync when the project is refactored or renamed.

This feature delivers a release that uses each host's native plugin model where one exists, renders native instruction files only where a plugin model does not exist, and replaces frozen project-local copies with runtime resolution against current project metadata. This release addresses plugin-served-artifact drift; multi-repository activity monitoring is deferred (see OOS-006), and the linked-secondary-repository writer is constrained by FR-035 so it cannot preserve the legacy copy architecture as a back door. The release is **pre-v1.0.0**, so there are no public users to migrate and no backward-compatibility tax.

The full architectural analysis, cross-AI debate, and converged design are captured in `issues/plugin-native-architecture/` (see `FINAL-REPORT.md` for the executive summary and the merged-findings files for the verified facts that drove every decision). The spec-phase cross-AI debate is recorded under `specs/019-plugin-native-arch/discussion/spec-phase/`.

## Clarifications

### Session 2026-05-17

- Q: V1.0 scope for architecture profiles given the codebase already validates 12 specific project_type values? → A: Preserve all 12 (command, query-sql, query-cosmos, processor, gateway, controlpanel, hybrid, vsa, clean-arch, ddd, modular-monolith, generic) + the microservice/generic branch split as validated at `src/dotnet_ai_kit/models.py:88-99`.
- Q: Is cross-platform support (Windows + macOS + Linux) a binding spec constraint or an implementation detail? → A: Binding on all three. Every functional requirement is binding on each OS; the validation command, smoke fixtures, and packaging test run in CI on Windows, macOS, and Linux.
- Q: How does `dotnet-ai check` verify "plugin install per configured host"? → A: Filesystem inspection of each host's documented plugin-cache directory; the command confirms the host's plugin manifest is present at the expected path. No shell-out to host CLIs in v1. Limitation (host-considers-plugin-disabled-but-file-on-disk) is documented as an acceptable v1 trade-off.
- Q: What is `dotnet-ai init`'s default host-selection behavior on first run? → A: Always launch the interactive host-selection prompt (the same one `configure` uses). No silent host writes. A `--host` flag MAY be supported for scripted use, but absence of the flag triggers the interactive prompt rather than a silent default.
- Q: Network and telemetry posture for the tool's own commands? → A: No outbound network calls and no telemetry from `init`, `upgrade`, `configure`, `check`, `migrate`, `render`, or any other tool command. Host plugin installation (which IS network-bound when the host fetches a plugin) is the host's responsibility, not the tool's. No analytics, no crash reporting, no auto-update check.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Plugin host users receive updates without per-repository action (Priority: P1)

A developer maintains several .NET solutions that all use the same AI host (Claude Code, Codex CLI, or Cursor). When the dotnet-ai-kit maintainer ships a fix or an improvement, the developer should be able to make the new plugin assets available to every solution that uses that host through the host's native plugin update path, without visiting each repository to run an upgrade command.

**Why this priority**: This is the central value proposition of moving to a plugin-native architecture. Without it, the refactor only changes file layout. With it, every downstream improvement reaches every user of a given host on a given machine simultaneously and predictably.

**Independent Test**: Initialize the tool in two separate .NET solutions on the same machine using the same plugin-supporting AI host. Make a change to the plugin source (for example, a skill body update). Run that host's plugin update action once. Verify both solutions exercise the new behavior on their next AI session with no per-solution upgrade command run. (Cross-host symmetry is not asserted: each host has its own update mechanism.)

**Acceptance Scenarios**:

1. **Given** the tool is initialized in two .NET solutions on the same machine using the same plugin host, **When** the maintainer publishes a plugin update and the user runs that host's native plugin update action, **Then** both solutions observe the new behavior on their next AI session.
2. **Given** a solution was initialized before a plugin update, **When** the user starts a new AI session in that solution, **Then** the available commands, skills, and agents are exactly those from the current plugin version with no stale or duplicate entries.

---

### User Story 2 - GitHub Copilot users keep structural parity with plugin host users (Priority: P1)

A developer uses GitHub Copilot, which has no plugin host. They expect the same logical content classes of project-aware assistance as plugin host users — repository-wide conventions, path-scoped domain guidance, and per-agent files — expressed through Copilot's native instruction and custom-agent files in `.github/`, with a clear way to refresh those files when the upstream tool or project metadata changes and a clear way to detect when a refresh is needed.

**Why this priority**: Co-equal with US1 because the Copilot path must not regress structurally. If the tool ships plugin-native behavior at the cost of Copilot users losing logical content classes (e.g., losing path-scoped guidance), the release is a non-starter for any team mixing tools.

**Independent Test**: Initialize the tool in a .NET solution with Copilot selected. Verify Copilot operates against rendered repository-wide, path-scoped, and per-agent files. Update the project metadata (rename a layer). Run the Copilot refresh action and verify the rendered files reflect the new metadata. Then make a change in the plugin source without running the refresh, run the validation command, and verify it reports the rendered files as stale.

**Acceptance Scenarios**:

1. **Given** a developer initializes the tool with Copilot enabled, **When** initialization completes, **Then** Copilot consumes a repository-wide instruction file, path-scoped instruction files matching the project's structure, and per-agent custom-agent files in the Copilot-native location.
2. **Given** the developer renames a layer or company value in the project metadata, **When** they run the Copilot refresh action, **Then** the rendered Copilot files reflect the new metadata.
3. **Given** the plugin source has changed since the last Copilot render, **When** the developer runs the validation command, **Then** the command reports the render as stale and recommends the refresh action.

---

### User Story 3 - Customization values resolve at the time the AI uses them (Priority: P2)

A developer can rename their company, change their domain identifier, switch architecture profiles, or refactor their folder layout, and the AI tool will reflect those changes the next time it resolves project state — at session start, at tool-use time, or at any other runtime resolution point — without the developer having to re-initialize or upgrade.

**Why this priority**: The frozen-at-init failure mode is silent — generated code looks plausible but uses outdated names or paths. Fixing it removes a class of bugs users currently cannot detect by reading their own repository. The runtime resolution covers both the session-start orientation hook and the pre-tool-use architecture-profile resolution hook; the second is required because architecture-profile choices can change mid-session through the validation command's correction path.

**Independent Test**: Initialize the tool. Rename the company value in the project metadata. Without running upgrade or re-init, start a new AI session and ask a code-generation skill to scaffold an artifact whose name depends on the company value. Verify the generated artifact uses the new name. Then refactor a layer folder name and verify the next skill invocation resolves the new path.

**Acceptance Scenarios**:

1. **Given** the tool is initialized with a project metadata value of "AcmeCorp", **When** the developer changes the metadata to "GlobexCorp" and runs a code-generation skill in a new session, **Then** the generated artifacts reference "GlobexCorp", not "AcmeCorp".
2. **Given** the developer renames a layer folder, **When** they run a skill that targets that layer, **Then** the skill resolves the new path from current project metadata rather than the path that was current at initialization time.
3. **Given** a session is already running and the developer changes the architecture profile in the project metadata, **When** the AI next invokes a tool that depends on profile-specific behavior, **Then** the pre-tool-use runtime resolution observes the new profile without requiring session restart.

---

### User Story 4 - Safe, reversible migration from the old per-solution layout (Priority: P2)

A developer with a solution initialized under the previous (per-solution copy) layout can run a single migration command that uses the managed-file manifest's content hashes to classify each previously-written file as either still-clean (matches what the tool originally wrote) or user-modified, moves the clean files into a rotated project-local backup, and leaves the modified files untouched unless they explicitly choose to remove them.

**Why this priority**: Even pre-v1.0.0, a maintainer using the tool on their own repositories will go through this path. Silent deletion would destroy user customizations. Manual cleanup would be error-prone. A reversible, manifest-driven, classified migration is the only acceptable bridge.

**Independent Test**: Initialize the tool under the old layout. Modify one of the generated files. Run the migration command. Verify the unmodified files were moved to a timestamped project-local backup folder, that the modified file is preserved in place, that the migration command reports the preservation, and that the backup folder is rotated to keep at most three.

**Acceptance Scenarios**:

1. **Given** a solution initialized under the old layout with no user modifications, **When** the developer runs the migration command, **Then** all previously-managed files (per the managed-file manifest) are moved to a timestamped project-local backup folder and the working tree is clean of duplicated artifacts.
2. **Given** a solution initialized under the old layout with one or more user-modified managed files, **When** the developer runs the migration command, **Then** the modified files are preserved in place and the command reports which files were preserved and why.
3. **Given** the migration command has been run three or more times, **When** the developer runs it again, **Then** the oldest backup folder is rotated out and only the three most recent are retained.
4. **Given** the developer runs initialization with the force option on an old-layout solution, **When** initialization detects shadowed legacy artifacts, **Then** it does not auto-delete them; it prints the exact migration command for the developer to run explicitly.

---

### User Story 5 - Validation is a single command that gates the release-relevant state (Priority: P2)

A developer can run a single validation command to confirm the tool is correctly installed for every configured host, that any external binary prerequisites are available on the developer's search path, that the project metadata file is structurally valid and consistent with the working tree, that the managed-file manifest is intact, and that any rendered files are not stale relative to the current plugin source and project metadata.

**Why this priority**: Validation centralizes a class of problems that previously hid in copy-time side effects. It is the gate for Copilot freshness, missing language-server prerequisites, project schema integrity, and manifest hash integrity — all of which can produce silent failures elsewhere. P2 because correct behavior in US1, US2, US3, US4 depends on knowing when state has drifted from expected, and only this command surfaces that.

**Independent Test**: Initialize the tool. Run the validation command in a clean state and verify it exits with status zero. Uninstall an external prerequisite the tool depends on. Run validation again and verify it reports the missing prerequisite by name with a remediation hint and exits with a non-zero status. Corrupt the managed-file manifest. Run validation and verify it reports the manifest as inconsistent and exits with a non-zero status uniquely identifying that failure class.

**Acceptance Scenarios**:

1. **Given** a correctly-initialized solution, **When** the developer runs the validation command, **Then** the command reports plugin install status per configured host, presence of external binary prerequisites, project metadata schema and detected-path correctness, Copilot render freshness, and managed-file manifest integrity, exiting with status zero.
2. **Given** an external binary prerequisite is missing from the developer's search path, **When** the developer runs the validation command, **Then** the command identifies the missing prerequisite and the host that needs it, and exits with a non-zero status that uniquely identifies the failing check class.
3. **Given** the managed-file manifest is missing or inconsistent with the working tree, **When** the developer runs the validation command, **Then** the command reports the inconsistency with actionable failure output and exits with a non-zero status that uniquely identifies the manifest-integrity check class.

---

### User Story 6 - Runtime inspection mitigates the loss of pre-rendered files (Priority: P3)

A developer can run an inspection command — `render <skill|rule>` — to print what a given skill or rule resolves to right now, using current project metadata. This restores the inspectability property users implicitly relied on under the old layout (where pre-rendered files sat in the repository and could be opened), without restoring those files on disk.

**Why this priority**: A developer affordance that mitigates one side effect of moving to runtime resolution. Not a release gate, not a precondition for any other story. P3 because the underlying behaviors in US1–US5 must be correct before this meta-command is useful.

**Independent Test**: Initialize the tool. Run `render` on a parameterized skill that references a project metadata value. Verify the output shows the fully-resolved skill body with current metadata values substituted, completes within 2 seconds, and is identifiable as the Claude-host-shaped output (v1 scope; other hosts' render shapes are deferred).

**Acceptance Scenarios**:

1. **Given** a parameterized skill that references current project metadata, **When** the developer runs `render` for that skill, **Then** the output shows the fully-resolved skill body with current metadata values substituted.
2. **Given** a rule that references project metadata, **When** the developer runs `render` for that rule, **Then** the output shows the fully-resolved rule body and is clearly identified as the Claude-host-shaped output.

---

### Edge Cases

- **Plugin updated mid-session**: The host loads plugin assets on session start. When the user updates a plugin while an AI session is active, the new behavior may not appear until the user invokes the host-equivalent plugin reload action (Claude Code's `/reload-plugins`, Codex CLI's equivalent, Cursor's equivalent) or starts a new session. The tool's documentation must call out each host's reload mechanism.
- **Project metadata missing or corrupt at runtime**: A developer can delete or corrupt the project metadata file after init. Skills, rules, the session-start orientation, and the pre-tool-use architecture-profile resolution that depend on it must degrade gracefully with a clear error message naming the missing/corrupt file and the corrective command, rather than producing silently wrong output.
- **External binary prerequisite missing when a host depends on it**: One host depends on an external binary (the C# language server) being on the developer's search path. If the binary is missing after a system reinstall, the validation command must surface this before runtime invocation of the dependent feature fails opaquely.
- **User-modified managed files during migration**: A user may have edited a file the tool previously generated. The migration command must classify such files as user-modified by content hash (against the managed-file manifest) and preserve them, even if the user originally intended them as throwaway. The default is preservation; explicit user action is required to remove.
- **Experimental host capability with undocumented loader (Cursor sub-agents)**: One host's documentation announces support for a packaging primitive but does not yet describe how its loader consumes packaged definitions. The release ships a single fixture for that host and gates the full rollout on the fixture loading cleanly. The fixture itself is mandatory; if it does not load, full support for that capability is deferred to the next release and the spec is revised to reflect that scope reduction — the release must not quietly ship a failed capability as "supported."
- **Repository file collision with developer-owned paths**: The release writes to host-native locations only. Any repository path outside the formally-managed manifest is treated as user-owned and must not be written, modified, migrated, or deleted by any tool command unless the user explicitly opts in to that exact path. This applies to root files commonly authored by .NET developers (a non-exhaustive list documented in user-facing material), not only to the AGENTS.md example.
- **Shared asset format with field divergence between hosts**: The tool emits per-host outputs from a single source-of-truth definition. The generated output must not contain fields unsupported by the target host, and verification must lock this in per host.
- **Linked secondary repositories (new edge case)**: A primary repository can deploy tooling into linked secondary repositories. After this release, the secondary-repository writer must honor the same plugin-native footprint, host selection, and managed-manifest ownership rules as primary-repository initialization. It must not preserve the old per-solution copy architecture for plugin-supporting hosts via the secondary-repository path (see FR-035 and SC-014).

## Requirements *(mandatory)*

### Functional Requirements

#### Plugin packaging and host coverage

- **FR-001**: The tool MUST ship installable plugin packages for the three AI hosts with first-class plugin models (Claude Code, Codex CLI, Cursor). Each package MUST be installable through its host's native installation path. Individual capabilities inside each package MUST be gated by the host's documented primitives and the corresponding host-specific smoke fixture.
- **FR-002**: Each host-specific plugin package MUST declare only the primitives that the host's documentation supports. Capabilities not documented for a host MUST NOT be exposed in that host's manifest.
- **FR-003**: The tool's distribution package MUST include every host-specific plugin manifest such that installing the distribution package makes a working plugin install available for every supported plugin host. After installation, no further project-local copying of commands, rules, skills, or agents for plugin-supporting hosts is required to make those assets usable.
- **FR-004**: The tool MUST support GitHub Copilot through repository-native instruction and custom-agent files (no plugin model), rendered into the user's repository at the locations Copilot consumes.

#### Per-solution footprint

- **FR-005**: For solutions using only plugin-supporting hosts, initialization MUST write only the per-solution files defined by the converged design (the project-metadata file, the user-configuration file, and a permissions-merge file for the chosen host's tool settings). It MUST NOT write any other per-solution file by default.
- **FR-006**: Initialization MUST NOT copy commands, rules, skills, or agents into the user's repository for any plugin-supporting host.
- **FR-007**: For solutions that select Copilot in addition to plugin hosts, initialization MUST additionally render three logical content classes into the user's repository at the Copilot-native paths: a repository-wide instruction file, path-scoped instruction files for the project's structural areas, and per-agent custom-agent files (one per specialist agent).
- **FR-008**: Paths outside the formally-managed manifest MUST NOT be written, modified, migrated, or deleted by any tool command unless the user explicitly opts in to that exact path. The repository-root `AGENTS.md` file is a concrete example of a developer-owned path that MUST be left untouched, but the rule generalizes to every path not declared in the managed-file manifest.

#### Runtime resolution of customization

- **FR-009**: Customization values that depend on the project (company name, domain, architecture profile, detected layer paths) MUST be resolved from current project metadata at the time the AI uses them, not frozen into copied files at initialization time.
- **FR-010**: When the developer changes a project metadata value, the next runtime resolution point in that project MUST observe the new value with no upgrade or re-initialization step. Runtime resolution points include session start, pre-tool-use hook invocation, and skill body evaluation.

#### Convention and domain rules

- **FR-011**: The tool MUST classify behavior-shaping rules into two buckets: exactly five always-on conventions (`async-concurrency`, `coding-style`, `existing-projects`, `security`, `tool-calls`) and eleven just-in-time domain rules (`api-design`, `architecture`, `configuration`, `data-access`, `error-handling`, `localization`, `multi-repo`, `naming`, `observability`, `performance`, `testing`). Just-in-time rules MUST load only when the skill or task they apply to is invoked.
- **FR-012**: Rules with architecture-specific branches (e.g., `error-handling`) or runtime substitution requirements (e.g., `naming`, which needs runtime company/domain substitution) MUST be in the just-in-time set, not the always-on set.
- **FR-013**: The session-start orientation message MUST be ≤500 tokens of standard output under typical project metadata, MUST serve as an index pointing to current project metadata and the validation command, and MUST NOT contain full rule bodies (a compact bootstrap, not a concatenation).

#### Command behavior

- **FR-014**: The initialization command MUST behave as a thin host-aware setup step for plugin-supporting hosts. It MUST NOT bulk-copy plugin-served assets into the user's repository. When invoked without an explicit host selection (e.g., no `--host` flag), it MUST launch the interactive host-selection prompt (the same prompt used by the configure command, per FR-016) and write files only for the hosts the user selects; it MUST NOT default to writing files for all supported hosts silently.
- **FR-015**: The upgrade command for plugin-supporting hosts MUST validate local configuration and schema state without updating plugin-served assets (host plugin update paths are the responsibility of the host, not the tool). A separate Copilot-targeted variant MUST re-render the Copilot-native files using the current plugin source and current project metadata.
- **FR-016**: The configure command MUST present every supported AI host as individually selectable in its interactive flow. Files MUST be written only for hosts the user selects.
- **FR-017**: The validation command MUST verify, at minimum: plugin install per configured host (via filesystem inspection of each host's documented plugin-cache directory, confirming the plugin manifest is present at the expected path; v1 does not shell out to host CLIs), presence of external binary prerequisites, structural validity of project metadata, detected-path correctness against the working tree, rendered-file freshness for non-plugin hosts, and managed-file manifest integrity.
- **FR-018**: A migration command MUST exist that cleans up legacy per-solution copies from previous layouts.
- **FR-019**: A `render <skill|rule>` command MUST exist that prints the runtime-resolved content of a named skill or rule using current project metadata, restoring on-demand inspectability without restoring on-disk pre-renders.

#### Migration safety

- **FR-020**: The migration command MUST classify each previously-managed file by content hash (against the managed-file manifest) as either still-clean (matches the original generated content) or user-modified.
- **FR-021**: The migration command MUST move still-clean files into a timestamped project-local backup folder at `.dotnet-ai-kit/backups/migrate/<timestamp>/` within the initialized solution. It MUST NOT delete clean files outright.
- **FR-022**: The migration command MUST preserve user-modified files in place unless the developer explicitly selects them for removal.
- **FR-023**: The backup folders created by the migration command MUST be retained with the same rotation policy as existing backup retention (keep most recent three).
- **FR-024**: The migration command MUST NOT re-render Copilot files. Re-rendering MUST be handled exclusively by the Copilot-targeted upgrade variant.
- **FR-025**: Initialization run with the force option MUST detect legacy artifacts that would be shadowed by the new architecture, MUST NOT auto-delete them, and MUST print the exact migration command for the developer to invoke.

#### Agent generation

- **FR-026**: Each logical specialist agent MUST have one source-of-truth definition. Host-specific agent files (per the host's documented format) MUST be generated from that single source.
- **FR-027**: For every supported host, the generated agent files MUST NOT contain fields unsupported by that host. The Claude Code path's agent files MUST NOT introduce a skill-preload field that causes performance regression at session start.

#### C# language intelligence

- **FR-028**: C# diagnostics and navigation MUST be exposed to the AI host through the host's edit-time language-intelligence path (the host's language-server primitive), so they surface at edit time rather than only when the AI explicitly invokes a tool. C# language intelligence MUST NOT regress through the migration, and missing prerequisites MUST be detected before release. (The "model-context-protocol primitive" and "language-server primitive" terminology preserves the user-visible distinction between explicit tool invocation and edit-time diagnostics.)

#### Verification gates

- **FR-029**: Before release, every supported plugin host MUST have a passing host-specific smoke fixture. For v1.0 this means three fixtures: one demonstrating that a Claude Code custom agent is listed under the plugin namespace; one demonstrating that a Codex CLI skill is visible after install; and one demonstrating that a Cursor sub-agent fixture is listed by Cursor.
- **FR-030**: A packaging test MUST exist that installs the distribution package into an isolated environment and confirms each host-specific plugin manifest directory is present in the installed location.
- **FR-031**: The validation command's output for a correctly-installed solution MUST exit with a zero status. For any broken state it MUST exit with a non-zero status that uniquely identifies the failing check class. Failing check classes MUST include, at minimum: missing plugin install per host, missing external binary prerequisite, invalid project metadata schema, detected-path inconsistency, stale Copilot render, and managed-file manifest inconsistency.

#### Additional requirements added in spec-phase round 1

- **FR-032**: The validation command MUST verify managed-file manifest integrity, including manifest readability, expected managed paths, content hashes for rendered/managed files, and actionable failure output when the manifest is missing, corrupt, or inconsistent with the working tree.
- **FR-033**: Any command path that writes tooling into linked secondary repositories MUST honor the same plugin-native footprint, host selection, and managed-manifest ownership rules as primary-repository initialization. It MUST NOT deploy legacy copied commands, rules, skills, or agents for plugin-supporting hosts.
- **FR-034**: Runtime architecture-profile selection MUST be resolved from current project metadata at hook/tool-use time, not frozen into session-start orientation output or into init-time renders. Missing or corrupt metadata MUST produce a clear corrective error.
- **FR-035**: A new host MUST NOT be added to the supported-host list or the configure UI unless it has all of: a documented host-native install/update path, documented artifact primitives for the assets being exposed, a passing host-specific smoke fixture, and a passing packaging test.

### Key Entities *(include if feature involves data)*

- **Plugin package per host**: One installable bundle for each AI host that has a plugin model (Claude Code, Codex CLI, Cursor). Each declares the host-specific manifest plus the shared assets the host can consume natively.
- **Project metadata**: A per-solution descriptor of the user's project, including company name, domain identifier, side (server/client), project type, and detected layer paths. Resolved at runtime by skills, rules, the session-start orientation hook, and the pre-tool-use architecture-profile resolution hook.
- **User configuration**: A per-solution descriptor of the developer's tool preferences (which hosts are enabled, retention settings, permission profile). Distinct from project metadata.
- **Source-of-truth agent definition**: A single markdown body per logical specialist agent, used as the input to per-host agent generators.
- **Always-on convention rule**: A rule consulted by every relevant AI interaction. The full set is exactly five files (broad code correctness, security, AI-behavior governance).
- **Just-in-time domain rule**: A rule loaded only when a skill or task that references it is invoked. The full set is eleven files covering area-specific guidance.
- **Architecture profile**: A bundle of conventions and structural assumptions tied to a project type. V1.0 supports exactly the 12 project types validated by the codebase today, organized in two branches: **microservice** (`command`, `query-sql`, `query-cosmos`, `processor`, `gateway`, `controlpanel`, `hybrid`) and **generic** (`vsa`, `clean-arch`, `ddd`, `modular-monolith`, `generic`). Resolved at runtime, not frozen at initialization.
- **Managed-file manifest**: A record of every file the tool wrote, with content hashes, used by the migration command to classify clean versus user-modified files and used by the validation command to assert manifest integrity.
- **Backup folder**: A timestamped, rotated project-local folder at `.dotnet-ai-kit/backups/migrate/<timestamp>/` where the migration command moves still-clean managed files.
- **Smoke fixture per host**: A minimal artifact (one agent for Claude Code, one skill for Codex CLI, one sub-agent for Cursor) used as the pre-merge verification that the host can load assets from the plugin package.
- **Linked secondary repository**: A sibling repository to which the primary-repository writer can deploy tooling. After this release, the secondary-repository writer must honor the plugin-native footprint and managed-manifest ownership rules.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For plugin-supporting hosts, initialization writes at least 90% fewer files into the user's repository than the previous layout (target: roughly an order of magnitude reduction).
- **SC-002**: For plugin-supporting hosts, a plugin update published by the maintainer reaches every initialized solution on a machine through one host-side update action per host ecosystem (not one global dotnet-ai action). Zero per-solution upgrade commands are required for plugin-supporting hosts. Copilot users continue to refresh via the Copilot-targeted upgrade variant; this success criterion does not apply to them.
- **SC-003**: After a developer renames a project metadata value (e.g., company name) and triggers the next runtime resolution point, the next code-generation invocation that references that value produces output using the new value, with no upgrade or re-initialization step.
- **SC-004**: The always-on context cost loaded at the start of every AI session is reduced by **at least 65%** compared to the previous layout, with a target band of **2500–3000 tokens** under typical project metadata. Measurement uses the repository's tokenizer with a conservative character-length fallback. (Tokens are used as the normative unit because the user-visible harm is model-context-budget burn; this is feature-specific reasoning that overrides the general guidance against tech-specific units.)
- **SC-005**: In Claude Code, the number of available command and skill entries listed to the user is exactly one per logical command and one per logical skill (no duplicate or triple-listed entries).
- **SC-006**: GitHub Copilot users observe the same logical content classes of project-aware assistance after the release as plugin host users — repository-wide conventions, path-scoped domain guidance, and per-agent files. The validation command can detect stale Copilot renders and report them for refresh.
- **SC-007**: When the migration command is run on a solution with user-modified managed files, 100% of user-modified files are preserved in place unless the developer explicitly selects them for removal.
- **SC-008**: All host-specific smoke fixtures pass before the release branch is merged. The release MUST NOT merge with any host-specific smoke fixture failing or absent. If the Cursor sub-agent fixture fails, full Cursor sub-agent generation is removed from the release scope (per OOS-005) and the release is revised accordingly; the fixture itself cannot be skipped while Cursor remains advertised as a supported plugin host. **Realized outcome (v1.0)**: the Cursor sub-agent spike fixture outcome flipped to `passed` per `discussion/tasks-phase/cursor-subagent-outcome.json`; full Cursor sub-agent generation is in scope and shipped (per A-005 PASS branch); the post-tag `workflow_dispatch` smoke run (T200) remains the authoritative validator.
- **SC-009**: The packaging test passes against a freshly built distribution package: every host-specific plugin manifest directory is present in the installed location.
- **SC-010**: For a correctly-installed solution with all prerequisites present, the validation command exits with zero status in under 10 seconds on a developer's typical workstation.
- **SC-011**: When the C# language-server binary is removed from the developer's search path, the validation command detects and reports this within its standard run, with a non-zero exit and a remediation hint that names the missing binary.
- **SC-012**: The `render` command produces the runtime-resolved Claude-host-shaped content of a parameterized skill or rule against a project metadata file in under 2 seconds. (v1 scope; rendering shapes for other plugin hosts are deferred to v1.1 if needed.)
- **SC-013**: The session-start orientation output is ≤500 tokens under typical project metadata and contains no full rule bodies. Verified by tokenizer count with character-length fallback.
- **SC-014**: In a linked-secondary-repository configuration, plugin-host initialization and migration do not create legacy copied commands, rules, skills, or agents in sibling repositories. The secondary-repository writer honors the same plugin-native footprint as the primary-repository writer.

## Assumptions

- **A-001**: Release context is **pre-v1.0.0**. The tool has no public users today and therefore carries no backward-compatibility tax. This justifies removal of broken aspirational code paths and a migration command that does not have to support production-deployed older layouts. Pre-v1.0.0 status does **not** justify relaxing validation gates: host smoke fixtures, packaging tests, project schema validation, manifest integrity checks, and language-server binary checks remain mandatory.
- **A-002**: Copilot remains in scope. Copilot has no plugin host, so its support is delivered through rendered repository-native files only; this is a deliberate design choice, not a workaround for missing implementation.
- **A-003**: The extensions subsystem is out of scope for this release. It remains as-is and is not modified by this work.
- **A-004**: The cross-AI debate captured in `issues/plugin-native-architecture/` and the spec-phase debate at `specs/019-plugin-native-arch/discussion/spec-phase/` have converged. The architecture, command behavior, verification gates, and deferred items recorded in those folders are the basis of this specification and are not re-litigated here.
- **A-005**: One Cursor sub-agent fixture is in scope and MUST pass before merge. Full Cursor sub-agent generation is in scope only if the fixture passes. A failed fixture forces either a spec revision removing full Cursor sub-agent generation from scope, or explicit deferral to v1.1; the release does not ship the capability advertised as supported with a failing fixture. **Spike outcome (v1.0)**: PASSED. The fixture at `agents/dotnet-ai-architect.md` loads in Cursor and appears in the host's sub-agent listing per `cursor-subagent-outcome.json::outcome == "passed"`. Full per-specialist Cursor sub-agent generation (13 specialists under `agents/`) ships in v1.0 per the PASS branch of `contracts/cursor-fixture-decision.contract.md:27-31`.
- **A-006**: Codex CLI's documented plugin primitives cover skills, model-context-protocol servers, and hooks. Native plugin agents for Codex are not yet documented and are therefore explicitly deferred to a future release rather than shipped in v1.0.
- **A-007**: The language-server-based path for C# intelligence depends on an external language-server binary being available on the developer's machine search path. The release's validation command must surface this dependency to the user.
- **A-008**: Repository paths outside the formally-managed manifest are treated as user-owned. Concrete examples on a .NET solution root include `AGENTS.md`, `.editorconfig`, `Directory.Build.props`, `Directory.Build.targets`, `Directory.Packages.props`, `global.json`, `nuget.config`, `.gitignore`, `.gitattributes`, `Dockerfile`, `docker-compose.yml`, CI workflow files, README files, license files, and solution/project files. The list is non-exhaustive and is captured in user-facing documentation; the FR-008 rule is the binding constraint.
- **A-009**: Each AI host's documented plugin model is treated as the source of truth for what that host loads. Symmetry between hosts is not assumed; per-host smoke fixtures are required as gates against treating documentation symmetry as loader symmetry.
- **A-010**: The release MUST work on Windows, macOS, and Linux. Every functional requirement is binding on each OS. The validation command (FR-017), the host-specific smoke fixtures (FR-029), the packaging test (FR-030), and the migration command (FR-018) MUST be exercised in continuous integration on Windows, macOS, and Linux. Path handling, subprocess invocation, search-path semantics, and file encoding follow the project conventions documented in `CLAUDE.md`.
- **A-011**: The tool MUST NOT make outbound network calls and MUST NOT emit telemetry from any of its commands (`init`, `upgrade`, `configure`, `check`, `migrate`, `render`, `extension-*`). No analytics, no crash reporting, no auto-update check. Host plugin installation, which is network-bound when the host fetches a plugin from its plugin registry, remains the host's responsibility and is out of the tool's process scope.

(Note: single-PR delivery is a plan/process decision, not a feature assumption; it has been moved to plan-phase scope.)

## Out of Scope

- **OOS-001**: Per-project GitHub Copilot plugin support. Copilot has no plugin host; render-time delivery via `.github/` is the only viable path and is the chosen approach.
- **OOS-002**: Extensions subsystem changes. The extensions subsystem stays exactly as-is in this release.
- **OOS-003**: A standalone-executable launcher (shiv / PyInstaller). Source-tree `bin/` wrappers (`bin/dotnet-ai` POSIX + `bin/dotnet-ai.cmd` Windows) that delegate to `python -m dotnet_ai_kit.cli` ship in v1.0 via Phase 10 commit 27 (tasks.md T180-T182) per `discussion/review-phase/claude/final-consolidated-review.md` line 674 + 720. A true standalone executable (no Python on PATH, cross-platform binary) remains deferred to v1.1 pending a cross-platform packaging spike.
- **OOS-004**: Native Codex CLI **plugin-manifest-bundled** subagents. **Partially lifted (v1.0, May 2026)**: per-project subagent rendering (`.codex/agents/<name>.toml` written by `CodexHost.write_per_solution_files()`) shipped in v1.0 per `https://developers.openai.com/codex/subagents` (retrieved 2026-05-19). What remains deferred: bundling subagents through the **plugin manifest** itself — the Codex docs at `developers.openai.com/codex/plugins/build` do NOT document an `agents` or `subagents` field on the plugin manifest, so the plugin-distribution surface for subagents stays OOS until the docs catch up.
- **OOS-005**: Full Cursor sub-agent generation if the in-release fixture does not pass. The release ships one mandatory Cursor sub-agent fixture; the full set is in scope only if that fixture passes. If the fixture fails, full generation is removed from this release's scope and deferred to v1.1 (see A-005 and SC-008 for the binding contract). **Resolved (v1.0)**: NOT triggered. The fixture passed per A-005, so full Cursor sub-agent generation is in scope and shipped; this OOS clause remains the documented fail-branch contract for future regression handling (a failing post-tag `workflow_dispatch` smoke run reinstates it).
- **OOS-006**: A multi-repository activity monitor. Justified as future work but not bundled in this release. Plugin-served-artifact drift across sibling repositories is solved by FR-033 (linked-secondary-repository footprint) plus US1 (single-host-action update propagation); sibling-repository activity surveillance beyond that is deferred.
- **OOS-007**: Backward-compatibility shims for the previous per-solution copy layout. Pre-v1.0.0 status removes the need; the migration command handles the bridge.
