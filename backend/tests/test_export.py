"""Tests for script export endpoints."""

import io
import uuid
import zipfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


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


def _make_mock_script():
    script = MagicMock()
    script.yaml_content = DEMO_YAML
    return script


@pytest.fixture
def mock_db():
    db = MagicMock()

    async def _execute(stmt):
        result = MagicMock()
        result.scalar_one_or_none = MagicMock(return_value=_make_mock_script())
        return result

    db.execute = _execute
    return db


@pytest.fixture
def client(mock_db):
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()


@pytest.fixture
def demo_project_id() -> str:
    return "123e4567-e89b-12d3-a456-426614174000"


class TestExportEndpoints:
    def test_export_yaml(self, client: TestClient, demo_project_id: str) -> None:
        resp = client.get(f"/api/projects/{demo_project_id}/export/yaml")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/x-yaml"
        assert "三体" in resp.text
        assert "schema_version" in resp.text

    def test_export_fountain(self, client: TestClient, demo_project_id: str) -> None:
        resp = client.get(f"/api/projects/{demo_project_id}/export/fountain")
        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]
        body = resp.text
        assert "Title: 三体" in body
        assert "INT. 汪淼家 - 客厅 - NIGHT" in body
        assert "汪淼" in body

    def test_export_pdf(self, client: TestClient, demo_project_id: str) -> None:
        resp = client.get(f"/api/projects/{demo_project_id}/export/pdf")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        # PDF starts with %PDF-
        assert resp.content[:5] == b"%PDF-"

    def test_export_fdx(self, client: TestClient, demo_project_id: str) -> None:
        resp = client.get(f"/api/projects/{demo_project_id}/export/fdx")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/xml"
        body = resp.text
        assert "FinalDraft" in body
        assert "汪淼" in body

    def test_export_batch_zip(self, client: TestClient, demo_project_id: str) -> None:
        resp = client.post(
            f"/api/projects/{demo_project_id}/export/batch",
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

    def test_export_batch_single_format(self, client: TestClient, demo_project_id: str) -> None:
        resp = client.post(
            f"/api/projects/{demo_project_id}/export/batch",
            json={"formats": ["yaml"]},
        )
        assert resp.status_code == 200
        buf = io.BytesIO(resp.content)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert len(names) == 1
            assert names[0].endswith(".yaml")


class TestExportNotFound:
    """When project has no script."""

    @pytest.fixture
    def empty_db(self):
        db = MagicMock()

        async def _execute(stmt):
            result = MagicMock()
            result.scalar_one_or_none = MagicMock(return_value=None)
            return result

        db.execute = _execute
        return db

    @pytest.fixture
    def empty_client(self, empty_db):
        async def override_get_db():
            yield empty_db

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as tc:
            yield tc
        app.dependency_overrides.clear()

    def test_export_yaml_not_found(self, empty_client: TestClient, demo_project_id: str) -> None:
        resp = empty_client.get(f"/api/projects/{demo_project_id}/export/yaml")
        assert resp.status_code == 404
