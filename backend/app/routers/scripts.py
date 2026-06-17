"""Script retrieval and update endpoints.

Returns or replaces the latest generated screenplay (ScriptV1 JSON) for a
project, using normalized scenes/blocks/characters rows as the source of truth.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.project import Project
from app.schemas.script import ScriptV1
from app.services.script_persistence_service import ScriptPersistenceService

router = APIRouter(prefix="/api/projects/{project_id}/script", tags=["script"])


@router.get("", response_model=dict)
async def get_script(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the persisted ScriptV1 (as JSON) for a project.

    404 if no script has been generated yet (the project hasn't been converted).
    """
    script = await ScriptPersistenceService.load_script(db, project_id)
    if script is None:
        raise HTTPException(status_code=404, detail="尚未生成剧本")
    return script.model_dump(mode="json")


@router.put("", response_model=dict)
async def update_script(
    project_id: uuid.UUID,
    script: ScriptV1,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Replace the project's script with the provided ScriptV1.

    The payload is validated and persisted to scenes/blocks/characters rows.
    """
    result = await db.execute(select(Project).where(Project.id == project_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="项目不存在")

    await ScriptPersistenceService.persist_script(db, project_id, script)
    updated = await ScriptPersistenceService.load_script(db, project_id)
    if updated is None:
        raise HTTPException(status_code=500, detail="保存后读取剧本失败")
    return updated.model_dump(mode="json")
