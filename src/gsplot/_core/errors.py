"""Typed exceptions raised by canonical gsplot operations."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


class GsplotError(Exception):
    """Base class for errors that are part of the canonical API contract.

    Examples
    --------
    >>> import gsplot as gs
    >>> isinstance(gs.GsplotError("operation failed"), Exception)
    True
    """


class ConfigError(GsplotError):
    """Raised when configuration cannot be parsed or validated.

    Examples
    --------
    >>> import gsplot as gs
    >>> isinstance(gs.ConfigError("invalid configuration"), gs.GsplotError)
    True
    """


class DataError(GsplotError):
    """Raised when plotting or numerical input violates the data contract.

    Examples
    --------
    >>> import gsplot as gs
    >>> isinstance(gs.DataError("non-finite data"), gs.GsplotError)
    True
    """


class LayoutError(ConfigError):
    """Raised when a figure or axes layout is invalid.

    Layout failures are configuration failures as well, so callers may catch
    either the specific layout type or the broader :class:`ConfigError`.

    Examples
    --------
    >>> import gsplot as gs
    >>> isinstance(gs.LayoutError("invalid size"), gs.ConfigError)
    True
    """


class PlotError(GsplotError):
    """Raised when a plotting operation cannot be completed safely.

    Examples
    --------
    >>> import gsplot as gs
    >>> isinstance(gs.PlotError("invalid target"), gs.GsplotError)
    True
    """


class OptionError(PlotError, TypeError):
    """Internal typed error for an unknown or duplicate public option."""


class OutputError(GsplotError):
    """Raised when figure output or display cannot be completed.

    Parameters
    ----------
    message
        Public-safe explanation of the failed output operation.
    committed_paths
        Absolute final paths already replaced before the failure. The value
        defaults to an empty immutable tuple.

    Attributes
    ----------
    committed_paths
        Immutable tuple of final paths already committed by the operation.

    Examples
    --------
    >>> from pathlib import Path
    >>> import gsplot as gs
    >>> error = gs.OutputError("commit failed", committed_paths=(Path("figure.png"),))
    >>> len(error.committed_paths)
    1
    """

    def __init__(
        self,
        message: str,
        *,
        committed_paths: Iterable[Path] = (),
    ) -> None:
        """Initialize one public-safe output failure."""

        super().__init__(message)
        self.committed_paths = tuple(committed_paths)


class MetadataError(GsplotError):
    """Raised when reproducibility metadata is invalid or cannot be written.

    Examples
    --------
    >>> import gsplot as gs
    >>> isinstance(gs.MetadataError("invalid metadata"), gs.GsplotError)
    True
    """


__all__ = [
    "GsplotError",
    "ConfigError",
    "DataError",
    "LayoutError",
    "PlotError",
    "OptionError",
    "OutputError",
    "MetadataError",
]
