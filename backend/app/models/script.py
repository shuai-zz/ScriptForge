"""Script and Scene ORM models."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Script(Base):
    """A generated screenplay for a project (normalized into scenes/blocks)."""

    __tablename__ = "scripts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        unique=True,
    )
    version: Mapped[str] = mapped_column(String(50), default="1.0")
    script_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )


class Scene(Base):
    """A single scene within a script."""

    __tablename__ = "scenes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    script_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scripts.id", ondelete="CASCADE"),
    )
    scene_number: Mapped[int]
    location_type: Mapped[str] = mapped_column(String(10))
    location_name: Mapped[str] = mapped_column(String(255))
    time: Mapped[str] = mapped_column(String(20))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    characters_present: Mapped[list[str]] = mapped_column(JSONB, default=list)
    props: Mapped[list[str]] = mapped_column(JSONB, default=list)
    order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )


class Block(Base):
    """A single action or dialogue block within a scene."""

    __tablename__ = "blocks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    scene_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scenes.id", ondelete="CASCADE"),
    )
    order: Mapped[int]
    type: Mapped[str] = mapped_column(String(20))
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    char_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("characters.id", ondelete="SET NULL"),
        nullable=True,
    )
    char_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parenthetical: Mapped[str | None] = mapped_column(Text, nullable=True)
    line: Mapped[str | None] = mapped_column(Text, nullable=True)
    annotation_refs: Mapped[list[str]] = mapped_column(JSONB, default=list)
    source_ref: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
