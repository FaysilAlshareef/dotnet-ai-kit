---
description: "Generates project documentation. Use when creating README, API docs, ADRs, or deployment guides."
---

# Docs

Generate or update technical and business documentation. With no subcommand, scans for documentation gaps and reports what is missing. With a subcommand, generates that specific documentation type.

## Usage

```
/dotnet-ai.docs $ARGUMENTS
```

**Subcommands:**
- (no args) -- Scan for documentation gaps, report what is missing
- `readme` -- Generate or update README.md
- `api` -- Generate API documentation from OpenAPI/controllers
- `adr "Decision Title"` -- Create new Architecture Decision Record
- `deploy` -- Generate deployment guide per environment
- `release` -- Generate release notes from git history
- `service` -- Generate service documentation (microservice mode)
- `code` -- Scan and add missing XML doc comments to public APIs
- `feature` -- Generate user-facing feature documentation
- `all` -- Generate all documentation types

**Examples:**
- `/dotnet-ai.docs` -- Report documentation gaps
- `/dotnet-ai.docs readme` -- Generate README
- `/dotnet-ai.docs adr "Use Cosmos for read model"` -- Create ADR
- `/dotnet-ai.docs all --dry-run` -- Preview all docs generation
- `/dotnet-ai.docs api --verbose` -- Generate API docs with details

## Flags

| Flag | Description |
|------|-------------|
| `--dry-run` | Show generated documentation without writing files |
| `--dry-run` | List files that would be created/modified |
| `--verbose` | Show scanning details and content summaries |
| `--update` | Update existing docs only, do not create new ones |

## Load Specialist Agent

Read `agents/docs-engineer.md` for documentation patterns. Load all skills listed in the agent's Skills Loaded section.

## Pre-Generation (all subcommands)

1. **Detect project mode** -- microservice vs generic from config or project structure.
2. **Detect .NET version** -- for version-specific documentation.
3. **Scan existing documentation** -- check what already exists, detect style and format.
4. **Load config** -- read `.dotnet-ai-kit/config.yml` for company name, project details.

## Skills to Read (per subcommand)

| Subcommand | Skills |
|------------|--------|
| `readme` | `skills/docs/readme-gen` |
| `api` | `skills/docs/api-docs` |
| `adr` | `skills/docs/adr` |
| `deploy` | `skills/docs/runbook` |
| `release` | `skills/docs/changelog-gen` |
| `service` | `skills/docs/architecture-docs` |
| `code` | `skills/docs/api-docs` |
| `feature` | `skills/docs/onboarding` |
| `all` | All docs skills |

## Gap Scan (no subcommand)

When run without a subcommand, scan the project and report:

```
Documentation Gap Report:

  Missing:
  - README.md (no project README found)
  - docs/adr/ (no ADR directory)
  - API documentation (controllers found but no OpenAPI docs)

  Outdated:
  - docs/deployment/dev.md (last updated 3 months ago, infrastructure changed)

  Present:
  - CHANGELOG.md (up to date)
  - docs/architecture.md (present)

  Suggestion: Run /dotnet-ai.docs readme to start
```

## Subcommand: `readme`

Generate or update `README.md` at project root.
- Scan project for: name, description, tech stack, build instructions
- Include: badges, prerequisites, getting started, project structure, contributing
- If README exists: update sections while preserving custom content

## Subcommand: `api`

Generate API reference documentation.
- Scan controllers/endpoints for routes, methods, request/response types
- Generate: `docs/api/api-reference.md` with endpoint tables
- If OpenAPI/Swagger configured: reference the Scalar/Swagger URL
- Include request/response examples

## Subcommand: `adr "Title"`

Create a new Architecture Decision Record.
- Path: `docs/adr/{NNNN}-{slugified-title}.md`
- Auto-increment ADR number from existing ADRs
- Template: Status, Context, Decision, Consequences
- Update `docs/adr/README.md` index if it exists
- Title from `$ARGUMENTS` after `adr` keyword

## Subcommand: `deploy`

Generate deployment guides per environment.
- Scan for: Dockerfile, K8s manifests, GitHub Actions, Azure configs
- Generate: `docs/deployment/dev.md`, `staging.md`, `production.md`
- Include: prerequisites, environment variables, deployment steps, rollback

## Subcommand: `release`

Generate release notes from git history.
- Scan: git log since last tag or release
- Categorize: features, bug fixes, breaking changes
- Generate: update `CHANGELOG.md` or create release notes file
- Follow Keep a Changelog format if existing CHANGELOG detected

## Subcommand: `service`

Generate service documentation (microservice mode).
- Scan: events published/consumed, gRPC services, dependencies
- Generate: `docs/service-catalogue.md` with service entry
- Include: purpose, API surface, events, dependencies, SLAs

## Subcommand: `code`

Add missing XML documentation comments to public APIs.
- Scan: public classes, methods, properties without `///` comments
- Generate: XML doc comments with `<summary>`, `<param>`, `<returns>`
- Modify source files in-place (only adds comments, never changes code)
- After modifications: run `dotnet build` to verify compilation
- Record all modified files in the active feature's `undo-log.md`:
  ```
  ## Docs Code - XML Comments ({DATE})
  - modified: {file path} (added XML doc comments)
  ```

## Subcommand: `feature`

Generate user-facing feature documentation.
- Read: active feature spec and implementation
- Generate: `docs/features/{feature-name}.md`
- Include: feature description, usage guide, API examples

## Subcommand: `all`

Run all documentation subcommands in sequence. Skip types that are already up to date.

## Multi-Repo Support (microservice mode)

- **Per-repo docs**: Each service gets its own README, API docs, service catalogue entry
- **Umbrella docs**: Cross-service architecture overview, event flow diagram, deployment orchestration
- Detect which repos are available locally and generate docs for each

## Output Locations

```
project-root/
  README.md
  CHANGELOG.md
  docs/
    adr/
      README.md
      0001-*.md
    api/
      api-reference.md
    deployment/
      dev.md, staging.md, production.md
    architecture.md
    service-catalogue.md
    features/
      {feature-name}.md
```

## Preview / Dry-Run Behavior

- `--dry-run`: Show generated documentation content. No file writes.
- `--dry-run`: List files that would be created/modified. No content, no writes.
