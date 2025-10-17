"""Tests for CLI interface."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gittyup import __version__
from gittyup.cli import main
from gittyup.models import RepoInfo, RepoLogEntry, RepoStatus, ScanResult


class TestCLIBasics:
    """Tests for basic CLI functionality."""

    def test_version_flag(self) -> None:
        """Test --version flag displays version."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert __version__ in result.output

    def test_help_flag(self) -> None:
        """Test --help flag displays help."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Gitty Up" in result.output
        assert "DIRECTORY" in result.output
        assert "--dry-run" in result.output
        assert "--verbose" in result.output

    def test_quiet_and_verbose_are_mutually_exclusive(self) -> None:
        """Test that --quiet and --verbose cannot be used together."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["--quiet", "--verbose"])

        assert result.exit_code == 1
        assert "Cannot use both --quiet and --verbose" in result.output

    @patch("gittyup.cli.git_operations.check_git_installed")
    def test_exits_if_git_not_installed(self, mock_check_git: MagicMock) -> None:
        """Test that CLI exits if git is not installed."""
        mock_check_git.return_value = False

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["."])

        assert result.exit_code == 1
        assert "Git is not installed" in result.output


class TestCLIDirectoryHandling:
    """Tests for directory argument handling."""

    @patch("gittyup.cli.git_operations.check_git_installed")
    @patch("gittyup.cli.scanner.scan_directory")
    def test_default_directory_is_current(
        self, mock_scan: MagicMock, mock_check_git: MagicMock, tmp_path: Path
    ) -> None:
        """Test that default directory is current directory."""
        mock_check_git.return_value = True
        mock_scan.return_value = ScanResult(scan_root=tmp_path)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, [])

        assert result.exit_code == 0
        mock_scan.assert_called_once()
        # Should be called with resolved current directory
        call_args = mock_scan.call_args
        assert call_args[0][0].is_absolute()

    @patch("gittyup.cli.git_operations.check_git_installed")
    @patch("gittyup.cli.scanner.scan_directory")
    def test_custom_directory(self, mock_scan: MagicMock, mock_check_git: MagicMock, tmp_path: Path) -> None:
        """Test specifying custom directory."""
        mock_check_git.return_value = True
        test_dir = tmp_path / "test_repos"
        test_dir.mkdir()
        mock_scan.return_value = ScanResult(scan_root=test_dir)

        runner = CliRunner()
        result = runner.invoke(main, [str(test_dir)])

        assert result.exit_code == 0
        mock_scan.assert_called_once()
        assert str(test_dir) in str(mock_scan.call_args[0][0])

    def test_nonexistent_directory_fails(self) -> None:
        """Test that nonexistent directory causes error."""
        runner = CliRunner()
        result = runner.invoke(main, ["/nonexistent/path/xyz123"])

        assert result.exit_code != 0
        # Click should handle this with its path validation


class TestCLIOptions:
    """Tests for CLI options."""

    @patch("gittyup.cli.git_operations.check_git_installed")
    @patch("gittyup.cli.scanner.scan_directory")
    def test_max_depth_option(self, mock_scan: MagicMock, mock_check_git: MagicMock, tmp_path: Path) -> None:
        """Test --max-depth option is passed to scanner."""
        mock_check_git.return_value = True
        mock_scan.return_value = ScanResult(scan_root=tmp_path)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["--max-depth", "3"])

        assert result.exit_code == 0
        mock_scan.assert_called_once()
        assert mock_scan.call_args[1]["max_depth"] == 3

    @patch("gittyup.cli.git_operations.check_git_installed")
    @patch("gittyup.cli.scanner.scan_directory")
    def test_exclude_option(self, mock_scan: MagicMock, mock_check_git: MagicMock, tmp_path: Path) -> None:
        """Test --exclude option is passed to scanner."""
        mock_check_git.return_value = True
        mock_scan.return_value = ScanResult(scan_root=tmp_path)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["--exclude", "temp", "--exclude", "cache"])

        assert result.exit_code == 0
        mock_scan.assert_called_once()
        exclude_patterns = mock_scan.call_args[1]["exclude_patterns"]
        assert "temp" in exclude_patterns
        assert "cache" in exclude_patterns

    @patch("gittyup.cli.git_operations.check_git_installed")
    @patch("gittyup.cli.scanner.scan_directory")
    @patch("gittyup.cli.git_operations.update_repository")
    def test_dry_run_option(
        self, mock_update: MagicMock, mock_scan: MagicMock, mock_check_git: MagicMock, tmp_path: Path
    ) -> None:
        """Test --dry-run option doesn't actually update."""
        mock_check_git.return_value = True

        # Create a scan result with one repo
        result = ScanResult(scan_root=tmp_path)
        repo = result.add_repository(tmp_path / "test-repo")
        mock_scan.return_value = result

        runner = CliRunner()
        cli_result = runner.invoke(main, ["--dry-run", str(tmp_path)])

        assert cli_result.exit_code == 0
        assert "[DRY RUN]" in cli_result.output
        # update_repository should NOT be called in dry run
        mock_update.assert_not_called()
        # Repo should have pending status with message
        assert repo.status == RepoStatus.PENDING


class TestCLIWorkflow:
    """Tests for complete CLI workflow."""

    @patch("gittyup.cli.git_operations.check_git_installed")
    @patch("gittyup.cli.scanner.scan_directory")
    def test_no_repos_found(self, mock_scan: MagicMock, mock_check_git: MagicMock, tmp_path: Path) -> None:
        """Test output when no repositories are found."""
        mock_check_git.return_value = True
        mock_scan.return_value = ScanResult(scan_root=tmp_path)

        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_path)])

        assert result.exit_code == 0
        assert "No git repositories found" in result.output

    @patch("gittyup.cli.git_operations.check_git_installed")
    @patch("gittyup.cli.scanner.scan_directory")
    @patch("gittyup.cli.git_operations.async_update_repository_with_log")
    def test_successful_update(
        self, mock_update: MagicMock, mock_scan: MagicMock, mock_check_git: MagicMock, tmp_path: Path
    ) -> None:
        """Test successful repository update."""
        mock_check_git.return_value = True

        # Create scan result with repos
        result = ScanResult(scan_root=tmp_path)
        result.add_repository(tmp_path / "repo1")
        result.add_repository(tmp_path / "repo2")
        mock_scan.return_value = result

        # Mock update to return tuple of (repo, repo_log) - must be async
        async def update_side_effect(
            repo: RepoInfo, skip_dirty: bool = True, timeout: int = 60
        ) -> tuple[RepoInfo, RepoLogEntry]:
            repo.status = RepoStatus.UP_TO_DATE
            repo.message = "Already up to date"
            repo_log = RepoLogEntry(path=str(repo.path), name=repo.name, status="up_to_date", duration_ms=100)
            return repo, repo_log

        mock_update.side_effect = update_side_effect

        runner = CliRunner()
        cli_result = runner.invoke(main, [str(tmp_path)])

        assert cli_result.exit_code == 0
        assert "Found 2 git" in cli_result.output
        assert "Summary" in cli_result.output
        assert mock_update.call_count == 2

    @patch("gittyup.cli.git_operations.check_git_installed")
    @patch("gittyup.cli.scanner.scan_directory")
    @patch("gittyup.cli.git_operations.async_update_repository_with_log")
    def test_update_with_errors(
        self, mock_update: MagicMock, mock_scan: MagicMock, mock_check_git: MagicMock, tmp_path: Path
    ) -> None:
        """Test handling of update errors."""
        mock_check_git.return_value = True

        # Create scan result
        result = ScanResult(scan_root=tmp_path)
        result.add_repository(tmp_path / "repo1")
        result.add_error(tmp_path / "bad-path", "Permission denied")
        mock_scan.return_value = result

        # Mock update to return tuple with error status - must be async
        async def update_side_effect(
            repo: RepoInfo, skip_dirty: bool = True, timeout: int = 60
        ) -> tuple[RepoInfo, RepoLogEntry]:
            repo.status = RepoStatus.ERROR
            repo.error = "Network timeout"
            repo_log = RepoLogEntry(
                path=str(repo.path), name=repo.name, status="error", duration_ms=100, error="Network timeout"
            )
            return repo, repo_log

        mock_update.side_effect = update_side_effect

        runner = CliRunner()
        cli_result = runner.invoke(main, [str(tmp_path)])

        # Should exit with error code when errors occur
        assert cli_result.exit_code == 1
        assert "Summary" in cli_result.output


class TestCLIVerbosity:
    """Tests for verbosity levels."""

    @patch("gittyup.cli.git_operations.check_git_installed")
    @patch("gittyup.cli.scanner.scan_directory")
    @patch("gittyup.cli.git_operations.async_update_repository_with_log")
    def test_quiet_mode_only_shows_errors(
        self, mock_update: MagicMock, mock_scan: MagicMock, mock_check_git: MagicMock, tmp_path: Path
    ) -> None:
        """Test --quiet mode only shows errors."""
        mock_check_git.return_value = True

        # Create repos with different statuses
        result = ScanResult(scan_root=tmp_path)
        result.add_repository(tmp_path / "repo1")
        result.add_repository(tmp_path / "repo2")
        mock_scan.return_value = result

        async def update_side_effect(
            repo: RepoInfo, skip_dirty: bool = True, timeout: int = 60
        ) -> tuple[RepoInfo, RepoLogEntry]:
            if repo.name == "repo1":
                repo.status = RepoStatus.UP_TO_DATE
                status = "up_to_date"
            else:
                repo.status = RepoStatus.ERROR
                repo.error = "Test error"
                status = "error"
                # Must also add to result.errors for has_errors to be True
                result.add_error(repo.path, "Test error")
            repo_log = RepoLogEntry(path=str(repo.path), name=repo.name, status=status, duration_ms=100)
            return repo, repo_log

        mock_update.side_effect = update_side_effect

        runner = CliRunner()
        cli_result = runner.invoke(main, ["--quiet", str(tmp_path)])

        # Should exit with error code
        assert cli_result.exit_code == 1
        # Should show error repo
        assert "repo2" in cli_result.output or "Error" in cli_result.output
        # Should not show header/summary
        assert "Gitty Up" not in cli_result.output
        assert "Summary" not in cli_result.output

    @patch("gittyup.cli.git_operations.check_git_installed")
    @patch("gittyup.cli.scanner.scan_directory")
    @patch("gittyup.cli.git_operations.async_update_repository_with_log")
    def test_verbose_mode_shows_all(
        self, mock_update: MagicMock, mock_scan: MagicMock, mock_check_git: MagicMock, tmp_path: Path
    ) -> None:
        """Test --verbose mode shows all repositories."""
        mock_check_git.return_value = True

        result = ScanResult(scan_root=tmp_path)
        result.add_repository(tmp_path / "repo1")
        result.add_repository(tmp_path / "repo2")
        mock_scan.return_value = result

        async def update_side_effect(
            repo: RepoInfo, skip_dirty: bool = True, timeout: int = 60
        ) -> tuple[RepoInfo, RepoLogEntry]:
            repo.status = RepoStatus.UP_TO_DATE
            repo.message = "Already up to date"
            repo_log = RepoLogEntry(path=str(repo.path), name=repo.name, status="up_to_date", duration_ms=100)
            return repo, repo_log

        mock_update.side_effect = update_side_effect

        runner = CliRunner()
        cli_result = runner.invoke(main, ["--verbose", str(tmp_path)])

        assert cli_result.exit_code == 0
        # Both repos should be shown even though they're up-to-date
        assert "repo1" in cli_result.output
        assert "repo2" in cli_result.output

    @patch("gittyup.cli.git_operations.check_git_installed")
    @patch("gittyup.cli.scanner.scan_directory")
    @patch("gittyup.cli.git_operations.async_update_repository_with_log")
    def test_normal_mode_skips_up_to_date(
        self, mock_update: MagicMock, mock_scan: MagicMock, mock_check_git: MagicMock, tmp_path: Path
    ) -> None:
        """Test normal mode doesn't show up-to-date repos."""
        mock_check_git.return_value = True

        result = ScanResult(scan_root=tmp_path)
        result.add_repository(tmp_path / "repo1")
        result.add_repository(tmp_path / "repo2")
        mock_scan.return_value = result

        async def update_side_effect(
            repo: RepoInfo, skip_dirty: bool = True, timeout: int = 60
        ) -> tuple[RepoInfo, RepoLogEntry]:
            if repo.name == "repo1":
                repo.status = RepoStatus.UP_TO_DATE
                status = "up_to_date"
            else:
                repo.status = RepoStatus.UPDATED
                repo.message = "Pulled 3 commits"
                status = "updated"
            repo_log = RepoLogEntry(path=str(repo.path), name=repo.name, status=status, duration_ms=100)
            return repo, repo_log

        mock_update.side_effect = update_side_effect

        runner = CliRunner()
        cli_result = runner.invoke(main, [str(tmp_path)])

        assert cli_result.exit_code == 0
        # Should show updated repo
        assert "repo2" in cli_result.output or "Updated" in cli_result.output or "Pulled" in cli_result.output


class TestCLIEdgeCases:
    """Tests for edge cases and error handling."""

    @patch("gittyup.cli.git_operations.check_git_installed")
    @patch("gittyup.cli.scanner.scan_directory")
    @patch("gittyup.cli.git_operations.async_update_repository_with_log")
    def test_unexpected_exception_handling(
        self, mock_update: MagicMock, mock_scan: MagicMock, mock_check_git: MagicMock, tmp_path: Path
    ) -> None:
        """Test handling of unexpected exceptions during update."""
        mock_check_git.return_value = True

        result = ScanResult(scan_root=tmp_path)
        repo = result.add_repository(tmp_path / "repo1")
        mock_scan.return_value = result

        # Raise unexpected exception - async version
        async def raise_error(repo: RepoInfo, skip_dirty: bool = True, timeout: int = 60):
            raise RuntimeError("Unexpected error")

        mock_update.side_effect = raise_error

        runner = CliRunner()
        cli_result = runner.invoke(main, [str(tmp_path)])

        # Should handle gracefully and exit with error
        assert cli_result.exit_code == 1
        assert repo.status == RepoStatus.ERROR
        assert "Unexpected error" in repo.error

    @patch("gittyup.cli.git_operations.check_git_installed")
    @patch("gittyup.cli.scanner.scan_directory")
    def test_single_repository_grammar(self, mock_scan: MagicMock, mock_check_git: MagicMock, tmp_path: Path) -> None:
        """Test correct grammar for single repository."""
        mock_check_git.return_value = True

        result = ScanResult(scan_root=tmp_path)
        result.add_repository(tmp_path / "repo1")
        mock_scan.return_value = result

        runner = CliRunner()
        cli_result = runner.invoke(main, ["--dry-run", str(tmp_path)])

        assert cli_result.exit_code == 0
        # Should say "repository" not "repositories"
        assert "1 git repository" in cli_result.output


class TestCLIIntegration:
    """Integration tests with real directory structures."""

    @patch("gittyup.cli.git_operations.check_git_installed")
    @patch("gittyup.cli.git_operations.async_update_repository_with_log")
    def test_real_directory_scan(self, mock_update: MagicMock, mock_check_git: MagicMock, tmp_path: Path) -> None:
        """Test with real directory structure."""
        mock_check_git.return_value = True

        # Create directory structure with git repos
        repo1 = tmp_path / "repo1"
        repo1.mkdir()
        (repo1 / ".git").mkdir()

        repo2 = tmp_path / "subdir" / "repo2"
        repo2.mkdir(parents=True)
        (repo2 / ".git").mkdir()

        # Mock update - async version
        async def update_side_effect(
            repo: RepoInfo, skip_dirty: bool = True, timeout: int = 60
        ) -> tuple[RepoInfo, RepoLogEntry]:
            repo.status = RepoStatus.UP_TO_DATE
            repo.message = "Already up to date"
            repo_log = RepoLogEntry(path=str(repo.path), name=repo.name, status="up_to_date", duration_ms=100)
            return repo, repo_log

        mock_update.side_effect = update_side_effect

        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_path)])

        assert result.exit_code == 0
        assert "Found 2 git" in result.output
        assert mock_update.call_count == 2


class TestCLIExplain:
    """Tests for --explain flag functionality."""

    @patch("gittyup.cli.LogManager")
    def test_explain_with_no_history(self, mock_log_manager_class: MagicMock, tmp_path: Path) -> None:
        """Test --explain when no history exists."""
        # Setup mock
        mock_log_manager = MagicMock()
        mock_log_manager_class.return_value.__enter__.return_value = mock_log_manager
        mock_log_manager.has_log.return_value = False

        runner = CliRunner()
        result = runner.invoke(main, ["--explain", str(tmp_path)])

        assert result.exit_code == 0
        assert "No history found" in result.output

    @patch("gittyup.cli.LogManager")
    def test_explain_with_history(self, mock_log_manager_class: MagicMock, tmp_path: Path) -> None:
        """Test --explain displays history correctly."""
        from gittyup.models import OperationLog

        # Create a mock operation log
        operation_log = OperationLog(
            timestamp="2025-10-15T14:23:45",
            scan_root=str(tmp_path),
            duration_seconds=2.34,
            dry_run=False,
            max_depth=None,
            exclude_patterns=[],
            total_repos=1,
            updated_repos=0,
            up_to_date_repos=1,
            skipped_repos=0,
            error_repos=0,
            repositories=[],
            gittyup_version="1.0.0",
            git_version="2.39.0",
            python_version="3.14.0",
            platform="Darwin",
        )

        # Setup mock
        mock_log_manager = MagicMock()
        mock_log_manager_class.return_value.__enter__.return_value = mock_log_manager
        mock_log_manager.has_log.return_value = True
        mock_log_manager.get_log.return_value = operation_log

        runner = CliRunner()
        result = runner.invoke(main, ["--explain", str(tmp_path)])

        assert result.exit_code == 0
        assert "Operation History" in result.output
        assert "Total repositories: 1" in result.output

    @patch("gittyup.cli.LogManager")
    def test_explain_with_failed_retrieval(self, mock_log_manager_class: MagicMock, tmp_path: Path) -> None:
        """Test --explain when log retrieval fails."""
        # Setup mock
        mock_log_manager = MagicMock()
        mock_log_manager_class.return_value.__enter__.return_value = mock_log_manager
        mock_log_manager.has_log.return_value = True
        mock_log_manager.get_log.return_value = None

        runner = CliRunner()
        result = runner.invoke(main, ["--explain", str(tmp_path)])

        assert result.exit_code == 1
        assert "Failed to retrieve operation log" in result.output


class TestCLILogging:
    """Tests for operation logging functionality."""

    @patch("gittyup.cli.LogManager")
    @patch("gittyup.cli.git_operations.check_git_installed")
    @patch("gittyup.cli.git_operations.async_update_repository_with_log")
    def test_log_saved_after_operation(
        self, mock_update: MagicMock, mock_check_git: MagicMock, mock_log_manager_class: MagicMock, tmp_path: Path
    ) -> None:
        """Test that logs are saved after normal operation."""
        mock_check_git.return_value = True

        # Create a git repo
        repo = tmp_path / "repo1"
        repo.mkdir()
        (repo / ".git").mkdir()

        # Mock update - async version
        async def update_side_effect(
            repo_info: RepoInfo, skip_dirty: bool = True, timeout: int = 60
        ) -> tuple[RepoInfo, RepoLogEntry]:
            repo_info.status = RepoStatus.UP_TO_DATE
            repo_log = RepoLogEntry(path=str(repo_info.path), name=repo_info.name, status="up_to_date", duration_ms=100)
            return repo_info, repo_log

        mock_update.side_effect = update_side_effect

        # Setup log manager mock
        mock_log_manager = MagicMock()
        mock_log_manager_class.return_value.__enter__.return_value = mock_log_manager

        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_path)])

        assert result.exit_code == 0
        # Verify that save_log was called
        mock_log_manager.save_log.assert_called_once()

    @patch("gittyup.cli.LogManager")
    @patch("gittyup.cli.git_operations.check_git_installed")
    @patch("gittyup.cli.git_operations.async_update_repository_with_log")
    def test_dry_run_does_not_save_log(
        self, mock_update: MagicMock, mock_check_git: MagicMock, mock_log_manager_class: MagicMock, tmp_path: Path
    ) -> None:
        """Test that dry runs don't save logs."""
        mock_check_git.return_value = True

        # Create a git repo
        repo = tmp_path / "repo1"
        repo.mkdir()
        (repo / ".git").mkdir()

        # Mock update - async version (not actually called in dry-run but needs to be here)
        async def update_side_effect(
            repo_info: RepoInfo, skip_dirty: bool = True, timeout: int = 60
        ) -> tuple[RepoInfo, RepoLogEntry]:
            repo_info.status = RepoStatus.UP_TO_DATE
            repo_log = RepoLogEntry(path=str(repo_info.path), name=repo_info.name, status="up_to_date", duration_ms=100)
            return repo_info, repo_log

        mock_update.side_effect = update_side_effect

        # Setup log manager mock
        mock_log_manager = MagicMock()
        mock_log_manager_class.return_value.__enter__.return_value = mock_log_manager

        runner = CliRunner()
        result = runner.invoke(main, ["--dry-run", str(tmp_path)])

        assert result.exit_code == 0
        # Verify that save_log was NOT called
        mock_log_manager.save_log.assert_not_called()

    @patch("gittyup.cli.LogManager")
    @patch("gittyup.cli.git_operations.check_git_installed")
    @patch("gittyup.cli.git_operations.async_update_repository_with_log")
    def test_logging_failure_does_not_crash(
        self, mock_update: MagicMock, mock_check_git: MagicMock, mock_log_manager_class: MagicMock, tmp_path: Path
    ) -> None:
        """Test that logging failures don't crash the application."""
        mock_check_git.return_value = True

        # Create a git repo
        repo = tmp_path / "repo1"
        repo.mkdir()
        (repo / ".git").mkdir()

        # Mock update - async version
        async def update_side_effect(
            repo_info: RepoInfo, skip_dirty: bool = True, timeout: int = 60
        ) -> tuple[RepoInfo, RepoLogEntry]:
            repo_info.status = RepoStatus.UP_TO_DATE
            repo_log = RepoLogEntry(path=str(repo_info.path), name=repo_info.name, status="up_to_date", duration_ms=100)
            return repo_info, repo_log

        mock_update.side_effect = update_side_effect

        # Setup log manager mock to raise exception
        mock_log_manager = MagicMock()
        mock_log_manager_class.return_value.__enter__.return_value = mock_log_manager
        mock_log_manager.save_log.side_effect = Exception("Disk full")

        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_path)])

        # Should still succeed despite logging failure
        assert result.exit_code == 0
        assert "Failed to save operation log" in result.output
