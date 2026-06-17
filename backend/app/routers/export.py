"""Script export endpoints."""

import io
import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.script import ScriptV1
from app.services.export_service import ExportService
from app.services.script_persistence_service import ScriptPersistenceService

router = APIRouter(prefix="/api/projects/{project_id}/export", tags=["export"])


def _content_disposition(filename: str) -> str:
    """Build RFC 5987 / RFC 6266 Content-Disposition header."""
    ascii_name = "".join(
        c if c.isascii() and (c.isalnum() or c in "._-") else "_" for c in filename
    )
    encoded = quote(filename, safe="")
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded}"


async def _load_script(db: AsyncSession, project_id: uuid.UUID) -> ScriptV1:
    """Load the project's script from normalized DB rows."""
    script = await ScriptPersistenceService.load_script(db, project_id)
    if script is None:
        raise HTTPException(status_code=404, detail="该项目暂无剧本")
    return script


@router.get("/yaml")
async def export_yaml(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export script as YAML."""
    script = await _load_script(db, project_id)
    content = ExportService.to_yaml(script)
    return Response(
        content=content,
        media_type="application/x-yaml",
        headers={"Content-Disposition": _content_disposition(f"{script.metadata.title}.yaml")},
    )


@router.get("/fountain")
async def export_fountain(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export script as Fountain."""
    script = await _load_script(db, project_id)
    content = ExportService.to_fountain(script)
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": _content_disposition(f"{script.metadata.title}.fountain")},
    )


@router.get("/pdf")
async def export_pdf(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export script as PDF."""
    script = await _load_script(db, project_id)
    content = ExportService.to_pdf(script)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition(f"{script.metadata.title}.pdf")},
    )


@router.get("/fdx")
async def export_fdx(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export script as Final Draft XML."""
    script = await _load_script(db, project_id)
    content = ExportService.to_fdx(script)
    return Response(
        content=content,
        media_type="application/xml",
        headers={"Content-Disposition": _content_disposition(f"{script.metadata.title}.fdx")},
    )


@router.post("/batch")
async def export_batch(
    project_id: uuid.UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export multiple formats as a ZIP archive."""
    script = await _load_script(db, project_id)
    formats = data.get("formats", ["yaml"])
    content = ExportService.to_zip(script, formats)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/zip",
        headers={"Content-Disposition": _content_disposition(f"{script.metadata.title}.zip")},
    )
