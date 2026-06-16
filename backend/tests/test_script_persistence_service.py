"""Tests for ScriptPersistenceService — converting ScriptV1 into DB rows."""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.database import async_session_factory
from app.models.character import Character
from app.models.project import Project
from app.models.script import Block, Scene, Script
from app.schemas.script import (
    BlockType,
    LocationType,
    RoleType,
    ScriptBlock,
    ScriptCharacter,
    ScriptMetadata,
    ScriptV1,
    Slug,
    TimeOfDay,
)
from app.schemas.script import (
    Scene as SceneSchema,
)
from app.services.script_persistence_service import ScriptPersistenceService

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest_asyncio.fixture(loop_scope="session")
async def db():
    async with async_session_factory() as session:
        yield session


@pytest_asyncio.fixture(loop_scope="session")
async def project(db):
    p = Project(name=f"persist-test-{uuid.uuid4().hex[:8]}")
    db.add(p)
    await db.commit()
    await db.refresh(p)
    yield p
    # Cascade cleanup
    refreshed = await db.get(Project, p.id)
    if refreshed:
        await db.delete(refreshed)
        await db.commit()


def _make_script() -> ScriptV1:
    return ScriptV1(
        metadata=ScriptMetadata(
            title="Test Script",
            source_novel="Test Novel",
            total_scenes=1,
            estimated_runtime=5,
        ),
        characters=[
            ScriptCharacter(
                character_id="char_001",
                name="Alice",
                role_type=RoleType.PROTAGONIST,
                aliases=["A"],
                traits=["brave"],
            ),
            ScriptCharacter(
                character_id="char_002",
                name="Bob",
                role_type=RoleType.SUPPORTING,
                aliases=[],
                traits=["funny"],
            ),
        ],
        scenes=[
            SceneSchema(
                scene_id="scene_1",
                scene_number=1,
                slug=Slug(
                    location_type=LocationType.INT,
                    location_name="Room",
                    time=TimeOfDay.DAY,
                ),
                summary="Alice and Bob talk.",
                characters_present=["char_001", "char_002"],
                props=["cup"],
                blocks=[
                    ScriptBlock(
                        block_id="b1",
                        order=0,
                        type=BlockType.ACTION,
                        text="Alice enters.",
                    ),
                    ScriptBlock(
                        block_id="b2",
                        order=1,
                        type=BlockType.DIALOGUE,
                        char_id="char_001",
                        char_name="Alice",
                        line="Hi.",
                    ),
                ],
            )
        ],
    )


async def test_persist_script_creates_rows(db, project):
    script = _make_script()
    await ScriptPersistenceService.persist_script(db, project.id, script)

    # Script row
    result = await db.execute(select(Script).where(Script.project_id == project.id))
    script_row = result.scalar_one()
    assert script_row.version == "1.0"
    assert script_row.script_metadata["title"] == "Test Script"
    assert script_row.yaml_content
    assert "Test Script" in script_row.yaml_content

    # Characters upserted by name
    result = await db.execute(
        select(Character).where(Character.project_id == project.id).order_by(Character.name)
    )
    chars = result.scalars().all()
    assert len(chars) == 2
    assert {c.name for c in chars} == {"Alice", "Bob"}

    # Scene row
    result = await db.execute(
        select(Scene).where(Scene.script_id == script_row.id)
    )
    scene = result.scalar_one()
    assert scene.scene_number == 1
    assert scene.location_name == "Room"
    assert scene.time == "DAY"
    assert len(scene.characters_present) == 2
    assert scene.props == ["cup"]

    # Block rows
    result = await db.execute(
        select(Block).where(Block.scene_id == scene.id).order_by(Block.order)
    )
    blocks = result.scalars().all()
    assert len(blocks) == 2
    assert blocks[0].type == "action"
    assert blocks[0].text == "Alice enters."
    assert blocks[1].type == "dialogue"
    assert blocks[1].line == "Hi."
    assert blocks[1].char_name == "Alice"
    assert blocks[1].char_id == chars[0].id  # Alice


async def test_persist_script_replaces_previous_scenes_and_blocks(db, project):
    script = _make_script()
    await ScriptPersistenceService.persist_script(db, project.id, script)

    # Second run with fewer scenes/blocks and updated character aliases
    script2 = ScriptV1(
        metadata=ScriptMetadata(title="Test Script 2"),
        characters=[
            ScriptCharacter(
                character_id="char_001",
                name="Alice",
                role_type=RoleType.PROTAGONIST,
                aliases=["A", "Alicia"],
                traits=["brave", "smart"],
            ),
        ],
        scenes=[
            SceneSchema(
                scene_id="scene_2",
                scene_number=1,
                slug=Slug(
                    location_type=LocationType.EXT,
                    location_name="Street",
                    time=TimeOfDay.NIGHT,
                ),
                summary="Alice walks.",
                characters_present=["char_001"],
                props=[],
                blocks=[
                    ScriptBlock(
                        block_id="b3",
                        order=0,
                        type=BlockType.ACTION,
                        text="Alice walks.",
                    )
                ],
            )
        ],
    )
    await ScriptPersistenceService.persist_script(db, project.id, script2)

    result = await db.execute(
        select(Script).where(Script.project_id == project.id)
    )
    script_row = result.scalar_one()

    scenes = (
        await db.execute(select(Scene).where(Scene.script_id == script_row.id))
    ).scalars().all()
    assert len(scenes) == 1
    assert scenes[0].location_name == "Street"

    blocks = (
        await db.execute(select(Block).where(Block.scene_id == scenes[0].id))
    ).scalars().all()
    assert len(blocks) == 1
    assert blocks[0].text == "Alice walks."

    # Alice aliases updated, Bob removed
    chars = (
        await db.execute(
            select(Character).where(Character.project_id == project.id)
        )
    ).scalars().all()
    assert len(chars) == 1
    assert chars[0].aliases == ["A", "Alicia"]
    assert chars[0].traits == ["brave", "smart"]
