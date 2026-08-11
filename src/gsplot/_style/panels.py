"""Renderer-neutral explicit panel labels."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from matplotlib.axes import Axes
from matplotlib.text import Text

from .._core.errors import LayoutError, PlotError
from .axes import _validate_props

_PANEL_PROPS = frozenset(
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


def panel_labels(
    target: Sequence[Axes] | Mapping[str, Axes],
    labels: Sequence[str] | None = None,
    *,
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
    texts: list[Text] = []
    for axis, label in zip(axes, selected_labels):
        texts.append(
            axis.text(0.02, 0.98, label, transform=axis.transAxes, **selected_props)
        )
    return tuple(texts)


__all__ = ["panel_labels"]
