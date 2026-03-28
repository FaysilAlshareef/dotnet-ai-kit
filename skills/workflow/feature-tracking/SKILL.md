---
name: feature-tracking
description: >
  Feature directory structure and status progression for tracking development.
  Covers feature briefs, specs, status files, and multi-service coordination.
  Trigger: feature tracking, status, progress, feature directory.
metadata:
  category: workflow
  agent: dotnet-architect
---

# Feature Tracking — Directory Structure & Status

## Core Principles

- Every feature gets a numbered directory under `.dotnet-ai-kit/features/`
- Status progresses: `planned` -> `specified` -> `implementing` -> `implemented` -> `reviewing` -> `shipped`
- Feature brief captures scope, acceptance criteria, and affected services
- Spec captures technical design before implementation begins
- Implementation log tracks what was done for handoff purposes

## Key Patterns

### Feature Brief Template

```markdown
# Feature: {Feature Name}

## Overview
{One-paragraph description of the feature}

## Acceptance Criteria
- [ ] {Criterion 1}
- [ ] {Criterion 2}
- [ ] {Criterion 3}

## Affected Services
- [ ] {domain}-command: {what changes}
- [ ] {domain}-query: {what changes}
- [ ] {domain}-gateway: {what changes}

## Dependencies
- Requires feature #{NNN} to be implemented first
- External: {any external dependencies}

## Estimated Scope
- Events: {count} new event types
- Endpoints: {count} new API endpoints
- UI: {count} new pages/dialogs
```

### Technical Spec Template

```markdown
# Spec: {Feature Name}

## Events
| Event Type | Data Fields | Produced By | Consumed By |
|---|---|---|---|
| OrderExportRequested | ExportFormat, Filters | command | processor |

## Aggregate Changes
- `Order` aggregate: add `RequestExport(format)` method
- New event: `OrderExportRequestedData(ExportFormat, DateTime)`

## Query Changes
- New query: `GetExportStatusQuery(Guid exportId)`
- New entity: `ExportJob` with status tracking

## API Endpoints
| Method | Path | Description |
|---|---|---|
| POST | /api/v1/orders/export | Request export |
| GET | /api/v1/orders/export/{id}/status | Check status |

## UI Changes
- Add "Export" button to Orders data grid toolbar
- Add export status dialog
```

### Status Transitions

```
planned → specified    (spec written)
specified → implementing (implementation started)
implementing → implemented (code complete)
implemented → reviewing (PR created)
reviewing → approved (review passed)
approved → shipped (deployed)

Blocked transitions:
reviewing → implementing (fix required, back to implementation)
```

### Querying Feature Status

```bash
# List all features and their status
for f in .dotnet-ai-kit/features/*/status.json; do
  echo "$(dirname $f | xargs basename): $(cat $f | jq -r .phase)"
done

# Find features in a specific phase
grep -rl '"phase": "implementing"' .dotnet-ai-kit/features/*/status.json
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| No feature directory | Create directory before starting work |
| Skipping spec phase | Always write spec before implementing |
| Stale status files | Update status.json at each phase transition |
| Feature too large | Break into sub-features with dependencies |

## Detect Existing Patterns

```bash
# Find feature tracking directory
ls -la .dotnet-ai-kit/features/ 2>/dev/null

# Count features by status
grep -c '"phase"' .dotnet-ai-kit/features/*/status.json 2>/dev/null
```

## Adding to Existing Project

1. **Check existing feature numbering** — continue the sequence
2. **Use existing templates** for brief and spec
3. **Update status.json** when phases change
4. **Link PRs** to feature directories in commit messages
5. **For multi-repo features**, create feature directory in the primary repo
