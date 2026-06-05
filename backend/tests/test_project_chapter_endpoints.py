"""Unit tests for Project and Chapter CRUD endpoints (Task 6.7)."""

import uuid
from datetime import datetime
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models.chapter import ChapterStatus
from app.models.project import ProjectStatus


# ── Helpers ──


def _make_project(**kwargs):
    """Build a mock Project ORM object."""
    project = MagicMock()
    project.id = kwargs.get("id", uuid.uuid4())
    project.name = kwargs.get("name", "Test Project")
    project.description = kwargs.get("description", None)
    project.status = kwargs.get("status", ProjectStatus.DRAFT)
    project.config = kwargs.get("config", None)
    project.created_at = kwargs.get("created_at", datetime.now())
    project.updated_at = kwargs.get("updated_at", datetime.now())
    return project


def _make_chapter(**kwargs):
    """Build a mock Chapter ORM object."""
    chapter = MagicMock()
    chapter.id = kwargs.get("id", uuid.uuid4())
    chapter.project_id = kwargs.get("project_id", uuid.uuid4())
    chapter.number = kwargs.get("number", 1)
    chapter.title = kwargs.get("title", "Test Chapter")
    chapter.raw_text = kwargs.get("raw_text", "This is test content.")
    chapter.word_count = kwargs.get("word_count", len(chapter.raw_text))
    chapter.status = kwargs.get("status", ChapterStatus.PENDING)
    chapter.created_at = kwargs.get("created_at", datetime.now())
    chapter.updated_at = kwargs.get("updated_at", datetime.now())
    return chapter


# ── Fixtures ──


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(mock_db):
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    # Bypass _enrich_with_stats so it never hits the mock db
    with patch(
        "app.routers.projects._enrich_with_stats",
        side_effect=lambda _db, _pid, resp: resp,
    ):
        with TestClient(app) as tc:
            yield tc

    app.dependency_overrides.clear()


# ═══════════════════════════════════════════════════════════════
# Project endpoints
# ═══════════════════════════════════════════════════════════════


class TestCreateProject:
    """POST /api/projects"""

    @patch("app.routers.projects.ProjectService.create")
    def test_success(self, mock_create, client, mock_db):
        project = _make_project(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            name="New Project",
            description="A test project",
        )
        mock_create.return_value = project

        response = client.post(
            "/api/projects",
            json={
                "name": "New Project",
                "description": "A test project",
                "target_format": "movie",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Project"
        assert data["description"] == "A test project"
        assert data["status"] == "draft"
        assert data["chapter_count"] == 0
        mock_create.assert_called_once()

    def test_missing_name(self, client, mock_db):
        response = client.post("/api/projects", json={"target_format": "movie"})
        assert response.status_code == 422

    def test_invalid_target_format(self, client, mock_db):
        response = client.post(
            "/api/projects",
            json={"name": "X", "target_format": "invalid"},
        )
        assert response.status_code == 422


class TestListProjects:
    """GET /api/projects"""

    @patch("app.routers.projects.ProjectService.list_all")
    def test_empty(self, mock_list, client, mock_db):
        mock_list.return_value = []
        response = client.get("/api/projects")
        assert response.status_code == 200
        assert response.json() == []

    @patch("app.routers.projects.ProjectService.list_all")
    def test_with_projects(self, mock_list, client, mock_db):
        p1 = _make_project(id=uuid.uuid4(), name="Alpha")
        p2 = _make_project(id=uuid.uuid4(), name="Beta")
        mock_list.return_value = [p1, p2]

        response = client.get("/api/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Alpha"
        assert data[1]["name"] == "Beta"


class TestGetProject:
    """GET /api/projects/{id}"""

    @patch("app.routers.projects.ProjectService.get")
    def test_success(self, mock_get, client, mock_db):
        pid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_get.return_value = _make_project(id=pid, name="Found")

        response = client.get(f"/api/projects/{pid}")
        assert response.status_code == 200
        assert response.json()["name"] == "Found"

    @patch("app.routers.projects.ProjectService.get")
    def test_not_found(self, mock_get, client, mock_db):
        mock_get.return_value = None
        response = client.get(f"/api/projects/{uuid.uuid4()}")
        assert response.status_code == 404


class TestUpdateProject:
    """PUT /api/projects/{id}"""

    @patch("app.routers.projects.ProjectService.get")
    @patch("app.routers.projects.ProjectService.update")
    def test_success(self, mock_update, mock_get, client, mock_db):
        pid = uuid.uuid4()
        mock_get.return_value = _make_project(id=pid, name="Old")
        mock_update.return_value = _make_project(id=pid, name="New", description="Updated")

        response = client.put(
            f"/api/projects/{pid}",
            json={"name": "New", "description": "Updated"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New"
        assert data["description"] == "Updated"

    @patch("app.routers.projects.ProjectService.get")
    def test_not_found(self, mock_get, client, mock_db):
        mock_get.return_value = None
        response = client.put(
            f"/api/projects/{uuid.uuid4()}",
            json={"name": "New"},
        )
        assert response.status_code == 404


class TestDeleteProject:
    """DELETE /api/projects/{id}"""

    @patch("app.routers.projects.ProjectService.delete")
    def test_success(self, mock_delete, client, mock_db):
        mock_delete.return_value = True
        response = client.delete(f"/api/projects/{uuid.uuid4()}")
        assert response.status_code == 204

    @patch("app.routers.projects.ProjectService.delete")
    def test_not_found(self, mock_delete, client, mock_db):
        mock_delete.return_value = False
        response = client.delete(f"/api/projects/{uuid.uuid4()}")
        assert response.status_code == 404


class TestGetProjectConfig:
    """GET /api/projects/{id}/config"""

    @patch("app.routers.projects.ProjectService.get")
    def test_with_stored_config(self, mock_get, client, mock_db):
        pid = uuid.uuid4()
        mock_get.return_value = _make_project(id=pid, config={"target_format": "tv_series"})

        response = client.get(f"/api/projects/{pid}/config")
        assert response.status_code == 200
        data = response.json()
        assert data["target_format"] == "tv_series"

    @patch("app.routers.projects.ProjectService.get")
    def test_defaults_when_no_config(self, mock_get, client, mock_db):
        mock_get.return_value = _make_project(config=None)
        response = client.get(f"/api/projects/{uuid.uuid4()}/config")
        assert response.status_code == 200
        data = response.json()
        assert "conversion_params" in data
        assert data["conversion_params"]["target_format"] == "movie"

    @patch("app.routers.projects.ProjectService.get")
    def test_not_found(self, mock_get, client, mock_db):
        mock_get.return_value = None
        response = client.get(f"/api/projects/{uuid.uuid4()}/config")
        assert response.status_code == 404


class TestUpdateProjectConfig:
    """PUT /api/projects/{id}/config"""

    @patch("app.routers.projects.ProjectService.get")
    @patch("app.routers.projects.ProjectService.update")
    def test_success(self, mock_update, mock_get, client, mock_db):
        pid = uuid.uuid4()
        mock_get.return_value = _make_project(id=pid)
        mock_update.return_value = _make_project(id=pid)

        response = client.put(
            f"/api/projects/{pid}/config",
            json={"target_format": "movie"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["target_format"] == "movie"

    @patch("app.routers.projects.ProjectService.get")
    @patch("app.routers.projects.ProjectService.update")
    def test_invalid_config(self, mock_update, mock_get, client, mock_db):
        mock_get.return_value = _make_project()
        response = client.put(
            f"/api/projects/{uuid.uuid4()}/config",
            json={"conversion_params": {"target_format": "invalid_format"}},
        )
        assert response.status_code == 422

    @patch("app.routers.projects.ProjectService.get")
    def test_not_found(self, mock_get, client, mock_db):
        mock_get.return_value = None
        response = client.put(
            f"/api/projects/{uuid.uuid4()}/config",
            json={"target_format": "movie"},
        )
        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════
# Chapter endpoints
# ═══════════════════════════════════════════════════════════════


class TestCreateChapter:
    """POST /api/projects/{id}/chapters"""

    @patch("app.routers.chapters.ChapterService.create")
    def test_success(self, mock_create, client, mock_db):
        pid = uuid.uuid4()
        cid = uuid.uuid4()
        mock_create.return_value = _make_chapter(
            id=cid,
            project_id=pid,
            number=3,
            title="Chapter Three",
            raw_text="Content here.",
        )

        response = client.post(
            f"/api/projects/{pid}/chapters",
            json={"title": "Chapter Three", "raw_text": "Content here."},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Chapter Three"
        assert data["number"] == 3
        assert data["raw_text"] == "Content here."

    def test_missing_title(self, client, mock_db):
        response = client.post(
            f"/api/projects/{uuid.uuid4()}/chapters",
            json={"raw_text": "Content"},
        )
        assert response.status_code == 422


class TestUploadChapter:
    """POST /api/projects/{id}/chapters/upload"""

    @patch("app.routers.chapters.ChapterService.create")
    def test_txt_file(self, mock_create, client, mock_db):
        pid = uuid.uuid4()
        cid = uuid.uuid4()
        mock_create.return_value = _make_chapter(
            id=cid, project_id=pid, title="my_chapter", raw_text="File content"
        )

        response = client.post(
            f"/api/projects/{pid}/chapters/upload",
            files={"file": ("my_chapter.txt", BytesIO(b"File content"), "text/plain")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "my_chapter"

    @patch("app.routers.chapters.ChapterService.create")
    def test_md_file(self, mock_create, client, mock_db):
        pid = uuid.uuid4()
        mock_create.return_value = _make_chapter(project_id=pid, title="readme")

        response = client.post(
            f"/api/projects/{pid}/chapters/upload",
            files={"file": ("readme.md", BytesIO(b"# Hello"), "text/markdown")},
        )
        assert response.status_code == 201

    def test_invalid_content_type(self, client, mock_db):
        response = client.post(
            f"/api/projects/{uuid.uuid4()}/chapters/upload",
            files={"file": ("bad.png", BytesIO(b"\x89PNG"), "image/png")},
        )
        assert response.status_code == 400


class TestListChapters:
    """GET /api/projects/{id}/chapters"""

    @patch("app.routers.chapters.ChapterService.list_by_project")
    def test_empty(self, mock_list, client, mock_db):
        mock_list.return_value = []
        response = client.get(f"/api/projects/{uuid.uuid4()}/chapters")
        assert response.status_code == 200
        assert response.json() == []

    @patch("app.routers.chapters.ChapterService.list_by_project")
    def test_with_chapters(self, mock_list, client, mock_db):
        pid = uuid.uuid4()
        c1 = _make_chapter(project_id=pid, number=1, title="First")
        c2 = _make_chapter(project_id=pid, number=2, title="Second")
        mock_list.return_value = [c1, c2]

        response = client.get(f"/api/projects/{pid}/chapters")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "First"
        assert data[1]["title"] == "Second"
        # List view should NOT include raw_text
        assert "raw_text" not in data[0]


class TestGetChapter:
    """GET /api/projects/{id}/chapters/{cid}"""

    @patch("app.routers.chapters.ChapterService.get")
    def test_success(self, mock_get, client, mock_db):
        pid = uuid.uuid4()
        cid = uuid.uuid4()
        mock_get.return_value = _make_chapter(
            id=cid, project_id=pid, title="Detail", raw_text="Full text"
        )

        response = client.get(f"/api/projects/{pid}/chapters/{cid}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Detail"
        assert data["raw_text"] == "Full text"

    @patch("app.routers.chapters.ChapterService.get")
    def test_not_found(self, mock_get, client, mock_db):
        mock_get.return_value = None
        response = client.get(f"/api/projects/{uuid.uuid4()}/chapters/{uuid.uuid4()}")
        assert response.status_code == 404

    @patch("app.routers.chapters.ChapterService.get")
    def test_wrong_project(self, mock_get, client, mock_db):
        mock_get.return_value = _make_chapter(
            project_id=uuid.uuid4(), title="Other"
        )
        response = client.get(f"/api/projects/{uuid.uuid4()}/chapters/{uuid.uuid4()}")
        assert response.status_code == 404


class TestUpdateChapter:
    """PUT /api/projects/{id}/chapters/{cid}"""

    @patch("app.routers.chapters.ChapterService.get")
    @patch("app.routers.chapters.ChapterService.update")
    def test_success(self, mock_update, mock_get, client, mock_db):
        pid = uuid.uuid4()
        cid = uuid.uuid4()
        mock_get.return_value = _make_chapter(id=cid, project_id=pid, title="Old")
        mock_update.return_value = _make_chapter(
            id=cid, project_id=pid, title="New", raw_text="Updated", word_count=7
        )

        response = client.put(
            f"/api/projects/{pid}/chapters/{cid}",
            json={"title": "New", "raw_text": "Updated"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New"
        assert data["raw_text"] == "Updated"
        assert data["word_count"] == 7

    @patch("app.routers.chapters.ChapterService.get")
    def test_not_found(self, mock_get, client, mock_db):
        mock_get.return_value = None
        response = client.put(
            f"/api/projects/{uuid.uuid4()}/chapters/{uuid.uuid4()}",
            json={"title": "New"},
        )
        assert response.status_code == 404


class TestReorderChapters:
    """PUT /api/projects/{id}/chapters/reorder"""

    @patch("app.routers.chapters.ChapterService.reorder")
    @patch("app.routers.chapters.ChapterService.list_by_project")
    def test_success(self, mock_list, mock_reorder, client, mock_db):
        pid = uuid.uuid4()
        c1 = _make_chapter(id=uuid.uuid4(), project_id=pid, number=1)
        c2 = _make_chapter(id=uuid.uuid4(), project_id=pid, number=2)
        mock_list.return_value = [c1, c2]

        response = client.put(
            f"/api/projects/{pid}/chapters/reorder",
            json={"order": [str(c2.id), str(c1.id)]},
        )
        assert response.status_code == 200
        data = response.json()
        # list_by_project is mocked; returned order reflects mock, not reorder effect
        assert data["order"] == [str(c1.id), str(c2.id)]
        mock_reorder.assert_called_once()
        # Verify reorder was called with the requested ID order
        call_args = mock_reorder.call_args
        assert call_args[0][1] == pid
        assert list(call_args[0][2]) == [c2.id, c1.id]


class TestDeleteChapter:
    """DELETE /api/projects/{id}/chapters/{cid}"""

    @patch("app.routers.chapters.ChapterService.get")
    @patch("app.routers.chapters.ChapterService.delete")
    def test_success(self, mock_delete, mock_get, client, mock_db):
        pid = uuid.uuid4()
        cid = uuid.uuid4()
        mock_get.return_value = _make_chapter(id=cid, project_id=pid)

        response = client.delete(f"/api/projects/{pid}/chapters/{cid}")
        assert response.status_code == 204
        mock_delete.assert_called_once_with(mock_db, cid)

    @patch("app.routers.chapters.ChapterService.get")
    def test_not_found(self, mock_get, client, mock_db):
        mock_get.return_value = None
        response = client.delete(f"/api/projects/{uuid.uuid4()}/chapters/{uuid.uuid4()}")
        assert response.status_code == 404
