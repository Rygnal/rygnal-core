import tomllib
from pathlib import Path


def test_pyproject_declares_build_system():
    data = tomllib.loads(Path("pyproject.toml").read_text())

    assert data["build-system"]["build-backend"] == "setuptools.build_meta"
    assert "setuptools>=68" in data["build-system"]["requires"]
    assert "wheel" in data["build-system"]["requires"]


def test_pyproject_uses_src_package_discovery():
    data = tomllib.loads(Path("pyproject.toml").read_text())

    assert data["tool"]["setuptools"]["packages"]["find"]["where"] == ["src"]


def test_pyproject_declares_rygnal_cli_script():
    data = tomllib.loads(Path("pyproject.toml").read_text())

    assert data["project"]["scripts"]["rygnal"] == "rygnal.cli:main"


def test_readme_documents_install_flow():
    content = Path("README.md").read_text()

    assert "python -m venv .venv" in content
    assert "pip install -e ." in content
    assert "rygnal --help" in content
    assert "rygnal demo run" in content
