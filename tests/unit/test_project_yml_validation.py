"""Unit test for ProjectMetadata derivation + linked_repos shape (T021 / commit 8).

Covers:
- architecture_branch derivation rule per data-model § 2 (the 7+5 split)
- linked_repos shape per § 11 (name/path/hosts, hosts unique)
- detected_paths must have non-empty values
"""

from __future__ import annotations

import pytest

from dotnet_ai_kit.models import LinkedRepo, ProjectMetadata, derive_architecture_branch


def test_linked_repos_accepts_valid_entry() -> None:
    """A linked_repos entry with name/path/hosts MUST be accepted."""
    pm = ProjectMetadata(
        company="Acme",
        domain="Sales",
        side="server",
        project_type="gateway",
        architecture_branch="microservice",
        detected_paths={"k": "v"},
        dotnet_version="8.0",
        linked_repos=[
            LinkedRepo(name="Acme.Sales.Query", path="../Acme.Sales.Query", hosts=["claude"]),
        ],
    )
    assert len(pm.linked_repos) == 1
    assert pm.linked_repos[0].name == "Acme.Sales.Query"


def test_linked_repos_hosts_must_match_enum() -> None:
    """linked_repos[i].hosts entries MUST be in the 4-host enum."""
    with pytest.raises(Exception):
        LinkedRepo(name="X", path="../X", hosts=["bogus-host"])  # type: ignore[list-item]


def test_linked_repos_hosts_unique() -> None:
    """Duplicate hosts in linked_repos[i].hosts MUST be rejected."""
    with pytest.raises(Exception):
        LinkedRepo(name="X", path="../X", hosts=["claude", "claude"])


def test_linked_repos_hosts_non_empty() -> None:
    """An empty hosts array MUST be rejected (min_length=1)."""
    with pytest.raises(Exception):
        LinkedRepo(name="X", path="../X", hosts=[])


def test_detected_paths_values_must_be_non_empty() -> None:
    """detected_paths values must be non-empty strings."""
    with pytest.raises(Exception):
        ProjectMetadata(
            company="Acme",
            domain="Sales",
            side="server",
            project_type="generic",
            architecture_branch="generic",
            detected_paths={"controllers": ""},  # empty value
            dotnet_version="8.0",
        )


@pytest.mark.parametrize(
    "project_type,expected",
    [
        ("command", "microservice"),
        ("query-sql", "microservice"),
        ("query-cosmos", "microservice"),
        ("processor", "microservice"),
        ("gateway", "microservice"),
        ("controlpanel", "microservice"),
        ("hybrid", "microservice"),
        ("vsa", "generic"),
        ("clean-arch", "generic"),
        ("ddd", "generic"),
        ("modular-monolith", "generic"),
        ("generic", "generic"),
    ],
)
def test_derivation_table_complete(project_type: str, expected: str) -> None:
    """Every one of the 12 project_type values MUST derive correctly."""
    assert derive_architecture_branch(project_type) == expected


def test_linked_repos_default_empty() -> None:
    """When linked_repos is omitted, the default MUST be an empty list."""
    pm = ProjectMetadata(
        company="Acme",
        domain="Sales",
        side="server",
        project_type="generic",
        architecture_branch="generic",
        detected_paths={"k": "v"},
        dotnet_version="8.0",
    )
    assert pm.linked_repos == []
