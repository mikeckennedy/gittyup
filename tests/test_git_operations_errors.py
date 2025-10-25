"""Tests for error handling in git operations."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gittyup.git_operations import (
    GitCommandError,
    GitTimeoutError,
    async_get_uncommitted_files,
    async_pull_repository_detailed,
    async_update_repository_with_log,
    pull_repository_detailed,
    update_repository_with_log,
)
from gittyup.models import RepoInfo, RepoStatus


class TestSyncUpdateRepositoryWithLogErrors:
    """Tests for error handling in sync update_repository_with_log."""

    @patch("gittyup.git_operations.get_repo_status")
    @patch("gittyup.git_operations.get_current_branch")
    def test_no_remote_configured(
        self,
        mock_branch: MagicMock,
        mock_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test when repository has no remote configured."""
        mock_branch.return_value = "main"
        mock_status.return_value = {
            "has_remote": False,
            "is_clean": True,
            "is_detached": False,
            "has_upstream": False,
        }

        repo = RepoInfo(path=tmp_path, name="test-repo")
        repo_info, log_entry = update_repository_with_log(repo)

        assert repo_info.status == RepoStatus.SKIPPED
        assert log_entry.status == "skipped"
        assert log_entry.skip_reason == "No remote configured"

    @patch("gittyup.git_operations.get_repo_status")
    @patch("gittyup.git_operations.get_current_branch")
    def test_detached_head_state(
        self,
        mock_branch: MagicMock,
        mock_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test when repository is in detached HEAD state."""
        mock_branch.return_value = None  # Detached HEAD
        mock_status.return_value = {
            "has_remote": True,
            "is_clean": True,
            "is_detached": True,
            "has_upstream": False,
        }

        repo = RepoInfo(path=tmp_path, name="test-repo")
        repo_info, log_entry = update_repository_with_log(repo)

        assert repo_info.status == RepoStatus.SKIPPED
        assert log_entry.status == "skipped"
        assert log_entry.skip_reason == "Detached HEAD state"

    @patch("gittyup.git_operations.get_repo_status")
    @patch("gittyup.git_operations.get_current_branch")
    def test_no_upstream_branch(
        self,
        mock_branch: MagicMock,
        mock_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test when repository has no upstream branch configured."""
        mock_branch.return_value = "main"
        mock_status.return_value = {
            "has_remote": True,
            "is_clean": True,
            "is_detached": False,
            "has_upstream": False,
        }

        repo = RepoInfo(path=tmp_path, name="test-repo")
        repo_info, log_entry = update_repository_with_log(repo)

        assert repo_info.status == RepoStatus.SKIPPED
        assert log_entry.status == "skipped"
        assert log_entry.skip_reason == "No upstream branch configured"

    @patch("gittyup.git_operations.get_repo_status")
    @patch("gittyup.git_operations.get_current_branch")
    @patch("gittyup.git_operations.get_uncommitted_files")
    def test_uncommitted_changes_skipped(
        self,
        mock_uncommitted: MagicMock,
        mock_branch: MagicMock,
        mock_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test when repository has uncommitted changes."""
        from gittyup.models import UncommittedFile

        mock_branch.return_value = "main"
        mock_status.return_value = {
            "has_remote": True,
            "is_clean": False,
            "is_detached": False,
            "has_upstream": True,
        }
        mock_uncommitted.return_value = [
            UncommittedFile("modified.py", " M", "Modified (unstaged)"),
        ]

        repo = RepoInfo(path=tmp_path, name="test-repo")
        repo_info, log_entry = update_repository_with_log(repo, skip_dirty=True)

        assert repo_info.status == RepoStatus.SKIPPED
        assert log_entry.status == "skipped"
        assert log_entry.skip_reason == "Repository has uncommitted changes"
        assert len(log_entry.uncommitted_files) > 0

    @patch("gittyup.git_operations.get_repo_status")
    @patch("gittyup.git_operations.get_current_branch")
    @patch("gittyup.git_operations.pull_repository_detailed")
    def test_git_timeout_error(
        self,
        mock_pull: MagicMock,
        mock_branch: MagicMock,
        mock_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test when git operation times out."""
        mock_branch.return_value = "main"
        mock_status.return_value = {
            "has_remote": True,
            "is_clean": True,
            "is_detached": False,
            "has_upstream": True,
        }
        mock_pull.side_effect = GitTimeoutError("Git pull timed out after 60 seconds")

        repo = RepoInfo(path=tmp_path, name="test-repo")
        repo_info, log_entry = update_repository_with_log(repo)

        assert repo_info.status == RepoStatus.ERROR
        assert log_entry.status == "error"
        assert "timed out" in log_entry.error.lower()

    @patch("gittyup.git_operations.get_repo_status")
    @patch("gittyup.git_operations.get_current_branch")
    @patch("gittyup.git_operations.pull_repository_detailed")
    def test_git_command_error(
        self,
        mock_pull: MagicMock,
        mock_branch: MagicMock,
        mock_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test when git command fails."""
        mock_branch.return_value = "main"
        mock_status.return_value = {
            "has_remote": True,
            "is_clean": True,
            "is_detached": False,
            "has_upstream": True,
        }
        mock_pull.side_effect = GitCommandError("Failed to execute git command")

        repo = RepoInfo(path=tmp_path, name="test-repo")
        repo_info, log_entry = update_repository_with_log(repo)

        assert repo_info.status == RepoStatus.ERROR
        assert log_entry.status == "error"
        assert "failed" in log_entry.error.lower()

    @patch("gittyup.git_operations.get_repo_status")
    @patch("gittyup.git_operations.get_current_branch")
    @patch("gittyup.git_operations.pull_repository_detailed")
    def test_unexpected_exception(
        self,
        mock_pull: MagicMock,
        mock_branch: MagicMock,
        mock_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test when unexpected exception occurs."""
        mock_branch.return_value = "main"
        mock_status.return_value = {
            "has_remote": True,
            "is_clean": True,
            "is_detached": False,
            "has_upstream": True,
        }
        mock_pull.side_effect = RuntimeError("Unexpected error")

        repo = RepoInfo(path=tmp_path, name="test-repo")
        repo_info, log_entry = update_repository_with_log(repo)

        assert repo_info.status == RepoStatus.ERROR
        assert log_entry.status == "error"
        assert "unexpected error" in log_entry.error.lower()


class TestAsyncUpdateRepositoryWithLogErrors:
    """Tests for error handling in async update_repository_with_log."""

    @pytest.mark.asyncio
    @patch("gittyup.git_operations.async_get_repo_status")
    @patch("gittyup.git_operations.async_get_current_branch")
    async def test_async_no_remote(
        self,
        mock_branch: MagicMock,
        mock_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test async version when repository has no remote configured."""
        mock_branch.return_value = "main"
        mock_status.return_value = {
            "has_remote": False,
            "is_clean": True,
            "is_detached": False,
            "has_upstream": False,
        }

        repo = RepoInfo(path=tmp_path, name="test-repo")
        repo_info, log_entry = await async_update_repository_with_log(repo)

        assert repo_info.status == RepoStatus.SKIPPED
        assert log_entry.status == "skipped"
        assert log_entry.skip_reason == "No remote configured"

    @pytest.mark.asyncio
    @patch("gittyup.git_operations.async_get_repo_status")
    @patch("gittyup.git_operations.async_get_current_branch")
    async def test_async_detached_head(
        self,
        mock_branch: MagicMock,
        mock_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test async version when repository is in detached HEAD state."""
        mock_branch.return_value = None  # Detached HEAD
        mock_status.return_value = {
            "has_remote": True,
            "is_clean": True,
            "is_detached": True,
            "has_upstream": False,
        }

        repo = RepoInfo(path=tmp_path, name="test-repo")
        repo_info, log_entry = await async_update_repository_with_log(repo)

        assert repo_info.status == RepoStatus.SKIPPED
        assert log_entry.status == "skipped"
        assert log_entry.skip_reason == "Detached HEAD state"

    @pytest.mark.asyncio
    @patch("gittyup.git_operations.async_get_repo_status")
    @patch("gittyup.git_operations.async_get_current_branch")
    async def test_async_no_upstream(
        self,
        mock_branch: MagicMock,
        mock_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test async version when repository has no upstream branch."""
        mock_branch.return_value = "main"
        mock_status.return_value = {
            "has_remote": True,
            "is_clean": True,
            "is_detached": False,
            "has_upstream": False,
        }

        repo = RepoInfo(path=tmp_path, name="test-repo")
        repo_info, log_entry = await async_update_repository_with_log(repo)

        assert repo_info.status == RepoStatus.SKIPPED
        assert log_entry.status == "skipped"
        assert log_entry.skip_reason == "No upstream branch configured"

    @pytest.mark.asyncio
    @patch("gittyup.git_operations.async_get_repo_status")
    @patch("gittyup.git_operations.async_get_current_branch")
    @patch("gittyup.git_operations.async_pull_repository_detailed")
    async def test_async_git_timeout_error(
        self,
        mock_pull: MagicMock,
        mock_branch: MagicMock,
        mock_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test async version when git operation times out."""
        mock_branch.return_value = "main"
        mock_status.return_value = {
            "has_remote": True,
            "is_clean": True,
            "is_detached": False,
            "has_upstream": True,
        }
        mock_pull.side_effect = GitTimeoutError("Git pull timed out after 60 seconds")

        repo = RepoInfo(path=tmp_path, name="test-repo")
        repo_info, log_entry = await async_update_repository_with_log(repo)

        assert repo_info.status == RepoStatus.ERROR
        assert log_entry.status == "error"
        assert "timed out" in log_entry.error.lower()

    @pytest.mark.asyncio
    @patch("gittyup.git_operations.async_get_repo_status")
    @patch("gittyup.git_operations.async_get_current_branch")
    @patch("gittyup.git_operations.async_pull_repository_detailed")
    async def test_async_git_command_error(
        self,
        mock_pull: MagicMock,
        mock_branch: MagicMock,
        mock_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test async version when git command fails."""
        mock_branch.return_value = "main"
        mock_status.return_value = {
            "has_remote": True,
            "is_clean": True,
            "is_detached": False,
            "has_upstream": True,
        }
        mock_pull.side_effect = GitCommandError("Failed to execute git command")

        repo = RepoInfo(path=tmp_path, name="test-repo")
        repo_info, log_entry = await async_update_repository_with_log(repo)

        assert repo_info.status == RepoStatus.ERROR
        assert log_entry.status == "error"
        assert "failed" in log_entry.error.lower()

    @pytest.mark.asyncio
    @patch("gittyup.git_operations.async_get_repo_status")
    @patch("gittyup.git_operations.async_get_current_branch")
    @patch("gittyup.git_operations.async_pull_repository_detailed")
    async def test_async_unexpected_exception(
        self,
        mock_pull: MagicMock,
        mock_branch: MagicMock,
        mock_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test async version when unexpected exception occurs."""
        mock_branch.return_value = "main"
        mock_status.return_value = {
            "has_remote": True,
            "is_clean": True,
            "is_detached": False,
            "has_upstream": True,
        }
        mock_pull.side_effect = RuntimeError("Unexpected error")

        repo = RepoInfo(path=tmp_path, name="test-repo")
        repo_info, log_entry = await async_update_repository_with_log(repo)

        assert repo_info.status == RepoStatus.ERROR
        assert log_entry.status == "error"
        assert "unexpected error" in log_entry.error.lower()


class TestPullRepositoryDetailedErrors:
    """Tests for error handling in pull_repository_detailed."""

    @patch("gittyup.git_operations._run_git_command")
    def test_merge_conflict_error(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test when pull results in merge conflict."""
        result = MagicMock()
        result.returncode = 1
        result.stdout = ""
        result.stderr = "error: merge conflict in file.txt"
        mock_run.return_value = result

        pull_result = pull_repository_detailed(tmp_path)

        assert pull_result.success is False
        assert "merge conflict" in pull_result.error_message.lower()

    @patch("gittyup.git_operations._run_git_command")
    def test_network_error(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test when pull fails due to network error."""
        result = MagicMock()
        result.returncode = 1
        result.stdout = ""
        result.stderr = "fatal: could not resolve host: github.com"
        mock_run.return_value = result

        pull_result = pull_repository_detailed(tmp_path)

        assert pull_result.success is False
        assert "network" in pull_result.error_message.lower()

    @patch("gittyup.git_operations._run_git_command")
    def test_authentication_error(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test when pull fails due to authentication error."""
        result = MagicMock()
        result.returncode = 1
        result.stdout = ""
        result.stderr = "fatal: Authentication failed"
        mock_run.return_value = result

        pull_result = pull_repository_detailed(tmp_path)

        assert pull_result.success is False
        assert "authentication" in pull_result.error_message.lower()

    @patch("gittyup.git_operations._run_git_command")
    def test_no_tracking_information(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test when branch has no tracking information."""
        result = MagicMock()
        result.returncode = 1
        result.stdout = "There is no tracking information for the current branch"
        result.stderr = ""
        mock_run.return_value = result

        pull_result = pull_repository_detailed(tmp_path)

        assert pull_result.success is False
        assert "upstream" in pull_result.error_message.lower()


class TestAsyncPullRepositoryDetailedErrors:
    """Tests for error handling in async_pull_repository_detailed."""

    @pytest.mark.asyncio
    @patch("gittyup.git_operations._async_run_git_command")
    async def test_async_merge_conflict(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test async version when pull results in merge conflict."""

        async def git_side_effect(*args, **kwargs):
            return 1, "", "error: merge conflict in file.txt"

        mock_run.side_effect = git_side_effect

        pull_result = await async_pull_repository_detailed(tmp_path)

        assert pull_result.success is False
        assert "merge conflict" in pull_result.error_message.lower()

    @pytest.mark.asyncio
    @patch("gittyup.git_operations._async_run_git_command")
    async def test_async_network_error(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test async version when pull fails due to network error."""

        async def git_side_effect(*args, **kwargs):
            return 1, "", "fatal: could not resolve host: github.com"

        mock_run.side_effect = git_side_effect

        pull_result = await async_pull_repository_detailed(tmp_path)

        assert pull_result.success is False
        assert "network" in pull_result.error_message.lower()

    @pytest.mark.asyncio
    @patch("gittyup.git_operations._async_run_git_command")
    async def test_async_authentication_error(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test async version when pull fails due to authentication error."""

        async def git_side_effect(*args, **kwargs):
            return 1, "", "fatal: Authentication failed"

        mock_run.side_effect = git_side_effect

        pull_result = await async_pull_repository_detailed(tmp_path)

        assert pull_result.success is False
        assert "authentication" in pull_result.error_message.lower()

    @pytest.mark.asyncio
    @patch("gittyup.git_operations._async_run_git_command")
    async def test_async_no_tracking_information(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test async version when branch has no tracking information."""

        async def git_side_effect(*args, **kwargs):
            return 1, "There is no tracking information for the current branch", ""

        mock_run.side_effect = git_side_effect

        pull_result = await async_pull_repository_detailed(tmp_path)

        assert pull_result.success is False
        assert "upstream" in pull_result.error_message.lower()

    @pytest.mark.asyncio
    @patch("gittyup.git_operations._async_run_git_command")
    async def test_async_timeout_error(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test async version when operation times out."""

        async def git_side_effect(*args, **kwargs):
            raise TimeoutError("Operation timed out")

        mock_run.side_effect = git_side_effect

        with pytest.raises(GitTimeoutError):
            await async_pull_repository_detailed(tmp_path)

    @pytest.mark.asyncio
    @patch("gittyup.git_operations._async_run_git_command")
    async def test_async_generic_error_with_long_message(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test async version with long error message (tests truncation)."""

        async def git_side_effect(*args, **kwargs):
            long_error = "a" * 150  # Create a 150 character error message
            return 1, "", long_error

        mock_run.side_effect = git_side_effect

        pull_result = await async_pull_repository_detailed(tmp_path)

        assert pull_result.success is False
        # Should be truncated to 100 chars + "..."
        assert len(pull_result.error_message) == 103


class TestAsyncGetUncommittedFilesEdgeCases:
    """Tests for edge cases in async_get_uncommitted_files."""

    @pytest.mark.asyncio
    @patch("gittyup.git_operations._async_run_git_command")
    async def test_async_command_fails(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test when git status command fails."""

        async def git_side_effect(*args, **kwargs):
            return 1, "", "fatal: not a git repository"

        mock_run.side_effect = git_side_effect

        uncommitted_files = await async_get_uncommitted_files(tmp_path)

        # Should return empty list on error
        assert uncommitted_files == []

    @pytest.mark.asyncio
    @patch("gittyup.git_operations._async_run_git_command")
    async def test_async_timeout(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test when operation times out."""

        async def git_side_effect(*args, **kwargs):
            raise TimeoutError("Operation timed out")

        mock_run.side_effect = git_side_effect

        uncommitted_files = await async_get_uncommitted_files(tmp_path)

        # Should return empty list on timeout
        assert uncommitted_files == []

    @pytest.mark.asyncio
    @patch("gittyup.git_operations._async_run_git_command")
    async def test_async_empty_lines(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test parsing with empty lines in output."""

        async def git_side_effect(*args, **kwargs):
            return 0, "M  file.txt\n\n?? other.txt\n", ""

        mock_run.side_effect = git_side_effect

        uncommitted_files = await async_get_uncommitted_files(tmp_path)

        # Should skip empty lines
        assert len(uncommitted_files) == 2

    @pytest.mark.asyncio
    @patch("gittyup.git_operations._async_run_git_command")
    async def test_async_malformed_lines(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test parsing with malformed lines."""

        async def git_side_effect(*args, **kwargs):
            # Include a line that's too short (less than 3 chars)
            return 0, "M  file.txt\nAB\n?? other.txt\n", ""

        mock_run.side_effect = git_side_effect

        uncommitted_files = await async_get_uncommitted_files(tmp_path)

        # Should skip malformed lines
        assert len(uncommitted_files) == 2
