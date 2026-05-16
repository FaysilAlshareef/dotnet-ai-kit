---
description: "Reviews code against standards and conventions. Use when implementation is complete and ready for quality check."
---

# /dotnet-ai.review — Standards Review

You are an AI coding assistant executing the `/dotnet-ai.review` command.
Your job is to review implemented code against coding standards and report findings.

## Usage

```
/dotnet-ai.review $ARGUMENTS
```

**Examples:**
- (no args) — Review current feature changes against standards
- `--verbose` — Show detailed check output per category

## Input

Flags: `--dry-run` (preview review scope), `--verbose` (diagnostic output),
       `--auto-fix` (apply safe auto-fixes), `--skip-coderabbit` (skip CodeRabbit)

## Load Specialist Agent

Read `agents/reviewer.md` for review standards and quality checks. Bounded skill selection (FR-012): keep one architect agent for the project type loaded, load at most 2 task-specific skills initially, and run MCP queries (codebase-memory-mcp) before broad file reads.

When checking project-specific conventions, read `.dotnet-ai-kit/memory/conventions.md` and `.dotnet-ai-kit/memory/interfaces.md` rather than the full constitution (FR-024).

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
- Read `skills/workflow/verification-gate/SKILL.md` — every review finding must be backed by evidence
- Read `skills/workflow/receiving-review-feedback/SKILL.md` — when processing CodeRabbit or external feedback

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

### Check 9: Brief Compliance (microservice secondary repos)
When reviewing a secondary repo, look for feature briefs in `.dotnet-ai-kit/briefs/*/` matching the current feature. Load the brief and compare actual changes (`git diff`) against:
- Brief's "Required Changes" — flag changes not listed in the brief (scope creep)
- Brief's "Tasks" — flag brief items with no corresponding code changes (incomplete)
- Severity: MEDIUM for scope creep, HIGH for missing brief items

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

Safe (auto-apply): remove unused `using`s, add `sealed`, file-scoped namespaces, formatting, XML-doc stubs. Unsafe (list, don't apply): logic, error-handling, architecture, authorization.

If `--auto-fix`: apply safe fixes; `dotnet build` to verify; record each in `undo-log.md`; list unsafe fixes and ask "Apply these {N} changes? [y/N/select]".

## Step 6: Output Report

Write `review.md`:

```markdown
# Review Report: {Feature}
**Date**: {DATE} | **Mode**: {mode}
## {Repo} ({PASS|NEEDS FIXES})
- {check}: {PASS|N violations}
  - {finding} [{severity}]
## Summary — CRITICAL/HIGH/MEDIUM/LOW counts, auto-fixed, remaining
```

Print: `Review complete for {NNN}-{short-name}.` per-repo PASS/FIXES + counts. Next: `/dotnet-ai.verify`.

## Dry-Run / Errors

## Error Handling

- No changes to review: direct to `/dotnet-ai.implement`
- Git not available: "Cannot detect changes without git."
- CodeRabbit fails: continue with standards review, note the failure

## MCP-first (FR-021 / FR-022)

Graph/dependency/ownership/architecture questions: query `codebase-memory-mcp` first; use `csharp-ls` for symbol-precise lookups; `grep`/file reads only as last resort.

If MCP is unavailable, emit exactly:
> MCP unavailable: codebase-memory-mcp is not connected or below >=0.6.1; falling back to csharp-ls + grep/read.

