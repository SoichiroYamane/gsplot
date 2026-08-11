"""Canonical explicit-Axes line and scatter adapters."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from numpy.typing import ArrayLike

from .._config.model import Config
from .._core.errors import OptionError, PlotError
from .._core.numerics import validate_xy

_LINE_PROPS = frozenset(
    {
        "alpha",
        "antialiased",
        "color",
        "dash_capstyle",
        "dash_joinstyle",
        "drawstyle",
        "fillstyle",
        "gapcolor",
        "label",
        "linestyle",
        "linewidth",
        "marker",
        "markeredgecolor",
        "markeredgewidth",
        "markerfacecolor",
        "markerfacecoloralt",
        "markersize",
        "markevery",
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
        "vmax",
        "vmin",
        "visible",
        "zorder",
    }
)

# Characterized 0.x visual defaults retained by the canonical operations.
# Colors still come from the target Axes property cycle; these values do not
# introduce a gsplot-owned counter or any other process-wide state.
_LINE_DEFAULTS: dict[str, Any] = {
    "marker": "o",
    "markersize": 7.0,
    "markeredgewidth": 1.5,
    "linestyle": "--",
    "linewidth": 1.0,
    "alpha": 1.0,
}
_SCATTER_DEFAULTS: dict[str, Any] = {"s": 1.0, "alpha": 1.0}


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


def _resolve_config_color(config: Config | None, props: dict[str, Any]) -> None:
    """Apply an explicit Config color only when props did not provide one."""

    if config is None:
        return
    if not isinstance(config, Config):
        raise PlotError("config must be a gsplot Config")
    if config.plotting.default_color != "axes" and not any(
        key in props for key in ("color", "c", "facecolors")
    ):
        props["color"] = config.plotting.default_color


def line(
    ax: Axes,
    x: ArrayLike,
    y: ArrayLike,
    *,
    props: Mapping[str, Any] | None = None,
    config: Config | None = None,
) -> list[Line2D]:
    """Plot finite one-dimensional data on an explicit Axes.

    ``props`` is a closed mapping of supported Matplotlib ``Line2D``
    properties.  The function returns the native list produced by
    :meth:`matplotlib.axes.Axes.plot` and never consults a current Axes or a
    process-wide color counter.

    Parameters
    ----------
    ax
        Explicit Matplotlib target Axes.
    x, y
        Equal-length finite one-dimensional data.
    props
        Optional finite mapping of supported ``Line2D`` properties.
    config
        Optional immutable configuration for omitted gsplot defaults.

    Returns
    -------
    list[matplotlib.lines.Line2D]
        Native line artists returned by Matplotlib.

    Raises
    ------
    DataError, PlotError
        If the data, target, configuration, or property mapping is invalid.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, ax = gs.subplots()
    >>> artists = gs.line(ax, [0, 1], [1, 2], props={"color": "navy"})
    >>> artists[0].axes is ax
    True
    >>> figure.clear()
    """

    target = validate_axes(ax)
    x_values, y_values = validate_xy(x, y)
    selected_props = validate_props(props, _LINE_PROPS, "line")
    for name, default in _LINE_DEFAULTS.items():
        selected_props.setdefault(name, default)
    _resolve_config_color(config, selected_props)
    artists = list(target.plot(x_values, y_values, **selected_props))
    if "markerfacecolor" not in selected_props:
        alpha = float(selected_props["alpha"])
        for artist in artists:
            red, green, blue, _ = to_rgba(artist.get_color())
            artist.set_markerfacecolor((red, green, blue, 0.2 * alpha))
    return artists


def scatter(
    ax: Axes,
    x: ArrayLike,
    y: ArrayLike,
    *,
    props: Mapping[str, Any] | None = None,
    config: Config | None = None,
) -> PathCollection:
    """Create a native ``PathCollection`` on an explicit Axes.

    Parameters
    ----------
    ax
        Explicit Matplotlib target Axes.
    x, y
        Equal-length finite one-dimensional data.
    props
        Optional finite mapping of supported scatter properties.
    config
        Optional immutable configuration for omitted gsplot defaults.

    Returns
    -------
    matplotlib.collections.PathCollection
        The native scatter collection attached to ``ax``.

    Raises
    ------
    DataError, PlotError
        If the data, target, configuration, or property mapping is invalid.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, ax = gs.subplots()
    >>> collection = gs.scatter(ax, [0, 1], [1, 2])
    >>> collection.axes is ax
    True
    >>> figure.clear()
    """

    target = validate_axes(ax)
    x_values, y_values = validate_xy(x, y)
    selected_props = validate_props(props, _SCATTER_PROPS, "scatter")
    color_controls = tuple(
        name for name in ("color", "c", "facecolors") if name in selected_props
    )
    if len(color_controls) > 1:
        raise OptionError(
            "scatter props cannot combine color controls: " + ", ".join(color_controls)
        )
    for name, default in _SCATTER_DEFAULTS.items():
        selected_props.setdefault(name, default)
    _resolve_config_color(config, selected_props)
    return target.scatter(x_values, y_values, **selected_props)


__all__ = ["line", "scatter", "validate_axes", "validate_props"]
