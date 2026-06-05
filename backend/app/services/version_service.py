"""Git-based version management service for scripts."""

import asyncio
import os
import uuid
from datetime import datetime, timezone

import git
from git import Repo

from app.core.config import settings


class VersionServiceError(Exception):
    """Custom error for version operations."""

    pass


class VersionService:
    """Manages per-project Git repositories for script versioning."""

    @staticmethod
    def _repo_path(project_id: uuid.UUID) -> str:
        base = settings.PROJECTS_STORAGE_PATH
        return os.path.join(base, str(project_id))

    @staticmethod
    def _script_path(project_id: uuid.UUID) -> str:
        return os.path.join(VersionService._repo_path(project_id), "script.yaml")

    @staticmethod
    async def init_repo(project_id: uuid.UUID) -> str:
        """Initialize a Git repo for a project. Idempotent."""
        path = VersionService._repo_path(project_id)
        os.makedirs(path, exist_ok=True)

        def _init():
            if not os.path.exists(os.path.join(path, ".git")):
                repo = Repo.init(path)
                # Configure git user for commits
                with repo.config_writer() as cfg:
                    cfg.set_value("user", "name", "ScriptForge")
                    cfg.set_value("user", "email", "system@scriptforge.app")
                return True
            return False

        created = await asyncio.to_thread(_init)
        return path

    @staticmethod
    async def ensure_repo(project_id: uuid.UUID) -> Repo:
        """Ensure repo exists and return it."""
        path = VersionService._repo_path(project_id)
        if not os.path.exists(os.path.join(path, ".git")):
            await VersionService.init_repo(project_id)

        def _open():
            return Repo(path)

        return await asyncio.to_thread(_open)

    @staticmethod
    async def write_script(project_id: uuid.UUID, yaml_content: str) -> None:
        """Write script YAML to the project repo."""
        path = VersionService._script_path(project_id)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        def _write():
            with open(path, "w", encoding="utf-8") as f:
                f.write(yaml_content)

        await asyncio.to_thread(_write)

    @staticmethod
    async def read_script(project_id: uuid.UUID) -> str:
        """Read script YAML from the project repo."""
        path = VersionService._script_path(project_id)

        def _read():
            if not os.path.exists(path):
                return ""
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

        return await asyncio.to_thread(_read)

    @staticmethod
    async def has_changes(project_id: uuid.UUID) -> bool:
        """Check if repo has uncommitted changes."""
        repo = await VersionService.ensure_repo(project_id)

        def _check():
            return repo.is_dirty(untracked_files=True)

        return await asyncio.to_thread(_check)

    @staticmethod
    async def checkpoint(
        project_id: uuid.UUID,
        yaml_content: str,
        message: str,
        tag: str | None = None,
    ) -> dict:
        """Save script and create a git commit."""
        await VersionService.write_script(project_id, yaml_content)
        repo = await VersionService.ensure_repo(project_id)

        def _commit():
            repo.git.add("script.yaml")
            if not repo.is_dirty(untracked_files=True):
                # Nothing to commit
                return None
            commit = repo.index.commit(message)
            if tag:
                repo.create_tag(tag, commit.hexsha)
            return {
                "version_id": commit.hexsha,
                "message": commit.message.strip(),
                "committed_at": datetime.fromtimestamp(commit.committed_date, tz=timezone.utc).isoformat(),
                "author": commit.author.name,
            }

        return await asyncio.to_thread(_commit)

    @staticmethod
    async def list_versions(project_id: uuid.UUID) -> list[dict]:
        """Parse git log into structured version list."""
        repo = await VersionService.ensure_repo(project_id)

        def _log():
            versions = []
            try:
                for commit in repo.iter_commits("HEAD"):
                    tags = [t.name for t in repo.tags if t.commit.hexsha == commit.hexsha]
                    versions.append({
                        "version_id": commit.hexsha,
                        "short_id": commit.hexsha[:7],
                        "message": commit.message.strip(),
                        "committed_at": datetime.fromtimestamp(commit.committed_date, tz=timezone.utc).isoformat(),
                        "author": commit.author.name,
                        "tags": tags,
                    })
            except git.GitCommandError:
                # No commits yet
                pass
            return versions

        return await asyncio.to_thread(_log)

    @staticmethod
    async def get_diff(project_id: uuid.UUID, a: str, b: str) -> dict:
        """Get unified diff between two versions."""
        repo = await VersionService.ensure_repo(project_id)

        def _diff():
            try:
                diff_text = repo.git.diff(f"{a}..{b}", "script.yaml", unified=3)
            except git.GitCommandError as e:
                raise VersionServiceError(f"Invalid version reference: {e}")

            # Count changes
            added = diff_text.count("\n+")
            removed = diff_text.count("\n-")
            return {
                "diff": diff_text,
                "added_lines": added,
                "removed_lines": removed,
            }

        return await asyncio.to_thread(_diff)

    @staticmethod
    async def restore(project_id: uuid.UUID, version_id: str) -> dict:
        """Checkout a specific version. Creates a pre-restore snapshot first."""
        repo = await VersionService.ensure_repo(project_id)

        def _restore():
            # Create pre-restore snapshot if there are changes
            if repo.is_dirty(untracked_files=True):
                repo.git.add("script.yaml")
                pre_restore = repo.index.commit("auto: pre-restore snapshot")
            else:
                pre_restore = None

            # Checkout the target version
            repo.git.checkout(version_id, "--", "script.yaml")
            repo.git.add("script.yaml")
            restore_commit = repo.index.commit(f"restore: rollback to {version_id[:7]}")

            return {
                "restored_version": version_id,
                "pre_restore_version": pre_restore.hexsha if pre_restore else None,
                "restore_commit": restore_commit.hexsha,
            }

        return await asyncio.to_thread(_restore)
