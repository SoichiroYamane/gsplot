"""Explicit canonical configuration loading and precedence helpers."""

from __future__ import annotations

from collections.abc import Mapping
from os import PathLike
from typing import Any, Literal, TypeVar

from .._core.errors import ConfigError
from .._core.validation import MISSING, resolve_option
from .model import Config
from .schema import DEFAULT_CONFIG_NAME

T = TypeVar("T")


def load_config(
    path: str | PathLike[str],
) -> Config:
    """Explicitly load one canonical JSON file without discovery.

    Parameters
    ----------
    path
        Explicit JSON configuration file.

    Returns
    -------
    Config
        A fresh immutable configuration value.

    Raises
    ------
    ConfigError
        If the selected file is missing, malformed, too large, or violates
        the versioned schema.

    Examples
    --------
    >>> import gsplot as gs
    >>> config = gs.load_config("gsplot.json")  # doctest: +SKIP
    >>> config.schema_version
    2  # doctest: +SKIP
    """

    return Config.from_file(str(path))


def resolve_config_value(
    config: Config,
    section: Literal["figure", "plotting"],
    key: str,
    *,
    explicit: T | object = MISSING,
    default: T,
) -> T:
    """Resolve explicit input, then config, then a supplied default."""

    configured: Any = MISSING
    values: Mapping[str, Any] = config.section(section)
    if key in values:
        configured = values[key]
    return resolve_option(explicit, configured, default)


__all__ = [
    "DEFAULT_CONFIG_NAME",
    "load_config",
    "resolve_config_value",
]
