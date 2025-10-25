"""Tests for git operations."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gittyup.git_operations import (
    GitCommandError,
    GitTimeoutError,
    PullResult,
    _get_commit_details,
    _get_file_changes,
    _parse_git_pull_output,
    check_for_pull_conflicts,
    check_git_installed,
    get_current_branch,
    get_git_version,
    get_repo_status,
    get_uncommitted_files,
    has_only_untracked_files,
    pull_repository,
    pull_repository_detailed,
    update_repository,
    update_repository_with_log,
)
from gittyup.models import CommitInfo, FileChange, RepoInfo, RepoStatus, UncommittedFile


class TestCheckGitInstalled:
    """Tests for git installation check."""

    def test_git_installed(self) -> None:
        """Test detection when git is installed."""
        # This test runs against the actual system
        # If git is not installed, the test will fail
        result = check_git_installed()
        assert isinstance(result, bool)
        # On most development machines, git should be installed
        assert result is True

    @patch("subprocess.run")
    def test_git_not_found(self, mock_run: MagicMock) -> None:
        """Test when git command is not found."""
        mock_run.side_effect = FileNotFoundError()
        assert check_git_installed() is False

    @patch("subprocess.run")
    def test_git_command_fails(self, mock_run: MagicMock) -> None:
        """Test when git command fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        assert check_git_installed() is False


class TestGetRepoStatus:
    """Tests for repository status checking."""

    @patch("subprocess.run")
    def test_clean_repo_with_remote(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test status of clean repo with remote and upstream."""

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            result = MagicMock()
            result.returncode = 0

            if cmd[1] == "remote":
                result.stdout = "origin\n"
            elif cmd[1] == "status":
                result.stdout = ""  # Clean repo
            elif cmd[1] == "symbolic-ref":
                result.stdout = "refs/heads/main\n"  # Not detached
            elif cmd[1] == "rev-parse":
                result.stdout = "origin/main\n"  # Has upstream

            return result

        mock_run.side_effect = run_side_effect

        status = get_repo_status(tmp_path)

        assert status["has_remote"] is True
        assert status["is_clean"] is True
        assert status["is_detached"] is False
        assert status["has_upstream"] is True

    @patch("subprocess.run")
    def test_dirty_repo(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test status of dirty repo with uncommitted changes."""

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            result = MagicMock()
            result.returncode = 0

            if cmd[1] == "remote":
                result.stdout = "origin\n"
            elif cmd[1] == "status":
                result.stdout = " M modified_file.py\n"  # Dirty repo
            elif cmd[1] == "symbolic-ref":
                result.stdout = "refs/heads/main\n"
            elif cmd[1] == "rev-parse":
                result.stdout = "origin/main\n"

            return result

        mock_run.side_effect = run_side_effect

        status = get_repo_status(tmp_path)

        assert status["is_clean"] is False

    @patch("subprocess.run")
    def test_no_remote(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test status of repo with no remote."""

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            result = MagicMock()
            result.returncode = 0

            if cmd[1] == "remote":
                result.stdout = ""  # No remotes
            elif cmd[1] == "status":
                result.stdout = ""
            elif cmd[1] == "symbolic-ref":
                result.stdout = "refs/heads/main\n"
            elif cmd[1] == "rev-parse":
                result.returncode = 1  # No upstream

            return result

        mock_run.side_effect = run_side_effect

        status = get_repo_status(tmp_path)

        assert status["has_remote"] is False

    @patch("subprocess.run")
    def test_detached_head(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test status of repo with detached HEAD."""

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            result = MagicMock()

            if cmd[1] == "remote":
                result.returncode = 0
                result.stdout = "origin\n"
            elif cmd[1] == "status":
                result.returncode = 0
                result.stdout = ""
            elif cmd[1] == "symbolic-ref":
                result.returncode = 1  # Detached HEAD
                result.stdout = ""
            else:
                result.returncode = 0

            return result

        mock_run.side_effect = run_side_effect

        status = get_repo_status(tmp_path)

        assert status["is_detached"] is True

    @patch("subprocess.run")
    def test_no_upstream(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test status of repo with no upstream branch."""

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            result = MagicMock()

            if cmd[1] == "remote":
                result.returncode = 0
                result.stdout = "origin\n"
            elif cmd[1] == "status":
                result.returncode = 0
                result.stdout = ""
            elif cmd[1] == "symbolic-ref":
                result.returncode = 0
                result.stdout = "refs/heads/main\n"
            elif cmd[1] == "rev-parse":
                result.returncode = 1  # No upstream
                result.stdout = ""
            else:
                result.returncode = 0

            return result

        mock_run.side_effect = run_side_effect

        status = get_repo_status(tmp_path)

        assert status["has_upstream"] is False

    @patch("subprocess.run")
    def test_timeout(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test timeout during status check."""
        mock_run.side_effect = subprocess.TimeoutExpired("git", 10)

        with pytest.raises(GitTimeoutError):
            get_repo_status(tmp_path, timeout=10)

    @patch("subprocess.run")
    def test_command_error(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test command error during status check."""
        mock_run.side_effect = subprocess.SubprocessError("Command failed")

        with pytest.raises(GitCommandError):
            get_repo_status(tmp_path)


class TestPullRepository:
    """Tests for git pull operations."""

    @patch("subprocess.run")
    def test_already_up_to_date(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test pull when repo is already up-to-date."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Already up to date."
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        success, message = pull_repository(tmp_path)

        assert success is True
        assert "up-to-date" in message.lower()

    @patch("subprocess.run")
    def test_successful_pull(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test successful pull with changes."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Updating abc123..def456\nFast-forward\n file.py | 2 +-\n 1 file changed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        success, message = pull_repository(tmp_path)

        assert success is True
        assert "success" in message.lower() or "pulled" in message.lower()

    @patch("subprocess.run")
    def test_merge_conflict(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test pull with merge conflict."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "CONFLICT (content): Merge conflict in file.py"
        mock_run.return_value = mock_result

        success, message = pull_repository(tmp_path)

        assert success is False
        assert "conflict" in message.lower()

    @patch("subprocess.run")
    def test_network_error(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test pull with network error."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "fatal: could not resolve host: github.com"
        mock_run.return_value = mock_result

        success, message = pull_repository(tmp_path)

        assert success is False
        assert "network" in message.lower()

    @patch("subprocess.run")
    def test_authentication_error(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test pull with authentication error."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "fatal: Authentication failed"
        mock_run.return_value = mock_result

        success, message = pull_repository(tmp_path)

        assert success is False
        assert "authentication" in message.lower()

    @patch("subprocess.run")
    def test_no_tracking_branch(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test pull when branch has no tracking information."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "There is no tracking information for the current branch"
        mock_run.return_value = mock_result

        success, message = pull_repository(tmp_path)

        assert success is False
        assert "upstream" in message.lower() or "tracking" in message.lower()

    @patch("subprocess.run")
    def test_timeout(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test pull timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("git pull", 60)

        with pytest.raises(GitTimeoutError):
            pull_repository(tmp_path, timeout=60)

    @patch("subprocess.run")
    def test_generic_error(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test pull with generic error."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "fatal: some unknown error"
        mock_run.return_value = mock_result

        success, message = pull_repository(tmp_path)

        assert success is False
        assert "error" in message.lower()

    @patch("subprocess.run")
    def test_long_error_message_truncated(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test that long error messages are truncated."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "A" * 200  # Very long error message
        mock_run.return_value = mock_result

        success, message = pull_repository(tmp_path)

        assert success is False
        assert len(message) < 150  # Should be truncated
        assert "..." in message


class TestUpdateRepository:
    """Tests for the main update_repository function."""

    def test_no_remote(self, tmp_path: Path) -> None:
        """Test skipping repo with no remote."""
        repo = RepoInfo(path=tmp_path, name="test-repo")

        with patch("gittyup.git_operations.get_repo_status") as mock_status:
            mock_status.return_value = {
                "has_remote": False,
                "is_clean": True,
                "is_detached": False,
                "has_upstream": True,
            }

            result = update_repository(repo)

            assert result.status == RepoStatus.SKIPPED
            assert "remote" in result.message.lower()

    def test_detached_head(self, tmp_path: Path) -> None:
        """Test skipping repo with detached HEAD."""
        repo = RepoInfo(path=tmp_path, name="test-repo")

        with patch("gittyup.git_operations.get_repo_status") as mock_status:
            mock_status.return_value = {
                "has_remote": True,
                "is_clean": True,
                "is_detached": True,
                "has_upstream": False,
            }

            result = update_repository(repo)

            assert result.status == RepoStatus.SKIPPED
            assert "detached" in result.message.lower()

    def test_no_upstream(self, tmp_path: Path) -> None:
        """Test skipping repo with no upstream branch."""
        repo = RepoInfo(path=tmp_path, name="test-repo")

        with patch("gittyup.git_operations.get_repo_status") as mock_status:
            mock_status.return_value = {
                "has_remote": True,
                "is_clean": True,
                "is_detached": False,
                "has_upstream": False,
            }

            result = update_repository(repo)

            assert result.status == RepoStatus.SKIPPED
            assert "upstream" in result.message.lower()

    def test_uncommitted_changes_skip(self, tmp_path: Path) -> None:
        """Test skipping dirty repo when skip_dirty=True."""
        repo = RepoInfo(path=tmp_path, name="test-repo")

        with patch("gittyup.git_operations.get_repo_status") as mock_status:
            mock_status.return_value = {
                "has_remote": True,
                "is_clean": False,
                "is_detached": False,
                "has_upstream": True,
            }

            result = update_repository(repo, skip_dirty=True)

            assert result.status == RepoStatus.SKIPPED
            assert "uncommitted" in result.message.lower()

    def test_successful_update(self, tmp_path: Path) -> None:
        """Test successful repository update."""
        repo = RepoInfo(path=tmp_path, name="test-repo")

        with (
            patch("gittyup.git_operations.get_repo_status") as mock_status,
            patch("gittyup.git_operations.pull_repository") as mock_pull,
        ):
            mock_status.return_value = {
                "has_remote": True,
                "is_clean": True,
                "is_detached": False,
                "has_upstream": True,
            }
            # Note: The actual message includes color codes
            mock_pull.return_value = (True, "Pulled changes successfully")

            result = update_repository(repo)

            assert result.status == RepoStatus.UPDATED
            assert "success" in result.message.lower() or "pulled" in result.message.lower()

    def test_already_up_to_date(self, tmp_path: Path) -> None:
        """Test when repo is already up-to-date."""
        repo = RepoInfo(path=tmp_path, name="test-repo")

        with (
            patch("gittyup.git_operations.get_repo_status") as mock_status,
            patch("gittyup.git_operations.pull_repository") as mock_pull,
        ):
            mock_status.return_value = {
                "has_remote": True,
                "is_clean": True,
                "is_detached": False,
                "has_upstream": True,
            }
            mock_pull.return_value = (True, "Already up-to-date")

            result = update_repository(repo)

            assert result.status == RepoStatus.UP_TO_DATE
            assert "up-to-date" in result.message.lower()

    def test_pull_error(self, tmp_path: Path) -> None:
        """Test handling pull errors."""
        repo = RepoInfo(path=tmp_path, name="test-repo")

        with (
            patch("gittyup.git_operations.get_repo_status") as mock_status,
            patch("gittyup.git_operations.pull_repository") as mock_pull,
        ):
            mock_status.return_value = {
                "has_remote": True,
                "is_clean": True,
                "is_detached": False,
                "has_upstream": True,
            }
            mock_pull.return_value = (False, "Network error")

            result = update_repository(repo)

            assert result.status == RepoStatus.ERROR
            assert "network" in result.error.lower()

    def test_timeout_error(self, tmp_path: Path) -> None:
        """Test handling timeout errors."""
        repo = RepoInfo(path=tmp_path, name="test-repo")

        with (
            patch("gittyup.git_operations.get_repo_status") as mock_status,
            patch("gittyup.git_operations.pull_repository") as mock_pull,
        ):
            mock_status.return_value = {
                "has_remote": True,
                "is_clean": True,
                "is_detached": False,
                "has_upstream": True,
            }
            mock_pull.side_effect = GitTimeoutError("Timeout!")

            result = update_repository(repo)

            assert result.status == RepoStatus.ERROR
            assert "timeout" in result.error.lower()

    def test_command_error(self, tmp_path: Path) -> None:
        """Test handling command errors."""
        repo = RepoInfo(path=tmp_path, name="test-repo")

        with patch("gittyup.git_operations.get_repo_status") as mock_status:
            mock_status.side_effect = GitCommandError("Command failed")

            result = update_repository(repo)

            assert result.status == RepoStatus.ERROR
            assert result.error is not None

    def test_unexpected_error(self, tmp_path: Path) -> None:
        """Test handling unexpected errors."""
        repo = RepoInfo(path=tmp_path, name="test-repo")

        with patch("gittyup.git_operations.get_repo_status") as mock_status:
            mock_status.side_effect = Exception("Unexpected!")

            result = update_repository(repo)

            assert result.status == RepoStatus.ERROR
            assert "unexpected" in result.error.lower()


class TestParseGitPullOutput:
    """Tests for _parse_git_pull_output function."""

    def test_parse_fast_forward_pull(self) -> None:
        """Test parsing a successful fast-forward pull."""
        output = """Updating abc1234..def5678
Fast-forward
 src/main.py           | 23 ++++++++++++---
 tests/test_main.py    |  5 ++++
 2 files changed, 24 insertions(+), 4 deletions(-)"""

        result = _parse_git_pull_output(output)

        assert result["old_commit"] == "abc1234"
        assert result["new_commit"] == "def5678"
        assert result["files_changed"] == 2
        assert result["insertions"] == 24
        assert result["deletions"] == 4

    def test_parse_single_file_change(self) -> None:
        """Test parsing pull with single file change."""
        output = """Updating a1b2c3d..e4f5a6b
Fast-forward
 README.md | 10 ++++++++--
 1 file changed, 8 insertions(+), 2 deletions(-)"""

        result = _parse_git_pull_output(output)

        assert result["old_commit"] == "a1b2c3d"
        assert result["new_commit"] == "e4f5a6b"
        assert result["files_changed"] == 1
        assert result["insertions"] == 8
        assert result["deletions"] == 2

    def test_parse_only_insertions(self) -> None:
        """Test parsing pull with only insertions (new file)."""
        output = """Updating abc123..def456
Fast-forward
 new_file.py | 50 ++++++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 50 insertions(+)"""

        result = _parse_git_pull_output(output)

        assert result["files_changed"] == 1
        assert result["insertions"] == 50
        assert result["deletions"] == 0

    def test_parse_only_deletions(self) -> None:
        """Test parsing pull with only deletions (file removed)."""
        output = """Updating abc123..def456
Fast-forward
 old_file.py | 30 ------------------------------
 1 file changed, 30 deletions(-)"""

        result = _parse_git_pull_output(output)

        assert result["files_changed"] == 1
        assert result["insertions"] == 0
        assert result["deletions"] == 30

    def test_parse_no_commits(self) -> None:
        """Test parsing output without commit information."""
        output = "Already up to date."

        result = _parse_git_pull_output(output)

        assert result["old_commit"] is None
        assert result["new_commit"] is None
        assert result["files_changed"] == 0


class TestGetCommitDetails:
    """Tests for _get_commit_details function."""

    @patch("subprocess.run")
    def test_get_commit_details(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test getting commit details between two commits."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """a1b2c3d|John Doe|2025-10-15T10:23:00-07:00|Add new feature
b2c3d4e|Jane Smith|2025-10-15T09:15:00-07:00|Fix bug in validation
c3d4e5f|Bob Jones|2025-10-14T16:45:00-07:00|Update dependencies"""
        mock_run.return_value = mock_result

        commits = _get_commit_details(tmp_path, "old123", "new456")

        assert len(commits) == 3
        assert commits[0].commit_hash == "a1b2c3d"
        assert commits[0].author == "John Doe"
        assert commits[0].date == "2025-10-15T10:23:00-07:00"
        assert commits[0].message == "Add new feature"

    @patch("subprocess.run")
    def test_get_commit_details_empty(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test getting commit details when there are no commits."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        commits = _get_commit_details(tmp_path, "old123", "new456")

        assert len(commits) == 0

    @patch("subprocess.run")
    def test_get_commit_details_error(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test handling error when getting commit details."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        commits = _get_commit_details(tmp_path, "old123", "new456")

        assert len(commits) == 0

    @patch("subprocess.run")
    def test_get_commit_details_timeout(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test handling timeout when getting commit details."""
        mock_run.side_effect = subprocess.TimeoutExpired("git log", 10)

        commits = _get_commit_details(tmp_path, "old123", "new456")

        assert len(commits) == 0


class TestGetFileChanges:
    """Tests for _get_file_changes function."""

    @patch("subprocess.run")
    def test_get_file_changes(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test getting file changes between two commits."""

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            result = MagicMock()
            result.returncode = 0

            if "--numstat" in cmd:
                result.stdout = """45\t12\tsrc/auth.py
32\t0\tsrc/validators.py
28\t8\ttests/test_auth.py"""
            elif "--name-status" in cmd:
                result.stdout = """M\tsrc/auth.py
A\tsrc/validators.py
M\ttests/test_auth.py"""

            return result

        mock_run.side_effect = run_side_effect

        files = _get_file_changes(tmp_path, "old123", "new456")

        assert len(files) == 3
        assert files[0].path == "src/auth.py"
        assert files[0].change_type == "modified"
        assert files[0].insertions == 45
        assert files[0].deletions == 12
        assert files[1].path == "src/validators.py"
        assert files[1].change_type == "added"
        assert files[1].insertions == 32

    @patch("subprocess.run")
    def test_get_file_changes_with_deletions(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test getting file changes with deletions."""

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            result = MagicMock()
            result.returncode = 0

            if "--numstat" in cmd:
                result.stdout = "0\t50\told_file.py"
            elif "--name-status" in cmd:
                result.stdout = "D\told_file.py"

            return result

        mock_run.side_effect = run_side_effect

        files = _get_file_changes(tmp_path, "old123", "new456")

        assert len(files) == 1
        assert files[0].path == "old_file.py"
        assert files[0].change_type == "deleted"
        assert files[0].insertions == 0
        assert files[0].deletions == 50

    @patch("subprocess.run")
    def test_get_file_changes_with_rename(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test getting file changes with rename."""

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            result = MagicMock()
            result.returncode = 0

            if "--numstat" in cmd:
                result.stdout = "5\t3\tnew_name.py"
            elif "--name-status" in cmd:
                result.stdout = "R100\told_name.py\tnew_name.py"

            return result

        mock_run.side_effect = run_side_effect

        files = _get_file_changes(tmp_path, "old123", "new456")

        assert len(files) == 1
        assert files[0].path == "new_name.py"
        assert files[0].change_type == "renamed"
        assert files[0].old_path == "old_name.py"

    @patch("subprocess.run")
    def test_get_file_changes_binary_file(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test getting file changes with binary file."""

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            result = MagicMock()
            result.returncode = 0

            if "--numstat" in cmd:
                result.stdout = "-\t-\timage.png"
            elif "--name-status" in cmd:
                result.stdout = "M\timage.png"

            return result

        mock_run.side_effect = run_side_effect

        files = _get_file_changes(tmp_path, "old123", "new456")

        assert len(files) == 1
        assert files[0].path == "image.png"
        assert files[0].insertions == 0
        assert files[0].deletions == 0


class TestGetCurrentBranch:
    """Tests for get_current_branch function."""

    @patch("subprocess.run")
    def test_get_current_branch(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test getting current branch name."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "main\n"
        mock_run.return_value = mock_result

        branch = get_current_branch(tmp_path)

        assert branch == "main"

    @patch("subprocess.run")
    def test_get_current_branch_detached_head(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test getting branch name when in detached HEAD state."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "HEAD\n"
        mock_run.return_value = mock_result

        branch = get_current_branch(tmp_path)

        assert branch is None

    @patch("subprocess.run")
    def test_get_current_branch_error(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test handling error when getting current branch."""
        mock_run.side_effect = subprocess.SubprocessError()

        branch = get_current_branch(tmp_path)

        assert branch is None


class TestGetUncommittedFiles:
    """Tests for get_uncommitted_files function."""

    @patch("subprocess.run")
    def test_get_uncommitted_files_modified(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test getting uncommitted modified files."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = " M src/main.py\nM  src/config.py\n"
        mock_run.return_value = mock_result

        files = get_uncommitted_files(tmp_path)

        assert len(files) == 2
        assert files[0].path == "src/main.py"
        assert files[0].status == "M"
        assert "Modified" in files[0].status_description
        assert files[1].path == "src/config.py"
        assert files[1].status == "M"

    @patch("subprocess.run")
    def test_get_uncommitted_files_untracked(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test getting untracked files."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "?? new_file.py\n?? temp.txt\n"
        mock_run.return_value = mock_result

        files = get_uncommitted_files(tmp_path)

        assert len(files) == 2
        assert files[0].path == "new_file.py"
        assert files[0].status == "??"
        assert files[0].status_description == "Untracked"
        assert files[1].path == "temp.txt"
        assert files[1].status == "??"
        assert files[1].status_description == "Untracked"

    @patch("subprocess.run")
    def test_get_uncommitted_files_deleted(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test getting deleted files."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = " D deleted.py\n"
        mock_run.return_value = mock_result

        files = get_uncommitted_files(tmp_path)

        assert len(files) == 1
        assert files[0].path == "deleted.py"
        assert files[0].status == "D"
        assert "Deleted" in files[0].status_description

    @patch("subprocess.run")
    def test_get_uncommitted_files_added(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test getting added files."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "A  new_feature.py\n"
        mock_run.return_value = mock_result

        files = get_uncommitted_files(tmp_path)

        assert len(files) == 1
        assert files[0].path == "new_feature.py"
        assert files[0].status == "A"
        assert "Added" in files[0].status_description

    @patch("subprocess.run")
    def test_get_uncommitted_files_mixed(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test getting mixed uncommitted files."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = " M modified.py\nA  added.py\n D deleted.py\n?? untracked.py\nM  staged.py\n"
        mock_run.return_value = mock_result

        files = get_uncommitted_files(tmp_path)

        assert len(files) == 5
        # Check that we got all the different types
        statuses = {f.status for f in files}
        assert "M" in statuses
        assert "A" in statuses
        assert "D" in statuses
        assert "??" in statuses

    @patch("subprocess.run")
    def test_get_uncommitted_files_empty(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test getting uncommitted files when repo is clean."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        files = get_uncommitted_files(tmp_path)

        assert len(files) == 0

    @patch("subprocess.run")
    def test_get_uncommitted_files_error(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test handling error when getting uncommitted files."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        files = get_uncommitted_files(tmp_path)

        assert len(files) == 0

    @patch("subprocess.run")
    def test_get_uncommitted_files_timeout(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test handling timeout when getting uncommitted files."""
        mock_run.side_effect = subprocess.TimeoutExpired("git", 10)

        files = get_uncommitted_files(tmp_path)

        assert len(files) == 0


class TestGetGitVersion:
    """Tests for get_git_version function."""

    @patch("subprocess.run")
    def test_get_git_version(self, mock_run: MagicMock) -> None:
        """Test getting git version."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "git version 2.39.0\n"
        mock_run.return_value = mock_result

        version = get_git_version()

        assert version == "2.39.0"

    @patch("subprocess.run")
    def test_get_git_version_not_found(self, mock_run: MagicMock) -> None:
        """Test getting git version when git is not found."""
        mock_run.side_effect = FileNotFoundError()

        version = get_git_version()

        assert version == "unknown"


class TestPullRepositoryDetailed:
    """Tests for pull_repository_detailed function."""

    @patch("subprocess.run")
    def test_already_up_to_date(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test detailed pull when repo is already up-to-date."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Already up to date."
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = pull_repository_detailed(tmp_path)

        assert result.success is True
        assert result.already_up_to_date is True
        assert result.commits_count == 0
        assert result.files_changed == 0

    @patch("subprocess.run")
    def test_successful_pull_with_details(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test successful pull with detailed information."""

        def run_side_effect(*args, **kwargs):
            cmd = args[0]
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""

            if cmd[1] == "pull":
                result.stdout = """Updating abc123..def456
Fast-forward
 file.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)"""
            elif cmd[1] == "log":
                result.stdout = "a1b2c3d|Author|2025-10-15T10:00:00|Commit message"
            elif "--numstat" in cmd:
                result.stdout = "1\t1\tfile.py"
            elif "--name-status" in cmd:
                result.stdout = "M\tfile.py"

            return result

        mock_run.side_effect = run_side_effect

        result = pull_repository_detailed(tmp_path)

        assert result.success is True
        assert result.already_up_to_date is False
        assert result.old_commit == "abc123"
        assert result.new_commit == "def456"
        assert result.files_changed == 1
        assert result.insertions == 1
        assert result.deletions == 1

    @patch("subprocess.run")
    def test_pull_with_error(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test pull with error."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "fatal: Authentication failed"
        mock_run.return_value = mock_result

        result = pull_repository_detailed(tmp_path)

        assert result.success is False
        assert result.error_message == "Authentication failed"
        assert "Authentication failed" in result.error_details


class TestUpdateRepositoryWithLog:
    """Tests for update_repository_with_log function."""

    def test_skip_no_remote(self, tmp_path: Path) -> None:
        """Test skipping repo with no remote and generating log."""
        repo = RepoInfo(path=tmp_path, name="test-repo")

        with (
            patch("gittyup.git_operations.get_current_branch") as mock_branch,
            patch("gittyup.git_operations.get_repo_status") as mock_status,
        ):
            mock_branch.return_value = "main"
            mock_status.return_value = {
                "has_remote": False,
                "is_clean": True,
                "is_detached": False,
                "has_upstream": True,
            }

            repo_info, log_entry = update_repository_with_log(repo)

            assert repo_info.status == RepoStatus.SKIPPED
            assert log_entry.status == "skipped"
            assert log_entry.skip_reason == "No remote configured"
            assert log_entry.branch == "main"
            assert log_entry.duration_ms >= 0  # Can be 0 for very fast operations

    def test_successful_update_with_log(self, tmp_path: Path) -> None:
        """Test successful update with detailed log."""
        repo = RepoInfo(path=tmp_path, name="test-repo")

        with (
            patch("gittyup.git_operations.get_current_branch") as mock_branch,
            patch("gittyup.git_operations.get_repo_status") as mock_status,
            patch("gittyup.git_operations.pull_repository_detailed") as mock_pull,
        ):
            mock_branch.return_value = "main"
            mock_status.return_value = {
                "has_remote": True,
                "is_clean": True,
                "is_detached": False,
                "has_upstream": True,
            }

            # Create a detailed pull result
            pull_result = PullResult(
                success=True,
                already_up_to_date=False,
                full_output="Pull successful",
                commits_count=3,
                files_changed=5,
                insertions=127,
                deletions=43,
            )
            pull_result.commits = [
                CommitInfo("a1b2c3d", "Author", "2025-10-15T10:00:00", "Test commit"),
            ]
            pull_result.files = [
                FileChange("file.py", "modified", 10, 5),
            ]
            mock_pull.return_value = pull_result

            repo_info, log_entry = update_repository_with_log(repo)

            assert repo_info.status == RepoStatus.UPDATED
            assert log_entry.status == "updated"
            assert log_entry.commits_pulled == 3
            assert log_entry.files_changed == 5
            assert log_entry.insertions == 127
            assert log_entry.deletions == 43
            assert len(log_entry.commits) == 1
            assert len(log_entry.files) == 1

    def test_error_with_log(self, tmp_path: Path) -> None:
        """Test error handling with detailed log."""
        repo = RepoInfo(path=tmp_path, name="test-repo")

        with (
            patch("gittyup.git_operations.get_current_branch") as mock_branch,
            patch("gittyup.git_operations.get_repo_status") as mock_status,
            patch("gittyup.git_operations.pull_repository_detailed") as mock_pull,
        ):
            mock_branch.return_value = "main"
            mock_status.return_value = {
                "has_remote": True,
                "is_clean": True,
                "is_detached": False,
                "has_upstream": True,
            }

            pull_result = PullResult(
                success=False,
                already_up_to_date=False,
                error_message="Network error",
                error_details="Connection refused",
            )
            mock_pull.return_value = pull_result

            repo_info, log_entry = update_repository_with_log(repo)

            assert repo_info.status == RepoStatus.ERROR
            assert log_entry.status == "error"
            assert log_entry.error == "Network error"
            assert log_entry.error_details == "Connection refused"


@pytest.mark.integration
class TestGitOperationsIntegration:
    """Integration tests using real git repositories."""

    def test_real_git_check(self) -> None:
        """Test that git is actually installed (integration check)."""
        assert check_git_installed() is True

    def test_invalid_repo_path(self, tmp_path: Path) -> None:
        """Test operations on invalid repository path."""
        # Create a directory that's not a git repo
        non_repo = tmp_path / "not-a-repo"
        non_repo.mkdir()

        repo = RepoInfo(path=non_repo, name="not-a-repo")

        # This should handle gracefully
        result = update_repository(repo, timeout=5)

        # Should detect issues and skip or error
        assert result.status in (RepoStatus.SKIPPED, RepoStatus.ERROR)
