"""Pydantic schemas for Project API."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectStatus(str, Enum):
    """Project lifecycle states."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectCreate(BaseModel):
    """Request body for creating a project."""

    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    target_format: str = Field(default="movie", pattern="^(movie|tv_series|stage_play)$")


class ProjectUpdate(BaseModel):
    """Request body for updating a project. All fields optional."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    config: Optional[dict] = None


class ProjectResponse(BaseModel):
    """Response model for a project."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    status: str
    config: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Stats populated by router via JOIN queries
    chapter_count: int = 0
    scene_count: int = 0
    character_count: int = 0
