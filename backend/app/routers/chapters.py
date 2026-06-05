"""Chapter CRUD endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.chapter import (
    ChapterCreate,
    ChapterListItem,
    ChapterReorder,
    ChapterResponse,
    ChapterUpdate,
)
from app.services.chapter_service import ChapterService

router = APIRouter(prefix="/api/projects/{project_id}/chapters", tags=["chapters"])


def _to_list_item(ch) -> dict:
    return {
        "id": str(ch.id),
        "number": ch.number,
        "title": ch.title,
        "word_count": ch.word_count,
        "status": ch.status.value if hasattr(ch.status, "value") else ch.status,
        "created_at": ch.created_at,
        "updated_at": ch.updated_at,
    }


def _to_response(ch) -> dict:
    return {
        "id": str(ch.id),
        "project_id": str(ch.project_id),
        "number": ch.number,
        "title": ch.title,
        "raw_text": ch.raw_text,
        "word_count": ch.word_count,
        "status": ch.status.value if hasattr(ch.status, "value") else ch.status,
        "created_at": ch.created_at,
        "updated_at": ch.updated_at,
    }


@router.post("", response_model=dict, status_code=201)
async def create_chapter(
    project_id: uuid.UUID,
    data: ChapterCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a chapter with auto-assigned number."""
    chapter = await ChapterService.create(
        db,
        project_id=project_id,
        title=data.title,
        raw_text=data.raw_text,
        number=data.number,
    )
    return _to_response(chapter)


@router.post("/upload", response_model=dict, status_code=201)
async def upload_chapter(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upload a chapter via .txt or .md file."""
    if file.content_type and file.content_type not in (
        "text/plain",
        "text/markdown",
        "text/x-markdown",
        "application/octet-stream",
    ):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}。请上传 .txt 或 .md 文件。",
        )

    content = await file.read()
    try:
        raw_text = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            raw_text = content.decode("gbk")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="无法解码文件内容，请使用 UTF-8 编码")

    # Derive title from filename
    title = file.filename.rsplit(".", 1)[0] if file.filename else "未命名章节"

    chapter = await ChapterService.create(
        db,
        project_id=project_id,
        title=title,
        raw_text=raw_text,
    )
    return _to_response(chapter)


@router.get("", response_model=list[dict])
async def list_chapters(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all chapters for a project (metadata only, no raw_text)."""
    chapters = await ChapterService.list_by_project(db, project_id)
    return [_to_list_item(c) for c in chapters]


@router.get("/{chapter_id}", response_model=dict)
async def get_chapter(
    project_id: uuid.UUID,
    chapter_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a single chapter including raw_text."""
    chapter = await ChapterService.get(db, chapter_id)
    if not chapter or chapter.project_id != project_id:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return _to_response(chapter)


@router.put("/reorder", response_model=dict)
async def reorder_chapters(
    project_id: uuid.UUID,
    data: ChapterReorder,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Reorder chapters by providing an ordered list of chapter IDs."""
    ids = [uuid.UUID(cid) for cid in data.order]
    await ChapterService.reorder(db, project_id, ids)
    chapters = await ChapterService.list_by_project(db, project_id)
    return {"order": [str(c.id) for c in chapters], "message": "排序已更新"}


@router.put("/{chapter_id}", response_model=dict)
async def update_chapter(
    project_id: uuid.UUID,
    chapter_id: uuid.UUID,
    data: ChapterUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a chapter."""
    chapter = await ChapterService.get(db, chapter_id)
    if not chapter or chapter.project_id != project_id:
        raise HTTPException(status_code=404, detail="Chapter not found")

    updates = {}
    if data.title is not None:
        updates["title"] = data.title
    if data.number is not None:
        updates["number"] = data.number
    if data.raw_text is not None:
        updates["raw_text"] = data.raw_text
        updates["word_count"] = len(data.raw_text)
    if data.status is not None:
        updates["status"] = data.status

    if updates:
        chapter = await ChapterService.update(db, chapter_id, **updates)

    return _to_response(chapter)


@router.delete("/{chapter_id}", status_code=204)
async def delete_chapter(
    project_id: uuid.UUID,
    chapter_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a chapter."""
    chapter = await ChapterService.get(db, chapter_id)
    if not chapter or chapter.project_id != project_id:
        raise HTTPException(status_code=404, detail="Chapter not found")
    await ChapterService.delete(db, chapter_id)
