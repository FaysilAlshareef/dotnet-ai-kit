---
name: verification-gate
description: >
  Use when about to claim work is complete, fixed, passing, or ready — before
  committing, creating PRs, or moving to the next task. Requires running
  verification commands and confirming output before making any success claims.
metadata:
  category: workflow
  when-to-use: "Before any completion claim, commit, PR, or task transition"
---

# Verification Gate — Evidence Before Claims

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command **in this message**, you cannot claim it passes.

**Violating the letter of this rule is violating the spirit of this rule.**

## The Gate

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY  → What command proves this claim?
2. RUN       → Execute the FULL command (fresh, not cached)
3. READ      → Full output — check exit code, count failures
4. VERIFY    → Does the output confirm the claim?
   YES → State the claim WITH the evidence
   NO  → State actual status with evidence
5. ONLY THEN → Make the claim
```

Skip any step = false claim, not efficiency.

## .NET Verification Commands

| Claim | Required Command | Not Sufficient |
|-------|-----------------|----------------|
| "Build succeeds" | `dotnet build` exit 0 | "Linter passed", "code looks right" |
| "Tests pass" | `dotnet test` with 0 failures | Previous run, "should pass" |
| "No warnings" | `dotnet build -warnaserror` exit 0 | Build passing (warnings hidden) |
| "Lint clean" | `ruff check` or analyzer output: 0 errors | Partial check, extrapolation |
| "Bug fixed" | Test reproducing the original symptom passes | "Code changed, assumed fixed" |
| "Migration works" | `dotnet ef database update` exit 0 | "Schema looks correct" |
| "Endpoint works" | HTTP request + response validation | "Controller compiles" |
| "Requirements met" | Line-by-line checklist against spec | "Tests passing" |

## Forbidden Phrases

These phrases are **never acceptable** without preceding verification output:

- "Should work now"
- "Should pass"
- "Looks correct"
- "Seems fine"
- "That should fix it"
- "I'm confident this works"
- "Done!"
- "Perfect!"
- "Great, that's complete"
- Any variation implying success without evidence

## Rationalization Table

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence is not evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter does not check compilation |
| "Build passed" | Build does not check test logic |
| "Tests passed last time" | Last time is not this time |
| "I only changed one line" | One line can break everything |
| "The code is simple" | Simple code still needs verification |
| "I'm running out of context" | Verification is never optional |
| "Partial check is enough" | Partial proves nothing about the whole |
| "Different words so rule doesn't apply" | Spirit over letter, always |

## Red Flags — STOP

If you catch yourself:
- Using "should", "probably", "seems to", "likely"
- Expressing satisfaction before running commands
- About to commit or push without verification
- About to mark a task complete without evidence
- Trusting a subagent's success report without checking
- Relying on a previous verification run
- Thinking "just this once"
- **ANY wording implying success without having run verification**

**All of these mean: STOP. Run the command. Read the output. Then speak.**

## Multi-Step Verification

When implementation touches multiple areas, verify each:

```
1. dotnet build         → Compiles?
2. dotnet test          → All green?
3. Review test output   → Expected count? No skipped?
4. Check spec           → Each requirement has evidence?
```

Do NOT bundle: "build and tests pass" — run each, report each.

## After Agent Delegation

When a subagent reports success:
1. Check the actual diff (`git diff`)
2. Run `dotnet build` yourself
3. Run `dotnet test` yourself
4. THEN report the status

Agent reports are claims. Claims need verification.

## The Bottom Line

**No shortcuts. Run the command. Read the output. THEN claim the result.**
