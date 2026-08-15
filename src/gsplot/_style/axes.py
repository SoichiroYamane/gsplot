"""Explicit Axes labels, scales, limits, ticks, and text helpers."""

from __future__ import annotations

import inspect
from collections.abc import Mapping, Sequence
from typing import Any, Literal, cast, get_type_hints, overload

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.text import Text

from .._core.errors import LayoutError, OptionError, PlotError
from .._core.options import MISSING
from .._core.plans import TargetPlan
from .._core.targets import normalize_axes, resolve_target_mapping
from .._core.types import (
    _SCALES,
    AxesTarget,
    AxisSpec,
    LabelRecords,
    Limit,
    Scale,
    TickSpec,
    _limits,
)
from .._core.validation import ensure_bool, ensure_finite_real, ensure_positive

_TEXT_PROPS = frozenset(
    {
        "alpha",
        "color",
        "fontfamily",
        "fontproperties",
        "fontsize",
        "fontstretch",
        "fontstyle",
        "fontvariant",
        "fontweight",
        "ha",
        "horizontalalignment",
        "label",
        "linespacing",
        "math_fontfamily",
        "multialignment",
        "parse_math",
        "rotation",
        "rotation_mode",
        "va",
        "verticalalignment",
        "visible",
        "zorder",
    }
)
_TITLE_PROPS = _TEXT_PROPS | {"bbox", "fontdict", "loc", "pad", "y"}


def axes_targets(target: AxesTarget) -> tuple[Axes, ...]:
    """Validate and normalize an explicit Axes target collection."""

    values: tuple[Axes, ...]
    if isinstance(target, Axes):
        values = (target,)
    elif isinstance(target, Mapping):
        values = tuple(target.values())
    elif isinstance(target, np.ndarray):
        values = tuple(target.flat)
    elif isinstance(target, Sequence) and not isinstance(target, (str, bytes)):
        values = tuple(target)
    else:
        raise LayoutError("target must be an Axes or an Axes sequence/mapping")
    if any(not isinstance(axis, Axes) for axis in values):
        raise LayoutError("target contains a non-Matplotlib Axes")
    return values


def _validate_props(
    props: Mapping[str, Any] | None, allowed: frozenset[str], name: str
) -> dict[str, Any]:
    """Copy a closed styling property mapping."""

    if props is None:
        return {}
    if not isinstance(props, Mapping):
        raise PlotError(f"{name} props must be a mapping")
    if any(not isinstance(key, str) for key in props):
        raise PlotError(f"{name} props keys must be strings")
    unknown = sorted(set(props) - allowed)
    if unknown:
        joined = ", ".join(repr(key) for key in unknown)
        raise OptionError(f"{name} props contains unknown key(s): {joined}")
    return dict(props)


def _validate_scale_domain(axis: Axes, spec: AxisSpec) -> None:
    """Reject impossible log/logit domains before a target is mutated."""

    for coordinate, scale, limits, ticks in (
        ("x", spec.xscale, spec.xlim, spec.xticks),
        ("y", spec.yscale, spec.ylim, spec.yticks),
    ):
        if scale == "linear" or scale == "symlog":
            continue
        if limits is not None:
            domain_values: tuple[float, ...] = limits
        elif axis.has_data():
            bounds = (
                axis.dataLim.intervalx if coordinate == "x" else axis.dataLim.intervaly
            )
            domain_values = tuple(float(item) for item in bounds)
        else:
            domain_values = ()
        if any(not np.isfinite(value) for value in domain_values):
            raise LayoutError(
                f"{coordinate}scale={scale!r} requires finite domain data"
            )
        if scale == "log" and any(value <= 0 for value in domain_values):
            raise LayoutError(f"{coordinate}scale='log' requires positive data")
        if scale == "logit" and any(
            value <= 0 or value >= 1 for value in domain_values
        ):
            raise LayoutError(f"{coordinate}scale='logit' requires data in (0, 1)")
        if ticks is not None:
            if scale == "log" and any(value <= 0 for value in ticks):
                raise LayoutError(f"{coordinate}scale='log' requires positive ticks")
            if scale == "logit" and any(value <= 0 or value >= 1 for value in ticks):
                raise LayoutError(f"{coordinate}scale='logit' requires ticks in (0, 1)")


def style_axes(target: AxesTarget, spec: AxisSpec) -> None:
    """Apply one validated :class:`AxisSpec` to explicit Axes targets.

    Parameters
    ----------
    target
        One Axes, an ordered Axes sequence, or a string-keyed Axes mapping.
    spec
        Immutable labels, limits, scales, ticks, and padding.

    Returns
    -------
    None
        The supplied Axes objects are styled in place.

    Raises
    ------
    LayoutError
        If the target, specification, scale domain, or value is invalid.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, ax = gs.subplots()
    >>> gs.style_axes(ax, gs.AxisSpec(xlabel="time", ylabel="value"))
    >>> ax.get_xlabel()
    'time'
    >>> figure.clear()
    """

    if not isinstance(spec, AxisSpec):
        raise LayoutError("spec must be a gsplot AxisSpec")
    axes = axes_targets(target)
    for axis in axes:
        _validate_scale_domain(axis, spec)
    for axis in axes:
        _apply_axis_spec(axis, spec)


def _apply_axis_spec(axis: Axes, spec: AxisSpec) -> None:
    """Apply one already validated axis specification."""

    if spec.xlabel is not None or spec.xlabelpad is not None:
        axis.set_xlabel(
            spec.xlabel if spec.xlabel is not None else axis.get_xlabel(),
            labelpad=spec.xlabelpad,
        )
    if spec.ylabel is not None or spec.ylabelpad is not None:
        axis.set_ylabel(
            spec.ylabel if spec.ylabel is not None else axis.get_ylabel(),
            labelpad=spec.ylabelpad,
        )
    axis.set_xscale(spec.xscale)
    axis.set_yscale(spec.yscale)
    if spec.xlim is not None:
        axis.set_xlim(spec.xlim)
    if spec.ylim is not None:
        axis.set_ylim(spec.ylim)
    if spec.xticks is not None:
        axis.set_xticks(spec.xticks)
    if spec.yticks is not None:
        axis.set_yticks(spec.yticks)
    if spec.xminor is not None:
        _set_minor(axis, spec.xminor, "x")
    if spec.yminor is not None:
        _set_minor(axis, spec.yminor, "y")


def _set_minor(axis: Axes, enabled: bool, coordinate: Literal["x", "y"]) -> None:
    """Set one scale-aware minor locator without consulting pyplot."""

    selected = axis.xaxis if coordinate == "x" else axis.yaxis
    if enabled:
        selected.minorticks_on()
    else:
        selected.minorticks_off()


def _text(value: Any, name: str) -> str:
    """Validate a title or label string."""

    if not isinstance(value, str):
        raise PlotError(f"{name} must be a string")
    return value


def title(ax: Axes, text: str, *, props: Mapping[str, Any] | None = None) -> Text:
    """Set an explicit Axes title and return its native Text artist.

    Parameters
    ----------
    ax
        Explicit target Axes.
    text
        Title text.
    props
        Finite Matplotlib Text property mapping.

    Returns
    -------
    matplotlib.text.Text
        Native title artist attached to ``ax``.

    Raises
    ------
    PlotError
        If the target, text, or property mapping is invalid.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, ax = gs.subplots()
    >>> text = gs.title(ax, "Signal")
    >>> text.axes is ax
    True
    >>> figure.clear()
    """

    if not isinstance(ax, Axes):
        raise PlotError("ax must be a Matplotlib Axes")
    selected_props = _validate_props(props, _TITLE_PROPS, "title")
    return ax.set_title(_text(text, "text"), **selected_props)


def suptitle(fig: Figure, text: str, *, props: Mapping[str, Any] | None = None) -> Text:
    """Set an explicit Figure suptitle and return its native Text artist.

    Parameters
    ----------
    fig
        Explicit target Figure.
    text
        Suptitle text.
    props
        Finite Matplotlib Text property mapping.

    Returns
    -------
    matplotlib.text.Text
        Native suptitle artist attached to ``fig``.

    Raises
    ------
    PlotError
        If the Figure, text, or property mapping is invalid.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, _ = gs.subplots()
    >>> text = gs.suptitle(figure, "Experiment")
    >>> text.figure is figure
    True
    >>> figure.clear()
    """

    if not isinstance(fig, Figure):
        raise PlotError("fig must be a Matplotlib Figure")
    selected_props = _validate_props(props, _TITLE_PROPS, "suptitle")
    return fig.suptitle(_text(text, "text"), **selected_props)


def minor_ticks(
    target: AxesTarget,
    enabled: bool,
    *,
    axis: Literal["x", "y", "both"] = "both",
) -> None:
    """Enable or disable minor ticks on explicit Axes targets.

    Parameters
    ----------
    target
        One Axes, an ordered Axes sequence, or an Axes mapping.
    enabled
        Whether minor ticks should be visible.
    axis
        Coordinate axis to update: ``"x"``, ``"y"``, or ``"both"``.

    Returns
    -------
    None
        The supplied Axes objects are updated in place.

    Raises
    ------
    LayoutError
        If the target, enabled flag, or axis selector is invalid.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, ax = gs.subplots()
    >>> gs.minor_ticks(ax, True, axis="x")
    >>> figure.clear()
    """

    if not isinstance(enabled, bool):
        raise LayoutError("enabled must be a boolean")
    if axis not in {"x", "y", "both"}:
        raise LayoutError("axis must be 'x', 'y', or 'both'")
    axes = axes_targets(target)
    for item in axes:
        if axis in {"x", "both"}:
            _set_minor(item, enabled, "x")
        if axis in {"y", "both"}:
            _set_minor(item, enabled, "y")


def box_aspect(target: AxesTarget, aspect: float | None) -> None:
    """Set or clear an explicit Axes box aspect.

    Parameters
    ----------
    target
        One Axes, an ordered Axes sequence, or an Axes mapping.
    aspect
        Positive aspect ratio, or ``None`` to clear the constraint.

    Returns
    -------
    None
        The supplied Axes objects are updated in place.

    Raises
    ------
    LayoutError
        If the target or aspect is invalid.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, ax = gs.subplots()
    >>> gs.box_aspect(ax, 1.0)
    >>> figure.clear()
    """

    if aspect is not None:
        if isinstance(aspect, bool):
            raise LayoutError("aspect must be positive or None")
        try:
            value = float(aspect)
        except (TypeError, ValueError) as exc:
            raise LayoutError("aspect must be positive or None") from exc
        if not np.isfinite(value) or value <= 0:
            raise LayoutError("aspect must be positive or None")
        aspect = value
    axes = axes_targets(target)
    for item in axes:
        item.set_box_aspect(aspect)


def _parse_limit_and_scale(
    value: Any, default_scale: Scale, name: str
) -> tuple[tuple[float, float] | None, Scale]:
    """Parse a limit field which can be None, a scale string, a 2-tuple (min, max), or a 3-tuple (min, max, scale)."""

    if value is None or value is MISSING:
        return None, default_scale
    if isinstance(value, str):
        if value in _SCALES:
            return None, cast(Scale, value)
        if value == "*":
            return None, default_scale
        raise LayoutError(
            f"{name} string must be a scale: {', '.join(sorted(_SCALES))}"
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        items = tuple(value)
        if len(items) == 2:
            return _limits(items, name), default_scale
        if len(items) == 3:
            scale_val = items[2]
            if not isinstance(scale_val, str) or scale_val not in _SCALES:
                raise LayoutError(
                    f"{name} scale must be one of: {', '.join(sorted(_SCALES))}"
                )
            return _limits((items[0], items[1]), name), cast(Scale, scale_val)
        raise LayoutError(f"{name} must contain two limits or two limits with a scale")
    raise LayoutError(f"{name} must be a limit sequence or scale string")


def _record_spec(
    value: Any,
    *,
    name: str,
    xscale: Scale,
    yscale: Scale,
    xticks: TickSpec | None,
    yticks: TickSpec | None,
    xminor: bool,
    yminor: bool,
    xpad: float,
    ypad: float,
) -> AxisSpec:
    """Normalize one concise two- or four-field label record."""

    if isinstance(value, (str, bytes)):
        raise LayoutError(f"label: {name} must be a two- or four-field record")
    try:
        fields = tuple(value)
    except TypeError as exc:
        raise LayoutError(f"label: {name} must be a two- or four-field record") from exc
    if len(fields) not in {2, 4}:
        raise LayoutError(f"label: {name} must be a two- or four-field record")
    if not isinstance(fields[0], str) or not isinstance(fields[1], str):
        raise LayoutError(f"label: {name} labels must be strings")
    raw_xlim = None if len(fields) == 2 else fields[2]
    raw_ylim = None if len(fields) == 2 else fields[3]
    record_xlim, record_xscale = _parse_limit_and_scale(
        raw_xlim, xscale, f"label: {name} xlim"
    )
    record_ylim, record_yscale = _parse_limit_and_scale(
        raw_ylim, yscale, f"label: {name} ylim"
    )
    return AxisSpec(
        xlabel=fields[0],
        ylabel=fields[1],
        xlim=record_xlim,
        ylim=record_ylim,
        xscale=record_xscale,
        yscale=record_yscale,
        xticks=None if xticks is None else tuple(xticks),
        yticks=None if yticks is None else tuple(yticks),
        xminor=xminor,
        yminor=yminor,
        xlabelpad=xpad,
        ylabelpad=ypad,
    )


def _label_specs(
    target: TargetPlan,
    xlabel: Any,
    ylabel: Any,
    xlim: Any,
    ylim: Any,
    *,
    xscale: Any,
    yscale: Any,
    xticks: Any,
    yticks: Any,
    minor: Any,
    xminor: Any,
    yminor: Any,
    pad: Any,
    xpad: Any,
    ypad: Any,
) -> tuple[AxisSpec, ...]:
    """Resolve all concise label values before any Axes is changed."""

    selected_minor = ensure_bool(minor, "label: minor", error=LayoutError)
    selected_xminor = (
        selected_minor
        if xminor is None
        else ensure_bool(xminor, "label: xminor", error=LayoutError)
    )
    selected_yminor = (
        selected_minor
        if yminor is None
        else ensure_bool(yminor, "label: yminor", error=LayoutError)
    )
    selected_pad = ensure_finite_real(pad, "label: pad", error=LayoutError)
    selected_xpad = (
        selected_pad
        if xpad is None
        else ensure_finite_real(xpad, "label: xpad", error=LayoutError)
    )
    selected_ypad = (
        selected_pad
        if ypad is None
        else ensure_finite_real(ypad, "label: ypad", error=LayoutError)
    )

    common = {
        "xscale": xscale,
        "yscale": yscale,
        "xticks": xticks,
        "yticks": yticks,
        "xminor": selected_xminor,
        "yminor": selected_yminor,
        "xpad": selected_xpad,
        "ypad": selected_ypad,
    }
    if isinstance(xlabel, str):
        selected_ylabel = "" if ylabel is MISSING else ylabel
        if not isinstance(selected_ylabel, str):
            raise LayoutError("label: ylabel must be a string")
        direct_xlim, direct_xscale = _parse_limit_and_scale(xlim, xscale, "label: xlim")
        direct_ylim, direct_yscale = _parse_limit_and_scale(ylim, yscale, "label: ylim")
        spec = AxisSpec(
            xlabel=xlabel,
            ylabel=selected_ylabel,
            xlim=direct_xlim,
            ylim=direct_ylim,
            xscale=direct_xscale,
            yscale=direct_yscale,
            xticks=xticks,
            yticks=yticks,
            xminor=selected_xminor,
            yminor=selected_yminor,
            xlabelpad=selected_xpad,
            ylabelpad=selected_ypad,
        )
        return tuple(spec for _ in target.axes)

    if any(value is not MISSING for value in (ylabel, xlim, ylim)):
        raise LayoutError(
            "label: record input cannot be combined with ylabel, xlim, or ylim"
        )
    if isinstance(xlabel, Mapping):
        records = resolve_target_mapping(target, xlabel, name="xlabel records")
    elif isinstance(xlabel, Sequence) and not isinstance(xlabel, (str, bytes)):
        records = tuple(xlabel)
        if not records:
            raise LayoutError("label: label records must not be empty")
        if len(records) != len(target.axes):
            raise LayoutError("label: label records must match the target length")
    else:
        raise LayoutError(
            "label: xlabel must be a string or ordered/exact-key label records"
        )
    return tuple(
        _record_spec(record, name=f"record[{position}]", **common)
        for position, record in enumerate(records)
    )


@overload
def label(
    target: AxesTarget,
    xlabel: str = "",
    ylabel: str = "",
    xlim: Limit | None = None,
    ylim: Limit | None = None,
    *,
    xscale: Scale = "linear",
    yscale: Scale = "linear",
    xticks: TickSpec | None = None,
    yticks: TickSpec | None = None,
    minor: bool = True,
    xminor: bool | None = None,
    yminor: bool | None = None,
    pad: float = 5,
    xpad: float | None = None,
    ypad: float | None = None,
    square: bool = False,
    index: bool | Literal["in", "out"] = False,
) -> None: ...


@overload
def label(
    target: AxesTarget,
    xlabel: LabelRecords | Sequence[Any],
    *,
    xscale: Scale = "linear",
    yscale: Scale = "linear",
    xticks: TickSpec | None = None,
    yticks: TickSpec | None = None,
    minor: bool = True,
    xminor: bool | None = None,
    yminor: bool | None = None,
    pad: float = 5,
    xpad: float | None = None,
    ypad: float | None = None,
    square: bool = False,
    index: bool | Literal["in", "out"] = False,
) -> None: ...


def label(
    target: AxesTarget,
    xlabel: Any = "",
    ylabel: Any = MISSING,
    xlim: Any = MISSING,
    ylim: Any = MISSING,
    *,
    xscale: Any = "linear",
    yscale: Any = "linear",
    xticks: Any = None,
    yticks: Any = None,
    minor: Any = True,
    xminor: Any = None,
    yminor: Any = None,
    pad: Any = 5,
    xpad: Any = None,
    ypad: Any = None,
    square: Any = False,
    index: Any = False,
) -> None:
    """Set publication labels and optional panel geometry on explicit Axes.

    Parameters
    ----------
    target
        One Axes or a deterministic same-Figure collection of Axes.
    xlabel, ylabel
        Shared axis labels. ``xlabel`` may instead contain ordered or
        exact-key two- or four-field label records.
    xlim, ylim
        Optional finite, unequal limits; inverted limits are preserved.
    xscale, yscale
        Shared ``linear``, ``log``, ``symlog``, or ``logit`` scales.
    xticks, yticks
        Optional shared finite tick locations.
    minor, xminor, yminor
        Minor-tick controls. Coordinate-specific ``None`` inherits ``minor``.
    pad, xpad, ypad
        Label padding in points. Coordinate-specific ``None`` inherits ``pad``.
    square
        Apply the same unit box aspect as :func:`square` when true.
    index
        Add generated panel indexes outside, or at the selected ``in``/``out``
        location.

    Returns
    -------
    None
        The supplied Axes are changed in place.

    Raises
    ------
    LayoutError, PlotError
        If targets, records, domains, ticks, padding, or controls are invalid.

    Notes
    -----
    Every target and value is validated before mutation. The operation never
    executes a Figure layout engine, resizes a Figure, or inspects pyplot's
    current Figure.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, ax = gs.subplots()
    >>> gs.label(ax, "time", "signal", xlim=(0, 1), square=True)
    >>> ax.get_xlabel()
    'time'
    >>> figure.clear()
    """

    target_plan = normalize_axes(target, operation="label")
    try:
        specs = _label_specs(
            target_plan,
            xlabel,
            ylabel,
            xlim,
            ylim,
            xscale=xscale,
            yscale=yscale,
            xticks=xticks,
            yticks=yticks,
            minor=minor,
            xminor=xminor,
            yminor=yminor,
            pad=pad,
            xpad=xpad,
            ypad=ypad,
        )
    except LayoutError as exc:
        if str(exc).startswith("label:"):
            raise
        raise LayoutError(f"label: {exc}") from exc
    selected_square = ensure_bool(square, "label: square", error=LayoutError)
    if isinstance(index, bool):
        index_loc = "out" if index else None
    elif isinstance(index, str) and index in {"in", "out"}:
        index_loc = index
    else:
        raise LayoutError("label: index must be False, True, 'in', or 'out'")

    index_plan = None
    if index_loc is not None:
        from .panels import _prepare_index

        index_plan = _prepare_index(target_plan, None, loc=index_loc)
    for axis, spec in zip(target_plan.axes, specs):
        _validate_scale_domain(axis, spec)
    aspect = (
        ensure_positive(1, "label: aspect", error=LayoutError)
        if selected_square
        else None
    )

    for axis, spec in zip(target_plan.axes, specs):
        _apply_axis_spec(axis, spec)
    if aspect is not None:
        _apply_square(target_plan.axes, aspect)
    if index_plan is not None:
        from .panels import _apply_index

        _apply_index(target_plan, *index_plan)


def _apply_square(axes: Sequence[Axes], aspect: float) -> None:
    """Apply one validated positive box aspect."""

    for axis in axes:
        axis.set_box_aspect(aspect)


def square(target: AxesTarget, aspect: float = 1) -> None:
    """Apply a finite positive box aspect to explicit Axes.

    Parameters
    ----------
    target
        One Axes or a deterministic same-Figure collection of Axes.
    aspect
        Positive ratio of box height to box width. The default is ``1``.

    Returns
    -------
    None
        The supplied Axes are changed in place.

    Raises
    ------
    LayoutError, PlotError
        If the target is invalid or ``aspect`` is not finite and positive.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, ax = gs.subplots()
    >>> gs.square(ax)
    >>> ax.get_box_aspect()
    1.0
    >>> figure.clear()
    """

    target_plan = normalize_axes(target, operation="square")
    selected = ensure_positive(aspect, "square: aspect", error=LayoutError)
    _apply_square(target_plan.axes, selected)


def _label_signature(
    target: AxesTarget,
    xlabel: str | LabelRecords = "",
    ylabel: str = "",
    xlim: Limit | None = None,
    ylim: Limit | None = None,
    *,
    xscale: Scale = "linear",
    yscale: Scale = "linear",
    xticks: TickSpec | None = None,
    yticks: TickSpec | None = None,
    minor: bool = True,
    xminor: bool | None = None,
    yminor: bool | None = None,
    pad: float = 5,
    xpad: float | None = None,
    ypad: float | None = None,
    square: bool = False,
    index: bool | Literal["in", "out"] = False,
) -> None:
    raise AssertionError("signature-only function")


label.__signature__ = inspect.signature(_label_signature)  # type: ignore[attr-defined]
label.__annotations__ = get_type_hints(_label_signature)


__all__ = [
    "AxesTarget",
    "axes_targets",
    "style_axes",
    "title",
    "suptitle",
    "minor_ticks",
    "box_aspect",
    "label",
    "square",
]
