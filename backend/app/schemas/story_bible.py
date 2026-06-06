"""Pydantic model for story-bible-v1.yaml."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.character import RelationshipType, RoleType


class EventSignificance(str, Enum):
    """Chapter event significance classification."""

    MAJOR = "major"
    MINOR = "minor"
    SETUP = "setup"
    PAYOFF = "payoff"


class TimeLabel(str, Enum):
    """Temporal positioning of an event."""

    NOW = "now"
    FLASHBACK = "flashback"
    FLASHFORWARD = "flashforward"


class TimeOfDay(str, Enum):
    """Time of day for timeline events."""

    DAWN = "dawn"
    MORNING = "morning"
    AFTERNOON = "afternoon"
    DUSK = "dusk"
    EVENING = "evening"
    NIGHT = "night"
    MIDNIGHT = "midnight"


class ForeshadowingStatus(str, Enum):
    """Tracking state for a foreshadowing item."""

    UNRESOLVED = "unresolved"
    RESOLVED = "resolved"


class KeyEvent(BaseModel):
    """A significant event within a chapter synopsis."""

    model_config = ConfigDict(extra="allow")

    description: str
    significance: EventSignificance


class ChapterSynopsis(BaseModel):
    """Per-chapter breakdown for the story bible."""

    model_config = ConfigDict(extra="allow")

    chapter_number: int = Field(ge=1)
    summary: str
    key_events: list[KeyEvent] = Field(default_factory=list)
    new_characters: list[str] = Field(default_factory=list)
    new_locations: list[str] = Field(default_factory=list)
    foreshadowing_setups: list[str] = Field(default_factory=list)
    foreshadowing_payoffs: list[str] = Field(default_factory=list)


class CharacterNetworkNode(BaseModel):
    """Node in the character relationship graph."""

    model_config = ConfigDict(extra="allow")

    character_id: str
    name: str
    role_type: RoleType


class CharacterNetworkEdge(BaseModel):
    """Directed/undirected relationship edge."""

    model_config = ConfigDict(extra="allow")

    source: str
    target: str
    type: RelationshipType
    intensity: int = Field(ge=1, le=5)
    key_moments: list[str] = Field(default_factory=list)


class CharacterNetwork(BaseModel):
    """Graph representation of character relationships."""

    model_config = ConfigDict(extra="allow")

    nodes: list[CharacterNetworkNode] = Field(default_factory=list)
    edges: list[CharacterNetworkEdge] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    """Chronological event with flashback support."""

    model_config = ConfigDict(extra="allow")

    event_id: str
    time_label: TimeLabel
    description: str
    duration: Optional[str] = None
    time_of_day: TimeOfDay
    trigger_events: list[str] = Field(default_factory=list)
    chapter: int = Field(ge=1)


class Theme(BaseModel):
    """Core theme with textual and visual evidence."""

    model_config = ConfigDict(extra="allow")

    theme_id: str
    name: str
    description: str
    textual_instances: list[str] = Field(default_factory=list)
    visual_motifs: list[str] = Field(default_factory=list)


class ForeshadowingItem(BaseModel):
    """Tracked setup/payoff pair."""

    model_config = ConfigDict(extra="allow")

    item_id: str
    setup_chapter: int = Field(ge=1)
    description: str
    status: ForeshadowingStatus
    payoff_chapter: Optional[int] = None


class LocationIndexEntry(BaseModel):
    """Location catalog with prop inventory and scene references."""

    model_config = ConfigDict(extra="allow")

    location_id: str
    name: str
    description: str
    key_props: list[str] = Field(default_factory=list)
    first_chapter: int = Field(ge=1)
    scenes: list[str] = Field(default_factory=list)


class StoryBibleV1(BaseModel):
    """Root model for story-bible-v1.yaml."""

    model_config = ConfigDict(extra="allow")

    schema_version: str = "1.0"
    schema_name: str = "scriptforge-story-bible"
    overall_synopsis: str
    chapter_synopses: list[ChapterSynopsis] = Field(default_factory=list)
    character_network: CharacterNetwork = Field(default_factory=CharacterNetwork)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    themes: list[Theme] = Field(default_factory=list)
    foreshadowing_tracking: list[ForeshadowingItem] = Field(default_factory=list)
    location_index: list[LocationIndexEntry] = Field(default_factory=list)
