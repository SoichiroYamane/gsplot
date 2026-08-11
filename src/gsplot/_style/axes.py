"""Explicit Axes labels, scales, limits, ticks, and text helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Literal

import matplotlib.ticker as ticker
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.text import Text

from .._core.errors import LayoutError, PlotError
from .._core.types import AxisSpec

AxesTarget = Axes | Sequence[Axes] | Mapping[str, Axes]

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
        raise PlotError(f"{name} props contains unknown key(s): {joined}")
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
    """Set one minor locator without consulting pyplot."""

    locator = ticker.AutoMinorLocator() if enabled else ticker.NullLocator()
    if coordinate == "x":
        axis.xaxis.set_minor_locator(locator)
    else:
        axis.yaxis.set_minor_locator(locator)


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

    axes = axes_targets(ax)
    selected_props = _validate_props(props, _TITLE_PROPS, "title")
    return axes[0].set_title(_text(text, "text"), **selected_props)


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


__all__ = [
    "AxesTarget",
    "axes_targets",
    "style_axes",
    "title",
    "suptitle",
    "minor_ticks",
    "box_aspect",
]
