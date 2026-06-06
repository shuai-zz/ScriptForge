"""Annotation CRUD service."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.annotation import Annotation
from app.schemas.annotation_api import AnnotationCreate, AnnotationUpdate


class AnnotationService:
    """Business logic for annotation management."""

    @staticmethod
    async def create(
        db: AsyncSession,
        project_id: uuid.UUID,
        data: AnnotationCreate,
    ) -> Annotation:
        annotation = Annotation(
            project_id=project_id,
            annotation_id=data.annotation_id,
            severity=data.severity.value,
            category=data.category,
            title=data.title,
            description=data.description,
            target_reference=data.target_reference.model_dump(mode="json"),
            alternatives=[a.model_dump(mode="json") for a in data.alternatives],
            confidence=data.confidence,
            auto_applied=data.auto_applied,
            source_quote=data.source_quote,
        )
        db.add(annotation)
        await db.commit()
        await db.refresh(annotation)
        return annotation

    @staticmethod
    async def get(db: AsyncSession, annotation_id: uuid.UUID) -> Annotation | None:
        result = await db.execute(
            select(Annotation).where(Annotation.id == annotation_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_project(
        db: AsyncSession,
        project_id: uuid.UUID,
        *,
        severity: str | None = None,
        category: str | None = None,
        status: str | None = None,
        confidence_min: float | None = None,
        confidence_max: float | None = None,
        target_type: str | None = None,
        block_id: str | None = None,
    ) -> list[Annotation]:
        stmt = select(Annotation).where(Annotation.project_id == project_id)

        if severity:
            stmt = stmt.where(Annotation.severity == severity)
        if category:
            stmt = stmt.where(Annotation.category == category)
        if status:
            stmt = stmt.where(Annotation.status == status)
        if confidence_min is not None:
            stmt = stmt.where(Annotation.confidence >= confidence_min)
        if confidence_max is not None:
            stmt = stmt.where(Annotation.confidence <= confidence_max)
        if target_type:
            stmt = stmt.where(
                Annotation.target_reference["type"].astext == target_type
            )
        if block_id:
            stmt = stmt.where(
                Annotation.target_reference["block_id"].astext == block_id
            )

        stmt = stmt.order_by(Annotation.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update(
        db: AsyncSession,
        annotation_id: uuid.UUID,
        data: AnnotationUpdate,
    ) -> Annotation | None:
        annotation = await AnnotationService.get(db, annotation_id)
        if not annotation:
            return None

        if data.status is not None:
            annotation.status = data.status.value
        if data.title is not None:
            annotation.title = data.title
        if data.description is not None:
            annotation.description = data.description
        if data.confidence is not None:
            annotation.confidence = data.confidence

        await db.commit()
        await db.refresh(annotation)
        return annotation

    @staticmethod
    async def delete(db: AsyncSession, annotation_id: uuid.UUID) -> bool:
        annotation = await AnnotationService.get(db, annotation_id)
        if not annotation:
            return False
        await db.delete(annotation)
        await db.commit()
        return True

    @staticmethod
    async def set_status(
        db: AsyncSession,
        annotation_id: uuid.UUID,
        status: str,
    ) -> Annotation | None:
        annotation = await AnnotationService.get(db, annotation_id)
        if not annotation:
            return None
        annotation.status = status
        await db.commit()
        await db.refresh(annotation)
        return annotation
