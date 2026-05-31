---
name: release
description: "Closes out a merged feature — version bump, changelog, tag, and GitHub release. Use after pull requests merge to publish a release. Do NOT use to open the pull request (use pr) or to write release-note documentation only (use docs)."
disable-model-invocation: true
---
# /dotnet-ai.release — Post-Merge Release

Publish a release after the feature's PRs have merged.

## Usage
```
/dotnet-ai.release $ARGUMENTS
```

## Steps
1. Determine the version bump from the merged changes (semver; honor the constitution's versioning policy).
2. Generate/append the changelog from merged commits/PRs.
3. Tag the release and create the GitHub release with notes.
4. Optionally trigger a deploy hook (CI/CD owns deployment — the AI never deploys directly).

This is a user-invoked command (off the always-loaded listing).
