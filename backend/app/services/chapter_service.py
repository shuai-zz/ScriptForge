"""Chapter CRUD service."""

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chapter import Chapter, ChapterStatus


class ChapterService:
    """Business logic for chapter management."""

    @staticmethod
    async def create(
        db: AsyncSession,
        project_id: uuid.UUID,
        title: str,
        raw_text: str,
        number: int | None = None,
    ) -> Chapter:
        """Create a chapter, auto-assigning number if not provided."""
        if number is None:
            result = await db.execute(
                select(func.coalesce(func.max(Chapter.number), 0)).where(
                    Chapter.project_id == project_id
                )
            )
            number = (result.scalar() or 0) + 1

        chapter = Chapter(
            project_id=project_id,
            number=number,
            title=title,
            raw_text=raw_text,
            word_count=len(raw_text),
        )
        db.add(chapter)
        await db.commit()
        await db.refresh(chapter)
        return chapter

    @staticmethod
    async def get(db: AsyncSession, chapter_id: uuid.UUID) -> Chapter | None:
        result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_project(
        db: AsyncSession,
        project_id: uuid.UUID,
    ) -> list[Chapter]:
        result = await db.execute(
            select(Chapter)
            .where(Chapter.project_id == project_id)
            .order_by(Chapter.number)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update(
        db: AsyncSession,
        chapter_id: uuid.UUID,
        **kwargs,
    ) -> Chapter | None:
        chapter = await ChapterService.get(db, chapter_id)
        if not chapter:
            return None

        for key, value in kwargs.items():
            if hasattr(chapter, key):
                setattr(chapter, key, value)

        await db.commit()
        await db.refresh(chapter)
        return chapter

    @staticmethod
    async def delete(db: AsyncSession, chapter_id: uuid.UUID) -> bool:
        chapter = await ChapterService.get(db, chapter_id)
        if not chapter:
            return False
        await db.delete(chapter)
        await db.commit()
        return True

    @staticmethod
    async def reorder(
        db: AsyncSession, project_id: uuid.UUID, chapter_ids: list[uuid.UUID]
    ) -> None:
        """Reassign chapter numbers based on the ordered list of IDs.

        Renumbering happens in two phases to avoid transiently violating the
        ``(project_id, number)`` unique constraint when chapters swap places:
        first park every chapter at a unique negative number and flush, then
        assign the final ``1..N`` sequence. The intermediate flush is required —
        without it SQLAlchemy collapses each object's negative-then-final write
        into a single UPDATE, reintroducing the collision.
        """
        chapters: list[Chapter] = []
        for cid in chapter_ids:
            ch = await ChapterService.get(db, cid)
            if ch and ch.project_id == project_id:
                chapters.append(ch)
        if not chapters:
            return

        # Phase 1: park at negative numbers that cannot collide with live rows.
        for offset, ch in enumerate(chapters, start=1):
            ch.number = -offset
        await db.flush()

        # Phase 2: assign the final positions.
        for idx, ch in enumerate(chapters, start=1):
            ch.number = idx
        await db.commit()
