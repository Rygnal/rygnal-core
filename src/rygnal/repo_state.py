"""Repository state detection and safety validation.

This module protects uncommitted developer work by ensuring Rygnal does
not execute guarded runs in a dirty repository unless explicitly overridden.
"""

from __future__ import annotations

import os
import subprocess  # nosec B404
from dataclasses import dataclass, field
from pathlib import Path


class DirtyRepositoryError(Exception):
    """Raised when uncommitted changes are detected in the trusted repository."""


@dataclass(frozen=True)
class RepoChanges:
    """Categorized uncommitted changes in a Git repository."""

    staged: list[str] = field(default_factory=list)
    unstaged: list[str] = field(default_factory=list)
    untracked: list[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not (self.staged or self.unstaged or self.untracked)


def _run_git(args: list[str], cwd: Path) -> str:
    """Execute a git command securely without host environment leakage."""
    env = os.environ.copy()
    env.pop("GIT_WORK_TREE", None)
    env.pop("GIT_DIR", None)

    try:
        result = subprocess.run(  # nosec B603 B607
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() or e.stdout.strip()
        raise RuntimeError(f"Git operation failed: {error_msg}") from e


def get_uncommitted_changes(repo_path: Path) -> RepoChanges:
    """Parse git status to detect staged, unstaged, and untracked files."""
    output = _run_git(["status", "--porcelain"], cwd=repo_path)
    if not output.strip():
        return RepoChanges()

    staged: list[str] = []
    unstaged: list[str] = []
    untracked: list[str] = []

    for line in output.splitlines():
        if len(line) < 4:
            continue

        # Format is 'XY PATH'. X is index (staged), Y is working tree (unstaged).
        status_x = line[0]
        status_y = line[1]
        path = line[3:]

        if status_x == "?" and status_y == "?":
            untracked.append(path)
            continue

        if status_x not in (" ", "?"):
            staged.append(path)
        if status_y not in (" ", "?"):
            unstaged.append(path)

    return RepoChanges(staged=staged, unstaged=unstaged, untracked=untracked)


def verify_repo_is_clean(repo_path: Path, allow_dirty_override: bool = False) -> None:
    """Ensure the repository has no uncommitted changes to protect developer work.

    Raises:
        DirtyRepositoryError: If changes are found and override is False.
    """
    changes = get_uncommitted_changes(repo_path)
    if changes.is_clean:
        return

    if allow_dirty_override:
        # In a full system this would trigger an audit log warning.
        return

    error_lines = ["Uncommitted changes detected in trusted repository:"]
    if changes.staged:
        error_lines.append(f"  Staged: {len(changes.staged)} files")
    if changes.unstaged:
        error_lines.append(f"  Unstaged: {len(changes.unstaged)} files")
    if changes.untracked:
        error_lines.append(f"  Untracked: {len(changes.untracked)} files")

    error_lines.append("\nRygnal guarded execution blocked to prevent data loss.")
    error_lines.append("Please commit your changes, or pass allow_dirty_override=True.")

    raise DirtyRepositoryError("\n".join(error_lines))
