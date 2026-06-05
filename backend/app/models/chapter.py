"""Chapter ORM model."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ChapterStatus(str, Enum):
    """Chapter processing states."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class Chapter(Base):
    """A novel chapter uploaded for conversion."""

    __tablename__ = "chapters"
    __table_args__ = (UniqueConstraint("project_id", "number"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
    )
    number: Mapped[int]
    title: Mapped[str] = mapped_column(String(255))
    raw_text: Mapped[str] = mapped_column(Text)
    word_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[ChapterStatus] = mapped_column(default=ChapterStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
