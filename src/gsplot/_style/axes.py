"""Explicit Axes labels, scales, limits, ticks, and text helpers."""

from __future__ import annotations

import inspect
import math
from collections.abc import Mapping, Sequence
from typing import Any, Literal, cast, get_type_hints, overload

import numpy as np
from matplotlib.axes import Axes
from matplotlib.axes._base import _AxesBase
from matplotlib.figure import Figure
from matplotlib.text import Text

from .._core.errors import LayoutError, OptionError, PlotError
from .._core.options import MISSING
from .._core.plans import TargetPlan
from .._core.targets import normalize_axes, resolve_target_mapping
from .._core.types import (
    _DIRECTIONS,
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


def axes_targets(target: AxesTarget) -> tuple[Axes | _AxesBase, ...]:
    """Validate and normalize an explicit Axes target collection."""

    return normalize_axes(target, operation="style").axes


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


def _validate_scale_domain(axis: Axes | _AxesBase, spec: AxisSpec) -> None:
    """Reject impossible log/logit domains before a target is mutated."""

    for coordinate, scale, limits, ticks in (
        ("x", spec.xscale, spec.xlim, spec.xticks),
        ("y", spec.yscale, spec.ylim, spec.yticks),
    ):
        if scale == "linear" or scale == "symlog":
            continue
        if limits is not None:
            domain_values: tuple[float, ...] = tuple(
                float(val) for val in limits if val is not None
            )
            if not domain_values and axis.has_data():
                bounds = (
                    axis.dataLim.intervalx
                    if coordinate == "x"
                    else axis.dataLim.intervaly
                )
                domain_values = tuple(float(item) for item in bounds)
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


def _get_axis_data_bounds(
    axis: Axes | _AxesBase, coordinate: Literal["x", "y"], scale: Scale
) -> tuple[float, float] | None:
    """Return effective data bounds (min, max) for one coordinate, or None if no data."""

    data_lim = getattr(axis, "dataLim", None)
    if data_lim is not None:
        interval = data_lim.intervalx if coordinate == "x" else data_lim.intervaly
        dmin, dmax = float(interval[0]), float(interval[1])
        if math.isfinite(dmin) and math.isfinite(dmax) and dmin <= dmax:
            if scale == "log":
                if dmin > 0:
                    return (dmin, dmax)
            else:
                return (dmin, dmax)
    return None


def _resolve_axis_limit(
    axis: Axes | _AxesBase,
    limit: tuple[float | None, float | None] | None,
    coordinate: Literal["x", "y"],
    scale: Scale,
    margin_ratio: float,
) -> tuple[float, float] | None:
    """Resolve a limit tuple with automatic smart margins for None endpoints."""

    if limit is None:
        return None

    raw_low, raw_high = limit
    if raw_low is not None and raw_high is not None:
        return (raw_low, raw_high)

    bounds = _get_axis_data_bounds(axis, coordinate, scale)
    if bounds is None:
        if raw_low is not None or raw_high is not None:
            dmin, dmax = (0.0, 1.0) if scale != "log" else (1.0, 10.0)
        else:
            return None
    else:
        dmin, dmax = bounds

    if scale == "log":
        log_dmin = math.log10(max(dmin, 1e-300))
        log_dmax = math.log10(max(dmax, 1e-300))
        if log_dmax < log_dmin:
            log_dmin, log_dmax = log_dmax, log_dmin

        if raw_low is not None and raw_high is None:
            log_low = math.log10(max(raw_low, 1e-300))
            if log_low < log_dmax:
                span = log_dmax - log_low
                if span <= 0:
                    span = (log_dmax - log_dmin) if (log_dmax > log_dmin) else 1.0
                log_high = log_dmax + span * margin_ratio
            else:
                span = log_low - log_dmin
                if span <= 0:
                    span = (log_dmax - log_dmin) if (log_dmax > log_dmin) else 1.0
                log_high = log_dmin - span * margin_ratio
            return (raw_low, 10.0**log_high)
        elif raw_low is None and raw_high is not None:
            log_high = math.log10(max(raw_high, 1e-300))
            if log_high > log_dmin:
                span = log_high - log_dmin
                if span <= 0:
                    span = (log_dmax - log_dmin) if (log_dmax > log_dmin) else 1.0
                log_low = log_dmin - span * margin_ratio
            else:
                span = log_dmax - log_high
                if span <= 0:
                    span = (log_dmax - log_dmin) if (log_dmax > log_dmin) else 1.0
                log_low = log_dmax + span * margin_ratio
            return (10.0**log_low, raw_high)
        else:
            span = log_dmax - log_dmin
            if span <= 0:
                span = 1.0
            log_low = log_dmin - span * margin_ratio
            log_high = log_dmax + span * margin_ratio
            return (10.0**log_low, 10.0**log_high)
    else:
        if raw_low is not None and raw_high is None:
            if raw_low < dmax:
                span = dmax - raw_low
                if span <= 0:
                    span = (
                        (dmax - dmin)
                        if (dmax > dmin)
                        else (abs(dmax) * 0.1 if dmax != 0 else 1.0)
                    )
                high = dmax + span * margin_ratio
            else:
                span = raw_low - dmin
                if span <= 0:
                    span = (
                        (dmax - dmin)
                        if (dmax > dmin)
                        else (abs(dmin) * 0.1 if dmin != 0 else 1.0)
                    )
                high = dmin - span * margin_ratio
            return (raw_low, high)
        elif raw_low is None and raw_high is not None:
            if raw_high > dmin:
                span = raw_high - dmin
                if span <= 0:
                    span = (
                        (dmax - dmin)
                        if (dmax > dmin)
                        else (abs(dmin) * 0.1 if dmin != 0 else 1.0)
                    )
                low = dmin - span * margin_ratio
            else:
                span = dmax - raw_high
                if span <= 0:
                    span = (
                        (dmax - dmin)
                        if (dmax > dmin)
                        else (abs(dmax) * 0.1 if dmax != 0 else 1.0)
                    )
                low = dmax + span * margin_ratio
            return (low, raw_high)
        else:
            span = dmax - dmin
            if span <= 0:
                span = abs(dmax) * 0.1 if dmax != 0 else 1.0
            low = dmin - span * margin_ratio
            high = dmax + span * margin_ratio
            return (low, high)


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
    target_plan = normalize_axes(target, operation="style_axes")
    for axis in target_plan.axes:
        _validate_scale_domain(axis, spec)
    for axis in target_plan.axes:
        _apply_axis_spec(axis, spec)


def _apply_axis_spec(axis: Axes | _AxesBase, spec: AxisSpec) -> None:
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
        resolved_xlim = _resolve_axis_limit(
            axis, spec.xlim, "x", spec.xscale, spec.xmargin
        )
        if resolved_xlim is not None:
            axis.set_xlim(resolved_xlim)
    elif getattr(axis, "has_data", lambda: False)():
        resolved_xlim = _resolve_axis_limit(
            axis, (None, None), "x", spec.xscale, spec.xmargin
        )
        if resolved_xlim is not None:
            axis.set_xlim(resolved_xlim)

    if spec.ylim is not None:
        resolved_ylim = _resolve_axis_limit(
            axis, spec.ylim, "y", spec.yscale, spec.ymargin
        )
        if resolved_ylim is not None:
            axis.set_ylim(resolved_ylim)
    elif getattr(axis, "has_data", lambda: False)():
        resolved_ylim = _resolve_axis_limit(
            axis, (None, None), "y", spec.yscale, spec.ymargin
        )
        if resolved_ylim is not None:
            axis.set_ylim(resolved_ylim)
    if spec.xticks is not None:
        axis.set_xticks(spec.xticks)
    if spec.yticks is not None:
        axis.set_yticks(spec.yticks)
    if spec.xminor is not None:
        _set_minor(axis, spec.xminor, "x")
    if spec.yminor is not None:
        _set_minor(axis, spec.yminor, "y")
    if (
        spec.top is not None
        or spec.bottom is not None
        or spec.left is not None
        or spec.right is not None
        or spec.direction is not None
    ):
        _apply_tick_controls(
            axis,
            top=spec.top,
            bottom=spec.bottom,
            left=spec.left,
            right=spec.right,
            direction=spec.direction,
        )


def _apply_tick_controls(
    axis_obj: Axes | _AxesBase,
    *,
    axis: Literal["x", "y", "both"] = "both",
    which: Literal["both", "major", "minor"] = "both",
    top: bool | None = None,
    bottom: bool | None = None,
    left: bool | None = None,
    right: bool | None = None,
    direction: Literal["in", "out", "inout"] | None = None,
    **kwargs: Any,
) -> None:
    """Apply tick visibility, direction, and parameters to an Axes."""

    params: dict[str, Any] = {}
    if top is not None:
        params["top"] = top
        params["labeltop"] = top
    if bottom is not None:
        params["bottom"] = bottom
        params["labelbottom"] = bottom
    if left is not None:
        params["left"] = left
        params["labelleft"] = left
    if right is not None:
        params["right"] = right
        params["labelright"] = right
    if direction is not None:
        params["direction"] = direction
    params.update(kwargs)
    if params:
        axis_obj.tick_params(axis=axis, which=which, **params)


def _set_minor(
    axis: Axes | _AxesBase, enabled: bool, coordinate: Literal["x", "y"]
) -> None:
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


def _merge_props(
    props: Mapping[str, Any] | None,
    kwargs: Mapping[str, Any],
    name: str,
) -> dict[str, Any]:
    """Merge an explicit props mapping and direct keyword arguments."""

    if props is not None and not isinstance(props, Mapping):
        raise PlotError(f"{name} props must be a mapping")
    merged = dict(props or {})
    merged.update(kwargs)
    return merged


def title(
    ax: Axes | _AxesBase,
    text: str,
    *,
    props: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> Text:
    """Set an explicit Axes title and return its native Text artist.

    Parameters
    ----------
    ax
        Explicit target Axes.
    text
        Title text.
    props
        Optional finite Matplotlib Text property mapping.
    **kwargs
        Optional direct Matplotlib Text properties (e.g. ``fontsize``,
        ``color``, ``loc``, ``pad``). Direct keyword arguments are merged with
        and take precedence over ``props``.

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

    if not isinstance(ax, (Axes, _AxesBase)):
        raise PlotError("ax must be a Matplotlib Axes")
    merged_props = _merge_props(props, kwargs, "title")
    selected_props = _validate_props(merged_props, _TITLE_PROPS, "title")
    return cast(Text, cast(Any, ax).set_title(_text(text, "text"), **selected_props))


def suptitle(
    fig: Figure,
    text: str,
    *,
    props: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> Text:
    """Set an explicit Figure suptitle and return its native Text artist.

    Parameters
    ----------
    fig
        Explicit target Figure.
    text
        Suptitle text.
    props
        Optional finite Matplotlib Text property mapping.
    **kwargs
        Optional direct Matplotlib Text properties (e.g. ``fontsize``,
        ``color``, ``y``, ``va``). Direct keyword arguments are merged with and
        take precedence over ``props``.

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
    merged_props = _merge_props(props, kwargs, "suptitle")
    selected_props = _validate_props(merged_props, _TITLE_PROPS, "suptitle")
    return fig.suptitle(_text(text, "text"), **selected_props)


def minor_ticks(
    target: AxesTarget,
    enabled: bool,
    *,
    axis: Literal["x", "y", "both"] = "both",
    top: bool | None = None,
    bottom: bool | None = None,
    left: bool | None = None,
    right: bool | None = None,
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
    top, bottom, left, right
        Optional boolean flags for minor tick visibility on each edge.

    Returns
    -------
    None
        The supplied Axes objects are updated in place.

    Raises
    ------
    LayoutError
        If the target, enabled flag, axis selector, or edge options are invalid.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, ax = gs.subplots()
    >>> gs.minor_ticks(ax, True, axis="x", right=False)
    >>> figure.clear()
    """

    if not isinstance(enabled, bool):
        raise LayoutError("enabled must be a boolean")
    if axis not in {"x", "y", "both"}:
        raise LayoutError("axis must be 'x', 'y', or 'both'")
    for edge_name, edge_val in (
        ("top", top),
        ("bottom", bottom),
        ("left", left),
        ("right", right),
    ):
        if edge_val is not None and not isinstance(edge_val, bool):
            raise LayoutError(f"{edge_name} must be a boolean or None")

    target_plan = normalize_axes(target, operation="minor_ticks")
    for item in target_plan.axes:
        if axis in {"x", "both"}:
            _set_minor(item, enabled, "x")
        if axis in {"y", "both"}:
            _set_minor(item, enabled, "y")
        if (
            top is not None
            or bottom is not None
            or left is not None
            or right is not None
        ):
            _apply_tick_controls(
                item,
                axis=axis,
                which="minor",
                top=top,
                bottom=bottom,
                left=left,
                right=right,
            )


def ticks(
    target: AxesTarget,
    *,
    minor: bool | None = None,
    axis: Literal["x", "y", "both"] = "both",
    top: bool | None = None,
    bottom: bool | None = None,
    left: bool | None = None,
    right: bool | None = None,
    direction: Literal["in", "out", "inout"] | None = None,
    which: Literal["both", "major", "minor"] = "both",
    **kwargs: Any,
) -> None:
    """Configure tick visibility, minor ticks, direction, and parameters.

    Parameters
    ----------
    target
        One Axes, an ordered Axes sequence, or an Axes mapping.
    minor
        Optional flag to turn minor ticks on (``True``) or off (``False``).
    axis
        Coordinate axis to configure: ``"x"``, ``"y"``, or ``"both"``.
    top, bottom, left, right
        Optional booleans controlling tick (and tick label) visibility on each edge.
    direction
        Tick direction: ``"in"``, ``"out"``, or ``"inout"``.
    which
        Which ticks to style: ``"both"``, ``"major"``, or ``"minor"``.
    **kwargs
        Additional Matplotlib tick properties passed to ``tick_params`` (e.g.
        ``length``, ``width``, ``color``, ``pad``).

    Returns
    -------
    None
        The supplied Axes objects are updated in place.

    Raises
    ------
    LayoutError
        If target or options are invalid.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, ax = gs.subplots()
    >>> gs.ticks(ax, minor=True, right=False, direction="in")
    >>> figure.clear()
    """

    if axis not in {"x", "y", "both"}:
        raise LayoutError("axis must be 'x', 'y', or 'both'")
    if which not in {"both", "major", "minor"}:
        raise LayoutError("which must be 'both', 'major', or 'minor'")
    for edge_name, edge_val in (
        ("top", top),
        ("bottom", bottom),
        ("left", left),
        ("right", right),
    ):
        if edge_val is not None and not isinstance(edge_val, bool):
            raise LayoutError(f"{edge_name} must be a boolean or None")
    if direction is not None and (
        not isinstance(direction, str) or direction not in _DIRECTIONS
    ):
        raise LayoutError(f"direction must be one of: {', '.join(sorted(_DIRECTIONS))}")
    if minor is not None and not isinstance(minor, bool):
        raise LayoutError("minor must be a boolean or None")

    target_plan = normalize_axes(target, operation="ticks")
    for item in target_plan.axes:
        if minor is not None:
            if axis in {"x", "both"}:
                _set_minor(item, minor, "x")
            if axis in {"y", "both"}:
                _set_minor(item, minor, "y")
        _apply_tick_controls(
            item,
            axis=axis,
            which=which,
            top=top,
            bottom=bottom,
            left=left,
            right=right,
            direction=direction,
            **kwargs,
        )


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
    target_plan = normalize_axes(target, operation="box_aspect")
    for item in target_plan.axes:
        item.set_box_aspect(aspect)


def _parse_limit_and_scale(
    value: Any, default_scale: Scale, name: str
) -> tuple[tuple[float | None, float | None] | None, Scale]:
    """Parse a limit field which can be None, a scale string, a 2-tuple (min, max), or a 3-tuple (min, max, scale)."""

    if value is None or value is MISSING:
        return None, default_scale
    if isinstance(value, str):
        if value in _SCALES:
            return None, cast(Scale, value)
        if value in ("", "*"):
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


def _resolve_margins(margin: Any, xmargin: Any, ymargin: Any) -> tuple[float, float]:
    """Validate and resolve effective (xmargin, ymargin) ratios."""

    def _validate_single(val: Any, name: str) -> float:
        if isinstance(val, bool):
            raise LayoutError(f"label: {name} must be a non-negative number")
        try:
            num = float(val)
        except (TypeError, ValueError) as exc:
            raise LayoutError(f"label: {name} must be a non-negative number") from exc
        if not math.isfinite(num) or num < 0:
            raise LayoutError(f"label: {name} must be a non-negative number")
        return num

    default_margin = 0.05

    if margin is None:
        base_x = default_margin
        base_y = default_margin
    elif isinstance(margin, Sequence) and not isinstance(margin, (str, bytes)):
        items = tuple(margin)
        if len(items) != 2:
            raise LayoutError(
                "label: margin tuple must contain exactly two values (xmargin, ymargin)"
            )
        base_x = _validate_single(items[0], "margin[0]")
        base_y = _validate_single(items[1], "margin[1]")
    else:
        single = _validate_single(margin, "margin")
        base_x = single
        base_y = single

    eff_x = _validate_single(xmargin, "xmargin") if xmargin is not None else base_x
    eff_y = _validate_single(ymargin, "ymargin") if ymargin is not None else base_y

    return eff_x, eff_y


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
    xmargin: float,
    ymargin: float,
    top: bool | None = None,
    bottom: bool | None = None,
    left: bool | None = None,
    right: bool | None = None,
    direction: Literal["in", "out", "inout"] | None = None,
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
        xmargin=xmargin,
        ymargin=ymargin,
        top=top,
        bottom=bottom,
        left=left,
        right=right,
        direction=direction,
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
    margin: Any = None,
    xmargin: Any = None,
    ymargin: Any = None,
    top: Any = None,
    bottom: Any = None,
    left: Any = None,
    right: Any = None,
    direction: Any = None,
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
    eff_xmargin, eff_ymargin = _resolve_margins(margin, xmargin, ymargin)

    for edge_name, edge_val in (
        ("top", top),
        ("bottom", bottom),
        ("left", left),
        ("right", right),
    ):
        if edge_val is not None and not isinstance(edge_val, bool):
            raise LayoutError(f"label: {edge_name} must be a boolean or None")
    selected_direction: Literal["in", "out", "inout"] | None = None
    if direction is not None:
        if not isinstance(direction, str) or direction not in _DIRECTIONS:
            raise LayoutError(
                f"label: direction must be one of: {', '.join(sorted(_DIRECTIONS))}"
            )
        selected_direction = cast(Literal["in", "out", "inout"], direction)

    common = {
        "xscale": xscale,
        "yscale": yscale,
        "xticks": xticks,
        "yticks": yticks,
        "xminor": selected_xminor,
        "yminor": selected_yminor,
        "xpad": selected_xpad,
        "ypad": selected_ypad,
        "xmargin": eff_xmargin,
        "ymargin": eff_ymargin,
        "top": top,
        "bottom": bottom,
        "left": left,
        "right": right,
        "direction": selected_direction,
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
            xmargin=eff_xmargin,
            ymargin=eff_ymargin,
            top=top,
            bottom=bottom,
            left=left,
            right=right,
            direction=selected_direction,
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
    margin: float | tuple[float, float] | None = None,
    xmargin: float | None = None,
    ymargin: float | None = None,
    top: bool | None = None,
    bottom: bool | None = None,
    left: bool | None = None,
    right: bool | None = None,
    direction: Literal["in", "out", "inout"] | None = None,
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
    margin: float | tuple[float, float] | None = None,
    xmargin: float | None = None,
    ymargin: float | None = None,
    top: bool | None = None,
    bottom: bool | None = None,
    left: bool | None = None,
    right: bool | None = None,
    direction: Literal["in", "out", "inout"] | None = None,
    square: bool = False,
    index: bool | Literal["in", "out"] = False,
    index_offset: tuple[float, float] | float | None = None,
    index_xoffset: float | None = None,
    index_yoffset: float | None = None,
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
    margin: Any = None,
    xmargin: Any = None,
    ymargin: Any = None,
    top: Any = None,
    bottom: Any = None,
    left: Any = None,
    right: Any = None,
    direction: Any = None,
    square: Any = False,
    index: Any = False,
    index_offset: Any = None,
    index_xoffset: Any = None,
    index_yoffset: Any = None,
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
        Endpoints set to ``None`` or wildcard placeholders use automatic
        smart margins.
    xscale, yscale
        Shared ``linear``, ``log``, ``symlog``, or ``logit`` scales.
    xticks, yticks
        Optional shared finite tick locations.
    minor, xminor, yminor
        Minor-tick controls. Coordinate-specific ``None`` inherits ``minor``.
    pad, xpad, ypad
        Label padding in points. Coordinate-specific ``None`` inherits ``pad``.
    margin, xmargin, ymargin
        Margin ratios for auto-determined limits (defaults to ``0.05`` / 5%).
        Coordinate-specific ``None`` inherits ``margin``.
    top, bottom, left, right
        Optional boolean flags for edge tick and label visibility.
    direction
        Optional tick direction: ``"in"``, ``"out"``, or ``"inout"``.
    square
        Apply the same unit box aspect as :func:`square` when true.
    index
        Add generated panel indexes outside, or at the selected ``in``/``out``
        location.
    index_offset
        Optional point shift relative to baseline panel index placement.
        Accepts a scalar for equal shift in x/y or a 2-tuple ``(dx, dy)`` in points.
    index_xoffset
        Optional direct point shift along the x-axis for panel indexes.
    index_yoffset
        Optional direct point shift along the y-axis for panel indexes.

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
    >>> gs.line(ax, [0, 1], [0, 1])
    [<matplotlib.lines.Line2D object ...>]
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
            margin=margin,
            xmargin=xmargin,
            ymargin=ymargin,
            top=top,
            bottom=bottom,
            left=left,
            right=right,
            direction=direction,
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

        index_plan = _prepare_index(
            target_plan,
            None,
            loc=index_loc,
            offset=index_offset,
            xoffset=index_xoffset,
            yoffset=index_yoffset,
        )
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


def _apply_square(axes: Sequence[Axes | _AxesBase], aspect: float) -> None:
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
    margin: float | tuple[float, float] | None = None,
    xmargin: float | None = None,
    ymargin: float | None = None,
    top: bool | None = None,
    bottom: bool | None = None,
    left: bool | None = None,
    right: bool | None = None,
    direction: Literal["in", "out", "inout"] | None = None,
    square: bool = False,
    index: bool | Literal["in", "out"] = False,
    index_offset: tuple[float, float] | float | None = None,
    index_xoffset: float | None = None,
    index_yoffset: float | None = None,
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
    "ticks",
    "box_aspect",
    "label",
    "square",
]
