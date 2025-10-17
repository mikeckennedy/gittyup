# Change Log - Gitty Up

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Concurrent Batch Processing** - Complete ✅
  - Asynchronous repository updates using asyncio for dramatic performance improvements
  - Default batch processing: updates 3 repositories simultaneously
  - New CLI options:
    - `--batch-size N` / `-b N`: Configure number of concurrent repository updates (default: 3)
    - `--sync` / `-s`: Force sequential processing for debugging or careful monitoring
  - Intelligent batch output: displays batch groups with ordered results after completion
  - Safe concurrent operations: maintains all existing safety checks and error handling
  - Backward compatible: all existing functions remain available
  - Performance optimization: network I/O happens concurrently while waiting for git operations
  - Clear visual feedback: shows which repos are updating in each batch
  - Async implementation in `git_operations.py`: 
    - `async_update_repository_with_log()` - Main async update function
    - `_async_run_git_command()` - Core async subprocess wrapper
    - `async_pull_repository_detailed()` - Async pull with detailed results
  - Batch orchestration in `cli.py`:
    - `async_update_repos_in_batches()` - Manages concurrent batch processing
    - Modified main update loop for async operation
  - Documentation updates:
    - Updated readme with batch processing explanation and examples
    - New FAQ entry explaining concurrency and performance benefits
    - Updated command reference with new CLI options
    - New workflow examples: "Performance Mode" and "Safe and Sequential"
  - Updated example output to show batch-based processing format

### Fixed
- **Explain Output Labeling** - Complete ✅
  - Fixed misleading "Changed repositories:" header in `--explain` output
  - Now properly separates repositories into distinct sections:
    - "Unchanged repositories:" (up-to-date repos, compact format)
    - "Updated repositories:" (repos that were actually updated)
    - "Skipped repositories:" (repos that couldn't be updated)
    - "Error repositories:" (repos with errors)
  - Improves clarity and prevents confusion when viewing skipped repositories
  - Each section now has appropriate color coding (green for updated, yellow for skipped, red for errors)

### Added
- **Alphabetical Repository Sorting** - Complete ✅
  - Repositories now processed and reported in alphabetical order by name
  - Applies to both normal operation output and `--explain` command output
  - Within the explain output, repositories are also sorted alphabetically within each status group
  - Improves consistency and makes it easier to find specific repositories in output
  - Works seamlessly with existing features and sorting criteria

- **Compact Explain Output for Unchanged Repos** - Complete ✅
  - Unchanged (up-to-date) repositories now display as single compact lines in `--explain` output
  - Format: `💤 repo-name - Already up-to-date`
  - Unchanged repos grouped together at the top for easy scanning
  - Changed repos (updated, skipped, error) shown below with full details
  - Improves readability when dealing with many up-to-date repositories
  - All existing tests pass (65 tests in test_output.py)
  
- **Uncommitted Files Display** - Complete ✅
  - New `UncommittedFile` data model with status tracking (Modified, Untracked, Deleted, Added, etc.)
  - Enhanced `get_uncommitted_files()` function to parse git status --porcelain output
  - Detailed file listing in `--explain` output when repositories are skipped due to uncommitted changes
  - Color-coded status indicators: yellow for modified, cyan for untracked, red for deleted, green for added
  - Smart truncation: shows first 15 files with "... and N more files" message for readability
  - 13 new comprehensive tests for uncommitted files functionality
  - Updated logger deserialization to support UncommittedFile objects
  - Seamless integration with existing logging and explain infrastructure
  - Coverage maintained at 92% with 211 total tests passing

- **CLI Enhancement - Explain Command Suggestion** - Complete ✅
  - Automatic suggestion to run `gittyup --explain` after operations with updates, skips, or errors
  - Smart detection: only shows suggestion when there are noteworthy changes
  - Non-intrusive: only appears in non-quiet mode after normal operations
  - Helps users discover detailed logging feature without overwhelming them
  
- **Logging and Explain Feature** - Complete ✅
  - ✅ **Phase 1: Foundation** - Dependencies (platformdirs, diskcache), data models, LogManager, unit tests
  - ✅ **Phase 2: Enhanced Git Operations** - Commit details, file changes, git output parsing
  - ✅ **Phase 3: CLI Integration** - --explain flag, log saving, operation tracking  
  - ✅ **Phase 4: Explain Output** - Rich formatted output with detailed operation history
  - ✅ **Phase 5: Testing and Polish** - 216 total tests passing with 91.93% coverage
  - ✅ **Phase 6: Documentation** - Complete readme, troubleshooting, FAQ, and release notes
  
  **Key Features:**
  - Persistent operation logging with OS-specific cache directories (macOS, Linux, Windows)
  - Detailed log data: commits, file changes, errors, timing, branch info
  - `--explain` command to review previous operations without re-running
  - Zero impact on normal CLI output—logging happens silently
  - JSON-based storage for human readability and debuggability
  - Comprehensive test coverage with 101 new tests for logging functionality
  - Cross-platform cache location support via platformdirs
  - Efficient key-value storage with diskcache
  
  **Documentation:**
  - Updated readme.md with --explain flag usage and examples
  - Added cache location documentation for all platforms
  - Added troubleshooting guide for logging issues
  - Added 4 new FAQ entries about logging and history
  - Updated project stats (216 tests, 91.93% coverage)

### Previous Additions
- Initial project structure and configuration (Phase 1)
- Core module placeholders (cli, scanner, git_operations, output, models)
- Test suite structure
- Project configuration files (pyproject.toml, pytest.ini, ruff.toml)
- Development tooling setup (ruff for linting/formatting, pytest for testing)
- Data models: `RepoInfo`, `RepoStatus`, `ScanResult` for repository tracking (Phase 2)
- Directory scanner with recursive traversal using pathlib.Path (Phase 2)
- Git repository detection via .git directory check (Phase 2)
- Directory exclusion patterns (node_modules, venv, __pycache__, etc.) (Phase 2)
- Symlink handling with broken symlink detection and circular reference prevention (Phase 2)
- Comprehensive scanner test suite with 26 tests (Phase 2)
- Edge case handling: permission errors, max depth limits, custom exclusions (Phase 2)
- Git operations module with safe subprocess execution and timeout handling (Phase 3)
- Repository status checking: clean/dirty state, remote configuration, detached HEAD detection (Phase 3)
- Git pull functionality with comprehensive error handling (Phase 3)
- Error detection for: merge conflicts, network failures, authentication errors, no upstream (Phase 3)
- Main `update_repository()` orchestration function for complete update workflow (Phase 3)
- Custom exceptions: `GitError`, `GitCommandError`, `GitTimeoutError` (Phase 3)
- Comprehensive git operations test suite with 31 tests including integration tests (Phase 3)
- Colorful CLI output formatting using colorama for cross-platform support (Phase 4)
- Status-specific colors and symbols (✓, ✗, ⊙, →, ↓) for visual clarity (Phase 4)
- Repository status formatting with `format_repo_status()` and `print_repo_status()` (Phase 4)
- Summary statistics with `format_summary()` and `print_summary()` including elapsed time (Phase 4)
- Utility functions: `print_header()`, `print_separator()`, `print_error()`, `print_success()`, etc. (Phase 4)
- Progress indicators with percentage and repository counts (Phase 4)
- Comprehensive output test suite with 39 tests covering all formatting scenarios (Phase 4)
- Full-featured CLI implementation using Click framework (Phase 5)
- Command-line arguments: directory path with validation, support for current directory default (Phase 5)
- CLI options: `--dry-run`, `--max-depth`, `--exclude`, `--verbose`, `--quiet`, `--version` (Phase 5)
- Complete workflow orchestration: scan → update → display with timing (Phase 5)
- Git installation validation before execution (Phase 5)
- Intelligent verbosity levels: normal (changes only), verbose (all), quiet (errors only) (Phase 5)
- Proper exit codes: 0 for success, 1 for errors (Phase 5)
- Exception handling for unexpected errors during updates (Phase 5)
- Comprehensive CLI test suite with 19 tests covering all user scenarios (Phase 5)
- Working `gittyup` command entry point configured in pyproject.toml (Phase 5)
- Overall test coverage: **95.82% across 115 tests** (Phases 2-5)
- Green colored success messages for git operations: "Pulled changes successfully", "Already up-to-date", "Updated successfully" (Phase 6)
- Code quality verification with ruff format and ruff check - all checks passing (Phase 6)
- Comprehensive docstring coverage across all modules and functions (Phase 6)
- Final test coverage verification: **98.76% across 115 tests** - exceeding 90% goal (Phase 6)
- Quality assurance complete: all edge cases handled, error messages clear and actionable (Phase 6)
- Comprehensive readme.md with installation instructions, usage examples, and CLI documentation (Phase 7)
- Complete troubleshooting guide with solutions for common issues (Phase 7)
- FAQ section answering 8 common user questions (Phase 7)
- Error reference table mapping error messages to solutions (Phase 7)
- Development guidelines and contributing section for open source collaboration (Phase 7)
- Brand Guardian enhancement: polished readme with visual appeal, GitHub badges, and engaging narrative (Phase 7)
- Professional documentation structure optimized for GitHub presentation (Phase 7)
- Verified and validated pyproject.toml for production distribution (Phase 8)
- Successful local installation testing with `uv pip install -e .` (Phase 8)
- Package builds cleanly with hatchling build backend (Phase 8)
- Verified `gittyup` CLI command entry point works correctly after installation (Phase 8)
- Comprehensive RELEASE_NOTES.md documenting v1.0.0 features, use cases, and roadmap (Phase 8)
- Installation verification guide with step-by-step instructions (Phase 8)
- Production-ready package configuration for future PyPI distribution (Phase 8)

---

## [1.0.0] - 2025-10-15

### Added
- **First stable production release! 🎉**
- Complete CLI tool for automatic Git repository discovery and updates
- Recursive directory scanning with intelligent exclusions
- Automated `git pull` operations with comprehensive error handling
- Beautiful colored output with progress indicators and summary statistics
- Flexible CLI options: dry-run, max-depth, exclude patterns, verbosity levels
- 95.83% test coverage with 115 comprehensive tests
- Professional documentation including readme, troubleshooting guide, and FAQ
- Cross-platform support (macOS, Linux, Windows)

---

*Change log format: [Keep a Changelog](https://keepachangelog.com/)*

