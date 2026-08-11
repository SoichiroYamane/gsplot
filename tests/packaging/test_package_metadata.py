"""Tests for the package layout and distribution metadata boundary."""

from importlib import metadata, resources

import gsplot


def test_package_version_comes_from_distribution_metadata() -> None:
    """The compatibility value matches the installed distribution."""

    assert gsplot.__version__ == metadata.version("gsplot")
    assert gsplot.__commit__ is None


def test_package_ships_pep561_marker() -> None:
    """The wheel exposes the marker required by typed consumers."""

    assert resources.files("gsplot").joinpath("py.typed").is_file()


def test_runtime_metadata_contains_only_canonical_dependencies() -> None:
    """Rich and YAML remain out of the installed runtime requirement set."""

    requirements = metadata.requires("gsplot") or ()
    names = {requirement.split(" ", 1)[0].lower() for requirement in requirements}
    assert names.isdisjoint({"rich", "pyyaml", "types-pyyaml"})
