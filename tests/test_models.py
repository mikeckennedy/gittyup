"""Tests for data models including logging models."""

import json
from dataclasses import asdict

from gittyup.models import (
    CommitInfo,
    FileChange,
    OperationLog,
    RepoLogEntry,
    UncommittedFile,
)


class TestFileChange:
    """Tests for FileChange dataclass."""

    def test_file_change_creation(self) -> None:
        """Test basic FileChange creation."""
        file_change = FileChange(
            path="src/main.py",
            change_type="modified",
            insertions=10,
            deletions=5,
        )

        assert file_change.path == "src/main.py"
        assert file_change.change_type == "modified"
        assert file_change.insertions == 10
        assert file_change.deletions == 5
        assert file_change.old_path is None

    def test_file_change_renamed(self) -> None:
        """Test FileChange for renamed files."""
        file_change = FileChange(
            path="src/new_name.py",
            change_type="renamed",
            old_path="src/old_name.py",
        )

        assert file_change.path == "src/new_name.py"
        assert file_change.change_type == "renamed"
        assert file_change.old_path == "src/old_name.py"
        assert file_change.insertions == 0
        assert file_change.deletions == 0

    def test_file_change_serialization(self) -> None:
        """Test FileChange can be serialized to dict/JSON."""
        file_change = FileChange(
            path="test.py",
            change_type="added",
            insertions=100,
        )

        as_dict = asdict(file_change)
        assert isinstance(as_dict, dict)
        assert as_dict["path"] == "test.py"
        assert as_dict["change_type"] == "added"

        # Test JSON serialization
        json_str = json.dumps(as_dict)
        assert isinstance(json_str, str)
        loaded = json.loads(json_str)
        assert loaded["path"] == "test.py"


class TestUncommittedFile:
    """Tests for UncommittedFile dataclass."""

    def test_uncommitted_file_creation(self) -> None:
        """Test basic UncommittedFile creation."""
        file = UncommittedFile(
            path="src/modified.py",
            status="M",
            status_description="Modified",
        )

        assert file.path == "src/modified.py"
        assert file.status == "M"
        assert file.status_description == "Modified"

    def test_uncommitted_file_untracked(self) -> None:
        """Test UncommittedFile for untracked files."""
        file = UncommittedFile(
            path="new_file.py",
            status="??",
            status_description="Untracked",
        )

        assert file.path == "new_file.py"
        assert file.status == "??"
        assert file.status_description == "Untracked"

    def test_uncommitted_file_serialization(self) -> None:
        """Test UncommittedFile can be serialized to dict/JSON."""
        file = UncommittedFile(
            path="deleted.py",
            status="D",
            status_description="Deleted",
        )

        as_dict = asdict(file)
        assert isinstance(as_dict, dict)
        assert as_dict["path"] == "deleted.py"
        assert as_dict["status"] == "D"
        assert as_dict["status_description"] == "Deleted"

        # Test JSON serialization
        json_str = json.dumps(as_dict)
        assert isinstance(json_str, str)
        loaded = json.loads(json_str)
        assert loaded["path"] == "deleted.py"


class TestCommitInfo:
    """Tests for CommitInfo dataclass."""

    def test_commit_info_creation(self) -> None:
        """Test basic CommitInfo creation."""
        commit = CommitInfo(
            commit_hash="abc123d",
            author="John Doe",
            date="2025-10-15T10:00:00",
            message="Add new feature",
        )

        assert commit.commit_hash == "abc123d"
        assert commit.author == "John Doe"
        assert commit.date == "2025-10-15T10:00:00"
        assert commit.message == "Add new feature"

    def test_commit_info_serialization(self) -> None:
        """Test CommitInfo can be serialized to dict/JSON."""
        commit = CommitInfo(
            commit_hash="def456e",
            author="Jane Smith",
            date="2025-10-15T11:00:00",
            message="Fix bug in authentication",
        )

        as_dict = asdict(commit)
        assert isinstance(as_dict, dict)
        assert as_dict["commit_hash"] == "def456e"

        # Test JSON serialization
        json_str = json.dumps(as_dict)
        assert isinstance(json_str, str)
        loaded = json.loads(json_str)
        assert loaded["author"] == "Jane Smith"


class TestRepoLogEntry:
    """Tests for RepoLogEntry dataclass."""

    def test_repo_log_entry_minimal(self) -> None:
        """Test RepoLogEntry with minimal fields."""
        entry = RepoLogEntry(
            path="/home/user/projects/my-repo",
            name="my-repo",
            status="up_to_date",
            duration_ms=123,
        )

        assert entry.path == "/home/user/projects/my-repo"
        assert entry.name == "my-repo"
        assert entry.status == "up_to_date"
        assert entry.duration_ms == 123
        assert entry.message is None
        assert entry.error is None
        assert entry.branch is None
        assert entry.commits_pulled == 0
        assert len(entry.commits) == 0
        assert len(entry.files) == 0

    def test_repo_log_entry_updated(self) -> None:
        """Test RepoLogEntry for an updated repository."""
        commits = [
            CommitInfo(
                commit_hash="abc123d",
                author="John Doe",
                date="2025-10-15T10:00:00",
                message="Update feature",
            )
        ]

        files = [FileChange(path="src/main.py", change_type="modified", insertions=10, deletions=5)]

        entry = RepoLogEntry(
            path="/home/user/projects/my-repo",
            name="my-repo",
            status="updated",
            duration_ms=456,
            branch="main",
            commits_pulled=1,
            files_changed=1,
            insertions=10,
            deletions=5,
            commits=commits,
            files=files,
        )

        assert entry.status == "updated"
        assert entry.branch == "main"
        assert entry.commits_pulled == 1
        assert entry.files_changed == 1
        assert entry.insertions == 10
        assert entry.deletions == 5
        assert len(entry.commits) == 1
        assert len(entry.files) == 1

    def test_repo_log_entry_skipped(self) -> None:
        """Test RepoLogEntry for a skipped repository."""
        entry = RepoLogEntry(
            path="/home/user/projects/my-repo",
            name="my-repo",
            status="skipped",
            duration_ms=89,
            skip_reason="Repository has uncommitted changes",
            message="Skipped due to uncommitted changes",
        )

        assert entry.status == "skipped"
        assert entry.skip_reason == "Repository has uncommitted changes"
        assert entry.message == "Skipped due to uncommitted changes"

    def test_repo_log_entry_error(self) -> None:
        """Test RepoLogEntry for an error."""
        entry = RepoLogEntry(
            path="/home/user/projects/my-repo",
            name="my-repo",
            status="error",
            duration_ms=234,
            error="Git pull failed",
            error_details="fatal: unable to access repository",
        )

        assert entry.status == "error"
        assert entry.error == "Git pull failed"
        assert entry.error_details == "fatal: unable to access repository"

    def test_repo_log_entry_serialization(self) -> None:
        """Test RepoLogEntry can be serialized to dict/JSON."""
        commits = [
            CommitInfo(
                commit_hash="abc123d",
                author="John Doe",
                date="2025-10-15T10:00:00",
                message="Test commit",
            )
        ]

        files = [FileChange(path="test.py", change_type="added", insertions=50)]

        entry = RepoLogEntry(
            path="/home/user/projects/test",
            name="test",
            status="updated",
            duration_ms=300,
            commits=commits,
            files=files,
        )

        as_dict = asdict(entry)
        assert isinstance(as_dict, dict)
        assert as_dict["path"] == "/home/user/projects/test"
        assert isinstance(as_dict["commits"], list)
        assert isinstance(as_dict["files"], list)

        # Test JSON serialization
        json_str = json.dumps(as_dict)
        assert isinstance(json_str, str)


class TestOperationLog:
    """Tests for OperationLog dataclass."""

    def test_operation_log_minimal(self) -> None:
        """Test OperationLog with minimal fields."""
        log = OperationLog(
            timestamp="2025-10-15T14:00:00",
            scan_root="/home/user/projects",
            duration_seconds=2.5,
            dry_run=False,
            max_depth=None,
            exclude_patterns=[],
            total_repos=5,
            updated_repos=1,
            up_to_date_repos=3,
            skipped_repos=1,
            error_repos=0,
        )

        assert log.timestamp == "2025-10-15T14:00:00"
        assert log.scan_root == "/home/user/projects"
        assert log.duration_seconds == 2.5
        assert not log.dry_run
        assert log.max_depth is None
        assert log.exclude_patterns == []
        assert log.total_repos == 5
        assert log.updated_repos == 1
        assert log.up_to_date_repos == 3
        assert log.skipped_repos == 1
        assert log.error_repos == 0
        assert len(log.repositories) == 0

    def test_operation_log_with_repositories(self) -> None:
        """Test OperationLog with repository entries."""
        repo_entries = [
            RepoLogEntry(
                path="/home/user/projects/repo1",
                name="repo1",
                status="updated",
                duration_ms=500,
            ),
            RepoLogEntry(
                path="/home/user/projects/repo2",
                name="repo2",
                status="up_to_date",
                duration_ms=100,
            ),
        ]

        log = OperationLog(
            timestamp="2025-10-15T14:00:00",
            scan_root="/home/user/projects",
            duration_seconds=2.5,
            dry_run=False,
            max_depth=3,
            exclude_patterns=["node_modules", "venv"],
            total_repos=2,
            updated_repos=1,
            up_to_date_repos=1,
            skipped_repos=0,
            error_repos=0,
            repositories=repo_entries,
            gittyup_version="1.0.0",
            git_version="2.39.0",
            python_version="3.14.0",
            platform="Darwin-25.0.0-arm64",
        )

        assert log.max_depth == 3
        assert len(log.exclude_patterns) == 2
        assert len(log.repositories) == 2
        assert log.gittyup_version == "1.0.0"
        assert log.git_version == "2.39.0"
        assert log.python_version == "3.14.0"
        assert log.platform == "Darwin-25.0.0-arm64"

    def test_operation_log_serialization(self) -> None:
        """Test OperationLog can be serialized to dict/JSON."""
        repo_entries = [
            RepoLogEntry(
                path="/home/user/projects/repo1",
                name="repo1",
                status="updated",
                duration_ms=500,
                commits=[
                    CommitInfo(
                        commit_hash="abc123d",
                        author="John Doe",
                        date="2025-10-15T10:00:00",
                        message="Test",
                    )
                ],
            )
        ]

        log = OperationLog(
            timestamp="2025-10-15T14:00:00",
            scan_root="/home/user/projects",
            duration_seconds=2.5,
            dry_run=False,
            max_depth=None,
            exclude_patterns=[],
            total_repos=1,
            updated_repos=1,
            up_to_date_repos=0,
            skipped_repos=0,
            error_repos=0,
            repositories=repo_entries,
        )

        as_dict = asdict(log)
        assert isinstance(as_dict, dict)
        assert as_dict["scan_root"] == "/home/user/projects"
        assert isinstance(as_dict["repositories"], list)
        assert len(as_dict["repositories"]) == 1

        # Test JSON serialization
        json_str = json.dumps(as_dict, indent=2)
        assert isinstance(json_str, str)
        loaded = json.loads(json_str)
        assert loaded["total_repos"] == 1
        assert loaded["repositories"][0]["name"] == "repo1"
