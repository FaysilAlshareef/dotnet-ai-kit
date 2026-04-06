# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.0.x   | Yes                |
| < 1.0   | No                 |

## Reporting a Vulnerability

If you discover a security vulnerability in dotnet-ai-kit, please report it
responsibly. **Do not open a public GitHub issue.**

### How to Report

1. Email **faysil@ecom.ltd** with the subject line: `[SECURITY] dotnet-ai-kit vulnerability`
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
- The `dotnet-ai-kit` Python package (`src/dotnet_ai_kit/`)
- CLI commands and their behavior
- Hook scripts (`hooks/`)
- Permission configurations (`config/`)

This policy does **not** cover:
- Slash command markdown files (they are instructions, not executable code)
- Skill/agent/rule content (documentation, not runtime code)
- Template files (rendered by the tool, not executed directly)

## Security Design

dotnet-ai-kit includes safety features:
- **Bash guard hook** blocks dangerous shell commands (rm -rf /, DROP TABLE, etc.)
- **Permission levels** (minimal, standard, full) control what operations the AI can perform
- **No `shell=True`** in subprocess calls -- all commands use list arguments
- **No hardcoded paths** -- uses `pathlib.Path` and `tempfile` for cross-platform safety
