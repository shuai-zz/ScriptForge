"""Tests for the script retrieval endpoint and the conversion script-persistence helper."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
import yaml
from httpx import ASGITransport, AsyncClient

from app.database import async_session_factory, get_db
from app.main import app
from app.models.project import Project
from app.models.script import Script
from app.routers.conversion import _persist_script
from app.schemas.script import (
    BlockType,
    LocationType,
    RoleType,
    ScriptBlock,
    ScriptCharacter,
    ScriptMetadata,
    ScriptV1,
    Slug,
    TimeOfDay,
)
from app.schemas.script import (
    Scene as SceneSchema,
)
from app.services.script_persistence_service import ScriptPersistenceService

pytestmark = pytest.mark.asyncio(loop_scope="session")


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


def _script_with_content() -> ScriptV1:
    """ScriptV1 with characters, scenes and blocks for DB-row read tests."""
    return ScriptV1(
        schema_version="1.0",
        schema_name="scriptforge-script",
        metadata=ScriptMetadata(
            title="DB Row Script",
            source_novel="Test Novel",
            total_scenes=1,
            estimated_runtime=5,
        ),
        characters=[
            ScriptCharacter(
                character_id="char_001",
                name="Alice",
                role_type=RoleType.PROTAGONIST,
                aliases=["A"],
                traits=["brave"],
            ),
        ],
        scenes=[
            SceneSchema(
                scene_id="scene_1",
                scene_number=1,
                slug=Slug(
                    location_type=LocationType.INT,
                    location_name="Room",
                    time=TimeOfDay.DAY,
                ),
                summary="Alice enters the room.",
                characters_present=["char_001"],
                props=["cup"],
                blocks=[
                    ScriptBlock(
                        block_id="b1",
                        order=0,
                        type=BlockType.ACTION,
                        text="Alice enters.",
                    ),
                    ScriptBlock(
                        block_id="b2",
                        order=1,
                        type=BlockType.DIALOGUE,
                        char_id="char_001",
                        char_name="Alice",
                        line="Hi.",
                    ),
                ],
            )
        ],
        scene_index=[],
        global_annotations=[],
    )


# ── GET /api/projects/{id}/script ──


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def async_db():
    async with async_session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def async_project(async_db):
    p = Project(name=f"script-read-test-{uuid.uuid4().hex[:8]}")
    async_db.add(p)
    await async_db.commit()
    await async_db.refresh(p)
    yield p
    refreshed = await async_db.get(Project, p.id)
    if refreshed:
        await async_db.delete(refreshed)
        await async_db.commit()


@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def async_client():
    async def override_get_db():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


async def test_get_script_from_db_rows(async_client, async_project, async_db):
    script = _script_with_content()
    await ScriptPersistenceService.persist_script(async_db, async_project.id, script)

    r = await async_client.get(f"/api/projects/{async_project.id}/script")
    assert r.status_code == 200
    data = r.json()
    assert data["metadata"]["title"] == "DB Row Script"
    assert len(data["scenes"]) == 1
    assert data["scenes"][0]["slug"]["location_name"] == "Room"
    assert len(data["scenes"][0]["blocks"]) == 2
    assert data["scenes"][0]["blocks"][0]["text"] == "Alice enters."
    assert data["scenes"][0]["blocks"][1]["line"] == "Hi."
    assert len(data["characters"]) == 1
    assert data["characters"][0]["name"] == "Alice"


async def test_get_script_fallback_to_yaml(async_client, async_project, async_db):
    payload = _valid_script().model_dump(mode="json")
    payload["metadata"]["title"] = "YAML Fallback"
    script_row = Script(
        project_id=async_project.id,
        version="1.0",
        script_metadata={"title": "YAML Fallback"},
        yaml_content=yaml.safe_dump(payload, allow_unicode=True),
    )
    async_db.add(script_row)
    await async_db.commit()

    r = await async_client.get(f"/api/projects/{async_project.id}/script")
    assert r.status_code == 200
    data = r.json()
    assert data["metadata"]["title"] == "YAML Fallback"


async def test_get_script_not_found(async_client, async_project):
    r = await async_client.get(f"/api/projects/{async_project.id}/script")
    assert r.status_code == 404


# ── _persist_script helper ──


def _exec_result(scalar_one=None) -> MagicMock:
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar_one
    return result


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
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock(return_value=_exec_result(scalar_one=None))

    with patch(
        "app.routers.conversion.async_session_factory",
        return_value=_FakeSessionCtx(db),
    ):
        await _persist_script(project_id, graph, MagicMock())

    # The first add is the script metadata row.
    assert db.add.call_count >= 1
    added = db.add.call_args_list[0].args[0]
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
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
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
