"""Pydantic schemas for Annotation REST API."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AnnotationStatus(str, Enum):
    """Review status of an annotation."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    IGNORED = "ignored"
    MODIFIED = "modified"


class Severity(str, Enum):
    """Annotation severity level."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUGGESTION = "suggestion"


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
    """An alternative adaptation choice."""

    model_config = ConfigDict(extra="allow")

    alternative_id: str
    text: str
    pros: str
    cons: str


class AnnotationCreate(BaseModel):
    """Request body for creating an annotation."""

    annotation_id: str
    severity: Severity
    category: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    target_reference: TargetReference
    source_quote: Optional[str] = None
    alternatives: list[Alternative] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    auto_applied: bool = False


class AnnotationUpdate(BaseModel):
    """Request body for updating annotation status or content."""

    status: Optional[AnnotationStatus] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, min_length=1)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class AnnotationAction(BaseModel):
    """Request body for performing an action on an annotation."""

    action: str = Field(pattern="^(accept|ignore|modify)$")
    alternative_id: Optional[str] = None  # for modify action
    custom_text: Optional[str] = None  # for modify action


class AnnotationResponse(BaseModel):
    """Response model for an annotation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    annotation_id: str
    severity: str
    category: str
    title: str
    description: str
    target_reference: Optional[dict] = None
    source_quote: Optional[str] = None
    alternatives: list[dict]
    confidence: float
    auto_applied: bool
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AnnotationListParams(BaseModel):
    """Query parameters for listing annotations."""

    severity: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    confidence_min: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    confidence_max: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    target_type: Optional[str] = None
    block_id: Optional[str] = None
