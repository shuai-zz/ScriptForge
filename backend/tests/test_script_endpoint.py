"""Tests for the script retrieval endpoint and the conversion script-persistence helper."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.routers.conversion import _persist_script
from app.schemas.script import ScriptMetadata, ScriptV1


def _valid_script() -> ScriptV1:
    """Minimal valid ScriptV1 (mirrors the validators test helper)."""
    return ScriptV1(
        schema_version="1.0",
        schema_name="scriptforge-script",
        metadata=ScriptMetadata(title="测试剧本", total_scenes=0, estimated_runtime=0),
        characters=[],
        scenes=[],
        scene_index=[],
        global_annotations=[],
    )


# ── GET /api/projects/{id}/script ──


def _exec_result(scalar_one=None) -> MagicMock:
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar_one
    return result


def _mock_db() -> MagicMock:
    db = MagicMock()
    db.execute = AsyncMock(return_value=_exec_result())
    return db


def _client(mock_db):
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


class TestGetScript:
    def test_success(self):
        mock_db = _mock_db()
        script = MagicMock()
        script.yaml_content = (
            "schema_version: '1.0'\n"
            "metadata:\n  title: 测试剧本\n"
            "scenes:\n  - scene_id: s1\n    scene_number: 1\n"
        )
        mock_db.execute = AsyncMock(return_value=_exec_result(scalar_one=script))
        with _client(mock_db) as client:
            r = client.get(f"/api/projects/{uuid.uuid4()}/script")
        app.dependency_overrides.clear()
        assert r.status_code == 200
        data = r.json()
        assert data["metadata"]["title"] == "测试剧本"
        assert len(data["scenes"]) == 1

    def test_not_found(self):
        mock_db = _mock_db()
        mock_db.execute = AsyncMock(return_value=_exec_result(scalar_one=None))
        with _client(mock_db) as client:
            r = client.get(f"/api/projects/{uuid.uuid4()}/script")
        app.dependency_overrides.clear()
        assert r.status_code == 404


# ── _persist_script helper ──


class _FakeSessionCtx:
    def __init__(self, db):
        self._db = db

    async def __aenter__(self):
        return self._db

    async def __aexit__(self, *args):
        return False


def _graph_with_script(script_dict):
    snapshot = MagicMock()
    snapshot.values = {"assembled_script": script_dict}
    graph = MagicMock()
    graph.aget_state = AsyncMock(return_value=snapshot)
    return graph


async def test_persist_creates_new_row():
    project_id = uuid.uuid4()
    graph = _graph_with_script(_valid_script().model_dump())
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.execute = AsyncMock(return_value=_exec_result(scalar_one=None))

    with patch(
        "app.routers.conversion.async_session_factory",
        return_value=_FakeSessionCtx(db),
    ):
        await _persist_script(project_id, graph, MagicMock())

    db.add.assert_called_once()
    added = db.add.call_args.args[0]
    assert added.project_id == project_id
    assert "测试剧本" in added.yaml_content
    db.commit.assert_awaited_once()


async def test_persist_updates_existing_row():
    project_id = uuid.uuid4()
    graph = _graph_with_script(_valid_script().model_dump())
    existing = MagicMock()
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.execute = AsyncMock(return_value=_exec_result(scalar_one=existing))

    with patch(
        "app.routers.conversion.async_session_factory",
        return_value=_FakeSessionCtx(db),
    ):
        await _persist_script(project_id, graph, MagicMock())

    db.add.assert_not_called()
    assert "测试剧本" in existing.yaml_content
    db.commit.assert_awaited_once()


async def test_persist_noop_when_no_assembled_script():
    graph = _graph_with_script(None)  # snapshot.values has assembled_script=None
    with patch("app.routers.conversion.async_session_factory") as factory:
        await _persist_script(uuid.uuid4(), graph, MagicMock())
        factory.assert_not_called()
