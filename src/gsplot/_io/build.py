"""Explicit installed-distribution metadata access."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .._core.types import BuildInfo


def build_info() -> BuildInfo:
    """Return only the installed gsplot version and a null commit value.

    Returns
    -------
    BuildInfo
        Immutable distribution metadata.  The commit is ``None`` unless a
        future public build contract explicitly supplies one.

    Examples
    --------
    >>> import gsplot as gs
    >>> info = gs.build_info()
    >>> isinstance(info.version, str)
    True
    """

    try:
        package_version = version("gsplot")
    except PackageNotFoundError:
        package_version = "0+unknown"
    return BuildInfo(package_version, commit=None)


__all__ = ["build_info"]
