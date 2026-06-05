"""Project CRUD service."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectStatus


class ProjectService:
    """Business logic for project management."""

    @staticmethod
    async def create(
        db: AsyncSession,
        name: str,
        description: str | None = None,
        config: dict | None = None,
    ) -> Project:
        project = Project(
            name=name,
            description=description,
            config=config,
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project

    @staticmethod
    async def get(db: AsyncSession, project_id: uuid.UUID) -> Project | None:
        result = await db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_all(db: AsyncSession) -> list[Project]:
        result = await db.execute(select(Project).order_by(Project.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def update(
        db: AsyncSession,
        project_id: uuid.UUID,
        **kwargs,
    ) -> Project | None:
        project = await ProjectService.get(db, project_id)
        if not project:
            return None

        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)

        project.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(project)
        return project

    @staticmethod
    async def delete(db: AsyncSession, project_id: uuid.UUID) -> bool:
        project = await ProjectService.get(db, project_id)
        if not project:
            return False
        await db.delete(project)
        await db.commit()
        return True
