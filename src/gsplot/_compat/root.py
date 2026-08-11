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
    "show": ("gsplot._compat.root_api", "show"),
    "hello_world": ("gsplot.hello_world.hello_world", "hello_world"),
    "config_load": ("gsplot.config.config", "config_load"),
    "config_dict": ("gsplot.config.config", "config_dict"),
    "config_entry_option": ("gsplot.config.config", "config_entry_option"),
    "home": ("gsplot.path.path", "home"),
    "pwd": ("gsplot.path.path", "pwd"),
    "pwd_move": ("gsplot.path.path", "pwd_move"),
    "pwd_main": ("gsplot.path.path", "pwd_main"),
    "line": ("gsplot._compat.root_api", "line"),
    "line_colormap_solid": (
        "gsplot.plot.line_colormap_solid",
        "line_colormap_solid",
    ),
    "line_colormap_dashed": (
        "gsplot.plot.line_colormap_dashed",
        "line_colormap_dashed",
    ),
    "scatter": ("gsplot._compat.root_api", "scatter"),
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
    "legend": ("gsplot._compat.root_api", "legend"),
    "legend_axes": ("gsplot.style.legend", "legend_axes"),
    "legend_handlers": ("gsplot.style.legend", "legend_handlers"),
    "legend_reverse": ("gsplot.style.legend", "legend_reverse"),
    "legend_get_handlers": ("gsplot.style.legend", "legend_get_handlers"),
    "legend_colormap": ("gsplot.style.legend_colormap", "legend_colormap"),
    "ticks_off": ("gsplot.style.ticks", "ticks_off"),
    "ticks_on": ("gsplot.style.ticks", "ticks_on"),
    "ticks_on_axes": ("gsplot.style.ticks", "ticks_on_axes"),
    "title": ("gsplot._compat.root_api", "title"),
    "title_axes": ("gsplot.style.title", "title_axes"),
    "Config": ("gsplot.config.config", "Config"),
    "save_metadata": ("gsplot._compat.root_legacy", "save_metadata"),
    "logger": ("gsplot.logger", "logger"),
}

_CANONICAL_EXPORTS: Final[dict[str, tuple[str, str]]] = {
    "subplots": ("gsplot._figure.layout", "subplots"),
    "inset_axes": ("gsplot._figure.inset", "inset_axes"),
    "savefig": ("gsplot._figure.output", "savefig"),
    "show": ("gsplot._compat.root_api", "show"),
    "use_backend": ("gsplot._figure.backend", "use_backend"),
    "line": ("gsplot._compat.root_api", "line"),
    "scatter": ("gsplot._compat.root_api", "scatter"),
    "cmap_line": ("gsplot._plot.colored", "cmap_line"),
    "cmap_dash": ("gsplot._plot.colored", "cmap_dash"),
    "cmap_scatter": ("gsplot._plot.colored", "cmap_scatter"),
    "sample_cmap": ("gsplot._plot.colormap", "sample_cmap"),
    "style_axes": ("gsplot._style.axes", "style_axes"),
    "title": ("gsplot._compat.root_api", "title"),
    "suptitle": ("gsplot._style.axes", "suptitle"),
    "minor_ticks": ("gsplot._style.axes", "minor_ticks"),
    "box_aspect": ("gsplot._style.axes", "box_aspect"),
    "panel_labels": ("gsplot._style.panels", "panel_labels"),
    "fig_facecolor": ("gsplot._style.themes", "fig_facecolor"),
    "legend": ("gsplot._compat.root_api", "legend"),
    "legends": ("gsplot._style.legends", "legends"),
    "legend_entries": ("gsplot._style.legends", "legend_entries"),
    "cmap_legend": ("gsplot._style.legends", "cmap_legend"),
    "set_theme": ("gsplot._style.themes", "set_theme"),
    "load_config": ("gsplot._config.loader", "load_config"),
    "read_array": ("gsplot._io.arrays", "read_array"),
    "write_meta": ("gsplot._io.metadata", "write_meta"),
    "build_info": ("gsplot._io.build", "build_info"),
    "Config": ("gsplot._config.model", "Config"),
    "AxisSpec": ("gsplot._core.types", "AxisSpec"),
    "Theme": ("gsplot._core.types", "Theme"),
    "InsetSpec": ("gsplot._core.types", "InsetSpec"),
    "MetadataSnapshot": ("gsplot._core.types", "MetadataSnapshot"),
    "BuildInfo": ("gsplot._core.types", "BuildInfo"),
    "LegendEntries": ("gsplot._core.types", "LegendEntries"),
    "GsplotError": ("gsplot._core.errors", "GsplotError"),
    "ConfigError": ("gsplot._core.errors", "ConfigError"),
    "DataError": ("gsplot._core.errors", "DataError"),
    "LayoutError": ("gsplot._core.errors", "LayoutError"),
    "PlotError": ("gsplot._core.errors", "PlotError"),
    "OutputError": ("gsplot._core.errors", "OutputError"),
    "MetadataError": ("gsplot._core.errors", "MetadataError"),
    "MosaicSpec": ("gsplot._core.types", "MosaicSpec"),
    "NormalizeSpec": ("gsplot._core.types", "NormalizeSpec"),
    "ColorSpec": ("gsplot._core.types", "ColorSpec"),
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


def resolve_export(name: str) -> Any:
    """Resolve a canonical or historical root export lazily."""

    exports = _CANONICAL_EXPORTS if name in _CANONICAL_EXPORTS else _LEGACY_EXPORTS
    try:
        module_name, attribute_name = exports[name]
    except KeyError as error:
        raise AttributeError(f"module 'gsplot' has no attribute {name!r}") from error
    module = import_module(module_name)
    return getattr(module, attribute_name)


def legacy_names() -> tuple[str, ...]:
    """Return the stable historical names exposed by the root package."""

    return LEGACY_ALL


def canonical_names() -> tuple[str, ...]:
    """Return canonical root names currently implemented."""

    return tuple(_CANONICAL_EXPORTS)
