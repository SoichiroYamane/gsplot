"""Lazy canonical explicit-target styling adapters."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = [
    "style_axes",
    "title",
    "suptitle",
    "minor_ticks",
    "box_aspect",
    "panel_labels",
    "fig_facecolor",
    "legend",
    "legends",
    "legend_entries",
    "cmap_legend",
    "set_theme",
    "paper",
]

if TYPE_CHECKING:
    style_axes: Any
    title: Any
    suptitle: Any
    minor_ticks: Any
    box_aspect: Any
    panel_labels: Any
    fig_facecolor: Any
    legend: Any
    legends: Any
    legend_entries: Any
    cmap_legend: Any
    set_theme: Any
    paper: Any


_MODULES = {
    "style_axes": ("gsplot._style.axes", "style_axes"),
    "title": ("gsplot._style.axes", "title"),
    "suptitle": ("gsplot._style.axes", "suptitle"),
    "minor_ticks": ("gsplot._style.axes", "minor_ticks"),
    "box_aspect": ("gsplot._style.axes", "box_aspect"),
    "panel_labels": ("gsplot._style.panels", "panel_labels"),
    "fig_facecolor": ("gsplot._style.themes", "fig_facecolor"),
    "legend": ("gsplot._style.legends", "legend"),
    "legends": ("gsplot._style.legends", "legends"),
    "legend_entries": ("gsplot._style.legends", "legend_entries"),
    "cmap_legend": ("gsplot._style.legends", "cmap_legend"),
    "set_theme": ("gsplot._style.themes", "set_theme"),
    "paper": ("gsplot._style.paper", "paper"),
}


def __getattr__(name: str) -> Any:
    """Import one styling adapter only when requested."""

    try:
        module_name, attribute_name = _MODULES[name]
    except KeyError as error:
        raise AttributeError(
            f"module 'gsplot._style' has no attribute {name!r}"
        ) from error
    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value
