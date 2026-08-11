"""Explicit configuration discovery and precedence helpers."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal, TypeVar

from .._core.errors import ConfigError
from .._core.validation import MISSING, resolve_option
from .model import Config
from .schema import DEFAULT_CONFIG_NAME

T = TypeVar("T")


def discover_config_path(
    *,
    cwd: str | Path | None = None,
    home: str | Path | None = None,
) -> Path | None:
    """Find ``gsplot.json`` in cwd, user config, then home order."""

    current = Path.cwd() if cwd is None else Path(cwd).expanduser()
    home_path = Path.home() if home is None else Path(home).expanduser()
    candidates = (
        current / DEFAULT_CONFIG_NAME,
        home_path / ".config" / "gsplot" / DEFAULT_CONFIG_NAME,
        home_path / DEFAULT_CONFIG_NAME,
    )
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def load_config(
    path: str | Path | None = None,
    *,
    cwd: str | Path | None = None,
    home: str | Path | None = None,
) -> Config:
    """Explicitly load one file or discover a JSON file without import effects."""

    if path is not None:
        return Config.from_file(str(path))
    discovered = discover_config_path(cwd=cwd, home=home)
    return Config() if discovered is None else Config.from_file(str(discovered))


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
    "discover_config_path",
    "load_config",
    "resolve_config_value",
]
