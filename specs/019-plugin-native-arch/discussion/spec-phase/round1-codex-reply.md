# Spec Round 1 - Codex reply

## Spec critique

### User stories

US1 - REVISE. The story earns P1, but it currently tests "make a change to plugin source, run host update once" as if all three plugin hosts have identical update semantics. Keep the user value, but state the observable contract as "host-native plugin update makes the current plugin assets available to every project that uses that host" and let host-specific update mechanics live in plan. The agreed architecture says plugin update propagation applies to Claude/Codex/Cursor, while Copilot is explicitly separate through render refresh (issues/plugin-native-architecture/FINAL-REPORT.md:75-84, issues/plugin-native-architecture/codex/final-merged-findings.md:236-245).

US2 - REVISE. Copilot parity is P1, but the current wording says "same quality" and later SC-006 tries to measure quality by freshness, which is not a quality baseline. The acceptance scenarios are closer to correct because they name repo-wide, path-scoped, and per-agent Copilot outputs (specs/019-plugin-native-arch/spec.md:49-51). Rewrite the story around structural parity and freshness detection, not subjective assistance quality.

US3 - DISAGREE. This is plumbing dressed as a user story. The spec itself admits it is "a precondition for the rest of the release" and "not a user-observable value win on its own" (specs/019-plugin-native-arch/spec.md:57-60). That violates the independent-MVP-slice rule Claude called out in the assignment (specs/019-plugin-native-arch/discussion/spec-phase/round1-claude-to-codex.md:21-24). Demote it to FR-016 plus verification gates, or reframe it as a team story about mixed-tool repositories where the independent value is avoiding unwanted host files.

US4 - AGREE with one missing edge. Runtime customization is real user value and directly addresses stale Jinja and stale detected paths (issues/plugin-native-architecture/codex/final-merged-findings.md:131-139). The story should also cover runtime architecture-profile resolution through the PreToolUse hook, because that was a specific commit-order item and is currently missing from the spec story layer (issues/plugin-native-architecture/FINAL-REPORT.md:101-104).

US5 - AGREE with precision fixes. Safe migration is necessary even pre-v1.0 because user-modified files can exist in dogfood repos. The story correctly uses content-hash classification and backup rotation (specs/019-plugin-native-arch/spec.md:85-98), but it should cite manifest-driven ownership, not generic hash scanning, because the agreed design explicitly reuses existing manifest/hash infrastructure (issues/plugin-native-architecture/codex/final-merged-findings.md:88-91, issues/plugin-native-architecture/codex/final-merged-findings.md:243-247).

US6 - REVISE. Split `check` and `render`. `check` is not P3; it gates Copilot freshness, missing binary prerequisites, project schema validity, and LSP safety before merge (issues/plugin-native-architecture/FINAL-REPORT.md:81-83, issues/plugin-native-architecture/FINAL-REPORT.md:137-143). `render` is a P3 inspectability mitigation. Keeping both in one P3 story understates validation and overstates inspection as a general user feature.

### Functional requirements

FR-001 - REVISE. "Three AI hosts with first-class plugin models" is correct for v1, but Cursor sub-agent depth is conditional on a spike. Say the tool ships installable plugin packages for Claude Code, Codex CLI, and Cursor; individual capabilities inside those packages are gated by each host's documented primitives and smoke fixtures (specs/019-plugin-native-arch/spec.md:134-135, issues/plugin-native-architecture/FINAL-REPORT.md:23-31).

FR-002 - AGREE. This captures the host-native boundary and prevents Codex from inheriting Claude-only primitives (issues/plugin-native-architecture/codex/final-merged-findings.md:49-58).

FR-003 - REVISE. "Without further file copying" is too broad. Host plugin installation can copy into a host-managed plugin cache; the user-visible prohibition is project-local copying of commands/rules/skills/agents for plugin hosts (specs/019-plugin-native-arch/spec.md:141-143).

FR-004 - AGREE. Copilot is correctly non-plugin and GitHub-native (issues/plugin-native-architecture/FINAL-REPORT.md:68-72).

FR-005 - REVISE. "Minimum files" is not testable, and "one order of magnitude" duplicates SC-001. Use the agreed per-solution file list or a numeric ceiling. The final report names `.dotnet-ai-kit/config.yml`, `.dotnet-ai-kit/project.yml`, and `.claude/settings.json`, plus Copilot `.github/*` renders when selected (issues/plugin-native-architecture/FINAL-REPORT.md:61-72).

FR-006 - AGREE. This is the core footprint contract.

FR-007 - REVISE. It should explicitly require repo-wide, path-scoped, and per-agent Copilot outputs. The current FR says "instruction and custom-agent files" but leaves path-scoped granularity to US2 only (specs/019-plugin-native-arch/spec.md:143, issues/plugin-native-architecture/FINAL-REPORT.md:68-72).

FR-008 - REVISE. Too narrow. Root `AGENTS.md` was the concrete bug, but the rule should be generic: commands MUST NOT write, modify, migrate, or delete paths outside the formally managed manifest unless the user explicitly opts into that exact path. The final design says root `AGENTS.md` stays untouched (issues/plugin-native-architecture/FINAL-REPORT.md:73), but the spec should protect all user-owned root files, not just one example (specs/019-plugin-native-arch/spec.md:144).

FR-009 - AGREE. This directly maps to stale substitution and stale detected paths.

FR-010 - REVISE. "Next AI session" is too narrow for hooks that fire during a session. Use "next runtime resolution point" and require clear failure when metadata is missing or invalid (specs/019-plugin-native-arch/spec.md:149, specs/019-plugin-native-arch/spec.md:120-122).

FR-011 - REVISE. The split is correct, but the spec dodges the agreed 5/11 classification while the verification checklist hard-codes it (specs/019-plugin-native-arch/checklists/verification.md:66-72). Either the spec owns "exactly five always-on conventions" or the checklist is enforcing policy not present in the spec.

FR-012 - REVISE. "Deliberately small relative to the previous set" is not objectively testable. Tie it to the agreed five always-on files or the always-on context budget (issues/plugin-native-architecture/codex/final-merged-findings.md:284-313).

FR-013 - REVISE. The quantitative SessionStart budget is not plan trivia. The converged design says `<=500` tokens and "not concatenated rule bodies" (issues/plugin-native-architecture/codex/final-merged-findings.md:322-327). Put that number in the spec, and add the missing PreToolUse runtime architecture-profile contract.

FR-014 - AGREE. Good user-observable command behavior.

FR-015 - REVISE. "Near no-op" is informal and vague. Specify that plugin-host upgrade validates local config/schema state and does not update plugin-served assets; Copilot refresh is a named render-refresh path (issues/plugin-native-architecture/codex/final-merged-findings.md:240-245).

FR-016 - AGREE, but this is where US3 belongs if US3 is removed.

FR-017 - REVISE. Missing manifest hash integrity. The agreed `check` command validates plugin install, binary, project schema, detected paths, Copilot freshness, and manifest hash integrity (issues/plugin-native-architecture/codex/final-merged-findings.md:241-244). The spec omits the last item (specs/019-plugin-native-arch/spec.md:162).

FR-018 - AGREE.

FR-019 - REVISE. The command is named `render` in the agreed CLI table, but the spec calls it "inspection command" (issues/plugin-native-architecture/FINAL-REPORT.md:83-84, specs/019-plugin-native-arch/spec.md:164). Use the user-facing command name or explicitly say the name is deferred. Also require host-qualified output where host rendering differs.

FR-020 - AGREE.

FR-021 - REVISE. "Within the tool's data directory" may mean global app data. The agreed path is project-local `.dotnet-ai-kit/backups/migrate/<timestamp>/` with 3-keep rotation (issues/plugin-native-architecture/FINAL-REPORT.md:81-83, issues/plugin-native-architecture/codex/final-merged-findings.md:243-245).

FR-022 - AGREE.

FR-023 - AGREE.

FR-024 - AGREE. This preserves the R3 separation of cleanup and Copilot refresh (issues/plugin-native-architecture/discussion/round2-codex-signoff.md:13-17).

FR-025 - AGREE.

FR-026 - AGREE. This is the right user-facing agent-source contract.

FR-027 - DISAGREE. "Named per-host generators, not a generic runtime field map" is plan-phase implementation detail. The spec should require host-native output with no unsupported fields; the generator shape belongs in the plan and verification checklist. This contradicts the checklist's "No implementation details" claim (specs/019-plugin-native-arch/checklists/requirements.md:9-11).

FR-028 - REVISE. The "no unsupported fields" part is a product contract; "tests MUST assert" and "Claude Code path" are verification details. Move test mechanics to verification.md and keep the observable output constraint in the spec.

FR-029 - REVISE. Protocol names are acceptable in this developer-tooling spec, but the requirement should lead with the observable outcome: C# diagnostics and navigation surface at edit time through the host's edit-time language intelligence path. MCP-vs-LSP can remain as explanatory specificity.

FR-030 - DISAGREE. This is sequencing and CI gating, not a functional requirement. Keep the user-visible contract as "C# intelligence must not regress and missing prerequisites must be detected before release"; leave CHK009-CHK012 to enforce order (specs/019-plugin-native-arch/checklists/verification.md:28-36).

FR-031 - REVISE. Host names are fine for v1, but phrase it as "each supported plugin host" with the current three listed. Also resolve the Cursor contradiction: SC-008 says the release must not merge with a failing Cursor fixture (specs/019-plugin-native-arch/spec.md:216), while A-005/OOS-005 imply the release can continue after a failed fixture by deferring full generation (specs/019-plugin-native-arch/spec.md:228, specs/019-plugin-native-arch/spec.md:241).

FR-032 - AGREE.

FR-033 - AGREE with one addition: the failing check classes must include manifest integrity and stale Copilot render classes, not only generic broken state.

MISSING - FR-034: The validation command MUST verify managed-file manifest integrity, including manifest readability, expected managed paths, content hashes for rendered/managed files, and actionable failure output when the manifest is missing, corrupt, or inconsistent with the working tree. Source: agreed `check` scope includes manifest hash integrity (issues/plugin-native-architecture/codex/final-merged-findings.md:241-244).

MISSING - FR-035: Any command path that writes tooling into linked secondary repositories MUST honor the same plugin-native footprint, host selection, and managed-manifest ownership rules as primary-repository initialization; it MUST NOT continue deploying legacy copied commands, rules, skills, or agents for plugin-supporting hosts. Source: linked secondary-repo deployment exists today and writes tooling (issues/plugin-native-architecture/codex/final-merged-findings.md:92).

MISSING - FR-036: Runtime architecture-profile selection MUST be resolved from current project metadata at hook/tool-use time, not frozen into SessionStart output or init-time renders, and missing/corrupt metadata MUST produce a clear corrective error. Source: commit 13 explicitly includes SessionStart compact bootstrap plus PreToolUse runtime arch-profile hook (issues/plugin-native-architecture/FINAL-REPORT.md:101-104).

MISSING - FR-037: A host MUST NOT be added to the supported-host list or configure UI unless it has a documented host-native install/update path, documented artifact primitives for the assets being exposed, and a passing host-specific smoke fixture plus packaging test. Source: the converged design uses host-specific smoke tests to avoid treating documentation symmetry as loader symmetry (issues/plugin-native-architecture/codex/final-merged-findings.md:465-483).

### Success criteria

SC-001 - AGREE.

SC-002 - REVISE. Good for plugin hosts, but ensure it does not imply one update action across different hosts. It is one host-side update action per host ecosystem, not one global dotnet-ai action (specs/019-plugin-native-arch/spec.md:210).

SC-003 - AGREE.

SC-004 - REVISE. Sixty percent is sandbagged. The agreed estimate is about 9000 tokens down to 2500-3000, a 67-72% reduction (issues/plugin-native-architecture/FINAL-REPORT.md:111-114, issues/plugin-native-architecture/codex/final-merged-findings.md:308-313). I would defend a 65% floor plus a target band of 2500-3000 tokens; 60% would allow 3600 tokens, which misses the agreed design.

SC-005 - AGREE.

SC-006 - DISAGREE. Untestable pre-v1.0. There is no public baseline, and freshness is not quality (specs/019-plugin-native-arch/spec.md:214). Replace with a structural criterion: Copilot render contains the same logical content classes as plugin hosts - repo-wide conventions, path-scoped domain guidance, per-agent files - and `check` detects stale renders.

SC-007 - AGREE.

SC-008 - REVISE. It is correct to make smoke fixtures mandatory, but the Cursor branch must be clarified. If Cursor fixture failure is allowed to defer only full sub-agent generation, then SC-008 cannot say the release MUST NOT merge with the Cursor fixture failing. My preference: the fixture itself is mandatory; full generation is conditional on it passing.

SC-009 - AGREE.

SC-010 - AGREE.

SC-011 - AGREE.

SC-012 - REVISE. "For at least one supported host" is too weak because `render` is the mitigation for losing pre-rendered files across plugin hosts (issues/plugin-native-architecture/codex/final-merged-findings.md:389-404). Require every host whose skill/rule rendering can differ, or explicitly state that v1 render output is Claude-shaped and document why that is enough.

MISSING - SC-013: SessionStart bootstrap output is `<=500` tokens under typical project metadata and contains no full rule bodies. This should be a success criterion because the agreed design made it a hard token-burn guard (issues/plugin-native-architecture/codex/final-merged-findings.md:322-327).

MISSING - SC-014: In a linked-secondary-repo configuration, plugin-host initialization and migration do not create legacy copied commands/rules/skills/agents in sibling repositories.

### Edge cases

Plugin updated mid-session - AGREE. Keep it and document host-equivalent reload wording rather than only Claude-style `/reload-plugins` (specs/019-plugin-native-arch/checklists/verification.md:95-100).

Project metadata missing or corrupt at runtime - AGREE. This is necessary for runtime resolution.

External binary prerequisite missing - AGREE.

User-modified managed files during migration - AGREE.

Experimental host capability undocumented loader - REVISE. This is really the Cursor sub-agent branch. It belongs as a risk/gate, but the spec must not let an unsupported capability quietly ship as "supported" after a failed fixture (specs/019-plugin-native-arch/spec.md:124).

Repository file collision - REVISE. Replace the one-file `AGENTS.md` edge with a general "unmanaged paths are untouched" rule and list common examples in docs (specs/019-plugin-native-arch/spec.md:125).

Shared asset format field mismatch - AGREE. This maps well to the per-host output contract.

MISSING - Linked secondary repositories. If linked repo deployment remains in code, it is an edge case for every footprint and migration promise. The current code fact is in the merged findings (issues/plugin-native-architecture/codex/final-merged-findings.md:92).

### Assumptions

A-001 - REVISE. Pre-v1.0 removes backward-compatibility tax, but it must not imply migration can ignore existing dogfood modifications or validation gates. Codex already signed off on "pre-v1 does not justify weak validation" (issues/plugin-native-architecture/discussion/round2-codex-signoff.md:23-27).

A-002 - AGREE.

A-003 - AGREE.

A-004 - AGREE.

A-005 - REVISE. Conditional scope in the spec is risky. State that one Cursor sub-agent fixture is in scope and must pass; full Cursor generation is in scope only if the fixture passes before implementation reaches that slice. A failed fixture should force either a spec revision or explicit removal of Cursor sub-agent support from the release.

A-006 - AGREE. Codex native agents are correctly deferred until documentation or smoke-test proof exists (issues/plugin-native-architecture/discussion/round2-codex-signoff.md:18-22).

A-007 - AGREE.

A-008 - REVISE. Root `AGENTS.md` is an example of the broader unmanaged-path rule, not the whole assumption.

A-009 - DISAGREE. Single-PR delivery is plan/process, not a feature assumption. Move it to plan. The spec can say verification gates are mandatory, but commit packaging is not user-observable (specs/019-plugin-native-arch/spec.md:232).

A-010 - AGREE. This is an important host-boundary assumption.

### Out of scope

OOS-001 - AGREE.

OOS-002 - AGREE.

OOS-003 - AGREE.

OOS-004 - AGREE.

OOS-005 - REVISE. This must be reconciled with SC-008. Full Cursor generation can be out of scope if the fixture fails, but the fixture itself cannot be optional if Cursor remains advertised as a supported plugin host (specs/019-plugin-native-arch/spec.md:216, specs/019-plugin-native-arch/spec.md:241).

OOS-006 - AGREE with wording changes. The monitor can be deferred, but the spec must stop implying all team/sibling-repo drift is solved if linked-repo tooling writes remain unaddressed (specs/019-plugin-native-arch/spec.md:15, issues/plugin-native-architecture/codex/final-merged-findings.md:410-425).

OOS-007 - AGREE.

## Answers to the 5 open questions

Q1. Cursor sub-agent loader status: Current Cursor public material does more than the older marketplace announcement, but still does not replace a dotnet-ai smoke fixture. Cursor's Feb 17, 2026 blog says plugins bundle "MCP servers, skills, subagents, rules, and hooks" and lists Subagents as a plugin primitive (https://cursor.com/blog/marketplace lines 48-52 and 92-98). The Cursor 2.5 changelog says plugins package "skills, subagents, MCP servers, hooks, and rules" and can be installed with `/add-plugin` (https://cursor.com/changelog/2-5 lines 37-45). The live marketplace page for Cursor's own Agent Compatibility plugin exposes `/add-plugin agent-compatibility` and lists four Subagents (https://cursor.com/marketplace/cursor/agent-compatibility lines 45-55). That proves marketplace-loaded plugin subagents exist in product UI. What I still do not see in static docs is a precise loader spec for file layout and discovery semantics; the official GitHub README's repository structure lists manifests, skills, rules, and MCP but not an `agents/` directory (https://github.com/cursor/plugins lines 286-300). So A-005's spike is meaningful, not placeholder.

Q2. Emerging AI hosts: Keep v1 cardinality at four, but add FR-037 so new hosts can be admitted without re-architecting. Gemini CLI is the closest v1.1 candidate: its extension reference documents install/update commands, extension manifests, custom commands, hooks, skills, preview sub-agents, and policy rules (https://geminicli.com/docs/extensions/reference/ lines 276-289, 370-423, 469-501). Cline is close for CLI/SDK/Kanban, but its own docs say plugins currently do not apply to the VSCode and JetBrains extensions (https://docs.cline.bot/customization/plugins lines 88-89); it also has skills, rules, and MCP (https://docs.cline.bot/customization/skills lines 97-109; https://docs.cline.bot/mcp/mcp-overview lines 96-124). Windsurf has Skills, Rules, Workflows, MCP, global/workspace skill scopes, and enterprise/system skills, but I did not find a single plugin package/update primitive comparable to Claude/Codex/Cursor (https://docs.windsurf.com/windsurf/cascade/skills lines 207-225, 273-282; https://docs.windsurf.com/windsurf/cascade/mcp lines 364-377). Continue.dev has configurable agents composed of models, rules, and tools/MCP, but this is config distribution rather than a host plugin package (https://docs.continue.dev/reference lines 55-80). JetBrains AI Assistant supports ACP agents and MCP pass-through, but that is an agent-hosting protocol, not a dotnet-ai asset plugin surface (https://www.jetbrains.com/help/ai-assistant/activate-agents.html lines 190-223). Recommendation: no fifth host in v1; design host onboarding gates now.

Q3. Path collision risk beyond root AGENTS.md: Use a generic rule, not an enumerated allow/deny list. Common .NET solution-root files that dotnet-ai-kit must treat as developer-owned unless already in its managed manifest: `AGENTS.md`, `.editorconfig`, `Directory.Build.props`, `Directory.Build.targets`, `Directory.Packages.props`, `global.json`, `nuget.config`/`NuGet.config`, `.gitignore`, `.gitattributes`, `Dockerfile`, `docker-compose.yml`, `azure-pipelines.yml`, `GitHub Actions` workflows under `.github/workflows/`, `README.md`, `LICENSE`, and solution/project files. The high-risk .NET-specific ones are `Directory.Build.*`, `Directory.Packages.props`, `global.json`, and NuGet config because changing them changes builds for the whole solution. FR-008 should say "not managed by manifest equals untouched," with examples in docs. The current "such as AGENTS.md" wording is too narrow (specs/019-plugin-native-arch/spec.md:144).

Q4. Multi-repo monitor scope: Defend OOS-006 for the monitor itself. The final merged design explicitly deferred it and says it is valuable but not required to remove the duplicate-copy architecture (issues/plugin-native-architecture/codex/final-merged-findings.md:410-425). However, the spec must still cover the existing linked secondary-repo writer because otherwise a legacy copy path can bypass the new footprint rules (issues/plugin-native-architecture/codex/final-merged-findings.md:92). My position: keep the activity monitor out of v1, add FR-035 to prevent linked-repo deployment from writing old project-local tooling for plugin hosts, and trim any claim that v1 fully solves sibling-repo divergence.

Q5. SessionStart token budget visibility: Keep the quantitative budget in the spec. SessionStart stdout enters model context, so the size is user-observable as context burn and response quality degradation. The converged design's contract is `<=500` tokens, compact index only, no rule-body concatenation (issues/plugin-native-architecture/codex/final-merged-findings.md:322-327). Use tokens as the normative unit because the harm is token budget; verification can use the repo's tokenizer with a conservative character fallback if needed.

## Verdict on each contestable claim C1-C12

C1 - DISAGREE. Six stories is not the right cardinality because US3 confesses it is scaffolding, not independent value (specs/019-plugin-native-arch/spec.md:57-60). Remove US3 as a story or reframe it around mixed-tool team setup; split US6 into `check` and `render` if story count matters.

C2 - REVISE. `check` deserves P2 because it gates Copilot freshness and LSP prerequisite safety; `render` deserves P3 as inspectability mitigation. The agreed CLI table treats them as separate commands with separate purposes (issues/plugin-native-architecture/FINAL-REPORT.md:81-84).

C3 - REVISE. Naming the four supported hosts is OK for v1 scope because the final report scope names them (issues/plugin-native-architecture/FINAL-REPORT.md:5-7). FR-031 should still generalize to "each supported plugin host" so adding Gemini/Cline/etc. later does not require rewriting the principle.

C4 - DISAGREE. SC-004's 60% floor is too low. The agreed estimate is ~9000 to ~2500-3000 tokens (issues/plugin-native-architecture/FINAL-REPORT.md:111-114). I would set a 65% floor and keep 2500-3000 as the target band.

C5 - DISAGREE. A-005's conditional branch is too loose for a spec. The release should commit to a passing Cursor fixture or explicitly revise scope before merge; full Cursor agent generation can remain conditional after the fixture passes.

C6 - DISAGREE. FR-030 is plan/verification sequencing. Keep the outcome in the spec and enforce order in CHK009-CHK012 (specs/019-plugin-native-arch/checklists/verification.md:28-36).

C7 - AGREE with wording. MCP and LSP are not implementation leaks for a developer-tooling spec, but the requirement should lead with the user-visible difference: edit-time diagnostics/navigation versus explicit tool invocation (specs/019-plugin-native-arch/spec.md:181-184).

C8 - DISAGREE. FR-008 is too narrow. Generalize to unmanaged paths and managed manifests; list `AGENTS.md` as a concrete example (specs/019-plugin-native-arch/spec.md:144).

C9 - DISAGREE. SC-006 is not testable because there is no public baseline and freshness is not quality (specs/019-plugin-native-arch/spec.md:214). Replace with structural Copilot parity.

C10 - DISAGREE. The spec dropped or diluted several agreed items: manifest hash integrity in `check` (issues/plugin-native-architecture/codex/final-merged-findings.md:241-244), PreToolUse runtime arch-profile (issues/plugin-native-architecture/FINAL-REPORT.md:101-104), linked secondary-repo write-path handling (issues/plugin-native-architecture/codex/final-merged-findings.md:92), and the exact SessionStart token budget (issues/plugin-native-architecture/codex/final-merged-findings.md:322-327).

C11 - REVISE. OOS-006 is correct for the monitor, but only if the spec adds a requirement preventing existing linked-repo deployment code from preserving the old copy architecture. Otherwise v1 leaves a back door through `copier.py` behavior recorded in the merged findings (issues/plugin-native-architecture/codex/final-merged-findings.md:92).

C12 - REVISE. The current personas are too developer-only. Do not add three new stories, but do add explicit contracts for the plugin maintainer publishing/packaging path and the new-tool integrator admission gate. A team lead's sibling-repo monitor can remain OOS with the FR-035 guard.

## New requirements (if any)

FR-034: The validation command MUST verify managed-file manifest integrity, including manifest readability, expected managed paths, content hashes for rendered/managed files, and actionable failure output when the manifest is missing, corrupt, or inconsistent with the working tree.

FR-035: Any command path that writes tooling into linked secondary repositories MUST honor the same plugin-native footprint, host selection, and managed-manifest ownership rules as primary-repository initialization; it MUST NOT deploy legacy copied commands, rules, skills, or agents for plugin-supporting hosts.

FR-036: Runtime architecture-profile selection MUST be resolved from current project metadata at hook/tool-use time, not frozen into SessionStart output or init-time renders; missing or corrupt metadata MUST produce a clear corrective error.

FR-037: A host MUST NOT be added to the supported-host list or configure UI unless it has a documented host-native install/update path, documented artifact primitives for the assets being exposed, and a passing host-specific smoke fixture plus packaging test.

## Other findings I haven't surfaced

The requirements checklist is over-green. It claims no implementation details and non-technical stakeholder readability (specs/019-plugin-native-arch/checklists/requirements.md:7-12), but the spec contains generator architecture, CI sequencing, MCP/LSP protocol routing, smoke fixtures, and commit delivery assumptions (specs/019-plugin-native-arch/spec.md:177-190, specs/019-plugin-native-arch/spec.md:224-233). That is not fatal, but the checklist should mark these as intentional technical-spec exceptions or move them out.

`verification.md` and `spec.md` disagree on the inspection command name. The agreed design calls it `render <skill|rule>` (issues/plugin-native-architecture/FINAL-REPORT.md:83-84), verification calls the section "Render command" (specs/019-plugin-native-arch/checklists/verification.md:85-89), but the spec calls it an "inspection command" (specs/019-plugin-native-arch/spec.md:102-115). Pick one user-facing name before plan.

The verification checklist has stronger rule classification than the spec. CHK030 says exactly five always-on conventions (specs/019-plugin-native-arch/checklists/verification.md:66-72), but FR-011/FR-012 only say "small" and "relative" (specs/019-plugin-native-arch/spec.md:153-155). A checklist should not silently introduce a stricter product contract.

The spec's Background says drift across a team's sibling repositories is an observed structural problem (specs/019-plugin-native-arch/spec.md:12-17), but OOS-006 defers the monitor that would address sibling-repo activity divergence (specs/019-plugin-native-arch/spec.md:242). Narrow the claim to plugin-served artifact drift unless FR-035 is added.

## Open disputes for round 2

US3 status: remove it as a story or reframe it around independent mixed-tool user value.

US6 priority split: `check` should be P2; `render` should be P3.

Cursor branch semantics: can the release merge if the Cursor sub-agent fixture fails, or is only full generation conditional after the fixture passes?

Spec-vs-plan boundary: FR-027 and FR-030 should move out of functional requirements.

SessionStart budget: spec should own `<=500` tokens, not leave it only in verification.

Linked secondary repos: monitor can be OOS, but legacy linked-repo writes cannot bypass plugin-native footprint rules.
