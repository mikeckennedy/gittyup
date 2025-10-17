"""Persistent logging for git operations using diskcache."""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from diskcache import Cache
from platformdirs import user_cache_dir

from gittyup.models import CommitInfo, FileChange, OperationLog, RepoLogEntry, UncommittedFile


class LogManager:
    """Manages persistent operation logs."""

    def __init__(self):
        """Initialize the log manager with cache directory."""
        cache_dir = Path(user_cache_dir("gittyup")) / "logs"
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = Cache(str(cache_dir))

    def close(self) -> None:
        """Close the cache connection."""
        if self.cache is not None:
            self.cache.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

    def save_log(self, scan_root: Path, log: OperationLog) -> None:
        """
        Save an operation log for a specific directory.

        Args:
            scan_root: Absolute path of the scanned directory
            log: Complete operation log to save
        """
        key = str(scan_root.resolve())
        log_json = json.dumps(asdict(log), indent=2)
        self.cache.set(key, log_json)

    def get_log(self, scan_root: Path) -> Optional[OperationLog]:
        """
        Retrieve the operation log for a specific directory.

        Args:
            scan_root: Absolute path of the scanned directory

        Returns:
            OperationLog if found, None otherwise
        """
        key = str(scan_root.resolve())
        log_json = self.cache.get(key)

        if log_json is None:
            return None

        log_dict = json.loads(log_json)
        return self._deserialize_log(log_dict)

    def has_log(self, scan_root: Path) -> bool:
        """Check if a log exists for the given directory."""
        key = str(scan_root.resolve())
        return key in self.cache

    def delete_log(self, scan_root: Path) -> bool:
        """Delete the log for a specific directory."""
        key = str(scan_root.resolve())
        return self.cache.delete(key)

    def list_logged_directories(self) -> list[str]:
        """Return list of all directories that have logs."""
        return list(self.cache.iterkeys())

    def get_cache_stats(self) -> dict:
        """Get cache statistics (size, count, etc)."""
        return {
            "total_entries": len(self.cache),
            "size_bytes": self.cache.volume(),
            "cache_directory": str(self.cache.directory),
        }

    @staticmethod
    def _deserialize_log(log_dict: dict) -> OperationLog:
        """Convert dictionary back to OperationLog with nested objects."""
        # Reconstruct nested objects for repositories
        repositories = []
        for repo_dict in log_dict.get("repositories", []):
            # Reconstruct commits
            commits = [CommitInfo(**commit_dict) for commit_dict in repo_dict.get("commits", [])]

            # Reconstruct files
            files = [FileChange(**file_dict) for file_dict in repo_dict.get("files", [])]

            # Reconstruct uncommitted files
            uncommitted_files = [UncommittedFile(**file_dict) for file_dict in repo_dict.get("uncommitted_files", [])]

            # Create RepoLogEntry with reconstructed nested objects
            repo_dict["commits"] = commits
            repo_dict["files"] = files
            repo_dict["uncommitted_files"] = uncommitted_files
            repositories.append(RepoLogEntry(**repo_dict))

        # Create OperationLog with reconstructed repositories
        log_dict["repositories"] = repositories
        return OperationLog(**log_dict)
