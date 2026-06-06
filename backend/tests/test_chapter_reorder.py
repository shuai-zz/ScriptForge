"""Unit tests for ChapterService.reorder two-phase renumbering.

The reorder must not transiently reuse a live ``number`` value, otherwise the
``(project_id, number)`` unique constraint is violated mid-operation. These
tests pin the two-phase behaviour (negative parking + flush, then final 1..N)
that prevents that collision.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.chapter_service import ChapterService


def _make_chapter(project_id: uuid.UUID, number: int) -> MagicMock:
    ch = MagicMock()
    ch.id = uuid.uuid4()
    ch.project_id = project_id
    ch.number = number
    return ch


def _mock_db() -> MagicMock:
    db = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    return db


async def test_reorder_assigns_final_positions():
    project_id = uuid.uuid4()
    chapters = [_make_chapter(project_id, n) for n in (1, 2, 3)]
    by_id = {c.id: c for c in chapters}
    db = _mock_db()

    async def fake_get(_db, cid):
        return by_id.get(cid)

    # Reverse the order: [c3, c2, c1] -> numbers 1, 2, 3
    new_order = [chapters[2].id, chapters[1].id, chapters[0].id]
    with patch.object(ChapterService, "get", new=AsyncMock(side_effect=fake_get)):
        await ChapterService.reorder(db, project_id, new_order)

    assert chapters[2].number == 1
    assert chapters[1].number == 2
    assert chapters[0].number == 3
    db.commit.assert_awaited_once()


async def test_reorder_parks_at_unique_temp_numbers_before_final():
    """A swap must flush collision-free temporary numbers before the final pass."""
    project_id = uuid.uuid4()
    chapters = [_make_chapter(project_id, n) for n in (1, 2)]
    by_id = {c.id: c for c in chapters}
    db = _mock_db()

    seen_at_flush: dict[str, list[int]] = {}

    async def record_flush():
        seen_at_flush["numbers"] = [c.number for c in chapters]

    db.flush = AsyncMock(side_effect=record_flush)

    async def fake_get(_db, cid):
        return by_id.get(cid)

    # Swap the two chapters.
    new_order = [chapters[1].id, chapters[0].id]
    with patch.object(ChapterService, "get", new=AsyncMock(side_effect=fake_get)):
        await ChapterService.reorder(db, project_id, new_order)

    # Two-phase boundary exists (the buggy single-pass never flushes).
    db.flush.assert_awaited()
    # At flush time the parked numbers were unique and not live positives,
    # so no (project_id, number) collision is possible.
    assert "numbers" in seen_at_flush
    parked = seen_at_flush["numbers"]
    assert len(set(parked)) == len(parked)
    assert all(n <= 0 for n in parked)
    # Final result reflects the requested swap.
    assert chapters[1].number == 1
    assert chapters[0].number == 2


async def test_reorder_empty_list_is_noop():
    project_id = uuid.uuid4()
    db = _mock_db()
    with patch.object(ChapterService, "get", new=AsyncMock(return_value=None)):
        await ChapterService.reorder(db, project_id, [])
    db.flush.assert_not_awaited()
    db.commit.assert_not_awaited()
