"""dotnet-ai-kit: AI dev tool plugin for the full .NET development lifecycle."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("dotnet-ai-kit")
except PackageNotFoundError:
    __version__ = "1.0.0"
