"""Canonical explicit-Axes line and scatter adapters."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
from numpy.typing import ArrayLike

from .._config.model import Config
from .._core.errors import PlotError
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
        raise PlotError(f"{context} props contains unknown key(s): {joined}")
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
    """

    target = validate_axes(ax)
    x_values, y_values = validate_xy(x, y)
    selected_props = validate_props(props, _LINE_PROPS, "line")
    _resolve_config_color(config, selected_props)
    return list(target.plot(x_values, y_values, **selected_props))


def scatter(
    ax: Axes,
    x: ArrayLike,
    y: ArrayLike,
    *,
    props: Mapping[str, Any] | None = None,
    config: Config | None = None,
) -> PathCollection:
    """Create a native ``PathCollection`` on an explicit Axes."""

    target = validate_axes(ax)
    x_values, y_values = validate_xy(x, y)
    selected_props = validate_props(props, _SCATTER_PROPS, "scatter")
    _resolve_config_color(config, selected_props)
    return target.scatter(x_values, y_values, **selected_props)


__all__ = ["line", "scatter", "validate_axes", "validate_props"]
