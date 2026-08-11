"""Lazy adapters for the 0.3.x package-root API.

The compatibility layer is deliberately one-way: it may import historical
modules when a legacy name is first used, while canonical implementation
modules must never import this module. Keeping the lookup lazy prevents a
plain ``import gsplot`` from importing pyplot, configuring Matplotlib, or
loading the legacy configuration singleton.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any, Final

_LEGACY_EXPORTS: Final[dict[str, tuple[str, str]]] = {
    "get_cmap": ("gsplot.color.colormap", "get_cmap"),
    "load_file": ("gsplot.data.load_file", "load_file"),
    "load_file_fast": ("gsplot.data.load_file", "load_file_fast"),
    "axes": ("gsplot.figure.axes", "axes"),
    "axes_inset": ("gsplot.figure.axes_inset", "axes_inset"),
    "axes_inset_padding": ("gsplot.figure.axes_inset", "axes_inset_padding"),
    "get_figure_size": ("gsplot.figure.figure_tools", "get_figure_size"),
    "show": ("gsplot.figure.show", "show"),
    "hello_world": ("gsplot.hello_world.hello_world", "hello_world"),
    "config_load": ("gsplot.config.config", "config_load"),
    "config_dict": ("gsplot.config.config", "config_dict"),
    "config_entry_option": ("gsplot.config.config", "config_entry_option"),
    "home": ("gsplot.path.path", "home"),
    "pwd": ("gsplot.path.path", "pwd"),
    "pwd_move": ("gsplot.path.path", "pwd_move"),
    "pwd_main": ("gsplot.path.path", "pwd_main"),
    "line": ("gsplot.plot.line", "line"),
    "line_colormap_solid": (
        "gsplot.plot.line_colormap_solid",
        "line_colormap_solid",
    ),
    "line_colormap_dashed": (
        "gsplot.plot.line_colormap_dashed",
        "line_colormap_dashed",
    ),
    "scatter": ("gsplot.plot.scatter", "scatter"),
    "scatter_colormap": ("gsplot.plot.scatter_colormap", "scatter_colormap"),
    "graph_square": ("gsplot.style.graph", "graph_square"),
    "graph_square_axes": ("gsplot.style.graph", "graph_square_axes"),
    "graph_white": ("gsplot.style.graph", "graph_white"),
    "graph_white_axes": ("gsplot.style.graph", "graph_white_axes"),
    "graph_transparent": ("gsplot.style.graph", "graph_transparent"),
    "graph_transparent_axes": (
        "gsplot.style.graph",
        "graph_transparent_axes",
    ),
    "graph_facecolor": ("gsplot.style.graph", "graph_facecolor"),
    "label": ("gsplot.style.label", "label"),
    "label_add_index": ("gsplot.style.label", "label_add_index"),
    "legend": ("gsplot.style.legend", "legend"),
    "legend_axes": ("gsplot.style.legend", "legend_axes"),
    "legend_handlers": ("gsplot.style.legend", "legend_handlers"),
    "legend_reverse": ("gsplot.style.legend", "legend_reverse"),
    "legend_get_handlers": ("gsplot.style.legend", "legend_get_handlers"),
    "legend_colormap": ("gsplot.style.legend_colormap", "legend_colormap"),
    "ticks_off": ("gsplot.style.ticks", "ticks_off"),
    "ticks_on": ("gsplot.style.ticks", "ticks_on"),
    "ticks_on_axes": ("gsplot.style.ticks", "ticks_on_axes"),
    "title": ("gsplot.style.title", "title"),
    "title_axes": ("gsplot.style.title", "title_axes"),
    "Config": ("gsplot.config.config", "Config"),
    "save_metadata": ("gsplot.config.config", "save_metadata"),
    "logger": ("gsplot.logger", "logger"),
}

LEGACY_ALL: Final[tuple[str, ...]] = (
    "get_cmap",
    "load_file",
    "load_file_fast",
    "axes",
    "axes_inset",
    "axes_inset_padding",
    "get_figure_size",
    "show",
    "hello_world",
    "config_load",
    "config_dict",
    "config_entry_option",
    "home",
    "pwd",
    "pwd_move",
    "pwd_main",
    "line",
    "line_colormap_solid",
    "line_colormap_dashed",
    "scatter",
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
    "legend",
    "legend_axes",
    "legend_handlers",
    "legend_reverse",
    "legend_get_handlers",
    "legend_colormap",
    "ticks_off",
    "ticks_on",
    "ticks_on_axes",
    "title",
    "title_axes",
)


def resolve_legacy(name: str) -> Any:
    """Load and return one historical root export on first use."""

    try:
        module_name, attribute_name = _LEGACY_EXPORTS[name]
    except KeyError as error:
        raise AttributeError(f"module 'gsplot' has no attribute {name!r}") from error

    module = import_module(module_name)
    return getattr(module, attribute_name)


def legacy_names() -> tuple[str, ...]:
    """Return the stable historical names exposed by the root package."""

    return LEGACY_ALL
