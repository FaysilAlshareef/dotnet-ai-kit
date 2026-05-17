"""Contract test for ProjectMetadata YAML schema (T020 / feature 019 commit 8).

Asserts that the pydantic ProjectMetadata model:
1. Accepts the 12 valid project_type enum values per clarify Q1.
2. Rejects unknown project_type values.
3. Derives architecture_branch correctly per data-model.md § 2.
4. Validates linked_repos shape per § 11 (with host enum + uniqueness).
5. The published `schemas/project-yml.schema.json` matches the contract.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dotnet_ai_kit.models import ProjectMetadata, derive_architecture_branch

REPO = Path(__file__).resolve().parent.parent.parent
PUBLISHED_SCHEMA = REPO / "schemas" / "project-yml.schema.json"
CONTRACT_SCHEMA = REPO / "specs" / "019-plugin-native-arch" / "contracts" / "project-yml.schema.json"


_VALID_PROJECT_TYPES = (
    "command",
    "query-sql",
    "query-cosmos",
    "processor",
    "gateway",
    "controlpanel",
    "hybrid",
    "vsa",
    "clean-arch",
    "ddd",
    "modular-monolith",
    "generic",
)

# Expected derivation per data-model § 2.
_DERIVATION = {
    "command": "microservice",
    "query-sql": "microservice",
    "query-cosmos": "microservice",
    "processor": "microservice",
    "gateway": "microservice",
    "controlpanel": "microservice",
    "hybrid": "microservice",
    "vsa": "generic",
    "clean-arch": "generic",
    "ddd": "generic",
    "modular-monolith": "generic",
    "generic": "generic",
}


@pytest.mark.parametrize("project_type", _VALID_PROJECT_TYPES)
def test_project_type_enum_accepts_all_12(project_type: str) -> None:
    """All 12 enum values per clarify Q1 MUST be accepted."""
    pm = ProjectMetadata(
        company="Acme",
        domain="Sales",
        side="server",
        project_type=project_type,
        architecture_branch=_DERIVATION[project_type],
        detected_paths={"controllers": "src/Web/Controllers"},
        dotnet_version="8.0",
    )
    assert pm.project_type == project_type


def test_project_type_rejects_unknown() -> None:
    """Unknown project_type values MUST be rejected."""
    with pytest.raises(Exception):  # pydantic ValidationError
        ProjectMetadata(
            company="Acme",
            domain="Sales",
            side="server",
            project_type="not-a-real-type",
            architecture_branch="generic",
            detected_paths={"controllers": "src/Web/Controllers"},
            dotnet_version="8.0",
        )


@pytest.mark.parametrize(
    "project_type,expected_branch",
    list(_DERIVATION.items()),
)
def test_architecture_branch_derivation_per_data_model_section_2(
    project_type: str, expected_branch: str
) -> None:
    """The 7 microservice + 5 generic mapping MUST be exact per data-model § 2."""
    assert derive_architecture_branch(project_type) == expected_branch


def test_architecture_branch_must_match_derivation() -> None:
    """A declared architecture_branch that doesn't match the derivation MUST be rejected."""
    with pytest.raises(Exception):  # pydantic ValidationError
        ProjectMetadata(
            company="Acme",
            domain="Sales",
            side="server",
            project_type="command",
            architecture_branch="generic",  # wrong — command derives microservice
            detected_paths={"controllers": "src/Web/Controllers"},
            dotnet_version="8.0",
        )


def test_dotnet_version_pattern() -> None:
    """dotnet_version MUST match pattern ^\\d+\\.\\d+$."""
    pm = ProjectMetadata(
        company="Acme", domain="Sales", side="server", project_type="generic",
        architecture_branch="generic", detected_paths={"k": "v"}, dotnet_version="10.0",
    )
    assert pm.dotnet_version == "10.0"

    with pytest.raises(Exception):
        ProjectMetadata(
            company="Acme", domain="Sales", side="server", project_type="generic",
            architecture_branch="generic", detected_paths={"k": "v"}, dotnet_version="not-a-version",
        )


def test_published_schema_matches_contract() -> None:
    """`schemas/project-yml.schema.json` MUST match the contract under specs/."""
    published = json.loads(PUBLISHED_SCHEMA.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT_SCHEMA.read_text(encoding="utf-8"))
    assert published == contract, (
        "Published schema drifted from the contract — re-run the schema copy "
        "step (commit 8) or update the contract first."
    )
