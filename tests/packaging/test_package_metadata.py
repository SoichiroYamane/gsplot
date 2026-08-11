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
