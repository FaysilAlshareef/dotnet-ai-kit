# Unmanaged paths — files dotnet-ai-kit will NEVER write to

**Spec source**: A-008 (extended in spec-phase round 1 / Q3), FR-008

Per the spec's binding rule (A-008), paths outside the formally-managed
manifest are NEVER written, modified, or deleted by any dotnet-ai-kit
command. This document publishes the non-exhaustive list of common .NET
solution-root developer-owned paths the tool will not touch.

If you author a file at any of these paths, dotnet-ai-kit `init`,
`upgrade`, `configure`, `migrate`, and `check` will leave it untouched.

## .NET / repo-root developer-owned files

These files are part of the .NET ecosystem or repository convention — not
the AI-tooling concern. dotnet-ai-kit will never write them:

- `AGENTS.md` — Codex CLI's repo-root agent file (per FR-008 / A-008; the
  legacy `copy_commands_codex` emitter was deleted in feature 019)
- `.editorconfig` — editor formatting config
- `Directory.Build.props` — MSBuild solution-wide properties
- `Directory.Build.targets` — MSBuild solution-wide targets
- `Directory.Packages.props` — centralized NuGet package management
- `global.json` — .NET SDK version pinning
- `nuget.config` — NuGet source / feed config
- `.gitignore` — git ignore patterns
- `.gitattributes` — git attribute rules
- `Dockerfile` (and `Dockerfile.<variant>`) — container build
- `docker-compose.yml` — local container orchestration
- `.github/workflows/*.yml` — CI workflow files
- `README.md` / `README.txt` / `README.rst` — project README
- `LICENSE` / `LICENSE.md` / `LICENSE.txt` — project license
- `*.sln` — Visual Studio solution files
- `*.csproj` / `*.fsproj` / `*.vbproj` — .NET project files

## How the rule is enforced

- `tests/unit/test_fr008_unmanaged_paths_parameterized.py` runs init across
  every path in this list and asserts the file is untouched (preserved
  if pre-existing, NOT created if absent).
- The migrate command's classification only touches files in the manifest;
  unmanaged paths are never classified or moved.
- The Copilot render path emits to `.github/copilot-instructions.md`,
  `.github/instructions/*.instructions.md`, `.github/agents/*.agent.md`.
  These ARE managed paths once `init --copilot` runs, but pre-existing
  user files at those paths are PRESERVED IN PLACE by default; the
  `--force-render <path>` flag is the user's explicit opt-in to overwrite.

## Reporting an issue

If `dotnet-ai-kit` writes to a path on this list (or to any path a
reasonable developer would expect not to be touched), it's a bug. Open an
issue at the repo's GitHub issues page; include:

1. The exact `dotnet-ai-kit` command that touched the file
2. The file path
3. The diff (before vs after)

Per the FR-008 + A-008 invariant, this should never happen.
