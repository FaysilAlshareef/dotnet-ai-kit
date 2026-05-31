# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 2.0.x   | Yes                |
| < 2.0   | No (v1 Python CLI removed) |

## Reporting a Vulnerability

If you discover a security vulnerability in dotnet-ai-kit, please report it
responsibly. **Do not open a public GitHub issue.**

### How to Report

1. Email **faysilalshareef@gmail.com** with the subject line: `[SECURITY] dotnet-ai-kit vulnerability`
2. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment** within 48 hours
- **Assessment** within 7 days
- **Fix or mitigation** within 30 days for confirmed vulnerabilities
- **Credit** in the release notes (unless you prefer to remain anonymous)

### Scope

This policy covers:
- The .NET CLI (`src/DotnetAiKit.*`) and the `dotnet-ai` tool
- CLI verbs and their behavior (init/check/render/generate/detect/migrate/configure/upgrade)
- The shipped Roslyn analyzers (`DotnetAiKit.Analyzers`)
- The projection engine and generated plugin manifests under `build/`

This policy does **not** cover:
- Slash-command / skill / agent / rule markdown content (instructions, not executable code)
- Generated guidance the assistant chooses to act on (subject to the host's own permissions)

## Security Design

dotnet-ai-kit is built for safe, deterministic operation:
- **No-network invariant** — `init`/`check`/`migrate`/`render`/`generate` make no network
  calls (enforced by `DotnetAiKit.Acceptance.Tests`).
- **Deterministic, reflection-free projection** — output is a pure function of `artifacts/`;
  CI's `generate --check` drift gate makes tampered/divergent output un-mergeable.
- **Manifest integrity** — `ManifestIntegrityService` computes a sha256 over
  newline-normalized content for verification.
- **Cross-platform path safety** — `System.IO.Path` everywhere; no hardcoded paths.
- **Deterministic enforcement** — the shipped analyzer turns mechanical conventions into
  build errors independent of which assistant wrote the code.
