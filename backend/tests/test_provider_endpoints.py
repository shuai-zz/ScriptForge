"""Unit tests for the global LLM Provider endpoints (/api/providers)."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.main import app


def _make_provider(provider_id: str = "prov-claude", label: str = "Claude") -> MagicMock:
    p = MagicMock()
    p.id = uuid.uuid4()
    p.provider_id = provider_id
    p.label = label
    p.provider_type = "anthropic"
    p.model_name = "claude-sonnet-4-6"
    p.base_url = None
    p.encrypted_api_key = "x" * 40
    p.assigned_stages = ["stage_0"]
    p.parameters = {"temperature": 0.7}
    return p


def _exec_result(scalars_all=None, scalar_one=None) -> MagicMock:
    """Build a mock for the object returned by ``await db.execute(...)``."""
    result = MagicMock()
    result.scalars.return_value.all.return_value = scalars_all or []
    result.scalar_one_or_none.return_value = scalar_one
    return result


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    db.rollback = AsyncMock()
    db.execute = AsyncMock(return_value=_exec_result())
    return db


@pytest.fixture
def client(mock_db):
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()


class TestListProviders:
    """GET /api/providers"""

    def test_empty(self, client, mock_db):
        mock_db.execute = AsyncMock(return_value=_exec_result(scalars_all=[]))
        r = client.get("/api/providers")
        assert r.status_code == 200
        assert r.json() == []

    def test_with_providers(self, client, mock_db):
        mock_db.execute = AsyncMock(
            return_value=_exec_result(scalars_all=[_make_provider()])
        )
        r = client.get("/api/providers")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["provider_id"] == "prov-claude"
        # key never returned in plaintext, only masked
        assert "api_key" not in data[0]
        assert data[0]["api_key_masked"]


class TestGetProvider:
    """GET /api/providers/{provider_id}"""

    def test_found(self, client, mock_db):
        mock_db.execute = AsyncMock(
            return_value=_exec_result(scalar_one=_make_provider())
        )
        r = client.get("/api/providers/prov-claude")
        assert r.status_code == 200
        assert r.json()["provider_id"] == "prov-claude"

    def test_not_found(self, client, mock_db):
        mock_db.execute = AsyncMock(return_value=_exec_result(scalar_one=None))
        r = client.get("/api/providers/prov-missing")
        assert r.status_code == 404


class TestCreateProvider:
    """POST /api/providers"""

    def test_success_with_base_url(self, client, mock_db):
        payload = {
            "label": "Claude Main",
            "provider_type": "anthropic",
            "model_name": "claude-sonnet-4-6",
            "base_url": "https://anthropic.proxy.internal",
            "api_key": "sk-ant-secret",
            "assigned_stages": ["stage_0", "stage_1"],
            "parameters": {"temperature": 0.7, "max_tokens": None, "thinking": True},
        }
        r = client.post("/api/providers", json=payload)
        assert r.status_code == 201
        data = r.json()
        assert data["provider_id"] == "prov-claude-main"
        assert data["base_url"] == "https://anthropic.proxy.internal"
        assert "secret" not in data["api_key_masked"]
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

    def test_duplicate_label_returns_409(self, client, mock_db):
        mock_db.commit = AsyncMock(
            side_effect=IntegrityError("INSERT", {}, Exception("dup"))
        )
        payload = {
            "label": "Dup",
            "provider_type": "anthropic",
            "model_name": "claude-sonnet-4-6",
            "api_key": "sk-x",
            "assigned_stages": [],
            "parameters": {"temperature": 0.7},
        }
        r = client.post("/api/providers", json=payload)
        assert r.status_code == 409
        mock_db.rollback.assert_awaited_once()


class TestDeleteProvider:
    """DELETE /api/providers/{provider_id}"""

    def test_success(self, client, mock_db):
        mock_db.execute = AsyncMock(
            return_value=_exec_result(scalar_one=_make_provider())
        )
        r = client.delete("/api/providers/prov-claude")
        assert r.status_code == 204
        mock_db.delete.assert_awaited_once()

    def test_not_found(self, client, mock_db):
        mock_db.execute = AsyncMock(return_value=_exec_result(scalar_one=None))
        r = client.delete("/api/providers/prov-missing")
        assert r.status_code == 404
