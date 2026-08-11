"""Typed exceptions raised by canonical gsplot operations."""

from __future__ import annotations


class GsplotError(Exception):
    """Base class for errors that are part of the canonical API contract."""


class ConfigError(GsplotError):
    """Raised when configuration cannot be parsed or validated."""


class DataError(GsplotError):
    """Raised when plotting or numerical input violates the data contract."""


class LayoutError(ConfigError):
    """Raised when a figure or axes layout is invalid.

    Layout failures are configuration failures as well, so callers may catch
    either the specific layout type or the broader :class:`ConfigError`.
    """


class PlotError(GsplotError):
    """Raised when a plotting operation cannot be completed safely."""


class OutputError(GsplotError):
    """Raised when figure output or display cannot be completed."""


class MetadataError(GsplotError):
    """Raised when reproducibility metadata is invalid or cannot be written."""


__all__ = [
    "GsplotError",
    "ConfigError",
    "DataError",
    "LayoutError",
    "PlotError",
    "OutputError",
    "MetadataError",
]
