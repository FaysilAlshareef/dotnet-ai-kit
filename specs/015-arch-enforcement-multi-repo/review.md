# Code Review: Commit d33f1d0 — Architecture Profiles, Multi-Repo Deployment, and Enforcement Optimization

**Branch**: `015-arch-enforcement-multi-repo`
**Commit**: `d33f1d081a0819e57ba7302c9c0d2e303dc6fe35`
**Reviewed**: 2026-04-04
**Spec**: `specs/015-arch-enforcement-multi-repo/spec.md`
**68 files changed, +4570 lines**
**All 254 tests pass. 6 ruff lint errors (3 introduced by this commit).**

---

## BUGS (Issues That Will Cause Incorrect Behavior)

### BUG-1: String version comparison will break for multi-digit versions (copier.py:740)
**Severity**: High | **Introduced by**: This commit

```python
if secondary_version and secondary_version > tool_version:
```

String comparison means `"9.0" > "10.0"` is `True` (compares char "9" > "1"). Version `9.0` would be incorrectly skipped as "newer". Same issue on line 830 (`secondary_version < tool_version`).

**Fix**: Use tuple-based numeric comparison: `tuple(int(x) for x in v.split("."))`.

### BUG-2: `_resolve_detected_path_tokens` only handles `/**/*.cs` suffix pattern (copier.py:325-328)
**Severity**: Medium | **Introduced by**: This commit

```python
if stripped.startswith("paths:"):
    value = stripped[len("paths:"):].strip().strip("\"'")
    if not value or value.endswith("/**/*.cs") and value.startswith("/**/*.cs"):
        continue
```

When a token resolves to empty string (missing key), the regex leaves the suffix intact (e.g., `paths: "/**/*.cs"`). The filter only removes lines where the entire value equals `/**/*.cs`. If a skill used a different pattern, the empty-resolved path would survive and break skill activation. The `and` also has operator precedence issues.

**Fix**: After resolving tokens, check if any `${detected_paths.` tokens remained unresolved or resulted in a bare glob pattern, and remove those paths lines.

### BUG-3: `copy_profile()` signature mismatch vs. contract (copier.py:532-537)
**Severity**: Low | **Introduced by**: This commit

Contract specifies 4 params; implementation adds `package_dir: Path` as required. Not a runtime bug since all callers pass it, but it's a contract deviation. Same for `copy_hook()` and `deploy_to_linked_repos()`.

---

## ISSUES INTRODUCED BY THIS COMMIT

### ISSUE-1: `configure()` doesn't call `deploy_to_linked_repos()` (cli.py)
**Severity**: High | **Spec Violation**: FR-008, FR-009, FR-010, FR-011

The spec (FR-008) says: "During `configure`, when repos are linked, tool MUST deploy the full tooling stack to each initialized secondary repo." The contract (`cli-changes.md`) explicitly lists `deploy_to_linked_repos()` as a new step in `configure()`.

The implementation deploys profiles and hooks locally but **never calls `deploy_to_linked_repos()`**. The function exists in `copier.py` but is never imported in `cli.py`.

### ISSUE-2: `upgrade()` doesn't call `deploy_to_linked_repos()` (cli.py)
**Severity**: High | **Spec Violation**: FR-012

Same as ISSUE-1 but for `upgrade()`. The contract says upgrade should call `deploy_to_linked_repos()` with branch `chore/dotnet-ai-kit-upgrade-{version}`.

### ISSUE-3: `deploy_to_linked_repos()` doesn't deploy rules, agents, or skills (copier.py:784-804)
**Severity**: High | **Spec Violation**: FR-008

The spec says "deploy the full tooling stack (profiles, rules, agents, skills)." The implementation only deploys profiles and hooks — missing `copy_rules()`, `copy_agents()`, `copy_skills()`, `copy_commands()`.

### ISSUE-4: Lint violations — 3 lines over 100 chars (cli.py:440, 930, 948)
**Severity**: Low

Three `E501` line-too-long errors introduced by this commit.

### ISSUE-5: Duplicate `import yaml` / `from dotnet_ai_kit.copier import ...` inside functions (cli.py)
**Severity**: Low | **Style**

`yaml` is imported inside try blocks at lines 399, 874, 939, 1418. `copy_profile` and `copy_hook` are imported inside loops at lines 946, 958, 1427, 1444. Should be at function top level, not repeated inside loops/try blocks.

---

## TEST COVERAGE GAPS

### GAP-1: No test for `role: testing` agent transformation
The `test-engineer` agent uses `role: testing` but no test verifies this mapping produces no `disallowedTools`.

### GAP-2: No test for `.NET file scope filter in prompt` (required by T062)
The hook tests use a stub template that lacks the real file extension filter.

### GAP-3: No test for "hook not deployed for non-claude tools" (required by T062)
The `copy_hook()` function doesn't check tool name — it's the caller's responsibility. No test verifies this boundary.

### GAP-4: No test for "older version upgraded" vs "same version deployed" distinction (required by T067)
`test_deploy_to_initialized_repo_succeeds` asserts `status in ("deployed", "upgraded")` without testing each case.

### GAP-5: No test verifying git branch creation arguments (required by T067)
No assertion checks `subprocess.run` was called with the expected branch name.

### GAP-6: No line count validation of actual profile files
Task T020 says to test "all profiles under 100 lines." Only dict size is checked, not real file line counts.

### GAP-7: No CLI integration tests for profile/hook/multi-repo deployment
`configure()` and `upgrade()` now deploy profiles and hooks, but `test_cli.py` was not updated.

---

## PRE-EXISTING ISSUES (Not Caused by This Commit)

### PRE-1: `test_cli.py` line 518 — lint error (E501: 102 chars)
### PRE-2: `test_cli.py` line 1179 — lint error (E501: 101 chars)
### PRE-3: `test_models.py` line 140 — lint error (E501: 113 chars)

---

## SPEC COMPLIANCE SUMMARY

| Requirement | Status | Notes |
|---|---|---|
| FR-001: 12 profiles | PASS | All 12 created |
| FR-002: Profiles under 100 lines | PASS | Verified but not in tests |
| FR-003: Deploy ONE matching profile | PASS | `copy_profile()` correct |
| FR-004: Generic fallback | PASS | On low confidence or missing type |
| FR-005: Works for all AI tools | PASS | Cross-tool via AGENT_CONFIG |
| FR-008: Deploy to secondary repos | **FAIL** | `deploy_to_linked_repos()` not called from CLI |
| FR-009: Check initialization | PASS | In `deploy_to_linked_repos()` |
| FR-010: Version check | **PARTIAL** | Logic exists but uses string comparison (BUG-1) |
| FR-011: Write linked_from | PASS | In `deploy_to_linked_repos()` |
| FR-012: Upgrade re-deploys | **FAIL** | `deploy_to_linked_repos()` not called from upgrade() |
| FR-018: PreToolUse hook | PASS | `copy_hook()` correct |
| FR-019: Only .NET files | PASS | In template, not tested |
| FR-020: Static baked-in prompt | PASS | Constraints embedded at deploy time |
| FR-021: No hooks for non-Claude | PASS | CLI guards this |
| FR-022: Universal frontmatter | PASS | All 13 agents updated |
| FR-023: Transform during deploy | PASS | AGENT_FRONTMATTER_MAP works |
| FR-026: Detected paths tokens | PASS | copy_skills() resolves tokens |
| FR-030: Context fork commands | PASS | review/verify/analyze updated |
| SC-010: All 6 test files pass | PASS | 60/60 tests green |
