---
name: systematic-debugging
description: >
  Use when encountering any bug, test failure, build error, or unexpected
  behavior — before proposing fixes or making changes.
metadata:
  category: workflow
  when-to-use: "When any test fails, build breaks, or behavior is unexpected during development"
---

# Systematic Debugging — Root Cause Before Fixes

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

**Violating the letter of this process is violating the spirit of debugging.**

## When to Use

Use for ANY technical issue:
- Test failures (`dotnet test` reports failures)
- Build errors (`dotnet build` fails)
- Runtime exceptions
- Unexpected behavior
- Performance problems
- EF Core migration failures
- DI resolution errors
- Integration test failures

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried one fix that didn't work
- You don't fully understand the issue

## The Four Phases

Complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

**1. Read Error Messages Carefully**
- Read the FULL stack trace, not just the first line
- Note exact file paths, line numbers, error codes
- Check inner exceptions (`---> System.InvalidOperationException`)
- Read build warnings — they often hint at the real problem

**2. Reproduce Consistently**
- Can you trigger it reliably with `dotnet test --filter "TestName"`?
- What are the exact steps?
- Does it happen every time or intermittently?
- If flaky → gather more data, don't guess

**3. Check Recent Changes**
- `git diff` — what changed since it last worked?
- `git log --oneline -10` — recent commits
- New NuGet packages? Config changes? Migration changes?

**4. Gather Evidence in Multi-Layer Systems**

For .NET solutions with multiple projects/layers:
```
For EACH layer boundary:
  - What data enters this layer?
  - What data exits this layer?
  - Are DI registrations correct at each level?
  - Is configuration propagating correctly?

Run once to gather evidence showing WHERE it breaks.
THEN investigate that specific layer.
```

**5. Trace Data Flow**
- Where does the bad value originate?
- What called this method with the bad value?
- Trace UP the call stack until you find the source
- Fix at the source, not the symptom

### Phase 2: Pattern Analysis

**1. Find Working Examples**
- Is there similar working code in the same solution?
- How do other handlers/services/controllers do this?

**2. Compare Against References**
- If implementing a pattern (CQRS, event sourcing, repository), compare against the existing project implementation — not a generic tutorial
- Read the project's conventions in `rules/`

**3. Identify Differences**
- What's different between the working code and the broken code?
- List every difference, however small
- Don't assume "that can't matter"

### Phase 3: Hypothesis Testing

**1. Form Single Hypothesis**
- "I think X is the root cause because Y"
- Be specific, not vague
- Write it down

**2. Test Minimally**
- Make the SMALLEST possible change to test the hypothesis
- One variable at a time
- Don't fix multiple things at once

**3. Verify**
- Did it work? → Phase 4
- Didn't work? → Form NEW hypothesis from new evidence
- DON'T stack more fixes on top

### Phase 4: Implementation

**1. Create Failing Test**
- Write a test that reproduces the bug
- Verify it fails (`dotnet test --filter "BugReproTest"`)
- This test prevents regression

**2. Implement Single Fix**
- Address the root cause identified in Phase 1-3
- ONE change at a time
- No "while I'm here" improvements

**3. Verify Fix**
- Failing test now passes?
- All other tests still pass?
- `dotnet build` clean?
- Issue actually resolved?

**4. If Fix Doesn't Work — Count Your Attempts**
- If fewer than 3 attempts: return to Phase 1 with new information
- **If 3+ fixes have failed: STOP and question the architecture**

### The 3-Fix Escalation Rule

**If 3 or more fixes have failed, the problem is probably architectural.**

Signals of an architectural problem:
- Each fix reveals new shared state or coupling
- Fixes require "massive refactoring" to implement
- Each fix creates new symptoms elsewhere
- You're patching around the same area repeatedly

**STOP and question fundamentals:**
- Is this pattern fundamentally sound for this use case?
- Should the data model change instead of the query?
- Is the layering correct, or is the abstraction leaking?
- Should this be a different type of component entirely?

**.NET-Specific Escalation Examples:**
- 3+ EF Core migration failures → question the data model, not the migration script
- 3+ DI resolution errors → question the service lifetime design, not the registration
- 3+ middleware pipeline issues → question the pipeline order/architecture, not individual middleware
- 3+ serialization failures → question the DTO design, not the serializer config

**Discuss with the user before attempting more fixes.**

## Rationalization Table

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I see the problem, let me fix it" | Seeing symptoms is not understanding root cause. |
| "The error message tells me what to fix" | Error messages show symptoms, not always causes. |
| "I'll write a test after confirming fix" | Untested fixes don't stick. Test first. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "One more fix attempt" (after 2+) | 3+ failures = architectural problem. Stop. |
| "It worked in another project" | This project has different constraints. Investigate this context. |

## Red Flags — STOP and Follow Process

- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- Proposing solutions before tracing the data flow
- "One more fix attempt" (when already tried 2+)
- Each fix reveals a new problem in a different place
- "Here are the main problems: [lists fixes without investigation]"

**All of these mean: STOP. Return to Phase 1.**

## Quick Reference

| Phase | Key Activities | Done When |
|-------|---------------|-----------|
| **1. Root Cause** | Read errors, reproduce, check changes, trace data | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare differences | Know what's different |
| **3. Hypothesis** | Form theory, test one variable | Confirmed or new theory |
| **4. Implementation** | Create test, fix, verify | Bug resolved, all tests green |

## The Bottom Line

**Find the root cause. Then fix it. Never guess.**
