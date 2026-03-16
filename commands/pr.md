---
description: "Create pull requests in all affected repos with linked descriptions"
---

# /dotnet-ai.pr — Pull Request Creation

You are an AI coding assistant executing the `/dotnet-ai.pr` command.
Your job is to create or update pull requests for the implemented feature.

## Input

Flags: `--dry-run` (preview PR content without creating), `--verbose` (diagnostic output),
       `--draft` (create as draft PRs), `--update` (update existing PRs)

## Step 1: Load Feature Context

1. Find the active feature in `.dotnet-ai-kit/features/`.
2. Load artifacts for PR content:
   - `spec.md` — feature summary for PR body.
   - `tasks.md` — completed tasks for change description.
   - `review.md` — review findings (if exists).
   - `verify.md` — verification results (if exists).
   - `service-map.md` — affected repos (microservice mode).
3. Detect mode: **generic** or **microservice**.
4. Read `.dotnet-ai-kit/config.yml` for default branch (e.g., `main`, `master`, `develop`).
   If not configured, detect from remote: `git remote show origin | grep 'HEAD branch'`.

## Step 2: Identify Repos and Branches

### Generic Mode
- Single repo: current directory.
- Branch: `feature/{NNN}-{short-name}`.
- Base: default branch from config or detection.

### Microservice Mode
- Multiple repos from `service-map.md` or config.
- Each repo has branch: `feature/{NNN}-{short-name}`.
- Collect all repos that have the feature branch with commits.

For each repo, verify:
- Feature branch exists and has commits ahead of base.
- Changes are committed (warn about uncommitted changes).

If `--verbose`, print: "Preparing PRs for {N} repos."

## Step 3: Build PR Content

For each repo, generate a PR body:

```markdown
## Summary

{1-2 sentence feature summary from spec.md}

**Feature**: {NNN}-{short-name}
**Mode**: {generic|microservice}

## Changes in this repo

{List of changes made — extracted from tasks.md for this repo}
- {Task description} ({file path})
- ...

## Related PRs

{Microservice mode only — cross-links to PRs in other repos}
- [{other-repo}#{pr-number}]({pr-url}) — {brief description}
{Or "Will be linked after all PRs are created" if creating simultaneously}

## Test Results

{From verify.md if exists}
- Build: {PASS/FAIL}
- Tests: {passed}/{total} passing
- Format: {PASS/FAIL}

## Review Findings

{From review.md if exists}
- Standards: {N} findings ({M} resolved)
- {CodeRabbit results if available}

## Checklist

- [ ] Code review approved
- [ ] All tests passing
- [ ] No CRITICAL analysis findings
- [ ] Documentation updated (if applicable)
```

PR title format: `feat({NNN}): {short feature description}`
- Max 70 characters
- Use conventional commit prefix: `feat`, `fix`, `refactor`

## Step 4: Create PRs

### If NOT --update (new PRs)

For each repo:
1. Push feature branch: `git push -u origin feature/{NNN}-{short-name}`
2. Create PR:
   ```bash
   gh pr create \
     --title "{pr-title}" \
     --body "{pr-body}" \
     --base {default-branch} \
     --head feature/{NNN}-{short-name} \
     {--draft if flag set}
   ```
3. Capture the PR URL from output.
4. After all PRs are created (microservice mode):
   - Update each PR body with cross-links to related PRs.
   - Use `gh pr edit {number} --body "{updated-body}"` per repo.

### If --update (existing PRs)

For each repo:
1. Find existing PR: `gh pr list --head feature/{NNN}-{short-name} --json number,url`
2. If found:
   - Push latest changes: `git push`
   - Update PR body: `gh pr edit {number} --body "{updated-body}"`
   - Add comment summarizing what changed since last push.
3. If not found: create new PR (fall back to create flow).

## Step 5: Report

```
PRs created for {NNN}-{short-name}:

  {repo}: {pr-url} {[DRAFT] if draft}
  {repo2}: {pr-url} {[DRAFT] if draft}
  ...

{Microservice mode}:
  Cross-repo links: {updated|pending}

{If --update}:
  Updated {N} existing PRs, created {M} new PRs.

Next: /dotnet-ai.wrap-up    (end session with handoff)
```

## Dry-Run Behavior

When `--dry-run` is active:
- Print the PR title and full body for each repo
- Show which repos WOULD have PRs created
- Show the git push commands that WOULD run
- Do NOT push branches or create PRs
- Prefix output with `[DRY-RUN]`

## Error Handling

- `gh` CLI not installed: "GitHub CLI required. Install: https://cli.github.com"
- Not authenticated: "Run `gh auth login` first."
- No feature branch: "No feature branch found. Run /dotnet-ai.implement first."
- No commits on branch: "Branch has no changes. Nothing to create a PR for."
- Push fails: report error, suggest `git pull --rebase` or force push (with warning)
- PR already exists (without --update): "PR already exists: {url}. Use --update to modify."
- Uncommitted changes: warn user, suggest committing before PR creation
