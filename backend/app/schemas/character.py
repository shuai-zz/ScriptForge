"""Pydantic model for character-v1.yaml."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RoleType(str, Enum):
    """Character role classification."""

    PROTAGONIST = "protagonist"
    ANTAGONIST = "antagonist"
    SUPPORTING = "supporting"
    MINOR = "minor"


class RelationshipType(str, Enum):
    """Character relationship taxonomy."""

    LOVER = "lover"
    FAMILY = "family"
    FRIEND = "friend"
    RIVAL = "rival"
    MENTOR = "mentor"
    ENEMY = "enemy"
    COLLEAGUE = "colleague"
    OTHER = "other"


class VocabularyLevel(str, Enum):
    """Character speech vocabulary register."""

    SIMPLE = "simple"
    CASUAL = "casual"
    FORMAL = "formal"
    ELEVATED = "elevated"
    TECHNICAL = "technical"


class BasicInfo(BaseModel):
    """Demographic and physical description."""

    model_config = ConfigDict(extra="allow")

    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    appearance: Optional[str] = None


class StoryRole(BaseModel):
    """Narrative function of the character."""

    model_config = ConfigDict(extra="allow")

    type: RoleType
    archetype: Optional[str] = None
    motivation: Optional[str] = None
    goals: list[str] = Field(default_factory=list)
    flaw: Optional[str] = None


class CharacterArc(BaseModel):
    """Three-act character transformation."""

    model_config = ConfigDict(extra="allow")

    starting_state: Optional[str] = None
    midpoint_shift: Optional[str] = None
    ending_state: Optional[str] = None


class Voice(BaseModel):
    """Distinctive speech characteristics for AI dialogue generation."""

    model_config = ConfigDict(extra="allow")

    speech_patterns: Optional[str] = None
    catchphrases: list[str] = Field(default_factory=list)
    vocabulary_level: Optional[VocabularyLevel] = None


class Relationship(BaseModel):
    """Directed relationship to another character."""

    model_config = ConfigDict(extra="allow")

    target_char_id: str
    type: RelationshipType
    intensity: int = Field(ge=1, le=5)
    history: Optional[str] = None
    current_status: Optional[str] = None
    predicted_evolution: Optional[str] = None


class SourceEvidence(BaseModel):
    """Novel text evidence supporting this profile."""

    model_config = ConfigDict(extra="allow")

    chapter: int
    paragraph: int
    quote: str
    context: Optional[str] = None


class AppearanceStats(BaseModel):
    """Computed screen-time statistics."""

    model_config = ConfigDict(extra="allow")

    scene_count: int = Field(default=0, ge=0)
    dialogue_count: int = Field(default=0, ge=0)
    first_scene: Optional[int] = None
    last_scene: Optional[int] = None


class CharacterV1(BaseModel):
    """Root model for character-v1.yaml."""

    model_config = ConfigDict(extra="allow")

    schema_version: str = "1.0"
    schema_name: str = "scriptforge-character"
    character_id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    basic_info: BasicInfo = Field(default_factory=BasicInfo)
    story_role: StoryRole
    arc: CharacterArc = Field(default_factory=CharacterArc)
    voice: Voice = Field(default_factory=Voice)
    relationships: list[Relationship] = Field(default_factory=list)
    source_evidence: list[SourceEvidence] = Field(default_factory=list)
    appearance_stats: AppearanceStats = Field(default_factory=AppearanceStats)
