"""Tests for always-ignored files functionality (Issue #2)."""

from pathlib import Path

import pytest

from gittyup.git_operations import ALWAYS_IGNORED_FILES, has_only_untracked_files, should_ignore_file
from gittyup.models import UncommittedFile


class TestShouldIgnoreFile:
    """Tests for the should_ignore_file function."""

    def test_ignore_ds_store(self) -> None:
        """Test that .DS_Store files are ignored."""
        assert should_ignore_file(".DS_Store")
        assert should_ignore_file("src/.DS_Store")
        assert should_ignore_file("path/to/project/.DS_Store")

    def test_ignore_thumbs_db(self) -> None:
        """Test that Thumbs.db files are ignored."""
        assert should_ignore_file("Thumbs.db")
        assert should_ignore_file("images/Thumbs.db")
        assert should_ignore_file("path/to/photos/Thumbs.db")

    def test_ignore_pycache(self) -> None:
        """Test that __pycache__ directories and their contents are ignored."""
        assert should_ignore_file("__pycache__")
        assert should_ignore_file("src/__pycache__")
        assert should_ignore_file("__pycache__/module.pyc")
        assert should_ignore_file("src/__pycache__/module.pyc")

    def test_do_not_ignore_regular_files(self) -> None:
        """Test that regular files are not ignored."""
        assert not should_ignore_file("readme.md")
        assert not should_ignore_file("src/main.py")
        assert not should_ignore_file("test.txt")
        assert not should_ignore_file(".gitignore")

    def test_case_sensitivity(self) -> None:
        """Test that file names are case-sensitive."""
        # Should not ignore variations in case
        assert not should_ignore_file(".ds_store")
        assert not should_ignore_file("thumbs.db")
        # But should ignore exact matches
        assert should_ignore_file(".DS_Store")
        assert should_ignore_file("Thumbs.db")


class TestHasOnlyUntrackedFiles:
    """Tests for has_only_untracked_files with always-ignored files."""

    def test_empty_list(self) -> None:
        """Test that empty list returns True."""
        assert has_only_untracked_files([])

    def test_only_ds_store(self) -> None:
        """Test that only .DS_Store file is treated as clean."""
        files = [
            UncommittedFile(path=".DS_Store", status="??", status_description="Untracked"),
        ]
        assert has_only_untracked_files(files)

    def test_only_thumbs_db(self) -> None:
        """Test that only Thumbs.db file is treated as clean."""
        files = [
            UncommittedFile(path="Thumbs.db", status="??", status_description="Untracked"),
        ]
        assert has_only_untracked_files(files)

    def test_only_pycache(self) -> None:
        """Test that only __pycache__ files are treated as clean."""
        files = [
            UncommittedFile(path="__pycache__/module.pyc", status="??", status_description="Untracked"),
        ]
        assert has_only_untracked_files(files)

    def test_multiple_ignored_files(self) -> None:
        """Test that multiple ignored files are treated as clean."""
        files = [
            UncommittedFile(path=".DS_Store", status="??", status_description="Untracked"),
            UncommittedFile(path="Thumbs.db", status="??", status_description="Untracked"),
            UncommittedFile(path="__pycache__/module.pyc", status="??", status_description="Untracked"),
        ]
        assert has_only_untracked_files(files)

    def test_ignored_plus_regular_untracked(self) -> None:
        """Test that ignored files plus regular untracked files returns True."""
        files = [
            UncommittedFile(path=".DS_Store", status="??", status_description="Untracked"),
            UncommittedFile(path="test.txt", status="??", status_description="Untracked"),
        ]
        # Regular untracked files should still be treated as "only untracked"
        assert has_only_untracked_files(files)

    def test_ignored_plus_modified(self) -> None:
        """Test that ignored files plus modified files returns False."""
        files = [
            UncommittedFile(path=".DS_Store", status="??", status_description="Untracked"),
            UncommittedFile(path="src/main.py", status="M", status_description="Modified"),
        ]
        assert not has_only_untracked_files(files)

    def test_ignored_plus_staged(self) -> None:
        """Test that ignored files plus staged files returns False."""
        files = [
            UncommittedFile(path=".DS_Store", status="??", status_description="Untracked"),
            UncommittedFile(path="src/main.py", status="A", status_description="Added"),
        ]
        assert not has_only_untracked_files(files)

    def test_only_modified(self) -> None:
        """Test that only modified files returns False."""
        files = [
            UncommittedFile(path="src/main.py", status="M", status_description="Modified"),
        ]
        assert not has_only_untracked_files(files)

    def test_nested_ignored_files(self) -> None:
        """Test that nested ignored files are treated as clean."""
        files = [
            UncommittedFile(path="src/.DS_Store", status="??", status_description="Untracked"),
            UncommittedFile(path="images/Thumbs.db", status="??", status_description="Untracked"),
            UncommittedFile(path="src/__pycache__/module.pyc", status="??", status_description="Untracked"),
        ]
        assert has_only_untracked_files(files)


class TestAlwaysIgnoredFilesConstant:
    """Test the ALWAYS_IGNORED_FILES constant."""

    def test_contains_expected_files(self) -> None:
        """Test that the constant contains all expected files."""
        assert ".DS_Store" in ALWAYS_IGNORED_FILES
        assert "Thumbs.db" in ALWAYS_IGNORED_FILES
        assert "__pycache__" in ALWAYS_IGNORED_FILES

    def test_is_set_type(self) -> None:
        """Test that ALWAYS_IGNORED_FILES is a set for fast lookups."""
        assert isinstance(ALWAYS_IGNORED_FILES, set)


@pytest.mark.integration
class TestIntegrationWithGitOperations:
    """Integration tests with actual git operations."""

    def test_repo_with_only_ds_store_treated_as_clean(self, tmp_path: Path) -> None:
        """Test that a repo with only .DS_Store is treated as clean."""
        import subprocess

        # Create a git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True, capture_output=True
        )
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True, capture_output=True)

        # Create an initial commit
        (repo_path / "readme.md").write_text("# Test\n")
        subprocess.run(["git", "add", "readme.md"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True, capture_output=True)

        # Add .DS_Store file
        (repo_path / ".DS_Store").write_text("dummy content")

        # Check that repository status is clean (ignoring .DS_Store)
        from gittyup.git_operations import get_repo_status

        status = get_repo_status(repo_path)
        assert status["is_clean"]

    def test_repo_with_only_thumbs_db_treated_as_clean(self, tmp_path: Path) -> None:
        """Test that a repo with only Thumbs.db is treated as clean."""
        import subprocess

        # Create a git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True, capture_output=True
        )
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True, capture_output=True)

        # Create an initial commit
        (repo_path / "readme.md").write_text("# Test\n")
        subprocess.run(["git", "add", "readme.md"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True, capture_output=True)

        # Add Thumbs.db file
        (repo_path / "Thumbs.db").write_text("dummy content")

        # Check that repository status is clean (ignoring Thumbs.db)
        from gittyup.git_operations import get_repo_status

        status = get_repo_status(repo_path)
        assert status["is_clean"]

    def test_repo_with_pycache_treated_as_clean(self, tmp_path: Path) -> None:
        """Test that a repo with only __pycache__ files is treated as clean."""
        import subprocess

        # Create a git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True, capture_output=True
        )
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True, capture_output=True)

        # Create an initial commit
        (repo_path / "readme.md").write_text("# Test\n")
        subprocess.run(["git", "add", "readme.md"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True, capture_output=True)

        # Add __pycache__ directory with files
        pycache_dir = repo_path / "__pycache__"
        pycache_dir.mkdir()
        (pycache_dir / "module.pyc").write_text("dummy content")

        # Check that repository status is clean (ignoring __pycache__)
        from gittyup.git_operations import get_repo_status

        status = get_repo_status(repo_path)
        assert status["is_clean"]

    def test_repo_with_ignored_plus_real_change_not_clean(self, tmp_path: Path) -> None:
        """Test that a repo with ignored files plus real changes is not clean."""
        import subprocess

        # Create a git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True, capture_output=True
        )
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True, capture_output=True)

        # Create an initial commit
        readme = repo_path / "readme.md"
        readme.write_text("# Test\n")
        subprocess.run(["git", "add", "readme.md"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True, capture_output=True)

        # Add .DS_Store file
        (repo_path / ".DS_Store").write_text("dummy content")

        # Modify the readme file
        readme.write_text("# Test Modified\n")

        # Check that repository status is NOT clean (has real modification)
        from gittyup.git_operations import get_repo_status

        status = get_repo_status(repo_path)
        assert not status["is_clean"]
