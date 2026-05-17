"""Abstract `Host` base class for plugin-native architecture (feature 019).

Each plugin host has its own subclass that knows:
- `install_paths()` — where the host stores its plugin cache (per-OS)
- `verify_install()` — whether the plugin is installed at the expected paths
- `write_per_solution_files()` — which per-solution files the host needs at
  init/upgrade time (these are SMALL: project.yml, manifest.json, host
  permission settings — NOT the full skill/command/agent corpus).

Per data-model.md § 10-12, research R7, plan.md commit 4 project-structure.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class InstallStatus:
    """Result of `Host.verify_install()`.

    `installed`: True if the host's plugin cache contains the expected paths.
    `expected_paths`: paths the host expects to see (per the host's own model).
    `missing_paths`: subset of `expected_paths` that were not found on disk.
    `notes`: optional human-readable diagnostic details.
    """

    host_name: str
    installed: bool
    expected_paths: list[Path] = field(default_factory=list)
    missing_paths: list[Path] = field(default_factory=list)
    notes: str = ""

    @property
    def is_healthy(self) -> bool:
        """Convenience: install present AND no missing paths."""
        return self.installed and not self.missing_paths


class Host(ABC):
    """Abstract host adapter.

    Subclasses implement the three plugin-host capabilities feature 019 cares
    about. They MUST NOT shell out to the host's CLI in v1 — `verify_install`
    is filesystem-inspection-only per clarify Q3. Future versions may add a
    `--probe` flag that does a real `claude /plugins-list` call, but for now
    the contract is read-only filesystem semantics.
    """

    #: Canonical lowercase host name. Matches values in
    #: `agents.SUPPORTED_AI_TOOLS`.
    name: str

    @abstractmethod
    def install_paths(self) -> list[Path]:
        """Return the per-host plugin cache paths under `Path.home()`.

        Each entry is an absolute path that, if it exists, indicates the
        plugin is installed for this host. Cross-platform — uses
        `pathlib.Path` only, never hard-coded `/` or `\\`.

        Examples (Claude):
          ~/.claude/plugins/cache/dotnet-ai-kit/<version>/
          ~/.claude/plugins/local/dotnet-ai-kit/  (developer symlink)
        """

    @abstractmethod
    def verify_install(self) -> InstallStatus:
        """Inspect the filesystem to determine plugin install status.

        Filesystem inspection only — does NOT shell out to the host's CLI
        per clarify Q3 (predictable, fast for `dotnet-ai check`).
        """

    @abstractmethod
    def write_per_solution_files(
        self,
        project_root: Path,
        *,
        permission_profile: Optional[str] = None,
    ) -> list[Path]:
        """Write the small set of per-solution files this host needs.

        Returns the list of paths written. Per FR-005 / FR-006, the
        per-solution file footprint must be small (target: ≤10 files per
        host, vs the pre-019 baseline of ~180 files per Claude install).

        Args:
            project_root: The .NET solution root.
            permission_profile: Optional permission preset (`minimal`,
                `standard`, `full`, `mcp`). When supplied, the host writes
                its corresponding permission file (e.g., `.claude/settings.json`).
        """
