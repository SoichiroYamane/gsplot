"""Concise, preflighted line and scatter operations for explicit Axes targets."""

from __future__ import annotations

import inspect
import math
from collections.abc import Mapping, Sequence
from typing import Any, Final, TypeAlias, cast, overload

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.colors import is_color_like, to_rgba
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.markers import MarkerStyle
from matplotlib.typing import LineStyleType, MarkerType
from numpy.typing import ArrayLike, NDArray

from .._config.model import Config
from .._core.errors import OptionError, PlotError
from .._core.numerics import validate_xy
from .._core.options import MISSING, OptionSpec, bind_options
from .._core.plans import OptionPlan, TargetPlan
from .._core.targets import normalize_axes, resolve_target_mapping
from .._core.types import AxesTarget, ColorSpec
from .series import line_series, scatter_series, series_index

DataInput: TypeAlias = ArrayLike | Mapping[object, ArrayLike]
LineResult: TypeAlias = list[Line2D] | tuple[list[Line2D], ...]
ScatterResult: TypeAlias = PathCollection | tuple[PathCollection, ...]

LINE_ADVANCED_OPTIONS: Final[tuple[str, ...]] = (
    "color",
    "markersize",
    "markeredgewidth",
    "markeredgecolor",
    "markerfacecolor",
    "linestyle",
    "linewidth",
    "antialiased",
    "dash_capstyle",
    "dash_joinstyle",
    "drawstyle",
    "fillstyle",
    "gapcolor",
    "markevery",
    "markerfacecoloralt",
    "picker",
    "pickradius",
    "solid_capstyle",
    "solid_joinstyle",
    "visible",
    "zorder",
)
SCATTER_ADVANCED_OPTIONS: Final[tuple[str, ...]] = (
    "color",
    "size",
    "cmap",
    "norm",
    "vmin",
    "vmax",
    "edgecolors",
    "facecolors",
    "linewidths",
    "antialiaseds",
    "plotnonfinite",
    "rasterized",
    "picker",
    "visible",
    "zorder",
)

_LINE_PROPS = frozenset(
    {
        "alpha",
        "alpha_mfc",
        "antialiased",
        "c",
        "color",
        "dash_capstyle",
        "dash_joinstyle",
        "drawstyle",
        "fillstyle",
        "gapcolor",
        "label",
        "linestyle",
        "ls",
        "linewidth",
        "lw",
        "marker",
        "markeredgecolor",
        "markeredgewidth",
        "markerfacecolor",
        "markerfacecoloralt",
        "markersize",
        "markevery",
        "mec",
        "mew",
        "mfc",
        "ms",
        "picker",
        "pickradius",
        "solid_capstyle",
        "solid_joinstyle",
        "visible",
        "zorder",
    }
)
_SCATTER_PROPS = frozenset(
    {
        "alpha",
        "antialiaseds",
        "c",
        "cmap",
        "color",
        "edgecolors",
        "facecolors",
        "label",
        "linewidths",
        "marker",
        "norm",
        "picker",
        "plotnonfinite",
        "rasterized",
        "s",
        "size",
        "vmax",
        "vmin",
        "visible",
        "zorder",
    }
)

_LINE_MAPPING_FIELDS = frozenset(
    {
        "c",
        "color",
        "mec",
        "markeredgecolor",
        "mfc",
        "markerfacecolor",
    }
)
_LINE_AMBIGUOUS_FIELDS = frozenset({"marker", "ls", "linestyle"})
_LINE_ORDERED_FIELDS = frozenset(
    {
        "series",
        "label",
        "marker",
        "ms",
        "markersize",
        "mew",
        "markeredgewidth",
        "alpha_mfc",
        "ls",
        "linestyle",
        "lw",
        "linewidth",
        "alpha",
    }
)
_SCATTER_MAPPING_FIELDS = frozenset({"c", "color", "edgecolors", "facecolors"})
_SCATTER_AMBIGUOUS_FIELDS = frozenset({"marker"})
_SCATTER_ORDERED_FIELDS = frozenset({"series", "label", "marker", "s", "size", "alpha"})


def validate_axes(ax: Any) -> Axes:
    """Validate one explicit Matplotlib Axes target."""

    if not isinstance(ax, Axes):
        raise PlotError("ax must be a Matplotlib Axes")
    return ax


def validate_props(
    props: Mapping[str, Any] | None,
    allowed: frozenset[str],
    context: str,
) -> dict[str, Any]:
    """Copy a closed property mapping before any artist is created."""

    if props is None:
        return {}
    if not isinstance(props, Mapping):
        raise PlotError(f"{context} props must be a mapping")
    if any(not isinstance(key, str) for key in props):
        raise PlotError(f"{context} props keys must be strings")
    unknown = sorted(set(props) - allowed)
    if unknown:
        joined = ", ".join(repr(key) for key in unknown)
        raise OptionError(f"{context} props contains unknown key(s): {joined}")
    return dict(props)


def _optional_color(value: Any, name: str) -> Any:
    """Validate one optional Matplotlib color without changing its spelling."""

    if value is MISSING:
        return MISSING
    if value is None:
        return None
    try:
        to_rgba(value)
    except (TypeError, ValueError) as exc:
        raise PlotError(f"{name} must be a valid Matplotlib color") from exc
    return value


def _marker(value: Any, name: str) -> MarkerStyle:
    """Copy one value accepted by Matplotlib's MarkerStyle."""

    try:
        return MarkerStyle(value)
    except (TypeError, ValueError) as exc:
        raise PlotError(f"{name} must be a valid Matplotlib marker") from exc


def _linestyle(value: Any, name: str) -> Any:
    """Validate one named or finite dash-tuple line style."""

    probe = Line2D([], [])
    try:
        probe.set_linestyle(value)
    except (TypeError, ValueError) as exc:
        raise PlotError(f"{name} must be a valid Matplotlib line style") from exc
    return value


def _finite(value: Any, name: str, *, minimum: float | None = None) -> float:
    """Return one finite real scalar, optionally with a closed lower bound."""

    if value is MISSING:
        return cast(float, MISSING)
    if isinstance(value, bool):
        raise PlotError(f"{name} must be a finite real number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise PlotError(f"{name} must be a finite real number") from exc
    if not math.isfinite(result):
        raise PlotError(f"{name} must be a finite real number")
    if minimum is not None and result < minimum:
        raise PlotError(f"{name} must be at least {minimum:g}")
    return result


def _nonnegative(value: Any, name: str) -> float:
    """Return one finite non-negative real scalar."""

    return _finite(value, name, minimum=0.0)


def _alpha(value: Any, name: str) -> float:
    """Return one finite alpha value in the closed unit interval."""

    result = _nonnegative(value, name)
    if result > 1:
        raise PlotError(f"{name} must be between 0 and 1")
    return result


def _label(value: Any, name: str) -> str | None:
    """Validate one optional artist label."""

    if value is MISSING:
        return cast(str, MISSING)
    if value is not None and not isinstance(value, str):
        raise PlotError(f"{name} must be a string or None")
    return value


def _scatter_c(value: Any, name: str) -> Any:
    """Validate a concise color or retained finite Matplotlib c-array."""

    if value is MISSING:
        return MISSING
    if value is None or is_color_like(value):
        return value
    try:
        array = np.asarray(value)
    except (TypeError, ValueError) as exc:
        raise PlotError(f"{name} must be a color or finite color-value array") from exc
    if array.size == 0:
        raise PlotError(f"{name} must not be empty")
    if np.issubdtype(array.dtype, np.number) and not np.all(np.isfinite(array)):
        raise PlotError(f"{name} must contain only finite values")
    return value


_LINE_SPECS: Final[tuple[OptionSpec[Any], ...]] = (
    OptionSpec("label", MISSING, validator=_label),
    OptionSpec("color", MISSING, aliases=("c",), validator=_optional_color),
    OptionSpec("marker", "o", validator=_marker),
    OptionSpec("markersize", 7.0, aliases=("ms",), validator=_nonnegative),
    OptionSpec("markeredgewidth", 1.5, aliases=("mew",), validator=_nonnegative),
    OptionSpec("markeredgecolor", MISSING, aliases=("mec",), validator=_optional_color),
    OptionSpec("markerfacecolor", MISSING, aliases=("mfc",), validator=_optional_color),
    OptionSpec("alpha_mfc", 0.2, validator=_alpha),
    OptionSpec("linestyle", "--", aliases=("ls",), validator=_linestyle),
    OptionSpec("linewidth", 1.0, aliases=("lw",), validator=_nonnegative),
    OptionSpec("alpha", 1.0, validator=_alpha),
    OptionSpec("antialiased", MISSING),
    OptionSpec("dash_capstyle", MISSING),
    OptionSpec("dash_joinstyle", MISSING),
    OptionSpec("drawstyle", MISSING),
    OptionSpec("fillstyle", MISSING),
    OptionSpec("gapcolor", MISSING),
    OptionSpec("markevery", MISSING),
    OptionSpec("markerfacecoloralt", MISSING),
    OptionSpec("picker", MISSING),
    OptionSpec("pickradius", MISSING, validator=_nonnegative),
    OptionSpec("solid_capstyle", MISSING),
    OptionSpec("solid_joinstyle", MISSING),
    OptionSpec("visible", MISSING),
    OptionSpec("zorder", MISSING, validator=_finite),
)
_SCATTER_SPECS: Final[tuple[OptionSpec[Any], ...]] = (
    OptionSpec("label", MISSING, validator=_label),
    OptionSpec("c", MISSING, validator=_scatter_c),
    OptionSpec("color", MISSING, validator=_optional_color),
    OptionSpec("marker", "o", validator=_marker),
    OptionSpec("s", 1.0, aliases=("size",), validator=_nonnegative),
    OptionSpec("alpha", 1.0, validator=_alpha),
    OptionSpec("cmap", MISSING),
    OptionSpec("norm", MISSING),
    OptionSpec("vmin", MISSING, validator=_finite),
    OptionSpec("vmax", MISSING, validator=_finite),
    OptionSpec("edgecolors", MISSING),
    OptionSpec("facecolors", MISSING),
    OptionSpec("linewidths", MISSING),
    OptionSpec("antialiaseds", MISSING),
    OptionSpec("plotnonfinite", MISSING),
    OptionSpec("rasterized", MISSING),
    OptionSpec("picker", MISSING),
    OptionSpec("visible", MISSING),
    OptionSpec("zorder", MISSING, validator=_finite),
)


def _ordered_values(value: Any) -> tuple[Any, ...] | None:
    """Snapshot an unambiguous ordered per-target style container."""

    if isinstance(value, np.ndarray):
        if value.ndim != 1:
            return None
        return tuple(value.tolist())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(value)
    return None


def _per_target(
    target: TargetPlan,
    value: Any,
    *,
    name: str,
    mapping_only: bool,
    ordered: bool,
    ambiguous: bool,
) -> tuple[Any, ...]:
    """Resolve one scalar or explicitly per-target value before binding."""

    if value is MISSING:
        return (MISSING,) * len(target.axes)
    if isinstance(value, Mapping):
        if not (mapping_only or ordered):
            return (value,) * len(target.axes)
        return resolve_target_mapping(target, value, name=name)
    values = _ordered_values(value) if ordered and not target.single else None
    if values is not None and ambiguous:
        validator = _marker if name == "marker" else _linestyle
        try:
            validator(value, name)
        except PlotError:
            pass
        else:
            return (value,) * len(target.axes)
    if values is not None:
        if len(values) != len(target.axes):
            raise PlotError(
                f"{target.operation}: {name} must contain one value per target"
            )
        return values
    return (value,) * len(target.axes)


def _expand_options(
    target: TargetPlan,
    values: Mapping[str, Any],
    *,
    mapping_fields: frozenset[str],
    ordered_fields: frozenset[str],
    ambiguous_fields: frozenset[str],
) -> tuple[dict[str, Any], ...]:
    """Expand finite direct or props values into target-local mappings."""

    expanded: list[dict[str, Any]] = [dict() for _ in target.axes]
    for name, value in values.items():
        selected = _per_target(
            target,
            value,
            name=name,
            mapping_only=name in mapping_fields,
            ordered=name in ordered_fields,
            ambiguous=name in ambiguous_fields,
        )
        for index, item in enumerate(selected):
            expanded[index][name] = item
    return tuple(expanded)


def _datasets(
    target: TargetPlan,
    x: DataInput,
    y: DataInput,
) -> tuple[tuple[NDArray[np.float64], NDArray[np.float64]], ...]:
    """Copy broadcast or exact-key x/y data for every target."""

    x_mapping = isinstance(x, Mapping)
    y_mapping = isinstance(y, Mapping)
    if x_mapping != y_mapping:
        raise PlotError(
            f"{target.operation}: x and y must both use exact per-target mappings"
        )
    x_values: tuple[ArrayLike, ...]
    y_values: tuple[ArrayLike, ...]
    if x_mapping and y_mapping:
        x_values = resolve_target_mapping(
            target, cast(Mapping[object, ArrayLike], x), name="x"
        )
        y_values = resolve_target_mapping(
            target, cast(Mapping[object, ArrayLike], y), name="y"
        )
    else:
        x_values = (cast(ArrayLike, x),) * len(target.axes)
        y_values = (cast(ArrayLike, y),) * len(target.axes)
    return tuple(
        validate_xy(x_item, y_item) for x_item, y_item in zip(x_values, y_values)
    )


def _config_color(config: Config | None) -> Any:
    """Validate Config and return its explicit color or the omission sentinel."""

    if config is None:
        return MISSING
    if not isinstance(config, Config):
        raise PlotError("config must be a gsplot Config")
    color = config.plotting.default_color
    return MISSING if color == "axes" else color


def _has_value(values: Mapping[str, Any], names: set[str]) -> bool:
    """Return whether one spelling was actually supplied in a finite mapping."""

    return any(name in values and values[name] is not MISSING for name in names)


def _line_plans(
    target: TargetPlan,
    direct: tuple[dict[str, Any], ...],
    properties: tuple[dict[str, Any], ...],
    series_values: tuple[Any, ...],
    config_color: Any,
) -> tuple[OptionPlan, ...]:
    """Bind every line option with explicit provenance before plotting."""

    plans: list[OptionPlan] = []
    for explicit, props, selected_series in zip(direct, properties, series_values):
        derived: dict[str, Any] = {}
        if selected_series is not MISSING and selected_series is not None:
            color, linestyle = line_series(selected_series)
            derived.update(color=color, linestyle=linestyle)
        configured = {} if config_color is MISSING else {"color": config_color}
        plans.append(
            bind_options(
                "line",
                _LINE_SPECS,
                explicit=explicit,
                derived=derived,
                configured=configured,
                props=props,
            )
        )
    return tuple(plans)


def _scatter_plans(
    target: TargetPlan,
    direct: tuple[dict[str, Any], ...],
    properties: tuple[dict[str, Any], ...],
    series_values: tuple[Any, ...],
    config_color: Any,
) -> tuple[OptionPlan, ...]:
    """Bind every scatter option and reject overlapping color controls."""

    plans: list[OptionPlan] = []
    controls = {"c", "color", "facecolors"}
    for explicit, props, selected_series in zip(direct, properties, series_values):
        supplied_controls = {
            name
            for name in controls
            if _has_value(explicit, {name}) or _has_value(props, {name})
        }
        if len(supplied_controls) > 1:
            joined = ", ".join(sorted(supplied_controls))
            raise OptionError(f"scatter cannot combine color controls: {joined}")
        derived: dict[str, Any] = {}
        if selected_series is not MISSING and selected_series is not None:
            color, marker = scatter_series(selected_series)
            derived["marker"] = marker
            if not supplied_controls:
                derived["color"] = color
        configured: dict[str, Any] = {}
        if not supplied_controls and config_color is not MISSING:
            configured["color"] = config_color
        plans.append(
            bind_options(
                "scatter",
                _SCATTER_SPECS,
                explicit=explicit,
                derived=derived,
                configured=configured,
                props=props,
            )
        )
    return tuple(plans)


def _line_kwargs(options: OptionPlan) -> tuple[dict[str, Any], bool, bool]:
    """Convert one immutable line plan into Matplotlib properties."""

    values = {
        name: value
        for name, value in options.items()
        if value is not MISSING and name != "alpha_mfc"
    }
    edge = values.get("markeredgecolor", MISSING)
    default_edge = edge is MISSING or edge is None
    if default_edge:
        values.pop("markeredgecolor", None)
    face = values.get("markerfacecolor", MISSING)
    default_face = face is MISSING or face is None
    if default_face:
        values.pop("markerfacecolor", None)
    elif not (isinstance(face, str) and face.lower() == "none"):
        red, green, blue, _ = to_rgba(cast(ColorSpec, face))
        values["markerfacecolor"] = (
            red,
            green,
            blue,
            options["alpha"] * options["alpha_mfc"],
        )
    return values, default_edge, default_face


def _scatter_kwargs(options: OptionPlan) -> dict[str, Any]:
    """Convert one immutable scatter plan into Matplotlib properties."""

    return {name: value for name, value in options.items() if value is not MISSING}


def _preflight_line(
    datasets: tuple[tuple[NDArray[np.float64], NDArray[np.float64]], ...],
    options: tuple[OptionPlan, ...],
) -> tuple[tuple[dict[str, Any], bool, bool], ...]:
    """Exercise all line data and properties on detached Matplotlib objects."""

    prepared = tuple(_line_kwargs(plan) for plan in options)
    try:
        probe = Figure().add_subplot()
        for (x_values, y_values), (values, _, _) in zip(datasets, prepared):
            probe.plot(x_values, y_values, **values)
    except (TypeError, ValueError) as exc:
        raise PlotError("line: invalid plotting options") from exc
    return prepared


def _preflight_scatter(
    datasets: tuple[tuple[NDArray[np.float64], NDArray[np.float64]], ...],
    options: tuple[OptionPlan, ...],
) -> tuple[dict[str, Any], ...]:
    """Exercise all scatter data and properties on detached Matplotlib objects."""

    prepared = tuple(_scatter_kwargs(plan) for plan in options)
    try:
        probe = Figure().add_subplot()
        for (x_values, y_values), values in zip(datasets, prepared):
            probe.scatter(x_values, y_values, **values)
    except (TypeError, ValueError) as exc:
        raise PlotError("scatter: invalid plotting options") from exc
    return prepared


@overload
def line(
    target: AxesTarget,
    x: DataInput,
    y: DataInput,
    *,
    series: int | Sequence[int] | Mapping[object, int] | None = None,
    label: str | Sequence[str] | Mapping[object, str] | None = None,
    c: ColorSpec | Mapping[object, ColorSpec] | None = None,
    marker: MarkerType | Sequence[MarkerType] | Mapping[object, MarkerType] = "o",
    ms: float | Sequence[float] | Mapping[object, float] = 7,
    mew: float | Sequence[float] | Mapping[object, float] = 1.5,
    mec: ColorSpec | Mapping[object, ColorSpec] | None = None,
    mfc: ColorSpec | Mapping[object, ColorSpec] | None = None,
    alpha_mfc: float | Sequence[float] | Mapping[object, float] = 0.2,
    ls: LineStyleType | Sequence[LineStyleType] | Mapping[object, LineStyleType] = "--",
    lw: float | Sequence[float] | Mapping[object, float] = 1,
    alpha: float | Sequence[float] | Mapping[object, float] = 1,
    config: Config | None = None,
    props: Mapping[str, object] | None = None,
) -> LineResult: ...


@overload
def line(
    target: AxesTarget,
    x: DataInput,
    y: DataInput,
    *,
    series: Any = None,
    label: Any = None,
    c: Any = None,
    marker: Any = "o",
    ms: Any = 7,
    mew: Any = 1.5,
    mec: Any = None,
    mfc: Any = None,
    alpha_mfc: Any = 0.2,
    ls: Any = "--",
    lw: Any = 1,
    alpha: Any = 1,
    config: Config | None = None,
    props: Mapping[str, object] | None = None,
    color: Any = None,
    markersize: Any = 7,
    markeredgewidth: Any = 1.5,
    markeredgecolor: Any = None,
    markerfacecolor: Any = None,
    linestyle: Any = "--",
    linewidth: Any = 1,
    antialiased: Any = None,
    dash_capstyle: Any = None,
    dash_joinstyle: Any = None,
    drawstyle: Any = None,
    fillstyle: Any = None,
    gapcolor: Any = None,
    markevery: Any = None,
    markerfacecoloralt: Any = None,
    picker: Any = None,
    pickradius: Any = None,
    solid_capstyle: Any = None,
    solid_joinstyle: Any = None,
    visible: Any = None,
    zorder: Any = None,
) -> LineResult: ...


def line(
    target: AxesTarget,
    x: DataInput,
    y: DataInput,
    *,
    series: Any = MISSING,
    label: Any = MISSING,
    c: Any = MISSING,
    marker: Any = MISSING,
    ms: Any = MISSING,
    mew: Any = MISSING,
    mec: Any = MISSING,
    mfc: Any = MISSING,
    alpha_mfc: Any = MISSING,
    ls: Any = MISSING,
    lw: Any = MISSING,
    alpha: Any = MISSING,
    config: Config | None = None,
    props: Mapping[str, object] | None = None,
    color: Any = MISSING,
    markersize: Any = MISSING,
    markeredgewidth: Any = MISSING,
    markeredgecolor: Any = MISSING,
    markerfacecolor: Any = MISSING,
    linestyle: Any = MISSING,
    linewidth: Any = MISSING,
    antialiased: Any = MISSING,
    dash_capstyle: Any = MISSING,
    dash_joinstyle: Any = MISSING,
    drawstyle: Any = MISSING,
    fillstyle: Any = MISSING,
    gapcolor: Any = MISSING,
    markevery: Any = MISSING,
    markerfacecoloralt: Any = MISSING,
    picker: Any = MISSING,
    pickradius: Any = MISSING,
    solid_capstyle: Any = MISSING,
    solid_joinstyle: Any = MISSING,
    visible: Any = MISSING,
    zorder: Any = MISSING,
) -> LineResult:
    """Plot publication-ready lines on one or more explicit Axes.

    Parameters
    ----------
    target
        One Axes or a deterministic same-Figure collection of Axes.
    x, y
        One finite one-dimensional pair broadcast to every target, or two
        exact-key mappings containing one pair per target.
    series
        Optional deterministic publication identity from 0 through 9.
    label, c, marker, ms, mew, mec, mfc, alpha_mfc, ls, lw, alpha
        Concise line controls. Scalars broadcast; exact-key mappings provide
        per-target colors, markers, and line styles.
    config
        Optional immutable configuration for omitted values.
    props
        Optional closed advanced property mapping. It cannot duplicate a
        separately supplied direct field.

    Returns
    -------
    list[matplotlib.lines.Line2D] or tuple of lists
        Native Matplotlib line results in normalized target order.

    Raises
    ------
    DataError, PlotError
        If targets, data, series, or style values fail atomic preflight.

    Notes
    -----
    The target Axes cycle supplies color when both ``series`` and ``c`` are
    omitted. Long Matplotlib spellings and the names in
    ``LINE_ADVANCED_OPTIONS`` remain accepted through 1.x.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, ax = gs.subplots()
    >>> artists = gs.line(ax, [0, 1], [1, 2], series=0, label="sample")
    >>> artists[0].axes is ax
    True
    >>> figure.clear()
    """

    target_plan = normalize_axes(target, operation="line")
    datasets = _datasets(target_plan, x, y)
    config_color = _config_color(config)
    direct_values = {
        "label": label,
        "c": c,
        "marker": marker,
        "ms": ms,
        "mew": mew,
        "mec": mec,
        "mfc": mfc,
        "alpha_mfc": alpha_mfc,
        "ls": ls,
        "lw": lw,
        "alpha": alpha,
        "color": color,
        "markersize": markersize,
        "markeredgewidth": markeredgewidth,
        "markeredgecolor": markeredgecolor,
        "markerfacecolor": markerfacecolor,
        "linestyle": linestyle,
        "linewidth": linewidth,
        "antialiased": antialiased,
        "dash_capstyle": dash_capstyle,
        "dash_joinstyle": dash_joinstyle,
        "drawstyle": drawstyle,
        "fillstyle": fillstyle,
        "gapcolor": gapcolor,
        "markevery": markevery,
        "markerfacecoloralt": markerfacecoloralt,
        "picker": picker,
        "pickradius": pickradius,
        "solid_capstyle": solid_capstyle,
        "solid_joinstyle": solid_joinstyle,
        "visible": visible,
        "zorder": zorder,
    }
    direct = _expand_options(
        target_plan,
        direct_values,
        mapping_fields=_LINE_MAPPING_FIELDS,
        ordered_fields=_LINE_ORDERED_FIELDS,
        ambiguous_fields=_LINE_AMBIGUOUS_FIELDS,
    )
    selected_props = validate_props(props, _LINE_PROPS, "line")
    properties = _expand_options(
        target_plan,
        selected_props,
        mapping_fields=_LINE_MAPPING_FIELDS,
        ordered_fields=_LINE_ORDERED_FIELDS,
        ambiguous_fields=_LINE_AMBIGUOUS_FIELDS,
    )
    series_values = _per_target(
        target_plan,
        series,
        name="series",
        mapping_only=False,
        ordered=True,
        ambiguous=False,
    )
    for value in series_values:
        if value is not MISSING and value is not None:
            series_index(value)
    plans = _line_plans(target_plan, direct, properties, series_values, config_color)
    prepared = _preflight_line(datasets, plans)

    results: list[list[Line2D]] = []
    created: list[Line2D] = []
    try:
        for axis, (x_values, y_values), plan, item in zip(
            target_plan.axes, datasets, plans, prepared
        ):
            values, default_edge, default_face = item
            artists = list(axis.plot(x_values, y_values, **values))
            for artist in artists:
                if default_edge:
                    artist.set_markeredgecolor(artist.get_color())
                if default_face:
                    red, green, blue, _ = to_rgba(artist.get_color())
                    artist.set_markerfacecolor(
                        (red, green, blue, plan["alpha"] * plan["alpha_mfc"])
                    )
            results.append(artists)
            created.extend(artists)
    except Exception:
        for artist in reversed(created):
            artist.remove()
        raise
    return results[0] if target_plan.single else tuple(results)


@overload
def scatter(
    target: AxesTarget,
    x: DataInput,
    y: DataInput,
    *,
    series: int | Sequence[int] | Mapping[object, int] | None = None,
    label: str | Sequence[str] | Mapping[object, str] | None = None,
    c: ColorSpec | Mapping[object, ColorSpec] | None = None,
    marker: MarkerType | Sequence[MarkerType] | Mapping[object, MarkerType] = "o",
    s: float | Sequence[float] | Mapping[object, float] = 1,
    alpha: float | Sequence[float] | Mapping[object, float] = 1,
    config: Config | None = None,
    props: Mapping[str, object] | None = None,
) -> ScatterResult: ...


@overload
def scatter(
    target: AxesTarget,
    x: DataInput,
    y: DataInput,
    *,
    series: Any = None,
    label: Any = None,
    c: Any = None,
    marker: Any = "o",
    s: Any = 1,
    alpha: Any = 1,
    config: Config | None = None,
    props: Mapping[str, object] | None = None,
    color: Any = None,
    size: Any = 1,
    cmap: Any = None,
    norm: Any = None,
    vmin: Any = None,
    vmax: Any = None,
    edgecolors: Any = None,
    facecolors: Any = None,
    linewidths: Any = None,
    antialiaseds: Any = None,
    plotnonfinite: Any = None,
    rasterized: Any = None,
    picker: Any = None,
    visible: Any = None,
    zorder: Any = None,
) -> ScatterResult: ...


def scatter(
    target: AxesTarget,
    x: DataInput,
    y: DataInput,
    *,
    series: Any = MISSING,
    label: Any = MISSING,
    c: Any = MISSING,
    marker: Any = MISSING,
    s: Any = MISSING,
    alpha: Any = MISSING,
    config: Config | None = None,
    props: Mapping[str, object] | None = None,
    color: Any = MISSING,
    size: Any = MISSING,
    cmap: Any = MISSING,
    norm: Any = MISSING,
    vmin: Any = MISSING,
    vmax: Any = MISSING,
    edgecolors: Any = MISSING,
    facecolors: Any = MISSING,
    linewidths: Any = MISSING,
    antialiaseds: Any = MISSING,
    plotnonfinite: Any = MISSING,
    rasterized: Any = MISSING,
    picker: Any = MISSING,
    visible: Any = MISSING,
    zorder: Any = MISSING,
) -> ScatterResult:
    """Plot publication-ready points on one or more explicit Axes.

    Parameters
    ----------
    target
        One Axes or a deterministic same-Figure collection of Axes.
    x, y
        One finite one-dimensional pair broadcast to every target, or two
        exact-key mappings containing one pair per target.
    series
        Optional deterministic publication identity from 0 through 9.
    label, c, marker, s, alpha
        Concise point controls. Scalars broadcast; exact-key mappings provide
        per-target colors and markers.
    config
        Optional immutable configuration for omitted values.
    props
        Optional closed advanced property mapping. It cannot duplicate a
        separately supplied direct field.

    Returns
    -------
    matplotlib.collections.PathCollection or tuple of PathCollection
        Native Matplotlib collections in normalized target order.

    Raises
    ------
    DataError, PlotError
        If targets, data, series, or style values fail atomic preflight.

    Notes
    -----
    The target Axes cycle supplies color when both ``series`` and ``c`` are
    omitted. Long Matplotlib spellings and the names in
    ``SCATTER_ADVANCED_OPTIONS`` remain accepted through 1.x.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, ax = gs.subplots()
    >>> points = gs.scatter(ax, [0, 1], [1, 2], series=1, label="sample")
    >>> points.axes is ax
    True
    >>> figure.clear()
    """

    target_plan = normalize_axes(target, operation="scatter")
    datasets = _datasets(target_plan, x, y)
    config_color = _config_color(config)
    direct_values = {
        "label": label,
        "c": c,
        "marker": marker,
        "s": s,
        "alpha": alpha,
        "color": color,
        "size": size,
        "cmap": cmap,
        "norm": norm,
        "vmin": vmin,
        "vmax": vmax,
        "edgecolors": edgecolors,
        "facecolors": facecolors,
        "linewidths": linewidths,
        "antialiaseds": antialiaseds,
        "plotnonfinite": plotnonfinite,
        "rasterized": rasterized,
        "picker": picker,
        "visible": visible,
        "zorder": zorder,
    }
    direct = _expand_options(
        target_plan,
        direct_values,
        mapping_fields=_SCATTER_MAPPING_FIELDS,
        ordered_fields=_SCATTER_ORDERED_FIELDS,
        ambiguous_fields=_SCATTER_AMBIGUOUS_FIELDS,
    )
    selected_props = validate_props(props, _SCATTER_PROPS, "scatter")
    properties = _expand_options(
        target_plan,
        selected_props,
        mapping_fields=_SCATTER_MAPPING_FIELDS,
        ordered_fields=_SCATTER_ORDERED_FIELDS,
        ambiguous_fields=_SCATTER_AMBIGUOUS_FIELDS,
    )
    series_values = _per_target(
        target_plan,
        series,
        name="series",
        mapping_only=False,
        ordered=True,
        ambiguous=False,
    )
    for value in series_values:
        if value is not MISSING and value is not None:
            series_index(value)
    plans = _scatter_plans(target_plan, direct, properties, series_values, config_color)
    prepared = _preflight_scatter(datasets, plans)

    results: list[PathCollection] = []
    try:
        for axis, (x_values, y_values), values in zip(
            target_plan.axes, datasets, prepared
        ):
            results.append(axis.scatter(x_values, y_values, **values))
    except Exception:
        for collection in reversed(results):
            collection.remove()
        raise
    return results[0] if target_plan.single else tuple(results)


def _line_signature(
    target: AxesTarget,
    x: DataInput,
    y: DataInput,
    *,
    series: int | Sequence[int] | Mapping[object, int] | None = None,
    label: str | Sequence[str] | Mapping[object, str] | None = None,
    c: ColorSpec | Mapping[object, ColorSpec] | None = None,
    marker: MarkerType | Sequence[MarkerType] | Mapping[object, MarkerType] = "o",
    ms: float | Sequence[float] | Mapping[object, float] = 7,
    mew: float | Sequence[float] | Mapping[object, float] = 1.5,
    mec: ColorSpec | Mapping[object, ColorSpec] | None = None,
    mfc: ColorSpec | Mapping[object, ColorSpec] | None = None,
    alpha_mfc: float | Sequence[float] | Mapping[object, float] = 0.2,
    ls: LineStyleType | Sequence[LineStyleType] | Mapping[object, LineStyleType] = "--",
    lw: float | Sequence[float] | Mapping[object, float] = 1,
    alpha: float | Sequence[float] | Mapping[object, float] = 1,
    config: Config | None = None,
    props: Mapping[str, object] | None = None,
) -> LineResult:
    raise AssertionError("signature-only function")


def _scatter_signature(
    target: AxesTarget,
    x: DataInput,
    y: DataInput,
    *,
    series: int | Sequence[int] | Mapping[object, int] | None = None,
    label: str | Sequence[str] | Mapping[object, str] | None = None,
    c: ColorSpec | Mapping[object, ColorSpec] | None = None,
    marker: MarkerType | Sequence[MarkerType] | Mapping[object, MarkerType] = "o",
    s: float | Sequence[float] | Mapping[object, float] = 1,
    alpha: float | Sequence[float] | Mapping[object, float] = 1,
    config: Config | None = None,
    props: Mapping[str, object] | None = None,
) -> ScatterResult:
    raise AssertionError("signature-only function")


line.__signature__ = inspect.signature(_line_signature)  # type: ignore[attr-defined]
scatter.__signature__ = inspect.signature(_scatter_signature)  # type: ignore[attr-defined]


__all__ = [
    "LINE_ADVANCED_OPTIONS",
    "SCATTER_ADVANCED_OPTIONS",
    "line",
    "scatter",
    "validate_axes",
    "validate_props",
]
