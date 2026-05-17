"""Allow ``python -m dotnet_ai_kit`` to invoke the typer CLI."""

from __future__ import annotations

from dotnet_ai_kit.cli import app

if __name__ == "__main__":
    app()
