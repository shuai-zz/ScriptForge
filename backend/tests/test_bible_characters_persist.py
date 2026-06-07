"""Tests for persisting the Story Bible + characters/relationships after a run."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.routers.conversion import _persist_bible_and_characters


class _FakeSessionCtx:
    def __init__(self, db):
        self._db = db

    async def __aenter__(self):
        return self._db

    async def __aexit__(self, *args):
        return False


def _graph_with_bible(bible):
    snapshot = MagicMock()
    snapshot.values = {"story_bible": bible}
    graph = MagicMock()
    graph.aget_state = AsyncMock(return_value=snapshot)
    return graph


async def test_persist_bible_and_characters_creates_rows():
    bible = {
        "overall_synopsis": "概要",
        "character_network": {
            "nodes": [
                {"character_id": "c1", "name": "汪淼", "role_type": "protagonist"},
                {"character_id": "c2", "name": "史强", "role_type": "supporting"},
            ],
            "edges": [
                {"source": "c1", "target": "c2", "type": "friend", "intensity": 4}
            ],
        },
    }
    graph = _graph_with_bible(bible)

    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    no_bible = MagicMock()
    no_bible.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=no_bible)

    created = {}

    async def fake_create(_db, *, project_id, name, role_type, aliases, traits):
        char = MagicMock()
        char.id = uuid.uuid4()
        char.name = name
        created[name] = char
        return char

    with (
        patch(
            "app.routers.conversion.async_session_factory",
            return_value=_FakeSessionCtx(db),
        ),
        patch(
            "app.routers.conversion.CharacterService.list_by_project",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.routers.conversion.CharacterService.create",
            new=AsyncMock(side_effect=fake_create),
        ),
        patch(
            "app.routers.conversion.CharacterRelationshipService.list_by_project",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.routers.conversion.CharacterRelationshipService.create",
            new=AsyncMock(),
        ) as rel_create,
    ):
        await _persist_bible_and_characters(uuid.uuid4(), graph, MagicMock())

    # Story Bible upserted (db.add called with a StoryBible row)
    assert db.add.called
    # one character per node
    assert set(created) == {"汪淼", "史强"}
    # one relationship per edge
    rel_create.assert_awaited_once()


async def test_persist_skips_when_no_bible():
    graph = _graph_with_bible(None)
    with patch("app.routers.conversion.async_session_factory") as factory:
        await _persist_bible_and_characters(uuid.uuid4(), graph, MagicMock())
        factory.assert_not_called()
