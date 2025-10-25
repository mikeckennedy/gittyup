# Change Log - Gitty Up

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `--ignore-untracked` option to allow updates even when untracked files are present (addresses GitHub issue #2)
  - Performs safety checks to ensure untracked files won't be overwritten by pull
  - Fetches from origin and checks for potential conflicts before pulling
  - Distinguishes between untracked files (safe with checks) and modified files (still skipped)
  - Only proceeds with pull if no conflicts detected between untracked files and incoming changes
- Always-ignored files list for common working files that don't block updates (addresses GitHub issue #2)
  - `.DS_Store` (macOS file system metadata)
  - `Thumbs.db` (Windows thumbnail cache)
  - `__pycache__` (Python bytecode cache directories)
  - These files are automatically filtered when determining if a repository has uncommitted changes
  - Repositories with only these files are treated as clean and can be updated

### Changed
- Improved uncommitted files detection to distinguish between untracked vs modified/staged files
- Enhanced skip reason logging to provide more specific information about why repos were skipped
- Modified `get_repo_status()` and `async_get_repo_status()` to filter out always-ignored files
- Updated `has_only_untracked_files()` to automatically exclude always-ignored files from consideration

### Fixed
- Fixed `--explain` recommendation to include directory path when scanning non-current directories
  - Now correctly shows `gittyup /path/to/dir --explain` instead of just `gittyup --explain`
  - Prevents confusion when users scan a different directory than their current working directory

---

## [1.0.1] - 2025-10-25

### Fixed
- Fixed AttributeError in CLI by importing RepoInfo and ScanResult from models module instead of scanner module (PR #4)

### Changed
- Updated documentation to reflect PyPI availability at https://pypi.org/project/gittyup/
- Changed primary installation method to `uv tool install gittyup` (from PyPI)
- Updated README.md, INSTALLATION.md, and RELEASE_NOTES.md with PyPI installation instructions
- Added PyPI badges to README.md
- Added pytest-asyncio to development dependencies for async test support
- Added asyncio marker to pytest.ini configuration
- Recompiled development requirements with updated dependencies
- Updated version management to use importlib.metadata for dynamic version resolution

---

## [1.0.0] - 2025-10-17

### Added
- **First stable production release! 🎉**
- Complete CLI tool for automatic Git repository discovery and updates across multiple directories
- Concurrent batch processing for dramatic performance improvements
  - Updates 3 repositories simultaneously by default
  - `--batch-size N` / `-b N`: Configure number of concurrent updates
  - `--sync` / `-s`: Force sequential processing when needed
- Persistent operation logging with `--explain` command
  - Review detailed history of previous operations without re-running
  - See commits pulled, files changed, errors encountered, and timing
  - Cross-platform cache storage (macOS, Linux, Windows)
- Intelligent output formatting
  - Repositories displayed in alphabetical order
  - Color-coded status indicators and symbols
  - Compact display for unchanged repositories
  - Detailed sections for updated, skipped, and error repositories
- Uncommitted files display
  - Shows detailed list of uncommitted files when repositories are skipped
  - Color-coded status indicators (modified, untracked, deleted, added)
  - Smart truncation for readability
- Recursive directory scanning with intelligent exclusions
- Automated `git pull` operations with comprehensive error handling
- Beautiful colored output with progress indicators and summary statistics
- Flexible CLI options: `--dry-run`, `--max-depth`, `--exclude`, `--verbose`, `--quiet`, `--version`
- Helpful suggestions to discover features (e.g., suggests `--explain` after operations)
- Cross-platform support (macOS, Linux, Windows)
- 92%+ test coverage with 211+ comprehensive tests
- Professional documentation including readme, troubleshooting guide, and FAQ

---

*Change log format: [Keep a Changelog](https://keepachangelog.com/)*

