"""Unit tests for Annotation REST endpoints (Tasks 8.1-8.2, 8.8)."""

import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


# ── Helpers ──


def _make_annotation(**kwargs):
    """Build a mock Annotation ORM object."""
    ann = MagicMock()
    ann.id = kwargs.get("id", uuid.uuid4())
    ann.project_id = kwargs.get("project_id", uuid.uuid4())
    ann.annotation_id = kwargs.get("annotation_id", "ann-001")
    ann.severity = kwargs.get("severity", "suggestion")
    ann.category = kwargs.get("category", "inner_to_visual")
    ann.title = kwargs.get("title", "Test Annotation")
    ann.description = kwargs.get("description", "Description here")
    ann.target_reference = kwargs.get("target_reference", {"type": "block", "block_id": "b1"})
    ann.source_quote = kwargs.get("source_quote", None)
    ann.alternatives = kwargs.get("alternatives", [])
    ann.confidence = kwargs.get("confidence", 0.85)
    ann.auto_applied = kwargs.get("auto_applied", False)
    ann.status = kwargs.get("status", "pending")
    ann.created_at = kwargs.get("created_at", datetime.now())
    ann.updated_at = kwargs.get("updated_at", datetime.now())
    return ann


# ── Fixtures ──


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


# ═══════════════════════════════════════════════════════════════
# Create
# ═══════════════════════════════════════════════════════════════


class TestCreateAnnotation:
    """POST /api/projects/{id}/annotations"""

    @patch("app.routers.annotations.AnnotationService.create")
    def test_success(self, mock_create, client, mock_db):
        pid = uuid.uuid4()
        aid = uuid.uuid4()
        mock_create.return_value = _make_annotation(
            id=aid, project_id=pid, title="Inner to visual"
        )

        response = client.post(
            f"/api/projects/{pid}/annotations",
            json={
                "annotation_id": "ann-001",
                "severity": "suggestion",
                "category": "inner_to_visual",
                "title": "Inner to visual",
                "description": "Converted internal monologue to visual action",
                "target_reference": {"type": "block", "block_id": "b1"},
                "confidence": 0.85,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Inner to visual"
        assert data["status"] == "pending"
        mock_create.assert_called_once()

    def test_invalid_severity(self, client, mock_db):
        response = client.post(
            f"/api/projects/{uuid.uuid4()}/annotations",
            json={
                "annotation_id": "ann-001",
                "severity": "invalid",
                "category": "inner_to_visual",
                "title": "X",
                "description": "Y",
                "target_reference": {"type": "block"},
                "confidence": 0.5,
            },
        )
        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════════
# List
# ═══════════════════════════════════════════════════════════════


class TestListAnnotations:
    """GET /api/projects/{id}/annotations"""

    @patch("app.routers.annotations.AnnotationService.list_by_project")
    def test_empty(self, mock_list, client, mock_db):
        mock_list.return_value = []
        response = client.get(f"/api/projects/{uuid.uuid4()}/annotations")
        assert response.status_code == 200
        assert response.json() == []

    @patch("app.routers.annotations.AnnotationService.list_by_project")
    def test_with_filters(self, mock_list, client, mock_db):
        pid = uuid.uuid4()
        mock_list.return_value = [
            _make_annotation(project_id=pid, severity="warning"),
        ]

        response = client.get(
            f"/api/projects/{pid}/annotations?severity=warning&confidence_min=0.5&status=pending"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["severity"] == "warning"
        mock_list.assert_called_once()
        call_kwargs = mock_list.call_args.kwargs
        assert call_kwargs["severity"] == "warning"
        assert call_kwargs["confidence_min"] == 0.5
        assert call_kwargs["status"] == "pending"


# ═══════════════════════════════════════════════════════════════
# Get
# ═══════════════════════════════════════════════════════════════


class TestGetAnnotation:
    """GET /api/projects/{id}/annotations/{aid}"""

    @patch("app.routers.annotations.AnnotationService.get")
    def test_success(self, mock_get, client, mock_db):
        pid = uuid.uuid4()
        aid = uuid.uuid4()
        mock_get.return_value = _make_annotation(id=aid, project_id=pid)

        response = client.get(f"/api/projects/{pid}/annotations/{aid}")
        assert response.status_code == 200
        assert response.json()["id"] == str(aid)

    @patch("app.routers.annotations.AnnotationService.get")
    def test_not_found(self, mock_get, client, mock_db):
        mock_get.return_value = None
        response = client.get(f"/api/projects/{uuid.uuid4()}/annotations/{uuid.uuid4()}")
        assert response.status_code == 404

    @patch("app.routers.annotations.AnnotationService.get")
    def test_wrong_project(self, mock_get, client, mock_db):
        mock_get.return_value = _make_annotation(project_id=uuid.uuid4())
        response = client.get(f"/api/projects/{uuid.uuid4()}/annotations/{uuid.uuid4()}")
        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════
# Update
# ═══════════════════════════════════════════════════════════════


class TestUpdateAnnotation:
    """PUT /api/projects/{id}/annotations/{aid}"""

    @patch("app.routers.annotations.AnnotationService.get")
    @patch("app.routers.annotations.AnnotationService.update")
    def test_success(self, mock_update, mock_get, client, mock_db):
        pid = uuid.uuid4()
        aid = uuid.uuid4()
        mock_get.return_value = _make_annotation(id=aid, project_id=pid, status="pending")
        mock_update.return_value = _make_annotation(id=aid, project_id=pid, status="accepted")

        response = client.put(
            f"/api/projects/{pid}/annotations/{aid}",
            json={"status": "accepted"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "accepted"

    @patch("app.routers.annotations.AnnotationService.get")
    def test_not_found(self, mock_get, client, mock_db):
        mock_get.return_value = None
        response = client.put(
            f"/api/projects/{uuid.uuid4()}/annotations/{uuid.uuid4()}",
            json={"status": "accepted"},
        )
        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════
# Action
# ═══════════════════════════════════════════════════════════════


class TestAnnotationAction:
    """POST /api/projects/{id}/annotations/{aid}/action"""

    @patch("app.routers.annotations.AnnotationService.get")
    @patch("app.routers.annotations.AnnotationService.set_status")
    def test_accept(self, mock_set_status, mock_get, client, mock_db):
        pid = uuid.uuid4()
        aid = uuid.uuid4()
        mock_get.return_value = _make_annotation(id=aid, project_id=pid)
        mock_set_status.return_value = _make_annotation(id=aid, project_id=pid, status="accepted")

        response = client.post(
            f"/api/projects/{pid}/annotations/{aid}/action",
            json={"action": "accept"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "accepted"
        mock_set_status.assert_called_once_with(mock_db, aid, "accepted")

    @patch("app.routers.annotations.AnnotationService.get")
    @patch("app.routers.annotations.AnnotationService.set_status")
    def test_ignore(self, mock_set_status, mock_get, client, mock_db):
        pid = uuid.uuid4()
        aid = uuid.uuid4()
        mock_get.return_value = _make_annotation(id=aid, project_id=pid)
        mock_set_status.return_value = _make_annotation(id=aid, project_id=pid, status="ignored")

        response = client.post(
            f"/api/projects/{pid}/annotations/{aid}/action",
            json={"action": "ignore"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"
        mock_set_status.assert_called_once_with(mock_db, aid, "ignored")

    @patch("app.routers.annotations.AnnotationService.get")
    def test_invalid_action(self, mock_get, client, mock_db):
        mock_get.return_value = _make_annotation()
        response = client.post(
            f"/api/projects/{uuid.uuid4()}/annotations/{uuid.uuid4()}/action",
            json={"action": "invalid"},
        )
        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════════
# Delete
# ═══════════════════════════════════════════════════════════════


class TestDeleteAnnotation:
    """DELETE /api/projects/{id}/annotations/{aid}"""

    @patch("app.routers.annotations.AnnotationService.get")
    @patch("app.routers.annotations.AnnotationService.delete")
    def test_success(self, mock_delete, mock_get, client, mock_db):
        pid = uuid.uuid4()
        aid = uuid.uuid4()
        mock_get.return_value = _make_annotation(id=aid, project_id=pid)
        mock_delete.return_value = True

        response = client.delete(f"/api/projects/{pid}/annotations/{aid}")
        assert response.status_code == 204

    @patch("app.routers.annotations.AnnotationService.get")
    def test_not_found(self, mock_get, client, mock_db):
        mock_get.return_value = None
        response = client.delete(f"/api/projects/{uuid.uuid4()}/annotations/{uuid.uuid4()}")
        assert response.status_code == 404
