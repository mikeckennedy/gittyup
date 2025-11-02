"""Tests for --ignore-all-changes feature."""

import subprocess
from pathlib import Path

import pytest

from gittyup import git_operations


class TestIgnoreAllChanges:
    """Tests for the --ignore-all-changes flag functionality."""

    @pytest.mark.asyncio
    async def test_check_merge_conflicts_no_upstream_changes(self, tmp_path: Path) -> None:
        """Test that when there are no upstream changes, it's safe to pull."""
        # Initialize a git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)

        # Create a file and commit
        (repo_path / "file1.txt").write_text("content")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)

        # Create a remote (fake)
        remote_path = tmp_path / "remote"
        remote_path.mkdir()
        subprocess.run(["git", "init", "--bare"], cwd=remote_path, check=True)

        # Add remote and push
        subprocess.run(["git", "remote", "add", "origin", str(remote_path)], cwd=repo_path, check=True)
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=repo_path, check=True)

        # Modify a different file locally
        (repo_path / "file2.txt").write_text("local change")
        subprocess.run(["git", "add", "file2.txt"], cwd=repo_path, check=True)

        # Check for conflicts - should be safe since no upstream changes
        is_safe, error_msg = await git_operations.async_check_for_merge_conflicts(repo_path, timeout=10)

        assert is_safe is True
        assert error_msg is None

    @pytest.mark.asyncio
    async def test_check_merge_conflicts_different_files(self, tmp_path: Path) -> None:
        """Test that when upstream changes different files, it's safe to pull."""
        # Initialize a git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)

        # Create files and commit
        (repo_path / "file1.txt").write_text("content1")
        (repo_path / "file2.txt").write_text("content2")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)

        # Create a remote (fake) using another directory
        remote_path = tmp_path / "remote"
        remote_path.mkdir()
        subprocess.run(["git", "init", "--bare"], cwd=remote_path, check=True)

        # Add remote and push
        subprocess.run(["git", "remote", "add", "origin", str(remote_path)], cwd=repo_path, check=True)
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=repo_path, check=True)

        # Clone to another location to simulate upstream changes
        upstream_repo = tmp_path / "upstream_clone"
        subprocess.run(["git", "clone", str(remote_path), str(upstream_repo)], check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=upstream_repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=upstream_repo, check=True)

        # Modify file1 in upstream and push
        (upstream_repo / "file1.txt").write_text("upstream change")
        subprocess.run(["git", "add", "file1.txt"], cwd=upstream_repo, check=True)
        subprocess.run(["git", "commit", "-m", "Upstream change"], cwd=upstream_repo, check=True)
        subprocess.run(["git", "push"], cwd=upstream_repo, check=True)

        # Modify file2 locally (different file)
        (repo_path / "file2.txt").write_text("local change")

        # Check for conflicts - should be safe since different files
        is_safe, error_msg = await git_operations.async_check_for_merge_conflicts(repo_path, timeout=10)

        assert is_safe is True
        assert error_msg is None

    @pytest.mark.asyncio
    async def test_check_merge_conflicts_same_file(self, tmp_path: Path) -> None:
        """Test that when upstream changes the same file as local changes, it's not safe."""
        # Initialize a git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)

        # Create files and commit
        (repo_path / "file1.txt").write_text("content1")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)

        # Create a remote (fake)
        remote_path = tmp_path / "remote"
        remote_path.mkdir()
        subprocess.run(["git", "init", "--bare"], cwd=remote_path, check=True)

        # Add remote and push
        subprocess.run(["git", "remote", "add", "origin", str(remote_path)], cwd=repo_path, check=True)
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=repo_path, check=True)

        # Clone to another location to simulate upstream changes
        upstream_repo = tmp_path / "upstream_clone"
        subprocess.run(["git", "clone", str(remote_path), str(upstream_repo)], check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=upstream_repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=upstream_repo, check=True)

        # Modify file1 in upstream and push
        (upstream_repo / "file1.txt").write_text("upstream change")
        subprocess.run(["git", "add", "file1.txt"], cwd=upstream_repo, check=True)
        subprocess.run(["git", "commit", "-m", "Upstream change"], cwd=upstream_repo, check=True)
        subprocess.run(["git", "push"], cwd=upstream_repo, check=True)

        # Modify file1 locally (same file)
        (repo_path / "file1.txt").write_text("local change")

        # Check for conflicts - should NOT be safe since same file
        is_safe, error_msg = await git_operations.async_check_for_merge_conflicts(repo_path, timeout=10)

        assert is_safe is False
        assert error_msg is not None
        assert "file1.txt" in error_msg

    @pytest.mark.asyncio
    async def test_check_merge_conflicts_with_untracked_files(self, tmp_path: Path) -> None:
        """Test that untracked files that don't conflict are safe."""
        # Initialize a git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)

        # Create files and commit
        (repo_path / "file1.txt").write_text("content1")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)

        # Create a remote (fake)
        remote_path = tmp_path / "remote"
        remote_path.mkdir()
        subprocess.run(["git", "init", "--bare"], cwd=remote_path, check=True)

        # Add remote and push
        subprocess.run(["git", "remote", "add", "origin", str(remote_path)], cwd=repo_path, check=True)
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=repo_path, check=True)

        # Create untracked file locally
        (repo_path / "untracked.txt").write_text("untracked content")

        # Check for conflicts - should be safe since no upstream changes
        is_safe, error_msg = await git_operations.async_check_for_merge_conflicts(repo_path, timeout=10)

        assert is_safe is True
        assert error_msg is None
