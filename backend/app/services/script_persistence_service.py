"""Persist a ScriptV1 into normalized database tables.

This is the first phase of moving from static YAML storage to DB-as-source-of-truth.
For now the YAML string is still written to ``scripts.yaml_content`` for backward
compatibility, but scenes/blocks/characters are also stored as relational rows.
"""

import uuid

import yaml
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.character import Character
from app.models.script import Block, Scene, Script
from app.schemas.script import (
    Scene as SceneSchema,
)
from app.schemas.script import (
    SceneIndexEntry,
    ScriptBlock,
    ScriptCharacter,
    ScriptMetadata,
    ScriptV1,
    Slug,
    SourceRef,
)


class ScriptPersistenceService:
    """Convert a ScriptV1 into database rows."""

    @staticmethod
    async def _upsert_character(
        db: AsyncSession,
        project_id: uuid.UUID,
        script_char,
    ) -> Character:
        """Get or create a Character row by name within a project."""
        result = await db.execute(
            select(Character).where(
                Character.project_id == project_id,
                Character.name == script_char.name,
            )
        )
        char = result.scalar_one_or_none()
        if char is None:
            char = Character(
                project_id=project_id,
                name=script_char.name,
                role_type=script_char.role_type,
                aliases=list(script_char.aliases or []),
                traits=list(script_char.traits or []),
            )
            db.add(char)
        else:
            char.role_type = script_char.role_type
            char.aliases = list(script_char.aliases or [])
            char.traits = list(script_char.traits or [])
        await db.flush()
        await db.refresh(char)
        return char

    @staticmethod
    async def load_script(
        db: AsyncSession,
        project_id: uuid.UUID,
    ) -> ScriptV1 | None:
        """Reconstruct a ScriptV1 from DB rows, falling back to YAML.

        Returns ``None`` when no script row exists. If scenes have not been
        normalized yet, the legacy ``yaml_content`` field is parsed instead.
        """
        result = await db.execute(
            select(Script).where(Script.project_id == project_id)
        )
        script_row = result.scalar_one_or_none()
        if script_row is None:
            return None

        scene_count = await db.scalar(
            select(func.count(Scene.id)).where(Scene.script_id == script_row.id)
        )
        if not scene_count:
            if not script_row.yaml_content:
                return None
            return ScriptV1.model_validate(yaml.safe_load(script_row.yaml_content))

        char_result = await db.execute(
            select(Character).where(Character.project_id == project_id)
        )
        chars = {str(char.id): char for char in char_result.scalars().all()}

        def _char_name(char_id: str | None) -> str | None:
            return chars[char_id].name if char_id and char_id in chars else None

        script_characters = [
            ScriptCharacter(
                character_id=char_id,
                name=char.name,
                role_type=char.role_type,
                aliases=list(char.aliases or []),
                traits=list(char.traits or []),
            )
            for char_id, char in chars.items()
        ]

        scene_result = await db.execute(
            select(Scene).where(Scene.script_id == script_row.id).order_by(Scene.order)
        )
        scenes: list[SceneSchema] = []
        scene_index: list[SceneIndexEntry] = []
        for scene_row in scene_result.scalars().all():
            block_result = await db.execute(
                select(Block)
                .where(Block.scene_id == scene_row.id)
                .order_by(Block.order)
            )
            blocks: list[ScriptBlock] = []
            for block_row in block_result.scalars().all():
                block = ScriptBlock(
                    block_id=str(block_row.id),
                    order=block_row.order,
                    type=block_row.type,
                    text=block_row.text,
                    line=block_row.line,
                    char_id=str(block_row.char_id) if block_row.char_id else None,
                    char_name=block_row.char_name or _char_name(block_row.char_id),
                    parenthetical=block_row.parenthetical,
                    annotation_refs=list(block_row.annotation_refs or []),
                    source_ref=(
                        SourceRef(**block_row.source_ref)
                        if block_row.source_ref
                        else None
                    ),
                )
                blocks.append(block)

            scene_id = str(scene_row.id)
            scene = SceneSchema(
                scene_id=scene_id,
                scene_number=scene_row.scene_number,
                slug=Slug(
                    location_type=scene_row.location_type,
                    location_name=scene_row.location_name,
                    time=scene_row.time,
                ),
                summary=scene_row.summary,
                characters_present=list(scene_row.characters_present or []),
                props=list(scene_row.props or []),
                blocks=blocks,
            )
            scenes.append(scene)
            scene_index.append(
                SceneIndexEntry(
                    scene_id=scene_id,
                    scene_number=scene_row.scene_number,
                    slug_line=(
                        f"{scene_row.location_type} {scene_row.location_name}"
                        f" - {scene_row.time}"
                    ),
                    summary=scene_row.summary,
                    characters=[
                        _char_name(cid) for cid in (scene_row.characters_present or [])
                    ],
                )
            )

        metadata_dict = dict(script_row.script_metadata)
        metadata_dict["total_scenes"] = len(scenes)
        metadata = ScriptMetadata(**metadata_dict)
        return ScriptV1(
            schema_version=script_row.version or "1.0",
            metadata=metadata,
            characters=script_characters,
            scenes=scenes,
            scene_index=scene_index,
        )

    @staticmethod
    async def persist_script(
        db: AsyncSession,
        project_id: uuid.UUID,
        script: ScriptV1,
    ) -> Script:
        """Persist ``script`` into ``scripts``, ``scenes``, ``blocks`` tables.

        Characters are upserted by name and mapped to their database IDs so that
        ``char_id`` references inside scenes/blocks remain valid.
        """
        # 1) Upsert the script metadata row.
        result = await db.execute(
            select(Script).where(Script.project_id == project_id)
        )
        script_row = result.scalar_one_or_none()
        if script_row is None:
            script_row = Script(
                project_id=project_id,
                yaml_content="",
                script_metadata={},
            )
            db.add(script_row)
            await db.flush()

        script_row.version = script.schema_version or "1.0"
        script_row.script_metadata = (
            script.metadata.model_dump(mode="json") if script.metadata else {}
        )
        script_row.yaml_content = yaml.safe_dump(
            script.model_dump(mode="json"),
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )

        # 2) Upsert characters and build an ID map.
        char_id_map: dict[str, uuid.UUID] = {}
        script_char_names = {script_char.name for script_char in script.characters}
        for script_char in script.characters:
            char = await ScriptPersistenceService._upsert_character(
                db, project_id, script_char
            )
            char_id_map[script_char.character_id] = char.id

        # Remove characters that are no longer in the script snapshot.
        await db.execute(
            delete(Character).where(
                Character.project_id == project_id,
                Character.name.not_in(script_char_names),
            )
        )

        # 3) Replace existing scenes/blocks for this script.
        await db.execute(
            delete(Block).where(
                Block.scene_id.in_(
                    select(Scene.id).where(Scene.script_id == script_row.id)
                )
            )
        )
        await db.execute(delete(Scene).where(Scene.script_id == script_row.id))

        # 4) Insert new scenes and blocks.
        for scene_idx, scene in enumerate(script.scenes):
            scene_row = Scene(
                script_id=script_row.id,
                scene_number=scene.scene_number,
                location_type=scene.slug.location_type.value,
                location_name=scene.slug.location_name,
                time=scene.slug.time.value,
                summary=scene.summary,
                characters_present=[
                    str(char_id_map[cid])
                    for cid in (scene.characters_present or [])
                    if cid in char_id_map
                ],
                props=list(scene.props or []),
                order=scene_idx,
            )
            db.add(scene_row)
            await db.flush()

            for block_idx, block in enumerate(scene.blocks):
                db_char_id = (
                    char_id_map.get(block.char_id) if block.char_id else None
                )
                block_row = Block(
                    scene_id=scene_row.id,
                    order=block_idx,
                    type=block.type.value,
                    text=block.text if block.type.value == "action" else None,
                    line=block.line if block.type.value == "dialogue" else None,
                    char_id=db_char_id,
                    char_name=block.char_name,
                    parenthetical=block.parenthetical,
                    annotation_refs=[
                        ref.annotation_id for ref in (block.annotation_refs or [])
                    ],
                    source_ref=(
                        block.source_ref.model_dump(mode="json")
                        if block.source_ref
                        else None
                    ),
                )
                db.add(block_row)

        await db.commit()
        await db.refresh(script_row)
        return script_row
