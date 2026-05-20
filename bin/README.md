# `bin/` — source-tree wrappers (T181)

> **For contributors working out of a fresh git clone.** End users should
> install the wheel and use the published `[project.scripts]` entry point.

## What these wrappers are

- `bin/dotnet-ai` — POSIX (Linux/macOS) bash wrapper.
- `bin/dotnet-ai.cmd` — Windows batch wrapper.

Both simply invoke `python -m dotnet_ai_kit.cli "$@"` against the current
source tree. They are convenience helpers for developers who haven't yet
run `pip install -e .` from the repo root.

## What end users should use instead

| Install method | Command | Notes |
|----------------|---------|-------|
| pip (recommended) | `pip install dotnet-ai-kit` | Standard Python install. |
| uv (also recommended) | `uv tool install dotnet-ai-kit` | Isolated tool install. |
| pipx | `pipx install dotnet-ai-kit` | Per-tool venv. |

All three install the published `dotnet-ai` script via `[project.scripts]`
in `pyproject.toml`. Use the installed binary; the source-tree wrappers
are only for contributors.

## Why no standalone executable in v1.0

Standalone-executable packaging (e.g., `shiv`, `PyInstaller`, `Nuitka`,
`pyoxidizer`) is **deferred to v1.1 per OOS-003**.

Rationale: v1.0 prioritises the Python ecosystem path — pip/uv/pipx all
already work and cover the supported developer environments. The
standalone binary adds non-trivial CI / signing / per-OS distribution
overhead that we did not want to gate the v1.0 release on. The v1.1
release notes will track this work.

## Usage (source-tree)

```bash
# Linux/macOS
./bin/dotnet-ai --version

# Windows (cmd / PowerShell)
.\bin\dotnet-ai.cmd --version
```

These wrappers MUST behave identically to the installed `dotnet-ai`
entry point: `bin/dotnet-ai --version` MUST emit the same string as
the installed `dotnet-ai --version`. The contract is enforced by
`tests/content/test_bin_wrappers.py` (T182).
