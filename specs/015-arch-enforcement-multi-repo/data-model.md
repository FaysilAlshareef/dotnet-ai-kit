# Data Model: Architecture Profiles, Multi-Repo Deployment, and Enforcement Optimization

**Date**: 2026-04-02 | **Branch**: `015-arch-enforcement-multi-repo`

## Model Changes

### DetectedProject (models.py) — Modified

**Existing fields** (unchanged):
- `mode`: Literal["microservice", "generic"]
- `project_type`: str (command, query-sql, query-cosmos, processor, gateway, controlpanel, hybrid, vsa, clean-arch, ddd, modular-monolith, generic)
- `dotnet_version`: str
- `architecture`: str
- `namespace_format`: str
- `packages`: list[str]
- `confidence`: Literal["high", "medium", "low"]
- `confidence_score`: float (0.0-1.0)
- `user_override`: bool
- `top_signals`: list[DetectionSignal]

**New field**:
- `detected_paths`: Optional[dict[str, str]] = None

**Description**: Maps logical path categories to actual filesystem paths relative to project root. Populated by `/dai.detect` command.

**Valid keys**: aggregates, events, commands, handlers, entities, tests, test_live, persistence, controllers, cosmos_entities, cosmos_repositories, features, pages, components. Not all keys will be present — depends on project type.

**Validation**: No validator needed. Keys are freeform strings; values are relative paths. Empty dict or None both mean "no paths detected."

**Example**:
```yaml
detected_paths:
  aggregates: "Company.Domain/Core"
  events: "Company.Domain/Events"
  handlers: "Company.Application/Features"
  tests: "Company.Test/Tests"
```

---

### DotnetAiConfig (models.py) — Modified

**Existing fields** (unchanged):
- `version`: str
- `company`: CompanyConfig
- `naming`: NamingConfig
- `repos`: ReposConfig
- `permissions_level`: Literal["minimal", "standard", "full"]
- `managed_permissions`: list[str]
- `ai_tools`: list[str]
- `command_style`: Literal["full", "short", "both"]

**New field**:
- `linked_from`: Optional[str] = None

**Description**: Path to the primary repo that deployed tooling to this secondary repo. Set during multi-repo deployment. None for primary repos or repos not part of a linked setup.

**Validation**: No validator needed. Value is a filesystem path string or None.

**Example**:
```yaml
linked_from: "C:/Users/dev/repos/my-command-service"
```

---

### PROFILE_MAP (copier.py) — New Constant

**Type**: dict[str, str]

**Description**: Maps project_type values to profile source file paths (relative to package root).

**Entries**: 12 entries covering all project types + 1 FALLBACK_PROFILE constant.

---

### AGENT_FRONTMATTER_MAP (agents.py) — New Constant

**Type**: dict[str, dict]

**Description**: Per-tool transformation mapping for universal agent frontmatter fields. v1.0 has only the "claude" entry.

**Structure**:
```
{
  "claude": {
    "role": { "advisory": {...}, "implementation": {...}, ... },
    "expertise": callable(list[str]) -> dict,
    "complexity": { "high": {...}, "medium": {...}, "low": {...} },
    "max_iterations": callable(int) -> dict,
  }
}
```

---

## Entity Relationships

```
DotnetAiConfig
  ├── repos: ReposConfig  (links to secondary repos)
  ├── linked_from: str    (back-link from secondary to primary)
  └── ai_tools: list[str] (determines which tool mappings to use)

DetectedProject
  ├── project_type: str   (selects which profile to deploy via PROFILE_MAP)
  └── detected_paths: dict (feeds token resolution in copy_skills)

AGENT_CONFIG[tool]        (directory paths for deployment)
AGENT_FRONTMATTER_MAP[tool] (frontmatter transformation rules)
PROFILE_MAP[project_type] (profile source file path)
```

## State Transitions

### Profile Lifecycle

```
No profile → configure (project_type detected) → Profile deployed
Profile deployed → re-configure (new project_type) → Old profile overwritten
Profile deployed → upgrade → Profile re-deployed (same or updated version)
```

### Linked Repo Lifecycle

```
Uninitialized → dotnet-ai init + /dai.detect → Initialized (has config.yml + project.yml)
Initialized → primary's configure links it → Tooling deployed + linked_from set
Linked → primary's configure un-links it → Tooling stays, linked_from stays (no cleanup)
Linked → primary's upgrade → Tooling re-deployed if version allows
```

### Branch Lifecycle (secondary repos)

```
Any branch → configure deploys → chore/dotnet-ai-kit-setup created
Any branch → /dai.specify → chore/brief-{NNN}-{name} created
chore/brief-* → /dai.plan or /dai.tasks → Same branch reused
Any branch → upgrade deploys → chore/dotnet-ai-kit-upgrade-{version} created
```
