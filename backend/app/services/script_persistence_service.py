"""Persist a ScriptV1 into normalized database tables.

This is the first phase of moving from static YAML storage to DB-as-source-of-truth.
For now the YAML string is still written to ``scripts.yaml_content`` for backward
compatibility, but scenes/blocks/characters are also stored as relational rows.
"""

import uuid

import yaml
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.character import Character
from app.models.script import Block, Scene, Script
from app.schemas.script import ScriptV1


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
