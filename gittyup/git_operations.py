"""Git pull operations and status handling."""

import asyncio
import re
import subprocess
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from colorama import Fore, Style

from gittyup.models import CommitInfo, FileChange, RepoInfo, RepoLogEntry, RepoStatus, UncommittedFile


class GitError(Exception):
    """Base exception for git-related errors."""

    pass


class GitCommandError(GitError):
    """Exception raised when a git command fails."""

    pass


class GitTimeoutError(GitError):
    """Exception raised when a git command times out."""

    pass


@dataclass
class PullResult:
    """Detailed result of a git pull operation."""

    success: bool
    already_up_to_date: bool
    error_message: Optional[str] = None
    error_details: Optional[str] = None
    full_output: Optional[str] = None

    # Pull statistics
    commits_count: int = 0
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0

    # Detailed change information
    commits: list[CommitInfo] = field(default_factory=list)
    files: list[FileChange] = field(default_factory=list)
    old_commit: Optional[str] = None
    new_commit: Optional[str] = None


def _run_git_command(
    command: list[str],
    cwd: Path | None = None,
    timeout: int = 10,
) -> subprocess.CompletedProcess[str]:
    """
    Helper function to run a git command with consistent parameters.

    Args:
        command: Git command and arguments (including 'git')
        cwd: Working directory for the command
        timeout: Command timeout in seconds

    Returns:
        CompletedProcess with the result

    Raises:
        subprocess.TimeoutExpired: If command times out
        subprocess.SubprocessError: If command fails to execute
    """
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def check_git_installed() -> bool:
    """
    Check if git is installed and available on the system.

    Returns:
        bool: True if git is installed, False otherwise.
    """
    try:
        result = _run_git_command(["git", "--version"], timeout=5)
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def get_repo_status(repo_path: Path, timeout: int = 10) -> dict[str, bool]:
    """
    Get the status of a git repository.

    Args:
        repo_path: Path to the git repository
        timeout: Command timeout in seconds

    Returns:
        dict with status flags:
            - has_remote: Repository has a remote configured
            - is_clean: Working directory is clean (no uncommitted changes)
            - is_detached: HEAD is detached
            - has_upstream: Current branch has upstream configured

    Raises:
        GitCommandError: If git status command fails
        GitTimeoutError: If command times out
    """
    status = {
        "has_remote": False,
        "is_clean": False,
        "is_detached": False,
        "has_upstream": False,
    }

    try:
        # Check for remotes
        remote_result = _run_git_command(["git", "remote"], cwd=repo_path, timeout=timeout)
        status["has_remote"] = bool(remote_result.stdout.strip())

        # Check if working directory is clean (filtering out always-ignored files)
        uncommitted_files = get_uncommitted_files(repo_path, timeout=timeout)
        relevant_files = [f for f in uncommitted_files if not should_ignore_file(f.path)]
        status["is_clean"] = len(relevant_files) == 0

        # Check if HEAD is detached
        branch_result = _run_git_command(["git", "symbolic-ref", "-q", "HEAD"], cwd=repo_path, timeout=timeout)
        status["is_detached"] = branch_result.returncode != 0

        # Check if current branch has upstream (only if not detached)
        if not status["is_detached"]:
            upstream_result = _run_git_command(
                ["git", "rev-parse", "--abbrev-ref", "@{upstream}"],
                cwd=repo_path,
                timeout=timeout,
            )
            status["has_upstream"] = upstream_result.returncode == 0

    except subprocess.TimeoutExpired as e:
        raise GitTimeoutError(f"Git status check timed out after {timeout} seconds") from e
    except subprocess.SubprocessError as e:
        raise GitCommandError(f"Failed to check git status: {e}") from e

    return status


def get_current_branch(repo_path: Path, timeout: int = 10) -> Optional[str]:
    """
    Get the current branch name.

    Args:
        repo_path: Path to the git repository
        timeout: Command timeout in seconds

    Returns:
        Branch name or None if detached HEAD
    """
    try:
        result = _run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path, timeout=timeout)
        if result.returncode == 0:
            branch = result.stdout.strip()
            return None if branch == "HEAD" else branch
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        pass
    return None


def get_uncommitted_files(repo_path: Path, timeout: int = 10) -> list[UncommittedFile]:
    """
    Get the list of uncommitted files in the repository.

    Uses git status --porcelain to get file status information.

    Args:
        repo_path: Path to the git repository
        timeout: Command timeout in seconds

    Returns:
        List of UncommittedFile objects with status information
    """
    status_descriptions = {
        "M": "Modified",
        "A": "Added",
        "D": "Deleted",
        "R": "Renamed",
        "C": "Copied",
        "U": "Updated but unmerged",
        "?": "Untracked",
        "!": "Ignored",
    }

    try:
        result = _run_git_command(["git", "status", "--porcelain"], cwd=repo_path, timeout=timeout)

        if result.returncode != 0:
            return []

        uncommitted_files = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            # Porcelain format: XY filename
            # X = index status, Y = working tree status
            # Examples: " M file.txt", "M  file.txt", "?? file.txt"
            if len(line) < 3:
                continue

            # The status is always the first 2 characters
            # Then there's at least one space/tab, then the filename
            status_code = line[:2]
            # Skip status and any whitespace to get the filename
            file_path = line[2:].lstrip()

            # Determine the effective status (prioritize index status, then working tree)
            x_status = status_code[0].strip()
            y_status = status_code[1].strip()

            # For display, we'll show the most significant status
            if x_status and x_status != " ":
                main_status = x_status
                status_desc = "Untracked" if main_status == "?" else status_descriptions.get(main_status, "Modified")
            elif y_status and y_status != " ":
                main_status = y_status
                if main_status == "?":
                    status_desc = "Untracked"
                else:
                    status_desc = f"{status_descriptions.get(main_status, 'Modified')} (unstaged)"
            else:
                main_status = "M"
                status_desc = "Modified"

            # Handle special case for untracked files
            if status_code == "??":
                main_status = "?"
                status_desc = "Untracked"

            uncommitted_files.append(
                UncommittedFile(
                    path=file_path,
                    status=status_code.strip() or main_status,
                    status_description=status_desc,
                )
            )

        return uncommitted_files

    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        return []


# Files and directories that should always be ignored when checking for uncommitted changes
# These are common working files that don't indicate actual repository changes
ALWAYS_IGNORED_FILES = {
    ".DS_Store",  # macOS
    "Thumbs.db",  # Windows
    "__pycache__",  # Python
}


def should_ignore_file(file_path: str) -> bool:
    """
    Check if a file should be ignored when considering uncommitted changes.

    Args:
        file_path: Path to the file (can be relative)

    Returns:
        True if the file should always be ignored
    """
    # Check if the file name matches any ignored files
    file_name = Path(file_path).name
    if file_name in ALWAYS_IGNORED_FILES:
        return True

    # Check if any component of the path matches ignored directories
    path_parts = Path(file_path).parts
    return any(part in ALWAYS_IGNORED_FILES for part in path_parts)


def has_only_untracked_files(uncommitted_files: list[UncommittedFile]) -> bool:
    """
    Check if the uncommitted files are only untracked files.

    Args:
        uncommitted_files: List of UncommittedFile objects

    Returns:
        True if all files are untracked, False if there are any staged/modified files
    """
    if not uncommitted_files:
        return True  # No uncommitted files at all

    # Filter out files that should always be ignored
    relevant_files = [f for f in uncommitted_files if not should_ignore_file(f.path)]

    # If no relevant files remain after filtering, treat as clean
    if not relevant_files:
        return True

    # Check if all remaining files have status "??" (untracked)
    return all(file.status == "??" or file.status == "?" for file in relevant_files)


def check_for_pull_conflicts(repo_path: Path, timeout: int = 10) -> tuple[bool, Optional[str]]:
    """
    Check if a git pull would cause conflicts with untracked files.

    This performs the safety check suggested in GitHub issue #2:
    1. Fetch from origin
    2. Check if any files that would be pulled conflict with local untracked files

    Args:
        repo_path: Path to the git repository
        timeout: Command timeout in seconds

    Returns:
        tuple of (is_safe: bool, error_message: Optional[str])
        - is_safe is True if pull is safe to proceed
        - error_message is set if there's a conflict or error
    """
    try:
        # First, fetch from origin to get the latest refs
        fetch_result = _run_git_command(["git", "fetch"], cwd=repo_path, timeout=timeout)
        if fetch_result.returncode != 0:
            return False, f"Failed to fetch: {fetch_result.stderr.strip()}"

        # Get current branch
        branch = get_current_branch(repo_path, timeout=timeout)
        if not branch:
            return False, "Cannot determine current branch"

        # Get the upstream branch
        upstream_result = _run_git_command(
            ["git", "rev-parse", "--abbrev-ref", "@{upstream}"],
            cwd=repo_path,
            timeout=timeout,
        )
        if upstream_result.returncode != 0:
            return False, "No upstream branch configured"

        upstream = upstream_result.stdout.strip()

        # Check what files would change if we pulled
        # Use git diff --name-status to see what would be updated
        diff_result = _run_git_command(
            ["git", "diff", "--name-status", "HEAD", upstream],
            cwd=repo_path,
            timeout=timeout,
        )

        if diff_result.returncode != 0:
            return False, f"Failed to check differences: {diff_result.stderr.strip()}"

        # If there are no differences, it's safe
        if not diff_result.stdout.strip():
            return True, None

        # Get list of files that would be changed by pull
        files_to_pull = set()
        for line in diff_result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t", 2)
            if len(parts) >= 2:
                # Format is: STATUS\tFILENAME or STATUS\tOLDNAME\tNEWNAME (for renames)
                if len(parts) == 3:
                    # Rename case - check both old and new names
                    files_to_pull.add(parts[1])
                    files_to_pull.add(parts[2])
                else:
                    files_to_pull.add(parts[1])

        # Get list of untracked files
        uncommitted_files = get_uncommitted_files(repo_path, timeout=timeout)
        untracked_files = {file.path for file in uncommitted_files if file.status == "??" or file.status == "?"}

        # Check for conflicts
        conflicts = files_to_pull & untracked_files
        if conflicts:
            conflict_list = ", ".join(sorted(list(conflicts)[:3]))  # Show first 3
            if len(conflicts) > 3:
                conflict_list += f", ... ({len(conflicts)} total)"
            return False, f"Untracked files would be overwritten: {conflict_list}"

        # No conflicts found, safe to pull
        return True, None

    except subprocess.TimeoutExpired:
        return False, "Timeout while checking for conflicts"
    except Exception as e:
        return False, f"Error checking for conflicts: {e}"


def get_git_version() -> str:
    """
    Get the git version string.

    Returns:
        Git version or 'unknown' if not available
    """
    try:
        result = _run_git_command(["git", "--version"], timeout=5)
        if result.returncode == 0:
            # Output is like "git version 2.39.0"
            return result.stdout.strip().replace("git version ", "")
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return "unknown"


def _parse_git_pull_output(output: str) -> dict:
    """
    Parse git pull output to extract basic change statistics.

    Parses output like:
        Updating abc123..def456
        Fast-forward
         src/main.py           | 23 ++++++++++++---
         tests/test_main.py    |  5 ++++
         2 files changed, 24 insertions(+), 4 deletions(-)

    Args:
        output: Git pull output text

    Returns:
        dict with parsed information: {
            'old_commit': str | None,
            'new_commit': str | None,
            'files_changed': int,
            'insertions': int,
            'deletions': int
        }
    """
    result: dict = {
        "old_commit": None,
        "new_commit": None,
        "files_changed": 0,
        "insertions": 0,
        "deletions": 0,
    }

    # Extract commit hashes from "Updating abc123..def456"
    commit_match = re.search(r"Updating\s+([0-9a-f]+)\.\.([0-9a-f]+)", output)
    if commit_match:
        result["old_commit"] = commit_match.group(1)
        result["new_commit"] = commit_match.group(2)

    # Extract file statistics from "X files changed, Y insertions(+), Z deletions(-)"
    stats_match = re.search(
        r"(\d+)\s+files?\s+changed(?:,\s+(\d+)\s+insertions?\(\+\))?(?:,\s+(\d+)\s+deletions?\(-\))?", output
    )
    if stats_match:
        result["files_changed"] = int(stats_match.group(1))
        result["insertions"] = int(stats_match.group(2) or 0)
        result["deletions"] = int(stats_match.group(3) or 0)

    return result


def _get_commit_details(repo_path: Path, old_hash: str, new_hash: str, timeout: int = 10) -> list[CommitInfo]:
    """
    Get detailed commit information for commits between two refs.

    Args:
        repo_path: Path to the git repository
        old_hash: Starting commit hash
        new_hash: Ending commit hash
        timeout: Command timeout in seconds

    Returns:
        List of CommitInfo objects
    """
    try:
        # Format: hash|author|date|message
        format_string = "%h|%an|%aI|%s"
        result = _run_git_command(
            ["git", "log", f"--pretty=format:{format_string}", f"{old_hash}..{new_hash}"],
            cwd=repo_path,
            timeout=timeout,
        )

        if result.returncode != 0:
            return []

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append(
                    CommitInfo(
                        commit_hash=parts[0],
                        author=parts[1],
                        date=parts[2],
                        message=parts[3],
                    )
                )

        return commits

    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        return []


def _get_file_changes(repo_path: Path, old_hash: str, new_hash: str, timeout: int = 10) -> list[FileChange]:
    """
    Get detailed file change information between two commits.

    Uses git diff --numstat to get line-by-line statistics.

    Args:
        repo_path: Path to the git repository
        old_hash: Starting commit hash
        new_hash: Ending commit hash
        timeout: Command timeout in seconds

    Returns:
        List of FileChange objects
    """
    try:
        # Get file statistics
        result = _run_git_command(
            ["git", "diff", "--numstat", f"{old_hash}..{new_hash}"], cwd=repo_path, timeout=timeout
        )

        if result.returncode != 0:
            return []

        files = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            # Format: insertions\tdeletions\tfilename
            # For binary files: -\t-\tfilename
            parts = line.split("\t", 2)
            if len(parts) == 3:
                insertions = 0 if parts[0] == "-" else int(parts[0])
                deletions = 0 if parts[1] == "-" else int(parts[1])
                file_path = parts[2]

                # Detect change type by checking file status
                change_type = "modified"  # Default

                files.append(
                    FileChange(
                        path=file_path,
                        change_type=change_type,
                        insertions=insertions,
                        deletions=deletions,
                    )
                )

        # Now get more detailed status to determine add/delete/rename
        status_result = _run_git_command(
            ["git", "diff", "--name-status", f"{old_hash}..{new_hash}"], cwd=repo_path, timeout=timeout
        )

        if status_result.returncode == 0:
            status_map = {}
            for line in status_result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("\t", 2)
                if len(parts) >= 2:
                    status_code = parts[0]
                    file_path = parts[1]

                    # Map git status codes to our change types
                    if status_code == "A":
                        status_map[file_path] = "added"
                    elif status_code == "D":
                        status_map[file_path] = "deleted"
                    elif status_code.startswith("R"):
                        # Rename: R100 or similar
                        if len(parts) == 3:
                            old_path = parts[1]
                            new_path = parts[2]
                            status_map[new_path] = ("renamed", old_path)
                    elif status_code == "M":
                        status_map[file_path] = "modified"

            # Update change types based on status map
            for file_change in files:
                if file_change.path in status_map:
                    status_info = status_map[file_change.path]
                    if isinstance(status_info, tuple):
                        file_change.change_type = status_info[0]
                        file_change.old_path = status_info[1]
                    else:
                        file_change.change_type = status_info

        return files

    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        return []


def pull_repository_detailed(repo_path: Path, timeout: int = 60) -> PullResult:
    """
    Execute git pull on a repository and return detailed results.

    Args:
        repo_path: Path to the git repository
        timeout: Command timeout in seconds

    Returns:
        PullResult with detailed information about the pull operation

    Raises:
        GitTimeoutError: If command times out
    """
    try:
        result = _run_git_command(["git", "pull"], cwd=repo_path, timeout=timeout)

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        combined_output = f"{stdout}\n{stderr}".strip()

        # Success cases
        if result.returncode == 0:
            if "Already up to date" in stdout or "Already up-to-date" in stdout:
                return PullResult(success=True, already_up_to_date=True, full_output=combined_output)

            elif "Fast-forward" in stdout or "Updating" in stdout:
                # Parse the output to get statistics
                parsed = _parse_git_pull_output(stdout)

                pull_result = PullResult(
                    success=True,
                    already_up_to_date=False,
                    full_output=combined_output,
                    old_commit=parsed["old_commit"],
                    new_commit=parsed["new_commit"],
                    files_changed=parsed["files_changed"],
                    insertions=parsed["insertions"],
                    deletions=parsed["deletions"],
                )

                # Get detailed commit and file information if we have commit hashes
                if parsed["old_commit"] and parsed["new_commit"]:
                    pull_result.commits = _get_commit_details(repo_path, parsed["old_commit"], parsed["new_commit"])
                    pull_result.commits_count = len(pull_result.commits)

                    pull_result.files = _get_file_changes(repo_path, parsed["old_commit"], parsed["new_commit"])

                return pull_result
            else:
                # Some other success case
                return PullResult(success=True, already_up_to_date=False, full_output=combined_output)

        # Error cases
        error_message = None
        if "merge conflict" in combined_output.lower() or "conflict" in combined_output.lower():
            error_message = "Merge conflict detected"
        elif "could not resolve host" in combined_output.lower() or "network" in combined_output.lower():
            error_message = "Network error"
        elif "authentication" in combined_output.lower() or "permission denied" in combined_output.lower():
            error_message = "Authentication failed"
        elif "no tracking information" in combined_output.lower():
            error_message = "No upstream branch configured"
        else:
            # Generic error
            error_output = stderr if stderr else stdout
            if error_output:
                # Truncate long error messages
                error_message = error_output[:100] + "..." if len(error_output) > 100 else error_output
            else:
                error_message = "Pull failed with unknown error"

        return PullResult(
            success=False,
            already_up_to_date=False,
            error_message=error_message,
            error_details=combined_output,
            full_output=combined_output,
        )

    except subprocess.TimeoutExpired as e:
        raise GitTimeoutError(f"Git pull timed out after {timeout} seconds") from e
    except subprocess.SubprocessError as e:
        return PullResult(
            success=False,
            already_up_to_date=False,
            error_message=f"Command execution failed: {e}",
            error_details=str(e),
        )


def pull_repository(repo_path: Path, timeout: int = 60) -> tuple[bool, str]:
    """
    Execute git pull on a repository (legacy interface).

    This is a wrapper around pull_repository_detailed for backward compatibility.

    Args:
        repo_path: Path to the git repository
        timeout: Command timeout in seconds

    Returns:
        tuple of (success: bool, message: str)

    Raises:
        GitTimeoutError: If command times out
    """
    result = pull_repository_detailed(repo_path, timeout)

    if result.success:
        if result.already_up_to_date:
            return True, f"{Fore.GREEN}Already up-to-date{Style.RESET_ALL}"
        else:
            return True, f"{Fore.GREEN}Pulled changes successfully{Style.RESET_ALL}"
    else:
        return False, result.error_message or "Pull failed"


def update_repository(
    repo: RepoInfo,
    skip_dirty: bool = True,
    timeout: int = 60,
) -> RepoInfo:
    """
    Update a git repository by pulling the latest changes (legacy interface).

    This is the main function that orchestrates the update process:
    1. Check repository status (clean, has remote, etc.)
    2. Skip if conditions aren't met (dirty, no remote, etc.)
    3. Execute git pull
    4. Update RepoInfo with results

    Args:
        repo: RepoInfo object to update
        skip_dirty: If True, skip repos with uncommitted changes
        timeout: Command timeout in seconds

    Returns:
        RepoInfo: Updated repository info with new status and message
    """
    try:
        # Check repository status
        status = get_repo_status(repo.path, timeout=timeout)

        # Check if repository has a remote
        if not status["has_remote"]:
            repo.status = RepoStatus.SKIPPED
            repo.message = "No remote configured"
            return repo

        # Check if HEAD is detached
        if status["is_detached"]:
            repo.status = RepoStatus.SKIPPED
            repo.message = "Detached HEAD state"
            return repo

        # Check if branch has upstream
        if not status["has_upstream"]:
            repo.status = RepoStatus.SKIPPED
            repo.message = "No upstream branch"
            return repo

        # Check if working directory is clean
        if not status["is_clean"] and skip_dirty:
            repo.status = RepoStatus.SKIPPED
            repo.message = "Uncommitted changes"
            return repo

        # Execute git pull
        success, message = pull_repository(repo.path, timeout=timeout)

        if success:
            if "up-to-date" in message.lower():
                repo.status = RepoStatus.UP_TO_DATE
            else:
                repo.status = RepoStatus.UPDATED
            repo.message = message
        else:
            repo.status = RepoStatus.ERROR
            repo.error = message

    except GitTimeoutError as e:
        repo.status = RepoStatus.ERROR
        repo.error = str(e)
    except GitCommandError as e:
        repo.status = RepoStatus.ERROR
        repo.error = str(e)
    except Exception as e:
        repo.status = RepoStatus.ERROR
        repo.error = f"Unexpected error: {e}"

    return repo


def update_repository_with_log(
    repo: RepoInfo,
    skip_dirty: bool = True,
    timeout: int = 60,
) -> tuple[RepoInfo, RepoLogEntry]:
    """
    Update a git repository and return detailed log information.

    This function captures comprehensive information about the operation
    for logging purposes while maintaining backward compatibility.

    Args:
        repo: RepoInfo object to update
        skip_dirty: If True, skip repos with uncommitted changes
        timeout: Command timeout in seconds

    Returns:
        tuple of (RepoInfo, RepoLogEntry) with detailed operation information
    """
    start_time = time.time()

    # Initialize log entry
    repo_log = RepoLogEntry(
        path=str(repo.path.resolve()),
        name=repo.name,
        status="pending",
        duration_ms=0,
    )

    try:
        # Get current branch
        branch = get_current_branch(repo.path, timeout=timeout)
        repo_log.branch = branch

        # Check repository status
        status = get_repo_status(repo.path, timeout=timeout)

        # Check if repository has a remote
        if not status["has_remote"]:
            repo.status = RepoStatus.SKIPPED
            repo.message = "No remote configured"
            repo_log.status = "skipped"
            repo_log.skip_reason = "No remote configured"
            repo_log.message = repo.message
            return repo, repo_log

        # Check if HEAD is detached
        if status["is_detached"]:
            repo.status = RepoStatus.SKIPPED
            repo.message = "Detached HEAD state"
            repo_log.status = "skipped"
            repo_log.skip_reason = "Detached HEAD state"
            repo_log.message = repo.message
            return repo, repo_log

        # Check if branch has upstream
        if not status["has_upstream"]:
            repo.status = RepoStatus.SKIPPED
            repo.message = "No upstream branch"
            repo_log.status = "skipped"
            repo_log.skip_reason = "No upstream branch configured"
            repo_log.message = repo.message
            return repo, repo_log

        # Check if working directory is clean
        if not status["is_clean"] and skip_dirty:
            repo.status = RepoStatus.SKIPPED
            repo.message = "Uncommitted changes"
            repo_log.status = "skipped"
            repo_log.skip_reason = "Repository has uncommitted changes"
            repo_log.message = repo.message
            # Capture the uncommitted files for detailed logging
            repo_log.uncommitted_files = get_uncommitted_files(repo.path, timeout=timeout)
            return repo, repo_log

        # Execute git pull with detailed results
        pull_result = pull_repository_detailed(repo.path, timeout=timeout)
        repo_log.git_output = pull_result.full_output

        if pull_result.success:
            if pull_result.already_up_to_date:
                repo.status = RepoStatus.UP_TO_DATE
                repo.message = f"{Fore.GREEN}Already up-to-date{Style.RESET_ALL}"
                repo_log.status = "up_to_date"
                repo_log.message = "Already up-to-date"
            else:
                repo.status = RepoStatus.UPDATED
                repo.message = f"{Fore.GREEN}Pulled changes successfully{Style.RESET_ALL}"
                repo_log.status = "updated"
                repo_log.message = "Changes pulled successfully"

                # Capture detailed change information
                repo_log.commits_pulled = pull_result.commits_count
                repo_log.files_changed = pull_result.files_changed
                repo_log.insertions = pull_result.insertions
                repo_log.deletions = pull_result.deletions
                repo_log.commits = pull_result.commits
                repo_log.files = pull_result.files
        else:
            repo.status = RepoStatus.ERROR
            repo.error = pull_result.error_message or "Pull failed"
            repo_log.status = "error"
            repo_log.error = pull_result.error_message
            repo_log.error_details = pull_result.error_details

    except GitTimeoutError as e:
        repo.status = RepoStatus.ERROR
        repo.error = str(e)
        repo_log.status = "error"
        repo_log.error = str(e)
        repo_log.error_details = traceback.format_exc()
    except GitCommandError as e:
        repo.status = RepoStatus.ERROR
        repo.error = str(e)
        repo_log.status = "error"
        repo_log.error = str(e)
        repo_log.error_details = traceback.format_exc()
    except Exception as e:
        repo.status = RepoStatus.ERROR
        repo.error = f"Unexpected error: {e}"
        repo_log.status = "error"
        repo_log.error = f"Unexpected error: {e}"
        repo_log.error_details = traceback.format_exc()
    finally:
        # Calculate duration
        duration = time.time() - start_time
        repo_log.duration_ms = int(duration * 1000)

    return repo, repo_log


# ============================================================================
# Async Git Operations
# ============================================================================


async def _async_run_git_command(
    command: list[str],
    cwd: Path | None = None,
    timeout: int = 10,
) -> tuple[int, str, str]:
    """
    Helper function to run a git command asynchronously.

    Args:
        command: Git command and arguments (including 'git')
        cwd: Working directory for the command
        timeout: Command timeout in seconds

    Returns:
        tuple of (returncode, stdout, stderr)

    Raises:
        asyncio.TimeoutError: If command times out
    """
    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout,
        )

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        return process.returncode or 0, stdout, stderr

    except TimeoutError as e:
        # Try to kill the process if it's still running
        if process and process.returncode is None:
            try:
                process.kill()
                await process.wait()
            except Exception:
                pass
        raise TimeoutError(f"Command timed out after {timeout} seconds") from e


async def async_get_repo_status(repo_path: Path, timeout: int = 10) -> dict[str, bool]:
    """
    Get the status of a git repository asynchronously.

    Args:
        repo_path: Path to the git repository
        timeout: Command timeout in seconds

    Returns:
        dict with status flags:
            - has_remote: Repository has a remote configured
            - is_clean: Working directory is clean (no uncommitted changes)
            - is_detached: HEAD is detached
            - has_upstream: Current branch has upstream configured

    Raises:
        GitCommandError: If git status command fails
        GitTimeoutError: If command times out
    """
    status = {
        "has_remote": False,
        "is_clean": False,
        "is_detached": False,
        "has_upstream": False,
    }

    try:
        # Check for remotes
        returncode, stdout, _ = await _async_run_git_command(["git", "remote"], cwd=repo_path, timeout=timeout)
        status["has_remote"] = bool(stdout.strip())

        # Check if working directory is clean (filtering out always-ignored files)
        uncommitted_files = await async_get_uncommitted_files(repo_path, timeout=timeout)
        relevant_files = [f for f in uncommitted_files if not should_ignore_file(f.path)]
        status["is_clean"] = len(relevant_files) == 0

        # Check if HEAD is detached
        returncode, _, _ = await _async_run_git_command(
            ["git", "symbolic-ref", "-q", "HEAD"], cwd=repo_path, timeout=timeout
        )
        status["is_detached"] = returncode != 0

        # Check if current branch has upstream (only if not detached)
        if not status["is_detached"]:
            returncode, _, _ = await _async_run_git_command(
                ["git", "rev-parse", "--abbrev-ref", "@{upstream}"],
                cwd=repo_path,
                timeout=timeout,
            )
            status["has_upstream"] = returncode == 0

    except TimeoutError as e:
        raise GitTimeoutError(f"Git status check timed out after {timeout} seconds") from e
    except Exception as e:
        raise GitCommandError(f"Failed to check git status: {e}") from e

    return status


async def async_get_current_branch(repo_path: Path, timeout: int = 10) -> Optional[str]:
    """
    Get the current branch name asynchronously.

    Args:
        repo_path: Path to the git repository
        timeout: Command timeout in seconds

    Returns:
        Branch name or None if detached HEAD
    """
    try:
        returncode, stdout, _ = await _async_run_git_command(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path, timeout=timeout
        )
        if returncode == 0:
            branch = stdout.strip()
            return None if branch == "HEAD" else branch
    except (TimeoutError, Exception):
        pass
    return None


async def async_get_uncommitted_files(repo_path: Path, timeout: int = 10) -> list[UncommittedFile]:
    """
    Get the list of uncommitted files in the repository asynchronously.

    Args:
        repo_path: Path to the git repository
        timeout: Command timeout in seconds

    Returns:
        List of UncommittedFile objects with status information
    """
    status_descriptions = {
        "M": "Modified",
        "A": "Added",
        "D": "Deleted",
        "R": "Renamed",
        "C": "Copied",
        "U": "Updated but unmerged",
        "?": "Untracked",
        "!": "Ignored",
    }

    try:
        returncode, stdout, _ = await _async_run_git_command(
            ["git", "status", "--porcelain"], cwd=repo_path, timeout=timeout
        )

        if returncode != 0:
            return []

        uncommitted_files = []
        for line in stdout.strip().split("\n"):
            if not line:
                continue

            if len(line) < 3:
                continue

            status_code = line[:2]
            file_path = line[2:].lstrip()

            x_status = status_code[0].strip()
            y_status = status_code[1].strip()

            if x_status and x_status != " ":
                main_status = x_status
                status_desc = "Untracked" if main_status == "?" else status_descriptions.get(main_status, "Modified")
            elif y_status and y_status != " ":
                main_status = y_status
                if main_status == "?":
                    status_desc = "Untracked"
                else:
                    status_desc = f"{status_descriptions.get(main_status, 'Modified')} (unstaged)"
            else:
                main_status = "M"
                status_desc = "Modified"

            if status_code == "??":
                main_status = "?"
                status_desc = "Untracked"

            uncommitted_files.append(
                UncommittedFile(
                    path=file_path,
                    status=status_code.strip() or main_status,
                    status_description=status_desc,
                )
            )

        return uncommitted_files

    except (TimeoutError, Exception):
        return []


async def async_check_for_pull_conflicts(repo_path: Path, timeout: int = 10) -> tuple[bool, Optional[str]]:
    """
    Check if a git pull would cause conflicts with untracked files (async version).

    This performs the safety check suggested in GitHub issue #2:
    1. Fetch from origin
    2. Check if any files that would be pulled conflict with local untracked files

    Args:
        repo_path: Path to the git repository
        timeout: Command timeout in seconds

    Returns:
        tuple of (is_safe: bool, error_message: Optional[str])
        - is_safe is True if pull is safe to proceed
        - error_message is set if there's a conflict or error
    """
    try:
        # First, fetch from origin to get the latest refs
        returncode, _, stderr = await _async_run_git_command(["git", "fetch"], cwd=repo_path, timeout=timeout)
        if returncode != 0:
            return False, f"Failed to fetch: {stderr.strip()}"

        # Get current branch
        branch = await async_get_current_branch(repo_path, timeout=timeout)
        if not branch:
            return False, "Cannot determine current branch"

        # Get the upstream branch
        returncode, stdout, _ = await _async_run_git_command(
            ["git", "rev-parse", "--abbrev-ref", "@{upstream}"],
            cwd=repo_path,
            timeout=timeout,
        )
        if returncode != 0:
            return False, "No upstream branch configured"

        upstream = stdout.strip()

        # Check what files would change if we pulled
        returncode, stdout, stderr = await _async_run_git_command(
            ["git", "diff", "--name-status", "HEAD", upstream],
            cwd=repo_path,
            timeout=timeout,
        )

        if returncode != 0:
            return False, f"Failed to check differences: {stderr.strip()}"

        # If there are no differences, it's safe
        if not stdout.strip():
            return True, None

        # Get list of files that would be changed by pull
        files_to_pull = set()
        for line in stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t", 2)
            if len(parts) >= 2:
                if len(parts) == 3:
                    files_to_pull.add(parts[1])
                    files_to_pull.add(parts[2])
                else:
                    files_to_pull.add(parts[1])

        # Get list of untracked files
        uncommitted_files = await async_get_uncommitted_files(repo_path, timeout=timeout)
        untracked_files = {file.path for file in uncommitted_files if file.status == "??" or file.status == "?"}

        # Check for conflicts
        conflicts = files_to_pull & untracked_files
        if conflicts:
            conflict_list = ", ".join(sorted(list(conflicts)[:3]))
            if len(conflicts) > 3:
                conflict_list += f", ... ({len(conflicts)} total)"
            return False, f"Untracked files would be overwritten: {conflict_list}"

        # No conflicts found, safe to pull
        return True, None

    except TimeoutError:
        return False, "Timeout while checking for conflicts"
    except Exception as e:
        return False, f"Error checking for conflicts: {e}"


async def async_check_for_merge_conflicts(repo_path: Path, timeout: int = 10) -> tuple[bool, Optional[str]]:
    """
    Check if a git pull would cause merge conflicts with any uncommitted changes.

    This checks if files that would be changed by a pull overlap with files
    that have uncommitted changes (modified, staged, or untracked).

    Args:
        repo_path: Path to the git repository
        timeout: Command timeout in seconds

    Returns:
        tuple of (is_safe: bool, error_message: Optional[str])
        - is_safe is True if pull is safe to proceed
        - error_message is set if there's a conflict or error
    """
    try:
        # First, fetch from origin to get the latest refs
        returncode, _, stderr = await _async_run_git_command(["git", "fetch"], cwd=repo_path, timeout=timeout)
        if returncode != 0:
            return False, f"Failed to fetch: {stderr.strip()}"

        # Get current branch
        branch = await async_get_current_branch(repo_path, timeout=timeout)
        if not branch:
            return False, "Cannot determine current branch"

        # Get the upstream branch
        returncode, stdout, _ = await _async_run_git_command(
            ["git", "rev-parse", "--abbrev-ref", "@{upstream}"],
            cwd=repo_path,
            timeout=timeout,
        )
        if returncode != 0:
            return False, "No upstream branch configured"

        upstream = stdout.strip()

        # Check what files would change if we pulled
        returncode, stdout, stderr = await _async_run_git_command(
            ["git", "diff", "--name-status", "HEAD", upstream],
            cwd=repo_path,
            timeout=timeout,
        )

        if returncode != 0:
            return False, f"Failed to check differences: {stderr.strip()}"

        # If there are no differences, it's safe
        if not stdout.strip():
            return True, None

        # Get list of files that would be changed by pull
        files_to_pull = set()
        for line in stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t", 2)
            if len(parts) >= 2:
                if len(parts) == 3:
                    # Rename case - check both old and new names
                    files_to_pull.add(parts[1])
                    files_to_pull.add(parts[2])
                else:
                    files_to_pull.add(parts[1])

        # Get list of ALL uncommitted files (modified, staged, untracked)
        uncommitted_files = await async_get_uncommitted_files(repo_path, timeout=timeout)
        uncommitted_paths = {file.path for file in uncommitted_files}

        # Check for conflicts - any overlap between files to pull and uncommitted files
        conflicts = files_to_pull & uncommitted_paths
        if conflicts:
            conflict_list = ", ".join(sorted(list(conflicts)[:3]))
            if len(conflicts) > 3:
                conflict_list += f", ... ({len(conflicts)} total)"
            return False, f"Uncommitted changes would conflict with pull: {conflict_list}"

        # No conflicts found, safe to pull
        return True, None

    except TimeoutError:
        return False, "Timeout while checking for conflicts"
    except Exception as e:
        return False, f"Error checking for conflicts: {e}"


async def _async_get_commit_details(
    repo_path: Path, old_hash: str, new_hash: str, timeout: int = 10
) -> list[CommitInfo]:
    """
    Get detailed commit information for commits between two refs asynchronously.

    Args:
        repo_path: Path to the git repository
        old_hash: Starting commit hash
        new_hash: Ending commit hash
        timeout: Command timeout in seconds

    Returns:
        List of CommitInfo objects
    """
    try:
        format_string = "%h|%an|%aI|%s"
        returncode, stdout, _ = await _async_run_git_command(
            ["git", "log", f"--pretty=format:{format_string}", f"{old_hash}..{new_hash}"],
            cwd=repo_path,
            timeout=timeout,
        )

        if returncode != 0:
            return []

        commits = []
        for line in stdout.strip().split("\n"):
            if not line:
                continue

            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append(
                    CommitInfo(
                        commit_hash=parts[0],
                        author=parts[1],
                        date=parts[2],
                        message=parts[3],
                    )
                )

        return commits

    except (TimeoutError, Exception):
        return []


async def _async_get_file_changes(repo_path: Path, old_hash: str, new_hash: str, timeout: int = 10) -> list[FileChange]:
    """
    Get detailed file change information between two commits asynchronously.

    Args:
        repo_path: Path to the git repository
        old_hash: Starting commit hash
        new_hash: Ending commit hash
        timeout: Command timeout in seconds

    Returns:
        List of FileChange objects
    """
    try:
        # Get file statistics
        returncode, stdout, _ = await _async_run_git_command(
            ["git", "diff", "--numstat", f"{old_hash}..{new_hash}"],
            cwd=repo_path,
            timeout=timeout,
        )

        if returncode != 0:
            return []

        files = []
        for line in stdout.strip().split("\n"):
            if not line:
                continue

            parts = line.split("\t", 2)
            if len(parts) == 3:
                insertions = 0 if parts[0] == "-" else int(parts[0])
                deletions = 0 if parts[1] == "-" else int(parts[1])
                file_path = parts[2]

                change_type = "modified"

                files.append(
                    FileChange(
                        path=file_path,
                        change_type=change_type,
                        insertions=insertions,
                        deletions=deletions,
                    )
                )

        # Get more detailed status to determine add/delete/rename
        returncode, stdout, _ = await _async_run_git_command(
            ["git", "diff", "--name-status", f"{old_hash}..{new_hash}"],
            cwd=repo_path,
            timeout=timeout,
        )

        if returncode == 0:
            status_map = {}
            for line in stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("\t", 2)
                if len(parts) >= 2:
                    status_code = parts[0]
                    file_path = parts[1]

                    if status_code == "A":
                        status_map[file_path] = "added"
                    elif status_code == "D":
                        status_map[file_path] = "deleted"
                    elif status_code.startswith("R"):
                        if len(parts) == 3:
                            old_path = parts[1]
                            new_path = parts[2]
                            status_map[new_path] = ("renamed", old_path)
                    elif status_code == "M":
                        status_map[file_path] = "modified"

            # Update change types based on status map
            for file_change in files:
                if file_change.path in status_map:
                    status_info = status_map[file_change.path]
                    if isinstance(status_info, tuple):
                        file_change.change_type = status_info[0]
                        file_change.old_path = status_info[1]
                    else:
                        file_change.change_type = status_info

        return files

    except (TimeoutError, Exception):
        return []


async def async_pull_repository_detailed(repo_path: Path, timeout: int = 60) -> PullResult:
    """
    Execute git pull on a repository asynchronously and return detailed results.

    Args:
        repo_path: Path to the git repository
        timeout: Command timeout in seconds

    Returns:
        PullResult with detailed information about the pull operation

    Raises:
        GitTimeoutError: If command times out
    """
    try:
        returncode, stdout, stderr = await _async_run_git_command(["git", "pull"], cwd=repo_path, timeout=timeout)

        stdout = stdout.strip()
        stderr = stderr.strip()
        combined_output = f"{stdout}\n{stderr}".strip()

        # Success cases
        if returncode == 0:
            if "Already up to date" in stdout or "Already up-to-date" in stdout:
                return PullResult(success=True, already_up_to_date=True, full_output=combined_output)

            elif "Fast-forward" in stdout or "Updating" in stdout:
                # Parse the output to get statistics
                parsed = _parse_git_pull_output(stdout)

                pull_result = PullResult(
                    success=True,
                    already_up_to_date=False,
                    full_output=combined_output,
                    old_commit=parsed["old_commit"],
                    new_commit=parsed["new_commit"],
                    files_changed=parsed["files_changed"],
                    insertions=parsed["insertions"],
                    deletions=parsed["deletions"],
                )

                # Get detailed commit and file information if we have commit hashes
                if parsed["old_commit"] and parsed["new_commit"]:
                    pull_result.commits = await _async_get_commit_details(
                        repo_path, parsed["old_commit"], parsed["new_commit"]
                    )
                    pull_result.commits_count = len(pull_result.commits)

                    pull_result.files = await _async_get_file_changes(
                        repo_path, parsed["old_commit"], parsed["new_commit"]
                    )

                return pull_result
            else:
                # Some other success case
                return PullResult(success=True, already_up_to_date=False, full_output=combined_output)

        # Error cases
        error_message = None
        if "merge conflict" in combined_output.lower() or "conflict" in combined_output.lower():
            error_message = "Merge conflict detected"
        elif "could not resolve host" in combined_output.lower() or "network" in combined_output.lower():
            error_message = "Network error"
        elif "authentication" in combined_output.lower() or "permission denied" in combined_output.lower():
            error_message = "Authentication failed"
        elif "no tracking information" in combined_output.lower():
            error_message = "No upstream branch configured"
        else:
            # Generic error
            error_output = stderr if stderr else stdout
            if error_output:
                # Truncate long error messages
                error_message = error_output[:100] + "..." if len(error_output) > 100 else error_output
            else:
                error_message = "Pull failed with unknown error"

        return PullResult(
            success=False,
            already_up_to_date=False,
            error_message=error_message,
            error_details=combined_output,
            full_output=combined_output,
        )

    except TimeoutError as e:
        raise GitTimeoutError(f"Git pull timed out after {timeout} seconds") from e
    except Exception as e:
        return PullResult(
            success=False,
            already_up_to_date=False,
            error_message=f"Command execution failed: {e}",
            error_details=str(e),
        )


async def async_update_repository_with_log(
    repo: RepoInfo,
    skip_dirty: bool = True,
    ignore_untracked: bool = False,
    ignore_all_changes: bool = False,
    timeout: int = 60,
) -> tuple[RepoInfo, RepoLogEntry]:
    """
    Update a git repository asynchronously and return detailed log information.

    This is the async version of update_repository_with_log for concurrent operations.

    Args:
        repo: RepoInfo object to update
        skip_dirty: If True, skip repos with uncommitted changes
        ignore_untracked: If True, allow updates when only untracked files are present
        ignore_all_changes: If True, allow updates even with modified files (if no merge conflict)
        timeout: Command timeout in seconds

    Returns:
        tuple of (RepoInfo, RepoLogEntry) with detailed operation information
    """
    start_time = time.time()

    # Initialize log entry
    repo_log = RepoLogEntry(
        path=str(repo.path.resolve()),
        name=repo.name,
        status="pending",
        duration_ms=0,
    )

    try:
        # Get current branch
        branch = await async_get_current_branch(repo.path, timeout=timeout)
        repo_log.branch = branch

        # Check repository status
        status = await async_get_repo_status(repo.path, timeout=timeout)

        # Check if repository has a remote
        if not status["has_remote"]:
            repo.status = RepoStatus.SKIPPED
            repo.message = "No remote configured"
            repo_log.status = "skipped"
            repo_log.skip_reason = "No remote configured"
            repo_log.message = repo.message
            return repo, repo_log

        # Check if HEAD is detached
        if status["is_detached"]:
            repo.status = RepoStatus.SKIPPED
            repo.message = "Detached HEAD state"
            repo_log.status = "skipped"
            repo_log.skip_reason = "Detached HEAD state"
            repo_log.message = repo.message
            return repo, repo_log

        # Check if branch has upstream
        if not status["has_upstream"]:
            repo.status = RepoStatus.SKIPPED
            repo.message = "No upstream branch"
            repo_log.status = "skipped"
            repo_log.skip_reason = "No upstream branch configured"
            repo_log.message = repo.message
            return repo, repo_log

        # Check if working directory is clean
        if not status["is_clean"] and skip_dirty:
            # Get uncommitted files to check if they're only untracked
            uncommitted_files = await async_get_uncommitted_files(repo.path, timeout=timeout)
            only_untracked = has_only_untracked_files(uncommitted_files)

            # If ignore_all_changes is enabled, check for merge conflicts
            if ignore_all_changes:
                # Perform safety check before allowing update
                is_safe, conflict_msg = await async_check_for_merge_conflicts(repo.path, timeout=timeout)
                if not is_safe:
                    repo.status = RepoStatus.SKIPPED
                    repo.message = f"Would cause merge conflict: {conflict_msg}"
                    repo_log.status = "skipped"
                    repo_log.skip_reason = "Uncommitted changes would cause merge conflict"
                    repo_log.message = repo.message
                    repo_log.uncommitted_files = uncommitted_files
                    return repo, repo_log
                # If safe, continue with the pull (don't skip)
            elif ignore_untracked and only_untracked:
                # If ignore_untracked is enabled and files are only untracked, check for conflicts
                # Perform safety check before allowing update
                is_safe, conflict_msg = await async_check_for_pull_conflicts(repo.path, timeout=timeout)
                if not is_safe:
                    repo.status = RepoStatus.SKIPPED
                    repo.message = f"Untracked files conflict with pull: {conflict_msg}"
                    repo_log.status = "skipped"
                    repo_log.skip_reason = "Untracked files would be overwritten by pull"
                    repo_log.message = repo.message
                    repo_log.uncommitted_files = uncommitted_files
                    return repo, repo_log
                # If safe, continue with the pull (don't skip)
            else:
                # Either not only untracked, or neither flag is set
                repo.status = RepoStatus.SKIPPED
                repo.message = "Uncommitted changes"
                repo_log.status = "skipped"
                repo_log.skip_reason = "Repository has uncommitted changes"
                repo_log.message = repo.message
                repo_log.uncommitted_files = uncommitted_files
                return repo, repo_log

        # Execute git pull with detailed results
        pull_result = await async_pull_repository_detailed(repo.path, timeout=timeout)
        repo_log.git_output = pull_result.full_output

        if pull_result.success:
            if pull_result.already_up_to_date:
                repo.status = RepoStatus.UP_TO_DATE
                repo.message = f"{Fore.GREEN}Already up-to-date{Style.RESET_ALL}"
                repo_log.status = "up_to_date"
                repo_log.message = "Already up-to-date"
            else:
                repo.status = RepoStatus.UPDATED
                repo.message = f"{Fore.GREEN}Pulled changes successfully{Style.RESET_ALL}"
                repo_log.status = "updated"
                repo_log.message = "Changes pulled successfully"

                # Capture detailed change information
                repo_log.commits_pulled = pull_result.commits_count
                repo_log.files_changed = pull_result.files_changed
                repo_log.insertions = pull_result.insertions
                repo_log.deletions = pull_result.deletions
                repo_log.commits = pull_result.commits
                repo_log.files = pull_result.files
        else:
            repo.status = RepoStatus.ERROR
            repo.error = pull_result.error_message or "Pull failed"
            repo_log.status = "error"
            repo_log.error = pull_result.error_message
            repo_log.error_details = pull_result.error_details

    except GitTimeoutError as e:
        repo.status = RepoStatus.ERROR
        repo.error = str(e)
        repo_log.status = "error"
        repo_log.error = str(e)
        repo_log.error_details = traceback.format_exc()
    except GitCommandError as e:
        repo.status = RepoStatus.ERROR
        repo.error = str(e)
        repo_log.status = "error"
        repo_log.error = str(e)
        repo_log.error_details = traceback.format_exc()
    except Exception as e:
        repo.status = RepoStatus.ERROR
        repo.error = f"Unexpected error: {e}"
        repo_log.status = "error"
        repo_log.error = f"Unexpected error: {e}"
        repo_log.error_details = traceback.format_exc()
    finally:
        # Calculate duration
        duration = time.time() - start_time
        repo_log.duration_ms = int(duration * 1000)

    return repo, repo_log
