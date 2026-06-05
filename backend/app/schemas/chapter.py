"""Pydantic schemas for Chapter API."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ChapterStatus(str, Enum):
    """Chapter processing states."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class ChapterCreate(BaseModel):
    """Request body for creating a chapter."""

    title: str = Field(min_length=1, max_length=255)
    raw_text: str = Field(min_length=1)
    number: Optional[int] = None  # auto-assigned if omitted
    # For file upload: the frontend sends the content as raw_text


class ChapterUpdate(BaseModel):
    """Request body for updating a chapter. All fields optional."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    number: Optional[int] = Field(default=None, ge=1)
    raw_text: Optional[str] = Field(default=None, min_length=1)
    status: Optional[ChapterStatus] = None


class ChapterListItem(BaseModel):
    """Lightweight chapter info for list view (no raw_text)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    number: int
    title: str
    word_count: int
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChapterResponse(BaseModel):
    """Full chapter response including raw_text."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    number: int
    title: str
    raw_text: str
    word_count: int
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChapterReorder(BaseModel):
    """Request body for reordering chapters."""

    order: list[str]  # list of chapter IDs in desired order
