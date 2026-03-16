---
name: review-checklist
description: >
  Standards review categories and severity ratings for code review.
  Covers architecture, security, performance, and testing review criteria.
  Trigger: review checklist, standards, code quality, review criteria.
category: quality
agent: reviewer
---

# Review Checklist — Standards & Severity Ratings

## Core Principles

- Consistent review criteria across all code changes
- Severity-based prioritization: Critical > Major > Minor > Info
- Category-specific checklists for different aspects of code
- Automated checks complement manual review
- Review feedback is actionable with specific suggestions

## Key Patterns

### Review Categories

#### 1. Architecture & Design

```markdown
Critical:
- [ ] Correct layer placement (domain logic not in infrastructure)
- [ ] Dependency direction (inner layers don't reference outer)
- [ ] Aggregate boundaries respected (no cross-aggregate transactions)

Major:
- [ ] Single Responsibility Principle followed
- [ ] Proper use of abstractions (interfaces, not concrete types)
- [ ] No circular dependencies between projects

Minor:
- [ ] Consistent with existing patterns in the project
- [ ] Appropriate use of sealed classes
- [ ] File-scoped namespaces used
```

#### 2. Event Sourcing (Microservice)

```markdown
Critical:
- [ ] Events are immutable (no removed fields)
- [ ] Sequence numbers correct (start 1, increment 1)
- [ ] Outbox pattern used for publishing

Major:
- [ ] Event types registered in EventDeserializer
- [ ] Query handlers are idempotent
- [ ] Sequence checking in event handlers

Minor:
- [ ] Event data uses records (not classes)
- [ ] EventType constants match class names
- [ ] JSON serialization uses Newtonsoft (project convention)
```

#### 3. Security

```markdown
Critical:
- [ ] No secrets in source code or config files
- [ ] Authorization on all endpoints
- [ ] Input validation on all external inputs
- [ ] SQL injection prevention

Major:
- [ ] Proper authentication scheme configured
- [ ] Sensitive data not logged
- [ ] CORS properly configured
- [ ] Rate limiting on public endpoints

Minor:
- [ ] Security headers configured
- [ ] Audit logging for sensitive operations
```

#### 4. Performance

```markdown
Critical:
- [ ] No N+1 query patterns
- [ ] Pagination on all list endpoints

Major:
- [ ] AsNoTracking on read queries
- [ ] Appropriate database indexes for new queries
- [ ] No synchronous I/O in async code paths
- [ ] CancellationToken propagated

Minor:
- [ ] Select projection (not loading full entities)
- [ ] Compiled queries for hot paths
- [ ] Connection resiliency configured
```

#### 5. Testing

```markdown
Major:
- [ ] Unit tests for business logic
- [ ] Integration tests for handlers
- [ ] Edge cases covered (null, empty, boundary)

Minor:
- [ ] Test naming follows convention
- [ ] Fakers used for test data
- [ ] Assertion extensions for entity comparison
```

#### 6. Code Style

```markdown
Minor:
- [ ] Naming conventions followed (PascalCase, _camelCase)
- [ ] Async suffix on async methods
- [ ] Expression-bodied members where appropriate
- [ ] `is null` / `is not null` pattern
- [ ] Resource strings for user-facing messages
```

### Severity Decision Guide

```
Severity   | When to Use                              | Action Required
---------- | ---------------------------------------- | ---------------
Critical   | Security flaw, data corruption, breaking | Must fix before merge
Major      | Missing validation, performance issue     | Should fix before merge
Minor      | Style, naming, minor improvement          | Can be follow-up PR
Info       | Alternative approach, educational         | No action required
```

### PR Review Comment Template

```markdown
**[{Severity}]** {Brief description}

{Detailed explanation of the issue}

```csharp
// Suggestion
{code example if applicable}
```

{Link to relevant skill or documentation}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Reviewing only the diff | Understand the full context of changes |
| Blocking on style preferences | Use Minor severity for style |
| Not checking security | Always review auth, validation, secrets |
| Rubber-stamping approvals | Review every file meaningfully |
| Only finding problems | Acknowledge good patterns too |

## Detect Existing Patterns

```bash
# Find PR templates
find .github -name "PULL_REQUEST_TEMPLATE*"

# Find existing review documentation
find . -name "*review*" -path "*docs/*"
```

## Adding to Existing Project

1. **Adapt checklist** to project-specific patterns and conventions
2. **Add PR template** with checklist items in `.github/PULL_REQUEST_TEMPLATE.md`
3. **Configure automated checks** (linting, analyzers) in CI
4. **Train team** on severity ratings and review expectations
5. **Iterate on checklist** based on common issues found in reviews
