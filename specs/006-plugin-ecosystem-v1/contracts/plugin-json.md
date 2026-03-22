# Contract: plugin.json

**Location**: `.claude-plugin/plugin.json`

## Schema

```json
{
  "name": "dotnet-ai-kit",
  "version": "1.0.0",
  "description": "Full .NET development lifecycle — 26 commands, 104 skills, 13 agents. SDD workflow, code generation, AI detection for VSA, Clean Arch, DDD, CQRS Microservices.",
  "author": "Faysil Alshareef",
  "homepage": "https://github.com/FaysilAlshareef/dotnet-ai-kit",
  "tags": [
    "dotnet",
    "csharp",
    ".net",
    "cqrs",
    "microservices",
    "clean-architecture",
    "vertical-slice",
    "ddd",
    "code-generation",
    "sdd"
  ],
  "category": "development"
}
```

## Validation Rules

- `name`: Required, lowercase, no spaces
- `version`: Required, valid SemVer
- `description`: Required, under 200 characters for marketplace display
- `author`: Required, non-empty
- `tags`: Optional, array of lowercase strings
