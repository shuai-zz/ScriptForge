"""Character and CharacterRelationship CRUD endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.character import Character, CharacterRelationship
from app.services.character_service import CharacterRelationshipService, CharacterService

router = APIRouter(prefix="/api/projects/{project_id}/characters", tags=["characters"])


def _char_to_dict(c: Character) -> dict:
    return {
        "id": str(c.id),
        "name": c.name,
        "aliases": c.aliases,
        "role_type": c.role_type.value if hasattr(c.role_type, "value") else c.role_type,
        "traits": c.traits,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _rel_to_dict(r: CharacterRelationship) -> dict:
    return {
        "id": str(r.id),
        "source_character_id": str(r.source_character_id),
        "target_character_id": str(r.target_character_id),
        "type": r.type,
        "intensity": r.intensity,
    }


@router.post("", response_model=dict, status_code=201)
async def create_character(
    project_id: uuid.UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new character for a project."""
    char = await CharacterService.create(
        db,
        project_id=project_id,
        name=data["name"],
        role_type=data.get("role_type", "supporting"),
        aliases=data.get("aliases", []),
        traits=data.get("traits", []),
    )
    return _char_to_dict(char)


@router.get("", response_model=list[dict])
async def list_characters(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all characters for a project."""
    chars = await CharacterService.list_by_project(db, project_id)
    return [_char_to_dict(c) for c in chars]


# ── Relationships ──
#
# IMPORTANT: the literal ``/relationships`` routes must be declared BEFORE the
# ``/{character_id}`` routes below. FastAPI/Starlette matches routes in
# declaration order, so if ``/{character_id}`` came first a request to
# ``/relationships`` would bind ``character_id="relationships"`` and fail UUID
# validation with a 422 — which previously broke the character relationship
# graph.


@router.get("/relationships", response_model=list[dict])
async def list_relationships(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all character relationships for a project."""
    rels = await CharacterRelationshipService.list_by_project(db, project_id)
    return [_rel_to_dict(r) for r in rels]


@router.post("/relationships", response_model=dict, status_code=201)
async def create_relationship(
    project_id: uuid.UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a relationship between two characters."""
    source_id = data.get("source_character_id")
    target_id = data.get("target_character_id")
    if not source_id or not target_id:
        raise HTTPException(
            status_code=422,
            detail="source_character_id 和 target_character_id 不能为空",
        )
    rel = await CharacterRelationshipService.create(
        db,
        project_id=project_id,
        source_character_id=uuid.UUID(source_id),
        target_character_id=uuid.UUID(target_id),
        type=data["type"],
        intensity=data.get("intensity", 3),
    )
    return _rel_to_dict(rel)


@router.delete("/relationships/{relationship_id}", status_code=204)
async def delete_relationship(
    project_id: uuid.UUID,
    relationship_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a character relationship."""
    deleted = await CharacterRelationshipService.delete(db, relationship_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Relationship not found")


# ── Single character by ID ──


@router.get("/{character_id}", response_model=dict)
async def get_character(
    project_id: uuid.UUID,
    character_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a single character."""
    char = await CharacterService.get(db, character_id)
    if not char or char.project_id != project_id:
        raise HTTPException(status_code=404, detail="Character not found")
    return _char_to_dict(char)


@router.put("/{character_id}", response_model=dict)
async def update_character(
    project_id: uuid.UUID,
    character_id: uuid.UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a character."""
    char = await CharacterService.get(db, character_id)
    if not char or char.project_id != project_id:
        raise HTTPException(status_code=404, detail="Character not found")

    updates = {}
    if "name" in data:
        updates["name"] = data["name"]
    if "role_type" in data:
        updates["role_type"] = data["role_type"]
    if "aliases" in data:
        updates["aliases"] = data["aliases"]
    if "traits" in data:
        updates["traits"] = data["traits"]

    char = await CharacterService.update(db, character_id, **updates)
    return _char_to_dict(char)


@router.delete("/{character_id}", status_code=204)
async def delete_character(
    project_id: uuid.UUID,
    character_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a character."""
    char = await CharacterService.get(db, character_id)
    if not char or char.project_id != project_id:
        raise HTTPException(status_code=404, detail="Character not found")
    await CharacterService.delete(db, character_id)
