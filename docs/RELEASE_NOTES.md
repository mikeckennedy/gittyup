# 🎉 Gitty Up - Release Notes

---

## 🚀 v1.1.0 - Logging and History Feature

**Release Date**: TBD  
**Status**: Ready for Release ✅

### 🎯 What's New

#### 📊 **Operation Logging and History**

The headline feature of v1.1.0 is comprehensive operation logging with the new `--explain` command. Never wonder what happened during a previous gittyup run again!

**Key Features:**
- **Persistent Logging**: Every operation is automatically logged with detailed information
- **--explain Command**: Review previous operations with rich, detailed output
- **Zero Impact**: Logging happens silently—no changes to normal CLI output
- **Cross-Platform**: OS-specific cache directories (macOS, Linux, Windows)
- **Detailed Data**: Captures commits, file changes, errors, timing, and more

### 📝 New Command: `--explain`

View comprehensive history of the last gittyup operation:

```bash
$ cd ~/projects
$ gittyup --explain
```

**What you'll see:**
- Complete operation metadata (date, duration, versions)
- Summary statistics across all repositories
- Detailed per-repository information:
  - Exact commits pulled with authors and timestamps
  - Files changed with insertion/deletion counts
  - Skip reasons for repositories not updated
  - Full error details and diagnostics
  - Branch information and operation timing

### 🗄️ Cache Storage

Logs are stored in OS-specific cache directories:
- **macOS**: `~/Library/Caches/gittyup/logs`
- **Linux**: `~/.cache/gittyup/logs`  
- **Windows**: `C:\Users\<user>\AppData\Local\gittyup\logs`

**Storage Impact**: Minimal (10-50 KB per log entry)

### 🔧 Technical Details

**New Dependencies:**
- `platformdirs>=4.0.0` - Cross-platform cache directory detection
- `diskcache>=5.6.0` - Efficient persistent key-value storage

**New Modules:**
- `logger.py` - LogManager class for cache operations
- Extended `models.py` - FileChange, CommitInfo, RepoLogEntry, OperationLog

**Test Coverage:**
- Added 101 new tests for logging functionality
- Total: 216 tests passing (was 115)
- Coverage: 91.93% (exceeding 90% goal)

### 📚 Documentation Updates

- Complete `--explain` usage documentation
- Cache location guide for all platforms
- Troubleshooting section for logging issues
- 4 new FAQ entries about history and logs
- Updated project statistics

### 🎓 Usage Examples

**Review what changed:**
```bash
$ gittyup ~/projects
# ... updates repositories ...

$ gittyup --explain
# Shows detailed history including:
# - Which commits were pulled
# - What files changed
# - Why repos were skipped
# - Full error details
```

**Perfect for:**
- Debugging failed operations
- Reviewing what commits were pulled
- Understanding why repositories were skipped
- Tracking operation history over time
- Auditing changes across multiple repositories

### 🐛 Bug Fixes

None—this is a pure feature addition with zero breaking changes.

### ⚠️ Breaking Changes

None—fully backward compatible with v1.0.0.

### 📦 Installation

Same as before:
```bash
git clone https://github.com/mikeckennedy/gittyup
cd gittyup
uv tool install .
```

Or upgrade existing installation:
```bash
cd gittyup
git pull
uv tool install --force .
```

---

## 🎉 v1.0.0 - Initial Release

**Release Date**: October 15, 2025  
**Status**: Production Ready ✅

---

## 🚀 Overview

We're thrilled to announce the first production release of **Gitty Up** - a powerful CLI tool that automatically discovers and updates all Git repositories in a directory tree. Never forget to pull again!

---

## ✨ Key Features

### 🔍 **Intelligent Repository Discovery**
- Recursively scans directories to find all Git repositories
- Smart exclusion of common directories (`node_modules`, `venv`, `build`, etc.)
- Handles symlinks and circular references safely
- Configurable depth limits for large directory trees

### 🎯 **Automated Git Operations**
- Executes `git pull` on all discovered repositories
- Detects and respects repository states (detached HEAD, uncommitted changes)
- Identifies repositories without remotes or upstream branches
- Handles network timeouts and authentication errors gracefully

### 🎨 **Beautiful, Intuitive Output**
- **Color-coded status messages**:
  - 🟢 Green: Successfully updated repositories
  - 🔵 Cyan: Progress indicators and information
  - 🟡 Yellow: Warnings and skipped repositories
  - 🔴 Red: Errors requiring attention
- Real-time progress indicators
- Comprehensive summary statistics
- Customizable verbosity levels (quiet, normal, verbose)

### ⚙️ **Flexible CLI Options**
```bash
gittyup [OPTIONS] [DIRECTORY]

Options:
  -n, --dry-run            Preview changes without updating
  -d, --max-depth INTEGER  Limit directory traversal depth
  -e, --exclude TEXT       Exclude additional directory patterns
  -v, --verbose            Show detailed output
  -q, --quiet              Show only errors
  --version                Show version
  --help                   Show help message
```

### 🛡️ **Robust Error Handling**
- Non-blocking: One failure doesn't stop the entire process
- Clear error messages with actionable guidance
- Handles edge cases:
  - Permission denied
  - Network failures
  - Merge conflicts
  - Detached HEAD states
  - Uncommitted changes
  - Missing remotes

---

## 📊 Technical Excellence

### Test Coverage
- **95.83% code coverage** (exceeding 90% goal)
- **115 comprehensive tests** covering:
  - Unit tests for all modules
  - Integration tests for end-to-end workflows
  - Edge case scenarios
  - Error handling paths

### Code Quality
- Clean, modern Python 3.13+ codebase
- Follows PEP8 and best practices
- Fully type-hinted for better IDE support
- Comprehensive docstrings throughout
- Zero linting issues (ruff)

### Architecture
```
gittyup/
├── cli.py              # CLI entry point and orchestration
├── scanner.py          # Directory traversal and repo detection
├── git_operations.py   # Git command execution and parsing
├── output.py           # Colored output formatting
└── models.py           # Data models (RepoInfo, ScanResult)
```

---

## 🎯 Use Cases

### Daily Development Workflow
```bash
# Start your day by updating all projects
cd ~/projects
gittyup
```

### Project Management
```bash
# Check status of all client projects
gittyup ~/clients --verbose

# Preview what would be updated
gittyup ~/work --dry-run
```

### System Maintenance
```bash
# Update repos but skip deep node_modules
gittyup --max-depth 3 --exclude cache
```

---

## 📦 Installation

### Recommended: Global Tool Installation
```bash
# Install as a global CLI tool (no venv needed!)
git clone https://github.com/mikeckennedy/gittyup
cd gittyup
uv tool install .

# Use from anywhere
gittyup --version
```

**Benefits:**
- ✅ No virtual environment activation required
- ✅ Command available system-wide
- ✅ Isolated environment managed by uv
- ✅ Perfect for CLI tools

### Alternative: Virtual Environment
```bash
git clone https://github.com/mikeckennedy/gittyup
cd gittyup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
uv pip install -e .
```

### Verify Installation
```bash
gittyup --version
# Output: Gitty Up version 1.0.0

gittyup --help
# Shows complete usage information
```

---

## 🎓 Quick Start Examples

### Example 1: Update Current Directory
```bash
$ gittyup

🐴 Gitty Up!
════════════════════════════════════════
Scanning directory: /Users/mike/projects
✓ Found 5 git repositories

[1/5 - 20%] project-alpha
✓ project-alpha - Already up-to-date

[2/5 - 40%] project-beta
↓ project-beta - Pulled changes successfully

[3/5 - 60%] project-gamma
⊙ project-gamma - Uncommitted changes

[4/5 - 80%] project-delta
✓ project-delta - Already up-to-date

[5/5 - 100%] project-epsilon
✗ project-epsilon - Network timeout
  Error: Git pull timed out after 300 seconds

════════════════════════════════════════
Summary
════════════════════════════════════════
Total repositories found: 5
  ✓ Up to date: 2
  ↓ Updated: 1
  ⊙ Skipped: 1
  ✗ Errors: 1

Completed in 3.45 seconds
════════════════════════════════════════
```

### Example 2: Dry Run Preview
```bash
$ gittyup ~/projects --dry-run

# Shows what would be updated without actually pulling
```

### Example 3: Quiet Mode (Errors Only)
```bash
$ gittyup -q

# Only shows errors, perfect for scripting
```

### Example 4: Verbose Output
```bash
$ gittyup -v

# Shows all repositories including skipped ones
# Shows full git output and detailed status
```

---

## 🐛 Known Issues & Limitations

### Current Limitations
1. **Sequential Updates**: Repositories are updated one at a time (faster concurrent mode planned for v1.1)
2. **Pull Only**: Currently only supports `git pull` (status checking and other operations planned)
3. **No Stashing**: Doesn't auto-stash uncommitted changes (planned for v1.2)

### Workarounds
- For faster updates on many repos, run multiple instances in different directories
- Manually resolve uncommitted changes or merge conflicts before running

---

## 🔮 Roadmap (Future Versions)

### v1.1 - Performance & Parallel Operations
- Concurrent repository updates with `--parallel` flag
- Performance optimizations for large directory trees
- Caching for repository discovery

### v1.2 - Advanced Git Features
- Status checking mode (`--status`)
- Auto-stash uncommitted changes option
- Branch specification (`--branch`)
- Fetch-only mode

### v1.3 - Enhanced User Experience
- Interactive mode to select which repos to update
- Desktop notifications on completion
- Configuration file support (`.gittyuprc`)
- Report generation (JSON/CSV export)

### v2.0 - Ecosystem Integration
- GitHub/GitLab integration
- Team collaboration features
- Webhook notifications
- Plugin system for custom hooks

---

## 🙏 Acknowledgments

**Built with:**
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Colorama](https://github.com/tartley/colorama) - Cross-platform colored output
- [pytest](https://pytest.org/) - Testing framework
- [Ruff](https://github.com/astral-sh/ruff) - Python linter and formatter
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer

---

## 📄 License

MIT License - See LICENSE file for details

---

## 📞 Support & Contributing

### Get Help
- 📖 Read the [complete documentation](readme.md)
- 🐛 Report issues on [GitHub Issues](https://github.com/mikeckennedy/gittyup/issues)
- 💬 Ask questions in [Discussions](https://github.com/mikeckennedy/gittyup/discussions)

### Contribute
We welcome contributions! See [Contributing Guidelines](readme.md#-contributing) for:
- Code contributions
- Bug reports
- Feature requests
- Documentation improvements

---

## 🎯 Project Statistics

- **Lines of Code**: ~1,200 (production code)
- **Test Lines**: ~1,500 (test code)
- **Documentation**: 500+ lines
- **Test Coverage**: 95.83%
- **Tests**: 115 passing
- **Development Time**: ~35 hours
- **Python Version**: 3.13+

---

## ⭐ Show Your Support

If you find Gitty Up useful, please:
- ⭐ Star the repository on GitHub
- 🐦 Share on social media
- 🐛 Report bugs and suggest features
- 🤝 Contribute improvements

---

**Thank you for using Gitty Up! Happy coding! 🎉**

*Never forget to pull again.* 🐴

