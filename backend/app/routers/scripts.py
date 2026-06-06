"""Script retrieval endpoint.

Returns the latest generated screenplay (ScriptV1 JSON) for a project, parsed
from the persisted YAML in the ``scripts`` table.
"""

import uuid

import yaml
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.script import Script

router = APIRouter(prefix="/api/projects/{project_id}/script", tags=["script"])


@router.get("", response_model=dict)
async def get_script(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the persisted ScriptV1 (as JSON) for a project.

    404 if no script has been generated yet (the project hasn't been converted).
    """
    result = await db.execute(
        select(Script).where(Script.project_id == project_id)
    )
    script = result.scalar_one_or_none()
    if not script or not script.yaml_content:
        raise HTTPException(status_code=404, detail="尚未生成剧本")
    try:
        return yaml.safe_load(script.yaml_content)
    except Exception:
        raise HTTPException(status_code=500, detail="剧本数据解析失败")
