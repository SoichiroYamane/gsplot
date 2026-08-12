"""Finite root adapters for legacy names with canonical replacements.

The historical module shims remain available for the compatibility window, but
root-level legacy calls that have a canonical replacement are translated here.
This module resolves current Matplotlib objects only when a deprecated call
actually needs them; importing ``gsplot`` does not import this module.
"""

from __future__ import annotations

import copy
import json
import sys
import warnings
from collections.abc import Mapping, Sequence
from os import PathLike
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
from matplotlib import ticker
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1.inset_locator import inset_axes as _mpl_inset_axes
from numpy.typing import ArrayLike, NDArray

from .._core.errors import DataError, LayoutError, OptionError
from .._core.numerics import validate_color_values, validate_xy
from .._core.types import AxisSpec, InsetSpec, Theme, ZoomCorners
from .._figure.inset import _manual_zoom_indicator
from .._figure.inset import inset_axes as _inset_axes
from .._figure.layout import _validate_mosaic
from .._figure.layout import subplots as _subplots
from .._io.arrays import read_array
from .._plot.colored import cmap_dash as _cmap_dash
from .._plot.colored import cmap_line as _cmap_line
from .._plot.colored import cmap_scatter as _cmap_scatter
from .._plot.colormap import sample_cmap
from .._style.axes import _TEXT_PROPS
from .._style.axes import box_aspect as _box_aspect
from .._style.axes import minor_ticks as _minor_ticks
from .._style.axes import style_axes as _style_axes
from .._style.axes import title as _title
from .._style.legends import cmap_legend as _cmap_legend
from .._style.legends import legend as _legend
from .._style.legends import legend_entries as _legend_entries
from .._style.legends import legends as _legends
from .._style.panels import panel_labels as _panel_labels
from .._style.themes import fig_facecolor as _fig_facecolor
from .._style.themes import set_theme as _set_theme
from .config import discover_config_path
from .legacy.figure.store import StoreSingleton
from .legacy.plot.line_base import NumLines


def _warn(name: str, replacement: str) -> None:
    """Warn once per deprecated call with its canonical replacement."""

    warnings.warn(
        f"gsplot.{name} is deprecated; use {replacement}",
        DeprecationWarning,
        stacklevel=3,
    )


def _current_figure() -> Figure:
    """Resolve the current Figure only for a legacy current-object call."""

    import matplotlib.pyplot as plt

    return plt.gcf()


def _current_axes() -> tuple[Axes, ...]:
    """Return current Figure axes for a legacy collection adapter."""

    return tuple(_current_figure().axes)


def _flatten_axes(axes: Any) -> list[Axes]:
    """Translate canonical Matplotlib-compatible axes shapes to a flat list."""

    if isinstance(axes, dict):
        return list(axes.values())
    if isinstance(axes, Axes):
        return [axes]
    return list(np.asarray(axes, dtype=object).flat)


def _props(
    values: Mapping[str, Any], aliases: Mapping[str, str] | None = None
) -> dict[str, Any]:
    """Translate finite legacy keyword aliases into a copied property mapping."""

    aliases = {} if aliases is None else aliases
    result: dict[str, Any] = {}
    for name, value in values.items():
        canonical = aliases.get(name, name)
        if canonical in result:
            raise OptionError(f"duplicate legacy property: {canonical}")
        result[canonical] = value
    return result


def _merge_props(
    name: str,
    base: Mapping[str, Any],
    extra: Mapping[str, Any],
    aliases: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Merge finite legacy properties while rejecting duplicate controls."""

    combined = dict(base)
    for key, value in extra.items():
        if key in combined:
            raise OptionError(f"gsplot.{name} received duplicate control {key!r}")
        combined[key] = value
    return _props(combined, aliases)


_LEGACY_MOSAIC_OPTIONS = frozenset(
    {
        "sharex",
        "sharey",
        "width_ratios",
        "height_ratios",
        "empty_sentinel",
        "subplot_kw",
        "gridspec_kw",
        "per_subplot_kw",
    }
)
_LEGACY_PANEL_PROPS = frozenset(
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
_LEGACY_LABEL_PROPS = _TEXT_PROPS | frozenset({"fontdict", "labelpad", "loc"})


def get_cmap(
    cmap: str = "viridis",
    N: int | None = 10,
    cmap_data: ArrayLike | None = None,
    normalize: bool = True,
    reverse: bool = False,
) -> NDArray[np.float64]:
    """Adapt legacy colormap sampling to :func:`gsplot.sample_cmap`."""

    _warn("get_cmap", "sample_cmap")
    if cmap_data is None:
        return sample_cmap(cmap, count=N, reverse=reverse)
    if N is not None:
        raise ValueError("N and cmap_data cannot both be supplied")
    values = np.asarray(cmap_data, dtype=float)
    norm = None if normalize else (0.0, 1.0)
    return sample_cmap(cmap, values=values, norm=norm, reverse=reverse)


def _read_legacy_array(
    source: Any,
    *,
    loader: Literal["genfromtxt", "loadtxt"],
    options: Mapping[str, Any],
) -> NDArray[Any] | list[NDArray[Any]]:
    """Read a path through the canonical adapter or an iterable via NumPy."""

    if isinstance(source, (str, PathLike)):
        return read_array(source, loader=loader, options=options)
    loader_function = np.genfromtxt if loader == "genfromtxt" else np.loadtxt
    try:
        return cast(
            NDArray[Any] | list[NDArray[Any]],
            loader_function(source, **dict(options)),
        )
    except (OSError, TypeError, ValueError, UnicodeError) as exc:
        raise ValueError("legacy array source could not be read") from exc


def load_file(
    f: str | PathLike[str] | Any,
    delimiter: str | None = ",",
    skip_header: int = 0,
    skip_footer: int = 0,
    unpack: bool = True,
    **options: Any,
) -> NDArray[Any] | list[NDArray[Any]]:
    """Adapt legacy ``genfromtxt`` loading to :func:`gsplot.read_array`."""

    _warn("load_file", "read_array")
    selected = {
        "delimiter": delimiter,
        "skip_header": skip_header,
        "skip_footer": skip_footer,
        "unpack": unpack,
        **options,
    }
    return _read_legacy_array(f, loader="genfromtxt", options=selected)


def load_file_fast(
    f: str | PathLike[str] | Any,
    delimiter: str | None = ",",
    skiprows: int = 0,
    unpack: bool = True,
    **options: Any,
) -> NDArray[Any] | list[NDArray[Any]]:
    """Adapt legacy ``loadtxt`` loading to :func:`gsplot.read_array`."""

    _warn("load_file_fast", "read_array")
    selected = {
        "delimiter": delimiter,
        "skiprows": skiprows,
        "unpack": unpack,
        **options,
    }
    return _read_legacy_array(f, loader="loadtxt", options=selected)


def axes(
    store: bool = False,
    size: tuple[int | float, int | float] = (5, 5),
    unit: str = "in",
    mosaic: Any = "A",
    clear: bool = True,
    ion: bool = False,
    **options: Any,
) -> list[Axes]:
    """Adapt the old flat-list axes helper to explicit canonical subplots."""

    _warn("axes", "subplots")
    created: Axes | NDArray[Any] | dict[str, Axes]
    if options:
        unknown = sorted(set(options) - _LEGACY_MOSAIC_OPTIONS)
        if unknown:
            raise OptionError(f"legacy axes options are unsupported: {unknown}")
    if not isinstance(store, bool) or not isinstance(clear, bool):
        raise TypeError("store and clear must be booleans")
    if not isinstance(ion, bool):
        raise TypeError("ion must be a boolean")
    if not isinstance(size, Sequence) or isinstance(size, (str, bytes)):
        raise LayoutError("size must contain two finite positive values")
    if len(size) != 2:
        raise LayoutError("size must contain two finite positive values")
    factors = {"mm": 1 / 25.4, "cm": 1 / 2.54, "in": 1.0, "pt": 1 / 72.0}
    if unit not in factors:
        raise LayoutError("unit must be one of: cm, in, mm, pt")
    try:
        width = float(size[0]) * factors[unit]
        height = float(size[1]) * factors[unit]
    except (TypeError, ValueError) as exc:
        raise LayoutError("size must contain two finite positive values") from exc
    if not np.isfinite(width) or not np.isfinite(height) or width <= 0 or height <= 0:
        raise LayoutError("size must contain two finite positive values")
    _validate_mosaic(mosaic)
    StoreSingleton().store = store
    NumLines.reset()
    from .root_api import _register_legacy_plot_axes, _reset_legacy_plot_counts

    _reset_legacy_plot_counts()
    figure = _current_figure()
    # The old helper operated on the current Figure.  Reuse that object only
    # at this compatibility boundary; canonical ``subplots`` never does so
    # implicitly.
    if options:
        if clear:
            figure.clear()
        created = figure.subplot_mosaic(mosaic, **options)
    else:
        figure, created = _subplots(fig=figure, clear=clear, unit="in", mosaic=mosaic)
    figure.set_size_inches(width, height)
    figure.tight_layout()
    if ion:
        import matplotlib.pyplot as plt

        plt.ion()
    # ``store`` is retained only as a source-compatible flag.  New code owns
    # the returned Figure/Axes explicitly and no singleton is populated.
    del store
    flattened = _flatten_axes(created)
    _register_legacy_plot_axes(flattened)
    return flattened


def _legacy_limits(
    value: Any,
) -> tuple[tuple[float, float] | None, str, int | None, float | None]:
    """Translate a legacy limit, scale, and optional tick controls."""

    if value is None:
        return None, "linear", None, None
    if isinstance(value, (str, bytes)):
        raise LayoutError("legacy limits must be a finite sequence")
    values = tuple(value)
    if len(values) < 2:
        raise LayoutError("legacy limits must contain two values")
    try:
        limits = (float(values[0]), float(values[1]))
    except (TypeError, ValueError) as exc:
        raise LayoutError("legacy limits must contain finite values") from exc
    if not np.all(np.isfinite(limits)) or limits[0] == limits[1]:
        raise LayoutError("legacy limits must contain finite unequal values")
    scale = values[2] if len(values) > 2 and isinstance(values[2], str) else "linear"
    if scale not in {"linear", "log", "symlog", "logit"}:
        raise LayoutError(f"unsupported legacy scale: {scale!r}")
    minor_count: int | None = None
    major_base: float | None = None
    if len(values) > 2 and not isinstance(values[2], str):
        if isinstance(values[2], bool) or not isinstance(values[2], (int, float)):
            raise LayoutError("legacy minor tick count must be a positive integer")
        minor_count = int(values[2])
        if minor_count < 1 or minor_count != values[2]:
            raise LayoutError("legacy minor tick count must be a positive integer")
    if len(values) > 3:
        try:
            major_base = float(values[3])
        except (TypeError, ValueError) as exc:
            raise LayoutError("legacy major tick base must be positive") from exc
        if not np.isfinite(major_base) or major_base <= 0:
            raise LayoutError("legacy major tick base must be positive")
    return limits, scale, minor_count, major_base


def _apply_legacy_labels(
    axis: Axes,
    values: Sequence[Any],
    *,
    minor: bool,
    props: Mapping[str, Any] | None = None,
) -> None:
    """Translate one legacy label/limit record to canonical style operations."""

    if len(values) < 2:
        raise LayoutError("legacy labels require x and y labels")
    xlim, xscale, xminor_count, xmajor_base = _legacy_limits(
        values[2] if len(values) > 2 else None
    )
    ylim, yscale, yminor_count, ymajor_base = _legacy_limits(
        values[3] if len(values) > 3 else None
    )
    _style_axes(
        axis,
        AxisSpec(
            xlabel=values[0],
            ylabel=values[1],
            xlim=xlim,
            ylim=ylim,
            xscale=cast(Literal["linear", "log", "symlog", "logit"], xscale),
            yscale=cast(Literal["linear", "log", "symlog", "logit"], yscale),
            xminor=minor,
            yminor=minor,
        ),
    )
    selected_props = {} if props is None else dict(props)
    axis.set_xlabel(axis.get_xlabel(), **selected_props)
    axis.set_ylabel(axis.get_ylabel(), **selected_props)
    if xminor_count is not None:
        axis.xaxis.set_minor_locator(ticker.AutoMinorLocator(xminor_count))
    if yminor_count is not None:
        axis.yaxis.set_minor_locator(ticker.AutoMinorLocator(yminor_count))
    if xmajor_base is not None:
        axis.xaxis.set_major_locator(ticker.MultipleLocator(xmajor_base))
    if ymajor_base is not None:
        axis.yaxis.set_major_locator(ticker.MultipleLocator(ymajor_base))


def _apply_legacy_inset_options(
    parent: Axes,
    child: Axes,
    lab_lims: Sequence[Any] | None,
    minor: bool,
    zoom: bool | tuple[Any, ...],
    zoom_color: Any,
    zoom_alpha: float,
) -> None:
    """Apply explicitly translated legacy inset styling to a child Axes."""

    if lab_lims is not None:
        _apply_legacy_labels(child, lab_lims, minor=False)
    _minor_ticks(child, minor, axis="both")
    if zoom:
        selected_zorder = float(child.get_zorder()) - 0.01
        if zoom is True:
            parent.indicate_inset_zoom(
                child,
                edgecolor=zoom_color,
                alpha=zoom_alpha,
                zorder=selected_zorder,
            )
        else:
            _manual_zoom_indicator(
                parent,
                child,
                cast(ZoomCorners, zoom),
                color=zoom_color,
                alpha=zoom_alpha,
                zorder=selected_zorder,
            )


def _validate_legacy_zoom(zoom: bool | tuple[Any, ...]) -> bool | ZoomCorners:
    """Validate zoom corners before a compatibility inset is created."""

    if not isinstance(zoom, (bool, tuple)):
        raise LayoutError("zoom must be false, true, or a pair of corner pairs")
    if not isinstance(zoom, tuple):
        return zoom
    if len(zoom) != 2:
        raise LayoutError("legacy zoom must contain two corner pairs")
    pairs: list[tuple[int, int]] = []
    for corner in zoom:
        if not isinstance(corner, (tuple, list)) or len(corner) != 2:
            raise LayoutError("legacy zoom must contain two corner pairs")
        if any(type(value) is not int or value not in {1, 2, 3, 4} for value in corner):
            raise LayoutError("legacy zoom corners must be integers from 1 through 4")
        pairs.append((corner[0], corner[1]))
    if pairs[0] == pairs[1]:
        raise LayoutError("legacy zoom corner pairs must be distinct")
    return cast(ZoomCorners, tuple(pairs))


def _validate_legacy_label_record(values: Sequence[Any]) -> None:
    """Validate a legacy label record without touching an Axes."""

    if len(values) < 2:
        raise LayoutError("legacy labels require x and y labels")
    _legacy_limits(values[2] if len(values) > 2 else None)
    _legacy_limits(values[3] if len(values) > 3 else None)


def axes_inset(
    ax: Axes,
    bounds: tuple[float, float, float, float],
    transform: Any = None,
    projection: str | None = None,
    polar: bool = False,
    lab_lims: Sequence[Any] | None = None,
    minor_ticks: bool = True,
    zoom: bool | tuple[Any, ...] = True,
    zoom_color: Any = "black",
    zoom_alpha: float = 0.3,
    zorder: float = 5,
    **options: Any,
) -> Axes:
    """Adapt legacy inset placement and styling to an explicit parent Axes."""

    _warn("axes_inset", "inset_axes")
    if options:
        raise OptionError("legacy inset options are unsupported")
    if not isinstance(minor_ticks, bool):
        raise LayoutError("minor_ticks must be a boolean")
    if not isinstance(polar, bool):
        raise LayoutError("polar must be a boolean")
    selected_zoom = _validate_legacy_zoom(zoom)
    if not isinstance(zoom_alpha, (int, float)) or not np.isfinite(zoom_alpha):
        raise LayoutError("zoom_alpha must be finite")
    if zoom_alpha < 0 or zoom_alpha > 1:
        raise LayoutError("zoom_alpha must be between zero and one")
    if lab_lims is not None:
        _validate_legacy_label_record(lab_lims)
    spec = InsetSpec(bounds=bounds)
    if transform is None and projection is None and not polar and zorder == 5:
        child = _inset_axes(ax, spec)
    else:
        try:
            child = ax.inset_axes(
                bounds,
                transform=transform,
                projection="polar" if polar else projection,
                zorder=zorder,
            )
        except (TypeError, ValueError) as exc:
            raise LayoutError("could not create the legacy inset Axes") from exc
    _apply_legacy_inset_options(
        ax,
        child,
        lab_lims,
        minor_ticks,
        selected_zoom,
        zoom_color,
        float(zoom_alpha),
    )
    return cast(Axes, child)


def axes_inset_padding(
    ax: Axes,
    width: float | str,
    height: float | str,
    loc: str = "upper right",
    borderpad: float = 0.5,
    bbox_to_anchor: Any = None,
    bbox_transform: Any = None,
    axes_kwargs: Mapping[str, Any] | None = None,
    lab_lims: Sequence[Any] | None = None,
    minor_ticks: bool = True,
    zoom: bool | tuple[Any, ...] = True,
    zoom_color: Any = "black",
    zoom_alpha: float = 0.3,
    **options: Any,
) -> Axes:
    """Adapt legacy size-based inset creation to :class:`InsetSpec`."""

    _warn("axes_inset_padding", "inset_axes")
    if options:
        raise OptionError("legacy inset constructor options are unsupported")
    if bbox_transform is not None and not hasattr(bbox_transform, "transform"):
        raise LayoutError("bbox_transform must be a Matplotlib transform")
    if axes_kwargs is not None and not isinstance(axes_kwargs, Mapping):
        raise LayoutError("axes_kwargs must be a mapping")
    if not isinstance(minor_ticks, bool):
        raise LayoutError("minor_ticks must be a boolean")
    selected_zoom = _validate_legacy_zoom(zoom)
    if not isinstance(zoom_alpha, (int, float)) or not np.isfinite(zoom_alpha):
        raise LayoutError("zoom_alpha must be finite")
    if zoom_alpha < 0 or zoom_alpha > 1:
        raise LayoutError("zoom_alpha must be between zero and one")
    anchor = bbox_to_anchor
    if anchor is not None:
        if hasattr(anchor, "bounds"):
            anchor = tuple(anchor.bounds)
        else:
            try:
                anchor = tuple(anchor)
            except TypeError as exc:
                raise LayoutError("bbox_to_anchor must be a finite tuple") from exc
        if len(anchor) not in (2, 4):
            raise LayoutError("bbox_to_anchor must contain two or four values")
        try:
            anchor = tuple(float(value) for value in anchor)
        except (TypeError, ValueError) as exc:
            raise LayoutError("bbox_to_anchor must contain finite values") from exc
        if not np.all(np.isfinite(anchor)):
            raise LayoutError("bbox_to_anchor must contain finite values")
    if lab_lims is not None:
        _validate_legacy_label_record(lab_lims)
    if axes_kwargs is not None and any(not isinstance(key, str) for key in axes_kwargs):
        raise OptionError("axes_kwargs keys must be strings")
    try:
        child = _mpl_inset_axes(
            ax,
            width=width,
            height=height,
            loc=loc,
            borderpad=borderpad,
            bbox_to_anchor=anchor,
            bbox_transform=bbox_transform,
            axes_kwargs=None if axes_kwargs is None else dict(axes_kwargs),
        )
    except (TypeError, ValueError) as exc:
        raise LayoutError("could not create the legacy inset Axes") from exc
    _apply_legacy_inset_options(
        ax,
        child,
        lab_lims,
        minor_ticks,
        selected_zoom,
        zoom_color,
        float(zoom_alpha),
    )
    return cast(Axes, child)


def get_figure_size() -> NDArray[np.float64]:
    """Return the current Figure size as a compatibility-only query."""

    _warn("get_figure_size", "Figure.get_size_inches()")
    return np.asarray(_current_figure().get_size_inches()).copy()


def graph_square(ax: Axes) -> None:
    """Adapt one legacy square-aspect call to :func:`gsplot.box_aspect`."""

    _warn("graph_square", "box_aspect")
    _box_aspect(ax, 1.0)


def graph_square_axes() -> None:
    """Apply canonical square aspect to current compatibility axes."""

    _warn("graph_square_axes", "box_aspect")
    _box_aspect(_current_axes(), 1.0)


def graph_white(ax: Axes) -> None:
    """Adapt one legacy white theme call to :func:`gsplot.set_theme`."""

    _warn("graph_white", "set_theme")
    _set_theme(ax, Theme.white())


def graph_white_axes() -> None:
    """Apply the canonical white theme to current compatibility axes."""

    _warn("graph_white_axes", "set_theme")
    _set_theme(_current_figure(), Theme.white())


def graph_transparent(ax: Axes) -> None:
    """Adapt one legacy transparent theme call to :func:`gsplot.set_theme`."""

    _warn("graph_transparent", "set_theme")
    _set_theme(ax, Theme.transparent())


def graph_transparent_axes() -> None:
    """Apply the canonical transparent theme to current compatibility axes."""

    _warn("graph_transparent_axes", "set_theme")
    _set_theme(_current_figure(), Theme.transparent())


def graph_facecolor(color: str = "black") -> None:
    """Adapt the current-figure facecolor call to :func:`gsplot.fig_facecolor`."""

    _warn("graph_facecolor", "fig_facecolor")
    _fig_facecolor(_current_figure(), color)


def label(
    lab_lims: Sequence[Sequence[Any]],
    xpad_label: float = 5,
    ypad_label: float = 5,
    minor_ticks_axes: bool = True,
    tight_layout: bool = True,
    xpad_layout: float = 2,
    ypad_layout: float = 2,
    **options: Any,
) -> None:
    """Translate legacy label records into explicit :class:`AxisSpec` values."""

    _warn("label", "style_axes")
    unknown = sorted(set(options) - _LEGACY_LABEL_PROPS)
    if unknown:
        raise OptionError(f"legacy label options are unsupported: {unknown}")
    axes = _current_axes()
    if len(lab_lims) != len(axes):
        raise LayoutError("legacy label records must match current axes")
    for axis, record in zip(axes, lab_lims):
        _apply_legacy_labels(axis, record, minor=minor_ticks_axes, props=options)
        axis.xaxis.labelpad = xpad_label
        axis.yaxis.labelpad = ypad_label
    if tight_layout:
        _current_figure().tight_layout(w_pad=xpad_layout, h_pad=ypad_layout)


def label_add_index(
    loc: str = "out",
    x_offset: float = 0,
    y_offset: float = 0,
    ha: str = "center",
    va: str = "center",
    fontsize: float | str = "large",
    glyph: str = "alphabet",
    capitalize: bool = False,
    **options: Any,
) -> None:
    """Translate legacy panel-index labels to canonical panel text artists."""

    _warn("label_add_index", "panel_labels")
    unknown = sorted(set(options) - _LEGACY_PANEL_PROPS)
    if unknown or loc not in {"in", "out", "corner"}:
        raise OptionError("legacy panel-label placement options are unsupported")
    if any(name in options for name in {"ha", "va", "fontsize"}):
        raise OptionError("panel label controls cannot be supplied twice")
    if glyph not in {"alphabet", "roman", "number", "hiragana"}:
        raise OptionError("legacy glyph must be alphabet, roman, number, or hiragana")
    labels: list[str] = []
    for index in range(len(_current_axes())):
        if glyph == "number":
            value = str(index + 1)
        elif glyph == "roman":
            value = _roman(index + 1)
        elif glyph == "hiragana":
            value = _hiragana(index)
        else:
            value = _panel_name(index)
        labels.append(value.upper() if capitalize else value)
    texts = _panel_labels(
        _current_axes(),
        labels=labels,
        props={"ha": ha, "va": va, "fontsize": fontsize, **options},
    )
    position = {
        "in": (0.02 + x_offset, 0.98 + y_offset),
        "out": (0.02 + x_offset, 1.02 + y_offset),
        "corner": (0.0 + x_offset, 1.0 + y_offset),
    }[loc]
    for text in texts:
        text.set_position(position)


def _panel_name(index: int) -> str:
    """Return a deterministic alphabetic panel name."""

    value = index + 1
    result = ""
    while value:
        value, remainder = divmod(value - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def _roman(value: int) -> str:
    """Return a small positive integer in Roman numerals."""

    numerals = (
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    )
    result = ""
    for number, numeral in numerals:
        count, value = divmod(value, number)
        result += numeral * count
    return result


def _hiragana(index: int) -> str:
    """Return the historical hiragana panel sequence with a safe fallback."""

    syllables = "あいうえおかきくけこさしすせそたちつてとなにぬねの"
    if index < len(syllables):
        return syllables[index]
    return f"{syllables[-1]}{index + 1}"


def legend_axes(*, replace: bool = False, **props: Any) -> list[Any]:
    """Adapt current-figure legend creation to :func:`gsplot.legends`."""

    _warn("legend_axes", "legends")
    return list(_legends(_current_figure(), replace=replace, props=props or None))


def legend_handlers(
    ax: Axes,
    handles: Sequence[Any] | None = None,
    labels: Sequence[str] | None = None,
    handlers: Mapping[Any, Any] | None = None,
    **props: Any,
) -> Any:
    """Adapt legacy handler arguments to the local canonical legend map."""

    _warn("legend_handlers", "legend")
    return _legend(
        ax,
        handles=handles,
        labels=labels,
        handler_map=handlers,
        props=props or None,
    )


def legend_reverse(
    ax: Axes,
    handles: Sequence[Any] | None = None,
    labels: Sequence[str] | None = None,
    handlers: Mapping[Any, Any] | None = None,
    **props: Any,
) -> Any:
    """Adapt legacy reversed legend construction to ``reverse=True``."""

    _warn("legend_reverse", "legend(reverse=True)")
    return _legend(
        ax,
        handles=handles,
        labels=labels,
        handler_map=handlers,
        reverse=True,
        props=props or None,
    )


def legend_get_handlers(ax: Axes) -> tuple[Any, tuple[str, ...], dict[Any, Any]]:
    """Adapt legacy legend extraction to immutable :func:`legend_entries`."""

    _warn("legend_get_handlers", "legend_entries")
    entries = _legend_entries(ax)
    return (
        tuple(entries.handles),
        tuple(entries.labels),
        dict(entries.handler_map or {}),
    )


def legend_colormap(
    ax: Axes,
    cmap: str = "viridis",
    label: str | None = None,
    num_stripes: int = 8,
    vmin: float = 0,
    vmax: float = 1,
    reverse: bool = False,
    **props: Any,
) -> Any:
    """Adapt legacy colormap legends to :func:`gsplot.cmap_legend`."""

    _warn("legend_colormap", "cmap_legend")
    return _cmap_legend(
        ax,
        cmap=cmap,
        label=label,
        stripes=num_stripes,
        norm=(vmin, vmax),
        reverse=reverse,
        props=props or None,
    )


def ticks_off(ax: Axes, mode: str = "xy") -> None:
    """Adapt legacy minor-tick disabling to the canonical selector."""

    _warn("ticks_off", "minor_ticks")
    selected = {"xy": "both"}.get(mode, mode)
    _minor_ticks(
        ax,
        False,
        axis=cast(Literal["x", "y", "both"], selected),
    )


def ticks_on(ax: Axes, mode: str = "xy") -> None:
    """Adapt legacy minor-tick enabling to the canonical selector."""

    _warn("ticks_on", "minor_ticks")
    selected = {"xy": "both"}.get(mode, mode)
    _minor_ticks(
        ax,
        True,
        axis=cast(Literal["x", "y", "both"], selected),
    )


def ticks_on_axes() -> None:
    """Enable canonical minor ticks on current compatibility axes."""

    _warn("ticks_on_axes", "minor_ticks")
    _minor_ticks(_current_axes(), True, axis="both")


def title_axes(ax: Axes, title: str, **props: Any) -> Any:
    """Adapt legacy explicit-axis title calls to :func:`gsplot.title`."""

    _warn("title_axes", "title")
    return _title(ax, title, props=props or None)


def config_load(config_path: str | PathLike[str] | None = None) -> dict[str, Any]:
    """Return a defensive legacy configuration snapshot without applying it."""

    _warn("config_load", "load_config")
    selected = Path(config_path) if config_path is not None else discover_config_path()
    if selected is None:
        return {}
    try:
        with selected.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, ValueError) as exc:
        raise ValueError(f"could not read legacy configuration: {selected}") from exc
    if not isinstance(value, dict):
        raise ValueError("legacy configuration must be a JSON object")
    return copy.deepcopy(value)


def config_dict() -> dict[str, Any]:
    """Return a defensive snapshot of the discovered legacy configuration."""

    _warn("config_dict", "Config")
    return config_load()


def config_entry_option(key: str) -> Any:
    """Read one value from a defensive legacy configuration snapshot."""

    _warn("config_entry_option", "Config.get")
    return config_dict().get(key, {})


def home() -> str:
    """Return the process home path as a compatibility-only query."""

    _warn("home", "Path.home()")
    return str(Path.home())


def pwd() -> str:
    """Return the process current path as a compatibility-only query."""

    _warn("pwd", "Path.cwd()")
    return str(Path.cwd())


def pwd_move() -> None:
    """Warn and deliberately avoid changing the process working directory."""

    _warn(
        "pwd_move",
        "Path.cwd() and explicit path handling (this compatibility helper is a no-op)",
    )
    return None


def pwd_main() -> str:
    """Return the main script directory for compatibility-only callers."""

    _warn("pwd_main", "an explicit Path")
    main_file = getattr(sys.modules.get("__main__"), "__file__", None)
    return str(Path(main_file).resolve().parent if main_file else Path.cwd())


def _interpolate_legacy_line(
    x: ArrayLike,
    y: ArrayLike,
    values: ArrayLike,
    points: int | None,
) -> tuple[ArrayLike, ArrayLike, ArrayLike]:
    """Preserve the historical distance-based line interpolation option."""

    if points is None:
        return x, y, values
    if isinstance(points, bool) or not isinstance(points, int) or points < 2:
        raise OptionError("interpolation_points must be an integer >= 2")
    x_values, y_values = validate_xy(x, y, colored=True)
    color_values = validate_color_values(values)
    if color_values.shape != x_values.shape:
        raise DataError("cmapdata must have the same shape as x and y")
    distances = np.concatenate(
        ([0.0], np.cumsum(np.hypot(np.diff(x_values), np.diff(y_values))))
    )
    if distances[-1] <= 0:
        raise DataError("interpolation requires at least one non-zero segment")
    keep = np.r_[True, np.diff(distances) > 0]
    positions = np.linspace(0.0, distances[-1], points)
    return (
        np.interp(positions, distances[keep], x_values[keep]),
        np.interp(positions, distances[keep], y_values[keep]),
        np.interp(positions, distances[keep], color_values[keep]),
    )


def _validate_legacy_span(value: float | None, name: str) -> None:
    """Validate a legacy coordinate span retained for source compatibility."""

    if value is None:
        return
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise OptionError(f"{name} must be a finite positive number") from exc
    if not np.isfinite(numeric) or numeric <= 0:
        raise OptionError(f"{name} must be a finite positive number")


def line_colormap_solid(
    ax: Axes,
    x: ArrayLike,
    y: ArrayLike,
    cmapdata: ArrayLike,
    cmap: str = "viridis",
    linewidth: float = 1,
    label: str | None = None,
    interpolation_points: int | None = None,
    **props: Any,
) -> list[Any]:
    """Adapt legacy solid colormap lines to :func:`gsplot.cmap_line`."""

    _warn("line_colormap_solid", "cmap_line")
    x, y, cmapdata = _interpolate_legacy_line(x, y, cmapdata, interpolation_points)
    selected = _merge_props(
        "line_colormap_solid",
        {"linewidths": linewidth, "label": label},
        props,
        {"lw": "linewidths"},
    )
    return [_cmap_line(ax, x, y, cmapdata, cmap=cmap, props=selected)]


def line_colormap_dashed(
    ax: Axes,
    x: ArrayLike,
    y: ArrayLike,
    cmapdata: ArrayLike,
    cmap: str = "viridis",
    linewidth: float = 1,
    line_pattern: tuple[float, float] = (10, 10),
    label: str | None = None,
    xspan: float | None = None,
    yspan: float | None = None,
    **props: Any,
) -> list[Any]:
    """Adapt legacy dashed colormap lines to :func:`gsplot.cmap_dash`."""

    _warn("line_colormap_dashed", "cmap_dash")
    _validate_legacy_span(xspan, "xspan")
    _validate_legacy_span(yspan, "yspan")
    selected = _merge_props(
        "line_colormap_dashed",
        {"linewidths": linewidth, "label": label},
        props,
        {"lw": "linewidths"},
    )
    return list(
        _cmap_dash(
            ax,
            x,
            y,
            cmapdata,
            dash=line_pattern,
            cmap=cmap,
            props=selected,
        )
    )


def scatter_colormap(
    ax: Axes,
    x: ArrayLike,
    y: ArrayLike,
    cmapdata: ArrayLike,
    size: float = 1,
    cmap: str = "viridis",
    vmin: float = 0,
    vmax: float = 1,
    alpha: float = 1,
    label: str | None = None,
    **props: Any,
) -> Any:
    """Adapt legacy colormapped scatter calls to :func:`gsplot.cmap_scatter`."""

    _warn("scatter_colormap", "cmap_scatter")
    selected = _merge_props(
        "scatter_colormap",
        {"s": size, "alpha": alpha, "label": label},
        props,
        {"size": "s"},
    )
    return _cmap_scatter(
        ax,
        x,
        y,
        cmapdata,
        cmap=cmap,
        norm=(vmin, vmax),
        props=selected,
    )


__all__ = [
    "get_cmap",
    "load_file",
    "load_file_fast",
    "axes",
    "axes_inset",
    "axes_inset_padding",
    "get_figure_size",
    "line_colormap_solid",
    "line_colormap_dashed",
    "scatter_colormap",
    "graph_square",
    "graph_square_axes",
    "graph_white",
    "graph_white_axes",
    "graph_transparent",
    "graph_transparent_axes",
    "graph_facecolor",
    "label",
    "label_add_index",
    "legend_axes",
    "legend_handlers",
    "legend_reverse",
    "legend_get_handlers",
    "legend_colormap",
    "ticks_off",
    "ticks_on",
    "ticks_on_axes",
    "title_axes",
    "config_load",
    "config_dict",
    "config_entry_option",
    "home",
    "pwd",
    "pwd_move",
    "pwd_main",
]
