# Change Log - Gitty Up

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

