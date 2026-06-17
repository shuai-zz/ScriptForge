"""Pydantic model for script-v1.yaml."""

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.annotation import AnnotationV1


class RoleType(str, Enum):
    """Character role classification."""

    PROTAGONIST = "protagonist"
    ANTAGONIST = "antagonist"
    SUPPORTING = "supporting"
    MINOR = "minor"


class LocationType(str, Enum):
    """Scene location prefix."""

    INT = "INT."
    EXT = "EXT."
    INT_EXT = "INT./EXT."


class TimeOfDay(str, Enum):
    """Scene time-of-day suffix."""

    DAY = "DAY"
    NIGHT = "NIGHT"
    DAWN = "DAWN"
    DUSK = "DUSK"
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    EVENING = "EVENING"
    LATER = "LATER"
    CONTINUOUS = "CONTINUOUS"
    SAME_TIME = "SAME TIME"


class BlockType(str, Enum):
    """Script block type."""

    ACTION = "action"
    DIALOGUE = "dialogue"


class ScriptMetadata(BaseModel):
    """Top-level metadata for a screenplay."""

    model_config = ConfigDict(extra="allow")

    title: str
    subtitle: Optional[str] = None
    source_novel: Optional[str] = None
    source_author: Optional[str] = None
    schema_version: str = "1.0"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    total_scenes: int = Field(default=0, ge=0)
    estimated_runtime: int = Field(default=0, ge=0)


class ScriptCharacter(BaseModel):
    """Denormalized character snapshot in script context."""

    model_config = ConfigDict(extra="allow")

    character_id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    role_type: RoleType
    age: Optional[int] = None
    gender: Optional[str] = None
    archetype: Optional[str] = None
    traits: list[str] = Field(default_factory=list)
    arc_summary: Optional[str] = None


class Slug(BaseModel):
    """Scene slug line components."""

    model_config = ConfigDict(extra="allow")

    location_type: LocationType
    location_name: str
    time: TimeOfDay


class SourceRef(BaseModel):
    """Traceability: link back to original novel paragraph."""

    model_config = ConfigDict(extra="allow")

    chapter: int
    paragraph: int
    quote: str


class ScriptBlock(BaseModel):
    """Action or dialogue block within a scene."""

    model_config = ConfigDict(extra="allow")

    block_id: str
    order: int = Field(ge=0)
    type: BlockType
    # action fields
    text: Optional[str] = None
    # dialogue fields
    char_id: Optional[str] = None
    char_name: Optional[str] = None
    line: Optional[str] = None
    parenthetical: Optional[str] = None
    # common
    annotation_refs: list[str] = Field(default_factory=list)
    source_ref: Optional[SourceRef] = None


class SceneAnnotationRef(BaseModel):
    """Reference to an annotation attached to a scene."""

    model_config = ConfigDict(extra="allow")

    annotation_id: str


class Scene(BaseModel):
    """A single scene in the screenplay."""

    model_config = ConfigDict(extra="allow")

    scene_id: str
    scene_number: int = Field(ge=1)
    slug: Slug
    summary: Optional[str] = None
    characters_present: list[str] = Field(default_factory=list)
    props: list[str] = Field(default_factory=list)
    blocks: list[ScriptBlock]
    annotations: list[SceneAnnotationRef] = Field(default_factory=list)


class SceneIndexEntry(BaseModel):
    """Flat navigation entry for quick timeline rendering."""

    model_config = ConfigDict(extra="allow")

    scene_id: str
    scene_number: int
    slug_line: str
    summary: Optional[str] = None
    characters: list[str] = Field(default_factory=list)
    page_estimate: Optional[float] = None


class GlobalAnnotationRef(BaseModel):
    """Reference to a script-level global annotation."""

    model_config = ConfigDict(extra="allow")

    annotation_id: str


class ScriptV1(BaseModel):
    """Root model for script-v1.yaml."""

    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"] = "1.0"
    schema_name: Literal["scriptforge-script"] = "scriptforge-script"
    metadata: ScriptMetadata
    characters: list[ScriptCharacter] = Field(default_factory=list)
    scenes: list[Scene] = Field(default_factory=list)
    scene_index: list[SceneIndexEntry] = Field(default_factory=list)
    global_annotations: list[GlobalAnnotationRef] = Field(default_factory=list)
    annotations: list[AnnotationV1] = Field(default_factory=list)
