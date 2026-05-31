# Requirements Quality Checklist: v2 Planning-Fidelity Gaps

**Purpose**: Unit-test the *requirements* in [spec.md](../spec.md) — completeness, clarity, consistency, measurability, coverage — before implementation. (Tests the spec writing, not the code.)
**Created**: 2026-05-31
**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md)
**Depth**: Standard · **Audience**: Reviewer (PR) + author

## Requirement Completeness

- [ ] CHK001 Are resource requirements defined for every skill-kind that needs them (FR-D33 set, `add-*`, clusters) AND is the "no resources" default explicitly allowed? [Completeness, Spec §FR-022-01..03]
- [ ] CHK002 Is the hook-backend resolution requirement specified for all states (installed / shadowed / absent)? [Completeness, Spec §FR-022-10/12]
- [ ] CHK003 Are the user-owned files enumerated exhaustively, with an action for each file-state? [Completeness, Spec §FR-022-13, contracts/user-file-policy.md]
- [ ] CHK004 Are golden-output requirements defined for every artifact-type × host plus all singleton outputs (manifests/marketplace/hooks/AGENTS/copilot-instructions)? [Completeness, Spec §FR-022-08]
- [ ] CHK005 Is the eval-case file format (fields + required-ness) fully specified? [Completeness, contracts/eval-cases.schema.md]
- [ ] CHK006 Are the success criteria SC-022-1..7 each traceable to at least one FR and one user story? [Completeness, Spec §Success Criteria]
- [ ] CHK007 Is the script trust/security model's scope (which scripts, what "consent" means) defined? [Completeness, Spec §FR-022-05]

## Requirement Clarity

- [ ] CHK008 Is "resources where they add value" (AR-5 opt-in) quantified into a concrete firm subset, not left subjective? [Clarity, Spec §Clarifications, §FR-022-03]
- [ ] CHK009 Is "merge" for `settings.json` defined precisely (JSON deep-merge rules: key precedence, array handling)? [Clarity, contracts/user-file-policy.md]
- [ ] CHK010 Is "shadowing shim" defined by a checkable rule (resolved path is not the v2 tool)? [Clarity, Spec §FR-022-10]
- [ ] CHK011 Is the confusion-matrix pass condition unambiguous (rank within top-k AND no sibling above)? [Clarity, contracts/eval-cases.schema.md]
- [ ] CHK012 Is "fail safe" for the hook defined as a concrete behavior (exit 0, no block, clear stderr)? [Clarity, Spec §FR-022-12]

## Requirement Consistency

- [ ] CHK013 Does the opt-in resource decision (AR-5) reconcile the conflict with planning/23 §368 "every skill" without leaving both claims active? [Consistency, Conflict, Spec §Overview/Clarifications]
- [ ] CHK014 Is the launcher decision (require global tool) consistent between spec §FR-022-10, research §R1, and contracts/hook-launcher.md? [Consistency]
- [ ] CHK015 Are the Claude-scoped enforcement claims (T2 prompt / forced-output-style) consistent with planning/26 AR-3 (no Stop-level claims on non-Claude hosts)? [Consistency, Spec §FR-022-15/16]
- [ ] CHK016 Is terminology consistent ("user-owned file" vs "managed file" used the same way across spec/data-model/contracts)? [Consistency]

## Acceptance Criteria Quality (Measurability)

- [ ] CHK017 Can each SC-022-N be objectively verified by a named command or test (no vague "works")? [Measurability, Spec §Success Criteria]
- [ ] CHK018 Is the resource-presence criterion measurable (a corpus-integrity test asserts the required set)? [Measurability, Spec §SC-022-1]
- [ ] CHK019 Is the install-smoke criterion measurable and CI-portable (validate --strict, skip-if-absent)? [Measurability, Spec §SC-022-6, research §R7]
- [ ] CHK020 Is golden-test independence measurable (an induced format change fails a golden, separate from drift)? [Measurability, Spec §FR-022-09]

## Scenario & Edge-Case Coverage

- [ ] CHK021 Are requirements defined for an empty/missing-file resource dir (broken-resource load error)? [Coverage, Edge Case, Spec §Edge Cases]
- [ ] CHK022 Is the invalid-JSON `settings.json` case specified (back up + warn, never discard)? [Coverage, Edge Case, contracts/user-file-policy.md]
- [ ] CHK023 Is the "v2 tool genuinely absent" case specified (fail safe, no wedge)? [Coverage, Exception Flow, Spec §FR-022-12]
- [ ] CHK024 Are cross-platform script siblings (.ps1/.sh) required where a `.py` script ships (Windows parity)? [Coverage, NFR-3, Spec §FR-022-05]
- [ ] CHK025 Is the Stop-loop case covered (`stop_hook_active` prevents re-block)? [Coverage, contracts/hook-launcher.md]

## Non-Functional Requirements

- [ ] CHK026 Are no-network (NFR-1) and drift-clean (SC-A) preserved as explicit constraints for every phase? [NFR, Spec §SC-022-7, plan Constitution Check]
- [ ] CHK027 Is byte-stable/deterministic projection required for copied resources? [NFR, Spec §FR-022-04]
- [ ] CHK028 Is the no-new-abstraction constraint (AR-8) honored (work fits existing layers, no new projects)? [NFR, plan §Structure Decision]

## Dependencies & Assumptions

- [ ] CHK029 Is the external `claude` CLI dependency documented with a graceful skip when absent? [Dependency, research §R7]
- [ ] CHK030 Is the assumption that the v2 tool is install-able/on-PATH validated by a check + docs (not assumed)? [Assumption, Spec §FR-022-10]
- [ ] CHK031 Are Codex/Cursor's distinct discovery mechanisms documented as an explicit boundary (not assumed equal to Claude's)? [Dependency, Spec §FR-022-18, research §R7]

## Ambiguities & Conflicts (resolve before implement)

- [ ] CHK032 Are all `[NEEDS CLARIFICATION]` markers resolved in spec.md (launcher mechanism closed)? [Ambiguity, Spec §Clarifications]
- [ ] CHK033 Is the `blazor-hybrid` outcome unambiguous (author OR recorded de-scope — exactly one)? [Conflict, Spec §FR-022-20]
- [ ] CHK034 Is the eval scope boundary explicit (cluster deterministic now; ≥20/skill LLM later)? [Ambiguity, Spec §Out of scope, research §R3]
- [ ] CHK035 Is "live in-session hook firing" clearly out of scope so SC claims don't overreach? [Ambiguity, Spec §Out of scope]

## Traceability

- [ ] CHK036 Does every FR-022-NN trace to a user story (or a named standalone, e.g. FR-022-19/20) and a gap-trace row? [Traceability, Spec §Gap-trace]
- [ ] CHK037 Does every user story have an Independent Test and ≥1 acceptance scenario? [Traceability, Spec §User Scenarios]

## Notes

- Check items off as the spec is confirmed/clarified: `[x]`. `[Gap]` = the spec is missing the requirement; `[Conflict]`/`[Ambiguity]` = needs resolution before `/speckit.implement`.
- ≥80% of items carry a traceability reference (spec §, contract, research §, or marker).
