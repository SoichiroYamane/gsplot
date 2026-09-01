"""Local, explicit Matplotlib legend construction."""

from __future__ import annotations

import copy
import inspect
from collections.abc import Mapping, Sequence
from numbers import Integral
from typing import Any, cast, get_type_hints, overload

import matplotlib as mpl
import numpy as np
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.axes._base import _AxesBase
from matplotlib.colors import Colormap, Normalize
from matplotlib.figure import Figure
from matplotlib.legend import Legend
from matplotlib.legend_handler import HandlerBase
from matplotlib.patches import Rectangle
from matplotlib.transforms import Transform

from .._core.errors import LayoutError, OptionError, PlotError
from .._core.options import MISSING
from .._core.plans import TargetPlan
from .._core.targets import normalize_axes, resolve_target_mapping
from .._core.types import AxesTarget, LegendEntries, NormalizeSpec
from .._core.validation import ensure_bool, ensure_finite_real, ensure_nonnegative

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

_MAX_NUM_STRIPES = 256


def _props(
    props: Mapping[str, Any] | None,
    context: str,
    kwargs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate and copy legend constructor properties."""

    if props is not None and not isinstance(props, Mapping):
        raise PlotError(f"{context} props must be a mapping")
    merged = dict(props or {})
    if kwargs:
        merged.update(kwargs)
    if any(not isinstance(key, str) for key in merged):
        raise PlotError(f"{context} props keys must be strings")
    unknown = sorted(set(merged) - _LEGEND_PROPS)
    if unknown:
        joined = ", ".join(repr(key) for key in unknown)
        raise OptionError(f"{context} props contains unknown key(s): {joined}")
    if "ncol" in merged and "ncols" in merged:
        raise OptionError(f"{context} props cannot contain both 'ncol' and 'ncols'")
    return merged


def _existing(ax: Any) -> tuple[Legend, ...]:
    """Return legends attached to one Axes without creating anything."""

    found: list[Legend] = []
    for child in ax.get_children():
        if isinstance(child, Legend) and child not in found:
            found.append(child)
    current = ax.get_legend()
    if isinstance(current, Legend) and current not in found:
        found.append(current)
    return tuple(found)


class _ColormapHandler(HandlerBase):
    """Render one colormap proxy as a horizontal sequence of rectangles."""

    def __init__(self, colors: Sequence[tuple[float, float, float, float]]) -> None:
        super().__init__()
        self.colors = tuple(colors)

    def create_artists(
        self,
        legend: Legend,
        orig_handle: Artist,
        xdescent: float,
        ydescent: float,
        width: float,
        height: float,
        fontsize: float,
        trans: Transform,
    ) -> list[Rectangle]:
        """Create adjacent, edge-free Rectangle artists for one proxy."""

        del legend, orig_handle, fontsize
        stripe_width = width / len(self.colors)
        return [
            Rectangle(
                (xdescent + index * stripe_width, ydescent),
                stripe_width,
                height,
                facecolor=color,
                edgecolor="none",
                linewidth=0,
                transform=trans,
            )
            for index, color in enumerate(self.colors)
        ]


def _attach_legend(axis: Axes | _AxesBase, legend: Legend) -> None:
    """Attach one Legend through Matplotlib's native legend slot."""

    remove_legend = getattr(axis, "_remove_legend", None)
    if remove_legend is None:
        raise LayoutError("legend: target does not support native Legend removal")
    legend._remove_method = remove_legend  # type: ignore[attr-defined]
    axis.legend_ = legend


def _snapshot_legend_state(
    axis: Axes | _AxesBase,
    existing: Sequence[Legend],
) -> tuple[list[Any], dict[int, tuple[Any, Any, Any, Any]]]:
    """Capture observable Axes and old Legend state for rollback."""

    children = list(getattr(axis, "_children", ()))
    state = {
        id(old): (
            old.axes,
            old.figure,
            getattr(old, "_remove_method", None),
            old.stale_callback,
        )
        for old in existing
    }
    return children, state


def _restore_legend_state(
    axis: Axes | _AxesBase,
    current: Legend | None,
    children_before: list[Any],
    state_before: Mapping[int, tuple[Any, Any, Any, Any]],
    existing: Sequence[Legend],
) -> None:
    """Restore a Legend transaction without invoking the attach seam."""

    children = getattr(axis, "_children", None)
    if children is not None:
        children[:] = children_before
    for old in existing:
        old_axes, old_figure, old_remove, old_stale = state_before[id(old)]
        setattr(old, "axes", old_axes)
        setattr(old, "figure", old_figure)
        setattr(old, "_remove_method", old_remove)
        setattr(old, "stale_callback", old_stale)
    axis.legend_ = current


def _entries(
    ax: Any,
    handles: Sequence[Artist] | None = None,
    labels: Sequence[str] | None = None,
) -> tuple[tuple[Any, ...], tuple[str, ...]]:
    """Resolve normalized handles and string labels for one target Axes."""

    if (handles is None) != (labels is None):
        raise TypeError("handles and labels must be supplied together")
    selected_handles: tuple[Any, ...]
    selected_labels: tuple[str, ...]
    if handles is None:
        getter = getattr(ax, "get_legend_handles_labels", None)
        if getter is None:
            return (), ()
        discovered_handles, discovered_labels = getter()
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
    kwargs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve direct concise legend options against the advanced mapping."""

    selected = _props(props, "legend", kwargs)
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
) -> tuple[tuple[Axes | _AxesBase, tuple[Any, ...], tuple[str, ...]], ...]:
    """Resolve explicit or discovered entries for every target Axes."""

    if (handles is None) != (labels is None):
        raise TypeError("handles and labels must be supplied together")
    if handles is None:
        entries: list[tuple[Axes | _AxesBase, tuple[Any, ...], tuple[str, ...]]] = []
        for axis in target.axes:
            getter = getattr(axis, "get_legend_handles_labels", None)
            if getter is None:
                continue
            discovered_handles, discovered_labels = getter()
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


def _create_single_legend(
    axis: Axes | _AxesBase,
    handles: Sequence[Artist],
    labels: Sequence[str],
    handler_map: Mapping[object, HandlerBase],
    props: Mapping[str, Any],
    *,
    replace: bool,
) -> Legend:
    """Construct and atomically attach one Legend to one Axes target."""

    existing = _existing(axis)
    if existing and not replace:
        raise LayoutError("legend: an existing legend requires replace=True")
    current = axis.get_legend()
    children_before, state_before = _snapshot_legend_state(axis, existing)
    try:
        created = Legend(
            cast(Any, axis),
            tuple(handles),
            tuple(labels),
            handler_map=cast(Any, dict(handler_map)),
            **dict(props),
        )
    except (TypeError, ValueError) as exc:
        raise PlotError("legend: invalid entries, handlers, or options") from exc
    try:
        if replace:
            for old in existing:
                old.remove()
        _attach_legend(axis, created)
    except Exception:
        if created in getattr(axis, "_children", ()):
            created.remove()
        _restore_legend_state(axis, current, children_before, state_before, existing)
        raise
    return created


def _create_cmap_legend(
    ax: Axes,
    colors: Sequence[tuple[float, float, float, float]],
    label: str | None,
    *,
    replace: Any,
    props: Mapping[str, Any] | None,
    kwargs: Mapping[str, Any] | None = None,
    ambient: bool = False,
) -> Legend:
    """Create one gradient Legend from precomputed colors."""

    if not isinstance(ax, Axes):
        raise LayoutError("cmap_legend: ax must be a matplotlib.axes.Axes instance")
    if label is not None and not isinstance(label, str):
        raise PlotError("label must be a string or None")
    selected_replace = ensure_bool(replace, "legend: replace", error=LayoutError)
    if ambient:
        selected_props = _props(props, "legend_colormap", kwargs)
    else:
        selected_props = _legend_props(
            props,
            loc=MISSING,
            frameon=MISSING,
            fancybox=MISSING,
            labelspacing=MISSING,
            handlelength=MISSING,
            kwargs=kwargs,
        )
    if label is None:
        return _create_single_legend(
            ax,
            (),
            (),
            {},
            selected_props,
            replace=selected_replace,
        )
    proxy = Rectangle((0, 0), 1, 1)
    handler = _ColormapHandler(colors)
    return _create_single_legend(
        ax,
        (proxy,),
        (label,),
        {proxy: handler},
        selected_props,
        replace=selected_replace,
    )


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
    **kwargs: Any,
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
    **kwargs: Any,
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
    **kwargs: Any,
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
    **kwargs
        Optional direct Matplotlib Legend constructor properties (e.g.
        ``fontsize``, ``title``, ``framealpha``). Direct keyword arguments are
        merged with and take precedence over ``props``.

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
        kwargs=kwargs,
    )
    entry_sets = _entry_sets(target_plan, handles, labels)

    planned: list[
        tuple[
            Axes | _AxesBase,
            Legend,
            tuple[Legend, ...],
            Legend | None,
            list[Any],
            dict[int, tuple[Any, Any, Any, Any]],
        ]
    ] = []
    for axis, selected_handles, selected_labels in entry_sets:
        if selected_reverse:
            selected_handles = selected_handles[::-1]
            selected_labels = selected_labels[::-1]
        existing = _existing(axis)
        if existing and not selected_replace:
            raise LayoutError("legend: an existing legend requires replace=True")
        try:
            created = Legend(
                cast(Any, axis),
                selected_handles,
                selected_labels,
                handler_map=cast(Any, selected_handlers),
                **selected_props,
            )
        except (TypeError, ValueError) as exc:
            raise PlotError("legend: invalid entries, handlers, or options") from exc
        current = axis.get_legend()
        children_before, state_before = _snapshot_legend_state(axis, existing)
        planned.append(
            (
                axis,
                created,
                existing,
                current if isinstance(current, Legend) else None,
                children_before,
                state_before,
            )
        )

    attempted: list[
        tuple[
            Axes | _AxesBase,
            Legend,
            tuple[Legend, ...],
            Legend | None,
            list[Any],
            dict[int, tuple[Any, Any, Any, Any]],
        ]
    ] = []
    try:
        for axis, created, existing, current, children_before, state_before in planned:
            attempted.append(
                (axis, created, existing, current, children_before, state_before)
            )
            if selected_replace:
                for old in existing:
                    old.remove()
            _attach_legend(axis, created)
    except Exception:
        for (
            axis,
            created,
            existing,
            current,
            children_before,
            state_before,
        ) in reversed(attempted):
            if created in getattr(axis, "_children", ()):
                created.remove()
            _restore_legend_state(
                axis, current, children_before, state_before, existing
            )
        raise
    result = tuple(created for _, created, _, _, _, _ in planned)
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
    **kwargs: Any,
) -> Legend | tuple[Legend, ...]:
    raise AssertionError("signature-only function")


legend.__signature__ = inspect.signature(_legend_signature)  # type: ignore[attr-defined]
legend.__annotations__ = get_type_hints(_legend_signature)


def legends(
    target: Figure | Sequence[Axes] | Mapping[object, Axes],
    *,
    replace: bool = False,
    props: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> tuple[Legend, ...]:
    """Create legends for explicit axes with discoverable entries.

    Parameters
    ----------
    target
        Figure, Axes sequence, or string-keyed Axes mapping to inspect.
    replace
        Remove existing legends only when explicitly set to ``True``.
    props
        Optional finite Matplotlib Legend constructor properties.
    **kwargs
        Optional direct Matplotlib Legend constructor properties. Direct
        keyword arguments are merged with and take precedence over ``props``.

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
        target_plan = normalize_axes(tuple(target.axes), operation="legends")
    else:
        target_plan = normalize_axes(target, operation="legends")
    axes = target_plan.axes
    entries: list[
        tuple[Axes | _AxesBase, tuple[Any, ...], tuple[str, ...], tuple[Legend, ...]]
    ] = []
    for axis in axes:
        getter = getattr(axis, "get_legend_handles_labels", None)
        if getter is None:
            continue
        handles, labels = getter()
        if not handles:
            continue
        existing = _existing(axis)
        if existing and not replace:
            raise LayoutError("an existing legend requires replace=True")
        entries.append((axis, tuple(handles), tuple(labels), existing))
    planned: list[tuple[Axes | _AxesBase, Legend, tuple[Legend, ...]]] = []
    snapshots: list[
        tuple[
            Axes | _AxesBase,
            Legend | None,
            list[Any],
            dict[int, tuple[Any, Any, Any, Any]],
            tuple[Legend, ...],
        ]
    ] = []
    for axis, stored_handles, stored_labels, existing in entries:
        current = axis.get_legend()
        children_before, state_before = _snapshot_legend_state(axis, existing)
        try:
            item = Legend(
                cast(Any, axis), stored_handles, stored_labels, **selected_props
            )
        except (TypeError, ValueError) as exc:
            raise PlotError("legends: invalid entries or options") from exc
        planned.append((axis, item, existing))
        snapshots.append(
            (
                axis,
                current if isinstance(current, Legend) else None,
                children_before,
                state_before,
                existing,
            )
        )
    attempted: list[int] = []
    try:
        for index, (axis, item, existing) in enumerate(planned):
            attempted.append(index)
            if replace:
                for old in existing:
                    old.remove()
            _attach_legend(axis, item)
    except Exception:
        for index in reversed(attempted):
            axis, item, _ = planned[index]
            if item in getattr(axis, "_children", ()):
                item.remove()
            _, current, children_before, state_before, existing = snapshots[index]
            _restore_legend_state(
                axis, current, children_before, state_before, existing
            )
        raise
    return tuple(item for _, item, _ in planned)


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


def _effective_stripes(value: Any, name: str) -> int:
    """Validate a stripe count and apply the bounded legend limit."""

    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise PlotError(f"{name} must be a positive integer")
    count = int(value)
    if count < 1:
        raise PlotError(f"{name} must be a positive integer")
    return min(count, _MAX_NUM_STRIPES)


def _resolve_colormap(cmap: str | Colormap) -> Colormap:
    """Resolve a colormap name without mutating a caller-owned colormap."""

    if isinstance(cmap, str):
        if not cmap.strip():
            raise PlotError("cmap must be a non-empty colormap name")
        try:
            return mpl.colormaps.get_cmap(cmap)
        except (TypeError, ValueError) as exc:
            raise PlotError(f"unknown Matplotlib colormap: {cmap!r}") from exc
    if isinstance(cmap, Colormap):
        return cmap
    raise PlotError("cmap must be a colormap name or Colormap")


def _sample_colormap(
    selected: Colormap,
    values: np.ndarray,
    reverse: bool,
) -> tuple[tuple[float, float, float, float], ...]:
    """Sample RGBA colors and reverse the sampled rows when requested."""

    try:
        rgba = np.asarray(selected(values), dtype=float)
    except Exception as exc:
        raise PlotError("colormap must return RGBA values") from exc
    if rgba.shape != (len(values), 4) or not np.all(np.isfinite(rgba)):
        raise PlotError("colormap must return finite RGBA values")
    if reverse:
        rgba = rgba[::-1]
    rows: list[tuple[float, float, float, float]] = []
    for row in rgba:
        rows.append((float(row[0]), float(row[1]), float(row[2]), float(row[3])))
    return tuple(rows)


def _colormap_values(
    cmap: str | Colormap,
    stripes: int,
    norm: NormalizeSpec | None,
    reverse: bool,
) -> tuple[tuple[float, float, float, float], ...]:
    """Build deterministic canonical RGBA stripe colors."""

    stripes = _effective_stripes(stripes, "stripes")
    if not isinstance(reverse, bool):
        raise PlotError("reverse must be a boolean")
    selected = _resolve_colormap(cmap)
    positions = np.linspace(0.0, 1.0, stripes)
    if norm is not None:
        selected_norm: Any = norm
        if isinstance(norm, Normalize):
            try:
                selected_norm = copy.copy(norm)
            except Exception as exc:  # pragma: no cover - defensive boundary
                raise PlotError("norm could not be copied safely") from exc
            if selected_norm.vmin is None or selected_norm.vmax is None:
                raise PlotError("norm bounds must be finite and increasing")
            vmin = ensure_finite_real(selected_norm.vmin, "norm.vmin", error=PlotError)
            vmax = ensure_finite_real(selected_norm.vmax, "norm.vmax", error=PlotError)
            if vmin >= vmax:
                raise PlotError("norm bounds must be finite and increasing")
        elif not callable(norm):
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
            vmin = ensure_finite_real(bounds[0], "norm.vmin", error=PlotError)
            vmax = ensure_finite_real(bounds[1], "norm.vmax", error=PlotError)
            if vmin >= vmax:
                raise PlotError("norm bounds must be finite and increasing")
            selected_norm = Normalize(vmin=vmin, vmax=vmax, clip=True)
        try:
            positions = np.asarray(selected_norm(positions, clip=True), dtype=float)
        except Exception as exc:
            raise PlotError("norm must return finite values") from exc
        if positions.shape != (stripes,) or not np.all(np.isfinite(positions)):
            raise PlotError("norm must return finite values with the stripe shape")
        positions = np.clip(positions, 0.0, 1.0)
    return _sample_colormap(selected, positions, reverse)


def _legacy_colormap_values(
    cmap: Any,
    num_stripes: Any,
    vmin: Any,
    vmax: Any,
    reverse: Any,
) -> tuple[tuple[float, float, float, float], ...]:
    """Build v0.2-compatible RGBA colors for the legacy function route."""

    if not isinstance(cmap, str) or not cmap.strip():
        raise PlotError("cmap must be a non-empty colormap name")
    if not isinstance(reverse, bool):
        raise PlotError("reverse must be a boolean")
    stripes = _effective_stripes(num_stripes, "num_stripes")
    selected_vmin = ensure_finite_real(vmin, "vmin", error=PlotError)
    selected_vmax = ensure_finite_real(vmax, "vmax", error=PlotError)
    selected = _resolve_colormap(cmap)
    values = np.linspace(selected_vmin, selected_vmax, stripes)
    return _sample_colormap(selected, values, reverse)


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
    **kwargs: Any,
) -> Legend:
    """Create one native Legend entry containing a horizontal color gradient.

    Parameters
    ----------
    ax
        Explicit target Axes.
    cmap
        Colormap name or native Colormap object.
    label
        Optional label for the gradient entry. ``None`` creates an empty
        native Legend and does not render a gradient.
    stripes
        Positive requested stripe count. Counts above 256 are clamped to 256
        before sampling and rendering.
    norm
        Optional normalizer applied to ``linspace(0, 1, N_effective)`` with
        ``clip=True``. A pair is interpreted as ``(vmin, vmax)`` for a
        read-only ``Normalize`` operation; it is not a legacy raw-value
        alias.
    reverse
        Reverse the final sampled RGBA sequence from left to right.
    replace
        Remove an existing legend only when explicitly set to ``True``.
    props
        Optional finite Matplotlib Legend constructor properties.
    **kwargs
        Optional direct Matplotlib Legend constructor properties. Direct
        keyword arguments are merged with and take precedence over ``props``.

    Returns
    -------
    matplotlib.legend.Legend
        The native local Legend.

    Raises
    ------
    PlotError, LayoutError, OptionError
        If colormap, normalization, stripe count, target, replacement, or
        properties are invalid.

    Notes
    -----
    The gradient is rendered by one module-level local handler and one proxy
    handle. It does not modify Matplotlib's default handler map or add a
    colormap proxy to the Axes. When ``replace`` is false, an existing Legend
    raises ``LayoutError``; when it is true, the existing Legend is replaced
    transactionally.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, ax = gs.subplots()
    >>> item = gs.cmap_legend(ax, label="intensity")
    >>> item.axes is ax
    True
    >>> figure.clear()
    """

    stripes = _effective_stripes(stripes, "stripes")
    if label is not None and not isinstance(label, str):
        raise PlotError("label must be a string or None")
    colors = _colormap_values(cmap, stripes, norm, reverse)
    return _create_cmap_legend(
        ax,
        colors,
        label,
        replace=replace,
        props=props,
        kwargs=kwargs,
    )


__all__ = ["legend", "legends", "legend_entries", "cmap_legend"]
