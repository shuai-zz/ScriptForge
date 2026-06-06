"""Script and Scene ORM models."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Script(Base):
    """A generated screenplay for a project."""

    __tablename__ = "scripts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        unique=True,
    )
    version: Mapped[str] = mapped_column(String(50), default="1.0")
    yaml_content: Mapped[str] = mapped_column(Text)
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
    yaml_snippet: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
