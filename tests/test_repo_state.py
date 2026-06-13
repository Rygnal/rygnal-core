import subprocess  # nosec B404
from pathlib import Path

import pytest

from rygnal.repo_state import DirtyRepositoryError, get_uncommitted_changes, verify_repo_is_clean


@pytest.fixture
def mock_repo(tmp_path: Path) -> Path:
    repo_dir = tmp_path / "trusted_repo"
    repo_dir.mkdir()

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)  # nosec
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_dir, check=True)  # nosec
    subprocess.run(["git", "config", "user.email", "t@rygnal.local"], cwd=repo_dir, check=True)  # nosec

    (repo_dir / "base.txt").write_text("baseline")
    subprocess.run(["git", "add", "base.txt"], cwd=repo_dir, check=True)  # nosec
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True)  # nosec

    return repo_dir


def test_clean_repo_passes(mock_repo: Path) -> None:
    verify_repo_is_clean(mock_repo)
    changes = get_uncommitted_changes(mock_repo)
    assert changes.is_clean


def test_detects_untracked_file(mock_repo: Path) -> None:
    (mock_repo / "new.txt").write_text("hello")

    changes = get_uncommitted_changes(mock_repo)
    assert "new.txt" in changes.untracked
    assert not changes.is_clean

    with pytest.raises(DirtyRepositoryError, match="Untracked: 1 files"):
        verify_repo_is_clean(mock_repo)


def test_detects_unstaged_modification(mock_repo: Path) -> None:
    (mock_repo / "base.txt").write_text("modified")

    changes = get_uncommitted_changes(mock_repo)
    assert "base.txt" in changes.unstaged
    assert not changes.is_clean

    with pytest.raises(DirtyRepositoryError, match="Unstaged: 1 files"):
        verify_repo_is_clean(mock_repo)


def test_detects_staged_addition(mock_repo: Path) -> None:
    (mock_repo / "staged.txt").write_text("added")
    subprocess.run(["git", "add", "staged.txt"], cwd=mock_repo, check=True)  # nosec

    changes = get_uncommitted_changes(mock_repo)
    assert "staged.txt" in changes.staged
    assert not changes.is_clean

    with pytest.raises(DirtyRepositoryError, match="Staged: 1 files"):
        verify_repo_is_clean(mock_repo)


def test_allow_override_bypasses_error(mock_repo: Path) -> None:
    (mock_repo / "new.txt").write_text("hello")

    # Must raise without override
    with pytest.raises(DirtyRepositoryError):
        verify_repo_is_clean(mock_repo, allow_dirty_override=False)

    # Must pass silently with override
    verify_repo_is_clean(mock_repo, allow_dirty_override=True)
