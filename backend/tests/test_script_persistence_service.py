"""Tests for ScriptPersistenceService — converting ScriptV1 into DB rows."""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.database import async_session_factory
from app.models.annotation import Annotation
from app.models.character import Character
from app.models.project import Project
from app.models.script import Block, Scene, Script
from app.schemas.annotation import (
    Alternative,
    AnnotationCategory,
    AnnotationV1,
    Severity,
    TargetReference,
)
from app.schemas.script import (
    BlockType,
    LocationType,
    RoleType,
    ScriptBlock,
    ScriptCharacter,
    ScriptMetadata,
    ScriptV1,
    Slug,
    SourceRef,
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
                        source_ref=SourceRef(chapter=1, paragraph=1, quote="Alice enters."),
                    ),
                    ScriptBlock(
                        block_id="b2",
                        order=1,
                        type=BlockType.DIALOGUE,
                        char_id="char_001",
                        char_name="Alice",
                        line="Hi.",
                        source_ref=SourceRef(chapter=1, paragraph=2, quote="Hi."),
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

    # Second run with fewer scenes/blocks and updated character aliases.
    # The conversion pipeline opts in to stale-character cleanup.
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
    await ScriptPersistenceService.persist_script(
        db, project.id, script2, delete_missing_characters=True
    )

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


async def test_persist_script_keeps_missing_characters_by_default(db, project):
    script = _make_script()
    await ScriptPersistenceService.persist_script(db, project.id, script)

    script2 = ScriptV1(
        metadata=ScriptMetadata(title="Test Script 2"),
        characters=[
            ScriptCharacter(
                character_id="char_001",
                name="Alice",
                role_type=RoleType.PROTAGONIST,
                aliases=["A"],
                traits=["brave"],
            ),
        ],
        scenes=[],
    )
    await ScriptPersistenceService.persist_script(db, project.id, script2)

    chars = (
        await db.execute(
            select(Character).where(Character.project_id == project.id)
        )
    ).scalars().all()
    assert len(chars) == 2


async def test_persist_script_replace_annotations_translates_target_ids(
    db, project
):
    script = _make_script()
    script.annotations = [
        AnnotationV1(
            annotation_id="ann-block-001",
            severity=Severity.SUGGESTION,
            category=AnnotationCategory.INNER_TO_VISUAL,
            title="内心独白外化",
            description="建议把内心独白改为动作呈现。",
            confidence=0.85,
            target_reference=TargetReference(
                type="block", scene_id="scene_1", block_id="b1"
            ),
            alternatives=[
                Alternative(
                    alternative_id="alt-001",
                    text="保留独白",
                    pros="忠实原著",
                    cons="削弱悬疑",
                )
            ],
        ),
        AnnotationV1(
            annotation_id="ann-global-001",
            severity=Severity.WARNING,
            category=AnnotationCategory.PACING_SUGGESTION,
            title="节奏建议",
            description="前两场景都是室内夜戏，节奏偏慢。",
            confidence=0.78,
            target_reference=TargetReference(type="global"),
        ),
    ]

    await ScriptPersistenceService.persist_script(
        db, project.id, script, replace_annotations=True
    )

    anns = (
        await db.execute(
            select(Annotation).where(Annotation.project_id == project.id)
        )
    ).scalars().all()
    assert len(anns) == 2

    by_id = {a.annotation_id: a for a in anns}
    block_ann = by_id["ann-block-001"]
    assert block_ann.severity == "suggestion"
    assert block_ann.category == "inner_to_visual"
    assert block_ann.target_reference["type"] == "block"
    # Client IDs must have been translated to DB UUIDs.
    assert block_ann.target_reference["scene_id"] != "scene_1"
    assert block_ann.target_reference["block_id"] != "b1"
    assert len(block_ann.alternatives) == 1

    global_ann = by_id["ann-global-001"]
    assert global_ann.target_reference["type"] == "global"


async def test_persist_script_replace_annotations_deletes_old_ones(db, project):
    script = _make_script()
    script.annotations = [
        AnnotationV1(
            annotation_id="ann-old",
            severity=Severity.INFO,
            category=AnnotationCategory.ADAPTATION_DECISION,
            title="Old",
            description="Old annotation.",
            confidence=0.5,
            target_reference=TargetReference(type="global"),
        )
    ]
    await ScriptPersistenceService.persist_script(
        db, project.id, script, replace_annotations=True
    )

    script.annotations = [
        AnnotationV1(
            annotation_id="ann-new",
            severity=Severity.INFO,
            category=AnnotationCategory.ADAPTATION_DECISION,
            title="New",
            description="New annotation.",
            confidence=0.6,
            target_reference=TargetReference(type="global"),
        )
    ]
    await ScriptPersistenceService.persist_script(
        db, project.id, script, replace_annotations=True
    )

    anns = (
        await db.execute(
            select(Annotation).where(Annotation.project_id == project.id)
        )
    ).scalars().all()
    assert len(anns) == 1
    assert anns[0].annotation_id == "ann-new"
