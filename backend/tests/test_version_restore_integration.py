"""Integration test: version restore must sync DB rows as well as YAML."""

import tempfile
import uuid

import pytest
import pytest_asyncio
import yaml
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.database import async_session_factory, get_db
from app.main import app
from app.models.project import Project
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
from app.services.version_service import VersionService

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture
def temp_storage():
    with tempfile.TemporaryDirectory() as tmpdir:
        original = settings.PROJECTS_STORAGE_PATH
        settings.PROJECTS_STORAGE_PATH = tmpdir
        yield tmpdir
        settings.PROJECTS_STORAGE_PATH = original


def _make_script(title: str) -> ScriptV1:
    return ScriptV1(
        schema_version="1.0",
        schema_name="scriptforge-script",
        metadata=ScriptMetadata(
            title=title,
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
                summary=f"{title} scene.",
                characters_present=["char_001"],
                props=["cup"],
                blocks=[
                    ScriptBlock(
                        block_id="b1",
                        order=0,
                        type=BlockType.ACTION,
                        text=f"Action for {title}.",
                    ),
                ],
            )
        ],
        scene_index=[],
        global_annotations=[],
    )


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def async_db():
    async with async_session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def async_project(async_db):
    p = Project(name=f"version-test-{uuid.uuid4().hex[:8]}")
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


async def test_restore_syncs_scenes_blocks_and_yaml(
    async_client, async_project, async_db, temp_storage
):
    script_v1 = _make_script("Version One")
    script_v2 = _make_script("Version Two")

    await VersionService.init_repo(async_project.id)

    yaml_v1 = yaml.safe_dump(script_v1.model_dump(mode="json"), allow_unicode=True)
    v1 = await VersionService.checkpoint(async_project.id, yaml_v1, "v1")

    yaml_v2 = yaml.safe_dump(script_v2.model_dump(mode="json"), allow_unicode=True)
    await VersionService.checkpoint(async_project.id, yaml_v2, "v2")

    # Simulate current DB state being at v2.
    await ScriptPersistenceService.persist_script(
        async_db, async_project.id, script_v2
    )

    r = await async_client.post(
        f"/api/projects/{async_project.id}/versions/restore",
        json={"version_id": v1["version_id"]},
    )
    assert r.status_code == 200

    r_get = await async_client.get(f"/api/projects/{async_project.id}/script")
    assert r_get.status_code == 200
    data = r_get.json()
    assert data["metadata"]["title"] == "Version One"
    assert data["scenes"][0]["summary"] == "Version One scene."
    assert data["scenes"][0]["blocks"][0]["text"] == "Action for Version One."
