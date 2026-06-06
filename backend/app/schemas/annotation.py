"""Pydantic model for annotation-v1.yaml."""

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class Severity(str, Enum):
    """Annotation severity level."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUGGESTION = "suggestion"


class AnnotationCategory(str, Enum):
    """Controlled vocabulary for adaptation annotation categories."""

    ADAPTATION_DECISION = "adaptation_decision"
    INNER_TO_VISUAL = "inner_to_visual"
    PACING_SUGGESTION = "pacing_suggestion"
    CHARACTER_CONSISTENCY = "character_consistency"
    DIALOGUE_ENHANCEMENT = "dialogue_enhancement"
    SCENE_SPLIT_MERGE = "scene_split_merge"
    FORESHADOWING = "foreshadowing"
    FORMAT_MISMATCH = "format_mismatch"


class TargetType(str, Enum):
    """What the annotation refers to."""

    SCENE = "scene"
    BLOCK = "block"
    CHARACTER = "character"
    GLOBAL = "global"


class TargetReference(BaseModel):
    """Pointer to the annotated element."""

    model_config = ConfigDict(extra="allow")

    type: TargetType
    scene_id: Optional[str] = None
    block_id: Optional[str] = None
    character_id: Optional[str] = None


class Alternative(BaseModel):
    """An alternative adaptation choice with trade-off analysis."""

    model_config = ConfigDict(extra="allow")

    alternative_id: str
    text: str
    pros: str
    cons: str


class AnnotationV1(BaseModel):
    """Root model for annotation-v1.yaml."""

    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"] = "1.0"
    schema_name: Literal["scriptforge-annotation"] = "scriptforge-annotation"
    annotation_id: str
    severity: Severity
    category: AnnotationCategory
    target_reference: TargetReference
    title: str
    description: str
    source_quote: Optional[str] = None
    alternatives: list[Alternative] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    auto_applied: bool = False
    created_at: Optional[datetime] = None
