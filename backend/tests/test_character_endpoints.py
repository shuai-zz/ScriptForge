"""Unit tests for Character and CharacterRelationship endpoints."""

import uuid
from unittest.mock import MagicMock, patch

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


class TestCreateRelationship:
    """POST /api/projects/{id}/characters/relationships"""

    @patch("app.routers.characters.CharacterRelationshipService.create")
    def test_success(self, mock_create, client, mock_db):
        project_id = uuid.uuid4()
        source_id = uuid.uuid4()
        target_id = uuid.uuid4()
        rel = MagicMock()
        rel.id = uuid.uuid4()
        rel.project_id = project_id
        rel.source_character_id = source_id
        rel.target_character_id = target_id
        rel.type = "friend"
        rel.intensity = 4
        mock_create.return_value = rel

        response = client.post(
            f"/api/projects/{project_id}/characters/relationships",
            json={
                "source_character_id": str(source_id),
                "target_character_id": str(target_id),
                "type": "friend",
                "intensity": 4,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["source_character_id"] == str(source_id)
        assert data["target_character_id"] == str(target_id)
        assert data["type"] == "friend"
        assert data["intensity"] == 4
        mock_create.assert_called_once()

    def test_missing_source_character_id(self, client, mock_db):
        project_id = uuid.uuid4()
        response = client.post(
            f"/api/projects/{project_id}/characters/relationships",
            json={
                "source_character_id": "",
                "target_character_id": str(uuid.uuid4()),
                "type": "friend",
            },
        )

        assert response.status_code == 422
        data = response.json()
        message = data["error"]["message"]
        assert "source_character_id" in message and "target_character_id" in message

    def test_missing_target_character_id(self, client, mock_db):
        project_id = uuid.uuid4()
        response = client.post(
            f"/api/projects/{project_id}/characters/relationships",
            json={
                "source_character_id": str(uuid.uuid4()),
                "target_character_id": "",
                "type": "friend",
            },
        )

        assert response.status_code == 422
        data = response.json()
        message = data["error"]["message"]
        assert "source_character_id" in message and "target_character_id" in message


class TestListRelationships:
    """GET /api/projects/{id}/characters/relationships"""

    @patch("app.routers.characters.CharacterRelationshipService.list_by_project")
    def test_route_not_shadowed_by_character_id(self, mock_list, client, mock_db):
        # Regression: the literal /relationships route must be matched before
        # /{character_id}. If /{character_id} wins, "relationships" fails UUID
        # validation and this returns 422 instead of the relationship list,
        # which breaks the character graph.
        mock_list.return_value = []
        project_id = uuid.uuid4()

        response = client.get(
            f"/api/projects/{project_id}/characters/relationships"
        )

        assert response.status_code == 200
        assert response.json() == []
        mock_list.assert_called_once()
