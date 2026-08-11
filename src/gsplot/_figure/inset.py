"""Explicit parent-Axes inset creation."""

from __future__ import annotations

from typing import Any, cast

from matplotlib.axes import Axes
from mpl_toolkits.axes_grid1.inset_locator import inset_axes as _inset_axes

from .._core.errors import LayoutError
from .._core.types import InsetSpec


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
    >>> child.set_title("inset")
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


__all__ = ["inset_axes"]
