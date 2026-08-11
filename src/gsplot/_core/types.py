"""Small immutable value types shared by the canonical API."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, Mapping, Protocol, Sequence, TypeAlias, cast

from matplotlib.colors import is_color_like

from .errors import LayoutError, MetadataError, PlotError

RGBColor: TypeAlias = tuple[float, float, float] | tuple[float, float, float, float]
ColorSpec: TypeAlias = str | RGBColor
MosaicSpec: TypeAlias = str | Sequence[Sequence[str | None]]


class NormalizeSpec(Protocol):
    """Protocol for a Matplotlib-compatible color normalizer."""

    def __call__(self, value: Any, clip: bool | None = None) -> Any:
        """Normalize one or more scalar values."""


_SCALES = {"linear", "log", "symlog", "logit"}
_LOCATIONS = {
    "upper right",
    "upper left",
    "lower left",
    "lower right",
    "right",
    "center left",
    "center right",
    "lower center",
    "upper center",
    "center",
}
_PERCENTAGE = re.compile(r"^(?:0|[1-9]\d*)(?:\.\d+)?%$")


def _finite(value: Any, name: str, error: type[Exception]) -> float:
    """Return a finite real scalar for an immutable value constructor."""

    if isinstance(value, bool):
        raise error(f"{name} must be finite")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise error(f"{name} must be finite") from exc
    if not math.isfinite(result):
        raise error(f"{name} must be finite")
    return result


def _text(value: Any, name: str, error: type[Exception]) -> str:
    """Return a non-empty string."""

    if not isinstance(value, str) or not value.strip():
        raise error(f"{name} must be a non-empty string")
    return value


def _optional_text(value: Any, name: str, error: type[Exception]) -> str | None:
    """Validate an optional text field."""

    return None if value is None else _text(value, name, error)


def _color(value: Any, name: str) -> ColorSpec:
    """Validate and normalize a named or RGB/RGBA color value."""

    if isinstance(value, str):
        if not value.strip() or not is_color_like(value):
            raise PlotError(f"{name} must be a valid Matplotlib color")
        return value
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise PlotError(f"{name} must be a color name or RGB/RGBA sequence")
    if len(value) not in (3, 4):
        raise PlotError(f"{name} must contain three or four channels")
    channels = tuple(
        _finite(channel, f"{name}[{index}]", PlotError)
        for index, channel in enumerate(value)
    )
    if any(channel < 0 or channel > 1 for channel in channels):
        raise PlotError(f"{name} channels must be between 0 and 1")
    if len(channels) == 3:
        return cast(tuple[float, float, float], channels)
    return cast(tuple[float, float, float, float], channels)


def _limits(value: Any, name: str) -> tuple[float, float] | None:
    """Validate finite, non-equal limits while preserving their order."""

    if value is None:
        return None
    if isinstance(value, (str, bytes)):
        raise LayoutError(f"{name} must contain exactly two finite values")
    try:
        values = tuple(value)
    except TypeError as exc:
        raise LayoutError(f"{name} must contain exactly two finite values") from exc
    if len(values) != 2:
        raise LayoutError(f"{name} must contain exactly two finite values")
    result = (
        _finite(values[0], f"{name}[0]", LayoutError),
        _finite(values[1], f"{name}[1]", LayoutError),
    )
    if result[0] == result[1]:
        raise LayoutError(f"{name} values must not be equal")
    return result


def _ticks(value: Any, name: str) -> tuple[float, ...] | None:
    """Validate and normalize optional finite tick locations."""

    if value is None:
        return None
    if isinstance(value, (str, bytes)):
        raise LayoutError(f"{name} must be a sequence of finite values")
    try:
        values = tuple(value)
    except TypeError as exc:
        raise LayoutError(f"{name} must be a sequence of finite values") from exc
    return tuple(
        _finite(item, f"{name}[{index}]", LayoutError)
        for index, item in enumerate(values)
    )


def _optional_finite(value: Any, name: str) -> float | None:
    """Validate an optional finite numeric value."""

    return None if value is None else _finite(value, name, LayoutError)


@dataclass(frozen=True, slots=True)
class AxisSpec:
    """Immutable Cartesian labels, limits, scales, ticks, and padding."""

    xlabel: str | None = None
    ylabel: str | None = None
    xlim: tuple[float, float] | None = None
    ylim: tuple[float, float] | None = None
    xscale: Literal["linear", "log", "symlog", "logit"] = "linear"
    yscale: Literal["linear", "log", "symlog", "logit"] = "linear"
    xticks: tuple[float, ...] | None = None
    yticks: tuple[float, ...] | None = None
    xminor: bool | None = None
    yminor: bool | None = None
    xlabelpad: float | None = None
    ylabelpad: float | None = None

    def __post_init__(self) -> None:
        """Validate every field and normalize sequence-like inputs."""

        object.__setattr__(
            self, "xlabel", _optional_text(self.xlabel, "xlabel", LayoutError)
        )
        object.__setattr__(
            self, "ylabel", _optional_text(self.ylabel, "ylabel", LayoutError)
        )
        object.__setattr__(self, "xlim", _limits(self.xlim, "xlim"))
        object.__setattr__(self, "ylim", _limits(self.ylim, "ylim"))
        if self.xscale not in _SCALES:
            raise LayoutError(f"xscale must be one of: {', '.join(sorted(_SCALES))}")
        if self.yscale not in _SCALES:
            raise LayoutError(f"yscale must be one of: {', '.join(sorted(_SCALES))}")
        object.__setattr__(self, "xticks", _ticks(self.xticks, "xticks"))
        object.__setattr__(self, "yticks", _ticks(self.yticks, "yticks"))
        if self.xminor is not None and not isinstance(self.xminor, bool):
            raise LayoutError("xminor must be a boolean or None")
        if self.yminor is not None and not isinstance(self.yminor, bool):
            raise LayoutError("yminor must be a boolean or None")
        object.__setattr__(
            self, "xlabelpad", _optional_finite(self.xlabelpad, "xlabelpad")
        )
        object.__setattr__(
            self, "ylabelpad", _optional_finite(self.ylabelpad, "ylabelpad")
        )


@dataclass(frozen=True, slots=True)
class InsetSpec:
    """Immutable placement specification for an explicit parent Axes."""

    bounds: tuple[float, float, float, float] | None = None
    width: float | str | None = None
    height: float | str | None = None
    loc: str | int = "upper right"
    bbox_to_anchor: tuple[float, ...] | None = None
    borderpad: float = 0.5

    def __post_init__(self) -> None:
        """Validate one complete, finite placement mode."""

        has_bounds = self.bounds is not None
        has_size = self.width is not None or self.height is not None
        if has_bounds and has_size:
            raise LayoutError("InsetSpec cannot combine bounds with width or height")
        if not has_bounds and not (self.width is not None and self.height is not None):
            raise LayoutError("InsetSpec requires bounds or both width and height")
        if has_bounds:
            bounds = self.bounds
            if bounds is None or isinstance(bounds, (str, bytes)):
                raise LayoutError("bounds must contain four finite values")
            try:
                values = tuple(bounds)
            except TypeError as exc:
                raise LayoutError("bounds must contain four finite values") from exc
            if len(values) != 4:
                raise LayoutError("bounds must contain four finite values")
            normalized = tuple(
                _finite(item, f"bounds[{index}]", LayoutError)
                for index, item in enumerate(values)
            )
            if normalized[2] <= 0 or normalized[3] <= 0:
                raise LayoutError("bounds width and height must be positive")
            object.__setattr__(
                self, "bounds", cast(tuple[float, float, float, float], normalized)
            )
        else:
            object.__setattr__(self, "width", _size(self.width, "width"))
            object.__setattr__(self, "height", _size(self.height, "height"))
        if not (
            (isinstance(self.loc, str) and self.loc in _LOCATIONS)
            or (
                isinstance(self.loc, int)
                and not isinstance(self.loc, bool)
                and 1 <= self.loc <= 10
            )
        ):
            raise LayoutError(
                "loc must be a Matplotlib location name or an integer from 1 through 10"
            )
        if self.bbox_to_anchor is not None:
            if isinstance(self.bbox_to_anchor, (str, bytes)):
                raise LayoutError(
                    "bbox_to_anchor must contain two or four finite values"
                )
            values = tuple(self.bbox_to_anchor)
            if len(values) not in (2, 4):
                raise LayoutError(
                    "bbox_to_anchor must contain two or four finite values"
                )
            object.__setattr__(
                self,
                "bbox_to_anchor",
                tuple(
                    _finite(item, f"bbox_to_anchor[{index}]", LayoutError)
                    for index, item in enumerate(values)
                ),
            )
        object.__setattr__(
            self, "borderpad", _finite(self.borderpad, "borderpad", LayoutError)
        )
        if self.borderpad < 0:
            raise LayoutError("borderpad must be non-negative")


def _size(value: float | str | None, name: str) -> float | str:
    """Validate a numeric size or Matplotlib percentage string."""

    if isinstance(value, str):
        if (
            not _PERCENTAGE.fullmatch(value)
            or float(value[:-1]) <= 0
            or float(value[:-1]) > 100
        ):
            raise LayoutError(
                f"{name} must be positive or a percentage between 0% and 100%"
            )
        return value
    if value is None:
        raise LayoutError(f"{name} must be positive")
    result = _finite(value, name, LayoutError)
    if result <= 0:
        raise LayoutError(f"{name} must be positive")
    return result


@dataclass(frozen=True, slots=True)
class Theme:
    """Immutable explicit Figure/Axes appearance values."""

    figure_facecolor: ColorSpec | None = None
    axes_facecolor: ColorSpec | None = None
    text_color: ColorSpec | None = None
    spine_color: ColorSpec | None = None
    tick_color: ColorSpec | None = None
    grid: bool | None = None
    grid_color: ColorSpec | None = None
    grid_alpha: float | None = None

    def __post_init__(self) -> None:
        """Validate colors and the optional grid alpha."""

        for field_name in (
            "figure_facecolor",
            "axes_facecolor",
            "text_color",
            "spine_color",
            "tick_color",
            "grid_color",
        ):
            object.__setattr__(
                self,
                field_name,
                (
                    _color(getattr(self, field_name), field_name)
                    if getattr(self, field_name) is not None
                    else None
                ),
            )
        if self.grid is not None and not isinstance(self.grid, bool):
            raise PlotError("grid must be a boolean or None")
        alpha = (
            None
            if self.grid_alpha is None
            else _finite(self.grid_alpha, "grid_alpha", PlotError)
        )
        if alpha is not None and not 0 <= alpha <= 1:
            raise PlotError("grid_alpha must be between 0 and 1")
        object.__setattr__(self, "grid_alpha", alpha)

    @classmethod
    def default(cls) -> "Theme":
        """Return the no-op theme."""

        return cls()

    @classmethod
    def white(cls) -> "Theme":
        """Return the explicit white-text theme from the reform contract."""

        return cls(
            axes_facecolor=(1.0, 1.0, 1.0, 0.0),
            text_color="white",
            spine_color="white",
            tick_color="white",
        )

    @classmethod
    def transparent(cls) -> "Theme":
        """Return the explicit transparent Figure/Axes theme."""

        return cls(
            figure_facecolor=(0.0, 0.0, 0.0, 0.0),
            axes_facecolor=(0.0, 0.0, 0.0, 0.0),
        )


def _bounded_identifier(value: Any, name: str) -> str:
    """Validate a bounded metadata identifier."""

    result = _text(value, name, MetadataError)
    if len(result) > 128:
        raise MetadataError(f"{name} must be at most 128 characters")
    return result


def _readonly_labels(value: Mapping[str, str] | None) -> Mapping[str, str]:
    """Validate and recursively isolate public metadata labels."""

    if value is None:
        return MappingProxyType({})
    if len(value) > 64:
        raise MetadataError("labels must contain at most 64 entries")
    labels: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise MetadataError("labels keys and values must be strings")
        if len(key.encode("utf-8")) > 256 or len(item.encode("utf-8")) > 256:
            raise MetadataError(
                "labels keys and values must be at most 256 UTF-8 bytes"
            )
        labels[key] = item
    return MappingProxyType(labels)


@dataclass(frozen=True, slots=True)
class MetadataSnapshot:
    """Immutable, privacy-bounded metadata for one explicit output."""

    package_version: str
    schema_version: Literal[1] = 1
    commit: str | None = None
    config_digest: str | None = None
    labels: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate identifiers and freeze caller-owned metadata."""

        object.__setattr__(
            self,
            "package_version",
            _bounded_identifier(self.package_version, "package_version"),
        )
        if self.schema_version != 1 or isinstance(self.schema_version, bool):
            raise MetadataError("schema_version must be the integer 1")
        if self.commit is not None:
            object.__setattr__(
                self, "commit", _bounded_identifier(self.commit, "commit")
            )
        if self.config_digest is not None:
            object.__setattr__(
                self,
                "config_digest",
                _bounded_identifier(self.config_digest, "config_digest"),
            )
        object.__setattr__(self, "labels", _readonly_labels(self.labels))


@dataclass(frozen=True, slots=True)
class BuildInfo:
    """Immutable distribution metadata returned by :func:`build_info`."""

    version: str
    commit: str | None = None

    def __post_init__(self) -> None:
        """Validate the public metadata fields."""

        object.__setattr__(
            self, "version", _bounded_identifier(self.version, "version")
        )
        if self.commit is not None:
            object.__setattr__(
                self, "commit", _bounded_identifier(self.commit, "commit")
            )


@dataclass(frozen=True, slots=True)
class LegendEntries:
    """Immutable handles, labels, and local legend handler mappings."""

    handles: tuple[Any, ...]
    labels: tuple[str, ...]
    handler_map: Mapping[Any, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Normalize sequences and validate the entry relationship."""

        handles = tuple(self.handles)
        labels = tuple(self.labels)
        if len(handles) != len(labels):
            raise PlotError("handles and labels must have the same length")
        if any(not isinstance(label, str) for label in labels):
            raise PlotError("legend labels must be strings")
        object.__setattr__(self, "handles", handles)
        object.__setattr__(self, "labels", labels)
        object.__setattr__(
            self, "handler_map", MappingProxyType(dict(self.handler_map))
        )


__all__ = [
    "RGBColor",
    "ColorSpec",
    "MosaicSpec",
    "NormalizeSpec",
    "AxisSpec",
    "InsetSpec",
    "Theme",
    "MetadataSnapshot",
    "BuildInfo",
    "LegendEntries",
]
