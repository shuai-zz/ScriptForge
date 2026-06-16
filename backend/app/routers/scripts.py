"""Script retrieval endpoint.

Returns the latest generated screenplay (ScriptV1 JSON) for a project,
reconstructed from normalized DB rows when available, otherwise falling back
to the persisted YAML snapshot.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
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
