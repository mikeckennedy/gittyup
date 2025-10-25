"""Colored output formatting and display."""

from typing import Optional

import colorama
from colorama import Fore, Style

from gittyup.models import OperationLog, RepoInfo, RepoLogEntry, RepoStatus, ScanResult

# Initialize colorama for cross-platform colored terminal output
colorama.init(autoreset=True)


# Status symbols
SYMBOL_SUCCESS = "✓"
SYMBOL_ERROR = "✗"
SYMBOL_SKIP = "⊙"
SYMBOL_PENDING = "→"
SYMBOL_UPDATED = "↓"


def get_status_color(status: RepoStatus) -> str:
    """
    Get the color for a given repository status.

    Args:
        status: Repository status

    Returns:
        str: Colorama color code
    """
    color_map = {
        RepoStatus.UP_TO_DATE: Fore.GREEN,
        RepoStatus.UPDATED: Fore.CYAN,
        RepoStatus.SKIPPED: Fore.YELLOW,
        RepoStatus.ERROR: Fore.RED,
        RepoStatus.PENDING: Fore.WHITE,
    }
    return color_map.get(status, Fore.WHITE)


def get_status_symbol(status: RepoStatus) -> str:
    """
    Get the symbol for a given repository status.

    Args:
        status: Repository status

    Returns:
        str: Status symbol
    """
    symbol_map = {
        RepoStatus.UP_TO_DATE: SYMBOL_SUCCESS,
        RepoStatus.UPDATED: SYMBOL_UPDATED,
        RepoStatus.SKIPPED: SYMBOL_SKIP,
        RepoStatus.ERROR: SYMBOL_ERROR,
        RepoStatus.PENDING: SYMBOL_PENDING,
    }
    return symbol_map.get(status, SYMBOL_PENDING)


def format_repo_status(repo: RepoInfo, show_path: bool = True) -> str:
    """
    Format a repository's status for display.

    Args:
        repo: Repository information
        show_path: Whether to show the full path (default: True)

    Returns:
        str: Formatted repository status line
    """
    color = get_status_color(repo.status)
    symbol = get_status_symbol(repo.status)

    # Build the base output
    location = f"{repo.path}" if show_path else repo.name

    output = f"{color}{symbol} {Style.BRIGHT}{location}{Style.RESET_ALL}"

    # Add status message if present
    if repo.message:
        output += f"{color} - {repo.message}{Style.RESET_ALL}"

    # Add error details if present
    if repo.error:
        output += f"\n  {Fore.RED}Error: {repo.error}{Style.RESET_ALL}"

    return output


def print_repo_status(repo: RepoInfo, show_path: bool = True) -> None:
    """
    Print a repository's status.

    Args:
        repo: Repository information
        show_path: Whether to show the full path (default: True)
    """
    print(format_repo_status(repo, show_path))


def format_summary(result: ScanResult, elapsed_time: Optional[float] = None) -> str:
    """
    Format a summary of scan results.

    Args:
        result: Scan results
        elapsed_time: Optional elapsed time in seconds

    Returns:
        str: Formatted summary text
    """
    lines = []

    # Header
    lines.append(f"\n{Style.BRIGHT}{'=' * 60}{Style.RESET_ALL}")
    lines.append(f"{Style.BRIGHT}Summary{Style.RESET_ALL}")
    lines.append(f"{Style.BRIGHT}{'=' * 60}{Style.RESET_ALL}")

    # Repository counts
    total_repos = result.total_repos
    lines.append(f"{Fore.CYAN}Total repositories found: {Style.BRIGHT}{total_repos}{Style.RESET_ALL}")

    # Count by status
    status_counts = {
        RepoStatus.UP_TO_DATE: 0,
        RepoStatus.UPDATED: 0,
        RepoStatus.SKIPPED: 0,
        RepoStatus.ERROR: 0,
    }

    for repo in result.repositories:
        if repo.status in status_counts:
            status_counts[repo.status] += 1

    # Display status counts with colors
    if status_counts[RepoStatus.UP_TO_DATE] > 0:
        lines.append(
            f"  {Fore.GREEN}{SYMBOL_SUCCESS} Up to date: "
            f"{Style.BRIGHT}{status_counts[RepoStatus.UP_TO_DATE]}{Style.RESET_ALL}"
        )

    if status_counts[RepoStatus.UPDATED] > 0:
        lines.append(
            f"  {Fore.CYAN}{SYMBOL_UPDATED} Updated: {Style.BRIGHT}{status_counts[RepoStatus.UPDATED]}{Style.RESET_ALL}"
        )

    if status_counts[RepoStatus.SKIPPED] > 0:
        lines.append(
            f"  {Fore.YELLOW}{SYMBOL_SKIP} Skipped: {Style.BRIGHT}{status_counts[RepoStatus.SKIPPED]}{Style.RESET_ALL}"
        )

    if status_counts[RepoStatus.ERROR] > 0:
        lines.append(
            f"  {Fore.RED}{SYMBOL_ERROR} Errors: {Style.BRIGHT}{status_counts[RepoStatus.ERROR]}{Style.RESET_ALL}"
        )

    # Skipped paths
    if result.skipped_paths:
        lines.append(f"\n{Fore.YELLOW}Skipped paths: {len(result.skipped_paths)}{Style.RESET_ALL}")

    # Errors
    if result.has_errors:
        lines.append(f"\n{Fore.RED}Errors encountered: {len(result.errors)}{Style.RESET_ALL}")
        for error_path, error_msg in result.errors[:5]:  # Show first 5 errors
            lines.append(f"  {Fore.RED}✗ {error_path}: {error_msg}{Style.RESET_ALL}")
        if len(result.errors) > 5:
            remaining = len(result.errors) - 5
            lines.append(f"  {Fore.RED}... and {remaining} more errors{Style.RESET_ALL}")

    # Elapsed time
    if elapsed_time is not None:
        lines.append(f"\n{Fore.CYAN}Completed in {elapsed_time:.2f} seconds{Style.RESET_ALL}")

    lines.append(f"{Style.BRIGHT}{'=' * 60}{Style.RESET_ALL}\n")

    return "\n".join(lines)


def print_summary(result: ScanResult, elapsed_time: Optional[float] = None) -> None:
    """
    Print a summary of scan results.

    Args:
        result: Scan results
        elapsed_time: Optional elapsed time in seconds
    """
    print(format_summary(result, elapsed_time))


def print_header(title: str, width: int = 60) -> None:
    """
    Print a formatted header.

    Args:
        title: Header title
        width: Width of the header line
    """
    print(f"\n{Style.BRIGHT}{Fore.CYAN}{'=' * width}{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}{Fore.CYAN}{title}{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}{Fore.CYAN}{'=' * width}{Style.RESET_ALL}\n")


def print_separator(width: int = 60) -> None:
    """
    Print a separator line.

    Args:
        width: Width of the separator
    """
    print(f"{Fore.WHITE}{'-' * width}{Style.RESET_ALL}")


def print_error(message: str) -> None:
    """
    Print an error message.

    Args:
        message: Error message
    """
    print(f"{Fore.RED}{SYMBOL_ERROR} Error: {message}{Style.RESET_ALL}")


def print_success(message: str) -> None:
    """
    Print a success message.

    Args:
        message: Success message
    """
    print(f"{Fore.GREEN}{SYMBOL_SUCCESS} {message}{Style.RESET_ALL}")


def print_warning(message: str) -> None:
    """
    Print a warning message.

    Args:
        message: Warning message
    """
    print(f"{Fore.YELLOW}{SYMBOL_SKIP} Warning: {message}{Style.RESET_ALL}")


def print_info(message: str) -> None:
    """
    Print an info message.

    Args:
        message: Info message
    """
    print(f"{Fore.CYAN}{SYMBOL_PENDING} {message}{Style.RESET_ALL}")


def format_progress(current: int, total: int, repo_name: str) -> str:
    """
    Format a progress indicator.

    Args:
        current: Current repository number (1-indexed)
        total: Total number of repositories
        repo_name: Name of the current repository

    Returns:
        str: Formatted progress string
    """
    percentage = (current / total * 100) if total > 0 else 0
    return f"{Fore.CYAN}[{current}/{total} - {percentage:.0f}%]{Style.RESET_ALL} {repo_name}"


def print_progress(current: int, total: int, repo_name: str) -> None:
    """
    Print a progress indicator.

    Args:
        current: Current repository number (1-indexed)
        total: Total number of repositories
        repo_name: Name of the current repository
    """
    print(format_progress(current, total, repo_name))


# ============================================================================
# Explain Command Output Functions
# ============================================================================


def print_explain(operation_log: OperationLog) -> None:
    """
    Print detailed explanation of a previous operation.

    This provides much more detail than the normal run output.
    """
    from datetime import datetime

    # Header
    print_header("Gitty Up - Operation History", width=80)
    print()

    # Metadata
    timestamp = datetime.fromisoformat(operation_log.timestamp)
    print_section("Operation Details")
    print(f"  📅 Run Date: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  📂 Directory: {operation_log.scan_root}")
    print(f"  ⏱️  Duration: {operation_log.duration_seconds:.2f} seconds")
    print(f"  🔧 Gittyup Version: {operation_log.gittyup_version}")
    print(f"  🐙 Git Version: {operation_log.git_version}")
    print()

    # Summary
    print_section("Summary")
    print(f"  Total repositories: {operation_log.total_repos}")
    print(f"  ✅ Updated: {operation_log.updated_repos}")
    print(f"  💤 Already up-to-date: {operation_log.up_to_date_repos}")
    print(f"  ⏭️  Skipped: {operation_log.skipped_repos}")
    print(f"  ❌ Errors: {operation_log.error_repos}")
    print()

    # Detailed repository information
    print_section("Repository Details")
    print()

    # Separate repositories by status and sort alphabetically within each group
    unchanged_repos = sorted(
        [r for r in operation_log.repositories if r.status == "up_to_date"], key=lambda r: r.name.lower()
    )
    updated_repos = sorted(
        [r for r in operation_log.repositories if r.status == "updated"], key=lambda r: r.name.lower()
    )
    skipped_repos = sorted(
        [r for r in operation_log.repositories if r.status == "skipped"], key=lambda r: r.name.lower()
    )
    error_repos = sorted([r for r in operation_log.repositories if r.status == "error"], key=lambda r: r.name.lower())

    # Show unchanged repos compactly at the top
    if unchanged_repos:
        print(f"{Fore.WHITE}Unchanged repositories:{Style.RESET_ALL}")
        print()
        for repo_log in unchanged_repos:
            _print_repo_compact(repo_log)
        print()

    # Show detailed information for updated repos
    if updated_repos:
        print(f"{Fore.GREEN}Updated repositories:{Style.RESET_ALL}")
        print()
        for repo_log in updated_repos:
            _print_repo_detail(repo_log)
            print()

    # Show detailed information for skipped repos
    if skipped_repos:
        print(f"{Fore.YELLOW}Skipped repositories:{Style.RESET_ALL}")
        print()
        for repo_log in skipped_repos:
            _print_repo_detail(repo_log)
            print()

    # Show detailed information for error repos
    if error_repos:
        print(f"{Fore.RED}Error repositories:{Style.RESET_ALL}")
        print()
        for repo_log in error_repos:
            _print_repo_detail(repo_log)
            print()


def print_section(title: str) -> None:
    """
    Print a section header.

    Args:
        title: Section title
    """
    print(f"{Style.BRIGHT}{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}{Fore.CYAN}{title}{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")


def _print_repo_compact(repo_log: RepoLogEntry) -> None:
    """Print compact single-line information for an unchanged repository."""
    status_icon = "💤"
    status_message = "Already up-to-date"

    print(f"{status_icon} {Fore.CYAN}{repo_log.name}{Style.RESET_ALL} - {status_message}")


def _print_repo_detail(repo_log: RepoLogEntry) -> None:
    """Print detailed information for a single repository."""

    # Repository header with status indicator
    status_icon = {
        "updated": "✅",
        "up_to_date": "💤",
        "skipped": "⏭️",
        "error": "❌",
    }.get(repo_log.status, "❓")

    print(f"{status_icon} {Fore.CYAN}{Style.BRIGHT}{repo_log.name}{Style.RESET_ALL}")
    print(f"   Path: {repo_log.path}")
    print(f"   Duration: {repo_log.duration_ms}ms")

    if repo_log.branch:
        print(f"   Branch: {repo_log.branch}")

    # Status-specific details
    if repo_log.status == "updated":
        _print_update_details(repo_log)
    elif repo_log.status == "skipped":
        _print_skip_details(repo_log)
    elif repo_log.status == "error":
        _print_error_details(repo_log)
    elif repo_log.status == "up_to_date":
        print(f"   {Fore.GREEN}Already up-to-date{Style.RESET_ALL}")


def _print_update_details(repo_log: RepoLogEntry) -> None:
    """Print details for an updated repository."""
    print(f"   {Fore.GREEN}Changes pulled successfully{Style.RESET_ALL}")
    print(f"   Commits: {repo_log.commits_pulled}")
    print(f"   Files changed: {repo_log.files_changed}")
    print(f"   Insertions: +{repo_log.insertions}")
    print(f"   Deletions: -{repo_log.deletions}")

    # Show commits if available
    if repo_log.commits:
        print("\n   📝 Commits:")
        for commit in repo_log.commits[:5]:  # Show max 5 commits
            print(f"      {commit.commit_hash} - {commit.message[:60]}")
            print(f"         {commit.author} • {commit.date}")

        if len(repo_log.commits) > 5:
            print(f"      ... and {len(repo_log.commits) - 5} more commits")

    # Show file changes if available
    if repo_log.files:
        print("\n   📁 Files:")
        for file_change in repo_log.files[:10]:  # Show max 10 files
            change_icon = {
                "added": "+",
                "modified": "~",
                "deleted": "-",
                "renamed": "→",
            }.get(file_change.change_type, "?")

            print(f"      {change_icon} {file_change.path}")
            if file_change.insertions or file_change.deletions:
                print(f"         (+{file_change.insertions}/-{file_change.deletions})")

        if len(repo_log.files) > 10:
            print(f"      ... and {len(repo_log.files) - 10} more files")


def _print_skip_details(repo_log: RepoLogEntry) -> None:
    """Print details for a skipped repository."""
    print(f"   {Fore.YELLOW}Skipped{Style.RESET_ALL}")
    print(f"   Reason: {repo_log.skip_reason or 'Unknown'}")

    if repo_log.message:
        print(f"   Details: {repo_log.message}")

    # Show uncommitted files if available
    if repo_log.uncommitted_files:
        print(f"\n   📝 Uncommitted files ({len(repo_log.uncommitted_files)}):")
        for uncommitted_file in repo_log.uncommitted_files[:15]:  # Show max 15 files
            # Use different colors for different statuses
            status_color = Fore.YELLOW
            if uncommitted_file.status_description.startswith("Untracked"):
                status_color = Fore.CYAN
            elif uncommitted_file.status_description.startswith("Deleted"):
                status_color = Fore.RED
            elif uncommitted_file.status_description.startswith("Added"):
                status_color = Fore.GREEN

            print(
                f"      {status_color}{uncommitted_file.status_description:20s}{Style.RESET_ALL} {uncommitted_file.path}"
            )

        if len(repo_log.uncommitted_files) > 15:
            print(f"      ... and {len(repo_log.uncommitted_files) - 15} more files")


def _print_error_details(repo_log: RepoLogEntry) -> None:
    """Print details for an error repository."""
    print(f"   {Fore.RED}Error occurred{Style.RESET_ALL}")
    print(f"   Error: {repo_log.error or 'Unknown error'}")

    if repo_log.error_details:
        print("\n   📋 Details:")
        # Show first few lines of error details
        lines = repo_log.error_details.split("\n")[:10]
        for line in lines:
            print(f"      {line}")
        if len(repo_log.error_details.split("\n")) > 10:
            print("      ... (truncated)")
