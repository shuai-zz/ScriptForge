"""Pydantic schemas for Version Management API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CheckpointCreate(BaseModel):
    """Request body for creating a checkpoint."""

    yaml_content: str = Field(min_length=1)
    message: str = Field(min_length=1, max_length=500)
    tag: Optional[str] = Field(default=None, max_length=100)


class CheckpointResponse(BaseModel):
    """Response for a successful checkpoint."""

    version_id: str
    message: str
    committed_at: str
    author: str


class VersionEntry(BaseModel):
    """A single version in the timeline."""

    version_id: str
    short_id: str
    message: str
    committed_at: str
    author: str
    tags: list[str]


class VersionListResponse(BaseModel):
    """List of versions."""

    versions: list[VersionEntry]


class VersionDiffResponse(BaseModel):
    """Diff between two versions."""

    diff: str
    added_lines: int
    removed_lines: int


class VersionRestoreRequest(BaseModel):
    """Request body for restoring a version."""

    version_id: str


class VersionRestoreResponse(BaseModel):
    """Response after restoring a version."""

    restored_version: str
    pre_restore_version: Optional[str] = None
    restore_commit: str
