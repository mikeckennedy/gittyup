"""Tests for output formatting."""

from datetime import datetime
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from colorama import Fore

from gittyup.models import (
    CommitInfo,
    FileChange,
    OperationLog,
    RepoInfo,
    RepoLogEntry,
    RepoStatus,
    ScanResult,
)
from gittyup.output import (
    SYMBOL_ERROR,
    SYMBOL_PENDING,
    SYMBOL_SKIP,
    SYMBOL_SUCCESS,
    SYMBOL_UPDATED,
    _print_error_details,
    _print_repo_detail,
    _print_skip_details,
    _print_update_details,
    format_progress,
    format_repo_status,
    format_summary,
    get_status_color,
    get_status_symbol,
    print_error,
    print_explain,
    print_header,
    print_info,
    print_progress,
    print_repo_status,
    print_section,
    print_separator,
    print_success,
    print_summary,
    print_warning,
)


class TestGetStatusColor:
    """Tests for status color mapping."""

    def test_up_to_date_color(self) -> None:
        """Test color for up-to-date status."""
        color = get_status_color(RepoStatus.UP_TO_DATE)
        assert color == Fore.GREEN

    def test_updated_color(self) -> None:
        """Test color for updated status."""
        color = get_status_color(RepoStatus.UPDATED)
        assert color == Fore.CYAN

    def test_skipped_color(self) -> None:
        """Test color for skipped status."""
        color = get_status_color(RepoStatus.SKIPPED)
        assert color == Fore.YELLOW

    def test_error_color(self) -> None:
        """Test color for error status."""
        color = get_status_color(RepoStatus.ERROR)
        assert color == Fore.RED

    def test_pending_color(self) -> None:
        """Test color for pending status."""
        color = get_status_color(RepoStatus.PENDING)
        assert color == Fore.WHITE

    def test_unknown_status_defaults_to_white(self) -> None:
        """Test that unknown status defaults to white."""
        # This shouldn't happen in practice, but test defensive behavior
        color = get_status_color("unknown_status")  # type: ignore
        assert color == Fore.WHITE


class TestGetStatusSymbol:
    """Tests for status symbol mapping."""

    def test_up_to_date_symbol(self) -> None:
        """Test symbol for up-to-date status."""
        symbol = get_status_symbol(RepoStatus.UP_TO_DATE)
        assert symbol == SYMBOL_SUCCESS

    def test_updated_symbol(self) -> None:
        """Test symbol for updated status."""
        symbol = get_status_symbol(RepoStatus.UPDATED)
        assert symbol == SYMBOL_UPDATED

    def test_skipped_symbol(self) -> None:
        """Test symbol for skipped status."""
        symbol = get_status_symbol(RepoStatus.SKIPPED)
        assert symbol == SYMBOL_SKIP

    def test_error_symbol(self) -> None:
        """Test symbol for error status."""
        symbol = get_status_symbol(RepoStatus.ERROR)
        assert symbol == SYMBOL_ERROR

    def test_pending_symbol(self) -> None:
        """Test symbol for pending status."""
        symbol = get_status_symbol(RepoStatus.PENDING)
        assert symbol == SYMBOL_PENDING


class TestFormatRepoStatus:
    """Tests for repository status formatting."""

    def test_format_basic_status(self, tmp_path: Path) -> None:
        """Test basic status formatting with path."""
        repo = RepoInfo(path=tmp_path / "test-repo", name="test-repo", status=RepoStatus.UP_TO_DATE)

        output = format_repo_status(repo, show_path=True)

        assert "test-repo" in output
        assert SYMBOL_SUCCESS in output
        assert Fore.GREEN in output

    def test_format_status_with_message(self, tmp_path: Path) -> None:
        """Test status formatting with message."""
        repo = RepoInfo(
            path=tmp_path / "test-repo",
            name="test-repo",
            status=RepoStatus.UPDATED,
            message="Pulled 3 commits",
        )

        output = format_repo_status(repo)

        assert "test-repo" in output
        assert "Pulled 3 commits" in output
        assert SYMBOL_UPDATED in output

    def test_format_status_with_error(self, tmp_path: Path) -> None:
        """Test status formatting with error."""
        repo = RepoInfo(
            path=tmp_path / "test-repo",
            name="test-repo",
            status=RepoStatus.ERROR,
            error="Network timeout",
        )

        output = format_repo_status(repo)

        assert "test-repo" in output
        assert "Network timeout" in output
        assert SYMBOL_ERROR in output
        assert "Error:" in output

    def test_format_status_without_path(self, tmp_path: Path) -> None:
        """Test status formatting showing only name."""
        repo = RepoInfo(path=tmp_path / "test-repo", name="test-repo", status=RepoStatus.UP_TO_DATE)

        output = format_repo_status(repo, show_path=False)

        assert "test-repo" in output
        assert str(tmp_path) not in output  # Path should not be shown

    def test_format_status_all_statuses(self, tmp_path: Path) -> None:
        """Test formatting for all possible statuses."""
        for status in RepoStatus:
            repo = RepoInfo(path=tmp_path / "test-repo", name="test-repo", status=status)
            output = format_repo_status(repo)
            assert "test-repo" in output
            assert len(output) > 0


class TestPrintRepoStatus:
    """Tests for repository status printing."""

    def test_print_repo_status(self, tmp_path: Path) -> None:
        """Test printing repository status."""
        repo = RepoInfo(path=tmp_path / "test-repo", name="test-repo", status=RepoStatus.UP_TO_DATE)

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            print_repo_status(repo)
            output = mock_stdout.getvalue()

        assert "test-repo" in output
        assert SYMBOL_SUCCESS in output


class TestFormatSummary:
    """Tests for summary formatting."""

    def test_format_empty_summary(self, tmp_path: Path) -> None:
        """Test formatting summary with no repositories."""
        result = ScanResult(scan_root=tmp_path)

        output = format_summary(result)

        assert "Summary" in output
        assert "Total repositories found:" in output
        assert "0" in output

    def test_format_summary_with_repos(self, tmp_path: Path) -> None:
        """Test formatting summary with repositories."""
        result = ScanResult(scan_root=tmp_path)
        result.add_repository(tmp_path / "repo1")
        result.add_repository(tmp_path / "repo2")
        result.repositories[0].status = RepoStatus.UP_TO_DATE
        result.repositories[1].status = RepoStatus.UPDATED

        output = format_summary(result)

        assert "Summary" in output
        assert "Total repositories found:" in output
        assert "Up to date:" in output
        assert "Updated:" in output

    def test_format_summary_with_elapsed_time(self, tmp_path: Path) -> None:
        """Test formatting summary with elapsed time."""
        result = ScanResult(scan_root=tmp_path)

        output = format_summary(result, elapsed_time=3.14159)

        assert "3.14 seconds" in output

    def test_format_summary_with_errors(self, tmp_path: Path) -> None:
        """Test formatting summary with errors."""
        result = ScanResult(scan_root=tmp_path)
        result.add_error(tmp_path / "error1", "Error 1")
        result.add_error(tmp_path / "error2", "Error 2")

        output = format_summary(result)

        assert "Errors encountered: 2" in output
        assert "Error 1" in output
        assert "Error 2" in output

    def test_format_summary_truncates_many_errors(self, tmp_path: Path) -> None:
        """Test that summary truncates when there are many errors."""
        result = ScanResult(scan_root=tmp_path)
        for i in range(10):
            result.add_error(tmp_path / f"error{i}", f"Error {i}")

        output = format_summary(result)

        assert "Errors encountered: 10" in output
        assert "and 5 more errors" in output

    def test_format_summary_with_skipped_paths(self, tmp_path: Path) -> None:
        """Test formatting summary with skipped paths."""
        result = ScanResult(scan_root=tmp_path)
        result.add_skipped_path(tmp_path / "skip1")
        result.add_skipped_path(tmp_path / "skip2")

        output = format_summary(result)

        assert "Skipped paths: 2" in output

    def test_format_summary_all_status_types(self, tmp_path: Path) -> None:
        """Test summary with all status types."""
        result = ScanResult(scan_root=tmp_path)

        # Add repos with different statuses
        repo1 = result.add_repository(tmp_path / "repo1")
        repo1.status = RepoStatus.UP_TO_DATE

        repo2 = result.add_repository(tmp_path / "repo2")
        repo2.status = RepoStatus.UPDATED

        repo3 = result.add_repository(tmp_path / "repo3")
        repo3.status = RepoStatus.SKIPPED

        repo4 = result.add_repository(tmp_path / "repo4")
        repo4.status = RepoStatus.ERROR

        output = format_summary(result)

        assert "Total repositories found:" in output
        assert "Up to date:" in output
        assert "Updated:" in output
        assert "Skipped:" in output
        assert "Errors:" in output


class TestPrintSummary:
    """Tests for summary printing."""

    def test_print_summary(self, tmp_path: Path) -> None:
        """Test printing summary."""
        result = ScanResult(scan_root=tmp_path)

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            print_summary(result)
            output = mock_stdout.getvalue()

        assert "Summary" in output
        assert "Total repositories found:" in output


class TestPrintHeader:
    """Tests for header printing."""

    def test_print_header(self) -> None:
        """Test printing header."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            print_header("Test Header")
            output = mock_stdout.getvalue()

        assert "Test Header" in output
        assert "=" in output

    def test_print_header_custom_width(self) -> None:
        """Test printing header with custom width."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            print_header("Test", width=20)
            output = mock_stdout.getvalue()

        assert "Test" in output
        # Check that there are approximately 20 equals signs
        assert output.count("=") >= 20


class TestPrintSeparator:
    """Tests for separator printing."""

    def test_print_separator(self) -> None:
        """Test printing separator."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            print_separator()
            output = mock_stdout.getvalue()

        assert "-" in output

    def test_print_separator_custom_width(self) -> None:
        """Test printing separator with custom width."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            print_separator(width=30)
            output = mock_stdout.getvalue()

        # Check that there are 30 dashes
        assert output.strip().count("-") == 30


class TestPrintMessages:
    """Tests for message printing functions."""

    def test_print_error(self) -> None:
        """Test printing error message."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            print_error("Test error")
            output = mock_stdout.getvalue()

        assert "Test error" in output
        assert SYMBOL_ERROR in output
        assert "Error:" in output

    def test_print_success(self) -> None:
        """Test printing success message."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            print_success("Test success")
            output = mock_stdout.getvalue()

        assert "Test success" in output
        assert SYMBOL_SUCCESS in output

    def test_print_warning(self) -> None:
        """Test printing warning message."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            print_warning("Test warning")
            output = mock_stdout.getvalue()

        assert "Test warning" in output
        assert SYMBOL_SKIP in output
        assert "Warning:" in output

    def test_print_info(self) -> None:
        """Test printing info message."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            print_info("Test info")
            output = mock_stdout.getvalue()

        assert "Test info" in output
        assert SYMBOL_PENDING in output


class TestFormatProgress:
    """Tests for progress formatting."""

    def test_format_progress_basic(self) -> None:
        """Test basic progress formatting."""
        output = format_progress(1, 10, "test-repo")

        assert "1/10" in output
        assert "10%" in output
        assert "test-repo" in output

    def test_format_progress_halfway(self) -> None:
        """Test progress formatting at 50%."""
        output = format_progress(5, 10, "test-repo")

        assert "5/10" in output
        assert "50%" in output

    def test_format_progress_complete(self) -> None:
        """Test progress formatting at 100%."""
        output = format_progress(10, 10, "test-repo")

        assert "10/10" in output
        assert "100%" in output

    def test_format_progress_zero_total(self) -> None:
        """Test progress formatting with zero total."""
        output = format_progress(0, 0, "test-repo")

        assert "0%" in output
        assert "test-repo" in output


class TestPrintProgress:
    """Tests for progress printing."""

    def test_print_progress(self) -> None:
        """Test printing progress."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            print_progress(3, 10, "test-repo")
            output = mock_stdout.getvalue()

        assert "3/10" in output
        assert "30%" in output
        assert "test-repo" in output


class TestOutputIntegration:
    """Integration tests for output formatting."""

    def test_complete_workflow_output(self, tmp_path: Path) -> None:
        """Test complete workflow output formatting."""
        # Create a scan result with various statuses
        result = ScanResult(scan_root=tmp_path)

        repo1 = result.add_repository(tmp_path / "repo1")
        repo1.status = RepoStatus.UP_TO_DATE
        repo1.message = "Already up to date"

        repo2 = result.add_repository(tmp_path / "repo2")
        repo2.status = RepoStatus.UPDATED
        repo2.message = "Pulled 3 commits"

        repo3 = result.add_repository(tmp_path / "repo3")
        repo3.status = RepoStatus.SKIPPED
        repo3.message = "Uncommitted changes"

        repo4 = result.add_repository(tmp_path / "repo4")
        repo4.status = RepoStatus.ERROR
        repo4.error = "Network timeout"

        result.add_error(tmp_path / "bad-path", "Permission denied")

        # Format everything
        output_lines = []
        for repo in result.repositories:
            output_lines.append(format_repo_status(repo))

        summary = format_summary(result, elapsed_time=2.5)

        # Verify all output is present
        combined_output = "\n".join(output_lines) + summary

        assert "repo1" in combined_output
        assert "repo2" in combined_output
        assert "repo3" in combined_output
        assert "repo4" in combined_output
        assert "Already up to date" in combined_output
        assert "Pulled 3 commits" in combined_output
        assert "Uncommitted changes" in combined_output
        assert "Network timeout" in combined_output
        assert "Permission denied" in combined_output
        assert "2.50 seconds" in combined_output
        assert "Total repositories found:" in combined_output


# ============================================================================
# Tests for Explain Output Functions
# ============================================================================


class TestPrintSection:
    """Tests for section header printing."""

    def test_print_section(self) -> None:
        """Test printing section header."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            print_section("Test Section")
            output = mock_stdout.getvalue()

        assert "Test Section" in output
        assert "=" in output


class TestPrintUpdateDetails:
    """Tests for update details printing."""

    def test_print_update_details_basic(self) -> None:
        """Test printing basic update details."""
        repo_log = RepoLogEntry(
            path="/path/to/repo",
            name="test-repo",
            status="updated",
            duration_ms=500,
            commits_pulled=3,
            files_changed=5,
            insertions=42,
            deletions=10,
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_update_details(repo_log)
            output = mock_stdout.getvalue()

        assert "Changes pulled successfully" in output
        assert "Commits: 3" in output
        assert "Files changed: 5" in output
        assert "Insertions: +42" in output
        assert "Deletions: -10" in output

    def test_print_update_details_with_commits(self) -> None:
        """Test printing update details with commit information."""
        commits = [
            CommitInfo(
                commit_hash="abc123d",
                author="John Doe",
                date="2025-10-15T10:23:00",
                message="Add new feature for user authentication",
            ),
            CommitInfo(
                commit_hash="def456e",
                author="Jane Smith",
                date="2025-10-15T09:15:00",
                message="Fix bug in login validation",
            ),
        ]

        repo_log = RepoLogEntry(
            path="/path/to/repo",
            name="test-repo",
            status="updated",
            duration_ms=500,
            commits_pulled=2,
            files_changed=3,
            insertions=30,
            deletions=5,
            commits=commits,
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_update_details(repo_log)
            output = mock_stdout.getvalue()

        assert "📝 Commits:" in output
        assert "abc123d" in output
        assert "Add new feature for user authentication" in output
        assert "John Doe" in output
        assert "2025-10-15T10:23:00" in output
        assert "def456e" in output
        assert "Fix bug in login validation" in output
        assert "Jane Smith" in output

    def test_print_update_details_truncates_many_commits(self) -> None:
        """Test that update details truncates when there are many commits."""
        commits = [
            CommitInfo(
                commit_hash=f"hash{i:03d}",
                author=f"Author {i}",
                date="2025-10-15T10:00:00",
                message=f"Commit message {i}",
            )
            for i in range(10)
        ]

        repo_log = RepoLogEntry(
            path="/path/to/repo",
            name="test-repo",
            status="updated",
            duration_ms=500,
            commits_pulled=10,
            files_changed=20,
            insertions=100,
            deletions=50,
            commits=commits,
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_update_details(repo_log)
            output = mock_stdout.getvalue()

        assert "📝 Commits:" in output
        assert "hash000" in output
        assert "hash004" in output
        assert "and 5 more commits" in output

    def test_print_update_details_with_file_changes(self) -> None:
        """Test printing update details with file change information."""
        files = [
            FileChange(path="src/main.py", change_type="modified", insertions=20, deletions=5),
            FileChange(path="tests/test_main.py", change_type="added", insertions=45, deletions=0),
            FileChange(path="old_file.py", change_type="deleted", insertions=0, deletions=30),
            FileChange(path="new_name.py", change_type="renamed", insertions=0, deletions=0, old_path="old_name.py"),
        ]

        repo_log = RepoLogEntry(
            path="/path/to/repo",
            name="test-repo",
            status="updated",
            duration_ms=500,
            commits_pulled=1,
            files_changed=4,
            insertions=65,
            deletions=35,
            files=files,
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_update_details(repo_log)
            output = mock_stdout.getvalue()

        assert "📁 Files:" in output
        assert "~ src/main.py" in output
        assert "(+20/-5)" in output
        assert "+ tests/test_main.py" in output
        assert "(+45/-0)" in output
        assert "- old_file.py" in output
        assert "(+0/-30)" in output
        assert "→ new_name.py" in output

    def test_print_update_details_truncates_many_files(self) -> None:
        """Test that update details truncates when there are many files."""
        files = [
            FileChange(path=f"file{i:03d}.py", change_type="modified", insertions=i, deletions=i) for i in range(15)
        ]

        repo_log = RepoLogEntry(
            path="/path/to/repo",
            name="test-repo",
            status="updated",
            duration_ms=500,
            commits_pulled=1,
            files_changed=15,
            insertions=100,
            deletions=100,
            files=files,
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_update_details(repo_log)
            output = mock_stdout.getvalue()

        assert "📁 Files:" in output
        assert "file000.py" in output
        assert "file009.py" in output
        assert "and 5 more files" in output

    def test_print_update_details_with_unknown_change_type(self) -> None:
        """Test printing update details with unknown change type."""
        files = [FileChange(path="mystery.py", change_type="unknown", insertions=10, deletions=5)]

        repo_log = RepoLogEntry(
            path="/path/to/repo",
            name="test-repo",
            status="updated",
            duration_ms=500,
            commits_pulled=1,
            files_changed=1,
            insertions=10,
            deletions=5,
            files=files,
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_update_details(repo_log)
            output = mock_stdout.getvalue()

        assert "📁 Files:" in output
        assert "mystery.py" in output
        assert "?" in output  # Unknown change type should show ?


class TestPrintSkipDetails:
    """Tests for skip details printing."""

    def test_print_skip_details_basic(self) -> None:
        """Test printing basic skip details."""
        repo_log = RepoLogEntry(
            path="/path/to/repo",
            name="test-repo",
            status="skipped",
            duration_ms=100,
            skip_reason="Repository has uncommitted changes",
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_skip_details(repo_log)
            output = mock_stdout.getvalue()

        assert "Skipped" in output
        assert "Reason: Repository has uncommitted changes" in output

    def test_print_skip_details_with_message(self) -> None:
        """Test printing skip details with additional message."""
        repo_log = RepoLogEntry(
            path="/path/to/repo",
            name="test-repo",
            status="skipped",
            duration_ms=100,
            skip_reason="Detached HEAD state",
            message="Cannot pull in detached HEAD state",
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_skip_details(repo_log)
            output = mock_stdout.getvalue()

        assert "Skipped" in output
        assert "Reason: Detached HEAD state" in output
        assert "Details: Cannot pull in detached HEAD state" in output

    def test_print_skip_details_no_reason(self) -> None:
        """Test printing skip details without reason."""
        repo_log = RepoLogEntry(
            path="/path/to/repo", name="test-repo", status="skipped", duration_ms=100, skip_reason=None
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_skip_details(repo_log)
            output = mock_stdout.getvalue()

        assert "Skipped" in output

    def test_print_skip_details_with_uncommitted_files(self) -> None:
        """Test printing skip details with uncommitted files."""
        from gittyup.models import UncommittedFile

        repo_log = RepoLogEntry(
            path="/path/to/repo",
            name="test-repo",
            status="skipped",
            duration_ms=100,
            skip_reason="Repository has uncommitted changes",
            uncommitted_files=[
                UncommittedFile(path="modified.py", status="M", status_description="Modified"),
                UncommittedFile(path="new_file.py", status="?", status_description="Untracked"),
                UncommittedFile(path="deleted.py", status="D", status_description="Deleted"),
            ],
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_skip_details(repo_log)
            output = mock_stdout.getvalue()

        assert "Skipped" in output
        assert "Reason: Repository has uncommitted changes" in output
        assert "Uncommitted files (3)" in output
        assert "modified.py" in output
        assert "new_file.py" in output
        assert "deleted.py" in output

    def test_print_skip_details_with_many_uncommitted_files(self) -> None:
        """Test printing skip details with many uncommitted files (should truncate)."""
        from gittyup.models import UncommittedFile

        # Create 20 uncommitted files
        uncommitted_files = [
            UncommittedFile(path=f"file{i}.py", status="M", status_description="Modified") for i in range(20)
        ]

        repo_log = RepoLogEntry(
            path="/path/to/repo",
            name="test-repo",
            status="skipped",
            duration_ms=100,
            skip_reason="Repository has uncommitted changes",
            uncommitted_files=uncommitted_files,
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_skip_details(repo_log)
            output = mock_stdout.getvalue()

        assert "Skipped" in output
        assert "Uncommitted files (20)" in output
        assert "Reason: Repository has uncommitted changes" in output
        # Should show first 15 files
        assert "file0.py" in output
        assert "file14.py" in output
        # Should show truncation message
        assert "... and 5 more files" in output
        # Should not show file beyond 15
        assert "file19.py" not in output


class TestPrintErrorDetails:
    """Tests for error details printing."""

    def test_print_error_details_basic(self) -> None:
        """Test printing basic error details."""
        repo_log = RepoLogEntry(
            path="/path/to/repo", name="test-repo", status="error", duration_ms=200, error="Network timeout"
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_error_details(repo_log)
            output = mock_stdout.getvalue()

        assert "Error occurred" in output
        assert "Error: Network timeout" in output

    def test_print_error_details_with_details(self) -> None:
        """Test printing error details with full error details."""
        error_details = "Traceback (most recent call last):\n  File test.py, line 10\n    some error\nException: Failed"

        repo_log = RepoLogEntry(
            path="/path/to/repo",
            name="test-repo",
            status="error",
            duration_ms=200,
            error="Command failed",
            error_details=error_details,
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_error_details(repo_log)
            output = mock_stdout.getvalue()

        assert "Error occurred" in output
        assert "Error: Command failed" in output
        assert "📋 Details:" in output
        assert "Traceback" in output
        assert "Exception: Failed" in output

    def test_print_error_details_truncates_long_details(self) -> None:
        """Test that error details are truncated when they're too long."""
        # Create error details with more than 10 lines
        error_details = "\n".join([f"Line {i}" for i in range(20)])

        repo_log = RepoLogEntry(
            path="/path/to/repo",
            name="test-repo",
            status="error",
            duration_ms=200,
            error="Long error",
            error_details=error_details,
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_error_details(repo_log)
            output = mock_stdout.getvalue()

        assert "📋 Details:" in output
        assert "Line 0" in output
        assert "Line 9" in output
        assert "... (truncated)" in output
        # Line 10 and beyond should not be shown
        assert "Line 10" not in output

    def test_print_error_details_no_error_message(self) -> None:
        """Test printing error details without error message."""
        repo_log = RepoLogEntry(path="/path/to/repo", name="test-repo", status="error", duration_ms=200, error=None)

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_error_details(repo_log)
            output = mock_stdout.getvalue()

        assert "Error occurred" in output
        assert "Error: Unknown error" in output


class TestPrintRepoDetail:
    """Tests for repository detail printing."""

    def test_print_repo_detail_updated(self) -> None:
        """Test printing detail for updated repository."""
        repo_log = RepoLogEntry(
            path="/path/to/repo",
            name="test-repo",
            status="updated",
            duration_ms=500,
            branch="main",
            commits_pulled=2,
            files_changed=3,
            insertions=25,
            deletions=10,
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_repo_detail(repo_log)
            output = mock_stdout.getvalue()

        assert "✅" in output
        assert "test-repo" in output
        assert "Path: /path/to/repo" in output
        assert "Duration: 500ms" in output
        assert "Branch: main" in output
        assert "Changes pulled successfully" in output

    def test_print_repo_detail_up_to_date(self) -> None:
        """Test printing detail for up-to-date repository."""
        repo_log = RepoLogEntry(
            path="/path/to/repo",
            name="test-repo",
            status="up_to_date",
            duration_ms=150,
            branch="develop",
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_repo_detail(repo_log)
            output = mock_stdout.getvalue()

        assert "💤" in output
        assert "test-repo" in output
        assert "Path: /path/to/repo" in output
        assert "Duration: 150ms" in output
        assert "Branch: develop" in output
        assert "Already up-to-date" in output

    def test_print_repo_detail_skipped(self) -> None:
        """Test printing detail for skipped repository."""
        repo_log = RepoLogEntry(
            path="/path/to/repo",
            name="test-repo",
            status="skipped",
            duration_ms=80,
            branch="main",
            skip_reason="Uncommitted changes",
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_repo_detail(repo_log)
            output = mock_stdout.getvalue()

        assert "⏭️" in output
        assert "test-repo" in output
        assert "Path: /path/to/repo" in output
        assert "Duration: 80ms" in output
        assert "Branch: main" in output
        assert "Skipped" in output
        assert "Uncommitted changes" in output

    def test_print_repo_detail_error(self) -> None:
        """Test printing detail for error repository."""
        repo_log = RepoLogEntry(
            path="/path/to/repo",
            name="test-repo",
            status="error",
            duration_ms=300,
            error="Network timeout",
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_repo_detail(repo_log)
            output = mock_stdout.getvalue()

        assert "❌" in output
        assert "test-repo" in output
        assert "Path: /path/to/repo" in output
        assert "Duration: 300ms" in output
        assert "Error occurred" in output
        assert "Network timeout" in output

    def test_print_repo_detail_unknown_status(self) -> None:
        """Test printing detail for repository with unknown status."""
        repo_log = RepoLogEntry(
            path="/path/to/repo",
            name="test-repo",
            status="unknown",
            duration_ms=100,  # type: ignore
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_repo_detail(repo_log)
            output = mock_stdout.getvalue()

        assert "❓" in output
        assert "test-repo" in output

    def test_print_repo_detail_without_branch(self) -> None:
        """Test printing detail for repository without branch info."""
        repo_log = RepoLogEntry(
            path="/path/to/repo", name="test-repo", status="up_to_date", duration_ms=100, branch=None
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            _print_repo_detail(repo_log)
            output = mock_stdout.getvalue()

        assert "test-repo" in output
        assert "Path: /path/to/repo" in output
        # Branch line should not be present
        assert "Branch:" not in output


class TestPrintExplain:
    """Tests for explain command output."""

    def test_print_explain_basic(self, tmp_path: Path) -> None:
        """Test printing basic explain output."""
        operation_log = OperationLog(
            timestamp=datetime(2025, 10, 15, 14, 23, 45).isoformat(),
            scan_root=str(tmp_path),
            duration_seconds=2.34,
            dry_run=False,
            max_depth=None,
            exclude_patterns=[],
            total_repos=3,
            updated_repos=1,
            up_to_date_repos=2,
            skipped_repos=0,
            error_repos=0,
            repositories=[
                RepoLogEntry(
                    path=str(tmp_path / "repo1"),
                    name="repo1",
                    status="updated",
                    duration_ms=500,
                    branch="main",
                    commits_pulled=2,
                    files_changed=3,
                    insertions=25,
                    deletions=10,
                ),
                RepoLogEntry(
                    path=str(tmp_path / "repo2"),
                    name="repo2",
                    status="up_to_date",
                    duration_ms=150,
                    branch="develop",
                ),
                RepoLogEntry(
                    path=str(tmp_path / "repo3"),
                    name="repo3",
                    status="up_to_date",
                    duration_ms=120,
                    branch="main",
                ),
            ],
            gittyup_version="1.0.0",
            git_version="2.39.0",
            python_version="3.13.0",
            platform="macOS-14.0",
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            print_explain(operation_log)
            output = mock_stdout.getvalue()

        # Check header
        assert "Gitty Up - Operation History" in output

        # Check operation details
        assert "Operation Details" in output
        assert "2025-10-15 14:23:45" in output
        assert str(tmp_path) in output
        assert "2.34 seconds" in output
        assert "1.0.0" in output
        assert "2.39.0" in output

        # Check summary
        assert "Summary" in output
        assert "Total repositories: 3" in output
        assert "✅ Updated: 1" in output
        assert "💤 Already up-to-date: 2" in output
        assert "⏭️  Skipped: 0" in output
        assert "❌ Errors: 0" in output

        # Check repository details
        assert "Repository Details" in output
        assert "repo1" in output
        assert "repo2" in output
        assert "repo3" in output

    def test_print_explain_with_all_status_types(self, tmp_path: Path) -> None:
        """Test explain output with all repository status types."""
        operation_log = OperationLog(
            timestamp=datetime(2025, 10, 15, 14, 23, 45).isoformat(),
            scan_root=str(tmp_path),
            duration_seconds=5.5,
            dry_run=False,
            max_depth=3,
            exclude_patterns=["node_modules", ".venv"],
            total_repos=4,
            updated_repos=1,
            up_to_date_repos=1,
            skipped_repos=1,
            error_repos=1,
            repositories=[
                RepoLogEntry(
                    path=str(tmp_path / "updated-repo"),
                    name="updated-repo",
                    status="updated",
                    duration_ms=500,
                    branch="main",
                    commits_pulled=3,
                    files_changed=5,
                    insertions=42,
                    deletions=15,
                    commits=[
                        CommitInfo(
                            commit_hash="abc123d",
                            author="John Doe",
                            date="2025-10-15T10:23:00",
                            message="Add feature",
                        )
                    ],
                ),
                RepoLogEntry(
                    path=str(tmp_path / "uptodate-repo"),
                    name="uptodate-repo",
                    status="up_to_date",
                    duration_ms=150,
                    branch="main",
                ),
                RepoLogEntry(
                    path=str(tmp_path / "skipped-repo"),
                    name="skipped-repo",
                    status="skipped",
                    duration_ms=80,
                    branch="main",
                    skip_reason="Uncommitted changes",
                    message="Repository has local modifications",
                ),
                RepoLogEntry(
                    path=str(tmp_path / "error-repo"),
                    name="error-repo",
                    status="error",
                    duration_ms=200,
                    error="Network timeout",
                    error_details="Connection timed out after 30 seconds",
                ),
            ],
            gittyup_version="1.0.0",
            git_version="2.39.0",
            python_version="3.13.0",
            platform="macOS-14.0",
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            print_explain(operation_log)
            output = mock_stdout.getvalue()

        # Check all status types are represented
        assert "✅ Updated: 1" in output
        assert "💤 Already up-to-date: 1" in output
        assert "⏭️  Skipped: 1" in output
        assert "❌ Errors: 1" in output

        # Check repository names
        assert "updated-repo" in output
        assert "uptodate-repo" in output
        assert "skipped-repo" in output
        assert "error-repo" in output

        # Check status-specific details
        assert "Add feature" in output
        assert "Uncommitted changes" in output
        assert "Network timeout" in output

    def test_print_explain_empty_repositories(self, tmp_path: Path) -> None:
        """Test explain output with no repositories."""
        operation_log = OperationLog(
            timestamp=datetime(2025, 10, 15, 14, 23, 45).isoformat(),
            scan_root=str(tmp_path),
            duration_seconds=0.5,
            dry_run=False,
            max_depth=None,
            exclude_patterns=[],
            total_repos=0,
            updated_repos=0,
            up_to_date_repos=0,
            skipped_repos=0,
            error_repos=0,
            repositories=[],
            gittyup_version="1.0.0",
            git_version="2.39.0",
            python_version="3.13.0",
            platform="Linux",
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            print_explain(operation_log)
            output = mock_stdout.getvalue()

        assert "Total repositories: 0" in output
        assert "✅ Updated: 0" in output
        assert "Repository Details" in output


class TestExplainOutputIntegration:
    """Integration tests for explain output functionality."""

    def test_complete_explain_workflow(self, tmp_path: Path) -> None:
        """Test complete explain workflow with realistic data."""
        # Create realistic operation log
        operation_log = OperationLog(
            timestamp=datetime(2025, 10, 15, 10, 30, 0).isoformat(),
            scan_root=str(tmp_path),
            duration_seconds=3.75,
            dry_run=False,
            max_depth=5,
            exclude_patterns=["node_modules", ".venv", "venv"],
            total_repos=5,
            updated_repos=2,
            up_to_date_repos=2,
            skipped_repos=1,
            error_repos=0,
            repositories=[
                RepoLogEntry(
                    path=str(tmp_path / "project-alpha"),
                    name="project-alpha",
                    status="updated",
                    duration_ms=1200,
                    branch="main",
                    commits_pulled=3,
                    files_changed=8,
                    insertions=150,
                    deletions=45,
                    commits=[
                        CommitInfo(
                            commit_hash="a7f2c3d",
                            author="Alice Developer",
                            date="2025-10-15T09:30:00",
                            message="Implement user authentication system",
                        ),
                        CommitInfo(
                            commit_hash="b8e1d4f",
                            author="Bob Engineer",
                            date="2025-10-15T08:45:00",
                            message="Fix security vulnerability in login",
                        ),
                    ],
                    files=[
                        FileChange(path="src/auth.py", change_type="modified", insertions=75, deletions=20),
                        FileChange(path="src/models/user.py", change_type="modified", insertions=30, deletions=10),
                        FileChange(path="tests/test_auth.py", change_type="added", insertions=45, deletions=0),
                    ],
                ),
                RepoLogEntry(
                    path=str(tmp_path / "project-beta"),
                    name="project-beta",
                    status="updated",
                    duration_ms=800,
                    branch="develop",
                    commits_pulled=1,
                    files_changed=2,
                    insertions=25,
                    deletions=5,
                ),
                RepoLogEntry(
                    path=str(tmp_path / "project-gamma"),
                    name="project-gamma",
                    status="up_to_date",
                    duration_ms=150,
                    branch="main",
                ),
                RepoLogEntry(
                    path=str(tmp_path / "project-delta"),
                    name="project-delta",
                    status="up_to_date",
                    duration_ms=120,
                    branch="feature/new-api",
                ),
                RepoLogEntry(
                    path=str(tmp_path / "project-epsilon"),
                    name="project-epsilon",
                    status="skipped",
                    duration_ms=50,
                    branch="main",
                    skip_reason="Repository has uncommitted changes",
                    message="Pull would conflict with local modifications",
                ),
            ],
            gittyup_version="1.0.0",
            git_version="2.39.0",
            python_version="3.13.0",
            platform="macOS-14.0-arm64",
        )

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            print_explain(operation_log)
            output = mock_stdout.getvalue()

        # Verify comprehensive output
        assert "Gitty Up - Operation History" in output
        assert "2025-10-15 10:30:00" in output
        assert "3.75 seconds" in output
        assert "Total repositories: 5" in output
        assert "✅ Updated: 2" in output
        assert "💤 Already up-to-date: 2" in output
        assert "⏭️  Skipped: 1" in output

        # Verify all projects are listed
        assert "project-alpha" in output
        assert "project-beta" in output
        assert "project-gamma" in output
        assert "project-delta" in output
        assert "project-epsilon" in output

        # Verify detailed information for updated repo
        assert "Implement user authentication system" in output
        assert "Alice Developer" in output
        assert "src/auth.py" in output
        assert "(+75/-20)" in output

        # Verify skip reason
        assert "Repository has uncommitted changes" in output
