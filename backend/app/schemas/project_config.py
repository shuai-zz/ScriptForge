"""Pydantic model for project-config-v1.yaml."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProviderType(str, Enum):
    """LLM provider backend type."""

    ANTHROPIC = "anthropic"
    OPENAI_COMPATIBLE = "openai_compatible"


class PipelineStage(str, Enum):
    """Pipeline stage that a provider can be assigned to."""

    STAGE_0 = "stage_0"
    STAGE_1 = "stage_1"
    STAGE_2 = "stage_2"


class TargetFormat(str, Enum):
    """Screenplay target format."""

    MOVIE = "movie"
    TV_SERIES = "tv_series"
    STAGE_PLAY = "stage_play"


class Language(str, Enum):
    """Output language code."""

    ZH = "zh"
    EN = "en"


class SceneTitleStyle(str, Enum):
    """Scene title localization style."""

    INTERNATIONAL = "international"
    CHINESE = "chinese"


class DialogueNameStyle(str, Enum):
    """How character names appear in dialogue headers."""

    FULL_NAME = "full_name"
    NICKNAME = "nickname"
    ROLE = "role"


class AnnotationDetailLevel(str, Enum):
    """Verbosity of AI-generated annotations."""

    MINIMAL = "minimal"
    STANDARD = "standard"
    VERBOSE = "verbose"


class DialoguePreservation(str, Enum):
    """How original novel dialogue is handled during conversion."""

    REWRITE = "rewrite"
    PRESERVE = "preserve"
    ENHANCE = "enhance"


class ExportFormat(str, Enum):
    """Supported export formats."""

    YAML = "yaml"
    PDF = "pdf"
    FOUNTAIN = "fountain"
    FDX = "fdx"


class ProviderParameters(BaseModel):
    """Model-specific inference parameters."""

    model_config = ConfigDict(extra="allow")

    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    thinking: Optional[bool] = None


class LLMProvider(BaseModel):
    """Configured LLM provider with encrypted credentials."""

    model_config = ConfigDict(extra="allow")

    provider_id: str
    label: str
    provider_type: ProviderType
    model_name: str
    base_url: Optional[str] = None
    encrypted_api_key: str
    assigned_stages: list[PipelineStage] = Field(default_factory=list)
    parameters: ProviderParameters = Field(default_factory=ProviderParameters)


class ConversionParams(BaseModel):
    """User-tunable adaptation behaviour."""

    model_config = ConfigDict(extra="allow")

    target_format: TargetFormat = TargetFormat.MOVIE
    language: Language = Language.ZH
    scene_title_style: SceneTitleStyle = SceneTitleStyle.CHINESE
    dialogue_name_style: DialogueNameStyle = DialogueNameStyle.FULL_NAME
    annotation_detail_level: AnnotationDetailLevel = AnnotationDetailLevel.STANDARD
    auto_split: bool = True
    dialogue_preservation: DialoguePreservation = DialoguePreservation.PRESERVE


class InputChapter(BaseModel):
    """A novel chapter uploaded for conversion."""

    model_config = ConfigDict(extra="allow")

    chapter_number: int = Field(ge=1)
    title: str
    word_count: int = Field(ge=0)


class OutputSettings(BaseModel):
    """Export destination and format preferences."""

    model_config = ConfigDict(extra="allow")

    formats: list[ExportFormat] = Field(default_factory=list)
    destination: Optional[str] = None


class ProjectConfigV1(BaseModel):
    """Root model for project-config-v1.yaml."""

    model_config = ConfigDict(extra="allow")

    schema_version: str = "1.0"
    schema_name: str = "scriptforge-project-config"
    llm_providers: list[LLMProvider] = Field(default_factory=list)
    conversion_params: ConversionParams = Field(default_factory=ConversionParams)
    input_chapters: list[InputChapter] = Field(default_factory=list)
    output_settings: OutputSettings = Field(default_factory=OutputSettings)
