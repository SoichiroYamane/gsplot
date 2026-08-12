"""Renderer-neutral explicit panel labels."""

from __future__ import annotations

import inspect
from collections.abc import Mapping, Sequence
from typing import Any, Literal, Protocol, cast, get_type_hints, overload

import numpy as np
from matplotlib.axes import Axes
from matplotlib.backend_bases import RendererBase
from matplotlib.figure import Figure
from matplotlib.text import Text
from matplotlib.transforms import ScaledTranslation

from .._core.errors import LayoutError, PlotError
from .._core.options import MISSING
from .._core.plans import TargetPlan
from .._core.targets import normalize_axes, resolve_target_mapping
from .._core.types import AxesTarget
from .._core.validation import ensure_positive
from .axes import _validate_props

_PANEL_PROPS = frozenset(
    {
        "alpha",
        "color",
        "fontfamily",
        "fontproperties",
        "fontsize",
        "size",
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

_INDEX_INSIDE_GAP_POINTS = 4.0
_INDEX_OUTSIDE_GAP_POINTS = 6.0


class _RendererCanvas(Protocol):
    """Canvas capability required after a synchronous draw."""

    def get_renderer(self) -> RendererBase:
        """Return the renderer used by the latest draw."""
        ...


def _panel_targets(target: Sequence[Axes] | Mapping[str, Axes]) -> tuple[Axes, ...]:
    """Validate the ordered panel target required by the API."""

    if isinstance(target, Mapping):
        axes = tuple(target.values())
    elif isinstance(target, np.ndarray):
        axes = tuple(target.flat)
    elif isinstance(target, Sequence) and not isinstance(target, (str, bytes)):
        axes = tuple(target)
    else:
        raise LayoutError("target must be an Axes sequence or mapping")
    if not axes or any(not isinstance(axis, Axes) for axis in axes):
        raise LayoutError("target must contain at least one Matplotlib Axes")
    return axes


def _label_for_index(index: int) -> str:
    """Return A..Z, AA.. deterministic panel labels."""

    value = index + 1
    result = ""
    while value:
        value, remainder = divmod(value - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def _concise_label_for_index(index: int) -> str:
    """Return ``(a)`` through ``(z)``, then bijective lowercase labels."""

    return f"({_label_for_index(index).lower()})"


def _prepare_index(
    target: TargetPlan,
    labels: Sequence[str] | Mapping[object, str] | None,
    *,
    loc: Any,
    size: Any = MISSING,
    props: Mapping[str, object] | None = None,
) -> tuple[tuple[str, ...], dict[str, Any], Literal["in", "out"]]:
    """Validate every concise panel-index input without adding Text artists."""

    if not isinstance(loc, str) or loc not in {"in", "out"}:
        raise LayoutError("index: loc must be 'in' or 'out'")
    selected_loc = cast(Literal["in", "out"], loc)
    if labels is None:
        selected_labels = tuple(
            _concise_label_for_index(position) for position in range(len(target.axes))
        )
    elif isinstance(labels, Mapping):
        selected_labels = resolve_target_mapping(target, labels, name="labels")
    elif isinstance(labels, Sequence) and not isinstance(labels, (str, bytes)):
        selected_labels = tuple(labels)
        if len(selected_labels) != len(target.axes):
            raise LayoutError("index: labels must match the target length")
    else:
        raise LayoutError("index: labels must be an ordered sequence or mapping")
    if any(not isinstance(label, str) for label in selected_labels):
        raise LayoutError("index: labels must be strings")

    selected_props = _validate_props(props, _PANEL_PROPS, "index")
    if "fontsize" in selected_props and "size" in selected_props:
        raise LayoutError("index: props cannot contain both 'fontsize' and 'size'")
    if size is not MISSING:
        if "fontsize" in selected_props or "size" in selected_props:
            raise LayoutError("index: size conflicts with a props font-size field")
        selected_props["fontsize"] = size
    elif "fontsize" not in selected_props and "size" not in selected_props:
        selected_props["fontsize"] = "large"
    size_key = "size" if "size" in selected_props else "fontsize"
    selected_size = selected_props[size_key]
    if not isinstance(selected_size, str):
        selected_props[size_key] = ensure_positive(
            selected_size, f"index: {size_key}", error=LayoutError
        )
    if "ha" not in selected_props and "horizontalalignment" not in selected_props:
        selected_props["ha"] = "left"
    if "va" not in selected_props and "verticalalignment" not in selected_props:
        selected_props["va"] = "top" if selected_loc == "in" else "bottom"
    try:
        for text in selected_labels:
            Text(0, 1, text, **selected_props)
    except (TypeError, ValueError) as exc:
        raise PlotError("index: invalid text options") from exc
    return selected_labels, selected_props, selected_loc


def _apply_index(
    target: TargetPlan,
    labels: tuple[str, ...],
    props: Mapping[str, Any],
    loc: Literal["in", "out"],
) -> Text | tuple[Text, ...]:
    """Attach one completely preflighted panel index per target Axes."""

    created: list[Text] = []
    try:
        for axis, text in zip(target.axes, labels):
            if loc == "in":
                transform = axis.transAxes + ScaledTranslation(
                    _INDEX_INSIDE_GAP_POINTS / 72,
                    -_INDEX_INSIDE_GAP_POINTS / 72,
                    target.figure.dpi_scale_trans,
                )
                artist = axis.text(
                    0,
                    1,
                    text,
                    transform=transform,
                    **props,
                )
            else:
                artist = axis.annotate(
                    text,
                    xy=(0, 1),
                    xycoords=(axis.yaxis.label, axis.transAxes),
                    xytext=(0, _INDEX_OUTSIDE_GAP_POINTS),
                    textcoords="offset points",
                    **props,
                )
            created.append(artist)
    except Exception:
        for item in reversed(created):
            item.remove()
        raise
    result = tuple(created)
    return result[0] if target.single else result


@overload
def index(
    target: Axes,
    labels: Sequence[str] | Mapping[object, str] | None = None,
    *,
    loc: Literal["in", "out"] = "out",
    size: float | str = "large",
    props: Mapping[str, object] | None = None,
) -> Text: ...


@overload
def index(
    target: AxesTarget,
    labels: Sequence[str] | Mapping[object, str] | None = None,
    *,
    loc: Literal["in", "out"] = "out",
    size: float | str = "large",
    props: Mapping[str, object] | None = None,
) -> Text | tuple[Text, ...]: ...


def index(
    target: AxesTarget,
    labels: Sequence[str] | Mapping[object, str] | None = None,
    *,
    loc: Any = "out",
    size: Any = MISSING,
    props: Mapping[str, object] | None = None,
) -> Text | tuple[Text, ...]:
    """Add deterministic lowercase panel indexes to explicit Axes.

    Parameters
    ----------
    target
        One Axes or a deterministic same-Figure collection of Axes.
    labels
        Optional ordered labels or an exact-key mapping. Omitted values are
        generated as ``(a)`` through ``(z)``, then ``(aa)`` onward.
    loc
        ``"in"`` places text four points right/down from the upper-left Axes
        corner. ``"out"`` aligns the text's left edge with the rendered left
        edge of the y-axis label and places it six points above the Axes.
    size
        Matplotlib font size. The default is the historical ``"large"``.
    props
        Optional closed Text property mapping. A font-size field conflicts
        with a separately supplied ``size``.

    Returns
    -------
    matplotlib.text.Text or tuple of Text
        Native Text artists in normalized target order.

    Raises
    ------
    LayoutError, PlotError
        If targets, labels, placement, size, or text properties are invalid.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, axes = gs.subplots(1, 2)
    >>> labels = gs.index(axes, loc="in")
    >>> tuple(item.get_text() for item in labels)
    ('(a)', '(b)')
    >>> figure.clear()
    """

    target_plan = normalize_axes(target, operation="index")
    prepared = _prepare_index(
        target_plan,
        labels,
        loc=loc,
        size=size,
        props=props,
    )
    return _apply_index(target_plan, *prepared)


def _index_signature(
    target: AxesTarget,
    labels: Sequence[str] | Mapping[object, str] | None = None,
    *,
    loc: Literal["in", "out"] = "out",
    size: float | str = "large",
    props: Mapping[str, object] | None = None,
) -> Text | tuple[Text, ...]:
    raise AssertionError("signature-only function")


index.__signature__ = inspect.signature(_index_signature)  # type: ignore[attr-defined]
index.__annotations__ = get_type_hints(_index_signature)


def panel_labels(
    target: Sequence[Axes] | Mapping[str, Axes],
    labels: Sequence[str] | None = None,
    *,
    loc: str = "corner",
    props: Mapping[str, Any] | None = None,
) -> tuple[Text, ...]:
    """Add deterministic labels to an explicit ordered panel collection.

    Parameters
    ----------
    target
        Ordered Axes sequence or mapping whose values define panel order.
    labels
        Optional labels with exactly one string per target Axes.  Omitted
        labels are generated as ``A`` through ``Z``, then ``AA`` onward.
    loc
        Placement mode: ``"corner"`` places labels at a stable axes-relative
        corner, while ``"in"`` and ``"out"`` use the rendered Axes bounds to
        reproduce publication-style placement.
    props
        Finite Matplotlib Text property mapping.

    Returns
    -------
    tuple[matplotlib.text.Text, ...]
        Native text artists added to the target Axes objects.

    Raises
    ------
    LayoutError, PlotError
        If the target, labels, or property mapping is invalid.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, axes = gs.subplots(ncols=2)
    >>> labels = gs.panel_labels(axes, labels=("A", "B"))
    >>> len(labels)
    2
    >>> figure.clear()
    """

    axes = _panel_targets(target)
    if loc not in {"corner", "in", "out"}:
        raise LayoutError("loc must be 'corner', 'in', or 'out'")
    if labels is None:
        selected_labels = tuple(_label_for_index(index) for index in range(len(axes)))
    else:
        if isinstance(labels, (str, bytes)):
            raise LayoutError("labels must be a sequence of strings")
        selected_labels = tuple(labels)
        if len(selected_labels) != len(axes):
            raise LayoutError("labels must have the same length as target")
        if any(not isinstance(label, str) for label in selected_labels):
            raise LayoutError("panel labels must be strings")
    selected_props = _validate_props(props, _PANEL_PROPS, "panel_labels")
    selected_props.setdefault("ha", "left")
    selected_props.setdefault("va", "top")
    if loc == "corner":
        texts = [
            axis.text(
                0.02,
                0.98,
                label,
                transform=axis.transAxes,
                **selected_props,
            )
            for axis, label in zip(axes, selected_labels)
        ]
        return tuple(texts)

    figure = axes[0].figure
    if not isinstance(figure, Figure) or any(
        axis.figure is not figure for axis in axes
    ):
        raise LayoutError("rendered panel labels require Axes from one Figure")
    figure.canvas.draw()
    renderer = cast(_RendererCanvas, figure.canvas).get_renderer()
    width, height = figure.bbox.width, figure.bbox.height
    padding = (30, -30) if loc == "in" else (0, -5)
    texts = []
    for axis, label in zip(axes, selected_labels):
        bounds = (
            axis.get_window_extent(renderer)
            if loc == "in"
            else axis.get_tightbbox(renderer)
        )
        if bounds is None:
            raise LayoutError("could not determine the rendered Axes bounds")
        x = (bounds.x0 + padding[0]) / width
        y = (bounds.y0 + bounds.height + padding[1]) / height
        texts.append(
            figure.text(
                x,
                y,
                label,
                transform=figure.transFigure,
                **selected_props,
            )
        )
    return tuple(texts)


__all__ = ["panel_labels", "index"]
