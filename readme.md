<div align="center">

# 🐴 Gitty Up!

### *Never forget to pull again*

**Automatically discover and update all your Git repositories with one command**

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI Version](https://img.shields.io/pypi/v/gittyup.svg)](https://pypi.org/project/gittyup/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/gittyup.svg)](https://pypi.org/project/gittyup/)
[![Test Coverage](https://img.shields.io/badge/coverage-91.93%25-brightgreen.svg)](https://github.com)
[![Tests](https://img.shields.io/badge/tests-216%20passing-brightgreen.svg)](https://github.com)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-black.svg)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [FAQ](#-faq)

</div>

---

## 🎯 The Problem

You're about to start coding. You open your project, dive into the code, make changes... then realize you forgot to `git pull`. Now you're dealing with merge conflicts, rebasing headaches, and lost time. Sound familiar?

When you're juggling multiple projects, working across different machines, or collaborating with a team, keeping every repository up-to-date becomes a mental burden. One forgotten `git pull` can derail your entire workflow.

## ✨ The Solution

**Gitty Up** is your automated Git guardian. Point it at your projects directory, and it intelligently scans every repository, pulling the latest changes while keeping your work safe. It documents everything it does, so you always know exactly what changed. No more forgotten pulls. No more merge conflict surprises. No more wondering what happened. Just smooth, up-to-date repositories ready for action—with complete accountability.

Think of it as your morning coffee routine for your codebase—one command, and everything's fresh, safe, and fully documented.

---

## 🚀 Features

<table>
<tr>
<td width="50%">

### 🛡️ **Safety First**
Smart checks prevent data loss. Skips repos with uncommitted changes, detached HEADs, or missing upstreams. Your local work is always protected.

### 🔍 **Complete Transparency**
Your Git guardian keeps detailed records. Every operation is automatically logged with commit details, file changes, and timing data. Use `--explain` to review exactly what happened—perfect for debugging, auditing, or understanding what changed.

### 🎨 **Visual Clarity**  
Beautiful, color-coded output with intuitive symbols. Green for success, red for errors—know exactly what's happening at a glance.

### 🔎 **Intelligent Discovery**
Recursively finds every Git repository in your directory tree, no matter how deeply nested.

</td>
<td width="50%">

### ⚡ **Lightning Fast**
Concurrent batch processing updates multiple repositories simultaneously. Configurable batch sizes optimize performance for your workflow. Auto-excludes common junk directories.

### 🎯 **Flexible Control**
Dry-run mode, depth limits, custom exclusions, verbosity levels—you're in complete control of every operation.

### ✅ **Battle-Tested**
91.93% test coverage with 216 comprehensive tests. Production-ready and reliable with every release.

</td>
</tr>
</table>

---

## 📦 Installation

### Prerequisites

- **Python 3.13+** installed on your system
- **Git** available in your PATH
- **uv** package manager (recommended) or pip

### Method 1: Install from PyPI (Recommended) ⭐

Install directly from PyPI as a global CLI tool—no virtual environment needed!

```bash
# Install as a global tool with uv
uv tool install gittyup

# That's it! Use from anywhere without activating venv
gittyup --version
```

**Benefits:** ✅ No venv activation • ✅ Available system-wide • ✅ Isolated environment • ✅ Easy updates


### Method 2: Install from Source

For development or contributing to the project:

```bash
# Clone and navigate to the project
git clone https://github.com/mikeckennedy/gittyup
cd gittyup

# Install in editable mode with uv
uv tool install --editable .
```

---

## ⚡ Quick Start

### Basic Commands

```bash
# Update all repos in current directory
gittyup

# Update repos in a specific location
gittyup ~/dev/projects

# Preview what would happen (dry run)
gittyup --dry-run

# Get detailed output
gittyup --verbose
```

### Common Workflows

**The Monday Morning Refresh** 🌅
```bash
gittyup ~/projects
```
Start your week with every project up-to-date.

**The Quick Check** 👀
```bash
gittyup --dry-run --verbose
```
See what's outdated without touching anything.

**The Deep Dive** 🔎
```bash
gittyup ~/dev --max-depth 3 --exclude archive --verbose
```
Scan thoroughly but skip archived projects.

**The Accountability Check** 🔍
```bash
gittyup --explain
```
Review your guardian's detailed report: see exactly what commits were pulled, which files changed, and why any repos were skipped. Perfect for Monday morning catch-up or debugging unexpected changes.

**The Performance Mode** ⚡
```bash
gittyup ~/projects --batch-size 5
```
Update multiple repositories concurrently for maximum speed. Adjust batch size based on your system resources and network connection. Careful you don't over do it and get rate limited at GitHub.

**The Safe and Sequential** 🎯
```bash
gittyup --sync --verbose
```
Process repositories one at a time for careful monitoring or when debugging issues. Perfect for troubleshooting or conservative workflows.

---

## 📖 Documentation

### Command Reference

```bash
gittyup [DIRECTORY] [OPTIONS]
```

| Argument/Option | Description | Default |
|----------------|-------------|---------|
| `DIRECTORY` | Path to scan for repositories | Current directory |
| `-n, --dry-run` | Preview changes without updating | Disabled |
| `-b, --batch-size N` | Number of repos to update concurrently | 3 |
| `-s, --sync` | Force sequential updates (batch size = 1) | Concurrent |
| `-d, --max-depth N` | Maximum directory depth to scan | Unlimited |
| `-e, --exclude PATTERN` | Skip directories matching pattern | None |
| `-v, --verbose` | Show all repos, including up-to-date | Normal |
| `-q, --quiet` | Only show errors | Normal |
| `--explain` | Show detailed history of last run | Disabled |
| `--version` | Display version information | - |
| `--help` | Show help message | - |

### Output Guide

Gitty Up uses clear visual indicators to communicate status:

<table>
<tr>
<td><strong>✓</strong> Green</td>
<td>Repository is up-to-date or successfully updated</td>
</tr>
<tr>
<td><strong>↓</strong> Cyan</td>
<td>Repository pulled new commits</td>
</tr>
<tr>
<td><strong>⊙</strong> Yellow</td>
<td>Repository skipped (safety check failed)</td>
</tr>
<tr>
<td><strong>✗</strong> Red</td>
<td>Error occurred during update</td>
</tr>
<tr>
<td><strong>→</strong> White</td>
<td>Processing repository</td>
</tr>
</table>

### Example Output

```
╔════════════════════════════════════════════════════════════════════════════╗
║                              Gitty Up                                       ║
╚════════════════════════════════════════════════════════════════════════════╝

✓ Scanning directory: /Users/dev/projects
✓ Found 9 git repositories

Updating: project-alpha, project-beta, project-gamma
✓ project-alpha - Already up-to-date
↓ project-beta - Pulled 3 commits
⊙ project-gamma - Uncommitted changes

Updating: project-delta, project-epsilon, project-zeta
✓ project-delta - Already up-to-date
✗ project-epsilon - Network timeout
↓ project-zeta - Pulled 1 commit

Updating: project-omega, project-sigma, project-theta
✓ project-omega - Already up-to-date
✓ project-sigma - Already up-to-date
✓ project-theta - Already up-to-date

════════════════════════════════════════════════════════════════════════════
Summary
════════════════════════════════════════════════════════════════════════════
Total repositories found: 9
  ✓ Up to date: 5
  ↓ Updated: 2
  ⊙ Skipped: 1
  ✗ Errors: 1

Completed in 4.23 seconds
════════════════════════════════════════════════════════════════════════════
```

**Note:** The example shows default batch processing (3 repos at a time). Use `--sync` for sequential updates with individual progress indicators.

### Using --explain to Review History

Your Git guardian keeps detailed records of every operation. Need to know what changed? Just ask:

```bash
$ cd ~/projects
$ gittyup --explain
```

```
═══════════════════════════════════════════════════════════════════════════
                    Gitty Up - Operation History
═══════════════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════════════
Operation Details
═══════════════════════════════════════════════════════════════════════════
  📅 Run Date: 2025-10-15 14:23:45
  📂 Directory: /Users/dev/projects
  ⏱️  Duration: 2.34 seconds
  🔧 Gittyup Version: 1.0.0
  🐙 Git Version: 2.39.0

═══════════════════════════════════════════════════════════════════════════
Summary
═══════════════════════════════════════════════════════════════════════════
  Total repositories: 5
  ✅ Updated: 1
  💤 Already up-to-date: 3
  ⏭️  Skipped: 1
  ❌ Errors: 0

═══════════════════════════════════════════════════════════════════════════
Repository Details
═══════════════════════════════════════════════════════════════════════════

✅ project-alpha
   Path: /Users/dev/projects/project-alpha
   Duration: 487ms
   Branch: main
   Changes pulled successfully
   Commits: 3
   Files changed: 5
   Insertions: +127
   Deletions: -43

   📝 Commits:
      a7f2c3d - Add new feature for user authentication
         John Doe • 2025-10-15T10:23:00
      b8e1d4f - Fix bug in login validation
         Jane Smith • 2025-10-15T09:15:00
      c9f2e5g - Update dependencies to latest versions
         John Doe • 2025-10-14T16:45:00

   📁 Files:
      ~ src/auth.py
         (+45/-12)
      + src/validators.py
         (+32/-0)
      ~ tests/test_auth.py
         (+28/-8)

💤 project-beta
   Path: /Users/dev/projects/project-beta
   Duration: 123ms
   Branch: develop
   Already up-to-date

⏭️  project-gamma
   Path: /Users/dev/projects/project-gamma
   Duration: 89ms
   Branch: main
   Skipped
   Reason: Repository has uncommitted changes
   Details: Pull would conflict with local modifications

═══════════════════════════════════════════════════════════════════════════
```

**What --explain shows:**
- **Complete operation metadata**: When it ran, how long it took, tool versions
- **Summary statistics**: Overall results across all repositories  
- **Detailed repository information**:
  - Every commit that was pulled (who wrote it, when, what changed)
  - Exactly which files changed with insertion/deletion counts
  - Why any repos were skipped with specific reasons
  - Full error details for debugging failed operations
  - Branch information and precise timing data

**Perfect for:**
- Debugging issues or understanding unexpected changes
- Auditing what happened during automated runs
- Reviewing what you missed while away from your desk
- Team accountability and change tracking

**Where logs are stored:**
Your guardian keeps records in OS-specific cache directories:
- **macOS**: `~/Library/Caches/gittyup/logs`
- **Linux**: `~/.cache/gittyup/logs`
- **Windows**: `C:\Users\<user>\AppData\Local\gittyup\logs`

Each directory you scan gets its own log, automatically updated with each run. Storage is minimal (10-50 KB per log).

---

## 🛡️ Safety Features

Gitty Up protects your work with intelligent safety checks. It will **skip** updating a repository if it detects:

| Condition | Why it's Skipped | What to Do |
|-----------|------------------|------------|
| 🔒 Uncommitted changes | Prevents losing your work | Commit, stash, or discard changes first |
| 🔗 No remote configured | Nothing to pull from | Add a remote: `git remote add origin <url>` |
| 📍 Detached HEAD state | Not on a branch | Checkout a branch: `git checkout main` |
| 🎯 No upstream branch | Branch not tracking remote | Set upstream: `git push -u origin <branch>` |
| 🌐 Network errors | Can't reach remote | Check connection and remote URL |
| 🔐 Authentication failed | Credentials missing | Configure Git credentials |

**Your local work is always safe.** Gitty Up never forces changes or overwrites uncommitted work.

---

## 🧠 Smart Filtering

Gitty Up automatically skips common directories that aren't your code:

**Development Environments:**  
`node_modules`, `venv`, `.venv`, `env`, `.env`, `vendor`

**Build Artifacts:**  
`dist`, `build`, `target`, `.eggs`, `eggs`

**Caches:**  
`__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `htmlcov`

**Tools:**  
`.tox`, `.nox`, `.idea`, `.vscode`

**Version Control:**  
`.git`, `.svn`, `.hg`

Want to exclude more? Use `--exclude`:
```bash
gittyup --exclude temp --exclude backup --exclude old-stuff
```

---

## ❓ FAQ

<details>
<summary><strong>Will Gitty Up overwrite my local changes?</strong></summary>

**Absolutely not.** Gitty Up includes comprehensive safety checks and will skip any repository with uncommitted changes. Your local work is always protected.
</details>

<details>
<summary><strong>What happens if I have a merge conflict?</strong></summary>

Gitty Up will detect the conflict, report it as an error, and move on to the next repository. You'll need to resolve conflicts manually—Gitty Up never forces merges.
</details>

<details>
<summary><strong>Can I use this with private repositories?</strong></summary>

Yes! As long as your Git credentials are properly configured (SSH keys or credential helper), Gitty Up will work seamlessly with private repos.
</details>

<details>
<summary><strong>How do I exclude specific directories?</strong></summary>

Use the `--exclude` option (multiple times if needed):
```bash
gittyup --exclude archive --exclude temp --exclude old-projects
```
</details>

<details>
<summary><strong>Does it work with Git submodules?</strong></summary>

Gitty Up treats the parent repository as a single unit and doesn't traverse into submodules. This prevents confusion and duplicate updates.
</details>

<details>
<summary><strong>Can I run this on a schedule?</strong></summary>

Absolutely! Set up a cron job (Unix) or Task Scheduler (Windows):
```bash
# Example: Daily at 9 AM
0 9 * * * cd ~/projects && ~/.local/bin/gittyup --quiet
```
</details>

<details>
<summary><strong>What if one repository fails?</strong></summary>

Gitty Up continues processing all other repositories. Failures are clearly reported at the end, and you can address them individually.
</details>

<details>
<summary><strong>Does it support SVN or Mercurial?</strong></summary>

No, Gitty Up is specifically designed for Git repositories. It's Git all the way down. 🐴
</details>

<details>
<summary><strong>What information does --explain show?</strong></summary>

Think of `--explain` as your guardian's detailed report card. It shows:
- **Every commit that was pulled**: Who wrote it, when they committed it, and the commit message
- **Exactly which files changed**: File paths with insertion/deletion counts
- **Why any repos were skipped**: Specific reasons like uncommitted changes or detached HEAD
- **Full error details**: Complete diagnostics for debugging any issues
- **Operation metadata**: When it ran, how long it took, versions used

Perfect when you need to understand what happened, debug an issue, or provide accountability for automated runs. No need to re-run the operation—your guardian remembers everything.
</details>

<details>
<summary><strong>Where are logs stored and how much space do they use?</strong></summary>

Your guardian stores logs in OS-specific cache directories using efficient key-value storage:
- **macOS**: `~/Library/Caches/gittyup/logs`
- **Linux**: `~/.cache/gittyup/logs`
- **Windows**: `C:\Users\<user>\AppData\Local\gittyup\logs`

Storage impact is minimal: each log is typically 10-50 KB. Even with 100 directories logged, total storage is only 1-5 MB. Each directory gets one log that's updated with each run, so space doesn't grow unbounded.
</details>

<details>
<summary><strong>Do dry runs create logs?</strong></summary>

No, dry runs (`--dry-run`) do not save logs. Your guardian only records actual operations that modify repositories. This keeps your history clean and focused on real changes, not "what if" scenarios.
</details>

<details>
<summary><strong>How does concurrent batch processing work?</strong></summary>

By default, Gitty Up updates repositories in batches of 3 simultaneously using async I/O operations. This dramatically improves performance when updating many repositories:

```bash
# Default: 3 repos at a time
gittyup ~/projects

# High performance: 5 repos at a time
gittyup ~/projects --batch-size 5

# Sequential (old behavior): 1 repo at a time
gittyup ~/projects --sync
```

**Benefits:**
- **Faster updates**: Network I/O happens concurrently while waiting for git operations
- **Controlled resources**: Batch size prevents overwhelming your system
- **Clear output**: Results are displayed in order after each batch completes

**When to adjust batch size:**
- **Increase** (`--batch-size 5-10`): Fast internet, powerful system, many repos
- **Decrease** (`--batch-size 1` or `--sync`): Debugging issues, slow connection, conservative approach

The concurrent processing is safe and respects all the same safety checks as sequential mode.
</details>

---

## 🚨 Troubleshooting

### Git Not Found
```
Error: Git is not installed or not found in PATH
```
**Fix:** Install Git and ensure it's in your system PATH:
```bash
# macOS
brew install git

# Linux (Debian/Ubuntu)  
sudo apt-get install git

# Verify
git --version
```

### Authentication Issues
```
Error: Authentication failed
```
**Fix:** Configure your Git credentials:
```bash
# SSH keys (recommended)
ssh-keygen -t ed25519 -C "your@email.com"
# Then add to GitHub/GitLab/etc.

# Or use credential helper
git config --global credential.helper store
```

### Permission Denied
```
Error: Permission denied
```
**Fix:** Ensure you have read access to the directories being scanned. Check file permissions or run with appropriate privileges.

### Network Timeouts
```
Error: Network error
```
**Fix:**
- Check your internet connection
- Verify remote URLs: `git remote -v`
- Check firewall settings
- Consider using `--max-depth` to reduce scope

### Log History Not Found
```
⚠️  No history found for: /path/to/directory
```
**Fix:**
- Run `gittyup` in this directory first (your guardian needs something to record!)
- Remember: logs are only created for actual operations (non-dry-run)
- Verify you're in the same directory where you previously ran gittyup
- Check that the cache directory has write permissions

### Cache Permission Errors
```
Error: Failed to save operation log
```
**Fix:**
- Ensure write access to cache directory:
  - macOS: `~/Library/Caches/gittyup/logs`
  - Linux: `~/.cache/gittyup/logs`
  - Windows: `C:\Users\<user>\AppData\Local\gittyup\logs`
- Check directory permissions: `ls -la ~/.cache/gittyup` (Unix/macOS)
- Create directory manually if needed: `mkdir -p ~/.cache/gittyup/logs`

---

## 🔧 Development & Contributing

Interested in contributing to Gitty Up or running it locally for development?

**📚 See the [Development Guide](docs/development.md)** for:
- Development setup instructions
- Testing and code quality guidelines
- Contributing guidelines and PR process
- Project architecture and design decisions
- Release process and versioning

We welcome contributions of all kinds—bug reports, feature requests, documentation improvements, and code contributions!

---

## 📊 Project Stats

<div align="center">

| Metric | Value |
|--------|-------|
| **Test Coverage** | 91.93% |
| **Total Tests** | 216 passing |
| **Code Quality** | Zero linting issues |
| **Python Version** | 3.13+ |
| **Dependencies** | Minimal (click, colorama, platformdirs, diskcache) |
| **Lines of Code** | ~2,100 |

</div>

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with ❤️ for developers who juggle too many projects and forget to `git pull`.

**Powered by:**
- [Click](https://click.palletsprojects.com/) - Command-line interface magic
- [Colorama](https://github.com/tartley/colorama) - Cross-platform colored output
- [platformdirs](https://github.com/platformdirs/platformdirs) - OS-specific directory paths
- [diskcache](https://github.com/grantjenks/python-diskcache) - Fast persistent caching
- [Ruff](https://github.com/astral-sh/ruff) - Lightning-fast Python linting

---

## 📌 Version

**Current Release:** `1.0.0`

See [change-log.md](change-log.md) for complete version history and release notes.

---

<div align="center">

**Made with 🐴 by developers, for developers**

[⬆ Back to Top](#-gitty-up)

</div>
