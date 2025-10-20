"""CLI entry point and argument parsing for Gitty Up."""

import asyncio
import platform
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import click

from gittyup import __version__, git_operations, output, scanner
from gittyup.logger import LogManager
from gittyup.models import OperationLog, RepoInfo, RepoLogEntry, RepoStatus, ScanResult


def handle_explain_command(directory: Path) -> None:
    """
    Handle the --explain command.

    Shows detailed information about the last operation
    performed on the specified directory.
    """
    directory = directory.resolve()

    with LogManager() as log_manager:
        # Check if log exists
        if not log_manager.has_log(directory):
            output.print_warning(f"No history found for: {directory}")
            output.print_info("Run gittyup in this directory first to create a log")
            sys.exit(0)

        # Retrieve log
        operation_log = log_manager.get_log(directory)

        if operation_log is None:
            output.print_error("Failed to retrieve operation log")
            sys.exit(1)

        # Display formatted output
        output.print_explain(operation_log)

    sys.exit(0)


async def async_update_repos_in_batches(
    repos: list[RepoInfo],
    batch_size: int,
    quiet: bool,
    verbose: bool,
    dry_run: bool,
    result: ScanResult,
) -> list[RepoLogEntry]:
    """
    Update repositories in batches concurrently.

    Args:
        repos: List of repositories to update (already sorted)
        batch_size: Number of repos to update concurrently
        quiet: Minimal output mode
        verbose: Show all output including up-to-date repos
        dry_run: Don't actually update, just show what would be done
        result: ScanResult to add errors to

    Returns:
        List of RepoLogEntry objects in the same order as input repos
    """
    repo_logs: list[RepoLogEntry] = []
    total_repos = len(repos)

    # Process repos in batches
    for batch_start in range(0, total_repos, batch_size):
        batch_end = min(batch_start + batch_size, total_repos)
        batch = repos[batch_start:batch_end]

        # Print which repos are being updated (unless quiet)
        if not quiet and not dry_run:
            repo_names = ", ".join(repo.name for repo in batch)
            output.print_info(f"Updating: {repo_names}")

        if dry_run:
            # In dry run mode, just mark as pending
            batch_results = []
            for repo in batch:
                repo.status = git_operations.RepoStatus.PENDING
                repo.message = "Would attempt to update"
                repo_log = RepoLogEntry(
                    path=str(repo.path.resolve()),
                    name=repo.name,
                    status="pending",
                    duration_ms=0,
                    message="Dry run - no action taken",
                )
                batch_results.append((repo, repo_log))
        else:
            # Actually update repositories concurrently
            tasks = [git_operations.async_update_repository_with_log(repo) for repo in batch]

            try:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                # Handle any exceptions from gather
                for i, result_item in enumerate(batch_results):
                    if isinstance(result_item, Exception):
                        # Handle exception
                        repo = batch[i]
                        repo.status = git_operations.RepoStatus.ERROR
                        repo.error = f"Unexpected error: {result_item!s}"
                        result.add_error(repo.path, str(result_item))

                        # Create error log entry
                        repo_log = RepoLogEntry(
                            path=str(repo.path.resolve()),
                            name=repo.name,
                            status="error",
                            duration_ms=0,
                            error=str(result_item),
                        )
                        batch_results[i] = (repo, repo_log)

            except Exception as e:
                # Catch any unexpected errors
                for repo in batch:
                    repo.status = git_operations.RepoStatus.ERROR
                    repo.error = f"Batch processing error: {e!s}"
                    result.add_error(repo.path, str(e))

                    repo_log = RepoLogEntry(
                        path=str(repo.path.resolve()),
                        name=repo.name,
                        status="error",
                        duration_ms=0,
                        error=str(e),
                    )
                    batch_results.append((repo, repo_log))

        # Print results for this batch in order
        for repo, repo_log in batch_results:
            repo_logs.append(repo_log)

            # Print repo status based on verbosity
            if quiet:
                # Only show errors
                if repo.status == git_operations.RepoStatus.ERROR:
                    output.print_repo_status(repo, show_path=True)
            elif verbose:
                # Show everything
                output.print_repo_status(repo, show_path=True)
            else:
                # Show non-up-to-date repos
                if repo.status != git_operations.RepoStatus.UP_TO_DATE:
                    output.print_repo_status(repo, show_path=True)

        # Add blank line between batches (unless quiet)
        if not quiet and batch_end < total_repos:
            print()

    return repo_logs


def save_operation_log(
    directory: Path,
    result: ScanResult,
    start_time: float,
    dry_run: bool,
    max_depth: Optional[int],
    exclude: tuple[str, ...],
    repo_logs: list[RepoLogEntry],
) -> None:
    """
    Save the operation log to cache.

    Called at the end of a normal gittyup run.
    """
    # Don't save logs for dry runs
    if dry_run:
        return

    # Build operation log
    duration = time.time() - start_time

    operation_log = OperationLog(
        timestamp=datetime.now().isoformat(),
        scan_root=str(directory.resolve()),
        duration_seconds=duration,
        dry_run=dry_run,
        max_depth=max_depth,
        exclude_patterns=list(exclude),
        total_repos=result.total_repos,
        updated_repos=sum(1 for r in result.repositories if r.status == RepoStatus.UPDATED),
        up_to_date_repos=sum(1 for r in result.repositories if r.status == RepoStatus.UP_TO_DATE),
        skipped_repos=sum(1 for r in result.repositories if r.status == RepoStatus.SKIPPED),
        error_repos=sum(1 for r in result.repositories if r.status == RepoStatus.ERROR),
        repositories=repo_logs,
        gittyup_version=__version__,
        git_version=git_operations.get_git_version(),
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        platform=platform.platform(),
    )

    # Save to cache
    try:
        with LogManager() as log_manager:
            log_manager.save_log(directory, operation_log)
    except Exception as e:
        # Don't fail the whole operation if logging fails
        # Just silently ignore (in quiet mode) or show warning
        output.print_warning(f"Failed to save operation log: {e}")


@click.command()
@click.argument(
    "directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=".",
    required=False,
)
@click.option(
    "--dry-run",
    "-n",
    is_flag=True,
    help="Show what would be done without actually updating repositories.",
)
@click.option(
    "--max-depth",
    "-d",
    type=int,
    default=None,
    help="Maximum depth to traverse. Default: unlimited.",
)
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    help="Additional directory patterns to exclude (can be used multiple times).",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed output including skipped repositories.",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Minimal output - only show errors.",
)
@click.option(
    "--batch-size",
    "-b",
    type=int,
    default=3,
    help="Number of repositories to update concurrently (default: 3).",
)
@click.option(
    "--sync",
    "-s",
    is_flag=True,
    help="Force sequential updates (equivalent to --batch-size 1).",
)
@click.option(
    "--version",
    is_flag=True,
    help="Show version and exit.",
)
@click.option(
    "--explain",
    is_flag=True,
    help="Show detailed information about the last run for this directory.",
)
def main(
    directory: Path,
    dry_run: bool,
    max_depth: Optional[int],
    exclude: tuple[str, ...],
    verbose: bool,
    quiet: bool,
    batch_size: int,
    sync: bool,
    version: bool,
    explain: bool,
) -> None:
    """
    Gitty Up - Automatically discover and update all git repositories in a directory tree.

    DIRECTORY: Path to scan for git repositories (default: current directory)

    Examples:

      \b
      # Update all repos in current directory
      $ gittyup

      \b
      # Update repos in specific path
      $ gittyup ~/projects

      \b
      # Dry run to see what would happen
      $ gittyup --dry-run

      \b
      # Limit depth and exclude patterns
      $ gittyup --max-depth 3 --exclude temp --exclude cache
    """
    # Handle --version flag
    if version:
        click.echo(f"Gitty Up version {__version__}")
        sys.exit(0)

    # Handle --explain flag (separate mode)
    if explain:
        handle_explain_command(directory)
        return

    # Validate mutually exclusive options
    if quiet and verbose:
        output.print_error("Cannot use both --quiet and --verbose flags")
        sys.exit(1)

    # Handle --sync flag (forces batch_size to 1)
    if sync:
        batch_size = 1

    # Validate batch size
    if batch_size < 1:
        output.print_error("Batch size must be at least 1")
        sys.exit(1)

    # Check if git is installed
    if not git_operations.check_git_installed():
        output.print_error("Git is not installed or not available in PATH")
        output.print_info("Please install git and try again")
        sys.exit(1)

    # Resolve directory path
    directory = directory.resolve()

    # Print header unless quiet mode
    if not quiet:
        mode = " [DRY RUN]" if dry_run else ""
        output.print_header(f"Gitty Up{mode}", width=70)
        output.print_info(f"Scanning directory: {directory}")
        if max_depth:
            output.print_info(f"Maximum depth: {max_depth}")
        if exclude:
            output.print_info(f"Additional exclusions: {', '.join(exclude)}")
        print()

    # Start timing
    start_time = time.time()

    # Scan for repositories
    exclude_patterns = set(exclude) if exclude else None
    result = scanner.scan_directory(directory, exclude_patterns=exclude_patterns, max_depth=max_depth)

    if result.total_repos == 0:
        if not quiet:
            output.print_warning("No git repositories found")
        sys.exit(0)

    # Print found repositories count
    if not quiet:
        plural = "repositories" if result.total_repos != 1 else "repository"
        output.print_success(f"Found {result.total_repos} git {plural}")
        print()

    # Sort repositories alphabetically by name
    sorted_repos: list[RepoInfo] = sorted(result.repositories, key=lambda r: r.name.lower())

    # Update repositories using async batch processing
    repo_logs: list[RepoLogEntry] = asyncio.run(
        async_update_repos_in_batches(
            repos=sorted_repos,
            batch_size=batch_size,
            quiet=quiet,
            verbose=verbose,
            dry_run=dry_run,
            result=result,
        )
    )

    # Calculate elapsed time
    elapsed_time = time.time() - start_time

    # Print summary unless quiet
    if not quiet:
        print()
        output.print_summary(result, elapsed_time)

    # Save operation log (only if not dry run)
    if not dry_run:
        save_operation_log(directory, result, start_time, dry_run, max_depth, exclude, repo_logs)

        # Suggest running --explain if there were updates, skips, or errors
        if not quiet:
            updated_count = sum(1 for r in result.repositories if r.status == RepoStatus.UPDATED)
            skipped_count = sum(1 for r in result.repositories if r.status == RepoStatus.SKIPPED)
            error_count = sum(1 for r in result.repositories if r.status == RepoStatus.ERROR)

            if updated_count > 0 or skipped_count > 0 or error_count > 0:
                output.print_info("For detailed information about this run, use: gittyup --explain")
                print()

    # Exit with error code if there were errors
    if result.has_errors:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
