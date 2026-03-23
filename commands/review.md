---
description: "Review implemented code against standards with optional CodeRabbit integration"
---

# /dotnet-ai.review — Standards Review

You are an AI coding assistant executing the `/dotnet-ai.review` command.
Your job is to review implemented code against coding standards and report findings.

## Input

Flags: `--dry-run` (preview review scope), `--verbose` (diagnostic output),
       `--auto-fix` (apply safe auto-fixes), `--skip-coderabbit` (skip CodeRabbit)

## Load Specialist Agent

Read `agents/reviewer.md` for review standards and quality checks. Load all skills listed in the agent's Skills Loaded section.

## Step 1: Detect Changes

1. Find the active feature in `.dotnet-ai-kit/features/`.
2. Detect mode: **generic** or **microservice**.
3. Identify affected repos/directories:
   - Generic: current repo, `git diff` against base branch.
   - Microservice: each repo listed in `service-map.md`, `git diff` per repo.
4. If no changes detected: "No changes to review. Run /dotnet-ai.implement first."
5. If `--verbose`, print: "Reviewing changes in {N} repos, {M} files changed."

## Step 2: Load Skills

- Read `skills/quality/review-checklist/SKILL.md` for review criteria
- Read `skills/quality/code-analysis/SKILL.md` for code analysis patterns
- Read `skills/core/csharp-idioms/SKILL.md` for C# best practices

## Step 3: Standards Review

For each affected repo, review changed files against these checks:

### Check 1: Naming Conventions
- Classes, methods, properties follow project conventions (PascalCase)
- File names match class names
- Namespace matches folder structure
- Severity: MEDIUM for violations

### Check 2: Architecture Boundary Violations
- No Domain layer referencing Infrastructure
- No cross-layer shortcuts bypassing Application
- Service registrations in correct location
- Severity: HIGH for violations

### Check 3: Localization
- No hardcoded user-facing strings (if project uses `Phrases.resx` pattern)
- All display text references resource files
- Skip if project does not use localization
- Severity: MEDIUM for violations

### Check 4: Error Handling
- No swallowed exceptions (empty catch blocks)
- Appropriate use of Result pattern or ProblemDetails
- CancellationToken propagated in async methods
- No `async void` methods (except event handlers)
- Severity: HIGH for swallowed exceptions, MEDIUM for missing cancellation

### Check 5: Testing
- New public classes have corresponding test files
- Test methods follow project naming convention
- Test coverage for handlers and services
- Severity: MEDIUM for missing tests

### Check 6: Security
- No hardcoded secrets, connection strings, or API keys
- Parameterized queries (no string concatenation for SQL)
- Input validation on endpoints
- Authorization attributes on endpoints
- Severity: CRITICAL for hardcoded secrets, HIGH for missing validation

### Check 7: Event Structure (microservice mode)
- Events follow naming conventions ({Entity}{Past-tense-verb})
- Event data includes required fields (aggregate ID, timestamp)
- Event handlers are idempotent
- Severity: HIGH for structural issues

### Check 8: Performance
- CancellationToken passed through async call chains
- Pagination on list endpoints
- No N+1 query patterns
- Appropriate use of `AsNoTracking()` for read queries
- Severity: MEDIUM for performance issues

## Step 4: CodeRabbit Integration (Optional)

Unless `--skip-coderabbit` is set:

1. Check if `coderabbit` CLI is installed: `which coderabbit` or `coderabbit --version`.
2. If available:
   - Run `coderabbit review` on each affected repo.
   - Parse CodeRabbit output and merge findings with standards review.
   - Deduplicate: if both catch the same issue, keep the more detailed finding.
3. If not available:
   - Print: "CodeRabbit CLI not found. Install: https://coderabbit.ai/cli"
   - Continue with standards review only.

## Step 5: Auto-Fix (if --auto-fix)

**Safe fixes** (apply automatically):
- Remove unused `using` statements
- Add missing `sealed` keyword on classes with no inheritors
- Apply file-scoped namespaces (if .editorconfig requires)
- Fix formatting issues (whitespace, indentation)
- Add missing XML doc comment stubs on public members

**Unsafe fixes** (require user approval — list but do not apply):
- Logic changes, error handling modifications
- Architecture restructuring, dependency additions
- Adding/removing authorization attributes

If `--auto-fix`:
1. Apply all safe fixes.
2. List unsafe fixes and ask: "Apply these {N} changes? [y/N/select]"
3. Report what was auto-fixed.

## Step 6: Output Report

Generate report per repo. Save to `review.md` in the feature directory:

```markdown
# Review Report: {Feature Name}

**Date**: {DATE} | **Mode**: {mode}

## {Repo Name} ({PASS|NEEDS FIXES})
### Standards Review
- {check name}: {PASS|{N} violations}
  - {finding description} [{severity}]

### CodeRabbit (if run)
- {N} suggestions, {M} warnings

### Auto-Fixed (if --auto-fix)
- {list of applied fixes}

## Summary
- Total findings: {N}
- CRITICAL: {count} | HIGH: {count} | MEDIUM: {count} | LOW: {count}
- Auto-fixed: {count}
- Remaining: {count}
```

Print summary to terminal:
```
Review complete for {NNN}-{short-name}.
  {Repo}: {PASS|NEEDS FIXES} ({N} findings)
  ...

{If auto-fix applied}: Auto-fixed {N} safe issues.
{If findings remain}: Review review.md for details.

Next: /dotnet-ai.verify    (run verification pipeline)
```

## Dry-Run Behavior

When `--dry-run` is active:
- Print which repos and files WOULD be reviewed
- Print which checks WOULD run
- Do NOT analyze code or generate report
- Prefix output with `[DRY-RUN]`

## Error Handling

- No changes to review: direct to `/dotnet-ai.implement`
- Git not available: "Cannot detect changes without git."
- CodeRabbit fails: continue with standards review, note the failure
