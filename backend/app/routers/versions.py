"""Version management REST endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.version import (
    CheckpointCreate,
    CheckpointResponse,
    VersionDiffResponse,
    VersionListResponse,
    VersionRestoreRequest,
    VersionRestoreResponse,
)
from app.services.version_service import VersionService, VersionServiceError

router = APIRouter(prefix="/api/projects/{project_id}/versions", tags=["versions"])


@router.post("/init", status_code=204)
async def init_repo(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Initialize a Git repository for the project."""
    try:
        await VersionService.init_repo(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to init repo: {e}")


@router.post("/checkpoint", response_model=dict)
async def create_checkpoint(
    project_id: uuid.UUID,
    data: CheckpointCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Save script content and create a git checkpoint."""
    try:
        result = await VersionService.checkpoint(
            project_id,
            data.yaml_content,
            data.message,
            data.tag,
        )
        if result is None:
            return {"message": "No changes to commit", "version_id": None}
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Checkpoint failed: {e}")


@router.get("", response_model=list[dict])
async def list_versions(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Get version timeline for a project."""
    try:
        return await VersionService.list_versions(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list versions: {e}")


@router.get("/diff", response_model=dict)
async def get_diff(
    project_id: uuid.UUID,
    a: str,
    b: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get diff between two versions."""
    try:
        return await VersionService.get_diff(project_id, a, b)
    except VersionServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diff failed: {e}")


@router.post("/restore", response_model=dict)
async def restore_version(
    project_id: uuid.UUID,
    data: VersionRestoreRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Restore script to a specific version."""
    try:
        return await VersionService.restore(project_id, data.version_id)
    except VersionServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {e}")


@router.get("/has-changes", response_model=dict)
async def has_changes(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Check if repo has uncommitted changes."""
    try:
        changed = await VersionService.has_changes(project_id)
        return {"has_changes": changed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Check failed: {e}")
