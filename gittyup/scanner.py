"""Directory traversal and git repository detection."""

from pathlib import Path
from typing import Optional

from gittyup.models import ScanResult

# Default directories to exclude from scanning
DEFAULT_EXCLUDE_DIRS = {
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "__pycache__",
    ".tox",
    ".nox",
    "dist",
    "build",
    ".eggs",
    "eggs",
    ".git",  # Don't traverse into .git directories themselves
    ".svn",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "htmlcov",
    "coverage",
    ".idea",
    ".vscode",
    "target",  # Rust/Java build directories
    "vendor",  # Go/PHP dependencies
}


def is_git_repository(path: Path) -> bool:
    """
    Check if a directory is a git repository.

    Args:
        path: Directory path to check

    Returns:
        True if the directory contains a .git subdirectory
    """
    if not path.is_dir():
        return False

    git_dir = path / ".git"
    return git_dir.exists() and git_dir.is_dir()


def should_exclude_directory(path: Path, exclude_patterns: Optional[set[str]] = None) -> bool:
    """
    Determine if a directory should be excluded from scanning.

    Args:
        path: Directory path to check
        exclude_patterns: Additional patterns to exclude (merged with defaults)

    Returns:
        True if the directory should be excluded
    """
    exclude = exclude_patterns or set()
    all_excludes = DEFAULT_EXCLUDE_DIRS | exclude

    return path.name in all_excludes


def scan_directory(
    root_path: Path | str,
    exclude_patterns: Optional[set[str]] = None,
    max_depth: Optional[int] = None,
) -> ScanResult:
    """
    Recursively scan a directory tree for git repositories.

    Args:
        root_path: Root directory to start scanning from
        exclude_patterns: Additional directory names to exclude from scanning
        max_depth: Maximum depth to traverse (None for unlimited)

    Returns:
        ScanResult containing all discovered repositories and any errors

    Example:
        >>> result = scan_directory(Path.home() / "projects")
        >>> print(f"Found {result.total_repos} repositories")
        >>> for repo in result.repositories:
        ...     print(repo.path)
    """
    root = Path(root_path).resolve()
    result = ScanResult(scan_root=root)

    if not root.exists():
        result.add_error(root, "Path does not exist")
        return result

    if not root.is_dir():
        result.add_error(root, "Path is not a directory")
        return result

    _scan_recursive(root, result, exclude_patterns, max_depth, current_depth=0)
    return result


def _scan_recursive(
    path: Path,
    result: ScanResult,
    exclude_patterns: Optional[set[str]],
    max_depth: Optional[int],
    current_depth: int,
    visited: Optional[set[Path]] = None,
) -> None:
    """
    Internal recursive function to scan directories.

    Args:
        path: Current directory to scan
        result: ScanResult object to populate
        exclude_patterns: Directory names to exclude
        max_depth: Maximum depth to traverse
        current_depth: Current recursion depth
        visited: Set of visited paths (for cycle detection)
    """
    if visited is None:
        visited = set()

    # Resolve symlinks and check for cycles
    try:
        resolved_path = path.resolve(strict=True)
    except (OSError, RuntimeError) as e:
        result.add_error(path, f"Cannot resolve path: {e}")
        return

    # Check for circular references
    if resolved_path in visited:
        return

    visited.add(resolved_path)

    # Check max depth
    if max_depth is not None and current_depth > max_depth:
        return

    # Check if current directory is a git repository
    if is_git_repository(path):
        result.add_repository(path)
        # Don't traverse into git repositories
        return

    # Traverse subdirectories
    try:
        entries = list(path.iterdir())
    except PermissionError:
        result.add_error(path, "Permission denied")
        return
    except OSError as e:
        result.add_error(path, f"Error reading directory: {e}")
        return

    for entry in entries:
        # Handle symlinks first (before is_dir check, as broken symlinks return False for is_dir)
        if entry.is_symlink():
            try:
                # Check if symlink target exists and is a directory
                resolved = entry.resolve(strict=True)
                if not resolved.is_dir():
                    continue  # Skip symlinks to files
            except (OSError, RuntimeError):
                # Broken symlink - skip it
                result.add_skipped_path(entry)
                continue

        # Skip non-directories
        if not entry.is_dir():
            continue

        # Check if directory should be excluded
        if should_exclude_directory(entry, exclude_patterns):
            result.add_skipped_path(entry)
            continue

        # Recursively scan subdirectory
        _scan_recursive(
            entry,
            result,
            exclude_patterns,
            max_depth,
            current_depth + 1,
            visited,
        )


def find_repositories(
    root_path: Path | str,
    exclude_patterns: Optional[set[str]] = None,
    max_depth: Optional[int] = None,
) -> list[Path]:
    """
    Convenience function to get just the list of repository paths.

    Args:
        root_path: Root directory to start scanning from
        exclude_patterns: Additional directory names to exclude
        max_depth: Maximum depth to traverse

    Returns:
        List of paths to git repositories

    Example:
        >>> repos = find_repositories(Path.home() / "projects")
        >>> for repo in repos:
        ...     print(repo.name)
    """
    result = scan_directory(root_path, exclude_patterns, max_depth)
    return [repo.path for repo in result.repositories]
