"""Annotation ORM model."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AnnotationStatus(str, Enum):
    """Review status of an annotation."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    IGNORED = "ignored"
    MODIFIED = "modified"


class Annotation(Base):
    """An AI adaptation annotation."""

    __tablename__ = "annotations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
    )
    annotation_id: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(20))
    category: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    source_quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_reference: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    alternatives: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    confidence: Mapped[float]
    auto_applied: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(20), default=AnnotationStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
