---
name: changelog-gen
description: >
  Changelog generation from git history using Keep a Changelog format.
  Covers conventional commits, semantic versioning, and release notes.
  Trigger: changelog, release notes, conventional commits, version, CHANGELOG.
category: docs
agent: docs-engineer
---

# Changelog Generation — Keep a Changelog Format

## Core Principles

- CHANGELOG.md follows [Keep a Changelog](https://keepachangelog.com/) format
- Sections: Added, Changed, Deprecated, Removed, Fixed, Security
- Generated from conventional commits: `feat:`, `fix:`, `breaking:`
- Semantic versioning based on change types
- Microservice mode: per-service changelog + combined release notes

## Key Patterns

### CHANGELOG.md Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Order export endpoint with CSV download (#45)
- Bulk order creation via batch API (#42)

### Fixed
- Sequence checking race condition in OrderUpdatedHandler (#48)

## [1.2.0] - 2025-03-01

### Added
- Customer search endpoint with fuzzy matching
- MudDataGrid pagination in control panel

### Changed
- Upgraded to .NET 9
- Migrated from Swagger to Scalar for API docs

### Fixed
- Cosmos DB RU spike on cross-partition queries
- Service Bus session timeout configuration

## [1.1.0] - 2025-02-01

### Added
- Order completion workflow
- Daily sales report generation

### Security
- Updated JWT validation to check audience claim
```

### Conventional Commit Types

```
Type        | Changelog Section | Version Bump
----------- | ----------------- | -----------
feat:       | Added             | Minor
fix:        | Fixed             | Patch
docs:       | (skip)            | None
refactor:   | Changed           | None
perf:       | Changed           | Patch
test:       | (skip)            | None
chore:      | (skip)            | None
breaking:   | Changed           | Major
BREAKING CHANGE: | Changed      | Major
security:   | Security          | Patch
deprecate:  | Deprecated        | Minor
```

### Generating Changelog from Git

```bash
# Get commits since last tag
git log $(git describe --tags --abbrev=0)..HEAD --oneline --format="%s (%h)"

# Filter by type
git log v1.1.0..HEAD --oneline | grep "^feat:" | sed 's/feat: /- /'
git log v1.1.0..HEAD --oneline | grep "^fix:" | sed 's/fix: /- /'
```

### Automated Generation Script

```bash
#!/bin/bash
# generate-changelog.sh

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
RANGE="${LAST_TAG:+$LAST_TAG..}HEAD"

echo "## [Unreleased]"
echo ""

ADDED=$(git log $RANGE --oneline | grep -i "^feat:" | sed 's/^feat: /- /')
if [ -n "$ADDED" ]; then
    echo "### Added"
    echo "$ADDED"
    echo ""
fi

FIXED=$(git log $RANGE --oneline | grep -i "^fix:" | sed 's/^fix: /- /')
if [ -n "$FIXED" ]; then
    echo "### Fixed"
    echo "$FIXED"
    echo ""
fi

CHANGED=$(git log $RANGE --oneline | grep -i "^refactor:\|^perf:" | sed 's/^[^:]*: /- /')
if [ -n "$CHANGED" ]; then
    echo "### Changed"
    echo "$CHANGED"
    echo ""
fi
```

### GitHub Release Notes

```markdown
# Release v1.2.0

## Highlights
- Order export functionality for operators
- Migrated to Scalar API documentation

## What's Changed
### New Features
- Order export endpoint with CSV download by @developer in #45
- Bulk order creation via batch API by @developer in #42

### Bug Fixes
- Fixed sequence checking race condition by @developer in #48

### Infrastructure
- Upgraded to .NET 9
- Migrated from Swagger to Scalar

**Full Changelog**: https://github.com/{company}/{repo}/compare/v1.1.0...v1.2.0
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| No changelog at all | Maintain CHANGELOG.md from day one |
| Manual changelog only | Generate from conventional commits |
| Missing version dates | Always include release date |
| No version numbers | Use semantic versioning |

## Detect Existing Patterns

```bash
# Find existing changelog
find . -name "CHANGELOG*" -maxdepth 2

# Check commit message conventions
git log --oneline -20

# Find version tags
git tag --sort=-v:refname | head -5
```

## Adding to Existing Project

1. **Check for existing CHANGELOG.md** — append, don't replace
2. **Adopt conventional commits** for future commit messages
3. **Generate initial changelog** from git history
4. **Tag releases** with semantic version numbers
5. **Update changelog** as part of the release process
