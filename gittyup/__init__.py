"""Gitty Up - Automatically discover and update all git repositories in a directory tree."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("gittyup")
except PackageNotFoundError:
    # Package is not installed, fallback to a default version
    __version__ = "1.0.0.dev"
