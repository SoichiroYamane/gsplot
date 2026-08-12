"""Local, explicit Matplotlib legend construction."""

from __future__ import annotations

import inspect
from collections.abc import Mapping, Sequence
from typing import Any, cast, get_type_hints, overload

import matplotlib as mpl
import numpy as np
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.colors import Colormap, Normalize
from matplotlib.figure import Figure
from matplotlib.legend import Legend
from matplotlib.legend_handler import HandlerBase
from matplotlib.lines import Line2D

from .._core.errors import LayoutError, OptionError, PlotError
from .._core.options import MISSING
from .._core.plans import TargetPlan
from .._core.targets import normalize_axes, resolve_target_mapping
from .._core.types import AxesTarget, LegendEntries, NormalizeSpec
from .._core.validation import ensure_bool, ensure_nonnegative
from .axes import axes_targets

_LEGEND_PROPS = frozenset(
    {
        "alignment",
        "borderaxespad",
        "borderpad",
        "columnspacing",
        "facecolor",
        "edgecolor",
        "fancybox",
        "fontsize",
        "frameon",
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
        raise OptionError(f"{context} props contains unknown key(s): {joined}")
    if "ncol" in props and "ncols" in props:
        raise OptionError(f"{context} props cannot contain both 'ncol' and 'ncols'")
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
        if isinstance(handles, (str, bytes)) or isinstance(labels, (str, bytes)):
            raise LayoutError("legend: handles and labels must be sequences")
        try:
            selected_handles = tuple(handles)
            selected_labels = tuple(labels) if labels is not None else ()
        except TypeError as exc:
            raise LayoutError("legend: handles and labels must be sequences") from exc
    if len(selected_handles) != len(selected_labels):
        raise LayoutError("legend: handles and labels must have the same length")
    if not selected_handles:
        raise LayoutError("legend: at least one entry is required")
    if any(not isinstance(label, str) for label in selected_labels):
        raise LayoutError("legend: labels must be strings")
    return selected_handles, selected_labels


def _handler_map(
    value: Mapping[object, HandlerBase] | None,
) -> dict[object, HandlerBase]:
    """Copy and validate a local legend handler map."""

    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise PlotError("legend: handler_map must be a mapping")
    selected = dict(value)
    if any(not isinstance(handler, HandlerBase) for handler in selected.values()):
        raise PlotError("legend: handler_map values must be HandlerBase instances")
    return selected


def _legend_props(
    props: Mapping[str, object] | None,
    *,
    loc: Any,
    frameon: Any,
    fancybox: Any,
    labelspacing: Any,
    handlelength: Any,
) -> dict[str, Any]:
    """Resolve direct concise legend options against the advanced mapping."""

    selected = _props(props, "legend")
    controls = (
        ("loc", loc, "best"),
        ("frameon", frameon, False),
        ("fancybox", fancybox, False),
        ("labelspacing", labelspacing, 0.3),
        ("handlelength", handlelength, None),
    )
    for name, supplied, default in controls:
        if supplied is not MISSING and name in selected:
            raise OptionError(f"legend: {name} conflicts with props")
        if supplied is MISSING and name in selected:
            continue
        value = default if supplied is MISSING else supplied
        if name == "loc":
            if isinstance(value, bool) or not isinstance(value, (str, int)):
                raise LayoutError("legend: loc must be a location string or integer")
            if isinstance(value, str) and not value.strip():
                raise LayoutError("legend: loc must not be empty")
        elif name in {"frameon", "fancybox"}:
            value = ensure_bool(value, f"legend: {name}", error=LayoutError)
        elif name == "labelspacing":
            value = ensure_nonnegative(value, "legend: labelspacing", error=LayoutError)
        elif value is not None:
            value = ensure_nonnegative(value, "legend: handlelength", error=LayoutError)
        selected[name] = value
    return selected


def _entry_sets(
    target: TargetPlan,
    handles: Sequence[Artist] | Mapping[object, Sequence[Artist]] | None,
    labels: Sequence[str] | Mapping[object, Sequence[str]] | None,
) -> tuple[tuple[Axes, tuple[Any, ...], tuple[str, ...]], ...]:
    """Resolve explicit or discovered entries for every target Axes."""

    if (handles is None) != (labels is None):
        raise TypeError("handles and labels must be supplied together")
    if handles is None:
        entries: list[tuple[Axes, tuple[Any, ...], tuple[str, ...]]] = []
        for axis in target.axes:
            discovered_handles, discovered_labels = axis.get_legend_handles_labels()
            if not discovered_handles:
                continue
            discovered_entry_handles, discovered_entry_labels = _entries(
                axis, discovered_handles, discovered_labels
            )
            entries.append((axis, discovered_entry_handles, discovered_entry_labels))
        if target.kind == "single" and not entries:
            raise LayoutError("legend: target Axes has no legend entries")
        return tuple(entries)

    assert labels is not None
    if target.kind == "single":
        if isinstance(handles, Mapping) or isinstance(labels, Mapping):
            if not isinstance(handles, Mapping) or not isinstance(labels, Mapping):
                raise LayoutError(
                    "legend: handles and labels must use the same target form"
                )
            mapped_handles = resolve_target_mapping(target, handles, name="handles")
            mapped_labels = resolve_target_mapping(target, labels, name="labels")
            single_handles = mapped_handles[0]
            single_labels = mapped_labels[0]
        else:
            single_handles = handles
            single_labels = labels
        stored_handles, stored_labels = _entries(
            target.axes[0], single_handles, single_labels
        )
        return ((target.axes[0], stored_handles, stored_labels),)

    if not isinstance(handles, Mapping) or not isinstance(labels, Mapping):
        raise LayoutError(
            "legend: multi-target handles and labels must be exact-key mappings"
        )
    handle_sets = resolve_target_mapping(target, handles, name="handles")
    label_sets = resolve_target_mapping(target, labels, name="labels")
    entries = []
    for axis, axis_handles, axis_labels in zip(target.axes, handle_sets, label_sets):
        stored_handles, stored_labels = _entries(axis, axis_handles, axis_labels)
        entries.append((axis, stored_handles, stored_labels))
    return tuple(entries)


@overload
def legend(
    target: Axes,
    *,
    handles: Sequence[Artist] | Mapping[object, Sequence[Artist]] | None = None,
    labels: Sequence[str] | Mapping[object, Sequence[str]] | None = None,
    handler_map: Mapping[object, HandlerBase] | None = None,
    loc: str | int = "best",
    frameon: bool = False,
    fancybox: bool = False,
    labelspacing: float = 0.3,
    handlelength: float | None = None,
    reverse: bool = False,
    replace: bool = False,
    props: Mapping[str, object] | None = None,
) -> Legend: ...


@overload
def legend(
    target: AxesTarget,
    *,
    handles: Sequence[Artist] | Mapping[object, Sequence[Artist]] | None = None,
    labels: Sequence[str] | Mapping[object, Sequence[str]] | None = None,
    handler_map: Mapping[object, HandlerBase] | None = None,
    loc: str | int = "best",
    frameon: bool = False,
    fancybox: bool = False,
    labelspacing: float = 0.3,
    handlelength: float | None = None,
    reverse: bool = False,
    replace: bool = False,
    props: Mapping[str, object] | None = None,
) -> Legend | tuple[Legend, ...]: ...


def legend(
    target: AxesTarget,
    *,
    handles: Sequence[Artist] | Mapping[object, Sequence[Artist]] | None = None,
    labels: Sequence[str] | Mapping[object, Sequence[str]] | None = None,
    handler_map: Mapping[object, HandlerBase] | None = None,
    loc: Any = MISSING,
    frameon: Any = MISSING,
    fancybox: Any = MISSING,
    labelspacing: Any = MISSING,
    handlelength: Any = MISSING,
    reverse: Any = False,
    replace: Any = False,
    props: Mapping[str, object] | None = None,
) -> Legend | tuple[Legend, ...]:
    """Create publication legends on one or more explicit Axes.

    Parameters
    ----------
    target
        One Axes or a deterministic same-Figure collection of Axes.
    handles, labels
        Optional matched entries. Multi-target explicit entries require exact
        target-key mappings; otherwise Matplotlib discovery is used.
    handler_map
        Optional local handler mapping; it never changes Matplotlib defaults.
    loc, frameon, fancybox, labelspacing, handlelength
        Direct publication controls. Defaults are ``"best"``, ``False``,
        ``False``, ``0.3``, and ``None`` respectively.
    reverse
        Reverse each selected entry sequence before construction.
    replace
        Remove existing legends only when explicitly set to ``True``.
    props
        Finite Matplotlib Legend constructor properties.

    Returns
    -------
    matplotlib.legend.Legend or tuple of Legend
        Native Legends in normalized target order. Collection targets skip
        Axes that have no discovered entries.

    Raises
    ------
    LayoutError, PlotError
        If entries, controls, target, handlers, or properties are invalid.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, ax = gs.subplots()
    >>> gs.line(ax, [0, 1], [0, 1], props={"label": "signal"})
    [<matplotlib.lines.Line2D object ...>]
    >>> item = gs.legend(ax, handlelength=3)
    >>> item.axes is ax
    True
    >>> figure.clear()
    """

    target_plan = normalize_axes(target, operation="legend")
    selected_reverse = ensure_bool(reverse, "legend: reverse", error=LayoutError)
    selected_replace = ensure_bool(replace, "legend: replace", error=LayoutError)
    selected_handlers = _handler_map(handler_map)
    selected_props = _legend_props(
        props,
        loc=loc,
        frameon=frameon,
        fancybox=fancybox,
        labelspacing=labelspacing,
        handlelength=handlelength,
    )
    entry_sets = _entry_sets(target_plan, handles, labels)

    planned: list[tuple[Axes, Legend, tuple[Legend, ...], Legend | None]] = []
    for axis, selected_handles, selected_labels in entry_sets:
        if selected_reverse:
            selected_handles = selected_handles[::-1]
            selected_labels = selected_labels[::-1]
        existing = _existing(axis)
        if existing and not selected_replace:
            raise LayoutError("legend: an existing legend requires replace=True")
        try:
            created = Legend(
                axis,
                selected_handles,
                selected_labels,
                handler_map=cast(Any, selected_handlers),
                **selected_props,
            )
        except (TypeError, ValueError) as exc:
            raise PlotError("legend: invalid entries, handlers, or options") from exc
        current = axis.get_legend()
        planned.append(
            (axis, created, existing, current if isinstance(current, Legend) else None)
        )

    attempted: list[tuple[Axes, Legend, tuple[Legend, ...], Legend | None]] = []
    try:
        for axis, created, existing, current in planned:
            attempted.append((axis, created, existing, current))
            if selected_replace:
                for old in existing:
                    old.remove()
            axis.add_artist(created)
            axis.legend_ = created
    except Exception:
        for axis, created, existing, current in reversed(attempted):
            if created in axis.get_children():
                created.remove()
            for old in existing:
                if old not in axis.get_children():
                    axis.add_artist(old)
            axis.legend_ = current
        raise
    result = tuple(created for _, created, _, _ in planned)
    return result[0] if target_plan.kind == "single" else result


def _legend_signature(
    target: AxesTarget,
    *,
    handles: Sequence[Artist] | Mapping[object, Sequence[Artist]] | None = None,
    labels: Sequence[str] | Mapping[object, Sequence[str]] | None = None,
    handler_map: Mapping[object, HandlerBase] | None = None,
    loc: str | int = "best",
    frameon: bool = False,
    fancybox: bool = False,
    labelspacing: float = 0.3,
    handlelength: float | None = None,
    reverse: bool = False,
    replace: bool = False,
    props: Mapping[str, object] | None = None,
) -> Legend | tuple[Legend, ...]:
    raise AssertionError("signature-only function")


legend.__signature__ = inspect.signature(_legend_signature)  # type: ignore[attr-defined]
legend.__annotations__ = get_type_hints(_legend_signature)


def legends(
    target: Figure | Sequence[Axes] | Mapping[object, Axes],
    *,
    replace: bool = False,
    props: Mapping[str, Any] | None = None,
) -> tuple[Legend, ...]:
    """Create legends for explicit axes with discoverable entries.

    Parameters
    ----------
    target
        Figure, Axes sequence, or string-keyed Axes mapping to inspect.
    replace
        Remove existing legends only when explicitly set to ``True``.
    props
        Finite Matplotlib Legend constructor properties.

    Returns
    -------
    tuple[matplotlib.legend.Legend, ...]
        Native legends created for axes that have discoverable entries.

    Raises
    ------
    LayoutError, PlotError
        If the target, replacement control, or properties are invalid.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, axes = gs.subplots(ncols=2)
    >>> for axis in axes:
    ...     gs.line(axis, [0, 1], [0, 1], props={"label": "signal"})
    [<matplotlib.lines.Line2D object ...>]
    [<matplotlib.lines.Line2D object ...>]
    >>> items = gs.legends(figure)
    >>> len(items)
    2
    >>> figure.clear()
    """

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
    handler_map: Mapping[Any, HandlerBase] | None = None,
) -> LegendEntries:
    """Return discovered handles and labels without creating or printing.

    Parameters
    ----------
    ax
        Explicit target Axes.
    handler_map
        Optional local handler mapping to carry into a later legend call.

    Returns
    -------
    LegendEntries
        Immutable tuples of native handles, labels, and handler data.

    Raises
    ------
    PlotError
        If the target or handler mapping is invalid.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, ax = gs.subplots()
    >>> gs.line(ax, [0, 1], [0, 1], props={"label": "signal"})
    [<matplotlib.lines.Line2D object ...>]
    >>> entries = gs.legend_entries(ax)
    >>> entries.labels
    ('signal',)
    >>> figure.clear()
    """

    if not isinstance(ax, Axes):
        raise PlotError("ax must be a matplotlib.axes.Axes instance")
    target = ax
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
            if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin >= vmax:
                raise PlotError("norm bounds must be finite and increasing")
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
    """Create a local legend composed of finite colormap stripe proxies.

    Parameters
    ----------
    ax
        Explicit target Axes.
    cmap
        Colormap name or native Colormap object.
    label
        Optional label for the first stripe proxy.
    stripes
        Positive number of deterministic color proxies.
    norm, reverse
        Optional normalization and reversal controls.
    replace
        Remove an existing legend only when explicitly set to ``True``.
    props
        Finite Matplotlib Legend constructor properties.

    Returns
    -------
    matplotlib.legend.Legend
        The native local Legend.

    Raises
    ------
    PlotError, LayoutError
        If colormap, normalization, stripe count, target, or properties are
        invalid.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, ax = gs.subplots()
    >>> item = gs.cmap_legend(ax, label="intensity")
    >>> item.axes is ax
    True
    >>> figure.clear()
    """

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
