---
name: git-worktree-isolation
description: >
  Use when starting feature work that needs isolation from the current
  workspace, or before executing implementation plans with multiple tasks.
metadata:
  category: workflow
  when-to-use: "Before feature implementation, multi-task plans, or parallel development work"
---

# Git Worktree Isolation — Safe Workspaces for Features

## Core Principle

**Isolated workspace + verified baseline = safe experimentation.**

Git worktrees create separate working directories sharing the same repository, allowing work on features without polluting the main workspace.

## When to Use

- Starting a new feature (`/dai.go`)
- Executing a multi-task implementation plan
- Parallel development on multiple features
- Risky refactoring that might need to be discarded
- Subagent-driven development (each subagent gets clean context)

## Directory Selection

Follow this priority order:

### 1. Check Existing Directories
```bash
ls -d .worktrees 2>/dev/null     # Preferred (hidden)
ls -d worktrees 2>/dev/null      # Alternative
```
If found, use that directory. If both exist, `.worktrees` wins.

### 2. Check Project Configuration
```bash
grep -i "worktree" CLAUDE.md 2>/dev/null
```
If a preference is specified, use it.

### 3. Ask User
If no directory exists and no configuration preference:
```
No worktree directory found. Where should I create worktrees?
1. .worktrees/ (project-local, hidden)
2. Custom path

Which do you prefer?
```

## Safety Verification

### For Project-Local Directories

**MUST verify directory is gitignored before creating worktree:**

```bash
git check-ignore -q .worktrees 2>/dev/null
```

**If NOT ignored:**
1. Add `.worktrees/` to `.gitignore`
2. Commit the change
3. Then proceed with worktree creation

**Why critical:** Prevents accidentally committing worktree contents to the repository.

## Creation Steps

### 1. Create the Worktree

```bash
# Determine branch name from feature
branch_name="feature/$(echo "$FEATURE_NAME" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')"

# Create worktree with new branch
git worktree add ".worktrees/$FEATURE_NAME" -b "$branch_name"
cd ".worktrees/$FEATURE_NAME"
```

### 2. Run .NET Project Setup

Auto-detect and run appropriate setup:

```bash
# .NET Solution
if ls *.sln 1>/dev/null 2>&1; then
    dotnet restore
fi

# Python (for tools like this one)
if [ -f pyproject.toml ]; then
    pip install -e ".[dev]"
fi

# Node.js (for frontend projects in the solution)
if [ -f package.json ]; then
    npm install
fi
```

### 3. Verify Clean Baseline

Run tests to confirm the worktree starts clean:

```bash
# .NET
dotnet build
dotnet test

# Python
pytest
```

**If tests fail:** Report failures. Ask whether to proceed or investigate.
**If tests pass:** Report ready.

### 4. Report Status

```
Worktree ready at .worktrees/{feature-name}
Branch: feature/{feature-name}
Build: OK
Tests: {N}/{N} passing
Ready to implement.
```

## Cleanup After Completion

When feature work is done (merged, PR created, or discarded):

```bash
# Return to main workspace
cd /path/to/main/repo

# Remove the worktree
git worktree remove .worktrees/{feature-name}

# If branch was merged, clean it up
git branch -d feature/{feature-name}
```

## Quick Reference

| Situation | Action |
|-----------|--------|
| `.worktrees/` exists | Use it (verify ignored) |
| `worktrees/` exists | Use it (verify ignored) |
| Neither exists | Check config, then ask user |
| Directory not ignored | Add to `.gitignore` + commit |
| Baseline tests fail | Report failures, ask user |
| No solution file | Skip `dotnet restore` |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skipping ignore verification | Always `git check-ignore` first |
| Assuming directory location | Follow priority: existing > config > ask |
| Proceeding with failing baseline | Report failures, get explicit permission |
| Forgetting cleanup | Remove worktree after merge/discard |
| Hardcoding setup commands | Auto-detect from project files |

## Integration

**Used by:**
- `/dotnet-ai.implement` — set up workspace before executing tasks
- Subagent-driven development — isolated workspace per feature
- `/dotnet-ai.undo` — can discard entire worktree for clean rollback

**Pairs with:**
- `skills/workflow/verification-gate` — verify baseline before starting
- `skills/workflow/sdd-lifecycle` — worktree per SDD cycle
