import pytest

from rygnal.dependency_governance import (
    DependencyGovernanceError,
    EcosystemKind,
    ToolchainKind,
    build_dependency_governance_plan,
    normalize_repo_relative_path,
)


def test_nested_python_requirements_file_creates_workspace() -> None:
    plan = build_dependency_governance_plan(["backend/requirements/base.txt"])
    assert len(plan.workspaces) == 1
    ws = plan.workspaces[0]
    assert ws.directory == "backend/requirements"
    assert ws.ecosystem == EcosystemKind.PYTHON
    assert ws.toolchain == ToolchainKind.PYTHON_REQUIREMENTS
    assert ws.manifests == ("backend/requirements/base.txt",)


def test_marketing_blog_requirements_ignored() -> None:
    plan = build_dependency_governance_plan(["docs/requirements_for_marketing_blog.txt"])
    assert len(plan.workspaces) == 0


def test_same_directory_creates_multiple_toolchain_targets() -> None:
    plan = build_dependency_governance_plan(["backend/pyproject.toml", "backend/requirements.txt"])
    assert len(plan.workspaces) == 2
    toolchains = {ws.toolchain for ws in plan.workspaces}
    assert ToolchainKind.PYTHON_PYPROJECT in toolchains
    assert ToolchainKind.PYTHON_REQUIREMENTS in toolchains


def test_manifest_changes_require_private_registry_approval() -> None:
    plan = build_dependency_governance_plan(["package.json"])
    assert plan.private_registry_access_requires_approval is True
    ws = plan.workspaces[0]
    assert ws.requires_private_registry_approval is True


def test_registry_config_changes_governed_and_require_audit_redaction() -> None:
    plan = build_dependency_governance_plan([".npmrc"])
    assert plan.audit_secret_redaction_required is True
    assert plan.private_registry_access_requires_approval is True


def test_lockfile_only_change_requires_isolated_resolver() -> None:
    plan = build_dependency_governance_plan(["poetry.lock"])
    assert plan.resolver_environment_required is True
    assert plan.has_possible_manifest_lock_desync is True


def test_absolute_and_traversal_paths_rejected() -> None:
    with pytest.raises(DependencyGovernanceError):
        normalize_repo_relative_path("/etc/passwd")

    with pytest.raises(DependencyGovernanceError):
        normalize_repo_relative_path("../outside/file.txt")


def test_path_normalization_docstring_mentions_symlink_realpath_nofollow() -> None:
    doc = normalize_repo_relative_path.__doc__
    assert doc is not None
    doc_lower = doc.lower()
    assert "symlink" in doc_lower
    assert "realpath" in doc_lower
    assert "no-follow" in doc_lower or "nofollow" in doc_lower


def test_monorepo_python_and_node_changes_create_separate_targets() -> None:
    plan = build_dependency_governance_plan(["api/pyproject.toml", "ui/package.json"])
    assert len(plan.workspaces) == 2
    ecosystems = {ws.ecosystem for ws in plan.workspaces}
    assert EcosystemKind.PYTHON in ecosystems
    assert EcosystemKind.NODE in ecosystems


def test_aggregate_flags_behave_correctly() -> None:
    plan = build_dependency_governance_plan(["package.json"])
    assert plan.dependency_changes_detected is True
    assert plan.resolver_environment_required is True
    assert plan.resolver_environment_must_be_separate_from_host is True
    assert plan.resolver_environment_must_be_separate_from_runtime_workspace is True
    assert plan.shared_writable_cache_allowed is False
    assert plan.per_run_writable_cache_allowed is True
    assert plan.shared_readonly_cache_requires_hash_verification is True
    assert plan.transitive_dependency_delta_required is True
    assert plan.vulnerability_scan_required is True
    assert plan.network_resolution_requires_approval is True
    assert plan.new_dependency_tree_requires_approval is True
