"""Small immutable value types shared by the canonical API."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, Protocol, TypeAlias, cast, overload

from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.axes._base import _AxesBase
from matplotlib.colors import is_color_like
from matplotlib.legend_handler import HandlerBase
from matplotlib.typing import LineStyleType, MarkerType
from numpy.typing import NDArray

from .errors import LayoutError, MetadataError, PlotError

# Public type alias: RGBColor; an RGB or RGBA tuple with channels in [0, 1].
RGBColor: TypeAlias = tuple[float, float, float] | tuple[float, float, float, float]
# Public type alias: ColorSpec; a Matplotlib color name or RGB/RGBA tuple.
ColorSpec: TypeAlias = str | RGBColor
# Public type alias: MosaicSpec; a Matplotlib mosaic string or label rows.
MosaicSpec: TypeAlias = str | Sequence[Sequence[str | None]]
# Public type alias: AxesTarget; one Axes or a deterministic finite collection.
AxesTarget: TypeAlias = (
    Axes
    | _AxesBase
    | Sequence[Axes | _AxesBase]
    | Mapping[Any, Axes | _AxesBase]
    | NDArray[Any]
)
# Public type alias: PerTarget; ordered or exact-key per-target values.
PerTarget: TypeAlias = Sequence[Any] | Mapping[Any, Any]
# Public type alias: LineStyle; a named style or finite dash-tuple form.
LineStyle: TypeAlias = LineStyleType
# Public type alias: Marker; an input accepted by Matplotlib MarkerStyle.
Marker: TypeAlias = MarkerType
# Public type alias: Unit; supported physical figure-size units.
Unit: TypeAlias = Literal["in", "cm", "mm", "pt"]
# Public type alias: SizePreset; automatic publication canvas choices.
SizePreset: TypeAlias = Literal["auto", "single", "double"]
# Public type alias: SizeSpec; a preset, explicit dimensions, or ambient size.
SizeSpec: TypeAlias = SizePreset | tuple[float, float] | None
# Public type alias: LayoutMode; supported Figure layout-engine choices.
LayoutMode: TypeAlias = Literal["auto", "constrained", "tight", "none"]
# Public type alias: StyleMode; concise target-local style choices.
StyleMode: TypeAlias = Literal["auto", "paper"] | None
# Public type alias: ZoomCorners; two explicit parent/inset connector pairs.
ZoomCorners: TypeAlias = tuple[tuple[int, int], tuple[int, int]]
# Public type alias: Limit; finite two-value axis limits after validation.
Limit: TypeAlias = (
    tuple[float | str | None, float | str | None] | Sequence[float | str | None]
)
# Public type alias: Scale; supported Cartesian scale names.
Scale: TypeAlias = Literal["linear", "log", "symlog", "logit"]
# Public type alias: TickSpec; finite numeric tick locations after validation.
TickSpec: TypeAlias = Sequence[float]
# Public type alias: LabelRecord; concise labels with optional axis limits.
LabelRecord: TypeAlias = tuple[str, str] | tuple[str, str, Any, Any] | Sequence[Any]
# Public type alias: LabelRecords; ordered or exact-key per-target label records.
LabelRecords: TypeAlias = Sequence[LabelRecord] | Mapping[Any, LabelRecord]

_PUBLIC_TYPE_ALIAS_DOCS = MappingProxyType(
    {
        "MosaicSpec": """A subplot-mosaic string or rectangular sequence of label rows.

Examples
--------
>>> import gsplot as gs
>>> mosaic: gs.MosaicSpec = "AB;CC"
""",
        "NormalizeSpec": """Finite color bounds or a Matplotlib-compatible normalizer.

Examples
--------
>>> import gsplot as gs
>>> normalizer: gs.NormalizeSpec = (0.0, 1.0)
""",
        "ColorSpec": """A Matplotlib color name or an RGB or RGBA channel tuple.

Examples
--------
>>> import gsplot as gs
>>> color: gs.ColorSpec = "tab:blue"
""",
        "AxesTarget": """One Axes or a deterministic finite collection of Axes.

Examples
--------
>>> import gsplot as gs
>>> figure, axes = gs.subplots("AB")
>>> target: gs.AxesTarget = axes
>>> import matplotlib.pyplot as plt
>>> plt.close(figure)
""",
        "PerTarget": """An ordered sequence or exact-key mapping of per-target values.

Examples
--------
>>> import gsplot as gs
>>> values: gs.PerTarget = {"A": 1, "B": 2}
""",
        "LineStyle": """A Matplotlib named line style or finite dash-tuple form.

Examples
--------
>>> import gsplot as gs
>>> line_style: gs.LineStyle = "--"
""",
        "Marker": """An input accepted by Matplotlib's MarkerStyle.

Examples
--------
>>> import gsplot as gs
>>> marker: gs.Marker = "o"
""",
        "Unit": """A supported physical figure-size unit.

Values are inches, centimetres, millimetres, or points.

Examples
--------
>>> import gsplot as gs
>>> unit: gs.Unit = "mm"
""",
        "SizePreset": """An automatic publication canvas choice.

Examples
--------
>>> import gsplot as gs
>>> preset: gs.SizePreset = "double"
""",
        "SizeSpec": """A publication preset, explicit dimensions, or ambient Figure size.

Examples
--------
>>> import gsplot as gs
>>> size: gs.SizeSpec = (85.0, 60.0)
""",
        "LayoutMode": """A supported Figure layout-engine selection.

Examples
--------
>>> import gsplot as gs
>>> layout: gs.LayoutMode = "constrained"
""",
        "StyleMode": """A concise target-local style selection.

Examples
--------
>>> import gsplot as gs
>>> style: gs.StyleMode = "paper"
""",
        "ZoomCorners": """Two explicit parent-to-inset connector-corner pairs.

Examples
--------
>>> import gsplot as gs
>>> corners: gs.ZoomCorners = ((3, 2), (4, 1))
""",
        "Limit": """A finite two-value axis limit whose order is preserved.

Examples
--------
>>> import gsplot as gs
>>> limits: gs.Limit = (0.0, 1.0)
""",
        "Scale": """A supported Cartesian axis scale name.

Examples
--------
>>> import gsplot as gs
>>> scale: gs.Scale = "log"
""",
        "TickSpec": """A finite sequence of numeric tick locations.

Examples
--------
>>> import gsplot as gs
>>> ticks: gs.TickSpec = (0.0, 0.5, 1.0)
""",
        "LabelRecord": """Concise x/y labels with optional x/y axis limits.

Examples
--------
>>> import gsplot as gs
>>> labels: gs.LabelRecord = ("x", "y", (0.0, 1.0), (0.0, 2.0))
""",
        "LabelRecords": """Ordered or exact-key per-target label records.

Examples
--------
>>> import gsplot as gs
>>> labels: gs.LabelRecords = (("x", "y"),)
""",
    }
)


class _NormalizeProtocol(Protocol):
    """Protocol for a Matplotlib-compatible color normalizer."""

    def __call__(self, value: Any, clip: bool | None = None) -> Any:
        """Normalize one or more scalar values."""


# Public type alias: NormalizeSpec; finite bounds or a Matplotlib normalizer.
NormalizeSpec: TypeAlias = tuple[float, float] | _NormalizeProtocol


_SCALES = {"linear", "log", "symlog", "logit"}
_DIRECTIONS = {"in", "out", "inout"}
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

    if value is None:
        return None
    if not isinstance(value, str):
        raise error(f"{name} must be a string or None")
    return value


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


def _limits(value: Any, name: str) -> tuple[float | None, float | None] | None:
    """Validate finite limits or partial limits while preserving their order."""

    if value is None:
        return None
    if isinstance(value, (str, bytes)):
        if value in ("", "*"):
            return None
        raise LayoutError(f"{name} must contain exactly two finite values")
    try:
        values = tuple(value)
    except TypeError as exc:
        raise LayoutError(f"{name} must contain exactly two finite values") from exc
    if len(values) != 2:
        raise LayoutError(f"{name} must contain exactly two finite values")
    low = (
        None
        if values[0] in (None, "", "*")
        else _finite(values[0], f"{name}[0]", LayoutError)
    )
    high = (
        None
        if values[1] in (None, "", "*")
        else _finite(values[1], f"{name}[1]", LayoutError)
    )
    if low is not None and high is not None and low == high:
        raise LayoutError(f"{name} values must not be equal")
    return (low, high)


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


def _nonnegative_finite(value: Any, name: str, default: float = 0.05) -> float:
    """Validate a non-negative finite margin value."""

    if value is None:
        return default
    if isinstance(value, bool):
        raise LayoutError(f"{name} must be non-negative")
    try:
        num = float(value)
    except (TypeError, ValueError) as exc:
        raise LayoutError(f"{name} must be non-negative") from exc
    if not math.isfinite(num) or num < 0:
        raise LayoutError(f"{name} must be non-negative")
    return num


@dataclass(frozen=True, slots=True, kw_only=True)
class AxisSpec:
    """Immutable Cartesian labels, limits, scales, ticks, and padding.

    Parameters
    ----------
    xlabel, ylabel
        Optional axis label strings.
    xlim, ylim
        Optional finite, unequal two-value limits.
    xscale, yscale
        One of ``"linear"``, ``"log"``, ``"symlog"``, or ``"logit"``.
    xticks, yticks
        Optional finite tick locations.
    xminor, yminor
        Optional minor-tick enable flags.
    xlabelpad, ylabelpad
        Optional finite label padding values.
    xmargin, ymargin
        Optional non-negative margin ratios for automatic endpoints.
    top, bottom, left, right
        Optional boolean flags for edge tick and label visibility.
    direction
        Optional tick direction: ``"in"``, ``"out"``, or ``"inout"``.

    Notes
    -----
    Instances are frozen and normalize sequence inputs to tuples.  Invalid
    values raise :class:`gsplot.LayoutError` before styling begins.

    Examples
    --------
    >>> import gsplot as gs
    >>> spec = gs.AxisSpec(xlabel="time", xscale="linear", right=False)
    >>> spec.xlabel
    'time'
    >>> spec.right
    False
    """

    xlabel: str | None = None
    ylabel: str | None = None
    xlim: Limit | None = None
    ylim: Limit | None = None
    xscale: Literal["linear", "log", "symlog", "logit"] = "linear"
    yscale: Literal["linear", "log", "symlog", "logit"] = "linear"
    xticks: tuple[float, ...] | None = None
    yticks: tuple[float, ...] | None = None
    xminor: bool | None = None
    yminor: bool | None = None
    xlabelpad: float | None = None
    ylabelpad: float | None = None
    xmargin: float = 0.05
    ymargin: float = 0.05
    top: bool | None = None
    bottom: bool | None = None
    left: bool | None = None
    right: bool | None = None
    direction: Literal["in", "out", "inout"] | None = None

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
        if not isinstance(self.xscale, str) or self.xscale not in _SCALES:
            raise LayoutError(f"xscale must be one of: {', '.join(sorted(_SCALES))}")
        if not isinstance(self.yscale, str) or self.yscale not in _SCALES:
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
        object.__setattr__(
            self, "xmargin", _nonnegative_finite(self.xmargin, "xmargin")
        )
        object.__setattr__(
            self, "ymargin", _nonnegative_finite(self.ymargin, "ymargin")
        )
        for edge_name, edge_val in (
            ("top", self.top),
            ("bottom", self.bottom),
            ("left", self.left),
            ("right", self.right),
        ):
            if edge_val is not None and not isinstance(edge_val, bool):
                raise LayoutError(f"{edge_name} must be a boolean or None")
        if self.direction is not None:
            if not isinstance(self.direction, str) or self.direction not in _DIRECTIONS:
                raise LayoutError(
                    f"direction must be one of: {', '.join(sorted(_DIRECTIONS))}"
                )


@dataclass(frozen=True, slots=True, kw_only=True)
class InsetSpec:
    """Immutable placement specification for an explicit parent Axes.

    Parameters
    ----------
    bounds
        Optional ``(left, bottom, width, height)`` parent-coordinate bounds.
    width, height
        Optional numeric or Matplotlib percentage sizes.  Both are required
        when ``bounds`` is omitted.
    loc
        Matplotlib location name or integer code from 1 through 10.
    bbox_to_anchor
        Optional two- or four-value finite anchor box.
    borderpad
        Non-negative inset border padding.

    Notes
    -----
    Instances are frozen and accept exactly one placement mode: ``bounds``
    or ``width`` plus ``height``.

    Examples
    --------
    >>> import gsplot as gs
    >>> spec = gs.InsetSpec(bounds=(0.6, 0.6, 0.3, 0.3))
    >>> spec.bounds
    (0.6, 0.6, 0.3, 0.3)
    """

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
        if has_bounds and (has_size or self.bbox_to_anchor is not None):
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
            try:
                values = tuple(self.bbox_to_anchor)
            except TypeError as exc:
                raise LayoutError(
                    "bbox_to_anchor must contain two or four finite values"
                ) from exc
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


@dataclass(frozen=True, slots=True, kw_only=True)
class Theme:
    """Immutable explicit Figure/Axes appearance values.

    Parameters
    ----------
    figure_facecolor, axes_facecolor
        Optional Figure and Axes patch colors.
    text_color, spine_color, tick_color
        Optional explicit artist colors.
    grid
        Optional grid visibility flag.
    grid_color, grid_alpha
        Optional grid color and alpha in the unit interval.

    Notes
    -----
    Instances are frozen, validate all colors, and never modify global
    Matplotlib ``rcParams``.  Use :func:`gsplot.set_theme` on an explicit
    Figure or Axes.

    Examples
    --------
    >>> import gsplot as gs
    >>> theme = gs.Theme(axes_facecolor="white", grid=True)
    >>> theme.grid
    True
    """

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
        """Return the no-op theme.

        Returns
        -------
        Theme
            An immutable theme with no requested changes.

        Examples
        --------
        >>> import gsplot as gs
        >>> theme = gs.Theme.default()
        >>> theme.grid is None
        True
        """

        return cls()

    @classmethod
    def white(cls) -> "Theme":
        """Return the explicit white-text theme from the reform contract.

        Returns
        -------
        Theme
            An immutable theme with transparent axes and white artists.

        Examples
        --------
        >>> import gsplot as gs
        >>> gs.Theme.white().text_color
        'white'
        """

        return cls(
            axes_facecolor=(1.0, 1.0, 1.0, 0.0),
            text_color="white",
            spine_color="white",
            tick_color="white",
        )

    @classmethod
    def transparent(cls) -> "Theme":
        """Return the explicit transparent Figure/Axes theme.

        Returns
        -------
        Theme
            An immutable theme with transparent Figure and Axes patches.

        Examples
        --------
        >>> import gsplot as gs
        >>> gs.Theme.transparent().figure_facecolor
        (0.0, 0.0, 0.0, 0.0)
        """

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
    if not isinstance(value, Mapping):
        raise MetadataError("labels must be a string-to-string mapping")
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


@dataclass(frozen=True, slots=True, kw_only=True)
class MetadataSnapshot:
    """Immutable, privacy-bounded metadata for one explicit output.

    Parameters
    ----------
    package_version
        Public package version string.
    schema_version
        Supported metadata schema identity, currently integer ``1``.
    commit
        Optional bounded public commit label; no machine path is inferred.
    config_digest
        Optional bounded public digest supplied by the caller.
    labels
        Optional string-to-string public labels, copied and frozen at
        construction.

    Notes
    -----
    Instances contain only explicitly supplied, bounded values.  They never
    collect environment variables, usernames, hostnames, paths, or files.

    Examples
    --------
    >>> import gsplot as gs
    >>> snapshot = gs.MetadataSnapshot(package_version=gs.__version__)
    >>> snapshot.schema_version
    1
    """

    package_version: str = field(kw_only=False)
    schema_version: Literal[1] = 1
    commit: str | None = None
    config_digest: str | None = None
    labels: Mapping[str, str] | None = None

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
    """Immutable distribution metadata returned by :func:`build_info`.

    Parameters
    ----------
    version
        Installed distribution version.
    commit
        Optional public commit label; normally ``None``.

    Examples
    --------
    >>> import gsplot as gs
    >>> info = gs.build_info()
    >>> info.version == gs.__version__
    True
    """

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
    """Immutable handles, labels, and local legend handler mappings.

    Parameters
    ----------
    handles
        Native Matplotlib legend handles in display order.
    labels
        String labels matched one-to-one with ``handles``.
    handler_map
        Local handler mapping copied from the caller.

    Notes
    -----
    The mapping is frozen and is never registered in Matplotlib's global
    default handler map.

    Examples
    --------
    >>> import gsplot as gs
    >>> entries = gs.LegendEntries(handles=(), labels=())
    >>> entries.labels
    ()
    """

    handles: Sequence[Artist]
    labels: Sequence[str]
    handler_map: Mapping[Any, HandlerBase] | None = None

    def __post_init__(self) -> None:
        """Normalize sequences and validate the entry relationship."""

        if isinstance(self.handles, (str, bytes)) or isinstance(
            self.labels, (str, bytes)
        ):
            raise PlotError("handles and labels must be sequences")
        try:
            handles = tuple(self.handles)
            labels = tuple(self.labels)
        except TypeError as exc:
            raise PlotError("handles and labels must be sequences") from exc
        if len(handles) != len(labels):
            raise PlotError("handles and labels must have the same length")
        if any(not isinstance(label, str) for label in labels):
            raise PlotError("legend labels must be strings")
        object.__setattr__(self, "handles", handles)
        object.__setattr__(self, "labels", labels)
        if self.handler_map is not None and not isinstance(self.handler_map, Mapping):
            raise PlotError("handler_map must be a mapping")
        handler_map = {} if self.handler_map is None else dict(self.handler_map)
        object.__setattr__(self, "handler_map", MappingProxyType(handler_map))


class AxesDict(dict[str, Axes]):
    """A dictionary of mosaic Axes supporting both label and integer index access.

    Parameters
    ----------
    *args, **kwargs
        Dictionary initialization mapping label strings to Matplotlib Axes.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, axes = gs.subplots("AB")
    >>> isinstance(axes, gs.AxesDict)
    True
    >>> axes["A"] is axes[0]
    True
    >>> figure.clear()
    """

    @overload
    def __getitem__(self, key: str) -> Axes: ...

    @overload
    def __getitem__(self, key: int) -> Axes: ...

    @overload
    def __getitem__(self, key: slice) -> list[Axes]: ...

    def __getitem__(self, key: str | int | slice) -> Any:
        """Return an Axes by label key, integer position, or slice."""
        if isinstance(key, int):
            try:
                return list(self.values())[key]
            except IndexError as exc:
                raise IndexError(
                    f"AxesDict index {key} out of range (length {len(self)})"
                ) from exc
        if isinstance(key, slice):
            return list(self.values())[key]
        return super().__getitem__(key)


__all__ = [
    "AxesDict",
    "RGBColor",
    "ColorSpec",
    "MosaicSpec",
    "AxesTarget",
    "PerTarget",
    "LineStyle",
    "Marker",
    "Unit",
    "SizePreset",
    "SizeSpec",
    "LayoutMode",
    "StyleMode",
    "ZoomCorners",
    "Limit",
    "Scale",
    "TickSpec",
    "LabelRecord",
    "LabelRecords",
    "NormalizeSpec",
    "AxisSpec",
    "InsetSpec",
    "Theme",
    "MetadataSnapshot",
    "BuildInfo",
    "LegendEntries",
]
