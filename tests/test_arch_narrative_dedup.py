"""T058-test — FR-016: architecture narrative not duplicated agent vs profile."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

AGENT_TO_PROFILE = {
    "agents/command-architect.md": [
        "profiles/microservice/command.md",
    ],
    "agents/cosmos-architect.md": [
        "profiles/microservice/query-cosmos.md",
    ],
    "agents/query-architect.md": [
        "profiles/microservice/query-sql.md",
        "profiles/microservice/query-cosmos.md",
    ],
    "agents/processor-architect.md": [
        "profiles/microservice/processor.md",
    ],
    "agents/gateway-architect.md": [
        "profiles/microservice/gateway.md",
    ],
    "agents/controlpanel-architect.md": [
        "profiles/microservice/controlpanel.md",
    ],
    "agents/dotnet-architect.md": [
        "profiles/generic/clean-arch.md",
        "profiles/generic/ddd.md",
        "profiles/generic/modular-monolith.md",
        "profiles/generic/vsa.md",
        "profiles/generic/generic.md",
    ],
}

H2_HEADINGS = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
ARCH_HEADING_HINTS = ("HARD CONSTRAINTS", "Architecture")


def _h2s(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    return set(H2_HEADINGS.findall(path.read_text(encoding="utf-8")))


def test_no_duplicate_architecture_headings_between_agent_and_profile() -> None:
    duplicates: list[str] = []
    for agent_rel, profile_rels in AGENT_TO_PROFILE.items():
        agent = REPO / agent_rel
        agent_h2 = _h2s(agent)
        for profile_rel in profile_rels:
            profile_h2 = _h2s(REPO / profile_rel)
            shared = agent_h2 & profile_h2
            arch_dupes = {h for h in shared if any(hint in h for hint in ARCH_HEADING_HINTS)}
            for h in arch_dupes:
                duplicates.append(f"{agent_rel} ∩ {profile_rel}: {h!r}")
    assert not duplicates, "duplicate architecture headings:\n" + "\n".join(duplicates)
