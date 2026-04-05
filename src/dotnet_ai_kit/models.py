"""Pydantic v2 models for dotnet-ai-kit configuration and project detection."""

from __future__ import annotations

import logging
import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Known path keys for detected_paths validation
# ---------------------------------------------------------------------------

KNOWN_PATH_KEYS: frozenset[str] = frozenset(
    {
        "aggregates",
        "events",
        "commands",
        "handlers",
        "entities",
        "tests",
        "test_live",
        "persistence",
        "controllers",
        "cosmos_entities",
        "cosmos_repositories",
        "features",
        "pages",
        "components",
    }
)

# ---------------------------------------------------------------------------
# Detection signal models (used by signal-based detection pipeline)
# ---------------------------------------------------------------------------

_SIGNAL_TYPES = {"naming", "code-pattern", "structural", "build-config"}
_CONFIDENCE_LEVELS = {"high", "medium", "low"}
_CONFIDENCE_WEIGHTS = {"high": 3, "medium": 2, "low": 1}


class DetectionSignal(BaseModel):
    """A single indicator found during project analysis."""

    pattern_name: str = Field(description="Human-readable name, e.g. 'AggregateRoot base class'.")
    signal_type: str = Field(description="One of: naming, code-pattern, structural, build-config.")
    target_project_type: str = Field(description="Project type this signal supports.")
    confidence: str = Field(default="medium", description="high, medium, or low.")
    weight: int = Field(default=2, description="Scoring weight derived from confidence level.")
    evidence: str = Field(default="", description="File path + matched line.")
    is_negative: bool = Field(default=False, description="If True, reduces confidence for target.")

    @field_validator("signal_type")
    @classmethod
    def validate_signal_type(cls, v: str) -> str:
        if v.lower() not in _SIGNAL_TYPES:
            raise ValueError(f"signal_type must be one of {_SIGNAL_TYPES}, got '{v}'")
        return v.lower()

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: str) -> str:
        if v.lower() not in _CONFIDENCE_LEVELS:
            raise ValueError(f"confidence must be one of {_CONFIDENCE_LEVELS}, got '{v}'")
        return v.lower()


class DetectionScoreCard(BaseModel):
    """Internal scoring used to determine classification for a candidate project type."""

    project_type: str = Field(description="The candidate project type.")
    positive_score: float = Field(default=0.0, description="Sum of positive signal weights.")
    negative_score: float = Field(default=0.0, description="Sum of negative signal weights.")
    net_score: float = Field(default=0.0, description="positive_score - negative_score.")
    signal_count: int = Field(default=0, description="Number of signals contributing.")


# Valid C# identifier pattern: starts with letter or underscore, then letters/digits/underscores
_CSHARP_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Valid GitHub org/user pattern
_GITHUB_ORG_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9\-]*[A-Za-z0-9])?$")

# GitHub URL normalization patterns
_GITHUB_HTTPS_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/.]+?)(?:\.git)?/?$")
_GITHUB_SSH_RE = re.compile(r"^git@github\.com:([^/]+)/([^/.]+?)(?:\.git)?$")


class CompanyConfig(BaseModel):
    """Company-level configuration used in namespaces and repo naming."""

    name: str = Field(
        default="",
        description="Company name. Used in C# namespaces — must be a valid C# identifier.",
    )
    github_org: str = Field(
        default="",
        description="GitHub organization name for cloning repos.",
    )
    default_branch: str = Field(
        default="main",
        description="Default git branch name (main, master, develop).",
    )

    @field_validator("name")
    @classmethod
    def validate_company_name(cls, v: str) -> str:
        if v and not _CSHARP_IDENTIFIER_RE.match(v):
            raise ValueError(
                f"Company name '{v}' is not a valid C# identifier. "
                "Use letters, digits, and underscores only. Must start with a letter or underscore."
            )
        return v

    @field_validator("github_org")
    @classmethod
    def validate_github_org(cls, v: str) -> str:
        if v and not _GITHUB_ORG_RE.match(v):
            raise ValueError(
                f"GitHub org '{v}' is not a valid GitHub organization name. "
                "Use letters, digits, and hyphens only."
            )
        return v


class NamingConfig(BaseModel):
    """Naming convention patterns using {Company}, {Domain}, {Side}, {Layer} placeholders."""

    domain: str = Field(
        default="Domain",
        description="Domain name for template rendering (e.g., 'Draw', 'Order', 'Invoice').",
    )
    solution: str = Field(
        default="{Company}.{Domain}.{Side}",
        description="Solution naming pattern.",
    )
    topic: str = Field(
        default="{company}-{domain}-{side}",
        description="Service Bus topic naming pattern (lowercase).",
    )
    namespace: str = Field(
        default="{Company}.{Domain}.{Side}.{Layer}",
        description="C# namespace pattern.",
    )


class ReposConfig(BaseModel):
    """Repository paths or GitHub references for each microservice role.

    Each value is either a local filesystem path or a GitHub reference
    in the format 'github:org/repo'.
    """

    command: Optional[str] = Field(
        default=None,
        description="Path or github:org/repo for the Command service.",
    )
    query: Optional[str] = Field(
        default=None,
        description="Path or github:org/repo for the Query service.",
    )
    processor: Optional[str] = Field(
        default=None,
        description="Path or github:org/repo for the Processor service.",
    )
    gateway: Optional[str] = Field(
        default=None,
        description="Path or github:org/repo for the Gateway service.",
    )
    controlpanel: Optional[str] = Field(
        default=None,
        description="Path or github:org/repo for the Control Panel.",
    )

    @field_validator("command", "query", "processor", "gateway", "controlpanel", mode="before")
    @classmethod
    def validate_repo_path(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize repo path.

        Accepts: None, local path, 'github:org/repo',
        GitHub HTTPS URL, or git SSH URL.
        GitHub URLs are normalized to 'github:org/repo' format.
        """
        if v is None:
            return v
        if not isinstance(v, str) or not v.strip():
            msg = "Repo path must be None, 'github:org/repo', or non-empty."
            raise ValueError(msg)
        v = v.strip()

        # Normalize GitHub HTTPS URLs → github:org/repo
        m = _GITHUB_HTTPS_RE.match(v)
        if m:
            return f"github:{m.group(1)}/{m.group(2)}"

        # Normalize git SSH URLs → github:org/repo
        m = _GITHUB_SSH_RE.match(v)
        if m:
            return f"github:{m.group(1)}/{m.group(2)}"

        return v


_KNOWN_CONFIG_KEYS: frozenset[str] = frozenset(
    {
        "version",
        "company",
        "naming",
        "repos",
        "permissions_level",
        "ai_tools",
        "command_style",
        "linked_from",
    }
)


class DotnetAiConfig(BaseModel):
    """Main configuration model for dotnet-ai-kit.

    Stored in .dotnet-ai-kit/config.yml.
    """

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def warn_unknown_keys(cls, values: object) -> object:
        """Log a warning for any unrecognised top-level config keys."""
        if isinstance(values, dict):
            for key in values:
                if key not in _KNOWN_CONFIG_KEYS:
                    logger.warning(
                        "Unknown config key '%s' will be ignored. Known keys: %s",
                        key,
                        ", ".join(sorted(_KNOWN_CONFIG_KEYS)),
                    )
        return values

    version: str = Field(
        default="1.0",
        description="Configuration schema version.",
    )
    company: CompanyConfig = Field(
        default_factory=CompanyConfig,
        description="Company-level settings.",
    )
    naming: NamingConfig = Field(
        default_factory=NamingConfig,
        description="Naming convention patterns.",
    )
    repos: ReposConfig = Field(
        default_factory=ReposConfig,
        description="Repository paths for microservice roles.",
    )
    permissions_level: str = Field(
        default="standard",
        description="Permission level: minimal, standard, or full.",
    )
    managed_permissions: list[str] = Field(
        default_factory=list,
        description="Permission entries managed by the tool, used for merge diffs.",
    )
    ai_tools: list[str] = Field(
        default_factory=list,
        description="List of configured AI tools (claude).",
    )
    command_style: str = Field(
        default="both",
        description="Command file style: full, short, or both.",
    )
    linked_from: Optional[str] = Field(
        default=None,
        description="Path to the primary repo that deployed tooling to this secondary repo.",
    )

    @field_validator("permissions_level")
    @classmethod
    def validate_permissions(cls, v: str) -> str:
        allowed = {"minimal", "standard", "full"}
        if v.lower() not in allowed:
            raise ValueError(f"permissions_level must be one of {allowed}, got '{v}'")
        return v.lower()

    @field_validator("command_style")
    @classmethod
    def validate_command_style(cls, v: str) -> str:
        allowed = {"full", "short", "both"}
        if v.lower() not in allowed:
            raise ValueError(f"command_style must be one of {allowed}, got '{v}'")
        return v.lower()

    @field_validator("ai_tools")
    @classmethod
    def validate_ai_tools(cls, v: list[str]) -> list[str]:
        allowed = {"claude", "cursor", "copilot", "codex"}
        for tool in v:
            if tool.lower() not in allowed:
                raise ValueError(f"Unknown AI tool '{tool}'. Must be one of {allowed}.")
        return [t.lower() for t in v]


class DetectedProject(BaseModel):
    """Detected project information from scanning a .NET project.

    Stored in .dotnet-ai-kit/project.yml.
    """

    mode: str = Field(
        default="generic",
        description="Project mode: microservice or generic.",
    )
    project_type: str = Field(
        default="generic",
        description=(
            "Detected project type: command, query-sql, query-cosmos, processor, "
            "gateway, controlpanel, vsa, clean-arch, ddd, modular-monolith, generic."
        ),
    )
    dotnet_version: str = Field(
        default="",
        description="Detected .NET version (e.g., '10.0').",
    )
    architecture: str = Field(
        default="",
        description="Detected or configured architecture description.",
    )
    namespace_format: str = Field(
        default="",
        description="Detected namespace format from existing code.",
    )
    packages: list[str] = Field(
        default_factory=list,
        description="List of detected NuGet packages.",
    )
    confidence: str = Field(
        default="",
        description="Detection confidence: high, medium, low, or empty if not scored.",
    )
    confidence_score: float = Field(
        default=0.0,
        description="Numeric confidence score between 0.0 and 1.0.",
    )
    user_override: Optional[str] = Field(
        default=None,
        description="User's manual override of the detected project type, or None.",
    )
    top_signals: list[dict] = Field(
        default_factory=list,
        description="Top 3 signals that contributed most to classification (serialized).",
    )
    detected_paths: Optional[dict[str, str]] = Field(
        default=None,
        description="Logical path categories mapped to filesystem paths relative to project root.",
    )

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        allowed = {"microservice", "generic"}
        if v.lower() not in allowed:
            raise ValueError(f"mode must be one of {allowed}, got '{v}'")
        return v.lower()

    @field_validator("project_type")
    @classmethod
    def validate_project_type(cls, v: str) -> str:
        allowed = {
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
        }
        if v.lower() not in allowed:
            raise ValueError(f"project_type must be one of {allowed}, got '{v}'")
        return v.lower()

    @field_validator("confidence")
    @classmethod
    def validate_confidence_level(cls, v: str) -> str:
        if v and v.lower() not in {"high", "medium", "low"}:
            raise ValueError(f"confidence must be high, medium, low, or empty — got '{v}'")
        return v.lower() if v else ""

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence_score(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError(f"confidence_score must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator("detected_paths")
    @classmethod
    def validate_detected_paths(cls, v: dict[str, str] | None) -> dict[str, str] | None:
        if v is not None:
            for key in v:
                if key not in KNOWN_PATH_KEYS:
                    logger.warning(
                        "Unknown detected_paths key: %s. Known keys: %s",
                        key,
                        ", ".join(sorted(KNOWN_PATH_KEYS)),
                    )
        return v


# ---------------------------------------------------------------------------
# Feature Brief model (for cross-repo brief projection)
# ---------------------------------------------------------------------------

_BRIEF_PHASES = {
    "specified",
    "planned",
    "tasks-generated",
    "implementing",
    "implemented",
    "blocked",
}


class FeatureBrief(BaseModel):
    """Projected feature brief written to secondary repos.

    Stored in .dotnet-ai-kit/briefs/{source-repo}/{NNN}-{name}/feature-brief.md.
    """

    feature_name: str = Field(description="Feature display name.")
    feature_id: str = Field(description="Feature ID in NNN-short-name format.")
    projected_date: str = Field(description="ISO date when the brief was projected.")
    phase: str = Field(
        default="specified",
        description=(
            "Lifecycle phase: specified, planned, tasks-generated,"
            " implementing, implemented, blocked."
        ),
    )
    source_repo: str = Field(description="Source repo directory name.")
    source_path: str = Field(description="Local path or github:org/repo of source repo.")
    source_feature_path: str = Field(
        description="Relative path to source feature dir (e.g. .dotnet-ai-kit/features/001-name/).",
    )
    role: str = Field(default="", description="This repo's role in the feature.")
    required_changes: list[str] = Field(
        default_factory=list,
        description="List of required changes for this repo.",
    )
    events_produces: list[str] = Field(
        default_factory=list,
        description="Events this repo produces.",
    )
    events_consumes: list[str] = Field(
        default_factory=list,
        description="Events this repo consumes.",
    )
    tasks: list[dict] = Field(
        default_factory=list,
        description="Filtered task list: each dict has id, description, file, done.",
    )
    blocked_by: list[str] = Field(
        default_factory=list,
        description="Upstream repos that must complete first.",
    )
    blocks: list[str] = Field(
        default_factory=list,
        description="Downstream repos waiting on this repo.",
    )
    implementation_approach: str = Field(
        default="",
        description="Architecture decisions relevant to this repo from plan.",
    )

    @field_validator("phase")
    @classmethod
    def validate_phase(cls, v: str) -> str:
        if v.lower() not in _BRIEF_PHASES:
            raise ValueError(f"phase must be one of {_BRIEF_PHASES}, got '{v}'")
        return v.lower()

    @field_validator("feature_id")
    @classmethod
    def validate_feature_id(cls, v: str) -> str:
        if not re.match(r"^\d{3}-[a-z0-9-]+$", v):
            raise ValueError(
                f"feature_id must match NNN-short-name format (e.g. '001-order-export'), got '{v}'"
            )
        return v
