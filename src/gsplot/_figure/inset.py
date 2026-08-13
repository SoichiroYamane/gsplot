"""Explicit parent-Axes inset creation and zoom indicators."""

from __future__ import annotations

from typing import Any, Literal, cast

from matplotlib.axes import Axes
from matplotlib.patches import Patch
from matplotlib.transforms import TransformedBbox
from mpl_toolkits.axes_grid1.inset_locator import BboxConnector, BboxPatch
from mpl_toolkits.axes_grid1.inset_locator import inset_axes as _inset_axes

from .._core.errors import LayoutError
from .._core.types import AxisSpec, InsetSpec, LabelRecord, Limit, ZoomCorners
from .._core.validation import ensure_finite_real
from .._style.axes import _apply_axis_spec
from .._style.paper import paper

_Zoom = bool | ZoomCorners


def _placement(
    value: tuple[float, float, float, float] | InsetSpec,
) -> InsetSpec:
    """Validate concise placement without changing the parent Axes."""

    if isinstance(value, InsetSpec):
        return value
    if not isinstance(value, tuple) or len(value) != 4:
        raise LayoutError("inset: bounds must be a four-value tuple or InsetSpec")
    selected = tuple(
        ensure_finite_real(item, f"inset: bounds[{index}]", error=LayoutError)
        for index, item in enumerate(value)
    )
    left, bottom, width, height = selected
    if left < 0 or bottom < 0:
        raise LayoutError("inset: bounds left and bottom must be non-negative")
    if width <= 0 or height <= 0:
        raise LayoutError("inset: bounds width and height must be positive")
    if left + width > 1 or bottom + height > 1:
        raise LayoutError("inset: bounds must fit within the parent Axes")
    return InsetSpec(bounds=cast(tuple[float, float, float, float], selected))


def _label_spec(value: LabelRecord | None) -> AxisSpec | None:
    """Validate one optional concise inset label record."""

    if value is None:
        return None
    if isinstance(value, (str, bytes)):
        raise LayoutError("inset: label must be a two- or four-field record")
    try:
        fields = tuple(value)
    except TypeError as exc:
        raise LayoutError("inset: label must be a two- or four-field record") from exc
    if len(fields) not in {2, 4}:
        raise LayoutError("inset: label must be a two- or four-field record")
    if not isinstance(fields[0], str) or not isinstance(fields[1], str):
        raise LayoutError("inset: label texts must be strings")
    try:
        return AxisSpec(
            xlabel=fields[0],
            ylabel=fields[1],
            xlim=None if len(fields) == 2 else cast(Limit | None, fields[2]),
            ylim=None if len(fields) == 2 else cast(Limit | None, fields[3]),
            xminor=True,
            yminor=True,
            xlabelpad=0,
            ylabelpad=0,
        )
    except LayoutError as exc:
        raise LayoutError(f"inset: label: {exc}") from exc


def _zoom(value: _Zoom) -> _Zoom:
    """Validate automatic or exact-pair zoom selection."""

    if isinstance(value, bool):
        return value
    if not isinstance(value, tuple) or len(value) != 2:
        raise LayoutError("inset: zoom must be false, true, or two corner pairs")
    pairs: list[tuple[int, int]] = []
    for pair in value:
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise LayoutError("inset: zoom must contain two corner pairs")
        if any(
            type(corner) is not int or corner not in {1, 2, 3, 4} for corner in pair
        ):
            raise LayoutError("inset: zoom corners must be integers from 1 through 4")
        pairs.append((pair[0], pair[1]))
    if pairs[0] == pairs[1]:
        raise LayoutError("inset: zoom corner pairs must be distinct")
    return cast(ZoomCorners, tuple(pairs))


def _manual_zoom_indicator(
    parent: Axes,
    child: Axes,
    corners: ZoomCorners,
    *,
    color: Any = "black",
    alpha: float = 0.3,
    zorder: float,
) -> None:
    """Attach one rectangle and two requested connectors to the parent."""

    rectangle = TransformedBbox(child.viewLim, parent.transData)
    artists: list[Patch] = [
        BboxPatch(
            rectangle,
            fill=False,
            edgecolor=color,
            alpha=alpha,
            zorder=zorder,
        )
    ]
    for parent_corner, child_corner in corners:
        connector = BboxConnector(
            child.bbox,
            rectangle,
            loc1=child_corner,
            loc2=parent_corner,
            color=color,
            alpha=alpha,
            zorder=zorder,
        )
        connector.set_clip_on(False)
        artists.append(connector)
    for artist in artists:
        artist.set_in_layout(False)
        parent.add_patch(artist)


def _exclude_indicator_from_layout(indicator: Any) -> None:
    """Exclude supported Matplotlib indicator return forms from layout."""

    if hasattr(indicator, "set_in_layout"):
        indicator.set_in_layout(False)
        return
    if isinstance(indicator, (tuple, list)):
        for item in indicator:
            _exclude_indicator_from_layout(item)


def inset_axes(parent: Axes, spec: InsetSpec) -> Axes:
    """Create one placement-only inset below an explicit parent Axes.

    Parameters
    ----------
    parent
        The Matplotlib Axes that owns the child inset.
    spec
        Validated placement values from :class:`gsplot.InsetSpec`.

    Returns
    -------
    matplotlib.axes.Axes
        The newly created child Axes.

    Raises
    ------
    LayoutError
        If the parent, specification, or requested placement is invalid.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, axes = gs.subplots()
    >>> child = gs.inset_axes(axes, gs.InsetSpec(bounds=(0.6, 0.6, 0.3, 0.3)))
    >>> _ = child.set_title("inset")
    >>> figure.clear()
    """

    if not isinstance(parent, Axes):
        raise LayoutError("parent must be a Matplotlib Axes")
    if not isinstance(spec, InsetSpec):
        raise LayoutError("spec must be a gsplot InsetSpec")
    if spec.bounds is not None:
        return cast(Axes, parent.inset_axes(spec.bounds))
    kwargs: dict[str, Any] = {
        "width": spec.width,
        "height": spec.height,
        "loc": spec.loc,
        "borderpad": spec.borderpad,
    }
    if spec.bbox_to_anchor is not None:
        kwargs["bbox_to_anchor"] = spec.bbox_to_anchor
    try:
        return cast(Axes, _inset_axes(parent, **kwargs))
    except (TypeError, ValueError) as exc:
        raise LayoutError("could not create the requested inset Axes") from exc


def inset(
    parent: Axes,
    bounds: tuple[float, float, float, float] | InsetSpec,
    *,
    label: LabelRecord | None = None,
    zoom: bool | ZoomCorners = False,
    style: Literal["paper"] | None = "paper",
    zorder: float = 5,
    zoom_zorder: float | None = None,
) -> Axes:
    """Create a publication-styled inset on an explicit parent Axes.

    Parameters
    ----------
    parent
        Matplotlib Axes that owns the child and optional zoom indicator.
    bounds
        Normalized ``(left, bottom, width, height)`` parent-Axes fractions, or
        an advanced :class:`gsplot.InsetSpec` placement.
    label
        Optional ``(xlabel, ylabel)`` or ``(xlabel, ylabel, xlim, ylim)``
        record. Label padding is zero points.
    zoom
        ``False`` for no indicator, ``True`` for Matplotlib's automatic
        indicator, or exactly two ``(parent_corner, inset_corner)`` pairs.
        Corner identifiers are 1 upper-right, 2 upper-left, 3 lower-left, and
        4 lower-right.
    style
        Apply the target-local ``"paper"`` profile by default, or use ``None``
        to retain ambient Matplotlib styling.
    zorder
        Finite child Axes z-order, defaulting to ``5``.
    zoom_zorder
        Optional finite indicator z-order. The default is ``zorder - 0.01``
        and is valid only when ``zoom`` is enabled.

    Returns
    -------
    matplotlib.axes.Axes
        Newly created native child Axes.

    Raises
    ------
    LayoutError
        If the parent, placement, label, zoom controls, style, or z-orders are
        invalid, or Matplotlib cannot create the requested inset.

    Notes
    -----
    Every option is validated before child creation. Indicator artists belong
    to the parent Axes and track the child's limits. This function does not run
    a Figure layout engine or change global Matplotlib state.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, ax = gs.subplots()
    >>> child = gs.inset(ax, (0.6, 0.6, 0.3, 0.3), label=("x", "y"))
    >>> child.figure is figure
    True
    >>> figure.clear()
    """

    if not isinstance(parent, Axes):
        raise LayoutError("inset: parent must be a Matplotlib Axes")
    spec = _placement(bounds)
    selected_label = _label_spec(label)
    selected_zoom = _zoom(zoom)
    if style is not None and (not isinstance(style, str) or style != "paper"):
        raise LayoutError("inset: style must be 'paper' or None")
    selected_zorder = ensure_finite_real(zorder, "inset: zorder", error=LayoutError)
    if zoom_zorder is not None and selected_zoom is False:
        raise LayoutError("inset: zoom_zorder requires zoom")
    selected_zoom_zorder = (
        selected_zorder - 0.01
        if zoom_zorder is None
        else ensure_finite_real(zoom_zorder, "inset: zoom_zorder", error=LayoutError)
    )

    child = inset_axes(parent, spec)
    child.set_in_layout(False)
    child.set_zorder(selected_zorder)
    if style == "paper":
        paper(child)
    if selected_label is not None:
        _apply_axis_spec(child, selected_label)
    if selected_zoom is True:
        _exclude_indicator_from_layout(
            parent.indicate_inset_zoom(
                child,
                edgecolor="black",
                alpha=0.3,
                zorder=selected_zoom_zorder,
            )
        )
    elif isinstance(selected_zoom, tuple):
        _manual_zoom_indicator(
            parent,
            child,
            selected_zoom,
            zorder=selected_zoom_zorder,
        )
    return child


__all__ = ["inset", "inset_axes"]
