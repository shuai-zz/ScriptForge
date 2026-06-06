"""Character and CharacterRelationship CRUD service."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.character import Character, CharacterRelationship


class CharacterService:
    """Business logic for character management."""

    @staticmethod
    async def create(
        db: AsyncSession,
        project_id: uuid.UUID,
        name: str,
        role_type: str,
        aliases: list[str] | None = None,
        traits: list[str] | None = None,
    ) -> Character:
        char = Character(
            project_id=project_id,
            name=name,
            role_type=role_type,
            aliases=aliases or [],
            traits=traits or [],
        )
        db.add(char)
        await db.commit()
        await db.refresh(char)
        return char

    @staticmethod
    async def get(db: AsyncSession, character_id: uuid.UUID) -> Character | None:
        result = await db.execute(
            select(Character).where(Character.id == character_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_project(
        db: AsyncSession, project_id: uuid.UUID
    ) -> list[Character]:
        result = await db.execute(
            select(Character)
            .where(Character.project_id == project_id)
            .order_by(Character.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update(
        db: AsyncSession,
        character_id: uuid.UUID,
        **kwargs,
    ) -> Character | None:
        char = await CharacterService.get(db, character_id)
        if not char:
            return None

        for key, value in kwargs.items():
            if hasattr(char, key):
                setattr(char, key, value)

        await db.commit()
        await db.refresh(char)
        return char

    @staticmethod
    async def delete(db: AsyncSession, character_id: uuid.UUID) -> bool:
        char = await CharacterService.get(db, character_id)
        if not char:
            return False
        await db.delete(char)
        await db.commit()
        return True


class CharacterRelationshipService:
    """Business logic for character relationships."""

    @staticmethod
    async def create(
        db: AsyncSession,
        project_id: uuid.UUID,
        source_character_id: uuid.UUID,
        target_character_id: uuid.UUID,
        type: str,
        intensity: int,
    ) -> CharacterRelationship:
        rel = CharacterRelationship(
            project_id=project_id,
            source_character_id=source_character_id,
            target_character_id=target_character_id,
            type=type,
            intensity=intensity,
        )
        db.add(rel)
        await db.commit()
        await db.refresh(rel)
        return rel

    @staticmethod
    async def list_by_project(
        db: AsyncSession, project_id: uuid.UUID
    ) -> list[CharacterRelationship]:
        result = await db.execute(
            select(CharacterRelationship)
            .where(CharacterRelationship.project_id == project_id)
            .order_by(CharacterRelationship.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete(db: AsyncSession, relationship_id: uuid.UUID) -> bool:
        result = await db.execute(
            select(CharacterRelationship).where(
                CharacterRelationship.id == relationship_id
            )
        )
        rel = result.scalar_one_or_none()
        if not rel:
            return False
        await db.delete(rel)
        await db.commit()
        return True
