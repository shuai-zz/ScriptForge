"""Persist a ScriptV1 into normalized database tables.

The database is now the source of truth for scripts: scenes, blocks and
characters are stored as relational rows and reconstructed on read.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.annotation import Annotation
from app.models.character import Character
from app.models.script import Block, Scene, Script
from app.schemas.annotation import (
    Alternative,
    AnnotationCategory,
    AnnotationV1,
    Severity,
    TargetReference,
    TargetType,
)
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
from app.services.validators import ValidationSeverity, ValidatorRunner


# Map validator names to the controlled annotation category vocabulary.
_VALIDATOR_CATEGORY_MAP: dict[str, AnnotationCategory] = {
    "CharacterConsistencyValidator": AnnotationCategory.CHARACTER_CONSISTENCY,
    "CharacterAppearanceValidator": AnnotationCategory.CHARACTER_CONSISTENCY,
    "DialogueActionAlternationValidator": AnnotationCategory.PACING_SUGGESTION,
    "TimelineCoherenceValidator": AnnotationCategory.PACING_SUGGESTION,
    "SlugLineValidator": AnnotationCategory.FORMAT_MISMATCH,
    "SceneNumberContinuityValidator": AnnotationCategory.FORMAT_MISMATCH,
    "SourceRefCoverageValidator": AnnotationCategory.FORMAT_MISMATCH,
}


def _severity_from_validator(severity: ValidationSeverity) -> Severity:
    return Severity(severity.value)


def _target_type_for_finding(finding) -> TargetType:
    if finding.block_id:
        return TargetType.BLOCK
    if finding.scene_id:
        return TargetType.SCENE
    if finding.char_id:
        return TargetType.CHARACTER
    return TargetType.GLOBAL


def _build_validator_annotations(script: ScriptV1) -> list[AnnotationV1]:
    """Run semantic validators and convert their findings into annotations.

    The resulting annotations are attached to the script so they can be persisted
    and surfaced in the script editor sidebar.
    """
    runner = ValidatorRunner()
    report = runner.run(script)
    annotations: list[AnnotationV1] = []

    for finding in report.all_findings:
        annotation_id = f"ann-{uuid.uuid4().hex[:12]}"
        target_ref = TargetReference(
            type=_target_type_for_finding(finding),
            scene_id=finding.scene_id,
            block_id=finding.block_id,
            character_id=finding.char_id,
        )
        annotations.append(
            AnnotationV1(
                annotation_id=annotation_id,
                severity=_severity_from_validator(finding.severity),
                category=_VALIDATOR_CATEGORY_MAP.get(
                    finding.validator, AnnotationCategory.ADAPTATION_DECISION
                ),
                target_reference=target_ref,
                title=finding.validator.replace("Validator", "").replace("_", " "),
                description=finding.message,
                confidence=1.0,
                auto_applied=False,
                created_at=datetime.now(timezone.utc),
            )
        )

    # Link block-level annotations back to their blocks so the editor can show
    # the "N 批注" badge and navigate to the block.
    block_lookup = {
        block.block_id: block
        for scene in script.scenes
        for block in scene.blocks
    }
    for ann in annotations:
        block_id = ann.target_reference.block_id
        if block_id and block_id in block_lookup:
            block = block_lookup[block_id]
            if ann.annotation_id not in block.annotation_refs:
                block.annotation_refs.append(ann.annotation_id)

    return annotations


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
        """Reconstruct a ScriptV1 from normalized DB rows.

        Returns ``None`` when no script row exists or when the script has no
        scenes (e.g. it has not been persisted from a conversion/save yet).
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
            return None

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
        delete_missing_characters: bool = False,
        replace_annotations: bool = False,
    ) -> Script:
        """Persist ``script`` into ``scripts``, ``scenes``, ``blocks`` tables.

        Characters are upserted by name and mapped to their database IDs so that
        ``char_id`` references inside scenes/blocks remain valid.

        By default characters that are not present in ``script`` are left alone
        so that manually-created characters are not accidentally deleted. Pass
        ``delete_missing_characters=True`` to remove stale characters (used by
        the conversion pipeline where the script is the authoritative snapshot).

        When ``replace_annotations=True`` the existing project annotations are
        deleted and recreated from ``script.annotations``. The target IDs inside
        each annotation are translated to the newly created DB UUIDs.
        """
        # 1) Upsert the script metadata row.
        result = await db.execute(
            select(Script).where(Script.project_id == project_id)
        )
        script_row = result.scalar_one_or_none()
        if script_row is None:
            script_row = Script(
                project_id=project_id,
                script_metadata={},
            )
            db.add(script_row)
            await db.flush()

        script_row.version = script.schema_version or "1.0"
        script_row.script_metadata = (
            script.metadata.model_dump(mode="json") if script.metadata else {}
        )

        # 1.5) When replacing annotations, synthesize annotations from semantic
        # validators so the editor sidebar is populated after AI conversion.
        if replace_annotations:
            validator_annotations = _build_validator_annotations(script)
            script.annotations = list(script.annotations or []) + validator_annotations

        # 2) Upsert characters and build an ID map.
        char_id_map: dict[str, uuid.UUID] = {}
        script_char_names = {script_char.name for script_char in script.characters}
        for script_char in script.characters:
            char = await ScriptPersistenceService._upsert_character(
                db, project_id, script_char
            )
            char_id_map[script_char.character_id] = char.id

        # Optionally remove characters that are no longer in the script snapshot.
        if delete_missing_characters:
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

        # 4) Insert new scenes and blocks, keeping client-id -> DB-id maps.
        scene_id_map: dict[str, uuid.UUID] = {}
        block_id_map: dict[str, uuid.UUID] = {}
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
            scene_id_map[scene.scene_id] = scene_row.id

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
                    annotation_refs=list(block.annotation_refs or []),
                    source_ref=(
                        block.source_ref.model_dump(mode="json")
                        if block.source_ref
                        else None
                    ),
                )
                db.add(block_row)
                await db.flush()
                block_id_map[block.block_id] = block_row.id

        # 5) Optionally replace annotations and translate target IDs to DB UUIDs.
        if replace_annotations:
            await db.execute(
                delete(Annotation).where(Annotation.project_id == project_id)
            )
            for ann in script.annotations:
                target = ann.target_reference.model_dump(mode="json")
                if target.get("type") == "scene":
                    client_scene_id = target.get("scene_id")
                    if client_scene_id in scene_id_map:
                        target["scene_id"] = str(scene_id_map[client_scene_id])
                elif target.get("type") == "block":
                    client_scene_id = target.get("scene_id")
                    client_block_id = target.get("block_id")
                    if client_scene_id in scene_id_map:
                        target["scene_id"] = str(scene_id_map[client_scene_id])
                    if client_block_id in block_id_map:
                        target["block_id"] = str(block_id_map[client_block_id])
                elif target.get("type") == "character":
                    client_char_id = target.get("character_id")
                    if client_char_id in char_id_map:
                        target["character_id"] = str(char_id_map[client_char_id])

                db.add(
                    Annotation(
                        project_id=project_id,
                        annotation_id=ann.annotation_id,
                        severity=ann.severity.value,
                        category=ann.category.value,
                        title=ann.title,
                        description=ann.description,
                        source_quote=ann.source_quote,
                        target_reference=target,
                        alternatives=[
                            alt.model_dump(mode="json")
                            for alt in (ann.alternatives or [])
                        ],
                        confidence=ann.confidence,
                        auto_applied=ann.auto_applied,
                    )
                )

        await db.commit()
        await db.refresh(script_row)
        return script_row
