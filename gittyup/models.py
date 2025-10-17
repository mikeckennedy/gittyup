"""Data models for repository information and scan results."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class RepoStatus(str, Enum):
    """Status of a git repository."""

    PENDING = "pending"
    UP_TO_DATE = "up_to_date"
    UPDATED = "updated"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class RepoInfo:
    """Information about a discovered git repository."""

    path: Path
    name: str
    status: RepoStatus = RepoStatus.PENDING
    message: Optional[str] = None
    error: Optional[str] = None

    def __post_init__(self) -> None:
        """Ensure path is a Path object."""
        if not isinstance(self.path, Path):
            self.path = Path(self.path)


@dataclass
class ScanResult:
    """Results of scanning a directory tree for git repositories."""

    repositories: list[RepoInfo] = field(default_factory=list)
    skipped_paths: list[Path] = field(default_factory=list)
    errors: list[tuple[Path, str]] = field(default_factory=list)
    scan_root: Optional[Path] = None

    @property
    def total_repos(self) -> int:
        """Total number of repositories found."""
        return len(self.repositories)

    @property
    def has_errors(self) -> bool:
        """Check if any errors occurred during scanning."""
        return len(self.errors) > 0

    def add_repository(self, path: Path) -> RepoInfo:
        """Add a repository to the scan results."""
        repo = RepoInfo(path=path, name=path.name)
        self.repositories.append(repo)
        return repo

    def add_error(self, path: Path, error: str) -> None:
        """Add an error that occurred during scanning."""
        self.errors.append((path, error))

    def add_skipped_path(self, path: Path) -> None:
        """Add a path that was skipped during scanning."""
        self.skipped_paths.append(path)


# ============================================================================
# Logging and History Models
# ============================================================================


@dataclass
class FileChange:
    """Represents a single file change from git pull."""

    path: str  # Relative path to file
    change_type: str  # 'added', 'modified', 'deleted', 'renamed'
    insertions: int = 0  # Lines added
    deletions: int = 0  # Lines removed
    old_path: Optional[str] = None  # For renamed files


@dataclass
class CommitInfo:
    """Information about a commit pulled."""

    commit_hash: str  # Short hash (7 chars)
    author: str  # Commit author
    date: str  # ISO format date
    message: str  # First line of commit message


@dataclass
class UncommittedFile:
    """Represents an uncommitted file in a repository."""

    path: str  # Relative path to file
    status: str  # Status code from git (M, A, D, R, ??, etc.)
    status_description: str  # Human-readable status


@dataclass
class RepoLogEntry:
    """Detailed log entry for a single repository operation."""

    path: str  # Absolute path to repository
    name: str  # Repository name (directory name)
    status: str  # 'up_to_date', 'updated', 'skipped', 'error'

    # Timing
    duration_ms: int  # How long the operation took

    # Status details
    message: Optional[str] = None  # User-friendly status message
    error: Optional[str] = None  # Error message if applicable

    # Git details (for successful pulls)
    branch: Optional[str] = None  # Current branch name
    commits_pulled: int = 0  # Number of commits pulled
    files_changed: int = 0  # Number of files changed
    insertions: int = 0  # Total lines added
    deletions: int = 0  # Total lines removed

    # Detailed change information
    commits: list[CommitInfo] = field(default_factory=list)
    files: list[FileChange] = field(default_factory=list)

    # Skip/Error details
    skip_reason: Optional[str] = None  # Why repo was skipped
    error_details: Optional[str] = None  # Full error message/traceback
    git_output: Optional[str] = None  # Raw git command output
    uncommitted_files: list[UncommittedFile] = field(default_factory=list)  # Files with uncommitted changes


@dataclass
class OperationLog:
    """Complete log of a gittyup operation."""

    # Operation metadata
    timestamp: str  # ISO 8601 timestamp
    scan_root: str  # Absolute path scanned
    duration_seconds: float  # Total operation time

    # Operation parameters
    dry_run: bool
    max_depth: Optional[int]
    exclude_patterns: list[str]

    # Summary statistics
    total_repos: int
    updated_repos: int
    up_to_date_repos: int
    skipped_repos: int
    error_repos: int

    # Detailed repository logs
    repositories: list[RepoLogEntry] = field(default_factory=list)

    # System info
    gittyup_version: str = ""
    git_version: str = ""
    python_version: str = ""
    platform: str = ""  # OS info
