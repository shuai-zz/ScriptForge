"""Script export endpoints."""

import io
import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.script import ScriptV1
from app.services.export_service import ExportService

router = APIRouter(prefix="/api/projects/{project_id}/export", tags=["export"])


def _content_disposition(filename: str) -> str:
    """Build RFC 5987 / RFC 6266 Content-Disposition header."""
    ascii_name = "".join(c if c.isascii() and (c.isalnum() or c in "._-") else "_" for c in filename)
    encoded = quote(filename, safe="")
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded}"


# Demo script for export preview (mirrors frontend demo data)
def _demo_script() -> ScriptV1:
    return ScriptV1(
        schema_version="1.0",
        schema_name="scriptforge-script",
        metadata={
            "title": "三体",
            "subtitle": "第一部：地球往事",
            "source_novel": "三体",
            "source_author": "刘慈欣",
            "schema_version": "1.0",
            "total_scenes": 3,
            "estimated_runtime": 120,
        },
        characters=[
            {
                "character_id": "c1",
                "name": "汪淼",
                "aliases": ["淼淼"],
                "role_type": "protagonist",
                "age": 40,
                "gender": "男",
                "archetype": "科学家",
                "traits": ["理性", "好奇", "坚韧"],
                "arc_summary": "从怀疑到觉醒的科学家",
            },
            {
                "character_id": "c2",
                "name": "丁仪",
                "aliases": [],
                "role_type": "supporting",
                "age": 35,
                "gender": "男",
                "archetype": "物理学家",
                "traits": ["玩世不恭", "天才", "悲观"],
                "arc_summary": "揭示真相的物理学家",
            },
        ],
        scenes=[
            {
                "scene_id": "s1",
                "scene_number": 1,
                "slug": {
                    "location_type": "INT.",
                    "location_name": "汪淼家 - 客厅",
                    "time": "NIGHT",
                },
                "summary": "汪淼发现照片上的倒计时",
                "characters_present": ["c1"],
                "props": ["相机", "照片"],
                "blocks": [
                    {
                        "block_id": "b1",
                        "order": 0,
                        "type": "action",
                        "text": "汪淼坐在沙发上，手里拿着一叠照片。台灯的光线下，他的脸色苍白。",
                        "annotation_refs": [],
                    },
                    {
                        "block_id": "b2",
                        "order": 1,
                        "type": "dialogue",
                        "char_id": "c1",
                        "char_name": "汪淼",
                        "line": "这不可能...每一张照片上都有数字。",
                        "parenthetical": "颤抖着声音",
                        "annotation_refs": [],
                    },
                ],
                "annotations": [],
            },
            {
                "scene_id": "s2",
                "scene_number": 2,
                "slug": {
                    "location_type": "EXT.",
                    "location_name": "台球厅",
                    "time": "DAY",
                },
                "summary": "丁仪用台球比喻解释物理定律的崩溃",
                "characters_present": ["c1", "c2"],
                "props": ["台球", "球杆"],
                "blocks": [
                    {
                        "block_id": "b3",
                        "order": 0,
                        "type": "action",
                        "text": "台球厅里烟雾缭绕。丁仪拿起一支球杆，对准白球。",
                        "annotation_refs": [],
                    },
                    {
                        "block_id": "b4",
                        "order": 1,
                        "type": "dialogue",
                        "char_id": "c2",
                        "char_name": "丁仪",
                        "line": "想象一下，如果物理定律在不同的地方、不同的时间是不一样的，会怎样？",
                        "parenthetical": "吐出一口烟",
                        "annotation_refs": [],
                    },
                    {
                        "block_id": "b5",
                        "order": 2,
                        "type": "dialogue",
                        "char_id": "c1",
                        "char_name": "汪淼",
                        "line": "那科学就不存在了。",
                        "annotation_refs": ["a1"],
                    },
                ],
                "annotations": [],
            },
        ],
        scene_index=[
            {
                "scene_id": "s1",
                "scene_number": 1,
                "slug_line": "INT. 汪淼家 - 客厅 - NIGHT",
                "characters": ["c1"],
                "page_estimate": 1.5,
            },
            {
                "scene_id": "s2",
                "scene_number": 2,
                "slug_line": "EXT. 台球厅 - DAY",
                "characters": ["c1", "c2"],
                "page_estimate": 2,
            },
        ],
        global_annotations=[],
    )


@router.get("/yaml")
async def export_yaml(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export script as YAML."""
    script = _demo_script()
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
    script = _demo_script()
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
    script = _demo_script()
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
    script = _demo_script()
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
    script = _demo_script()
    formats = data.get("formats", ["yaml"])
    content = ExportService.to_zip(script, formats)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/zip",
        headers={"Content-Disposition": _content_disposition(f"{script.metadata.title}.zip")},
    )
