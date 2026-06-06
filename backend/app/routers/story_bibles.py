"""Story Bible read endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.story_bible import StoryBible

router = APIRouter(prefix="/api/projects/{project_id}/story-bible", tags=["story-bible"])


@router.get("", response_model=dict)
async def get_story_bible(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the Story Bible for a project."""
    result = await db.execute(
        select(StoryBible).where(StoryBible.project_id == project_id)
    )
    bible = result.scalar_one_or_none()
    if not bible:
        raise HTTPException(status_code=404, detail="该项目暂无故事圣经")

    return {
        "id": str(bible.id),
        "project_id": str(bible.project_id),
        "content": bible.content,
        "created_at": bible.created_at.isoformat() if bible.created_at else None,
        "updated_at": bible.updated_at.isoformat() if bible.updated_at else None,
    }
