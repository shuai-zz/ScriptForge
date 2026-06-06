"""Unit tests for Git-based VersionService (Task 9.11)."""

import os
import tempfile
import uuid

import pytest

from app.core.config import settings
from app.services.version_service import VersionService


@pytest.fixture
def temp_storage():
    """Provide a temporary directory for project repos."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original = settings.PROJECTS_STORAGE_PATH
        settings.PROJECTS_STORAGE_PATH = tmpdir
        yield tmpdir
        settings.PROJECTS_STORAGE_PATH = original


@pytest.fixture
def project_id():
    return uuid.uuid4()


@pytest.mark.asyncio
class TestInitRepo:
    """9.1: Git repository initialization"""

    async def test_creates_repo(self, temp_storage, project_id):
        path = await VersionService.init_repo(project_id)
        assert os.path.isdir(path)
        assert os.path.isdir(os.path.join(path, ".git"))

    async def test_idempotent(self, temp_storage, project_id):
        path1 = await VersionService.init_repo(project_id)
        path2 = await VersionService.init_repo(project_id)
        assert path1 == path2


@pytest.mark.asyncio
class TestCheckpoint:
    """9.3: Checkpoint creation"""

    async def test_creates_commit(self, temp_storage, project_id):
        await VersionService.init_repo(project_id)
        result = await VersionService.checkpoint(
            project_id, "title: Test\n", "Initial checkpoint", tag="v0.1"
        )
        assert result is not None
        assert "version_id" in result
        assert result["message"] == "Initial checkpoint"

    async def test_noop_on_no_changes(self, temp_storage, project_id):
        await VersionService.init_repo(project_id)
        # First commit
        await VersionService.checkpoint(project_id, "title: A\n", "First")
        # Same content again
        result = await VersionService.checkpoint(project_id, "title: A\n", "Second")
        assert result is None


@pytest.mark.asyncio
class TestListVersions:
    """9.4: Version timeline"""

    async def test_lists_commits(self, temp_storage, project_id):
        await VersionService.init_repo(project_id)
        await VersionService.checkpoint(project_id, "title: A\n", "First")
        await VersionService.checkpoint(project_id, "title: B\n", "Second")

        versions = await VersionService.list_versions(project_id)
        assert len(versions) == 2
        assert versions[0]["message"] == "Second"
        assert versions[1]["message"] == "First"

    async def test_empty_repo(self, temp_storage, project_id):
        await VersionService.init_repo(project_id)
        versions = await VersionService.list_versions(project_id)
        assert versions == []


@pytest.mark.asyncio
class TestHasChanges:
    """9.2: Auto-save check"""

    async def test_no_changes_after_commit(self, temp_storage, project_id):
        await VersionService.init_repo(project_id)
        await VersionService.checkpoint(project_id, "title: A\n", "First")
        changed = await VersionService.has_changes(project_id)
        assert changed is False

    async def test_changes_detected(self, temp_storage, project_id):
        await VersionService.init_repo(project_id)
        await VersionService.write_script(project_id, "title: B\n")
        changed = await VersionService.has_changes(project_id)
        assert changed is True


@pytest.mark.asyncio
class TestDiff:
    """9.5: Version diff"""

    async def test_returns_diff(self, temp_storage, project_id):
        await VersionService.init_repo(project_id)
        r1 = await VersionService.checkpoint(project_id, "title: A\n", "First")
        r2 = await VersionService.checkpoint(project_id, "title: B\n", "Second")

        diff = await VersionService.get_diff(project_id, r1["version_id"], r2["version_id"])
        assert "diff" in diff
        assert diff["added_lines"] >= 1
        assert diff["removed_lines"] >= 1

    async def test_invalid_ref_raises(self, temp_storage, project_id):
        await VersionService.init_repo(project_id)
        from app.services.version_service import VersionServiceError
        with pytest.raises(VersionServiceError):
            await VersionService.get_diff(project_id, "invalid", "also-invalid")


@pytest.mark.asyncio
class TestRestore:
    """9.6: Version restore with pre-restore snapshot"""

    async def test_restores_and_creates_snapshot(self, temp_storage, project_id):
        await VersionService.init_repo(project_id)
        r1 = await VersionService.checkpoint(project_id, "title: Original\n", "First")
        await VersionService.checkpoint(project_id, "title: Modified\n", "Second")

        # Create uncommitted changes so pre-restore snapshot is created
        await VersionService.write_script(project_id, "title: Uncommitted\n")

        result = await VersionService.restore(project_id, r1["version_id"])
        assert result["restored_version"] == r1["version_id"]
        assert result["pre_restore_version"] is not None
        assert result["restore_commit"] is not None

        # Verify content restored
        content = await VersionService.read_script(project_id)
        assert "Original" in content

    async def test_restore_without_pending_changes(self, temp_storage, project_id):
        await VersionService.init_repo(project_id)
        r1 = await VersionService.checkpoint(project_id, "title: A\n", "First")
        r2 = await VersionService.checkpoint(project_id, "title: B\n", "Second")

        result = await VersionService.restore(project_id, r1["version_id"])
        assert result["pre_restore_version"] is None  # no pending changes
        assert result["restored_version"] == r1["version_id"]
