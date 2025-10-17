"""Tests for log persistence and management."""

from pathlib import Path

import pytest

from gittyup.logger import LogManager
from gittyup.models import CommitInfo, FileChange, OperationLog, RepoLogEntry


@pytest.fixture
def temp_cache_dir(tmp_path: Path, monkeypatch) -> Path:
    """Create a temporary cache directory for testing."""
    cache_dir = tmp_path / "test_cache"
    cache_dir.mkdir()

    # Mock platformdirs to use our temp directory
    monkeypatch.setattr("gittyup.logger.user_cache_dir", lambda app_name: str(cache_dir))

    return cache_dir


@pytest.fixture
def log_manager(temp_cache_dir: Path):
    """Create a LogManager instance for testing."""
    manager = LogManager()
    yield manager
    manager.close()


@pytest.fixture
def sample_operation_log() -> OperationLog:
    """Create a sample OperationLog for testing."""
    repo_entries = [
        RepoLogEntry(
            path="/home/user/projects/repo1",
            name="repo1",
            status="updated",
            duration_ms=500,
            branch="main",
            commits_pulled=2,
            files_changed=3,
            insertions=45,
            deletions=12,
            commits=[
                CommitInfo(
                    commit_hash="abc123d",
                    author="John Doe",
                    date="2025-10-15T10:00:00",
                    message="Add new feature",
                ),
                CommitInfo(
                    commit_hash="def456e",
                    author="Jane Smith",
                    date="2025-10-15T09:00:00",
                    message="Fix bug",
                ),
            ],
            files=[
                FileChange(path="src/main.py", change_type="modified", insertions=30, deletions=10),
                FileChange(path="src/utils.py", change_type="modified", insertions=10, deletions=2),
                FileChange(path="tests/test_main.py", change_type="added", insertions=5, deletions=0),
            ],
        ),
        RepoLogEntry(
            path="/home/user/projects/repo2",
            name="repo2",
            status="up_to_date",
            duration_ms=100,
            branch="develop",
        ),
        RepoLogEntry(
            path="/home/user/projects/repo3",
            name="repo3",
            status="skipped",
            duration_ms=50,
            skip_reason="Uncommitted changes",
            message="Repository has uncommitted changes",
        ),
    ]

    return OperationLog(
        timestamp="2025-10-15T14:23:45",
        scan_root="/home/user/projects",
        duration_seconds=2.5,
        dry_run=False,
        max_depth=3,
        exclude_patterns=["node_modules", "venv"],
        total_repos=3,
        updated_repos=1,
        up_to_date_repos=1,
        skipped_repos=1,
        error_repos=0,
        repositories=repo_entries,
        gittyup_version="1.0.0",
        git_version="2.39.0",
        python_version="3.14.0",
        platform="Darwin-25.0.0-arm64",
    )


class TestLogManagerInitialization:
    """Tests for LogManager initialization."""

    def test_log_manager_creates_cache_directory(self, log_manager: LogManager, temp_cache_dir: Path) -> None:
        """Test that LogManager creates the cache directory."""
        logs_dir = temp_cache_dir / "logs"
        assert logs_dir.exists()
        assert logs_dir.is_dir()

    def test_log_manager_has_cache(self, log_manager: LogManager) -> None:
        """Test that LogManager initializes with a cache."""
        assert log_manager.cache is not None


class TestLogManagerSaveAndRetrieve:
    """Tests for saving and retrieving logs."""

    def test_save_and_retrieve_log(
        self, log_manager: LogManager, sample_operation_log: OperationLog, tmp_path: Path
    ) -> None:
        """Test saving and retrieving a log."""
        scan_root = tmp_path / "projects"
        scan_root.mkdir()

        # Save the log
        log_manager.save_log(scan_root, sample_operation_log)

        # Retrieve the log
        retrieved_log = log_manager.get_log(scan_root)

        assert retrieved_log is not None
        assert retrieved_log.timestamp == sample_operation_log.timestamp
        assert retrieved_log.scan_root == sample_operation_log.scan_root
        assert retrieved_log.duration_seconds == sample_operation_log.duration_seconds
        assert retrieved_log.total_repos == sample_operation_log.total_repos
        assert len(retrieved_log.repositories) == 3

    def test_retrieve_nonexistent_log(self, log_manager: LogManager, tmp_path: Path) -> None:
        """Test retrieving a log that doesn't exist returns None."""
        scan_root = tmp_path / "nonexistent"

        retrieved_log = log_manager.get_log(scan_root)

        assert retrieved_log is None

    def test_save_replaces_existing_log(
        self, log_manager: LogManager, sample_operation_log: OperationLog, tmp_path: Path
    ) -> None:
        """Test that saving a log replaces an existing log."""
        scan_root = tmp_path / "projects"
        scan_root.mkdir()

        # Save first log
        log_manager.save_log(scan_root, sample_operation_log)

        # Create and save a second log with different data
        modified_log = OperationLog(
            timestamp="2025-10-15T15:00:00",
            scan_root=sample_operation_log.scan_root,
            duration_seconds=3.0,
            dry_run=False,
            max_depth=None,
            exclude_patterns=[],
            total_repos=5,
            updated_repos=2,
            up_to_date_repos=3,
            skipped_repos=0,
            error_repos=0,
        )
        log_manager.save_log(scan_root, modified_log)

        # Retrieve and verify it's the second log
        retrieved_log = log_manager.get_log(scan_root)

        assert retrieved_log is not None
        assert retrieved_log.timestamp == "2025-10-15T15:00:00"
        assert retrieved_log.total_repos == 5
        assert retrieved_log.duration_seconds == 3.0

    def test_save_log_resolves_path(
        self, log_manager: LogManager, sample_operation_log: OperationLog, tmp_path: Path
    ) -> None:
        """Test that paths are resolved when saving/retrieving logs."""
        scan_root = tmp_path / "projects"
        scan_root.mkdir()

        # Save with absolute path
        log_manager.save_log(scan_root, sample_operation_log)

        # Create a relative path (if in same directory)
        # Since we can't easily test relative paths in pytest, we'll test with symlinks if possible
        # For now, just verify absolute path works
        retrieved_log = log_manager.get_log(scan_root.resolve())

        assert retrieved_log is not None


class TestLogManagerHasLog:
    """Tests for checking if a log exists."""

    def test_has_log_returns_true_when_exists(
        self, log_manager: LogManager, sample_operation_log: OperationLog, tmp_path: Path
    ) -> None:
        """Test has_log returns True when log exists."""
        scan_root = tmp_path / "projects"
        scan_root.mkdir()

        log_manager.save_log(scan_root, sample_operation_log)

        assert log_manager.has_log(scan_root)

    def test_has_log_returns_false_when_not_exists(self, log_manager: LogManager, tmp_path: Path) -> None:
        """Test has_log returns False when log doesn't exist."""
        scan_root = tmp_path / "nonexistent"

        assert not log_manager.has_log(scan_root)


class TestLogManagerDeleteLog:
    """Tests for deleting logs."""

    def test_delete_existing_log(
        self, log_manager: LogManager, sample_operation_log: OperationLog, tmp_path: Path
    ) -> None:
        """Test deleting an existing log."""
        scan_root = tmp_path / "projects"
        scan_root.mkdir()

        # Save and verify log exists
        log_manager.save_log(scan_root, sample_operation_log)
        assert log_manager.has_log(scan_root)

        # Delete log
        result = log_manager.delete_log(scan_root)

        assert result
        assert not log_manager.has_log(scan_root)

    def test_delete_nonexistent_log(self, log_manager: LogManager, tmp_path: Path) -> None:
        """Test deleting a non-existent log returns False."""
        scan_root = tmp_path / "nonexistent"

        result = log_manager.delete_log(scan_root)

        assert not result


class TestLogManagerListDirectories:
    """Tests for listing logged directories."""

    def test_list_empty_when_no_logs(self, log_manager: LogManager) -> None:
        """Test list_logged_directories returns empty list when no logs exist."""
        directories = log_manager.list_logged_directories()

        assert isinstance(directories, list)
        assert len(directories) == 0

    def test_list_logged_directories(
        self, log_manager: LogManager, sample_operation_log: OperationLog, tmp_path: Path
    ) -> None:
        """Test listing all logged directories."""
        # Create and save multiple logs
        scan_root1 = tmp_path / "projects1"
        scan_root1.mkdir()
        scan_root2 = tmp_path / "projects2"
        scan_root2.mkdir()

        log_manager.save_log(scan_root1, sample_operation_log)
        log_manager.save_log(scan_root2, sample_operation_log)

        directories = log_manager.list_logged_directories()

        assert len(directories) == 2
        assert str(scan_root1.resolve()) in directories
        assert str(scan_root2.resolve()) in directories


class TestLogManagerCacheStats:
    """Tests for cache statistics."""

    def test_cache_stats_empty(self, log_manager: LogManager) -> None:
        """Test cache stats when cache is empty."""
        stats = log_manager.get_cache_stats()

        assert isinstance(stats, dict)
        assert "total_entries" in stats
        assert "size_bytes" in stats
        assert "cache_directory" in stats
        assert stats["total_entries"] == 0

    def test_cache_stats_with_data(
        self, log_manager: LogManager, sample_operation_log: OperationLog, tmp_path: Path
    ) -> None:
        """Test cache stats after adding data."""
        scan_root = tmp_path / "projects"
        scan_root.mkdir()

        log_manager.save_log(scan_root, sample_operation_log)

        stats = log_manager.get_cache_stats()

        assert stats["total_entries"] == 1
        assert stats["size_bytes"] > 0
        assert isinstance(stats["cache_directory"], str)


class TestLogManagerDeserialization:
    """Tests for log deserialization."""

    def test_deserialize_log_with_nested_objects(
        self, log_manager: LogManager, sample_operation_log: OperationLog, tmp_path: Path
    ) -> None:
        """Test that nested objects are properly deserialized."""
        scan_root = tmp_path / "projects"
        scan_root.mkdir()

        # Save log with nested commits and files
        log_manager.save_log(scan_root, sample_operation_log)

        # Retrieve and verify nested objects
        retrieved_log = log_manager.get_log(scan_root)

        assert retrieved_log is not None
        assert len(retrieved_log.repositories) == 3

        # Check first repository with commits and files
        repo1 = retrieved_log.repositories[0]
        assert repo1.name == "repo1"
        assert len(repo1.commits) == 2
        assert isinstance(repo1.commits[0], CommitInfo)
        assert repo1.commits[0].commit_hash == "abc123d"
        assert repo1.commits[0].author == "John Doe"

        assert len(repo1.files) == 3
        assert isinstance(repo1.files[0], FileChange)
        assert repo1.files[0].path == "src/main.py"
        assert repo1.files[0].change_type == "modified"

    def test_deserialize_log_with_empty_collections(self, log_manager: LogManager, tmp_path: Path) -> None:
        """Test deserialization with empty commits and files lists."""
        scan_root = tmp_path / "projects"
        scan_root.mkdir()

        # Create log with repository that has no commits or files
        simple_log = OperationLog(
            timestamp="2025-10-15T14:00:00",
            scan_root="/home/user/projects",
            duration_seconds=1.0,
            dry_run=False,
            max_depth=None,
            exclude_patterns=[],
            total_repos=1,
            updated_repos=0,
            up_to_date_repos=1,
            skipped_repos=0,
            error_repos=0,
            repositories=[
                RepoLogEntry(
                    path="/home/user/projects/repo1",
                    name="repo1",
                    status="up_to_date",
                    duration_ms=100,
                )
            ],
        )

        log_manager.save_log(scan_root, simple_log)
        retrieved_log = log_manager.get_log(scan_root)

        assert retrieved_log is not None
        assert len(retrieved_log.repositories) == 1
        assert len(retrieved_log.repositories[0].commits) == 0
        assert len(retrieved_log.repositories[0].files) == 0
