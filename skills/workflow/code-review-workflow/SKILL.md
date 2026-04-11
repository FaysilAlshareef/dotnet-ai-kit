---
name: code-review-workflow
description: >
  Use when performing code review on completed implementation, before merge.
metadata:
  category: workflow
  agent: reviewer
  when-to-use: "When performing code reviews or configuring automated review workflows"
---

# Code Review Workflow — Checklist & Automation

## Core Principles

- Every PR gets reviewed against a standards checklist
- CodeRabbit provides automated initial review
- Human review focuses on design, business logic, and cross-cutting concerns
- Severity ratings guide review priority (Critical, Major, Minor, Info)
- Review feedback is actionable and specific

## Key Patterns

### Review Checklist Categories

```markdown
## Architecture & Design
- [ ] Follows established architecture patterns (CQRS, event sourcing)
- [ ] Proper separation of concerns (handler, aggregate, entity)
- [ ] No business logic in infrastructure layer
- [ ] Domain invariants enforced in aggregate

## Event Sourcing (Microservice Mode)
- [ ] Events are immutable (no removing fields)
- [ ] Sequence numbers are correct (start at 1, increment by 1)
- [ ] Event types registered in EventDeserializer
- [ ] Outbox pattern used for reliable publishing
- [ ] Query handlers are idempotent

## Code Quality
- [ ] Follows coding conventions (sealed, private setters, naming)
- [ ] No unused code or dead imports
- [ ] Async methods have Async suffix
- [ ] CancellationToken propagated through the call chain
- [ ] Resource strings used (no hardcoded messages)

## Testing
- [ ] Unit tests for business logic
- [ ] Integration tests for handlers
- [ ] Fakers for test data generation
- [ ] Edge cases covered (null, empty, boundary values)

## Security
- [ ] Authorization policies on endpoints
- [ ] No secrets in code or config
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)

## Performance
- [ ] AsNoTracking on read queries
- [ ] Appropriate indexes for new query patterns
- [ ] No N+1 queries
- [ ] Pagination on list endpoints
```

### Severity Ratings

```
Critical: Must fix before merge
  - Security vulnerability
  - Data integrity issue
  - Breaking change without migration

Major: Should fix before merge
  - Missing validation
  - Missing error handling
  - Performance concern on hot path

Minor: Nice to fix, can be follow-up
  - Naming improvement
  - Missing test case
  - Documentation gap

Info: Educational, no action required
  - Alternative approach suggestion
  - Pattern explanation
  - Future improvement idea
```

### CodeRabbit Configuration

```yaml
# .coderabbit.yaml
reviews:
  profile: assertive
  request_changes_workflow: true

chat:
  auto_reply: true

language: en

tools:
  dotnet:
    enabled: true
```

### Review Comment Format

```markdown
**[Major]** Missing sequence check in event handler

The `OrderUpdatedHandler` doesn't validate the event sequence before applying.
This could lead to out-of-order event processing.

```csharp
// Current (missing check)
order.Apply(@event);

// Should be
if (@event.Sequence <= order.Sequence) return true;
if (@event.Sequence != order.Sequence + 1) return false;
order.Apply(@event);
```
```

## The Iron Law

```
EVERY REVIEW HAS TWO PASSES: SPEC COMPLIANCE FIRST, THEN CODE QUALITY
```

Pass 1 catches "built the wrong thing." Pass 2 catches "built the right thing badly." Never skip Pass 1.

## Two-Stage Review Process

### Pass 1: Spec Compliance
- Compare implementation against spec/brief requirements
- Flag missing requirements (incomplete)
- Flag extra features not in spec (scope creep)
- Flag behavioral mismatches
- **Verdict: Spec-Compliant or Not**

### Pass 2: Code Quality (only after Pass 1 approves)
- Run the review checklist categories
- Check architecture, security, performance, testing
- Apply severity ratings
- **Verdict: Ready to Merge, Needs Fixes, or Rejected**

**Do NOT start Pass 2 if Pass 1 has open issues.** Fix spec compliance first.

## Rationalization Table

| Excuse | Reality |
|--------|---------|
| "The code looks good, skip spec check" | Good code for wrong requirements is still wrong. |
| "Spec is informal, close enough counts" | Close enough is not done. Check each requirement. |
| "I'll combine both passes for efficiency" | Combined passes miss spec issues. Separate them. |
| "Tests pass so it meets the spec" | Tests check code behavior, not spec alignment. |
| "It's a minor feature, one pass is fine" | Minor features still need spec compliance. |

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Approving without reading changes | Review every file changed |
| Vague feedback ("looks wrong") | Specific feedback with code examples |
| Blocking on style preferences | Use Minor severity for style issues |
| Skipping security review | Always check auth, validation, secrets |

## Detect Existing Patterns

```bash
# Find CodeRabbit config
find . -name ".coderabbit.yaml" -o -name ".coderabbit.yml"

# Find review templates
find . -name "PULL_REQUEST_TEMPLATE*" -path ".github/*"

# Check for review automation
find .github/workflows -name "*review*" -o -name "*lint*"
```

## Adding to Existing Project

1. **Use the existing review checklist** if one exists
2. **Configure CodeRabbit** via `.coderabbit.yaml` in repo root
3. **Follow severity conventions** for review comments
4. **Add PR template** in `.github/PULL_REQUEST_TEMPLATE.md`
5. **Review cross-service impact** for microservice changes
