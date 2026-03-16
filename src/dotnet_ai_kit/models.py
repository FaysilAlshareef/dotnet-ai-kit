"""Pydantic v2 models for dotnet-ai-kit configuration and project detection."""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# Valid C# identifier pattern: starts with letter or underscore, then letters/digits/underscores
_CSHARP_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Valid GitHub org/user pattern
_GITHUB_ORG_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9\-]*[A-Za-z0-9])?$")


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


class CodeRabbitConfig(BaseModel):
    """CodeRabbit integration settings."""

    enabled: bool = Field(
        default=False,
        description="Whether CodeRabbit integration is enabled.",
    )
    auto_fix: bool = Field(
        default=False,
        description="Whether CodeRabbit auto-fix suggestions are applied.",
    )
    severity_threshold: str = Field(
        default="warning",
        description="Minimum severity level for CodeRabbit findings.",
    )

    @field_validator("severity_threshold")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = {"info", "warning", "error"}
        if v.lower() not in allowed:
            raise ValueError(
                f"severity_threshold must be one of {allowed}, got '{v}'"
            )
        return v.lower()


class IntegrationsConfig(BaseModel):
    """External tool integrations."""

    coderabbit: CodeRabbitConfig = Field(
        default_factory=CodeRabbitConfig,
        description="CodeRabbit integration configuration.",
    )


class DotnetAiConfig(BaseModel):
    """Main configuration model for dotnet-ai-kit.

    Stored in .dotnet-ai-kit/config.yml.
    """

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
    integrations: IntegrationsConfig = Field(
        default_factory=IntegrationsConfig,
        description="External tool integration settings.",
    )
    permissions_level: str = Field(
        default="standard",
        description="Permission level: minimal, standard, or full.",
    )
    ai_tools: list[str] = Field(
        default_factory=list,
        description="List of configured AI tools (claude, cursor, copilot, codex, antigravity).",
    )
    command_style: str = Field(
        default="both",
        description="Command file style: full, short, or both.",
    )

    @field_validator("permissions_level")
    @classmethod
    def validate_permissions(cls, v: str) -> str:
        allowed = {"minimal", "standard", "full"}
        if v.lower() not in allowed:
            raise ValueError(
                f"permissions_level must be one of {allowed}, got '{v}'"
            )
        return v.lower()

    @field_validator("command_style")
    @classmethod
    def validate_command_style(cls, v: str) -> str:
        allowed = {"full", "short", "both"}
        if v.lower() not in allowed:
            raise ValueError(
                f"command_style must be one of {allowed}, got '{v}'"
            )
        return v.lower()

    @field_validator("ai_tools")
    @classmethod
    def validate_ai_tools(cls, v: list[str]) -> list[str]:
        allowed = {"claude", "cursor", "copilot", "codex", "antigravity"}
        for tool in v:
            if tool.lower() not in allowed:
                raise ValueError(
                    f"Unknown AI tool '{tool}'. Must be one of {allowed}."
                )
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
            "vsa",
            "clean-arch",
            "ddd",
            "modular-monolith",
            "generic",
        }
        if v.lower() not in allowed:
            raise ValueError(
                f"project_type must be one of {allowed}, got '{v}'"
            )
        return v.lower()
