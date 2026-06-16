"""Tests for script export endpoints using DB rows as source of truth."""

import io
import uuid
import zipfile

import pytest
import pytest_asyncio
import yaml
from httpx import ASGITransport, AsyncClient

from app.database import async_session_factory, get_db
from app.main import app
from app.models.project import Project
from app.schemas.script import ScriptV1
from app.services.script_persistence_service import ScriptPersistenceService

pytestmark = pytest.mark.asyncio(loop_scope="session")


DEMO_YAML = """schema_version: "1.0"
schema_name: "scriptforge-script"
metadata:
  title: "三体"
  subtitle: "第一部：地球往事"
  source_novel: "三体"
  source_author: "刘慈欣"
  total_scenes: 3
  estimated_runtime: 120
characters:
  - character_id: "c1"
    name: "汪淼"
    aliases: ["淼淼"]
    role_type: "protagonist"
    age: 40
    gender: "男"
    archetype: "科学家"
    traits: ["理性", "好奇", "坚韧"]
    arc_summary: "从怀疑到觉醒的科学家"
  - character_id: "c2"
    name: "丁仪"
    aliases: []
    role_type: "supporting"
    age: 35
    gender: "男"
    archetype: "物理学家"
    traits: ["玩世不恭", "天才", "悲观"]
    arc_summary: "揭示真相的物理学家"
scenes:
  - scene_id: "s1"
    scene_number: 1
    slug:
      location_type: "INT."
      location_name: "汪淼家 - 客厅"
      time: "NIGHT"
    summary: "汪淼发现照片上的倒计时"
    characters_present: ["c1"]
    props: ["相机", "照片"]
    blocks:
      - block_id: "b1"
        order: 0
        type: "action"
        text: "汪淼坐在沙发上，手里拿着一叠照片。台灯的光线下，他的脸色苍白。"
        annotation_refs: []
      - block_id: "b2"
        order: 1
        type: "dialogue"
        char_id: "c1"
        char_name: "汪淼"
        line: "这不可能...每一张照片上都有数字。"
        parenthetical: "颤抖着声音"
        annotation_refs: []
  - scene_id: "s2"
    scene_number: 2
    slug:
      location_type: "EXT."
      location_name: "台球厅"
      time: "DAY"
    summary: "丁仪用台球比喻解释物理定律的崩溃"
    characters_present: ["c1", "c2"]
    props: ["台球", "球杆"]
    blocks:
      - block_id: "b3"
        order: 0
        type: "action"
        text: "台球厅里烟雾缭绕。丁仪拿起一支球杆，对准白球。"
        annotation_refs: []
      - block_id: "b4"
        order: 1
        type: "dialogue"
        char_id: "c2"
        char_name: "丁仪"
        line: "想象一下，如果物理定律在不同的地方、不同的时间是不一样的，会怎样？"
        parenthetical: "吐出一口烟"
        annotation_refs: []
      - block_id: "b5"
        order: 2
        type: "dialogue"
        char_id: "c1"
        char_name: "汪淼"
        line: "那科学就不存在了。"
        annotation_refs: ["a1"]
scene_index:
  - scene_id: "s1"
    scene_number: 1
    slug_line: "INT. 汪淼家 - 客厅 - NIGHT"
    characters: ["c1"]
    page_estimate: 1.5
  - scene_id: "s2"
    scene_number: 2
    slug_line: "EXT. 台球厅 - DAY"
    characters: ["c1", "c2"]
    page_estimate: 2
global_annotations: []
"""


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def async_db():
    async with async_session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def async_project(async_db):
    p = Project(name=f"export-test-{uuid.uuid4().hex[:8]}")
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


@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def demo_project_with_script(async_project, async_db):
    script = ScriptV1.model_validate(yaml.safe_load(DEMO_YAML))
    await ScriptPersistenceService.persist_script(
        async_db, async_project.id, script
    )
    return async_project


class TestExportEndpoints:
    async def test_export_yaml(self, async_client, demo_project_with_script):
        resp = await async_client.get(
            f"/api/projects/{demo_project_with_script.id}/export/yaml"
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/x-yaml"
        assert "三体" in resp.text
        assert "schema_version" in resp.text

    async def test_export_fountain(self, async_client, demo_project_with_script):
        resp = await async_client.get(
            f"/api/projects/{demo_project_with_script.id}/export/fountain"
        )
        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]
        body = resp.text
        assert "Title: 三体" in body
        assert "INT. 汪淼家 - 客厅 - NIGHT" in body
        assert "汪淼" in body

    async def test_export_pdf(self, async_client, demo_project_with_script):
        resp = await async_client.get(
            f"/api/projects/{demo_project_with_script.id}/export/pdf"
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        # PDF starts with %PDF-
        assert resp.content[:5] == b"%PDF-"

    async def test_export_fdx(self, async_client, demo_project_with_script):
        resp = await async_client.get(
            f"/api/projects/{demo_project_with_script.id}/export/fdx"
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/xml"
        body = resp.text
        assert "FinalDraft" in body
        assert "汪淼" in body

    async def test_export_batch_zip(self, async_client, demo_project_with_script):
        resp = await async_client.post(
            f"/api/projects/{demo_project_with_script.id}/export/batch",
            json={"formats": ["yaml", "fountain", "pdf", "fdx"]},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/zip"

        buf = io.BytesIO(resp.content)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert any(n.endswith(".yaml") for n in names)
            assert any(n.endswith(".fountain") for n in names)
            assert any(n.endswith(".pdf") for n in names)
            assert any(n.endswith(".fdx") for n in names)

    async def test_export_batch_single_format(
        self, async_client, demo_project_with_script
    ):
        resp = await async_client.post(
            f"/api/projects/{demo_project_with_script.id}/export/batch",
            json={"formats": ["yaml"]},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/zip"

        buf = io.BytesIO(resp.content)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert len(names) == 1
            assert names[0].endswith(".yaml")


class TestExportNotFound:
    async def test_export_missing_project(self, async_client):
        resp = await async_client.get(
            f"/api/projects/{uuid.uuid4()}/export/yaml"
        )
        assert resp.status_code == 404
