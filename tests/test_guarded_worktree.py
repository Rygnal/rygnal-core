import subprocess
from pathlib import Path

import pytest

from rygnal.guarded_worktree import (
    GuardedWorktreeConfig,
    GuardedWorktreeError,
    create_guarded_worktree,
    detect_trusted_repo_root,
    run_unsafe_local_for_testing,
)


@pytest.fixture
def mock_trusted_repo(tmp_path: Path) -> Path:
    """Fixture that initializes a real, non-bare Git repository."""
    repo_dir = tmp_path / "trusted_repo"
    repo_dir.mkdir()

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@rygnal.local"], cwd=repo_dir, check=True)

    # Need at least one commit so HEAD exists
    (repo_dir / "base.txt").write_text("baseline content")
    subprocess.run(["git", "add", "base.txt"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True)

    return repo_dir


@pytest.fixture
def mock_bare_repo(tmp_path: Path) -> Path:
    """Fixture that initializes a bare Git repository."""
    repo_dir = tmp_path / "bare_repo.git"
    repo_dir.mkdir()
    subprocess.run(["git", "init", "--bare"], cwd=repo_dir, check=True, capture_output=True)
    return repo_dir


def test_detects_repo_root(mock_trusted_repo: Path) -> None:
    # Check from a nested directory inside the repo
    nested = mock_trusted_repo / "src" / "deep"
    nested.mkdir(parents=True)

    root = detect_trusted_repo_root(nested)
    assert root == mock_trusted_repo.resolve()


def test_fails_on_bare_repo(mock_bare_repo: Path, tmp_path: Path) -> None:
    config = GuardedWorktreeConfig(
        trusted_repo_path=mock_bare_repo,
        rygnal_run_root=tmp_path / "runs",
    )
    with pytest.raises(GuardedWorktreeError, match="Bare repositories are not supported"):
        create_guarded_worktree(config)


def test_creates_worktree_with_strict_permissions(mock_trusted_repo: Path, tmp_path: Path) -> None:
    run_root = tmp_path / "runs"
    config = GuardedWorktreeConfig(
        trusted_repo_path=mock_trusted_repo,
        rygnal_run_root=run_root,
    )

    worktree = create_guarded_worktree(config)

    # 1. UUID exists and dir is created
    assert worktree.run_id
    run_dir = run_root / worktree.run_id
    assert run_dir.exists()

    # 2. Permissions are strict (0o700)
    # Mask out the upper bits (file type) to check only permissions
    assert (run_dir.stat().st_mode & 0o777) == 0o700

    # 3. Worktree was actually created physically
    assert worktree.workspace_path.exists()
    assert (worktree.workspace_path / ".git").exists()
    assert (worktree.workspace_path / "base.txt").exists()


def test_captures_baseline_commit_sha(mock_trusted_repo: Path, tmp_path: Path) -> None:
    config = GuardedWorktreeConfig(
        trusted_repo_path=mock_trusted_repo,
        rygnal_run_root=tmp_path / "runs",
    )
    worktree = create_guarded_worktree(config)

    assert len(worktree.baseline_commit_sha) == 40
    # Verify the worktree points to the exact same commit
    wt_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=worktree.workspace_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert worktree.baseline_commit_sha == wt_sha


def test_workspace_must_be_outside_trusted_repo(mock_trusted_repo: Path) -> None:
    # Attempt to place the run root INSIDE the trusted repo (severe vulnerability)
    nested_run_root = mock_trusted_repo / "rygnal_runs"

    config = GuardedWorktreeConfig(
        trusted_repo_path=mock_trusted_repo,
        rygnal_run_root=nested_run_root,
    )

    with pytest.raises(GuardedWorktreeError, match="must not be inside trusted repo"):
        create_guarded_worktree(config)


def test_unsafe_local_runner_executes_in_workspace(mock_trusted_repo: Path, tmp_path: Path) -> None:
    config = GuardedWorktreeConfig(
        trusted_repo_path=mock_trusted_repo,
        rygnal_run_root=tmp_path / "runs",
    )
    worktree = create_guarded_worktree(config)

    # pwd proves execution isolation
    result = run_unsafe_local_for_testing(worktree, ["pwd"])
    output_path = Path(result.stdout.strip()).resolve()

    assert output_path == worktree.workspace_path.resolve()
    assert output_path != mock_trusted_repo.resolve()
