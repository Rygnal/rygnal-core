"""Dependency tree governance model for guarded workspace changes.

This module does not install or resolve dependencies. It identifies dependency
governance targets by workspace directory, ecosystem, and toolchain so later M1
code can perform semantic dependency delta analysis, manifest-lock sync checks,
vulnerability scanning, approval, and audit in an isolated resolver environment.

SECURITY WARNING: Path normalization here operates purely on strings. It does
NOT resolve symlinks. Downstream M1/M3 execution backends MUST resolve symlinks
using `realpath` or `O_NOFOLLOW` before mounting or reading these files inside
the guarded workspace sandbox.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from functools import cached_property
from pathlib import PurePosixPath


class DependencyGovernanceError(ValueError):
    """Raised when dependency governance receives an invalid repo path."""


class DependencyFileKind(StrEnum):
    MANIFEST = "manifest"
    LOCKFILE = "lockfile"
    PRIVATE_REGISTRY_CONFIG = "private_registry_config"


class EcosystemKind(StrEnum):
    PYTHON = "python"
    NODE = "node"


class ToolchainKind(StrEnum):
    PYTHON_PYPROJECT = "python_pyproject"
    PYTHON_REQUIREMENTS = "python_requirements"
    PYTHON_PIPENV = "python_pipenv"
    NODE_NPM = "node_npm"
    NODE_YARN = "node_yarn"
    NODE_PNPM = "node_pnpm"


@dataclass(frozen=True)
class DependencyFileChange:
    path: str
    directory: str
    ecosystem: EcosystemKind
    toolchain: ToolchainKind
    kind: DependencyFileKind


@dataclass(frozen=True)
class WorkspaceDependencyTarget:
    directory: str
    ecosystem: EcosystemKind
    toolchain: ToolchainKind
    manifests: tuple[str, ...] = ()
    lockfiles: tuple[str, ...] = ()
    private_registry_configs: tuple[str, ...] = ()

    @cached_property
    def requires_tree_delta_analysis(self) -> bool:
        """Flags if downstream code must parse the AST/Tree for transitive changes."""
        return bool(self.manifests or self.lockfiles)

    @cached_property
    def requires_manifest_lock_sync_check(self) -> bool:
        """Flags if the sandbox must physically verify manifest and lockfile sync."""
        return bool(self.manifests or self.lockfiles)

    @cached_property
    def has_possible_manifest_lock_desync(self) -> bool:
        """Assumes a possible desync if ANY dependency file is touched."""
        return bool(self.manifests or self.lockfiles)

    @cached_property
    def requires_private_registry_approval(self) -> bool:
        """Manifests can embed registry URLs. They must trigger approval checks."""
        return bool(self.private_registry_configs or self.manifests)


@dataclass(frozen=True)
class DependencyGovernancePlan:
    workspaces: tuple[WorkspaceDependencyTarget, ...]

    @cached_property
    def dependency_changes_detected(self) -> bool:
        return bool(self.workspaces)

    @cached_property
    def resolver_environment_required(self) -> bool:
        return any(ws.requires_tree_delta_analysis for ws in self.workspaces)

    @cached_property
    def resolver_environment_must_be_separate_from_host(self) -> bool:
        return self.dependency_changes_detected

    @cached_property
    def resolver_environment_must_be_separate_from_runtime_workspace(self) -> bool:
        return self.dependency_changes_detected

    @property
    def shared_writable_cache_allowed(self) -> bool:
        return False

    @cached_property
    def per_run_writable_cache_allowed(self) -> bool:
        return self.dependency_changes_detected

    @cached_property
    def shared_readonly_cache_requires_hash_verification(self) -> bool:
        return self.dependency_changes_detected

    @cached_property
    def transitive_dependency_delta_required(self) -> bool:
        return self.resolver_environment_required

    @cached_property
    def vulnerability_scan_required(self) -> bool:
        return self.resolver_environment_required

    @cached_property
    def network_resolution_requires_approval(self) -> bool:
        return self.resolver_environment_required

    @cached_property
    def private_registry_access_requires_approval(self) -> bool:
        return any(ws.requires_private_registry_approval for ws in self.workspaces)

    @cached_property
    def new_dependency_tree_requires_approval(self) -> bool:
        return self.resolver_environment_required

    @cached_property
    def audit_secret_redaction_required(self) -> bool:
        return self.dependency_changes_detected

    @cached_property
    def has_possible_manifest_lock_desync(self) -> bool:
        return any(ws.has_possible_manifest_lock_desync for ws in self.workspaces)


def build_dependency_governance_plan(
    changed_paths: Iterable[str],
) -> DependencyGovernancePlan:
    """Build an ecosystem-aware governance plan from changed repo-relative paths."""

    grouped: dict[tuple[str, EcosystemKind, ToolchainKind], list[DependencyFileChange]] = (
        defaultdict(list)
    )

    for path in sorted(set(changed_paths)):
        change = classify_dependency_file_change(path)
        if change is not None:
            grouped[(change.directory, change.ecosystem, change.toolchain)].append(change)

    workspaces = []
    for (directory, ecosystem, toolchain), changes in sorted(grouped.items()):
        manifests = tuple(c.path for c in changes if c.kind == DependencyFileKind.MANIFEST)
        lockfiles = tuple(c.path for c in changes if c.kind == DependencyFileKind.LOCKFILE)
        configs = tuple(
            c.path for c in changes if c.kind == DependencyFileKind.PRIVATE_REGISTRY_CONFIG
        )

        workspaces.append(
            WorkspaceDependencyTarget(
                directory=directory,
                ecosystem=ecosystem,
                toolchain=toolchain,
                manifests=manifests,
                lockfiles=lockfiles,
                private_registry_configs=configs,
            )
        )

    return DependencyGovernancePlan(workspaces=tuple(workspaces))


_REQUIREMENTS_EXACT = {
    "requirements.txt",
    "requirements-dev.txt",
    "requirements.prod.txt",
    "requirements.in",
    "reqs.txt",
}


def _is_python_requirements_file(path_obj: PurePosixPath) -> bool:
    if path_obj.name in _REQUIREMENTS_EXACT:
        return True

    parent_name = path_obj.parent.name
    if parent_name in {"requirements", "reqs"} and path_obj.suffix in {".txt", ".in"}:
        return True

    return False


def classify_dependency_file_change(path: str) -> DependencyFileChange | None:
    """Classify a file into an ecosystem and toolchain."""

    try:
        normalized_path = normalize_repo_relative_path(path)
    except DependencyGovernanceError:
        return None

    path_obj = PurePosixPath(normalized_path)
    filename = path_obj.name
    directory = path_obj.parent.as_posix()

    # Node Ecosystem
    if filename == "package.json":
        return DependencyFileChange(
            normalized_path,
            directory,
            EcosystemKind.NODE,
            ToolchainKind.NODE_NPM,
            DependencyFileKind.MANIFEST,
        )
    if filename in {"package-lock.json", "npm-shrinkwrap.json"}:
        return DependencyFileChange(
            normalized_path,
            directory,
            EcosystemKind.NODE,
            ToolchainKind.NODE_NPM,
            DependencyFileKind.LOCKFILE,
        )
    if filename == "yarn.lock":
        return DependencyFileChange(
            normalized_path,
            directory,
            EcosystemKind.NODE,
            ToolchainKind.NODE_YARN,
            DependencyFileKind.LOCKFILE,
        )
    if filename == "pnpm-lock.yaml":
        return DependencyFileChange(
            normalized_path,
            directory,
            EcosystemKind.NODE,
            ToolchainKind.NODE_PNPM,
            DependencyFileKind.LOCKFILE,
        )
    if filename == ".npmrc":
        return DependencyFileChange(
            normalized_path,
            directory,
            EcosystemKind.NODE,
            ToolchainKind.NODE_NPM,
            DependencyFileKind.PRIVATE_REGISTRY_CONFIG,
        )

    # Python Ecosystem
    if filename in {"pyproject.toml", "setup.py", "setup.cfg"}:
        return DependencyFileChange(
            normalized_path,
            directory,
            EcosystemKind.PYTHON,
            ToolchainKind.PYTHON_PYPROJECT,
            DependencyFileKind.MANIFEST,
        )
    if filename in {"poetry.lock", "uv.lock"}:
        return DependencyFileChange(
            normalized_path,
            directory,
            EcosystemKind.PYTHON,
            ToolchainKind.PYTHON_PYPROJECT,
            DependencyFileKind.LOCKFILE,
        )
    if filename == "Pipfile":
        return DependencyFileChange(
            normalized_path,
            directory,
            EcosystemKind.PYTHON,
            ToolchainKind.PYTHON_PIPENV,
            DependencyFileKind.MANIFEST,
        )
    if filename == "Pipfile.lock":
        return DependencyFileChange(
            normalized_path,
            directory,
            EcosystemKind.PYTHON,
            ToolchainKind.PYTHON_PIPENV,
            DependencyFileKind.LOCKFILE,
        )
    if filename in {"pip.conf", "pip.ini", ".pypirc"}:
        return DependencyFileChange(
            normalized_path,
            directory,
            EcosystemKind.PYTHON,
            ToolchainKind.PYTHON_REQUIREMENTS,
            DependencyFileKind.PRIVATE_REGISTRY_CONFIG,
        )

    if _is_python_requirements_file(path_obj):
        return DependencyFileChange(
            normalized_path,
            directory,
            EcosystemKind.PYTHON,
            ToolchainKind.PYTHON_REQUIREMENTS,
            DependencyFileKind.MANIFEST,
        )

    return None


def normalize_repo_relative_path(path: str) -> str:
    """Normalize and validate a repo-relative path.

    SECURITY WARNING: Path normalization here operates purely on strings. It does NOT
    resolve symlinks. Downstream M1/M3 execution backends MUST resolve symlinks using
    `realpath` or `O_NOFOLLOW` before mounting or reading these files inside the sandbox.
    """

    normalized = path.replace("\\", "/").strip()
    candidate = PurePosixPath(normalized)

    if candidate.is_absolute():
        raise DependencyGovernanceError(
            f"Dependency path must be repo-relative, got absolute: {path}"
        )

    if not candidate.parts:
        raise DependencyGovernanceError("Dependency path must not be empty.")

    if any(part == ".." for part in candidate.parts):
        raise DependencyGovernanceError(
            f"Dependency path must not traverse outside repository: {path}"
        )

    clean_parts = tuple(part for part in candidate.parts if part not in {"", "."})
    if not clean_parts:
        raise DependencyGovernanceError("Dependency path must not be empty.")

    return PurePosixPath(*clean_parts).as_posix()
