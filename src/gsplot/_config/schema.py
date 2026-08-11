"""Strict JSON parsing and scalar validation for schema version 1."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from os import PathLike
from pathlib import Path
from typing import Any, Literal, cast

from .._core.errors import ConfigError
from .._core.types import ColorSpec
from .._core.validation import (
    ensure_bool,
    ensure_finite_real,
    ensure_mapping,
    ensure_nonempty_text,
    ensure_positive,
    reject_unknown_keys,
)

SCHEMA_VERSION: Literal[1] = 1
MAX_CONFIG_BYTES = 1_048_576
DEFAULT_CONFIG_NAME = "gsplot.json"
FIGURE_KEYS = {"figsize", "unit", "squeeze", "tight_layout", "constrained_layout"}
PLOTTING_KEYS = {"default_color", "default_cmap", "nonfinite"}
ROOT_KEYS = {"schema_version", "figure", "plotting"}
UNITS = {"mm", "cm", "in", "pt"}


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build an object while rejecting duplicate JSON keys."""

    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ConfigError(f"duplicate configuration key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    """Reject JSON NaN and infinity spellings."""

    raise ConfigError(f"non-finite JSON constant is not allowed: {value}")


def _reject_nonfinite(value: Any, path: str = "configuration") -> None:
    """Reject non-finite numeric values, including overflowed exponents."""

    if isinstance(value, float) and not math.isfinite(value):
        raise ConfigError(f"{path} contains a non-finite number")
    if isinstance(value, Mapping):
        for key, nested in value.items():
            _reject_nonfinite(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_nonfinite(nested, f"{path}[{index}]")


def parse_json_text(text: str) -> dict[str, Any]:
    """Parse strict JSON text into a new mapping."""

    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_constant,
        )
    except ConfigError:
        raise
    except (TypeError, json.JSONDecodeError) as exc:
        raise ConfigError(f"invalid JSON configuration: {exc}") from exc

    mapping = ensure_mapping(value, "configuration")
    _reject_nonfinite(mapping)
    return dict(mapping)


def read_json_file(path: str | PathLike[str]) -> dict[str, Any]:
    """Read a bounded UTF-8 JSON configuration file."""

    config_path = Path(path).expanduser()
    try:
        size = config_path.stat().st_size
    except OSError as exc:
        raise ConfigError(f"cannot stat configuration file: {config_path}") from exc
    if size > MAX_CONFIG_BYTES:
        raise ConfigError(
            f"configuration file exceeds the {MAX_CONFIG_BYTES}-byte limit"
        )
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read configuration file: {config_path}") from exc
    return parse_json_text(text)


def parse_schema_version(value: Any) -> Literal[1]:
    """Validate the supported schema version."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError("schema_version must be the integer 1")
    if value != SCHEMA_VERSION:
        raise ConfigError(f"unsupported schema_version: {value}")
    return cast(Literal[1], value)


def parse_unit(value: Any) -> Literal["mm", "cm", "in", "pt"]:
    """Validate a figure size unit."""

    if not isinstance(value, str) or value not in UNITS:
        allowed = ", ".join(sorted(UNITS))
        raise ConfigError(f"figure.unit must be one of: {allowed}")
    return cast(Literal["mm", "cm", "in", "pt"], value)


def parse_figsize(value: Any) -> tuple[float, float] | None:
    """Validate a positive two-dimensional figure size."""

    if value is None:
        return None
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ConfigError("figure.figsize must be null or a two-item array")
    if len(value) != 2:
        raise ConfigError("figure.figsize must contain exactly two values")
    return (
        ensure_positive(value[0], "figure.figsize[0]", error=ConfigError),
        ensure_positive(value[1], "figure.figsize[1]", error=ConfigError),
    )


def parse_color(value: Any, name: str) -> ColorSpec:
    """Validate a named color or an RGB/RGBA sequence in the unit interval."""

    if isinstance(value, str):
        return ensure_nonempty_text(value, name, error=ConfigError)
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ConfigError(f"{name} must be a color name or RGB/RGBA array")
    if len(value) not in (3, 4):
        raise ConfigError(f"{name} must contain three or four channels")
    channels = tuple(
        ensure_finite_real(channel, f"{name}[{index}]", error=ConfigError)
        for index, channel in enumerate(value)
    )
    if any(channel < 0 or channel > 1 for channel in channels):
        raise ConfigError(f"{name} channels must be between 0 and 1")
    if len(channels) == 3:
        return channels  # type: ignore[return-value]
    return channels  # type: ignore[return-value]


def parse_default_color(
    value: Any,
) -> str | tuple[float, float, float] | tuple[float, float, float, float]:
    """Validate the plotting default color, including the ``axes`` sentinel."""

    if isinstance(value, str) and value == "axes":
        return "axes"
    return parse_color(value, "plotting.default_color")


def validate_section(mapping: Any, name: str, allowed: set[str]) -> Mapping[str, Any]:
    """Validate a named closed configuration section."""

    section = ensure_mapping(mapping, name)
    reject_unknown_keys(section, allowed, name)
    return section


__all__ = [
    "SCHEMA_VERSION",
    "MAX_CONFIG_BYTES",
    "DEFAULT_CONFIG_NAME",
    "FIGURE_KEYS",
    "PLOTTING_KEYS",
    "ROOT_KEYS",
    "read_json_file",
    "parse_json_text",
    "parse_schema_version",
    "parse_unit",
    "parse_figsize",
    "parse_color",
    "parse_default_color",
    "validate_section",
]
