# Command Files Contract: Usage + Examples Pattern

**Phase**: 1 — Contracts
**Date**: 2026-04-04

Defines the exact Usage + Examples block format required for the 14 lifecycle/project commands that are missing these sections.

---

## Standard Pattern (8 lines)

```markdown
## Usage

```
/dotnet-ai.{name} $ARGUMENTS
```

**Examples:**
- (no args) — {primary use case}
- `--dry-run` — Preview without changes
```

The block goes immediately after the frontmatter description line and before the first `## Step` or `## Flow` section. It must stay within the ≤ 200 line budget.

---

## Per-Command Specification

For commands at or near the 200-line limit, trimming notes are provided.

### `analyze.md` (197 lines → trim 5, add 8 → 200 max)

```markdown
## Usage

```
/dotnet-ai.analyze $ARGUMENTS
```

**Examples:**
- (no args) — Analyze current feature against spec/plan/tasks
- `--verbose` — Show detailed check output per pass
```

**Trim**: Merge "Step 3: Pass A" + sub-steps into 2 lines; merge "Step 4: Pass B" similarly.

---

### `clarify.md` (185 lines → add 8 → 193)

```markdown
## Usage

```
/dotnet-ai.clarify $ARGUMENTS
```

**Examples:**
- (no args) — Clarify current feature spec
- `001` — Clarify feature 001 by ID
```

---

### `configure.md` (143 lines → add 8 → 151)

```markdown
## Usage

```
/dotnet-ai.configure $ARGUMENTS
```

**Examples:**
- (no args) — Interactive configuration wizard
- `--no-input --company Acme` — CI/CD non-interactive mode
- `--style short` — Switch to short command aliases only
```

---

### `detect.md` (146 lines → add 8 → 154)

```markdown
## Usage

```
/dotnet-ai.detect $ARGUMENTS
```

**Examples:**
- (no args) — Detect project type and architecture
- `--verbose` — Show detection signals and confidence breakdown
```

---

### `do.md` (179 lines → add 8 → 187)

```markdown
## Usage

```
/dotnet-ai.do $ARGUMENTS
```

**Examples:**
- `"Add order management"` — Full lifecycle: specify → plan → implement → review → PR
- `--dry-run "Add payments"` — Preview what would be built
```

---

### `implement.md` (196 lines → trim 4, add 8 → 200 max)

```markdown
## Usage

```
/dotnet-ai.implement $ARGUMENTS
```

**Examples:**
- (no args) — Execute all tasks from tasks.md on current feature
- `--dry-run` — Show task list without writing code
```

**Trim**: Merge "Step 5a/5b" branch logic into single step.

---

### `init.md` (117 lines → add 8 → 125)

```markdown
## Usage

```
/dotnet-ai.init $ARGUMENTS
```

**Examples:**
- `. --ai claude` — Initialize current directory for Claude Code
- `. --ai claude --type command` — Force command-service project type
- `. --ai claude --permissions standard` — Apply standard permissions during init
```

---

### `learn.md` (129 lines → add 8 → 137)

```markdown
## Usage

```
/dotnet-ai.learn $ARGUMENTS
```

**Examples:**
- `clean architecture` — Learn clean architecture patterns with examples
- `--tutorial` — Step-by-step tutorial for new developers
```

---

### `plan.md` (143 lines → add 8 → 151)

```markdown
## Usage

```
/dotnet-ai.plan $ARGUMENTS
```

**Examples:**
- (no args) — Generate implementation plan from current spec
- `--dry-run` — Preview plan structure without writing files
```

---

### `pr.md` (162 lines → add 8 → 170)

```markdown
## Usage

```
/dotnet-ai.pr $ARGUMENTS
```

**Examples:**
- (no args) — Create PRs for all affected repos in current feature
- `--dry-run` — Show PR details without creating them
```

---

### `review.md` (188 lines → add 8 → 196)

```markdown
## Usage

```
/dotnet-ai.review $ARGUMENTS
```

**Examples:**
- (no args) — Review current feature changes against standards
- `--verbose` — Show detailed check output per category
```

---

### `specify.md` (200 lines → trim 8, add 8 → 200 max)

```markdown
## Usage

```
/dotnet-ai.specify $ARGUMENTS
```

**Examples:**
- `"Add order management"` — Create spec for new feature
- (no args) — Resume existing feature or create new
- `--dry-run "Add payments"` — Preview spec path without writing
```

**Trim**: Merge Step 2 sub-steps (2a, 2b) into single step. Condense Step 6 quality checklist items from list to inline.

---

### `tasks.md` (200 lines → trim 8, add 8 → 200 max)

```markdown
## Usage

```
/dotnet-ai.tasks $ARGUMENTS
```

**Examples:**
- (no args) — Generate tasks.md from current plan
- `--dry-run` — Preview task structure without writing
```

**Trim**: Merge Step 3 sub-bullets (3a/3b/3c) into a single numbered step. Condense Step 5 phase-per-repo examples.

---

### `verify.md` (186 lines → add 8 → 194)

```markdown
## Usage

```
/dotnet-ai.verify $ARGUMENTS
```

**Examples:**
- (no args) — Run verification pipeline: build, test, lint
- `--dry-run` — Show what would be verified without running
```

---

## Budget Summary After Changes

| Command | Before | Δ | After | Status |
|---------|--------|---|-------|--------|
| analyze.md | 197 | -5+8 | ≤200 | ✅ |
| clarify.md | 185 | +8 | 193 | ✅ |
| configure.md | 143 | +8 | 151 | ✅ |
| detect.md | 146 | +8 | 154 | ✅ |
| do.md | 179 | +8 | 187 | ✅ |
| implement.md | 196 | -4+8 | ≤200 | ✅ |
| init.md | 117 | +8 | 125 | ✅ |
| learn.md | 129 | +8 | 137 | ✅ |
| plan.md | 143 | +8 | 151 | ✅ |
| pr.md | 162 | +8 | 170 | ✅ |
| review.md | 188 | +8 | 196 | ✅ |
| specify.md | 200 | -8+8 | 200 | ✅ |
| tasks.md | 200 | -8+8 | 200 | ✅ |
| verify.md | 186 | +8 | 194 | ✅ |
