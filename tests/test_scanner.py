"""Tests for directory scanning and repository detection."""

from pathlib import Path

from gittyup.models import RepoStatus
from gittyup.scanner import (
    find_repositories,
    is_git_repository,
    scan_directory,
    should_exclude_directory,
)


class TestIsGitRepository:
    """Tests for git repository detection."""

    def test_identifies_git_repo(self, tmp_path: Path) -> None:
        """Test that a directory with .git is identified as a git repo."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        assert is_git_repository(tmp_path)

    def test_non_git_directory(self, tmp_path: Path) -> None:
        """Test that a directory without .git is not identified as a git repo."""
        assert not is_git_repository(tmp_path)

    def test_git_file_not_directory(self, tmp_path: Path) -> None:
        """Test that a .git file (not directory) is not considered a git repo."""
        git_file = tmp_path / ".git"
        git_file.touch()

        assert not is_git_repository(tmp_path)

    def test_file_path_returns_false(self, tmp_path: Path) -> None:
        """Test that passing a file path returns False."""
        file_path = tmp_path / "test.txt"
        file_path.touch()

        assert not is_git_repository(file_path)


class TestShouldExcludeDirectory:
    """Tests for directory exclusion logic."""

    def test_excludes_default_directories(self, tmp_path: Path) -> None:
        """Test that default exclude directories are properly excluded."""
        for dir_name in ["node_modules", "venv", ".venv", "__pycache__"]:
            test_dir = tmp_path / dir_name
            assert should_exclude_directory(test_dir)

    def test_does_not_exclude_normal_directory(self, tmp_path: Path) -> None:
        """Test that normal directories are not excluded."""
        normal_dir = tmp_path / "my_project"
        assert not should_exclude_directory(normal_dir)

    def test_custom_exclude_patterns(self, tmp_path: Path) -> None:
        """Test that custom exclude patterns work."""
        custom_dir = tmp_path / "custom_exclude"
        exclude_patterns = {"custom_exclude"}

        assert should_exclude_directory(custom_dir, exclude_patterns)

    def test_custom_patterns_merge_with_defaults(self, tmp_path: Path) -> None:
        """Test that custom patterns are merged with defaults."""
        venv_dir = tmp_path / "venv"
        custom_dir = tmp_path / "custom"
        exclude_patterns = {"custom"}

        assert should_exclude_directory(venv_dir, exclude_patterns)
        assert should_exclude_directory(custom_dir, exclude_patterns)


class TestScanDirectory:
    """Tests for directory scanning functionality."""

    def test_scan_empty_directory(self, tmp_path: Path) -> None:
        """Test scanning an empty directory finds no repos."""
        result = scan_directory(tmp_path)

        assert result.total_repos == 0
        assert not result.has_errors
        assert result.scan_root == tmp_path.resolve()

    def test_scan_single_repository(self, tmp_path: Path) -> None:
        """Test scanning finds a single git repository."""
        repo_dir = tmp_path / "my_repo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()

        result = scan_directory(tmp_path)

        assert result.total_repos == 1
        assert result.repositories[0].path == repo_dir
        assert result.repositories[0].name == "my_repo"
        assert result.repositories[0].status == RepoStatus.PENDING

    def test_scan_multiple_repositories(self, tmp_path: Path) -> None:
        """Test scanning finds multiple git repositories."""
        for i in range(3):
            repo_dir = tmp_path / f"repo_{i}"
            repo_dir.mkdir()
            (repo_dir / ".git").mkdir()

        result = scan_directory(tmp_path)

        assert result.total_repos == 3
        repo_names = {repo.name for repo in result.repositories}
        assert repo_names == {"repo_0", "repo_1", "repo_2"}

    def test_scan_nested_directories(self, tmp_path: Path) -> None:
        """Test scanning finds repos in nested directory structures."""
        # Create nested structure: tmp_path/parent/child/repo
        parent = tmp_path / "parent"
        parent.mkdir()
        child = parent / "child"
        child.mkdir()
        repo = child / "my_repo"
        repo.mkdir()
        (repo / ".git").mkdir()

        result = scan_directory(tmp_path)

        assert result.total_repos == 1
        assert result.repositories[0].name == "my_repo"

    def test_does_not_traverse_into_git_repos(self, tmp_path: Path) -> None:
        """Test that scanner doesn't traverse into git repositories."""
        # Create outer repo with nested .git-like directory inside
        repo_dir = tmp_path / "outer_repo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()

        # Create a directory inside that looks like a repo
        inner_dir = repo_dir / "subdir"
        inner_dir.mkdir()
        (inner_dir / ".git").mkdir()

        result = scan_directory(tmp_path)

        # Should only find the outer repo
        assert result.total_repos == 1
        assert result.repositories[0].name == "outer_repo"

    def test_excludes_directories(self, tmp_path: Path) -> None:
        """Test that excluded directories are skipped."""
        # Create repos in normal and excluded directories
        normal_repo = tmp_path / "normal_repo"
        normal_repo.mkdir()
        (normal_repo / ".git").mkdir()

        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()
        excluded_repo = venv_dir / "excluded_repo"
        excluded_repo.mkdir()
        (excluded_repo / ".git").mkdir()

        result = scan_directory(tmp_path)

        # Should only find the normal repo
        assert result.total_repos == 1
        assert result.repositories[0].name == "normal_repo"
        assert len(result.skipped_paths) > 0

    def test_handles_nonexistent_path(self, tmp_path: Path) -> None:
        """Test that scanning a nonexistent path reports an error."""
        nonexistent = tmp_path / "does_not_exist"

        result = scan_directory(nonexistent)

        assert result.total_repos == 0
        assert result.has_errors
        assert len(result.errors) == 1
        assert result.errors[0][0] == nonexistent.resolve()

    def test_handles_file_path(self, tmp_path: Path) -> None:
        """Test that scanning a file path reports an error."""
        file_path = tmp_path / "test.txt"
        file_path.touch()

        result = scan_directory(file_path)

        assert result.total_repos == 0
        assert result.has_errors
        assert "not a directory" in result.errors[0][1].lower()

    def test_max_depth_limits_traversal(self, tmp_path: Path) -> None:
        """Test that max_depth parameter limits directory traversal."""
        # Create nested structure: tmp_path/level1/level2/level3/repo
        level1 = tmp_path / "level1"
        level1.mkdir()
        level2 = level1 / "level2"
        level2.mkdir()
        level3 = level2 / "level3"
        level3.mkdir()
        repo = level3 / "deep_repo"
        repo.mkdir()
        (repo / ".git").mkdir()

        # Scan with max_depth=1, should not find the deep repo
        result = scan_directory(tmp_path, max_depth=1)
        assert result.total_repos == 0

        # Scan with max_depth=10, should find it
        result = scan_directory(tmp_path, max_depth=10)
        assert result.total_repos == 1

    def test_custom_exclude_patterns(self, tmp_path: Path) -> None:
        """Test scanning with custom exclude patterns."""
        # Create normal repo
        normal_repo = tmp_path / "normal"
        normal_repo.mkdir()
        (normal_repo / ".git").mkdir()

        # Create custom excluded directory
        custom_dir = tmp_path / "my_special_dir"
        custom_dir.mkdir()
        excluded_repo = custom_dir / "repo"
        excluded_repo.mkdir()
        (excluded_repo / ".git").mkdir()

        # Scan with custom exclusion
        result = scan_directory(tmp_path, exclude_patterns={"my_special_dir"})

        assert result.total_repos == 1
        assert result.repositories[0].name == "normal"


class TestFindRepositories:
    """Tests for the convenience function find_repositories."""

    def test_returns_list_of_paths(self, tmp_path: Path) -> None:
        """Test that find_repositories returns a list of Path objects."""
        for i in range(2):
            repo_dir = tmp_path / f"repo_{i}"
            repo_dir.mkdir()
            (repo_dir / ".git").mkdir()

        repos = find_repositories(tmp_path)

        assert len(repos) == 2
        assert all(isinstance(repo, Path) for repo in repos)
        repo_names = {repo.name for repo in repos}
        assert repo_names == {"repo_0", "repo_1"}

    def test_returns_empty_list_when_no_repos(self, tmp_path: Path) -> None:
        """Test that find_repositories returns empty list when no repos found."""
        repos = find_repositories(tmp_path)
        assert repos == []


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_handles_symlinks(self, tmp_path: Path) -> None:
        """Test that scanner handles symlinks correctly."""
        # Create a real repo
        real_repo = tmp_path / "real_repo"
        real_repo.mkdir()
        (real_repo / ".git").mkdir()

        # Create a symlink to it
        symlink = tmp_path / "linked_repo"
        symlink.symlink_to(real_repo)

        result = scan_directory(tmp_path)

        # Should find both (or handle appropriately based on visited tracking)
        assert result.total_repos >= 1

    def test_handles_broken_symlinks(self, tmp_path: Path) -> None:
        """Test that scanner handles broken symlinks gracefully."""
        # Create a symlink to a nonexistent target
        broken_link = tmp_path / "broken_link"
        nonexistent = tmp_path / "nonexistent"
        broken_link.symlink_to(nonexistent)

        # Scanner should not crash
        result = scan_directory(tmp_path)

        # The broken symlink should be skipped
        assert broken_link in result.skipped_paths

    def test_accepts_string_path(self, tmp_path: Path) -> None:
        """Test that scanner accepts string paths as well as Path objects."""
        repo_dir = tmp_path / "my_repo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()

        result = scan_directory(str(tmp_path))

        assert result.total_repos == 1
        assert result.repositories[0].name == "my_repo"

    def test_scan_result_helper_methods(self, tmp_path: Path) -> None:
        """Test ScanResult helper methods."""
        result = scan_directory(tmp_path)

        # Test add_repository
        repo = result.add_repository(tmp_path / "test_repo")
        assert repo in result.repositories
        assert repo.name == "test_repo"

        # Test add_error
        result.add_error(tmp_path / "error_path", "Test error")
        assert result.has_errors
        assert len(result.errors) == 1

        # Test add_skipped_path
        result.add_skipped_path(tmp_path / "skipped")
        assert tmp_path / "skipped" in result.skipped_paths

    def test_handles_symlink_to_file(self, tmp_path: Path) -> None:
        """Test that scanner skips symlinks pointing to files."""
        # Create a file
        file_path = tmp_path / "test.txt"
        file_path.write_text("test content")

        # Create a symlink to the file
        symlink = tmp_path / "link_to_file"
        symlink.symlink_to(file_path)

        # Scanner should not crash and should skip the file symlink
        result = scan_directory(tmp_path)

        assert result.total_repos == 0
        # The symlink to a file should be skipped silently (not counted as an error)

    def test_circular_reference_detection(self, tmp_path: Path) -> None:
        """Test that scanner handles circular symlink references."""
        # Create a directory structure with circular symlinks
        dir_a = tmp_path / "dir_a"
        dir_a.mkdir()
        dir_b = dir_a / "dir_b"
        dir_b.mkdir()

        # Create a symlink from dir_b back to dir_a (circular reference)
        circular_link = dir_b / "link_to_a"
        circular_link.symlink_to(dir_a)

        # Scanner should handle this without infinite recursion
        result = scan_directory(tmp_path)

        # Should complete without errors (visited set prevents infinite loop)
        assert result.total_repos == 0
