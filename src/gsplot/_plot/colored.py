"""Canonical scalar-to-color plotting adapters."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection, PathCollection
from matplotlib.colors import Normalize
from numpy.typing import ArrayLike

from .._config.model import Config
from .._core.errors import DataError, PlotError
from .._core.numerics import validate_color_values, validate_xy
from .._core.types import NormalizeSpec
from .basic import validate_axes, validate_props
from .colormap import cmap_from_config, map_values

_COLLECTION_PROPS = frozenset(
    {
        "alpha",
        "antialiaseds",
        "capstyle",
        "clip_on",
        "joinstyle",
        "label",
        "linestyles",
        "linewidths",
        "picker",
        "rasterized",
        "snap",
        "visible",
        "zorder",
    }
)
_DASH_PROPS = _COLLECTION_PROPS
_COLORED_SCATTER_PROPS = frozenset(
    {
        "alpha",
        "antialiaseds",
        "edgecolors",
        "facecolors",
        "label",
        "linewidths",
        "marker",
        "picker",
        "plotnonfinite",
        "rasterized",
        "s",
        "visible",
        "zorder",
    }
)


def _validate_cmap_args(
    cmap: str | None,
    norm: NormalizeSpec | tuple[float, float] | None,
    config: Config | None,
) -> tuple[str, NormalizeSpec | tuple[float, float] | None]:
    """Validate explicit color configuration before an Axes is touched."""

    if cmap is not None and (not isinstance(cmap, str) or not cmap.strip()):
        raise PlotError("cmap must be a non-empty colormap name")
    selected_cmap = cmap_from_config(config) if cmap is None else cmap
    if norm is not None and not callable(norm):
        if isinstance(norm, (str, bytes)):
            raise PlotError("norm must be a normalizer or a finite pair")
        try:
            bounds = tuple(norm)
        except TypeError as exc:
            raise PlotError("norm must be a normalizer or a finite pair") from exc
        if len(bounds) != 2:
            raise PlotError("norm must be a normalizer or a finite pair")
    return selected_cmap, norm


def _segment_data(
    x: ArrayLike,
    y: ArrayLike,
    values: ArrayLike,
) -> tuple[np.ndarray, np.ndarray]:
    """Validate point values and return non-zero segments with midpoint data."""

    x_values, y_values = validate_xy(x, y, colored=True)
    color_values = validate_color_values(values)
    if color_values.shape != x_values.shape:
        raise DataError("values must have the same one-dimensional shape as x and y")
    points = np.column_stack((x_values, y_values))
    segments = np.stack((points[:-1], points[1:]), axis=1)
    lengths = np.linalg.norm(segments[:, 1] - segments[:, 0], axis=1)
    nonzero = lengths > 0
    if not np.any(nonzero):
        raise DataError("colored line requires at least one non-zero-length segment")
    midpoint_values = (color_values[:-1] + color_values[1:]) / 2.0
    return segments[nonzero], midpoint_values[nonzero]


def _collection_props(
    props: Mapping[str, Any] | None,
    context: str,
) -> dict[str, Any]:
    """Reject duplicate color controls and copy collection properties."""

    selected = validate_props(props, _COLLECTION_PROPS, context)
    return selected


def cmap_line(
    ax: Axes,
    x: ArrayLike,
    y: ArrayLike,
    values: ArrayLike,
    *,
    cmap: str | None = None,
    norm: NormalizeSpec | tuple[float, float] | None = None,
    props: Mapping[str, Any] | None = None,
    config: Config | None = None,
) -> LineCollection:
    """Draw a finite polyline whose segments are mapped through a colormap."""

    target = validate_axes(ax)
    segments, segment_values = _segment_data(x, y, values)
    selected_cmap, selected_norm = _validate_cmap_args(cmap, norm, config)
    selected_props = _collection_props(props, "cmap_line")
    colors = map_values(segment_values, cmap=selected_cmap, norm=selected_norm)
    collection = LineCollection(
        cast(Any, segments.tolist()), colors=colors, **selected_props
    )
    target.add_collection(collection)
    target.autoscale_view()
    return collection


def cmap_dash(
    ax: Axes,
    x: ArrayLike,
    y: ArrayLike,
    values: ArrayLike,
    *,
    dash: tuple[float, float] = (5.0, 5.0),
    cmap: str | None = None,
    norm: NormalizeSpec | tuple[float, float] | None = None,
    props: Mapping[str, Any] | None = None,
    config: Config | None = None,
) -> tuple[LineCollection, ...]:
    """Draw a colormapped line with a local Matplotlib dash pattern.

    The returned tuple contains the one native collection owned by this
    operation.  Keeping the collection whole lets Matplotlib apply dash
    lengths in display points while preserving one scalar color per segment.
    """

    target = validate_axes(ax)
    if isinstance(dash, (str, bytes)):
        raise PlotError("dash must contain two positive finite values")
    try:
        dash_values = tuple(dash)
    except TypeError as exc:
        raise PlotError("dash must contain two positive finite values") from exc
    if len(dash_values) != 2:
        raise PlotError("dash must contain two positive finite values")
    try:
        on, off = (float(dash_values[0]), float(dash_values[1]))
    except (TypeError, ValueError) as exc:
        raise PlotError("dash must contain two positive finite values") from exc
    if not np.isfinite(on) or not np.isfinite(off) or on <= 0 or off <= 0:
        raise PlotError("dash must contain two positive finite values")
    segments, segment_values = _segment_data(x, y, values)
    selected_cmap, selected_norm = _validate_cmap_args(cmap, norm, config)
    selected_props = _collection_props(props, "cmap_dash")
    if "linestyles" in selected_props:
        raise PlotError("cmap_dash props cannot override the dash pattern")
    colors = map_values(segment_values, cmap=selected_cmap, norm=selected_norm)
    selected_props["linestyles"] = (0.0, (on, off))
    collection = LineCollection(
        cast(Any, segments.tolist()), colors=colors, **selected_props
    )
    target.add_collection(collection)
    target.autoscale_view()
    return (collection,)


def cmap_scatter(
    ax: Axes,
    x: ArrayLike,
    y: ArrayLike,
    values: ArrayLike,
    *,
    cmap: str | None = None,
    norm: NormalizeSpec | tuple[float, float] | None = None,
    props: Mapping[str, Any] | None = None,
    config: Config | None = None,
) -> PathCollection:
    """Create a scalar-colored native scatter collection."""

    target = validate_axes(ax)
    x_values, y_values = validate_xy(x, y, colored=True)
    color_values = validate_color_values(values)
    if color_values.shape != x_values.shape:
        raise DataError("values must have the same one-dimensional shape as x and y")
    selected_cmap, selected_norm = _validate_cmap_args(cmap, norm, config)
    selected_props = validate_props(props, _COLORED_SCATTER_PROPS, "cmap_scatter")
    colors = map_values(color_values, cmap=selected_cmap, norm=selected_norm)
    return target.scatter(x_values, y_values, color=colors, **selected_props)


__all__ = ["cmap_line", "cmap_dash", "cmap_scatter"]
