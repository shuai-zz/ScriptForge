"""Project CRUD endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.chapter import Chapter
from app.models.character import Character
from app.models.script import Script
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.project_config import ProjectConfigV1
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _to_response(project: Project) -> dict:
    """Convert ORM object to response dict. Stats populated by caller."""
    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "status": project.status.value if hasattr(project.status, "value") else project.status,
        "config": project.config,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "chapter_count": 0,
        "scene_count": 0,
        "character_count": 0,
    }


async def _enrich_with_stats(
    db: AsyncSession, project_id: uuid.UUID, resp: dict
) -> dict:
    """Add chapter/scene/character counts to a project response."""
    # Chapter count
    result = await db.execute(
        select(func.count(Chapter.id)).where(Chapter.project_id == project_id)
    )
    resp["chapter_count"] = result.scalar() or 0
    # Scene count (scripts.scenes via script_metadata or scene table)
    # Use Script's metadata.total_scenes if available, else count scenes
    result = await db.execute(
        select(func.count(Script.id)).where(Script.project_id == project_id)
    )
    script_exists = (result.scalar() or 0) > 0
    if script_exists:
        result = await db.execute(
            select(Script).where(Script.project_id == project_id)
        )
        script = result.scalar_one_or_none()
        if script and script.script_metadata:
            resp["scene_count"] = script.script_metadata.get("total_scenes", 0)
    # Character count
    result = await db.execute(
        select(func.count(Character.id)).where(Character.project_id == project_id)
    )
    resp["character_count"] = result.scalar() or 0
    return resp


@router.post("", response_model=dict, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new project."""
    config = {"target_format": data.target_format}
    project = await ProjectService.create(
        db,
        name=data.name,
        description=data.description,
        config=config,
    )
    resp = _to_response(project)
    # New project has no chapters/scenes/characters yet
    return resp


@router.get("", response_model=list[dict])
async def list_projects(
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all projects with stats."""
    projects = await ProjectService.list_all(db)
    result = []
    for p in projects:
        resp = _to_response(p)
        await _enrich_with_stats(db, p.id, resp)
        result.append(resp)
    return result


@router.get("/{project_id}", response_model=dict)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a single project by ID."""
    project = await ProjectService.get(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    resp = _to_response(project)
    await _enrich_with_stats(db, project_id, resp)
    return resp


@router.put("/{project_id}", response_model=dict)
async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a project."""
    project = await ProjectService.get(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    updates = {}
    if data.name is not None:
        updates["name"] = data.name
    if data.description is not None:
        updates["description"] = data.description
    if data.status is not None:
        updates["status"] = data.status
    if data.config is not None:
        updates["config"] = data.config

    if updates:
        project = await ProjectService.update(db, project_id, **updates)

    resp = _to_response(project)
    await _enrich_with_stats(db, project_id, resp)
    return resp


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a project and all related data (chapters, scripts, etc.)."""
    deleted = await ProjectService.delete(db, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")


# ── Config endpoints ──


@router.get("/{project_id}/config", response_model=dict)
async def get_project_config(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Read project configuration. Returns defaults if no config stored."""
    project = await ProjectService.get(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.config:
        try:
            cfg = ProjectConfigV1.model_validate(project.config)
            return cfg.model_dump(mode="json")
        except Exception:
            # Return raw config if validation fails (evolving schemas)
            return project.config
    # Return defaults
    cfg = ProjectConfigV1()
    return cfg.model_dump(mode="json")


@router.put("/{project_id}/config", response_model=dict)
async def update_project_config(
    project_id: uuid.UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update project configuration. Validates against ProjectConfigV1."""
    project = await ProjectService.get(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        cfg = ProjectConfigV1.model_validate(data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"配置验证失败: {e}")

    await ProjectService.update(db, project_id, config=cfg.model_dump(mode="json"))
    return cfg.model_dump(mode="json")
