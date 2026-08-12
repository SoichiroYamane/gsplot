"""Finite root-boundary adapters for overlapping 0.x names.

The compatibility boundary is the only place that accepts reviewed legacy
options.  Canonical implementation functions remain strict and never inspect
the caller, current Figure, or compatibility state.
"""

from __future__ import annotations

import inspect
import warnings
from collections.abc import Mapping, Sequence
from os import PathLike
from typing import Any, get_type_hints
from weakref import WeakKeyDictionary

import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import to_rgba
from matplotlib.figure import Figure
from numpy.typing import ArrayLike

from .._core.errors import OptionError
from .._figure.output import savefig as _savefig
from .._figure.output import show as _show
from .._plot.basic import line as _line
from .._plot.basic import scatter as _scatter
from .._plot.colormap import sample_cmap as _sample_cmap
from .._style.axes import suptitle as _suptitle
from .._style.axes import title as _title
from .._style.legends import legend as _legend

_UNSET = object()
_LEGACY_PLOT_COUNTS: WeakKeyDictionary[Axes, int] = WeakKeyDictionary()

_LEGACY_LINE_KEYS = {
    "color",
    "marker",
    "markersize",
    "markeredgewidth",
    "markeredgecolor",
    "markerfacecolor",
    "linestyle",
    "linewidth",
    "alpha",
    "alpha_mfc",
    "label",
    "ms",
    "mew",
    "ls",
    "lw",
    "c",
    "mec",
    "mfc",
    "antialiased",
    "dash_capstyle",
    "dash_joinstyle",
    "drawstyle",
    "fillstyle",
    "gapcolor",
    "markevery",
    "picker",
    "pickradius",
    "solid_capstyle",
    "solid_joinstyle",
    "visible",
    "zorder",
}
_LEGACY_SCATTER_KEYS = {
    "color",
    "size",
    "alpha",
    "s",
    "c",
    "cmap",
    "norm",
    "vmin",
    "vmax",
    "marker",
    "edgecolors",
    "facecolors",
    "linewidths",
    "antialiaseds",
    "plotnonfinite",
    "rasterized",
    "picker",
    "visible",
    "zorder",
}
_LEGACY_LEGEND_KEYS = {
    "handlers",
    "loc",
    "ncols",
    "ncol",
    "fontsize",
    "title",
    "title_fontsize",
    "title_fontproperties",
    "frameon",
    "framealpha",
    "facecolor",
    "edgecolor",
    "fancybox",
    "shadow",
    "borderpad",
    "labelspacing",
    "handlelength",
    "handleheight",
    "handletextpad",
    "borderaxespad",
    "columnspacing",
    "markerscale",
    "alignment",
    "mode",
    "prop",
    "labelcolor",
}
_LEGACY_TEXT_KEYS = {
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
    "bbox",
    "fontdict",
    "loc",
    "pad",
    "y",
}
_LEGACY_SAVE_KEYS = {
    "bbox_extra_artists",
    "bbox_inches",
    "edgecolor",
    "facecolor",
    "orientation",
    "papertype",
    "pad_inches",
    "pil_kwargs",
    "transparent",
}


def _warn(name: str) -> None:
    """Emit one caller-facing deprecation warning for a legacy dispatch."""

    warnings.warn(
        f"legacy gsplot.{name} call syntax is deprecated; use the canonical "
        "explicit-target signature",
        DeprecationWarning,
        stacklevel=3,
    )


def _legacy_suptitle(text: str, props: Mapping[str, Any] | None) -> Any:
    """Apply the historical current-Figure title through the canonical helper."""

    import matplotlib.pyplot as plt

    return _suptitle(plt.gcf(), text, props=props)


def _legacy_auto_color(ax: Axes) -> tuple[float, float, float, float]:
    """Resolve the historical viridis color for one compatibility plot."""

    count = _LEGACY_PLOT_COUNTS.get(ax, 0)
    color = np.asarray(_sample_cmap("viridis", count=5)[count % 5])
    return (
        float(color[0]),
        float(color[1]),
        float(color[2]),
        float(color[3]),
    )


def _record_legacy_plot(ax: Axes) -> None:
    """Advance the historical compatibility color sequence after a plot."""

    _LEGACY_PLOT_COUNTS[ax] = _LEGACY_PLOT_COUNTS.get(ax, 0) + 1


def _reset_legacy_plot_counts() -> None:
    """Reset compatibility color history without retaining any Axes objects."""

    _LEGACY_PLOT_COUNTS.clear()


def _legacy_show(options: Mapping[str, Any]) -> None:
    """Preserve the historical store-gated save and current-Figure display."""

    import matplotlib.pyplot as plt

    from .legacy.figure.store import StoreSingleton

    selected = dict(options)
    fname = selected.pop("fname", "gsplot")
    formats = selected.pop("ft_list", ("png", "pdf"))
    dpi = selected.pop("dpi", 600)
    display = selected.pop("show", True)
    if StoreSingleton().store:
        _savefig(
            plt.gcf(),
            fname,
            formats=formats,
            dpi=dpi,
            show=False,
            overwrite=True,
            props=selected or None,
        )
    if display:
        plt.show()


def _provided(values: Mapping[str, Any]) -> dict[str, Any]:
    """Remove sentinel values from one finite compatibility option set."""

    return {key: value for key, value in values.items() if value is not _UNSET}


def _reject_mixed(
    name: str, props: Mapping[str, Any] | None, legacy: Mapping[str, Any]
) -> None:
    """Reject canonical and legacy style controls supplied together."""

    if props is not None and legacy:
        raise OptionError(
            f"gsplot.{name} cannot combine canonical props with legacy options"
        )


def _translate_props(
    name: str,
    values: Mapping[str, Any],
    aliases: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Translate reviewed legacy property names into a closed mapping."""

    aliases = {} if aliases is None else aliases
    translated: dict[str, Any] = {}
    for legacy_name, value in values.items():
        if legacy_name == "alpha_mfc":
            continue
        canonical_name = aliases.get(legacy_name, legacy_name)
        if canonical_name in translated:
            raise OptionError(
                f"gsplot.{name} received duplicate controls for {canonical_name!r}"
            )
        translated[canonical_name] = value
    return translated


def _reject_duplicate_scatter_controls(legacy: Mapping[str, Any]) -> None:
    """Reject Matplotlib color controls that describe the same value."""

    duplicate_groups = (
        ("color", "c"),
        ("color", "facecolors"),
        ("c", "facecolors"),
        ("size", "s"),
    )
    for first, second in duplicate_groups:
        if first in legacy and second in legacy:
            raise OptionError(f"gsplot.scatter cannot combine {first!r} and {second!r}")


def _validate_alpha_mfc(value: Any) -> float:
    """Validate the legacy marker-face alpha before creating an artist."""

    if isinstance(value, bool):
        raise OptionError("alpha_mfc must be a finite real number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise OptionError("alpha_mfc must be a finite real number") from exc
    if not np.isfinite(result):
        raise OptionError("alpha_mfc must be a finite real number")
    return result


def line(
    ax: Axes,
    x: ArrayLike,
    y: ArrayLike,
    color: Any = _UNSET,
    marker: Any = _UNSET,
    markersize: Any = _UNSET,
    markeredgewidth: Any = _UNSET,
    markeredgecolor: Any = _UNSET,
    markerfacecolor: Any = _UNSET,
    linestyle: Any = _UNSET,
    linewidth: Any = _UNSET,
    alpha: Any = _UNSET,
    alpha_mfc: Any = _UNSET,
    label: Any = _UNSET,
    *,
    props: Mapping[str, Any] | None = None,
    config: Any = None,
    ms: Any = _UNSET,
    mew: Any = _UNSET,
    ls: Any = _UNSET,
    lw: Any = _UNSET,
    c: Any = _UNSET,
    mec: Any = _UNSET,
    mfc: Any = _UNSET,
    antialiased: Any = _UNSET,
    dash_capstyle: Any = _UNSET,
    dash_joinstyle: Any = _UNSET,
    drawstyle: Any = _UNSET,
    fillstyle: Any = _UNSET,
    gapcolor: Any = _UNSET,
    markevery: Any = _UNSET,
    picker: Any = _UNSET,
    pickradius: Any = _UNSET,
    solid_capstyle: Any = _UNSET,
    solid_joinstyle: Any = _UNSET,
    visible: Any = _UNSET,
    zorder: Any = _UNSET,
) -> Any:
    """Dispatch canonical ``line`` or finite legacy style options."""

    legacy = _provided(
        {
            "color": color,
            "marker": marker,
            "markersize": markersize,
            "markeredgewidth": markeredgewidth,
            "markeredgecolor": markeredgecolor,
            "markerfacecolor": markerfacecolor,
            "linestyle": linestyle,
            "linewidth": linewidth,
            "alpha": alpha,
            "alpha_mfc": alpha_mfc,
            "label": label,
            "ms": ms,
            "mew": mew,
            "ls": ls,
            "lw": lw,
            "c": c,
            "mec": mec,
            "mfc": mfc,
            "antialiased": antialiased,
            "dash_capstyle": dash_capstyle,
            "dash_joinstyle": dash_joinstyle,
            "drawstyle": drawstyle,
            "fillstyle": fillstyle,
            "gapcolor": gapcolor,
            "markevery": markevery,
            "picker": picker,
            "pickradius": pickradius,
            "solid_capstyle": solid_capstyle,
            "solid_joinstyle": solid_joinstyle,
            "visible": visible,
            "zorder": zorder,
        }
    )
    _reject_mixed("line", props, legacy)
    if not legacy:
        if props is None and config is None:
            artists = _line(ax, x, y, props={"color": _legacy_auto_color(ax)})
            _record_legacy_plot(ax)
            return artists
        return _line(ax, x, y, props=props, config=config)
    alpha_mfc = legacy.get("alpha_mfc", _UNSET)
    alpha_mfc_value = (
        _validate_alpha_mfc(alpha_mfc) if alpha_mfc is not _UNSET else None
    )
    translated = _translate_props(
        "line",
        legacy,
        {
            "ms": "markersize",
            "mew": "markeredgewidth",
            "ls": "linestyle",
            "lw": "linewidth",
            "c": "color",
            "mec": "markeredgecolor",
            "mfc": "markerfacecolor",
        },
    )
    if config is None and translated.get("color") is None:
        translated["color"] = _legacy_auto_color(ax)
    _warn("line")
    artists = _line(ax, x, y, props=translated, config=config)
    _record_legacy_plot(ax)
    if alpha_mfc_value is not None:
        alpha = float(translated.get("alpha", 1.0))
        for artist in artists:
            base_color = translated.get("markerfacecolor", artist.get_color())
            red, green, blue, _ = to_rgba(base_color)
            artist.set_markerfacecolor((red, green, blue, alpha * alpha_mfc_value))
    return artists


def scatter(
    ax: Axes,
    x: ArrayLike,
    y: ArrayLike,
    color: Any = _UNSET,
    size: Any = _UNSET,
    alpha: Any = _UNSET,
    *,
    props: Mapping[str, Any] | None = None,
    config: Any = None,
    s: Any = _UNSET,
    c: Any = _UNSET,
    cmap: Any = _UNSET,
    norm: Any = _UNSET,
    vmin: Any = _UNSET,
    vmax: Any = _UNSET,
    marker: Any = _UNSET,
    edgecolors: Any = _UNSET,
    facecolors: Any = _UNSET,
    linewidths: Any = _UNSET,
    antialiaseds: Any = _UNSET,
    plotnonfinite: Any = _UNSET,
    rasterized: Any = _UNSET,
    picker: Any = _UNSET,
    visible: Any = _UNSET,
    zorder: Any = _UNSET,
) -> Any:
    """Dispatch canonical ``scatter`` or finite legacy style options."""

    legacy = _provided(
        {
            "color": color,
            "size": size,
            "alpha": alpha,
            "s": s,
            "c": c,
            "cmap": cmap,
            "norm": norm,
            "vmin": vmin,
            "vmax": vmax,
            "marker": marker,
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
    )
    _reject_mixed("scatter", props, legacy)
    if not legacy:
        if props is None and config is None:
            collection = _scatter(ax, x, y, props={"color": _legacy_auto_color(ax)})
            _record_legacy_plot(ax)
            return collection
        return _scatter(ax, x, y, props=props, config=config)
    _reject_duplicate_scatter_controls(legacy)
    translated = _translate_props("scatter", legacy, {"size": "s"})
    if config is None and not any(
        name in translated and translated[name] is not None
        for name in ("color", "c", "facecolors")
    ):
        translated["color"] = _legacy_auto_color(ax)
    _warn("scatter")
    collection = _scatter(ax, x, y, props=translated, config=config)
    _record_legacy_plot(ax)
    return collection


def legend(
    ax: Axes,
    legacy_handles: Any = _UNSET,
    legacy_labels: Any = _UNSET,
    *,
    handles: Sequence[Any] | None = None,
    labels: Sequence[str] | None = None,
    handler_map: Mapping[Any, Any] | None = None,
    reverse: bool = False,
    replace: bool = False,
    props: Mapping[str, Any] | None = None,
    handlers: Any = _UNSET,
    loc: Any = _UNSET,
    ncols: Any = _UNSET,
    ncol: Any = _UNSET,
    fontsize: Any = _UNSET,
    title: Any = _UNSET,
    title_fontsize: Any = _UNSET,
    title_fontproperties: Any = _UNSET,
    frameon: Any = _UNSET,
    framealpha: Any = _UNSET,
    facecolor: Any = _UNSET,
    edgecolor: Any = _UNSET,
    fancybox: Any = _UNSET,
    shadow: Any = _UNSET,
    borderpad: Any = _UNSET,
    labelspacing: Any = _UNSET,
    handlelength: Any = _UNSET,
    handleheight: Any = _UNSET,
    handletextpad: Any = _UNSET,
    borderaxespad: Any = _UNSET,
    columnspacing: Any = _UNSET,
    markerscale: Any = _UNSET,
    alignment: Any = _UNSET,
    mode: Any = _UNSET,
    prop: Any = _UNSET,
    labelcolor: Any = _UNSET,
) -> Any:
    """Dispatch canonical ``legend`` or finite legacy options."""

    legacy = _provided(
        {
            "handlers": handlers,
            "loc": loc,
            "ncols": ncols,
            "ncol": ncol,
            "fontsize": fontsize,
            "title": title,
            "title_fontsize": title_fontsize,
            "title_fontproperties": title_fontproperties,
            "frameon": frameon,
            "framealpha": framealpha,
            "facecolor": facecolor,
            "edgecolor": edgecolor,
            "fancybox": fancybox,
            "shadow": shadow,
            "borderpad": borderpad,
            "labelspacing": labelspacing,
            "handlelength": handlelength,
            "handleheight": handleheight,
            "handletextpad": handletextpad,
            "borderaxespad": borderaxespad,
            "columnspacing": columnspacing,
            "markerscale": markerscale,
            "alignment": alignment,
            "mode": mode,
            "prop": prop,
            "labelcolor": labelcolor,
        }
    )
    if legacy_handles is not _UNSET:
        legacy["_legacy_handles"] = legacy_handles
    if legacy_labels is not _UNSET:
        legacy["_legacy_labels"] = legacy_labels
    if (legacy_handles is not _UNSET or legacy_labels is not _UNSET) and (
        handles is not None or labels is not None
    ):
        raise OptionError("legend cannot combine positional and canonical entries")
    if legacy and props is not None:
        raise OptionError(
            "gsplot.legend cannot combine canonical props with legacy options"
        )
    if not legacy:
        return _legend(
            ax,
            handles=handles,
            labels=labels,
            handler_map=handler_map,
            reverse=reverse,
            replace=replace,
            props=props,
        )
    positional_handles = legacy.pop("_legacy_handles", _UNSET)
    positional_labels = legacy.pop("_legacy_labels", _UNSET)
    if handlers is not _UNSET:
        if handler_map is not None:
            raise OptionError("legend cannot combine handlers and handler_map")
        handler_map = handlers
    translated = _translate_props(
        "legend",
        legacy,
        {"ncol": "ncols"},
    )
    if positional_handles is not _UNSET:
        if handles is not None:
            raise OptionError("legend received handles twice")
        handles = positional_handles
    if positional_labels is not _UNSET:
        if labels is not None:
            raise OptionError("legend received labels twice")
        labels = positional_labels
    _warn("legend")
    return _legend(
        ax,
        handles=handles,
        labels=labels,
        handler_map=handler_map,
        reverse=reverse,
        replace=replace,
        props=translated,
    )


def title(
    ax: Any = _UNSET,
    text: Any = _UNSET,
    *,
    props: Mapping[str, Any] | None = None,
    title: Any = _UNSET,
    alpha: Any = _UNSET,
    color: Any = _UNSET,
    fontfamily: Any = _UNSET,
    fontproperties: Any = _UNSET,
    fontsize: Any = _UNSET,
    fontstretch: Any = _UNSET,
    fontstyle: Any = _UNSET,
    fontvariant: Any = _UNSET,
    fontweight: Any = _UNSET,
    ha: Any = _UNSET,
    horizontalalignment: Any = _UNSET,
    label: Any = _UNSET,
    linespacing: Any = _UNSET,
    math_fontfamily: Any = _UNSET,
    multialignment: Any = _UNSET,
    parse_math: Any = _UNSET,
    rotation: Any = _UNSET,
    rotation_mode: Any = _UNSET,
    va: Any = _UNSET,
    verticalalignment: Any = _UNSET,
    visible: Any = _UNSET,
    zorder: Any = _UNSET,
    bbox: Any = _UNSET,
    fontdict: Any = _UNSET,
    loc: Any = _UNSET,
    pad: Any = _UNSET,
    y: Any = _UNSET,
) -> Any:
    """Dispatch an explicit Axes title or the legacy Figure title form."""

    legacy = _provided(
        {
            "alpha": alpha,
            "color": color,
            "fontfamily": fontfamily,
            "fontproperties": fontproperties,
            "fontsize": fontsize,
            "fontstretch": fontstretch,
            "fontstyle": fontstyle,
            "fontvariant": fontvariant,
            "fontweight": fontweight,
            "ha": ha,
            "horizontalalignment": horizontalalignment,
            "label": label,
            "linespacing": linespacing,
            "math_fontfamily": math_fontfamily,
            "multialignment": multialignment,
            "parse_math": parse_math,
            "rotation": rotation,
            "rotation_mode": rotation_mode,
            "va": va,
            "verticalalignment": verticalalignment,
            "visible": visible,
            "zorder": zorder,
            "bbox": bbox,
            "fontdict": fontdict,
            "loc": loc,
            "pad": pad,
            "y": y,
        }
    )
    if isinstance(ax, Axes):
        if text is _UNSET or title is not _UNSET or legacy:
            raise OptionError("canonical title requires text and props")
        return _title(ax, text, props=props)
    if text is not _UNSET:
        raise TypeError("legacy Figure title accepts one text value")
    if title is not _UNSET:
        if ax is not _UNSET:
            raise TypeError("title text was supplied twice")
        ax = title
    if ax is _UNSET:
        raise TypeError("title requires text")
    if props is not None:
        raise OptionError("legacy title cannot use canonical props")
    _warn("title")
    return _legacy_suptitle(ax, legacy or None)


def show(
    fig: Figure | str | PathLike[str] | None = None,
    fname: str | PathLike[str] | object = _UNSET,
    ft_list: Sequence[str] | object = _UNSET,
    dpi: float | object = _UNSET,
    display: bool | object = _UNSET,
    *,
    show: bool | object = _UNSET,
    bbox_extra_artists: Any = _UNSET,
    bbox_inches: Any = _UNSET,
    edgecolor: Any = _UNSET,
    facecolor: Any = _UNSET,
    orientation: Any = _UNSET,
    papertype: Any = _UNSET,
    pad_inches: Any = _UNSET,
    pil_kwargs: Any = _UNSET,
    transparent: Any = _UNSET,
) -> Any:
    """Dispatch explicit Figure display or finite legacy save-and-display syntax."""

    if isinstance(fig, Figure):
        if all(value is _UNSET for value in (fname, ft_list, dpi, display, show)):
            return _show(fig)
        raise TypeError("canonical show(fig) does not accept legacy save options")
    legacy = _provided(
        {
            "bbox_extra_artists": bbox_extra_artists,
            "bbox_inches": bbox_inches,
            "edgecolor": edgecolor,
            "facecolor": facecolor,
            "orientation": orientation,
            "papertype": papertype,
            "pad_inches": pad_inches,
            "pil_kwargs": pil_kwargs,
            "transparent": transparent,
        }
    )
    if fig is not None and not isinstance(fig, Figure):
        if fname is not _UNSET:
            raise TypeError("show received a path twice")
        fname = fig
    if fname is not _UNSET:
        legacy["fname"] = fname
    if ft_list is not _UNSET:
        legacy["ft_list"] = ft_list
    if dpi is not _UNSET:
        legacy["dpi"] = dpi
    if display is not _UNSET and show is not _UNSET:
        raise TypeError("show received display twice")
    if display is not _UNSET:
        legacy["show"] = display
    elif show is not _UNSET:
        legacy["show"] = show
    _warn("show")
    _legacy_show(legacy)
    return None


line.__signature__ = inspect.signature(_line)  # type: ignore[attr-defined]
scatter.__signature__ = inspect.signature(_scatter)  # type: ignore[attr-defined]
legend.__signature__ = inspect.signature(_legend)  # type: ignore[attr-defined]
title.__signature__ = inspect.signature(_title)  # type: ignore[attr-defined]
show.__signature__ = inspect.signature(_show)  # type: ignore[attr-defined]
line.__annotations__ = get_type_hints(_line)
scatter.__annotations__ = get_type_hints(_scatter)
legend.__annotations__ = get_type_hints(_legend)
title.__annotations__ = get_type_hints(_title)
show.__annotations__ = get_type_hints(_show)
line.__doc__ = _line.__doc__
scatter.__doc__ = _scatter.__doc__
legend.__doc__ = _legend.__doc__
title.__doc__ = _title.__doc__
show.__doc__ = _show.__doc__


__all__ = ["line", "scatter", "legend", "title", "show"]
