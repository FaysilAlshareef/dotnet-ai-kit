"""T033 — A-009: host symmetry (governance check).

Per FR-029 / A-009: every host with a plugin manifest MUST have a
corresponding smoke fixture entry. Inverse: no orphaned plugin manifests
without smoke fixtures.

Verifies structural symmetry between:
- `.{host}-plugin/plugin.json` files
- `tests/integration/test_smoke_{host}.py` files
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent

# Hosts that have a plugin manifest in the repo root
EXPECTED_PLUGIN_HOSTS = ("claude", "codex", "cursor")


def test_every_plugin_host_has_smoke_fixture() -> None:
    """A-009 governance: each plugin manifest MUST have a smoke fixture."""
    smoke_dir = REPO / "tests" / "integration"
    missing_smokes: list[str] = []
    for host in EXPECTED_PLUGIN_HOSTS:
        manifest = REPO / f".{host}-plugin" / "plugin.json"
        if not manifest.is_file():
            continue  # not yet shipped — not a violation
        smoke = smoke_dir / f"test_smoke_{host}.py"
        if not smoke.is_file():
            missing_smokes.append(host)
    assert not missing_smokes, (
        f"A-009 violation: hosts with plugin manifest but NO smoke fixture: {missing_smokes}"
    )


def test_no_orphaned_smoke_fixtures_without_manifests() -> None:
    """A-009 governance: no test_smoke_<host>.py without a matching manifest."""
    smoke_dir = REPO / "tests" / "integration"
    if not smoke_dir.is_dir():
        return  # no smokes in fresh checkout
    orphans: list[str] = []
    for smoke in smoke_dir.glob("test_smoke_*.py"):
        # extract host name from filename
        name = smoke.stem.replace("test_smoke_", "")
        # copilot has no plugin model (render-only) — exempt
        if name == "copilot":
            continue
        if name not in EXPECTED_PLUGIN_HOSTS:
            continue
        manifest = REPO / f".{name}-plugin" / "plugin.json"
        if not manifest.is_file():
            orphans.append(name)
    assert not orphans, f"A-009 violation: smoke fixtures without plugin manifest: {orphans}"
