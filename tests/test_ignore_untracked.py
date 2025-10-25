"""Tests for --ignore-untracked feature (GitHub issue #2)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gittyup.git_operations import check_for_pull_conflicts, has_only_untracked_files
from gittyup.models import UncommittedFile


class TestHasOnlyUntrackedFiles:
    """Tests for has_only_untracked_files function."""

    def test_empty_list(self) -> None:
        """Test with no uncommitted files."""
        assert has_only_untracked_files([]) is True

    def test_only_untracked_files(self) -> None:
        """Test with only untracked files."""
        files = [
            UncommittedFile("file1.txt", "??", "Untracked"),
            UncommittedFile("file2.log", "??", "Untracked"),
            UncommittedFile("debug.out", "?", "Untracked"),
        ]
        assert has_only_untracked_files(files) is True

    def test_modified_files(self) -> None:
        """Test with modified files."""
        files = [
            UncommittedFile("file1.txt", "M ", "Modified"),
            UncommittedFile("file2.py", "??", "Untracked"),
        ]
        assert has_only_untracked_files(files) is False

    def test_staged_files(self) -> None:
        """Test with staged files."""
        files = [
            UncommittedFile("file1.txt", "A ", "Added"),
            UncommittedFile("file2.py", "??", "Untracked"),
        ]
        assert has_only_untracked_files(files) is False

    def test_mixed_files(self) -> None:
        """Test with mix of modified and untracked."""
        files = [
            UncommittedFile("file1.txt", " M", "Modified (unstaged)"),
            UncommittedFile("file2.log", "??", "Untracked"),
            UncommittedFile("file3.txt", "M ", "Modified"),
        ]
        assert has_only_untracked_files(files) is False


class TestCheckForPullConflicts:
    """Tests for check_for_pull_conflicts function."""

    @patch("gittyup.git_operations._run_git_command")
    @patch("gittyup.git_operations.get_current_branch")
    @patch("gittyup.git_operations.get_uncommitted_files")
    def test_no_conflicts(
        self,
        mock_get_uncommitted: MagicMock,
        mock_get_branch: MagicMock,
        mock_run_git: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test when there are no conflicts."""
        mock_get_branch.return_value = "main"
        mock_get_uncommitted.return_value = [
            UncommittedFile("untracked.txt", "??", "Untracked"),
        ]

        def git_command_side_effect(*args, **kwargs):
            cmd = args[0]
            result = MagicMock()
            result.returncode = 0

            if cmd[1] == "fetch":
                result.stdout = ""
                result.stderr = ""
            elif cmd[1] == "rev-parse":
                result.stdout = "origin/main\n"
            elif cmd[1] == "diff":
                # Files that would be changed by pull (different from untracked)
                result.stdout = "M\tdifferent_file.py\n"

            return result

        mock_run_git.side_effect = git_command_side_effect

        is_safe, error_msg = check_for_pull_conflicts(tmp_path)

        assert is_safe is True
        assert error_msg is None

    @patch("gittyup.git_operations._run_git_command")
    @patch("gittyup.git_operations.get_current_branch")
    @patch("gittyup.git_operations.get_uncommitted_files")
    def test_with_conflicts(
        self,
        mock_get_uncommitted: MagicMock,
        mock_get_branch: MagicMock,
        mock_run_git: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test when untracked files would be overwritten."""
        mock_get_branch.return_value = "main"
        mock_get_uncommitted.return_value = [
            UncommittedFile("conflicting.txt", "??", "Untracked"),
            UncommittedFile("safe.log", "??", "Untracked"),
        ]

        def git_command_side_effect(*args, **kwargs):
            cmd = args[0]
            result = MagicMock()
            result.returncode = 0

            if cmd[1] == "fetch":
                result.stdout = ""
                result.stderr = ""
            elif cmd[1] == "rev-parse":
                result.stdout = "origin/main\n"
            elif cmd[1] == "diff":
                # Pull would change a file that exists as untracked locally
                result.stdout = "M\tconflicting.txt\nA\tother_file.py\n"

            return result

        mock_run_git.side_effect = git_command_side_effect

        is_safe, error_msg = check_for_pull_conflicts(tmp_path)

        assert is_safe is False
        assert error_msg is not None
        assert "conflicting.txt" in error_msg

    @patch("gittyup.git_operations._run_git_command")
    @patch("gittyup.git_operations.get_current_branch")
    def test_no_upstream_branch(
        self,
        mock_get_branch: MagicMock,
        mock_run_git: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test when there's no upstream branch."""
        mock_get_branch.return_value = "main"

        def git_command_side_effect(*args, **kwargs):
            cmd = args[0]
            result = MagicMock()

            if cmd[1] == "fetch":
                result.returncode = 0
                result.stdout = ""
                result.stderr = ""
            elif cmd[1] == "rev-parse":
                # No upstream configured
                result.returncode = 1
                result.stderr = "fatal: no upstream configured"

            return result

        mock_run_git.side_effect = git_command_side_effect

        is_safe, error_msg = check_for_pull_conflicts(tmp_path)

        assert is_safe is False
        assert error_msg is not None
        assert "upstream" in error_msg.lower()

    @patch("gittyup.git_operations._run_git_command")
    @patch("gittyup.git_operations.get_current_branch")
    @patch("gittyup.git_operations.get_uncommitted_files")
    def test_no_changes_to_pull(
        self,
        mock_get_uncommitted: MagicMock,
        mock_get_branch: MagicMock,
        mock_run_git: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test when there are no changes to pull (already up to date)."""
        mock_get_branch.return_value = "main"
        mock_get_uncommitted.return_value = [
            UncommittedFile("untracked.txt", "??", "Untracked"),
        ]

        def git_command_side_effect(*args, **kwargs):
            cmd = args[0]
            result = MagicMock()
            result.returncode = 0

            if cmd[1] == "fetch":
                result.stdout = ""
                result.stderr = ""
            elif cmd[1] == "rev-parse":
                result.stdout = "origin/main\n"
            elif cmd[1] == "diff":
                # No differences - already up to date
                result.stdout = ""

            return result

        mock_run_git.side_effect = git_command_side_effect

        is_safe, error_msg = check_for_pull_conflicts(tmp_path)

        assert is_safe is True
        assert error_msg is None

    @patch("gittyup.git_operations._run_git_command")
    @patch("gittyup.git_operations.get_current_branch")
    def test_fetch_fails(
        self,
        mock_get_branch: MagicMock,
        mock_run_git: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test when git fetch fails."""
        mock_get_branch.return_value = "main"

        def git_command_side_effect(*args, **kwargs):
            cmd = args[0]
            result = MagicMock()

            if cmd[1] == "fetch":
                result.returncode = 1
                result.stderr = "fatal: unable to access remote"
            return result

        mock_run_git.side_effect = git_command_side_effect

        is_safe, error_msg = check_for_pull_conflicts(tmp_path)

        assert is_safe is False
        assert error_msg is not None
        assert "fetch" in error_msg.lower()


class TestIgnoreUntrackedIntegration:
    """Integration tests for --ignore-untracked functionality."""

    @pytest.mark.asyncio
    @patch("gittyup.git_operations.get_current_branch")
    @patch("gittyup.git_operations.async_get_repo_status")
    @patch("gittyup.git_operations.async_get_uncommitted_files")
    @patch("gittyup.git_operations.async_check_for_pull_conflicts")
    @patch("gittyup.git_operations.async_pull_repository_detailed")
    async def test_ignore_untracked_with_safe_pull(
        self,
        mock_pull: MagicMock,
        mock_check_conflicts: MagicMock,
        mock_uncommitted: MagicMock,
        mock_status: MagicMock,
        mock_branch: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that pull proceeds when only untracked files and no conflicts."""
        from gittyup.git_operations import PullResult, async_update_repository_with_log
        from gittyup.models import RepoInfo

        repo = RepoInfo(path=tmp_path, name="test-repo")

        mock_branch.return_value = "main"
        mock_status.return_value = {
            "has_remote": True,
            "is_clean": False,  # Not clean because of untracked files
            "is_detached": False,
            "has_upstream": True,
        }
        mock_uncommitted.return_value = [
            UncommittedFile("untracked.txt", "??", "Untracked"),
        ]
        mock_check_conflicts.return_value = (True, None)  # Safe to pull
        mock_pull.return_value = PullResult(
            success=True,
            already_up_to_date=False,
            full_output="Pull successful",
        )

        repo_info, log_entry = await async_update_repository_with_log(
            repo, skip_dirty=True, ignore_untracked=True
        )

        # Should have pulled successfully
        assert repo_info.status.value == "updated"
        assert log_entry.status == "updated"
        mock_pull.assert_called_once()

    @pytest.mark.asyncio
    @patch("gittyup.git_operations.get_current_branch")
    @patch("gittyup.git_operations.async_get_repo_status")
    @patch("gittyup.git_operations.async_get_uncommitted_files")
    @patch("gittyup.git_operations.async_check_for_pull_conflicts")
    async def test_ignore_untracked_with_conflicts(
        self,
        mock_check_conflicts: MagicMock,
        mock_uncommitted: MagicMock,
        mock_status: MagicMock,
        mock_branch: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that pull is skipped when untracked files would conflict."""
        from gittyup.git_operations import async_update_repository_with_log
        from gittyup.models import RepoInfo

        repo = RepoInfo(path=tmp_path, name="test-repo")

        mock_branch.return_value = "main"
        mock_status.return_value = {
            "has_remote": True,
            "is_clean": False,
            "is_detached": False,
            "has_upstream": True,
        }
        mock_uncommitted.return_value = [
            UncommittedFile("conflicting.txt", "??", "Untracked"),
        ]
        mock_check_conflicts.return_value = (False, "Untracked files would be overwritten")

        repo_info, log_entry = await async_update_repository_with_log(
            repo, skip_dirty=True, ignore_untracked=True
        )

        # Should be skipped due to conflict
        assert repo_info.status.value == "skipped"
        assert log_entry.status == "skipped"
        assert repo_info.message is not None
        assert "overwritten" in repo_info.message.lower()

    @pytest.mark.asyncio
    @patch("gittyup.git_operations.get_current_branch")
    @patch("gittyup.git_operations.async_get_repo_status")
    @patch("gittyup.git_operations.async_get_uncommitted_files")
    async def test_ignore_untracked_false_with_untracked(
        self,
        mock_uncommitted: MagicMock,
        mock_status: MagicMock,
        mock_branch: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that repo is skipped when ignore_untracked=False."""
        from gittyup.git_operations import async_update_repository_with_log
        from gittyup.models import RepoInfo

        repo = RepoInfo(path=tmp_path, name="test-repo")

        mock_branch.return_value = "main"
        mock_status.return_value = {
            "has_remote": True,
            "is_clean": False,
            "is_detached": False,
            "has_upstream": True,
        }
        mock_uncommitted.return_value = [
            UncommittedFile("untracked.txt", "??", "Untracked"),
        ]

        repo_info, log_entry = await async_update_repository_with_log(
            repo, skip_dirty=True, ignore_untracked=False
        )

        # Should be skipped (default behavior)
        assert repo_info.status.value == "skipped"
        assert log_entry.status == "skipped"
        assert repo_info.message is not None
        assert "uncommitted changes" in repo_info.message.lower()

    @pytest.mark.asyncio
    @patch("gittyup.git_operations.get_current_branch")
    @patch("gittyup.git_operations.async_get_repo_status")
    @patch("gittyup.git_operations.async_get_uncommitted_files")
    async def test_ignore_untracked_with_modified_files(
        self,
        mock_uncommitted: MagicMock,
        mock_status: MagicMock,
        mock_branch: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that repo is skipped when there are modified (not just untracked) files."""
        from gittyup.git_operations import async_update_repository_with_log
        from gittyup.models import RepoInfo

        repo = RepoInfo(path=tmp_path, name="test-repo")

        mock_branch.return_value = "main"
        mock_status.return_value = {
            "has_remote": True,
            "is_clean": False,
            "is_detached": False,
            "has_upstream": True,
        }
        mock_uncommitted.return_value = [
            UncommittedFile("modified.txt", " M", "Modified (unstaged)"),
            UncommittedFile("untracked.txt", "??", "Untracked"),
        ]

        repo_info, log_entry = await async_update_repository_with_log(
            repo, skip_dirty=True, ignore_untracked=True
        )

        # Should be skipped because there are non-untracked changes
        assert repo_info.status.value == "skipped"
        assert log_entry.status == "skipped"
        assert repo_info.message is not None
        assert "uncommitted changes" in repo_info.message.lower()

