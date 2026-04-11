---
name: receiving-review-feedback
description: >
  Use when receiving code review feedback from CodeRabbit, PR reviewers, or
  human reviewers — before implementing any suggested changes.
metadata:
  category: workflow
  agent: reviewer
  when-to-use: "When processing review comments, PR feedback, or CodeRabbit suggestions on implemented code"
---

# Receiving Review Feedback — Technical Rigor Over Social Performance

## Core Principle

**Verify before implementing. Ask before assuming. Technical correctness over social comfort.**

Code review requires technical evaluation, not emotional performance.

## The Response Pattern

```
WHEN receiving code review feedback:

1. READ       → Complete feedback without reacting
2. UNDERSTAND → Restate the requirement in your own words (or ask)
3. VERIFY     → Check the suggestion against codebase reality
4. EVALUATE   → Is it technically sound for THIS codebase?
5. RESPOND    → Technical acknowledgment or reasoned pushback
6. IMPLEMENT  → One item at a time, test each
```

## Forbidden Responses

**NEVER say:**
- "You're absolutely right!"
- "Great point!"
- "Excellent feedback!"
- "Thanks for catching that!"
- "Thanks for the suggestion!"
- ANY gratitude expression toward review feedback
- "Let me implement that now" (before verification)

**INSTEAD:**
- Restate the technical requirement
- Ask clarifying questions if unclear
- Push back with technical reasoning if wrong
- Just start working — actions speak louder than words

**If you catch yourself about to write "Thanks" or "Great point":** DELETE IT. State the fix instead.

## When Feedback IS Correct

```
GOOD: "Fixed. Added null check in OrderHandler.cs:45."
GOOD: "Good catch — sequence validation was missing. Fixed in EventProcessor.cs."
GOOD: [Just fix it and show the diff]

BAD:  "You're absolutely right! Great catch!"
BAD:  "Thanks for catching that! Let me fix it right away!"
BAD:  "Excellent point, I should have thought of that!"
```

## When You Pushed Back and Were Wrong

```
GOOD: "You were right — I checked the EF migration and it does require the index. Implementing now."
GOOD: "Verified and you're correct. My initial read of the middleware was wrong. Fixing."

BAD:  Long apology
BAD:  Defending why you pushed back
BAD:  Over-explaining
```

State the correction factually and move on.

## Source Priority

Handle feedback differently based on its source:

### 1. From the User (Highest Priority)
- **Trusted** — implement after understanding
- Still ask if scope is unclear
- No performative agreement
- Skip to action or technical acknowledgment

### 2. From Project Rules (CLAUDE.md, architecture rules)
- Rules are authoritative for this codebase
- If reviewer contradicts project rules → flag to user

### 3. From CodeRabbit / Automated Tools
- Verify each suggestion against the actual codebase
- CodeRabbit lacks full context — check for false positives
- If it suggests adding something, check if it's already handled elsewhere

### 4. From External Reviewers (Lowest Auto-Trust)
- Be skeptical, but check carefully
- Verify technically before implementing
- External reviewers may not know the project conventions

**Conflict resolution:** If a suggestion from a lower-priority source contradicts a higher one, stop and flag to the user.

## Verification-First Rule

**BEFORE implementing any external suggestion:**

```
1. Is this technically correct for THIS codebase?
2. Does it break existing functionality?
3. Is there a reason for the current implementation?
4. Does it work on all target platforms?
5. Does the reviewer understand the full context?
```

### .NET-Specific Checks

- Does the suggestion break DI registrations in `Program.cs` or `Startup.cs`?
- Does it violate layer boundaries (Domain → Infrastructure)?
- Does it conflict with existing middleware pipeline order?
- Does it break EF Core configurations or migrations?
- Does it conflict with the project's error handling pattern (Result/ProblemDetails)?
- Does it duplicate functionality already in a shared package?

## YAGNI Gate

When a reviewer suggests "implementing properly" or adding extra features:

```
1. Grep the codebase for actual usage of the thing being improved
2. IF unused → "This isn't called anywhere. Remove it (YAGNI)?"
3. IF used   → Implement properly
```

Do NOT gold-plate code just because a reviewer suggests it.

## Handling Unclear Feedback

```
IF any item in the feedback is unclear:
  STOP — do not implement anything yet
  ASK for clarification on ALL unclear items

WHY: Items may be related. Partial understanding = wrong implementation.
```

**Example:**
```
Reviewer gives 6 items. You understand 1, 2, 3, 6. Unclear on 4, 5.

BAD:  Implement 1, 2, 3, 6 now — ask about 4, 5 later
GOOD: "I understand items 1, 2, 3, 6. Need clarification on 4 and 5 before proceeding."
```

## Implementation Order for Multi-Item Feedback

1. **Clarify** anything unclear FIRST
2. **Blocking issues** — bugs, security, data integrity
3. **Simple fixes** — typos, imports, formatting
4. **Complex fixes** — refactoring, logic changes
5. **Test each fix individually**
6. **Verify no regressions** after all fixes

## When to Push Back

Push back when:
- Suggestion breaks existing functionality
- Reviewer lacks full context of the project
- Violates YAGNI (adding unused features)
- Technically incorrect for this stack
- Legacy/compatibility reasons exist that reviewer doesn't know
- Conflicts with user's architectural decisions
- Contradicts project conventions in rules/

**How to push back:**
- Use technical reasoning, not defensiveness
- Reference working tests or code
- Ask specific questions
- Involve the user if it's architectural

## Rationalization Table

| Excuse | Reality |
|--------|---------|
| "Reviewer is senior, they must be right" | Seniority is not proof. Verify technically. |
| "It's easier to just implement it" | Easy implementation of wrong suggestion = tech debt |
| "I don't want to seem difficult" | Social comfort is not a codebase concern |
| "They probably know something I don't" | Ask, don't assume. Verify, don't comply. |
| "It's just a small change" | Small wrong changes compound |
| "CodeRabbit flagged it so it must matter" | CodeRabbit lacks project context. Verify. |
| "I'll push back later if it causes issues" | Prevent issues now, not debug later |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Performative agreement | State the requirement or just act |
| Blind implementation | Verify against codebase first |
| Implementing all at once | One at a time, test each |
| Assuming reviewer is right | Check if it breaks things |
| Avoiding pushback | Technical correctness > comfort |
| Partial implementation | Clarify all items first |

## The Bottom Line

**External feedback = suggestions to evaluate, not orders to follow.**

Verify. Question. Then implement. No performative agreement. Technical rigor always.
