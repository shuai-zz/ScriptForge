"""Annotation REST endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.annotation_api import (
    AnnotationAction,
    AnnotationCreate,
    AnnotationResponse,
    AnnotationUpdate,
)
from app.services.annotation_service import AnnotationService

router = APIRouter(prefix="/api/projects/{project_id}/annotations", tags=["annotations"])


def _to_response(annotation) -> dict:
    return {
        "id": str(annotation.id),
        "project_id": str(annotation.project_id),
        "annotation_id": annotation.annotation_id,
        "severity": annotation.severity,
        "category": annotation.category,
        "title": annotation.title,
        "description": annotation.description,
        "target_reference": annotation.target_reference,
        "source_quote": getattr(annotation, "source_quote", None),
        "alternatives": annotation.alternatives,
        "confidence": annotation.confidence,
        "auto_applied": annotation.auto_applied,
        "status": annotation.status,
        "created_at": annotation.created_at,
        "updated_at": annotation.updated_at,
    }


@router.post("", response_model=dict, status_code=201)
async def create_annotation(
    project_id: uuid.UUID,
    data: AnnotationCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new annotation for a project."""
    annotation = await AnnotationService.create(db, project_id, data)
    return _to_response(annotation)


@router.get("", response_model=list[dict])
async def list_annotations(
    project_id: uuid.UUID,
    severity: str | None = Query(None),
    category: str | None = Query(None),
    status: str | None = Query(None),
    confidence_min: float | None = Query(None, ge=0.0, le=1.0),
    confidence_max: float | None = Query(None, ge=0.0, le=1.0),
    target_type: str | None = Query(None),
    block_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List annotations with optional filtering."""
    annotations = await AnnotationService.list_by_project(
        db,
        project_id,
        severity=severity,
        category=category,
        status=status,
        confidence_min=confidence_min,
        confidence_max=confidence_max,
        target_type=target_type,
        block_id=block_id,
    )
    return [_to_response(a) for a in annotations]


@router.get("/{annotation_id}", response_model=dict)
async def get_annotation(
    project_id: uuid.UUID,
    annotation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a single annotation."""
    annotation = await AnnotationService.get(db, annotation_id)
    if not annotation or annotation.project_id != project_id:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return _to_response(annotation)


@router.put("/{annotation_id}", response_model=dict)
async def update_annotation(
    project_id: uuid.UUID,
    annotation_id: uuid.UUID,
    data: AnnotationUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update an annotation (status, title, description, confidence)."""
    annotation = await AnnotationService.get(db, annotation_id)
    if not annotation or annotation.project_id != project_id:
        raise HTTPException(status_code=404, detail="Annotation not found")
    updated = await AnnotationService.update(db, annotation_id, data)
    return _to_response(updated)


@router.post("/{annotation_id}/action", response_model=dict)
async def annotation_action(
    project_id: uuid.UUID,
    annotation_id: uuid.UUID,
    data: AnnotationAction,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Perform an action on an annotation: accept, ignore, or modify."""
    annotation = await AnnotationService.get(db, annotation_id)
    if not annotation or annotation.project_id != project_id:
        raise HTTPException(status_code=404, detail="Annotation not found")

    status_map = {
        "accept": "accepted",
        "ignore": "ignored",
        "modify": "modified",
    }
    new_status = status_map.get(data.action)
    if not new_status:
        raise HTTPException(status_code=400, detail=f"Invalid action: {data.action}")

    updated = await AnnotationService.set_status(db, annotation_id, new_status)
    return _to_response(updated)


@router.delete("/{annotation_id}", status_code=204)
async def delete_annotation(
    project_id: uuid.UUID,
    annotation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an annotation."""
    annotation = await AnnotationService.get(db, annotation_id)
    if not annotation or annotation.project_id != project_id:
        raise HTTPException(status_code=404, detail="Annotation not found")
    await AnnotationService.delete(db, annotation_id)
