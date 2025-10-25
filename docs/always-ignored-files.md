# Always-Ignored Files Feature

## Overview

Gittyup automatically ignores certain common system and cache files when determining if a repository has uncommitted changes. This prevents repositories from being skipped unnecessarily when only these non-essential files are present.

## Always-Ignored Files

The following files and directories are automatically ignored:

- **`.DS_Store`** - macOS file system metadata files
- **`Thumbs.db`** - Windows thumbnail cache files
- **`__pycache__`** - Python bytecode cache directories

## How It Works

When gittyup checks if a repository has uncommitted changes:

1. It gets the list of uncommitted files from git
2. It filters out any files from the always-ignored list
3. If only ignored files remain (or the list is empty), the repository is treated as **clean**
4. The repository can then be updated normally

## Examples

### Example 1: Repository with only .DS_Store

```
$ gittyup
✓ my-project
   Already up-to-date
```

Even though `.DS_Store` is present as an untracked file, gittyup treats the repository as clean and updates it.

### Example 2: Repository with .DS_Store and modified files

```
$ gittyup
⏭️ my-project
   Skipped
   Reason: Repository has uncommitted changes
   
   📝 Uncommitted files (2):
      Untracked            .DS_Store
      Modified             src/main.py
```

The repository is skipped because it has a real uncommitted change (`src/main.py`), even though `.DS_Store` would normally be ignored.

### Example 3: Repository with only __pycache__ files

```
$ gittyup
✓ my-python-project
   Already up-to-date
```

Python bytecode files in `__pycache__/` directories are automatically ignored.

## Implementation Details

The filtering happens at two levels:

1. **`should_ignore_file(file_path)`** - Checks if a file should be ignored
   - Matches against the file name
   - Matches against any directory component in the path
   
2. **`has_only_untracked_files(uncommitted_files)`** - Determines if files are safe to ignore
   - Filters out always-ignored files
   - Checks if remaining files are only untracked (not modified/staged)

## Compatibility

This feature works with:
- Both sync and async git operations
- The `--ignore-untracked` flag (when enabled)
- All gittyup output modes (normal, verbose, quiet)
- The `--explain` logging feature

## Related

- GitHub Issue #2: https://github.com/mikeckennedy/gittyup/issues/2
- `--ignore-untracked` flag documentation (for handling other untracked files)

