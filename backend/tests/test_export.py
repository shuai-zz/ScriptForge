"""Tests for script export endpoints."""

import io
import uuid
import zipfile
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


@pytest.fixture
def mock_db():
    return MagicMock()


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
