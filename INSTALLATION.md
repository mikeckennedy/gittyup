# 🚀 Gitty Up - Installation & Verification Guide

This guide provides step-by-step instructions for installing and verifying Gitty Up on your system.

---

## 📋 Prerequisites

Before installing Gitty Up, ensure you have:

- **Python 3.13 or later** installed on your system
- **Git** installed and available in your PATH
- **uv** package manager (recommended) or **pip**

### Check Prerequisites

```bash
# Check Python version (should be 3.13+)
python --version

# Check Git installation
git --version

# Check if uv is installed (optional but recommended)
uv --version
```

---

## 💿 Installation Methods

### Method 1: Global Tool Installation with uv (Recommended)

Install Gitty Up as a global CLI tool using `uv tool install`. This makes the `gittyup` command available system-wide without needing to activate a virtual environment.

```bash
# 1. Clone the repository
git clone https://github.com/mikeckennedy/gittyup
cd gittyup

# 2. Install as a global tool
uv tool install .

# That's it! The gittyup command is now available globally
gittyup --version
```

**Benefits:**
- ✅ No virtual environment activation needed
- ✅ Command available from anywhere
- ✅ Isolated environment managed by uv
- ✅ Perfect for CLI tools

**For Development (editable mode):**
```bash
# Install in editable mode to see changes immediately
uv tool install --editable .
```

**Managing the tool:**
```bash
# Update after changes
uv tool install --reinstall .

# Uninstall
uv tool uninstall gittyup

# List installed tools
uv tool list
```

### Method 2: Install from Source with Virtual Environment

Traditional installation method using a virtual environment.

```bash
# 1. Clone the repository
git clone https://github.com/mikeckennedy/gittyup
cd gittyup

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install in editable mode
uv pip install -e .
# Or with pip: pip install -e .
```

**Note:** With this method, you need to activate the venv each time before using `gittyup`.

### Method 2: Direct Installation (Future PyPI)

*Coming soon - once published to PyPI:*

```bash
# Install from PyPI (not yet available)
uv pip install gittyup
# Or: pip install gittyup
```

---

## ✅ Verification Steps

After installation, follow these steps to verify everything is working correctly.

### Step 1: Check Installation

```bash
# Verify the gittyup command is available
which gittyup

# Expected output (will vary by system):
# /Users/yourname/path/to/venv/bin/gittyup
```

### Step 2: Check Version

```bash
gittyup --version

# Expected output:
# Gitty Up version 1.0.0
```

✅ **If you see the version number, installation was successful!**

### Step 3: View Help

```bash
gittyup --help

# Expected output:
# Usage: gittyup [OPTIONS] [DIRECTORY]
# 
#   Gitty Up - Automatically discover and update all git repositories in a
#   directory tree.
# ...
```

✅ **If you see the help text with all options, the CLI is working correctly!**

### Step 4: Test with Dry Run

Create a test directory with a git repository:

```bash
# Create test directory structure
mkdir -p /tmp/gittyup-test/test-repo
cd /tmp/gittyup-test/test-repo

# Initialize a git repository
git init
git config user.email "test@example.com"
git config user.name "Test User"
echo "# Test" > README.md
git add README.md
git commit -m "Initial commit"

# Go back to parent directory and run gittyup
cd /tmp/gittyup-test
gittyup --dry-run
```

**Expected output:**
```
🐴 Gitty Up!
════════════════════════════════════════
Scanning directory: /tmp/gittyup-test
✓ Found 1 git repository

⊙ test-repo - Would attempt to update

════════════════════════════════════════
Summary
════════════════════════════════════════
Total repositories found: 1
  ⊙ Skipped: 1

Completed in 0.xx seconds
════════════════════════════════════════
```

✅ **If you see output like this, Gitty Up is working correctly!**

### Step 5: Clean Up Test

```bash
# Remove test directory
rm -rf /tmp/gittyup-test
```

---

## 🎯 Quick Start: Your First Real Run

Now that installation is verified, try it on your actual projects:

```bash
# Navigate to your projects directory
cd ~/projects  # or wherever your projects live

# Run gittyup (will show what needs updating)
gittyup

# Or do a dry run first to see what would happen
gittyup --dry-run
```

---

## 🔧 Troubleshooting

### Issue: Command Not Found

**Symptom:**
```bash
gittyup --version
# zsh: command not found: gittyup
```

**Solutions:**

1. **Make sure virtual environment is activated:**
   ```bash
   source venv/bin/activate
   # On Windows: venv\Scripts\activate
   ```

2. **Check if package is installed:**
   ```bash
   uv pip list | grep gittyup
   # Should show: gittyup 1.0.0
   ```

3. **Reinstall the package:**
   ```bash
   cd /path/to/gittyup
   uv pip install -e .
   ```

4. **Check Python's scripts directory is in PATH:**
   ```bash
   echo $PATH
   # Should include something like: /path/to/venv/bin
   ```

### Issue: Git Not Found

**Symptom:**
```bash
gittyup
# Git is not installed or not found in PATH. Please install Git to use Gitty Up.
```

**Solution:**

Install Git for your platform:

- **macOS:** `brew install git` or download from [git-scm.com](https://git-scm.com/)
- **Ubuntu/Debian:** `sudo apt-get install git`
- **Windows:** Download from [git-scm.com](https://git-scm.com/)

Then verify:
```bash
git --version
```

### Issue: Python Version Too Old

**Symptom:**
```bash
uv pip install -e .
# ERROR: This package requires Python >=3.13
```

**Solution:**

1. **Check your Python version:**
   ```bash
   python --version
   ```

2. **Install Python 3.13 or later:**
   - **macOS:** `brew install python@3.13`
   - **Ubuntu/Debian:** Use [deadsnakes PPA](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa)
   - **Windows:** Download from [python.org](https://www.python.org/downloads/)

3. **Create a new virtual environment with the correct Python:**
   ```bash
   python3.13 -m venv venv
   source venv/bin/activate
   uv pip install -e .
   ```

### Issue: Permission Denied Errors

**Symptom:**
```bash
gittyup ~/projects
# Permission denied: /some/directory
```

**Solution:**

This usually means Gitty Up encountered a directory it doesn't have permission to read. This is normal and expected. Gitty Up will skip these directories and continue scanning.

If you need to access these directories:
```bash
# On Unix-like systems, you might need to adjust permissions
chmod +r /path/to/directory

# Or run with sudo (not recommended for security reasons)
sudo gittyup ~/projects
```

### Issue: Import Errors

**Symptom:**
```bash
gittyup
# ModuleNotFoundError: No module named 'colorama'
```

**Solution:**

Dependencies weren't installed correctly. Reinstall:
```bash
cd /path/to/gittyup
uv pip install -e .
```

Or install dependencies manually:
```bash
uv pip install colorama click
```

---

## 🧪 Running Tests (For Developers)

If you're contributing to Gitty Up or want to verify the test suite:

```bash
# Navigate to project directory
cd /path/to/gittyup

# Activate virtual environment
source venv/bin/activate

# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov

# Run specific test file
pytest tests/test_cli.py -v
```

**Expected output:**
```
======================== 115 passed in 0.17s =========================
```

---

## 🔄 Updating Gitty Up

To update to the latest version:

```bash
# Navigate to the gittyup directory
cd /path/to/gittyup

# Pull latest changes
git pull

# Reinstall (in case dependencies changed)
uv pip install -e .

# Verify new version
gittyup --version
```

---

## 🗑️ Uninstallation

To completely remove Gitty Up:

```bash
# Uninstall the package
uv pip uninstall gittyup

# Optionally, remove the source directory
rm -rf /path/to/gittyup

# Deactivate and remove virtual environment
deactivate
rm -rf venv
```

---

## 📊 Verification Checklist

Use this checklist to ensure everything is working:

- [ ] Python 3.13+ installed
- [ ] Git installed and in PATH
- [ ] Virtual environment created and activated
- [ ] Gitty Up installed successfully
- [ ] `gittyup --version` shows version 1.0.0
- [ ] `gittyup --help` shows usage information
- [ ] Test run with `--dry-run` works correctly
- [ ] Can scan and update actual repositories

---

## 💡 Tips for Success

1. **Always activate your virtual environment** before using gittyup
2. **Use `--dry-run` first** when trying on a new directory
3. **Start with a small directory** to test before running on large directory trees
4. **Check `--help`** to see all available options
5. **Use `--verbose`** to see detailed information during updates

---

## 🆘 Getting Help

If you're still having issues:

1. **Check the [readme.md](readme.md)** for comprehensive documentation
2. **Review the [FAQ section](readme.md#-faq)** for common questions
3. **Search [GitHub Issues](https://github.com/mikeckennedy/gittyup/issues)** for similar problems
4. **Open a new issue** with:
   - Your operating system and version
   - Python version (`python --version`)
   - Git version (`git --version`)
   - Complete error message
   - Steps to reproduce

---

## ✅ Installation Complete!

**Congratulations!** 🎉 You've successfully installed and verified Gitty Up!

You're now ready to automatically update all your Git repositories with a single command.

### Quick Reference

```bash
# Update all repos in current directory
gittyup

# Update repos in specific directory
gittyup ~/projects

# Preview changes without updating
gittyup --dry-run

# Show detailed output
gittyup --verbose

# Show only errors
gittyup --quiet
```

**Happy coding! Never forget to pull again!** 🐴

---

*Last updated: October 15, 2025*

