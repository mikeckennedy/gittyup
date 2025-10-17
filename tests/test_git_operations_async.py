"""Tests for async git operations."""

# ruff: noqa: SIM117

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gittyup.git_operations import (
    GitTimeoutError,
    PullResult,
    _async_get_commit_details,
    _async_get_file_changes,
    _async_run_git_command,
    async_get_current_branch,
    async_get_repo_status,
    async_get_uncommitted_files,
    async_pull_repository_detailed,
    async_update_repository_with_log,
)
from gittyup.models import CommitInfo, FileChange, RepoInfo, RepoStatus, UncommittedFile


class TestAsyncRunGitCommand:
    """Tests for _async_run_git_command helper function."""

    @pytest.mark.asyncio
    async def test_successful_command(self) -> None:
        """Test successful command execution."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"test output", b""))
            mock_subprocess.return_value = mock_process

            returncode, stdout, stderr = await _async_run_git_command(["git", "status"])

            assert returncode == 0
            assert stdout == "test output"
            assert stderr == ""

    @pytest.mark.asyncio
    async def test_command_with_error_output(self) -> None:
        """Test command with stderr output."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(return_value=(b"", b"error message"))
            mock_subprocess.return_value = mock_process

            returncode, stdout, stderr = await _async_run_git_command(["git", "pull"])

            assert returncode == 1
            assert stdout == ""
            assert stderr == "error message"

    @pytest.mark.asyncio
    async def test_command_timeout(self) -> None:
        """Test command timeout handling."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = None
            mock_process.communicate = AsyncMock(side_effect=TimeoutError())
            mock_process.kill = MagicMock()
            mock_process.wait = AsyncMock()
            mock_subprocess.return_value = mock_process

            with pytest.raises(TimeoutError, match="timed out"):
                await _async_run_git_command(["git", "clone"], timeout=1)


class TestAsyncGetRepoStatus:
    """Tests for async_get_repo_status function."""

    @pytest.mark.asyncio
    async def test_clean_repo_with_remote(self, tmp_path: Path) -> None:
        """Test status check for clean repo with remote."""
        with patch("gittyup.git_operations._async_run_git_command") as mock_cmd:
            # Mock: has remote, is clean, not detached, has upstream
            mock_cmd.side_effect = [
                (0, "origin", ""),  # git remote
                (0, "", ""),  # git status --porcelain
                (0, "refs/heads/main", ""),  # symbolic-ref
                (0, "origin/main", ""),  # upstream branch
            ]

            status = await async_get_repo_status(tmp_path)

            assert status["has_remote"] is True
            assert status["is_clean"] is True
            assert status["is_detached"] is False
            assert status["has_upstream"] is True

    @pytest.mark.asyncio
    async def test_dirty_repo(self, tmp_path: Path) -> None:
        """Test status check for repo with uncommitted changes."""
        with patch("gittyup.git_operations._async_run_git_command") as mock_cmd:
            mock_cmd.side_effect = [
                (0, "origin", ""),  # git remote
                (0, " M file.txt", ""),  # git status --porcelain (dirty)
                (0, "refs/heads/main", ""),  # symbolic-ref
                (0, "origin/main", ""),  # upstream branch
            ]

            status = await async_get_repo_status(tmp_path)

            assert status["is_clean"] is False

    @pytest.mark.asyncio
    async def test_detached_head(self, tmp_path: Path) -> None:
        """Test status check for detached HEAD."""
        with patch("gittyup.git_operations._async_run_git_command") as mock_cmd:
            mock_cmd.side_effect = [
                (0, "origin", ""),  # git remote
                (0, "", ""),  # git status --porcelain
                (1, "", ""),  # symbolic-ref (fails = detached)
            ]

            status = await async_get_repo_status(tmp_path)

            assert status["is_detached"] is True

    @pytest.mark.asyncio
    async def test_timeout_error(self, tmp_path: Path) -> None:
        """Test handling of timeout errors."""
        with patch("gittyup.git_operations._async_run_git_command") as mock_cmd:
            mock_cmd.side_effect = TimeoutError("timeout")

            with pytest.raises(GitTimeoutError):
                await async_get_repo_status(tmp_path)


class TestAsyncGetCurrentBranch:
    """Tests for async_get_current_branch function."""

    @pytest.mark.asyncio
    async def test_get_current_branch(self, tmp_path: Path) -> None:
        """Test getting current branch name."""
        with patch("gittyup.git_operations._async_run_git_command") as mock_cmd:
            mock_cmd.return_value = (0, "main\n", "")

            branch = await async_get_current_branch(tmp_path)

            assert branch == "main"

    @pytest.mark.asyncio
    async def test_detached_head_returns_none(self, tmp_path: Path) -> None:
        """Test that detached HEAD returns None."""
        with patch("gittyup.git_operations._async_run_git_command") as mock_cmd:
            mock_cmd.return_value = (0, "HEAD", "")

            branch = await async_get_current_branch(tmp_path)

            assert branch is None

    @pytest.mark.asyncio
    async def test_error_returns_none(self, tmp_path: Path) -> None:
        """Test that errors return None."""
        with patch("gittyup.git_operations._async_run_git_command") as mock_cmd:
            mock_cmd.side_effect = Exception("error")

            branch = await async_get_current_branch(tmp_path)

            assert branch is None


class TestAsyncGetUncommittedFiles:
    """Tests for async_get_uncommitted_files function."""

    @pytest.mark.asyncio
    async def test_get_modified_files(self, tmp_path: Path) -> None:
        """Test getting modified files."""
        with patch("gittyup.git_operations._async_run_git_command") as mock_cmd:
            mock_cmd.return_value = (0, " M file.txt\n", "")

            files = await async_get_uncommitted_files(tmp_path)

            assert len(files) == 1
            assert files[0].path == "file.txt"
            assert files[0].status == "M"

    @pytest.mark.asyncio
    async def test_get_untracked_files(self, tmp_path: Path) -> None:
        """Test getting untracked files."""
        with patch("gittyup.git_operations._async_run_git_command") as mock_cmd:
            mock_cmd.return_value = (0, "?? newfile.txt\n", "")

            files = await async_get_uncommitted_files(tmp_path)

            assert len(files) == 1
            assert files[0].path == "newfile.txt"
            assert files[0].status_description == "Untracked"

    @pytest.mark.asyncio
    async def test_empty_status(self, tmp_path: Path) -> None:
        """Test with no uncommitted files."""
        with patch("gittyup.git_operations._async_run_git_command") as mock_cmd:
            mock_cmd.return_value = (0, "", "")

            files = await async_get_uncommitted_files(tmp_path)

            assert len(files) == 0


class TestAsyncGetCommitDetails:
    """Tests for _async_get_commit_details function."""

    @pytest.mark.asyncio
    async def test_get_commit_details(self, tmp_path: Path) -> None:
        """Test getting commit details."""
        output = "abc123|John Doe|2025-10-16T10:00:00|Initial commit\ndef456|Jane Doe|2025-10-16T11:00:00|Fix bug\n"
        with patch("gittyup.git_operations._async_run_git_command") as mock_cmd:
            mock_cmd.return_value = (0, output, "")

            commits = await _async_get_commit_details(tmp_path, "abc123", "def456")

            assert len(commits) == 2
            assert commits[0].commit_hash == "abc123"
            assert commits[0].author == "John Doe"
            assert commits[1].commit_hash == "def456"

    @pytest.mark.asyncio
    async def test_empty_commit_log(self, tmp_path: Path) -> None:
        """Test with no commits."""
        with patch("gittyup.git_operations._async_run_git_command") as mock_cmd:
            mock_cmd.return_value = (0, "", "")

            commits = await _async_get_commit_details(tmp_path, "abc123", "def456")

            assert len(commits) == 0


class TestAsyncGetFileChanges:
    """Tests for _async_get_file_changes function."""

    @pytest.mark.asyncio
    async def test_get_file_changes(self, tmp_path: Path) -> None:
        """Test getting file changes."""
        with patch("gittyup.git_operations._async_run_git_command") as mock_cmd:
            # First call: numstat
            # Second call: name-status
            mock_cmd.side_effect = [
                (0, "10\t5\tfile.txt\n", ""),
                (0, "M\tfile.txt\n", ""),
            ]

            files = await _async_get_file_changes(tmp_path, "abc123", "def456")

            assert len(files) == 1
            assert files[0].path == "file.txt"
            assert files[0].insertions == 10
            assert files[0].deletions == 5
            assert files[0].change_type == "modified"

    @pytest.mark.asyncio
    async def test_file_changes_with_additions(self, tmp_path: Path) -> None:
        """Test file changes including added files."""
        with patch("gittyup.git_operations._async_run_git_command") as mock_cmd:
            mock_cmd.side_effect = [
                (0, "20\t0\tnewfile.txt\n", ""),
                (0, "A\tnewfile.txt\n", ""),
            ]

            files = await _async_get_file_changes(tmp_path, "abc123", "def456")

            assert len(files) == 1
            assert files[0].change_type == "added"


class TestAsyncPullRepositoryDetailed:
    """Tests for async_pull_repository_detailed function."""

    @pytest.mark.asyncio
    async def test_already_up_to_date(self, tmp_path: Path) -> None:
        """Test pull when already up to date."""
        with patch("gittyup.git_operations._async_run_git_command") as mock_cmd:
            mock_cmd.return_value = (0, "Already up to date.", "")

            result = await async_pull_repository_detailed(tmp_path)

            assert result.success is True
            assert result.already_up_to_date is True

    @pytest.mark.asyncio
    async def test_successful_pull_with_changes(self, tmp_path: Path) -> None:
        """Test successful pull with changes."""
        output = "Updating abc123..def456\nFast-forward\n file.txt | 10 +++++++---\n 1 file changed, 8 insertions(+), 2 deletions(-)\n"
        with patch("gittyup.git_operations._async_run_git_command") as mock_cmd:
            with patch("gittyup.git_operations._async_get_commit_details") as mock_commits:
                with patch("gittyup.git_operations._async_get_file_changes") as mock_files:
                    mock_cmd.return_value = (0, output, "")
                    mock_commits.return_value = [CommitInfo("def456", "John Doe", "2025-10-16T10:00:00", "Test commit")]
                    mock_files.return_value = [FileChange("file.txt", "modified", 8, 2)]

                    result = await async_pull_repository_detailed(tmp_path)

                    assert result.success is True
                    assert result.already_up_to_date is False
                    assert result.files_changed == 1
                    assert result.insertions == 8
                    assert result.deletions == 2
                    assert len(result.commits) == 1

    @pytest.mark.asyncio
    async def test_pull_with_merge_conflict(self, tmp_path: Path) -> None:
        """Test pull with merge conflict."""
        with patch("gittyup.git_operations._async_run_git_command") as mock_cmd:
            mock_cmd.return_value = (1, "", "CONFLICT (content): Merge conflict in file.txt")

            result = await async_pull_repository_detailed(tmp_path)

            assert result.success is False
            assert result.error_message == "Merge conflict detected"

    @pytest.mark.asyncio
    async def test_pull_timeout(self, tmp_path: Path) -> None:
        """Test pull timeout."""
        with patch("gittyup.git_operations._async_run_git_command") as mock_cmd:
            mock_cmd.side_effect = TimeoutError("timeout")

            with pytest.raises(GitTimeoutError):
                await async_pull_repository_detailed(tmp_path)


class TestAsyncUpdateRepositoryWithLog:
    """Tests for async_update_repository_with_log function."""

    @pytest.mark.asyncio
    async def test_skip_no_remote(self, tmp_path: Path) -> None:
        """Test skipping repo with no remote."""
        repo = RepoInfo(path=tmp_path, name="test-repo")

        with patch("gittyup.git_operations.async_get_current_branch") as mock_branch:
            with patch("gittyup.git_operations.async_get_repo_status") as mock_status:
                mock_branch.return_value = "main"
                mock_status.return_value = {
                    "has_remote": False,
                    "is_clean": True,
                    "is_detached": False,
                    "has_upstream": False,
                }

                updated_repo, log_entry = await async_update_repository_with_log(repo)

                assert updated_repo.status == RepoStatus.SKIPPED
                assert log_entry.status == "skipped"
                assert log_entry.skip_reason == "No remote configured"

    @pytest.mark.asyncio
    async def test_skip_detached_head(self, tmp_path: Path) -> None:
        """Test skipping repo in detached HEAD state."""
        repo = RepoInfo(path=tmp_path, name="test-repo")

        with patch("gittyup.git_operations.async_get_current_branch") as mock_branch:
            with patch("gittyup.git_operations.async_get_repo_status") as mock_status:
                mock_branch.return_value = None
                mock_status.return_value = {
                    "has_remote": True,
                    "is_clean": True,
                    "is_detached": True,
                    "has_upstream": False,
                }

                updated_repo, _log_entry = await async_update_repository_with_log(repo)

                assert updated_repo.status == RepoStatus.SKIPPED
                assert "Detached HEAD" in updated_repo.message

    @pytest.mark.asyncio
    async def test_skip_uncommitted_changes(self, tmp_path: Path) -> None:
        """Test skipping repo with uncommitted changes."""
        repo = RepoInfo(path=tmp_path, name="test-repo")

        with patch("gittyup.git_operations.async_get_current_branch") as mock_branch:
            with patch("gittyup.git_operations.async_get_repo_status") as mock_status:
                with patch("gittyup.git_operations.async_get_uncommitted_files") as mock_files:
                    mock_branch.return_value = "main"
                    mock_status.return_value = {
                        "has_remote": True,
                        "is_clean": False,
                        "is_detached": False,
                        "has_upstream": True,
                    }
                    mock_files.return_value = [UncommittedFile("file.txt", "M", "Modified")]

                    updated_repo, log_entry = await async_update_repository_with_log(repo)

                    assert updated_repo.status == RepoStatus.SKIPPED
                    assert len(log_entry.uncommitted_files) == 1

    @pytest.mark.asyncio
    async def test_successful_update(self, tmp_path: Path) -> None:
        """Test successful repository update."""
        repo = RepoInfo(path=tmp_path, name="test-repo")

        with patch("gittyup.git_operations.async_get_current_branch") as mock_branch:
            with patch("gittyup.git_operations.async_get_repo_status") as mock_status:
                with patch("gittyup.git_operations.async_pull_repository_detailed") as mock_pull:
                    mock_branch.return_value = "main"
                    mock_status.return_value = {
                        "has_remote": True,
                        "is_clean": True,
                        "is_detached": False,
                        "has_upstream": True,
                    }
                    mock_pull.return_value = PullResult(
                        success=True,
                        already_up_to_date=False,
                        commits_count=2,
                        files_changed=3,
                        insertions=50,
                        deletions=10,
                    )

                    updated_repo, log_entry = await async_update_repository_with_log(repo)

                    assert updated_repo.status == RepoStatus.UPDATED
                    assert log_entry.status == "updated"
                    assert log_entry.commits_pulled == 2
                    assert log_entry.files_changed == 3

    @pytest.mark.asyncio
    async def test_already_up_to_date(self, tmp_path: Path) -> None:
        """Test repo that is already up to date."""
        repo = RepoInfo(path=tmp_path, name="test-repo")

        with patch("gittyup.git_operations.async_get_current_branch") as mock_branch:
            with patch("gittyup.git_operations.async_get_repo_status") as mock_status:
                with patch("gittyup.git_operations.async_pull_repository_detailed") as mock_pull:
                    mock_branch.return_value = "main"
                    mock_status.return_value = {
                        "has_remote": True,
                        "is_clean": True,
                        "is_detached": False,
                        "has_upstream": True,
                    }
                    mock_pull.return_value = PullResult(success=True, already_up_to_date=True)

                    updated_repo, log_entry = await async_update_repository_with_log(repo)

                    assert updated_repo.status == RepoStatus.UP_TO_DATE
                    assert log_entry.status == "up_to_date"

    @pytest.mark.asyncio
    async def test_update_error(self, tmp_path: Path) -> None:
        """Test handling of update errors."""
        repo = RepoInfo(path=tmp_path, name="test-repo")

        with patch("gittyup.git_operations.async_get_current_branch") as mock_branch:
            with patch("gittyup.git_operations.async_get_repo_status") as mock_status:
                with patch("gittyup.git_operations.async_pull_repository_detailed") as mock_pull:
                    mock_branch.return_value = "main"
                    mock_status.return_value = {
                        "has_remote": True,
                        "is_clean": True,
                        "is_detached": False,
                        "has_upstream": True,
                    }
                    mock_pull.return_value = PullResult(
                        success=False, already_up_to_date=False, error_message="Network error"
                    )

                    updated_repo, log_entry = await async_update_repository_with_log(repo)

                    assert updated_repo.status == RepoStatus.ERROR
                    assert log_entry.status == "error"
                    assert log_entry.error == "Network error"
