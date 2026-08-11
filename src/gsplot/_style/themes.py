"""Explicit Figure/Axes theme operations with no rcParams mutation."""

from __future__ import annotations

from typing import Any

from matplotlib.axes import Axes
from matplotlib.colors import is_color_like, to_rgba
from matplotlib.figure import Figure

from .._core.errors import PlotError
from .._core.types import ColorSpec, Theme


def _validate_color(value: ColorSpec, name: str) -> None:
    """Validate a final Matplotlib color at the mutation boundary."""

    if not is_color_like(value):
        raise PlotError(f"{name} must be a valid Matplotlib color")
    to_rgba(value)


def fig_facecolor(fig: Figure, color: ColorSpec) -> None:
    """Set one explicit Figure patch facecolor."""

    if not isinstance(fig, Figure):
        raise PlotError("fig must be a Matplotlib Figure")
    _validate_color(color, "color")
    fig.patch.set_facecolor(color)


def _apply_axes_theme(axis: Axes, theme: Theme) -> None:
    """Apply already validated axes fields to one Axes."""

    if theme.axes_facecolor is not None:
        axis.set_facecolor(theme.axes_facecolor)
    if theme.text_color is not None:
        axis.xaxis.label.set_color(theme.text_color)
        axis.yaxis.label.set_color(theme.text_color)
        axis.title.set_color(theme.text_color)
        for label in (*axis.get_xticklabels(), *axis.get_yticklabels()):
            label.set_color(theme.text_color)
    if theme.spine_color is not None:
        for spine in axis.spines.values():
            spine.set_color(theme.spine_color)
    if theme.tick_color is not None:
        axis.tick_params(axis="both", colors=theme.tick_color)
    if theme.grid is not None:
        grid_kwargs: dict[str, Any] = {"visible": theme.grid}
        if theme.grid_color is not None:
            grid_kwargs["color"] = theme.grid_color
        if theme.grid_alpha is not None:
            grid_kwargs["alpha"] = theme.grid_alpha
        axis.grid(**grid_kwargs)
    elif theme.grid_color is not None or theme.grid_alpha is not None:
        grid_kwargs = {"visible": True}
        if theme.grid_color is not None:
            grid_kwargs["color"] = theme.grid_color
        if theme.grid_alpha is not None:
            grid_kwargs["alpha"] = theme.grid_alpha
        axis.grid(**grid_kwargs)


def set_theme(target: Figure | Axes, theme: Theme) -> None:
    """Apply a validated Theme only to an explicit Figure or Axes."""

    if not isinstance(theme, Theme):
        raise PlotError("theme must be a gsplot Theme")
    if isinstance(target, Axes):
        if theme.figure_facecolor is not None:
            raise PlotError("figure_facecolor requires a Figure target")
        _apply_axes_theme(target, theme)
        return
    if not isinstance(target, Figure):
        raise PlotError("target must be a Matplotlib Figure or Axes")
    if theme.figure_facecolor is not None:
        target.patch.set_facecolor(theme.figure_facecolor)
    for axis in tuple(target.axes):
        _apply_axes_theme(axis, theme)


__all__ = ["fig_facecolor", "set_theme"]
