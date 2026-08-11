"""Local, explicit Matplotlib legend construction."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

import matplotlib as mpl
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import Colormap, Normalize
from matplotlib.figure import Figure
from matplotlib.legend import Legend
from matplotlib.lines import Line2D

from .._core.errors import LayoutError, PlotError
from .._core.types import LegendEntries, NormalizeSpec
from .axes import AxesTarget, axes_targets

_LEGEND_PROPS = frozenset(
    {
        "alignment",
        "borderaxespad",
        "borderpad",
        "columnspacing",
        "facecolor",
        "edgecolor",
        "fancybox",
        "framealpha",
        "handleheight",
        "handlelength",
        "handletextpad",
        "labelcolor",
        "labelspacing",
        "loc",
        "markerscale",
        "mode",
        "ncols",
        "ncol",
        "prop",
        "shadow",
        "title",
        "title_fontproperties",
        "title_fontsize",
    }
)


def _props(props: Mapping[str, Any] | None, context: str) -> dict[str, Any]:
    """Validate and copy legend constructor properties."""

    if props is None:
        return {}
    if not isinstance(props, Mapping):
        raise PlotError(f"{context} props must be a mapping")
    if any(not isinstance(key, str) for key in props):
        raise PlotError(f"{context} props keys must be strings")
    unknown = sorted(set(props) - _LEGEND_PROPS)
    if unknown:
        joined = ", ".join(repr(key) for key in unknown)
        raise PlotError(f"{context} props contains unknown key(s): {joined}")
    return dict(props)


def _existing(ax: Axes) -> tuple[Legend, ...]:
    """Return legends attached to one Axes without creating anything."""

    found: list[Legend] = []
    for child in ax.get_children():
        if isinstance(child, Legend) and child not in found:
            found.append(child)
    current = ax.get_legend()
    if isinstance(current, Legend) and current not in found:
        found.append(current)
    return tuple(found)


def _entries(
    ax: Axes,
    handles: Sequence[Any] | None,
    labels: Sequence[str] | None,
) -> tuple[tuple[Any, ...], tuple[str, ...]]:
    """Validate explicit or automatically discovered legend entries."""

    if (handles is None) != (labels is None):
        raise TypeError("handles and labels must be supplied together")
    selected_handles: tuple[Any, ...]
    selected_labels: tuple[str, ...]
    if handles is None:
        discovered_handles, discovered_labels = ax.get_legend_handles_labels()
        selected_handles = tuple(discovered_handles)
        selected_labels = tuple(discovered_labels)
    else:
        selected_handles = tuple(handles)
        selected_labels = tuple(labels or ())
    if len(selected_handles) != len(selected_labels):
        raise LayoutError("handles and labels must have the same length")
    if not selected_handles:
        raise LayoutError("legend requires at least one entry")
    if any(not isinstance(label, str) for label in selected_labels):
        raise LayoutError("legend labels must be strings")
    return selected_handles, selected_labels


def legend(
    ax: Axes,
    *,
    handles: Sequence[Any] | None = None,
    labels: Sequence[str] | None = None,
    handler_map: Mapping[Any, Any] | None = None,
    reverse: bool = False,
    replace: bool = False,
    props: Mapping[str, Any] | None = None,
) -> Legend:
    """Create one local Legend on an explicit Axes."""

    target = axes_targets(ax)[0]
    selected_handles, selected_labels = _entries(target, handles, labels)
    if not isinstance(reverse, bool) or not isinstance(replace, bool):
        raise LayoutError("reverse and replace must be booleans")
    selected_props = _props(props, "legend")
    if not isinstance(handler_map, Mapping) and handler_map is not None:
        raise PlotError("handler_map must be a mapping")
    selected_handlers = {} if handler_map is None else dict(handler_map)
    if reverse:
        selected_handles = selected_handles[::-1]
        selected_labels = selected_labels[::-1]
    existing = _existing(target)
    if existing and not replace:
        raise LayoutError("an existing legend requires replace=True")
    # Constructing the Legend is intentionally done before removing an old one.
    created = Legend(
        target,
        selected_handles,
        selected_labels,
        handler_map=selected_handlers,
        **selected_props,
    )
    for old in existing:
        old.remove()
    target.add_artist(created)
    target.legend_ = created
    return created


def legends(
    target: Figure | Sequence[Axes] | Mapping[str, Axes],
    *,
    replace: bool = False,
    props: Mapping[str, Any] | None = None,
) -> tuple[Legend, ...]:
    """Create legends for explicit axes with discoverable entries."""

    if not isinstance(replace, bool):
        raise LayoutError("replace must be a boolean")
    selected_props = _props(props, "legends")
    if isinstance(target, Figure):
        axes = tuple(target.axes)
    else:
        axes = axes_targets(target)
    entries: list[tuple[Axes, tuple[Any, ...], tuple[str, ...], tuple[Legend, ...]]] = (
        []
    )
    for axis in axes:
        handles, labels = axis.get_legend_handles_labels()
        if not handles:
            continue
        existing = _existing(axis)
        if existing and not replace:
            raise LayoutError("an existing legend requires replace=True")
        entries.append((axis, tuple(handles), tuple(labels), existing))
    planned: list[tuple[Axes, Legend, tuple[Legend, ...]]] = []
    for axis, stored_handles, stored_labels, existing in entries:
        item = Legend(axis, stored_handles, stored_labels, **selected_props)
        planned.append((axis, item, existing))
    created: list[Legend] = []
    for axis, item, existing in planned:
        if replace:
            for old in existing:
                old.remove()
        axis.add_artist(item)
        axis.legend_ = item
        created.append(item)
    return tuple(created)


def legend_entries(
    ax: Axes,
    *,
    handler_map: Mapping[Any, Any] | None = None,
) -> LegendEntries:
    """Return discovered handles and labels without creating or printing."""

    target = axes_targets(ax)[0]
    handles, labels = target.get_legend_handles_labels()
    if handler_map is not None and not isinstance(handler_map, Mapping):
        raise PlotError("handler_map must be a mapping")
    return LegendEntries(
        tuple(handles), tuple(labels), {} if handler_map is None else dict(handler_map)
    )


def _colormap_values(
    cmap: str | Colormap,
    stripes: int,
    norm: NormalizeSpec | None,
    reverse: bool,
) -> tuple[tuple[float, float, float, float], ...]:
    """Build deterministic RGBA stripe colors from a local colormap."""

    if isinstance(cmap, str):
        if not cmap.strip():
            raise PlotError("cmap must be a non-empty colormap name")
        try:
            selected = mpl.colormaps.get_cmap(cmap)
        except (TypeError, ValueError) as exc:
            raise PlotError(f"unknown Matplotlib colormap: {cmap!r}") from exc
    elif isinstance(cmap, Colormap):
        selected = cmap
    else:
        raise PlotError("cmap must be a colormap name or Colormap")
    if not isinstance(reverse, bool):
        raise PlotError("reverse must be a boolean")
    if reverse:
        selected = selected.reversed()
    positions = np.linspace(0.0, 1.0, stripes)
    if norm is not None:
        if not callable(norm):
            if isinstance(norm, (str, bytes)):
                raise PlotError(
                    "norm must be a normalizer or a finite (vmin, vmax) pair"
                )
            try:
                bounds = tuple(norm)
            except TypeError as exc:
                raise PlotError(
                    "norm must be a normalizer or a finite (vmin, vmax) pair"
                ) from exc
            if len(bounds) != 2:
                raise PlotError(
                    "norm must be a normalizer or a finite (vmin, vmax) pair"
                )
            try:
                vmin, vmax = (float(bounds[0]), float(bounds[1]))
            except (TypeError, ValueError) as exc:
                raise PlotError("norm bounds must be finite") from exc
            if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin == vmax:
                raise PlotError("norm bounds must be finite and different")
            norm = Normalize(vmin=vmin, vmax=vmax, clip=True)
        try:
            positions = np.asarray(norm(positions, clip=True), dtype=float)
        except (TypeError, ValueError) as exc:
            raise PlotError("norm must return finite values") from exc
        if positions.shape != (stripes,) or not np.all(np.isfinite(positions)):
            raise PlotError("norm must return finite values with the stripe shape")
        positions = np.clip(positions, 0.0, 1.0)
    return tuple(
        cast(
            tuple[float, float, float, float],
            tuple(float(channel) for channel in rgba),
        )
        for rgba in selected(positions)
    )


def cmap_legend(
    ax: Axes,
    *,
    cmap: str | Colormap = "viridis",
    label: str | None = None,
    stripes: int = 8,
    norm: NormalizeSpec | None = None,
    reverse: bool = False,
    replace: bool = False,
    props: Mapping[str, Any] | None = None,
) -> Legend:
    """Create a local legend composed of finite colormap stripe proxies."""

    if isinstance(stripes, bool) or not isinstance(stripes, int) or stripes < 1:
        raise PlotError("stripes must be a positive integer")
    if label is not None and not isinstance(label, str):
        raise PlotError("label must be a string or None")
    colors = _colormap_values(cmap, stripes, norm, reverse)
    handles = tuple(Line2D([], [], color=color, linewidth=4) for color in colors)
    labels = tuple("" for _ in colors)
    if label is not None:
        labels = (label,) + labels[1:]
    return legend(
        ax,
        handles=handles,
        labels=labels,
        reverse=False,
        replace=replace,
        props=props,
    )


__all__ = ["legend", "legends", "legend_entries", "cmap_legend"]
