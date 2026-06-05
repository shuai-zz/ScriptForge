"""Pydantic schemas for LLM Provider API."""

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProviderType(str, Enum):
    """LLM provider backend type."""

    ANTHROPIC = "anthropic"
    OPENAI_COMPATIBLE = "openai_compatible"


class PipelineStage(str, Enum):
    """Pipeline stage assignment."""

    STAGE_0 = "stage_0"
    STAGE_1 = "stage_1"
    STAGE_2 = "stage_2"


class ProviderParameters(BaseModel):
    """Model-specific inference parameters."""

    model_config = ConfigDict(extra="allow")

    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    thinking: Optional[bool] = None


class ProviderCreate(BaseModel):
    """Request body for creating a provider."""

    label: str
    provider_type: ProviderType
    model_name: str
    base_url: Optional[str] = None
    api_key: str  # plaintext, encrypted server-side
    assigned_stages: list[PipelineStage] = Field(default_factory=list)
    parameters: ProviderParameters = Field(default_factory=ProviderParameters)


class ProviderUpdate(BaseModel):
    """Request body for updating a provider."""

    label: Optional[str] = None
    provider_type: Optional[ProviderType] = None
    model_name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None  # if provided, re-encrypt
    assigned_stages: Optional[list[PipelineStage]] = None
    parameters: Optional[ProviderParameters] = None


class ProviderResponse(BaseModel):
    """Response model — api_key is never returned in plaintext."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    provider_id: str
    label: str
    provider_type: str
    model_name: str
    base_url: Optional[str] = None
    api_key_masked: str  # sk-***...***XyZ
    assigned_stages: list[str]
    parameters: Optional[dict] = None
