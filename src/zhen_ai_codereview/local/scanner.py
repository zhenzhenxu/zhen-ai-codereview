"""
Local code scanner for reviewing files and git changes
"""

import fnmatch
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import git

from ..config import ReviewConfig


@dataclass
class FileInfo:
    """Information about a local file"""
    path: str
    relative_path: str
    content: str
    size: int


@dataclass
class GitChange:
    """Git change information"""
    filename: str
    status: str  # A (added), M (modified), D (deleted), R (renamed)
    diff: Optional[str]
    content: Optional[str]


class LocalScanner:
    """Scanner for local code files and git repositories"""

    def __init__(self, config: ReviewConfig):
        self.config = config

    def _should_include(self, filename: str) -> bool:
        """Check if file should be included based on patterns"""
        # Check exclude patterns first
        for pattern in self.config.exclude_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return False

        # Check include patterns
        for pattern in self.config.include_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True

        return False

    def scan_directory(self, directory: str, recursive: bool = True) -> list[FileInfo]:
        """
        Scan directory for code files

        Args:
            directory: Path to directory to scan
            recursive: Whether to scan subdirectories

        Returns:
            List of FileInfo objects for matching files
        """
        directory = os.path.abspath(directory)
        files = []

        if recursive:
            for root, _, filenames in os.walk(directory):
                # Skip hidden directories and common non-code directories
                if any(part.startswith('.') or part in ['node_modules', 'venv', '__pycache__', 'dist', 'build']
                       for part in Path(root).parts):
                    continue

                for filename in filenames:
                    if self._should_include(filename):
                        file_path = os.path.join(root, filename)
                        file_info = self._read_file(file_path, directory)
                        if file_info:
                            files.append(file_info)
        else:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path) and self._should_include(filename):
                    file_info = self._read_file(file_path, directory)
                    if file_info:
                        files.append(file_info)

        return files

    def scan_files(self, file_paths: list[str]) -> list[FileInfo]:
        """
        Scan specific files

        Args:
            file_paths: List of file paths to scan

        Returns:
            List of FileInfo objects
        """
        files = []
        for file_path in file_paths:
            abs_path = os.path.abspath(file_path)
            file_info = self._read_file(abs_path, os.path.dirname(abs_path))
            if file_info:
                files.append(file_info)
        return files

    def _read_file(self, file_path: str, base_dir: str) -> Optional[FileInfo]:
        """Read file and return FileInfo if valid"""
        try:
            size = os.path.getsize(file_path)
            if size > self.config.max_file_size:
                return None

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            return FileInfo(
                path=file_path,
                relative_path=os.path.relpath(file_path, base_dir),
                content=content,
                size=size,
            )
        except (IOError, OSError):
            return None

    def get_git_changes(
        self,
        repo_path: str,
        base_ref: str = "HEAD~1",
        head_ref: str = "HEAD",
    ) -> list[GitChange]:
        """
        Get changed files between two git refs

        Args:
            repo_path: Path to git repository
            base_ref: Base reference (default: HEAD~1)
            head_ref: Head reference (default: HEAD)

        Returns:
            List of GitChange objects
        """
        try:
            repo = git.Repo(repo_path)
        except git.InvalidGitRepositoryError:
            raise ValueError(f"{repo_path} is not a valid git repository")

        changes = []

        # Get diff between refs
        try:
            diffs = repo.commit(base_ref).diff(head_ref)
        except git.BadName:
            # If base_ref doesn't exist (e.g., first commit), diff against empty tree
            diffs = repo.head.commit.diff(git.NULL_TREE)

        for diff in diffs:
            filename = diff.b_path or diff.a_path

            if not self._should_include(filename):
                continue

            # Determine status
            if diff.new_file:
                status = "A"
            elif diff.deleted_file:
                status = "D"
            elif diff.renamed:
                status = "R"
            else:
                status = "M"

            # Get diff text
            try:
                diff_text = diff.diff.decode('utf-8', errors='ignore') if diff.diff else None
            except Exception:
                diff_text = None

            # Get file content (for non-deleted files)
            content = None
            if status != "D":
                try:
                    file_path = os.path.join(repo_path, filename)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except (IOError, OSError):
                    pass

            changes.append(GitChange(
                filename=filename,
                status=status,
                diff=diff_text,
                content=content,
            ))

        return changes

    def get_staged_changes(self, repo_path: str) -> list[GitChange]:
        """
        Get staged (but not committed) changes

        Args:
            repo_path: Path to git repository

        Returns:
            List of GitChange objects for staged files
        """
        try:
            repo = git.Repo(repo_path)
        except git.InvalidGitRepositoryError:
            raise ValueError(f"{repo_path} is not a valid git repository")

        changes = []
        diffs = repo.index.diff("HEAD")

        for diff in diffs:
            filename = diff.b_path or diff.a_path

            if not self._should_include(filename):
                continue

            if diff.new_file:
                status = "A"
            elif diff.deleted_file:
                status = "D"
            else:
                status = "M"

            try:
                diff_text = diff.diff.decode('utf-8', errors='ignore') if diff.diff else None
            except Exception:
                diff_text = None

            content = None
            if status != "D":
                try:
                    file_path = os.path.join(repo_path, filename)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except (IOError, OSError):
                    pass

            changes.append(GitChange(
                filename=filename,
                status=status,
                diff=diff_text,
                content=content,
            ))

        return changes
